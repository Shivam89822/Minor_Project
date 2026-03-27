from pipelines.documents.extractor import extract_text
from processing.cleaner import clean_text
from processing.chunker import chunk_text


def run_document_pipeline(file_path):
    print("🔹 Starting pipeline...")

    text = extract_text(file_path)
    print(f"✅ Extracted length: {len(text)}")

    cleaned = clean_text(text)
    print(f"✅ Cleaned length: {len(cleaned)}")

    chunks = chunk_text(cleaned)
    print(f"✅ Total chunks: {len(chunks)}")

    return chunks