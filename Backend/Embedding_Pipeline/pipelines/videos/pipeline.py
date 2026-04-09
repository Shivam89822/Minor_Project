import os

from pipelines.videos.extractor import extract_transcript
from processing.cleaner import clean_text


def format_timestamp(seconds):
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _split_segment(segment, max_words):
    text = clean_text(segment.get("text", ""))
    if not text:
        return []

    words = text.split()
    start = float(segment.get("start", 0.0))
    end = float(segment.get("end", start))

    if len(words) <= max_words:
        return [
            {
                "text": text,
                "start": start,
                "end": end,
                "word_count": len(words),
            }
        ]

    units = []
    duration = max(end - start, 0.0)

    for index in range(0, len(words), max_words):
        chunk_words = words[index:index + max_words]
        part_start_ratio = index / len(words)
        part_end_ratio = (index + len(chunk_words)) / len(words)
        units.append(
            {
                "text": " ".join(chunk_words),
                "start": start + (duration * part_start_ratio),
                "end": start + (duration * part_end_ratio),
                "word_count": len(chunk_words),
            }
        )

    return units


def chunk_video_segments(segments, max_words=400, overlap=50):
    units = []
    for segment in segments:
        units.extend(_split_segment(segment, max_words=max_words))

    if not units:
        return []

    chunks = []
    current_units = []
    current_words = 0

    for unit in units:
        if current_units and current_words + unit["word_count"] > max_words:
            chunks.append(_build_chunk(current_units))
            current_units, current_words = _get_overlap_units(current_units, overlap)

        current_units.append(unit)
        current_words += unit["word_count"]

    if current_units:
        chunks.append(_build_chunk(current_units))

    return chunks


def _build_chunk(units):
    return {
        "text": " ".join(unit["text"] for unit in units).strip(),
        "start": units[0]["start"],
        "end": units[-1]["end"],
        "start_timestamp": format_timestamp(units[0]["start"]),
        "end_timestamp": format_timestamp(units[-1]["end"]),
    }


def _get_overlap_units(units, overlap):
    if overlap <= 0:
        return [], 0

    overlap_units = []
    overlap_words = 0

    for unit in reversed(units):
        overlap_units.insert(0, unit)
        overlap_words += unit["word_count"]
        if overlap_words >= overlap:
            break

    return overlap_units, overlap_words


def run_video_pipeline(
    file_path,
    model_name="tiny",
    language=None,
    max_words=400,
    overlap=50,
    source_id=None,
):
    print("Starting video pipeline...")

    transcript = extract_transcript(
        file_path,
        model_name=model_name,
        language=language,
    )
    text = transcript["text"].strip()
    print(f"Extracted length: {len(text)}")

    cleaned = clean_text(text)
    print(f"Cleaned length: {len(cleaned)}")

    timestamped_chunks = chunk_video_segments(
        transcript.get("segments", []),
        max_words=max_words,
        overlap=overlap,
    )

    if not timestamped_chunks and cleaned:
        timestamped_chunks = [
            {
                "text": cleaned,
                "start": 0.0,
                "end": 0.0,
                "start_timestamp": format_timestamp(0.0),
                "end_timestamp": format_timestamp(0.0),
            }
        ]

    print(f"Total chunks: {len(timestamped_chunks)}")

    source_name = source_id or os.path.basename(file_path)
    records = []
    for index, chunk in enumerate(timestamped_chunks, start=1):
        records.append(
            {
                "id": f"video_chunk_{index}",
                "text": chunk["text"],
                "metadata": {
                    "source": source_name,
                    "type": "video",
                    "start": chunk["start"],
                    "end": chunk["end"],
                },
            }
        )

    return {
        "text": text,
        "cleaned_text": cleaned,
        "chunks": records,
    }
