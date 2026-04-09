import mimetypes
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from assistants.store import assistant_exists, ensure_assistant, get_assistant_store
from pipelines.documents.pipeline import run_document_pipeline
from pipelines.videos.extractor import SUPPORTED_VIDEO_EXTENSIONS
from pipelines.videos.pipeline import run_video_pipeline
from vectorstores.chroma_store import query_chroma, reset_collection, store_in_chroma

SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx"}
DEFAULT_COLLECTION_NAME = "knowledge_base"


def _is_url(source):
    parsed = urlparse(source)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _guess_extension(source, content_type=None):
    parsed_path = urlparse(source).path
    extension = Path(parsed_path).suffix.lower()
    if extension:
        return extension

    guessed_from_mime = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed_from_mime == ".jpe":
        return ".jpg"
    return (guessed_from_mime or "").lower()


def _download_url_to_temp_file(source_url):
    request = Request(
        source_url,
        headers={"User-Agent": "MinorProject-Ingestion/1.0"},
    )

    with urlopen(request) as response:
        content_type = response.headers.get("Content-Type")
        extension = _guess_extension(source_url, content_type)
        if extension not in SUPPORTED_DOCUMENT_EXTENSIONS and extension not in SUPPORTED_VIDEO_EXTENSIONS:
            raise ValueError(
                f"Unsupported remote file type '{extension or 'unknown'}' for URL: {source_url}"
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(response.read())
            return temp_file.name


def _collect_chunks_from_single_source(source):
    temp_path = None
    source_path = source

    try:
        if _is_url(source):
            temp_path = _download_url_to_temp_file(source)
            source_path = temp_path

        extension = os.path.splitext(source_path)[1].lower()
        if extension in SUPPORTED_DOCUMENT_EXTENSIONS:
            result = run_document_pipeline(source_path, source_id=source)
        elif extension in SUPPORTED_VIDEO_EXTENSIONS:
            result = run_video_pipeline(source_path, source_id=source)
        else:
            raise ValueError(f"Unsupported file type: {source}")

        return result["chunks"]
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def ingest_sources(assistants_root, assistant_name, sources, replace_existing=False):
    existed_before = assistant_exists(assistants_root, assistant_name)
    assistant = ensure_assistant(assistants_root, assistant_name)
    all_chunks = []

    for source in sources:
        all_chunks.extend(_collect_chunks_from_single_source(source))

    if not all_chunks:
        raise FileNotFoundError("No supported source files were found.")

    if replace_existing:
        reset_collection(
            assistant.get("collection_name", DEFAULT_COLLECTION_NAME),
            persist_directory=assistant["persist_directory"],
        )

    store_result = store_in_chroma(
        chunks=all_chunks,
        collection_name=assistant.get("collection_name", DEFAULT_COLLECTION_NAME),
        persist_directory=assistant["persist_directory"],
    )

    return {
        "assistant": assistant,
        "assistant_existed_before": existed_before,
        "collection_name": store_result["collection_name"],
        "stored_count": store_result["stored_count"],
        "source_count": len(sources),
    }


def query_assistant_knowledge(assistants_root, assistant_name, question, top_k=2):
    assistant = get_assistant_store(assistants_root, assistant_name)
    return query_chroma(
        question=question,
        collection_name=assistant.get("collection_name", DEFAULT_COLLECTION_NAME),
        top_k=top_k,
        persist_directory=assistant["persist_directory"],
    )
