import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

print("=" * 60)
print(f"Running with Python: {sys.executable}")
try:
    import numpy
    print(f"NumPy Version: {numpy.__version__}")
except ImportError:
    print("NumPy is NOT installed in this environment.")
print("=" * 60)

from assistants.store import ensure_assistant, get_assistant_store, list_assistants
from ingestion.service import ingest_sources as ingest_assistant_sources
from ingestion.service import query_assistant_knowledge

DEFAULT_PDF_PATH = os.path.join(CURRENT_DIR, "sample.pdf")
DEFAULT_VIDEO_PATH = os.path.join(CURRENT_DIR, "sampleVideo.mp4")
ASSISTANTS_ROOT = os.path.join(CURRENT_DIR, "assistant_dbs")


def ingest_sources(assistant_name, file_paths, replace_existing=False):
    store_result = ingest_assistant_sources(
        assistants_root=ASSISTANTS_ROOT,
        assistant_name=assistant_name,
        sources=file_paths,
        replace_existing=replace_existing,
    )
    assistant = store_result["assistant"]

    print(
        f"Stored {store_result['stored_count']} chunks for assistant "
        f"'{assistant['assistant_name']}' in {assistant['persist_directory']}."
    )


def choose_assistant():
    assistants = list_assistants(ASSISTANTS_ROOT)
    if assistants:
        print("\nAvailable assistants:")
        for assistant in assistants:
            print(f"- {assistant['assistant_name']} ({assistant['assistant_id']})")
    else:
        print("\nNo assistants found yet.")

    return input("Assistant name: ").strip()


def choose_files():
    raw_value = input(
        "Enter file paths separated by commas, or press Enter for sample PDF/video: "
    ).strip()

    if not raw_value:
        return [DEFAULT_PDF_PATH, DEFAULT_VIDEO_PATH]

    return [path.strip() for path in raw_value.split(",") if path.strip()]


def interactive_query():
    assistant_name = choose_assistant()
    assistant = get_assistant_store(ASSISTANTS_ROOT, assistant_name)

    while True:
        question = input(
            f"\nAsk '{assistant['assistant_name']}' a question (or type 'exit'): "
        ).strip()
        if not question or question.lower() == "exit":
            print("Exiting.")
            break

        matches = query_assistant_knowledge(
            assistants_root=ASSISTANTS_ROOT,
            assistant_name=assistant["assistant_name"],
            question=question,
            top_k=2,
        )

        print("\nTop 2 matching chunks:")
        for index, match in enumerate(matches, start=1):
            preview = {
                "rank": index,
                "id": match["id"],
                "text": match["text"],
                "metadata": match["metadata"],
                "distance": match["distance"],
            }
            print(json.dumps(preview, indent=2))


def main():
    try:
        print("\n1. Create a new assistant knowledge base")
        print("2. Extend an existing assistant knowledge base")
        print("3. Query an assistant")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            assistant_name = input("New assistant name: ").strip()
            ingest_sources(
                assistant_name=assistant_name,
                file_paths=choose_files(),
                replace_existing=True,
            )
        elif choice == "2":
            assistant_name = choose_assistant()
            ingest_sources(
                assistant_name=assistant_name,
                file_paths=choose_files(),
                replace_existing=False,
            )
        elif choice == "3":
            interactive_query()
        else:
            print("Invalid option.")
            return 1

        return 0
    except ImportError as exc:
        print(exc)
        print("Install the missing package and run the script again.")
        return 1
    except Exception as exc:
        print(f"Test run failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
