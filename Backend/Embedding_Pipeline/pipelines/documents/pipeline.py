import os

from pipelines.documents.extractor import extract_document_units, extract_text
from processing.cleaner import clean_text


DEFAULT_DOCUMENT_MAX_WORDS = 150
DEFAULT_DOCUMENT_OVERLAP = 40
MIN_PARAGRAPH_WORDS = 35


def _split_document_unit(unit, max_words):
    cleaned_text = clean_text(unit.get("text", ""))
    if not cleaned_text:
        return []

    words = cleaned_text.split()
    chunks = []

    for index in range(0, len(words), max_words):
        chunk_words = words[index:index + max_words]
        chunks.append(
            {
                "text": " ".join(chunk_words),
                "page": unit.get("page"),
                "section": unit.get("section"),
                "paragraph_index": unit.get("paragraph_index"),
            }
        )

    return chunks


def _build_document_chunk(units):
    pages = [unit["page"] for unit in units if unit.get("page") is not None]
    sections = [unit["section"] for unit in units if unit.get("section")]
    paragraph_indexes = [unit["paragraph_index"] for unit in units if unit.get("paragraph_index") is not None]

    return {
        "text": " ".join(unit["text"] for unit in units).strip(),
        "page": pages[0] if pages else None,
        "page_end": pages[-1] if pages else None,
        "section": sections[0] if sections else None,
        "paragraph_index_start": paragraph_indexes[0] if paragraph_indexes else None,
        "paragraph_index_end": paragraph_indexes[-1] if paragraph_indexes else None,
    }


def _document_overlap_units(units, overlap):
    if overlap <= 0:
        return [], 0

    overlap_units = []
    overlap_words = 0

    for unit in reversed(units):
        overlap_units.insert(0, unit)
        overlap_words += len(unit["text"].split())
        if overlap_words >= overlap:
            break

    return overlap_units, overlap_words


def _should_force_new_chunk(current_units, unit, current_word_count, max_words):
    if not current_units:
        return False

    unit_word_count = len(unit["text"].split())
    previous_unit = current_units[-1]

    if current_word_count + unit_word_count <= max_words:
        return False

    if previous_unit.get("page") != unit.get("page"):
        return True

    if previous_unit.get("section") != unit.get("section") and current_word_count >= MIN_PARAGRAPH_WORDS:
        return True

    return current_word_count >= MIN_PARAGRAPH_WORDS


def _chunk_document_units(units, max_words=DEFAULT_DOCUMENT_MAX_WORDS, overlap=DEFAULT_DOCUMENT_OVERLAP):
    normalized_units = []
    for unit in units:
        normalized_units.extend(_split_document_unit(unit, max_words=max_words))

    if not normalized_units:
        return []

    chunks = []
    current_units = []
    current_word_count = 0

    for unit in normalized_units:
        unit_word_count = len(unit["text"].split())

        if _should_force_new_chunk(current_units, unit, current_word_count, max_words):
            chunks.append(_build_document_chunk(current_units))
            current_units, current_word_count = _document_overlap_units(
                current_units,
                overlap,
            )

        current_units.append(unit)
        current_word_count += unit_word_count

    if current_units:
        chunks.append(_build_document_chunk(current_units))

    return chunks


def run_document_pipeline(
    file_path,
    max_words=DEFAULT_DOCUMENT_MAX_WORDS,
    overlap=DEFAULT_DOCUMENT_OVERLAP,
    source_id=None,
):
    print("Starting document pipeline...")

    text = extract_text(file_path)
    print(f"Extracted length: {len(text)}")

    cleaned = clean_text(text)
    print(f"Cleaned length: {len(cleaned)}")

    units = extract_document_units(file_path)
    chunk_payloads = _chunk_document_units(units, max_words=max_words, overlap=overlap)
    print(f"Total chunks: {len(chunk_payloads)}")

    file_name = os.path.basename(file_path)
    file_stem, file_extension = os.path.splitext(file_name)
    source_name = source_id or file_name
    records = []

    for index, chunk in enumerate(chunk_payloads, start=1):
        records.append(
            {
                "id": f"{file_stem}_chunk_{index}",
                "text": chunk["text"],
                "metadata": {
                    "source": source_name,
                    "type": file_extension.lstrip(".").lower(),
                    "page": chunk["page"],
                    "page_end": chunk["page_end"],
                    "section": chunk["section"],
                    "chunk_index": index,
                    "paragraph_index_start": chunk["paragraph_index_start"],
                    "paragraph_index_end": chunk["paragraph_index_end"],
                },
            }
        )

    return {
        "text": text,
        "cleaned_text": cleaned,
        "chunks": records,
    }
