import json
import os
import sys
from urllib.error import URLError

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DEFAULT_DOCUMENT_PATH = os.path.join(BACKEND_DIR, "sample.pdf")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipelines.documents.pipeline import run_document_pipeline



def main():
    try:
        result = run_document_pipeline(DEFAULT_DOCUMENT_PATH)
    except FileNotFoundError:
        print(f"Document file not found: {DEFAULT_DOCUMENT_PATH}")
        return 1
    except URLError:
        print(
            "The embedding model could not be downloaded. "
            "Connect to the internet once or use a model that is already cached."
        )
        return 1
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        return 1

    records = result["records"]

    print("\n--- SAMPLE RECORDS ---")
    for record in records[:3]:
        preview_record = {
            "id": record["id"],
            "text": record["text"][:200] + ("..." if len(record["text"]) > 200 else ""),
            "embedding": record["embedding"][:5],
            "metadata": record["metadata"],
        }
        print(json.dumps(preview_record, indent=2))

    print("\n--- EMBEDDING INFO ---")
    print("Total records:", len(records))
    print("Embedding dimension:", len(records[0]["embedding"]) if records else 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
