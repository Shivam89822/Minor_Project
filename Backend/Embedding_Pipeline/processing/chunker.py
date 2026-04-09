def chunk_text(text, max_words=400, overlap=50):
    paragraphs = text.split("\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        words = para.split()
        word_count = len(words)

        if word_count > max_words:
            for i in range(0, word_count, max_words - overlap):
                chunk = " ".join(words[i:i + max_words])
                chunks.append(chunk)
            continue

        if current_length + word_count > max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.extend(words)
        current_length += word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks