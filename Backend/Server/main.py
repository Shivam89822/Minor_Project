import os
import sys
import tempfile

from fastapi import FastAPI
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
# from pipelines.videos.pipeline import process_video
# from pipelines.pdf.pipeline import process_pdf


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

    assistants_root = os.path.join(EMBEDDING_PIPELINE_DIR, "assistant_dbs")

    try:
        store_result = ingest_embedding_sources(
            assistants_root=assistants_root,
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
        "merged_into_existing_assistant": store_result["assistant_existed_before"],
        "created_new_assistant": not store_result["assistant_existed_before"],
    }


@app.post("/assistants/embeddings/from-url")
def create_embeddings_from_cloudinary_url(
    payload: schemas.AssistantEmbeddingURLCreate,
    current_user: str = Depends(verify_token),
):
    assistants_root = os.path.join(EMBEDDING_PIPELINE_DIR, "assistant_dbs")
    store_result = ingest_embedding_sources(
        assistants_root=assistants_root,
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
        "merged_into_existing_assistant": store_result["assistant_existed_before"],
        "created_new_assistant": not store_result["assistant_existed_before"],
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
