import os
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
OUT_OF_CONTEXT_REPLY = "Out of context."
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _citation_line(match):
    metadata = match.get("metadata") or {}
    source = metadata.get("source", "Unknown source")
    page = metadata.get("page")
    start = metadata.get("start")
    end = metadata.get("end")

    parts = [source]
    if page is not None:
        parts.append(f"page {page}")
    if start is not None:
        parts.append(f"start {start}")
    if end is not None:
        parts.append(f"end {end}")

    return " | ".join(parts)


def _build_context(matches):
    sections = []

    for index, match in enumerate(matches, start=1):
        text = " ".join((match.get("text") or "").split()).strip()
        if not text:
            continue

        sections.append(
            f"[Context {index}]\n"
            f"Source: {_citation_line(match)}\n"
            f"Text: {text}"
        )

    return "\n\n".join(sections)


def _should_expand_answer(question):
    lowered = (question or "").lower()
    return any(
        phrase in lowered
        for phrase in (
            "what is",
            "what are",
            "explain",
            "describe",
            "difference",
            "compare",
            "define",
            "why",
            "how",
        )
    )


def _is_too_short(answer_text):
    words = answer_text.split()
    return len(words) < 20 or len(answer_text) < 120


def _extract_answer_text(payload):
    answer_text = ""
    candidates = payload.get("candidates") or []
    if candidates:
        candidate_content = (candidates[0].get("content") or {}).get("parts") or []
        answer_text = " ".join(
            part.get("text", "").strip()
            for part in candidate_content
            if part.get("text")
        )

    return " ".join(answer_text.strip().split())


def _call_gemini(api_key, model_name, system_instruction, user_prompt, max_output_tokens=320):
    request_body = {
        "system_instruction": {
            "parts": [
                {
                    "text": system_instruction,
                }
            ]
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": user_prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "candidateCount": 1,
            "maxOutputTokens": max_output_tokens,
            "temperature": 0.2,
        },
    }
    request_url = (
        GEMINI_API_URL.format(model=model_name)
        + "?"
        + urlencode({"key": api_key})
    )
    request = Request(
        request_url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return _extract_answer_text(payload)


def generate_grounded_answer(question, matches):
    api_key = (
        os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_KEY", "").strip()
    )
    if not api_key:
        return {
            "answer": None,
            "used": False,
            "reason": "missing_api_key",
        }

    context = _build_context(matches)
    if not context:
        return {
            "answer": OUT_OF_CONTEXT_REPLY,
            "used": True,
            "reason": "no_context",
        }

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL

    system_instruction = (
        "You are an expert assistant. "
        "The provided context is the retrieved raw response from the assistant's knowledge base. "
        "Use it only as the source for your answer. "
        f"If the context does not contain the answer, reply exactly: {OUT_OF_CONTEXT_REPLY} "
        "Do not copy the context verbatim. Instead, synthesize and polish it into a longer, clear, fully formed final answer. "
        "Select only the necessary details from the retrieved response and omit irrelevant fragments or timestamps. "
        "Ignore OCR noise, repeated fragments, broken formatting, and obviously corrupted text. "
        "Do not invent facts or add unsupported information. "
        "Always answer in complete sentences. Never return sentence fragments. "
        "If the question asks for an explanation, definition, or comparison, provide a detailed, easy-to-understand response."
    )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Retrieved response:\n{context}\n\n"
        "Using only the retrieved response, provide a polished and organized final answer for the user. "
        "Do not copy raw text from the retrieved response. "
        "Do not include timestamps or metadata in the answer. "
        "Use only the necessary context details; omit irrelevant or redundant fragments. "
        "If the retrieved response is unrelated to the question, reply exactly: Out of context. "
        "Make the answer complete, clear, and well-structured."
    )

    try:
        answer_text = _call_gemini(
            api_key=api_key,
            model_name=model_name,
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_output_tokens=1000,
        )

        if _should_expand_answer(question) and _is_too_short(answer_text) and answer_text != OUT_OF_CONTEXT_REPLY:
            structured_system_instruction = (
                "You are an expert assistant. "
                "The provided context is the retrieved raw response from the assistant's knowledge base. "
                "Use it only as the source for your answer. "
                f"If the context does not contain enough information, reply exactly: {OUT_OF_CONTEXT_REPLY} "
                "Do not copy the context verbatim. Synthesize and polish it into a clear, professional final answer. "
                "Select only the necessary details and omit irrelevant fragments or timestamps. "
                "Do not invent facts or add unsupported information. Ignore OCR noise and broken fragments. "
                "Answer in 2 paragraphs. "
                "Paragraph 1: direct definition or core answer. "
                "Paragraph 2: explanation, difference, significance, or example supported by the context."
            )
            structured_user_prompt = (
                f"Question:\n{question}\n\n"
                f"Retrieved response:\n{context}\n\n"
                "Task:\n"
                "Provide a polished, detailed final answer using only the retrieved response.\n"
                "Do not include timestamps or metadata in the answer.\n"
                "Use only the necessary context details; omit irrelevant or redundant fragments.\n"
                "If this is a theory, definition, or comparison question, explain it clearly and thoroughly.\n"
                "Do not give a one-line summary.\n"
                "If unrelated or unsupported, reply exactly: Out of context."
            )
            answer_text = _call_gemini(
                api_key=api_key,
                model_name=model_name,
                system_instruction=structured_system_instruction,
                user_prompt=structured_user_prompt,
                max_output_tokens=1000,
            )
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            "answer": None,
            "used": False,
            "reason": f"api_error: {exc}",
        }

    answer_text = " ".join(answer_text.strip().split())
    if not answer_text:
        return {
            "answer": OUT_OF_CONTEXT_REPLY,
            "used": True,
            "reason": "empty_response",
        }

    normalized = answer_text.lower().strip(". ")
    if normalized in {"out of context", "out-of-context", "not in context"}:
        return {
            "answer": OUT_OF_CONTEXT_REPLY,
            "used": True,
            "reason": "out_of_context",
        }

    return {
        "answer": answer_text,
        "used": True,
        "reason": "gemini_success",
        "model": model_name,
    }
