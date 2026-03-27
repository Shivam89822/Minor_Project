from pipelines.documents.extractor import extract_text


def clean_text(text):
    return " ".join(text.split())


def chunk_text(text, max_words=400, overlap=50):
    paragraphs = text.split("\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        words = para.split()
        word_count = len(words)

        # If paragraph itself is too big → split it
        if word_count > max_words:
            for i in range(0, word_count, max_words - overlap):
                chunk = " ".join(words[i:i + max_words])
                chunks.append(chunk)
            continue

        # If adding paragraph exceeds limit → push chunk
        if current_length + word_count > max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.extend(words)
        current_length += word_count

    # Add last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def run_document_pipeline(file_path):
    print("🔹 Starting document pipeline...")

    # Step 1: Extract
    text = extract_text(file_path)
    print(f"✅ Extracted text length: {len(text)}")

    # Step 2: Clean
    cleaned = clean_text(text)
    print(f"✅ Cleaned text length: {len(cleaned)}")

    # Step 3: Chunk
    chunks = chunk_text(cleaned)
    print(f"✅ Total chunks created: {len(chunks)}")

    return chunks