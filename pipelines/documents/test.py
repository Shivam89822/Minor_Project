from pipelines.documents.pipeline import run_document_pipeline

file_path = "sample_3.pdf"  # change if needed

chunks = run_document_pipeline(file_path)

print("\n--- SAMPLE OUTPUT ---")
for i, chunk in enumerate(chunks[:3]):
    print(f"\nChunk {i+1}:\n{chunk[:200]}...")