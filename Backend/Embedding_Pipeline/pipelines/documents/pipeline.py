import os

from pipelines.documents.extractor import extract_document_units, extract_text
from processing.cleaner import clean_text



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
            }
        )

    return chunks



def _build_document_chunk(units):
    pages = [unit["page"] for unit in units if unit.get("page") is not None]
    sections = [unit["section"] for unit in units if unit.get("section")]

    return {
        "text": " ".join(unit["text"] for unit in units).strip(),
        "page": pages[0] if pages else None,
        "section": sections[0] if sections else None,
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



def _chunk_document_units(units, max_words=400, overlap=50):
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

        if current_units and current_word_count + unit_word_count > max_words:
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



def run_document_pipeline(file_path, max_words=400, overlap=50, source_id=None):
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
                    "chunk_index": index,
                },
            }
        )

    return {
        "text": text,
        "cleaned_text": cleaned,
        "chunks": records,
    }
