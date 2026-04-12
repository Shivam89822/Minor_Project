import mimetypes
import os
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from assistants.store import assistant_exists, ensure_assistant, get_assistant_store
from pipelines.documents.pipeline import run_document_pipeline
from pipelines.videos.extractor import SUPPORTED_VIDEO_EXTENSIONS
from pipelines.videos.pipeline import run_video_pipeline
from retrieval.reranker import select_strict_matches
from retrieval.sparse_index import load_sparse_index, query_sparse_index, store_sparse_index
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


def _normalize_source(source):
    if isinstance(source, dict):
        return source
    return {
        "path": source,
        "source_name": source,
    }


def _collect_chunks_from_single_source(source):
    source_payload = _normalize_source(source)
    temp_path = None
    source_path = source_payload["path"]
    source_name = source_payload.get("source_name") or source_path

    try:
        if _is_url(source_path):
            temp_path = _download_url_to_temp_file(source_path)
            source_path = temp_path

        extension = os.path.splitext(source_path)[1].lower()
        if extension in SUPPORTED_DOCUMENT_EXTENSIONS:
            result = run_document_pipeline(source_path, source_id=source_name)
        elif extension in SUPPORTED_VIDEO_EXTENSIONS:
            result = run_video_pipeline(source_path, source_id=source_name)
        else:
            raise ValueError(f"Unsupported file type: {source_name}")

        return result["chunks"]
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _prepare_chunks_for_storage(chunks):
    prepared_chunks = []

    for chunk in chunks:
        prepared_chunk = dict(chunk)
        prepared_chunk["metadata"] = dict(chunk.get("metadata") or {})
        prepared_chunk["storage_id"] = chunk.get("storage_id") or f"{chunk.get('id', 'chunk')}-{uuid.uuid4().hex}"
        prepared_chunks.append(prepared_chunk)

    return prepared_chunks


def _reciprocal_rank(rank, weight=1.0, constant=60):
    return weight * (1.0 / (constant + rank))


def _merge_hybrid_matches(dense_matches, sparse_matches, top_k):
    merged_matches = {}

    for rank, match in enumerate(dense_matches, start=1):
        entry = merged_matches.setdefault(
            match["id"],
            {
                "id": match["id"],
                "text": match.get("text", ""),
                "metadata": match.get("metadata") or {},
                "distance": match.get("distance"),
                "dense_rank": None,
                "sparse_rank": None,
                "dense_score": 0.0,
                "sparse_score": 0.0,
                "hybrid_score": 0.0,
                "retrieval_methods": [],
            },
        )
        entry["dense_rank"] = rank
        entry["dense_score"] = _reciprocal_rank(rank, weight=1.0)
        entry["hybrid_score"] += entry["dense_score"]
        entry["retrieval_methods"] = sorted(set(entry["retrieval_methods"] + ["dense"]))

    for rank, match in enumerate(sparse_matches, start=1):
        entry = merged_matches.setdefault(
            match["id"],
            {
                "id": match["id"],
                "text": match.get("text", ""),
                "metadata": match.get("metadata") or {},
                "distance": None,
                "dense_rank": None,
                "sparse_rank": None,
                "dense_score": 0.0,
                "sparse_score": 0.0,
                "hybrid_score": 0.0,
                "retrieval_methods": [],
            },
        )
        entry["sparse_rank"] = rank
        entry["sparse_score"] = _reciprocal_rank(rank, weight=0.9)
        entry["hybrid_score"] += entry["sparse_score"]
        if not entry.get("text"):
            entry["text"] = match.get("text", "")
        if not entry.get("metadata"):
            entry["metadata"] = match.get("metadata") or {}
        entry["retrieval_methods"] = sorted(set(entry["retrieval_methods"] + ["sparse"]))

    ranked_matches = sorted(
        merged_matches.values(),
        key=lambda item: (item["hybrid_score"], item["dense_rank"] is not None, -(item["dense_rank"] or 9999)),
        reverse=True,
    )

    return ranked_matches[:top_k]


