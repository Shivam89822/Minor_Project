import json
import os
import sys

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
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        return 1

    records = result["chunks"]

    print("\n--- SAMPLE CHUNKS ---")
    for record in records[:3]:
        preview_record = dict(record)
        preview_record["text"] = record["text"][:200] + ("..." if len(record["text"]) > 200 else "")
        print(json.dumps(preview_record, indent=2))

    print("\nTotal chunks:", len(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
