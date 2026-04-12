import os

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
}


def extract_transcript_from_video(file_path, model_name="tiny", language=None):
    try:
        import whisper
    except ImportError as exc:
        raise ImportError(
            "Video transcription dependencies are not ready. "
            f"Whisper import failed with: {exc}"
        ) from exc

    model = whisper.load_model(model_name)
    result = model.transcribe(
        file_path,
        fp16=False,
        language=language,
        verbose=False,
    )
    return result


def extract_text_from_video(file_path, model_name="tiny", language=None):
    result = extract_transcript_from_video(
        file_path=file_path,
        model_name=model_name,
        language=language,
    )
    return result["text"].strip()


def validate_video_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Video file does not exist")

    _, extension = os.path.splitext(file_path)
    if extension.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError("Unsupported video format")


def extract_transcript(file_path, model_name="tiny", language=None):
    validate_video_file(file_path)

    return extract_transcript_from_video(
        file_path=file_path,
        model_name=model_name,
        language=language,
    )


def extract_text(file_path, model_name="tiny", language=None):
    validate_video_file(file_path)

    return extract_text_from_video(
        file_path=file_path,
        model_name=model_name,
        language=language,
    )
