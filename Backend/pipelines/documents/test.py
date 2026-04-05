from pipelines.documents.pipeline import run_document_pipeline
from embeddings.embedder import embed_texts


file_path = "sample.pdf"  # change if needed

# Step 1: Run pipeline → get chunks
chunks = run_document_pipeline(file_path)

print("\n--- SAMPLE CHUNKS ---")
for i, chunk in enumerate(chunks[:3]):
    print(f"\nChunk {i+1}:\n{chunk[:200]}...")


# Step 2: Generate embeddings (use small subset for testing)
test_chunks = chunks[:5]   # keep small for speed

embeddings = embed_texts(test_chunks)

print("\n--- EMBEDDING INFO ---")
print("Total embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))

print("\nSample embedding (first 5 values):")
print(embeddings[0][:5])