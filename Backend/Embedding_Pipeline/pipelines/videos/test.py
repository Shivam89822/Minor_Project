import argparse
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DEFAULT_VIDEO_PATH = os.path.join(BACKEND_DIR, "sampleVideo.mp4")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipelines.videos.pipeline import run_video_pipeline



def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the video pipeline and print structured records."
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
