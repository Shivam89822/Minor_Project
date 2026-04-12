import json
import math
import os
import re


K1 = 1.5
B = 0.75


def _tokenize(text):
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
        if len(token) > 1
    ]


def _term_frequencies(tokens):
    frequencies = {}
    for token in tokens:
        frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies


def _build_index_payload(records):
    doc_frequencies = {}
    total_doc_length = 0

    for record in records:
        total_doc_length += record["length"]
        for token in record["term_freqs"]:
            doc_frequencies[token] = doc_frequencies.get(token, 0) + 1

    doc_count = len(records)
    avg_doc_length = (total_doc_length / doc_count) if doc_count else 0.0

    return {
        "doc_count": doc_count,
        "avg_doc_length": avg_doc_length,
        "doc_frequencies": doc_frequencies,
        "records": records,
    }


def _load_index(index_path):
    if not os.path.exists(index_path):
        return None

    with open(index_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_sparse_index(index_path):
    return _load_index(index_path)


def store_sparse_index(index_path, chunks, replace_existing=False):
    existing_index = None if replace_existing else _load_index(index_path)
    existing_records = (existing_index or {}).get("records", [])

    records = list(existing_records)
    for chunk in chunks:
        tokens = _tokenize(chunk.get("text", ""))
        if not tokens:
            continue

        records.append(
            {
                "id": chunk["storage_id"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata") or {},
                "length": len(tokens),
                "term_freqs": _term_frequencies(tokens),
            }
        )

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    payload = _build_index_payload(records)

    with open(index_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    return payload


def _bm25_score(query_terms, record, doc_frequencies, doc_count, avg_doc_length):
    score = 0.0
    document_length = max(1, record.get("length", 0))
    term_frequencies = record.get("term_freqs") or {}

    for term in query_terms:
        term_frequency = term_frequencies.get(term, 0)
        if not term_frequency:
            continue

        document_frequency = doc_frequencies.get(term, 0)
        inverse_document_frequency = math.log(
            1 + ((doc_count - document_frequency + 0.5) / (document_frequency + 0.5))
        )

        denominator = term_frequency + K1 * (1 - B + B * (document_length / max(avg_doc_length, 1.0)))
        score += inverse_document_frequency * ((term_frequency * (K1 + 1)) / denominator)

    return score


def query_sparse_index(index_path, question, top_k=10):
    index = load_sparse_index(index_path)
    if not index:
        return []

    query_terms = _tokenize(question)
    if not query_terms:
        return []

    scored_records = []
    doc_frequencies = index.get("doc_frequencies") or {}
    doc_count = index.get("doc_count") or 0
    avg_doc_length = index.get("avg_doc_length") or 0.0

    for record in index.get("records") or []:
        score = _bm25_score(query_terms, record, doc_frequencies, doc_count, avg_doc_length)
        if score <= 0:
            continue

        scored_records.append(
            {
                "id": record["id"],
                "text": record["text"],
                "metadata": record.get("metadata") or {},
                "sparse_score": score,
            }
        )

    scored_records.sort(key=lambda item: item["sparse_score"], reverse=True)
    return scored_records[:top_k]
