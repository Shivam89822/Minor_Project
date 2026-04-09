from sentence_transformers import SentenceTransformer

try:
    model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
except Exception:
    model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts):
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    return embeddings
