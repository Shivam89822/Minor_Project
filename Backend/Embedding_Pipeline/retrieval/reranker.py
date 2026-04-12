import re


def _tokenize(text):
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
        if len(token) > 2
    }


def _metadata_text(metadata):
    parts = []
    for key in ("source", "section", "type"):
        value = (metadata or {}).get(key)
        if value:
            parts.append(str(value))
    return " ".join(parts)


def _score_match(question, match):
    query_terms = _tokenize(question)
    text = match.get("text", "")
    metadata = match.get("metadata") or {}

    text_terms = _tokenize(text)
    metadata_terms = _tokenize(_metadata_text(metadata))

    overlap_count = len(query_terms & text_terms)
    metadata_overlap = len(query_terms & metadata_terms)
    overlap_ratio = overlap_count / max(len(query_terms), 1)

    exact_phrase_bonus = 0.0
    cleaned_question = " ".join((question or "").lower().split())
    cleaned_text = " ".join((text or "").lower().split())
    if cleaned_question and cleaned_question in cleaned_text:
        exact_phrase_bonus = 0.25

    section_bonus = 0.08 if metadata.get("section") and metadata_overlap > 0 else 0.0
    dense_score = float(match.get("dense_score") or 0.0)
    sparse_score = float(match.get("sparse_score") or 0.0)
    hybrid_score = float(match.get("hybrid_score") or 0.0)

    rerank_score = (
        (hybrid_score * 0.45)
        + (overlap_ratio * 0.35)
        + (metadata_overlap * 0.04)
        + exact_phrase_bonus
        + section_bonus
        + (0.03 if overlap_count > 0 else 0.0)
    )

    enriched_match = dict(match)
    enriched_match["keyword_overlap"] = overlap_count
    enriched_match["metadata_overlap"] = metadata_overlap
    enriched_match["overlap_ratio"] = overlap_ratio
    enriched_match["dense_score"] = dense_score
    enriched_match["sparse_score"] = sparse_score
    enriched_match["hybrid_score"] = hybrid_score
    enriched_match["rerank_score"] = rerank_score

    return enriched_match


def rerank_matches(question, matches):
    reranked = [_score_match(question, match) for match in matches]
    reranked.sort(
        key=lambda item: (
            item.get("rerank_score", 0.0),
            item.get("keyword_overlap", 0),
            item.get("hybrid_score", 0.0),
        ),
        reverse=True,
    )
    return reranked


def select_strict_matches(question, matches, top_k):
    reranked = rerank_matches(question, matches)
    selected = []

    for match in reranked:
        keyword_overlap = match.get("keyword_overlap", 0)
        metadata_overlap = match.get("metadata_overlap", 0)
        dense_rank = match.get("dense_rank")
        sparse_rank = match.get("sparse_rank")

        if (
            keyword_overlap > 0
            or metadata_overlap > 0
            or (dense_rank is not None and dense_rank <= 2)
            or (sparse_rank is not None and sparse_rank <= 2)
        ):
            selected.append(match)

        if len(selected) >= top_k:
            break

    if not selected:
        return reranked[:top_k]

    if len(selected) < min(2, top_k):
        seen_ids = {match["id"] for match in selected}
        for match in reranked:
            if match["id"] in seen_ids:
                continue
            selected.append(match)
            if len(selected) >= min(2, top_k):
                break

    return selected[:top_k]