def _neighbor_allowed(base_metadata, candidate_metadata):
    if not base_metadata or not candidate_metadata:
        return False

    if base_metadata.get("source") != candidate_metadata.get("source"):
        return False

    base_section = base_metadata.get("section")
    candidate_section = candidate_metadata.get("section")
    if base_section and candidate_section and base_section != candidate_section:
        return False

    base_page = base_metadata.get("page")
    candidate_page = candidate_metadata.get("page")
    if base_page is not None and candidate_page is not None and abs(int(base_page) - int(candidate_page)) > 1:
        return False

    return True


def _expand_with_neighbors(index_path, selected_matches, limit):
    sparse_index = load_sparse_index(index_path)
    if not sparse_index:
        return selected_matches

    records = sparse_index.get("records") or []
    records_by_source_and_chunk = {}
    records_by_id = {}

    for record in records:
        metadata = record.get("metadata") or {}
        source = metadata.get("source")
        chunk_index = metadata.get("chunk_index")
        if source is not None and chunk_index is not None:
            records_by_source_and_chunk[(source, chunk_index)] = record
        records_by_id[record["id"]] = record

    expanded = []
    seen_ids = set()

    for match in selected_matches:
        if match["id"] not in seen_ids:
            expanded.append(match)
            seen_ids.add(match["id"])

        if len(expanded) >= limit:
            break

        metadata = match.get("metadata") or {}
        source = metadata.get("source")
        chunk_index = metadata.get("chunk_index")
        if source is None or chunk_index is None:
            continue

        for direction in (-1, 1):
            neighbor_record = records_by_source_and_chunk.get((source, chunk_index + direction))
            if not neighbor_record or neighbor_record["id"] in seen_ids:
                continue
            if not _neighbor_allowed(metadata, neighbor_record.get("metadata") or {}):
                continue

            expanded.append(
                {
                    "id": neighbor_record["id"],
                    "text": neighbor_record.get("text", ""),
                    "metadata": neighbor_record.get("metadata") or {},
                    "distance": None,
                    "dense_rank": None,
                    "sparse_rank": None,
                    "dense_score": 0.0,
                    "sparse_score": 0.0,
                    "hybrid_score": float(match.get("hybrid_score") or 0.0) * 0.6,
                    "rerank_score": float(match.get("rerank_score") or 0.0) * 0.85,
                    "retrieval_methods": sorted(set((match.get("retrieval_methods") or []) + ["neighbor"])),
                }
            )
            seen_ids.add(neighbor_record["id"])

            if len(expanded) >= limit:
                break

        if len(expanded) >= limit:
            break

    return expanded


def ingest_sources(assistants_root, assistant_name, sources, replace_existing=False):
    existed_before = assistant_exists(assistants_root, assistant_name)
    assistant = ensure_assistant(assistants_root, assistant_name)
    all_chunks = []

    for source in sources:
        all_chunks.extend(_collect_chunks_from_single_source(source))

    if not all_chunks:
        raise FileNotFoundError("No supported source files were found.")

    prepared_chunks = _prepare_chunks_for_storage(all_chunks)

    if replace_existing:
        reset_collection(
            assistant.get("collection_name", DEFAULT_COLLECTION_NAME),
            persist_directory=assistant["persist_directory"],
        )

    store_result = store_in_chroma(
        chunks=prepared_chunks,
        collection_name=assistant.get("collection_name", DEFAULT_COLLECTION_NAME),
        persist_directory=assistant["persist_directory"],
    )
    store_sparse_index(
        assistant["sparse_index_path"],
        prepared_chunks,
        replace_existing=replace_existing,
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
    candidate_count = max(top_k * 3, 10)
    dense_matches = query_chroma(
        question=question,
        collection_name=assistant.get("collection_name", DEFAULT_COLLECTION_NAME),
        top_k=candidate_count,
        persist_directory=assistant["persist_directory"],
    )
    sparse_matches = query_sparse_index(
        assistant["sparse_index_path"],
        question=question,
        top_k=candidate_count,
    )

    if not sparse_matches:
        return dense_matches[:top_k]

    hybrid_matches = _merge_hybrid_matches(dense_matches, sparse_matches, top_k=candidate_count)
    selected_matches = select_strict_matches(question, hybrid_matches, top_k=top_k)
    return _expand_with_neighbors(
        assistant["sparse_index_path"],
        selected_matches,
        limit=max(top_k, min(top_k + 2, top_k * 2)),
    )
