from typing import List

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Splits text into overlapping chunks
    """

    words = text.split()
    chunks = []

    start = 0
    total_words = len(words)

    while start < total_words:
        end = start + chunk_size
        chunk = words[start:end]

        chunks.append(" ".join(chunk))

        # move with overlap
        start += (chunk_size - overlap)

    return chunks