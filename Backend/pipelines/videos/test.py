import argparse
import os
import sys
from urllib.error import URLError

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DEFAULT_VIDEO_PATH = os.path.join(BACKEND_DIR, "sampleVideo.mp4")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipelines.videos.pipeline import run_video_pipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the video pipeline and print sample chunks and embedding info."
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        default=DEFAULT_VIDEO_PATH,
        help="Path to the video file to process.",
    )
    parser.add_argument(
        "--model",
        default="tiny",
        help="Whisper model name to use for transcription.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language code for Whisper, for example 'en'.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        result = run_video_pipeline(
            file_path=args.file_path,
            model_name=args.model,
            language=args.language,
        )
    except FileNotFoundError:
        print(f"Video file not found: {args.file_path}")
        return 1
    except URLError:
        print(
            "Whisper could not download the requested model. "
            "Connect to the internet once or use a model that is already cached."
        )
        return 1
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        return 1

    chunks = result["chunks"]
    timestamped_chunks = result["timestamped_chunks"]
    embeddings = result["embeddings"]

    print("\n--- SAMPLE CHUNKS ---")
    for index, chunk in enumerate(timestamped_chunks[:3], start=1):
        print(
            f"\nChunk {index} "
            f"[{chunk['start_timestamp']} -> {chunk['end_timestamp']}]:\n"
            f"{chunk['text'][200]}..."
        )

    print("\n--- EMBEDDING INFO ---")
    print("Total embeddings:", len(embeddings))
    print("Embedding dimension:", len(embeddings[0]) if len(embeddings) else 0)

    if len(embeddings):
        print("\nSample embedding (first 5 values):")
        print(embeddings[0][:5])

    return 0


if __name__ == "__main__":
    sys.exit(main())
