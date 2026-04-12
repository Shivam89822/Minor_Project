import json
import os
import re
import sys
import tempfile
from datetime import datetime

from fastapi import BackgroundTasks, FastAPI
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Backend running 🚀"}

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException

from database import SessionLocal, engine, Base
import models, schemas
from utils.security import hash_password

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency (DB session)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(models.User).filter(models.User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        hashed_pwd = hash_password(user.password)

        new_user = models.User(
            email=user.email,
            password=hashed_pwd
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {"message": "User created successfully"}
    except Exception as e:
        print(f"Error in register: {e}")
        raise

from sqlalchemy.orm import Session

from utils.security import verify_password
from auth import create_access_token

@app.post("/login")
def login(
    username: str = Form(...),   # ⚠️ must be username (not email)
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    db_user = db.query(models.User).filter(models.User.email == username).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_access_token({"sub": db_user.email})

    return {"access_token": token, "token_type": "bearer"}


from auth import verify_token

@app.get("/me")
def get_current_user(current_user: str = Depends(verify_token)):
    return {"message": f"Welcome {current_user}"}

from fastapi import UploadFile, File
from auth import verify_token

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
EMBEDDING_PIPELINE_DIR = os.path.join(BACKEND_DIR, "Embedding_Pipeline")
if EMBEDDING_PIPELINE_DIR not in sys.path:
    sys.path.insert(0, EMBEDDING_PIPELINE_DIR)

from assistants.store import assistant_exists, delete_assistant as delete_assistant_store

import cloudinary.uploader
from cloudinary_config import *

from fastapi import UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import cloudinary.uploader

from database import get_db
import models
from auth import verify_token
from ingestion.service import ingest_sources as ingest_embedding_sources
from ingestion.service import query_assistant_knowledge
from utils.gemini_grounding import OUT_OF_CONTEXT_REPLY, generate_grounded_answer
# from pipelines.videos.pipeline import process_video
# from pipelines.pdf.pipeline import process_pdf

ASSISTANTS_ROOT = os.path.join(EMBEDDING_PIPELINE_DIR, "assistant_dbs")


def _serialize_chat_message(message: models.ChatMessage):
    return {
        "id": message.id,
        "role": message.role,
        "text": message.text,
        "matches": json.loads(message.matches_json) if message.matches_json else [],
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def _serialize_assistant(assistant: models.Assistant):
    return {
        "id": assistant.id,
        "assistant_id": assistant.assistant_id,
        "name": assistant.name,
        "status": assistant.status,
        "source_count": assistant.source_count,
        "user_email": assistant.user_email,
        "last_error": assistant.last_error,
        "created_at": assistant.created_at.isoformat() if assistant.created_at else None,
        "updated_at": assistant.updated_at.isoformat() if assistant.updated_at else None,
    }


def _assistant_slug(value: str):
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "assistant"


def _assistant_by_slug(db: Session, assistant_id: str, current_user: str):
    assistant = (
        db.query(models.Assistant)
        .filter(models.Assistant.assistant_id == assistant_id, models.Assistant.user_email == current_user)
        .first()
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


def _cleanup_orphan_chat_messages(db: Session):
    valid_assistant_ids = db.query(models.Assistant.id).subquery()
    db.query(models.ChatMessage).filter(
        ~models.ChatMessage.assistant_id.in_(valid_assistant_ids)
    ).delete(synchronize_session=False)


def _question_keywords(question: str):
    return {
        word
        for word in re.findall(r"[a-zA-Z0-9]+", question.lower())
        if len(word) > 2
    }


def _build_relevant_snippet(question: str, text: str, max_sentences: int = 2, max_chars: int = 320):
    cleaned_text = " ".join((text or "").split()).strip()
    if not cleaned_text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", cleaned_text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    if not sentences:
        return cleaned_text[:max_chars].rstrip() + ("..." if len(cleaned_text) > max_chars else "")

    keywords = _question_keywords(question)
    ranked_sentences = []

    for index, sentence in enumerate(sentences):
        sentence_terms = set(re.findall(r"[a-zA-Z0-9]+", sentence.lower()))
        overlap = len(keywords & sentence_terms)
        ranked_sentences.append((overlap, -index, sentence))

    ranked_sentences.sort(reverse=True)
    selected = [sentence for _, _, sentence in ranked_sentences[:max_sentences] if sentence]

    if not any(score > 0 for score, _, _ in ranked_sentences[:max_sentences]):
        selected = sentences[:max_sentences]

    snippet = " ".join(selected).strip()
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 3].rstrip() + "..."

    return snippet


def _build_source_payloads(files: list[UploadFile]):
    source_payloads = []
    temp_paths = []

    for file in files:
        suffix = os.path.splitext(file.filename or "")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file.file.read())
            temp_paths.append(temp_file.name)
            source_payloads.append(
                {
                    "path": temp_file.name,
                    "source_name": file.filename or os.path.basename(temp_file.name),
                }
            )

    return source_payloads, temp_paths


def _ingest_assistant_files(assistant_db_id: int, assistant_name: str, sources: list[dict]):
    db = SessionLocal()
    try:
        assistant_record = db.query(models.Assistant).filter(models.Assistant.id == assistant_db_id).first()
        if not assistant_record:
            return

        try:
            ingest_embedding_sources(
                assistants_root=ASSISTANTS_ROOT,
                assistant_name=assistant_name,
                sources=sources,
                replace_existing=False,
            )
            assistant_record.status = "active"
            assistant_record.last_error = None
        except Exception as exc:
            assistant_record.status = "failed"
            assistant_record.last_error = str(exc)
        finally:
            assistant_record.updated_at = datetime.utcnow()
            db.add(assistant_record)
            db.commit()
    finally:
        for source in sources:
            temp_path = source.get("path")
            if os.path.exists(temp_path):
                os.remove(temp_path)
        db.close()


@app.get("/assistants")
def list_user_assistants(
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    assistants = (
        db.query(models.Assistant)
        .filter(models.Assistant.user_email == current_user)
        .order_by(models.Assistant.updated_at.desc())
        .all()
    )
    return {"assistants": [_serialize_assistant(assistant) for assistant in assistants]}


@app.get("/assistants/{assistant_id}")
def get_user_assistant(
    assistant_id: str,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    assistant = _assistant_by_slug(db, assistant_id, current_user)
    _cleanup_orphan_chat_messages(db)
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.assistant_id == assistant.id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )
    return {
        "assistant": _serialize_assistant(assistant),
        "messages": [_serialize_chat_message(message) for message in messages],
    }


@app.post("/assistants")
def create_assistant(
    background_tasks: BackgroundTasks,
    assistant_name: str = Form(...),
    files: list[UploadFile] = File(...),
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    cleaned_name = assistant_name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Assistant name is required")

    existing_record = (
        db.query(models.Assistant)
        .filter(models.Assistant.name == cleaned_name)
        .first()
    )
    if existing_record or assistant_exists(ASSISTANTS_ROOT, cleaned_name):
        raise HTTPException(status_code=400, detail="Assistant name already exists. Please choose another name.")

    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one PDF or video file.")

    source_payloads, _ = _build_source_payloads(files)

    new_assistant = models.Assistant(
        assistant_id=_assistant_slug(cleaned_name),
        name=cleaned_name,
        status="training",
        source_count=len(files),
        user_email=current_user,
        updated_at=datetime.utcnow(),
    )

    db.add(new_assistant)
    db.commit()
    db.refresh(new_assistant)

    background_tasks.add_task(_ingest_assistant_files, new_assistant.id, cleaned_name, source_payloads)

    return {
        "message": "Assistant creation started",
        "assistant": _serialize_assistant(new_assistant),
    }


@app.post("/assistants/{assistant_id}/files")
def add_files_to_assistant(
    assistant_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    assistant = _assistant_by_slug(db, assistant_id, current_user)

    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one PDF or video file.")

    source_payloads, _ = _build_source_payloads(files)

    assistant.status = "training"
    assistant.source_count += len(files)
    assistant.last_error = None
    assistant.updated_at = datetime.utcnow()
    db.add(assistant)
    db.commit()
    db.refresh(assistant)

    background_tasks.add_task(_ingest_assistant_files, assistant.id, assistant.name, source_payloads)

    return {
        "message": "Files uploaded. Embeddings are being merged into the assistant.",
        "assistant": _serialize_assistant(assistant),
    }


@app.delete("/assistants/{assistant_id}")
def delete_assistant(
    assistant_id: str,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    assistant = _assistant_by_slug(db, assistant_id, current_user)
    serialized_assistant = _serialize_assistant(assistant)

    try:
        delete_assistant_store(ASSISTANTS_ROOT, assistant.name)
    except FileNotFoundError:
        pass
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to delete assistant embeddings: {exc}") from exc

    db.query(models.ChatMessage).filter(models.ChatMessage.assistant_id == assistant.id).delete(synchronize_session=False)
    db.delete(assistant)
    db.commit()

    return {
        "message": "Assistant deleted successfully.",
        "assistant": serialized_assistant,
    }


@app.post("/assistants/{assistant_id}/chat")
def chat_with_assistant(
    assistant_id: str,
    payload: schemas.AssistantChatRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    assistant = _assistant_by_slug(db, assistant_id, current_user)

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    if assistant.status == "failed":
        raise HTTPException(status_code=400, detail="Assistant is in failed state. Upload more files or recreate it.")

    try:
        matches = query_assistant_knowledge(
            assistants_root=ASSISTANTS_ROOT,
            assistant_name=assistant.name,
            question=question,
            top_k=max(1, min(payload.top_k, 8)),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Embeddings are still being prepared for this assistant.") from exc

    formatted_matches = []
    response_parts = []
    for index, match in enumerate(matches, start=1):
        metadata = match.get("metadata") or {}
        source = metadata.get("source", "Unknown source")
        page = metadata.get("page")
        start = metadata.get("start")
        end = metadata.get("end")

        citation_parts = [source]
        if page is not None:
            citation_parts.append(f"page {page}")
        if start is not None:
            citation_parts.append(f"{int(start // 60):02d}:{int(start % 60):02d}")
        if end is not None:
            citation_parts.append(f"to {int(end // 60):02d}:{int(end % 60):02d}")

        citation = " | ".join(citation_parts)
        snippet = _build_relevant_snippet(question, match.get("text", ""))
        formatted_matches.append(
            {
                "id": match.get("id"),
                "text": snippet,
                "source": source,
                "page": page,
                "start": start,
                "end": end,
                "citation": citation,
                "distance": match.get("distance"),
            }
        )
        response_parts.append(f"{index}. {snippet}\nSource: {citation}")

    generated_answer_result = (
        {
            "answer": OUT_OF_CONTEXT_REPLY,
            "used": True,
            "reason": "no_formatted_matches",
        }
        if not formatted_matches
        else generate_grounded_answer(question, matches)
    )
    if formatted_matches:
        paragraph = ". ".join([item["text"] for item in formatted_matches]) + "."
        sources = "\n\nSources:\n" + "\n".join([f"{i+1}. {item['citation']}" for i, item in enumerate(formatted_matches, 1)])
        fallback_answer = paragraph + sources
    else:
        fallback_answer = "No relevant context was found in this assistant's knowledge base."
    final_answer = (generated_answer_result or {}).get("answer") or fallback_answer

    user_message = models.ChatMessage(
        assistant_id=assistant.id,
        role="user",
        text=question,
        matches_json=None,
        created_at=datetime.utcnow(),
    )

    assistant_message = models.ChatMessage(
        assistant_id=assistant.id,
        role="assistant",
        text=final_answer,
        matches_json=json.dumps(formatted_matches),
        created_at=datetime.utcnow(),
    )

    db.add_all([user_message, assistant_message])
    db.commit()

    return {
        "assistant": _serialize_assistant(assistant),
        "question": question,
        "answer": final_answer,
        "matches": formatted_matches,
        "answer_source": "gemini" if (generated_answer_result or {}).get("used") and final_answer != fallback_answer else "fallback",
        "gemini_used": bool((generated_answer_result or {}).get("used")),
        "gemini_reason": (generated_answer_result or {}).get("reason"),
        "gemini_model": (generated_answer_result or {}).get("model"),
    }


@app.post("/upload/{workspace_id}")
def upload_file(
    workspace_id: int,
    assistant_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)   # 🔥 ADD THIS
):
    if not assistant_name.strip():
        raise HTTPException(status_code=400, detail="assistant_name is required")

    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name

    try:
        store_result = ingest_embedding_sources(
            assistants_root=ASSISTANTS_ROOT,
            assistant_name=assistant_name,
            sources=[temp_path],
            replace_existing=False,
        )
    except Exception as exc:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Embedding ingestion failed: {exc}") from exc

    file.file.seek(0)

    try:
        result = cloudinary.uploader.upload(
            file.file,
            resource_type="auto"
        )
    except Exception as exc:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {exc}") from exc

    file_url = result["secure_url"]
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 🔥 SAVE FILE IN DATABASE
    new_file = models.File(
        filename=file.filename,
        file_url=file_url,
        workspace_id=workspace_id,
        user_email=current_user
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    assistant = store_result["assistant"]

    return {
        "message": "Uploaded and embeddings created successfully",
        "file_url": file_url,
        "file_id": new_file.id,
        "assistant_name": assistant["assistant_name"],
        "assistant_id": assistant["assistant_id"],
        "stored_count": store_result["stored_count"],
        "source_count": store_result["source_count"],
        "merged_into_existing_assistant": store_result.get("assistant_existed_before", False),
        "created_new_assistant": not store_result.get("assistant_existed_before", False),
    }


@app.post("/assistants/embeddings/from-url")
def create_embeddings_from_cloudinary_url(
    payload: schemas.AssistantEmbeddingURLCreate,
    current_user: str = Depends(verify_token),
):
    store_result = ingest_embedding_sources(
        assistants_root=ASSISTANTS_ROOT,
        assistant_name=payload.assistant_name,
        sources=[payload.cloudinary_url],
        replace_existing=False,
    )

    assistant = store_result["assistant"]
    return {
        "message": "Embeddings created successfully",
        "assistant_name": assistant["assistant_name"],
        "assistant_id": assistant["assistant_id"],
        "cloudinary_url": payload.cloudinary_url,
        "stored_count": store_result["stored_count"],
        "source_count": store_result["source_count"],
        "persist_directory": assistant["persist_directory"],
        "merged_into_existing_assistant": store_result.get("assistant_existed_before", False),
        "created_new_assistant": not store_result.get("assistant_existed_before", False),
        "requested_by": current_user,
    }





@app.post("/workspace")
def create_workspace(
    workspace: schemas.WorkspaceCreate,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    new_ws = models.Workspace(
        name=workspace.name,
        user_email=current_user
    )

    db.add(new_ws)
    db.commit()
    db.refresh(new_ws)

    return {"message": "Workspace created", "id": new_ws.id}
