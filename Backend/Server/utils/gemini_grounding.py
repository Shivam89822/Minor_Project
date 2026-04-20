import os
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
OUT_OF_CONTEXT_REPLY = "Out of context."
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _retry_delay_from_error(error, attempt):
    retry_after = getattr(error, "headers", {}).get("Retry-After")
    if retry_after:
        try:
            return max(0.5, float(retry_after))
        except (TypeError, ValueError):
            pass

    # Keep retries short so chat stays responsive while still smoothing over
    # transient upstream failures.
    return min(6.0, 1.5 * (2 ** attempt))

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

    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return _extract_answer_text(payload)
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise

            delay_seconds = _retry_delay_from_error(exc, attempt)
            print(
                f"DEBUG: Gemini transient HTTP {exc.code}; "
                f"retrying in {delay_seconds:.1f}s (attempt {attempt + 2}/3)"
            )
            time.sleep(delay_seconds)
        except URLError as exc:
            last_error = exc
            if attempt == 2:
                raise

            delay_seconds = min(6.0, 1.5 * (2 ** attempt))
            print(
                f"DEBUG: Gemini network error; retrying in {delay_seconds:.1f}s "
                f"(attempt {attempt + 2}/3): {exc}"
            )
            time.sleep(delay_seconds)

    if last_error:
        raise last_error

    return ""


def generate_grounded_answer(question, matches):
    print(f"DEBUG: Question: {question}")
    print(f"DEBUG: Number of matches: {len(matches)}")
    for i, match in enumerate(matches[:3]):  # Log first 3 matches
        print(f"DEBUG: Match {i+1}: {match.get('text', '')[:200]}...")
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
    print(f"DEBUG: Built context length: {len(context)}")
    print(f"DEBUG: Context preview: {context[:500]}...")
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
        "Prefer a detailed and easy-to-understand explanation when the context supports it. "
        "When appropriate, begin with a direct answer and then elaborate with supporting details, explanation, distinctions, and examples drawn only from the provided context. "
        "If the user asks a definitional, conceptual, explanatory, or comparison question, answer in a moderately detailed way rather than a one-line summary."
    )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Retrieved response:\n{context}\n\n"
        "Using only the retrieved response, provide a polished and organized final answer for the user. "
        "Do not copy raw text from the retrieved response. "
        "Do not include timestamps or metadata in the answer. "
        "Use only the necessary context details; omit irrelevant or redundant fragments. "
        "If the retrieved response is unrelated to the question, reply exactly: Out of context. "
        "Make the answer complete, clear, and well-structured. "
        "Prefer 2 to 4 coherent paragraphs when enough context is available. "
        "If useful, explain the idea first and then elaborate on important details or differences."
    )

    try:
        print("DEBUG: Calling Gemini API...")
        answer_text = _call_gemini(
            api_key=api_key,
            model_name=model_name,
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_output_tokens=1000,
        )
        print(f"DEBUG: Gemini raw response: {answer_text}")

        if _should_expand_answer(question) and _is_too_short(answer_text) and answer_text != OUT_OF_CONTEXT_REPLY:
            structured_system_instruction = (
                "You are an expert assistant. "
                "The provided context is the retrieved raw response from the assistant's knowledge base. "
                "Use it only as the source for your answer. "
                f"If the context does not contain enough information, reply exactly: {OUT_OF_CONTEXT_REPLY} "
                "Do not copy the context verbatim. Synthesize and polish it into a clear, professional final answer. "
                "Select only the necessary details and omit irrelevant fragments or timestamps. "
                "Do not invent facts or add unsupported information. Ignore OCR noise and broken fragments. "
                "Answer in 2 to 4 paragraphs. "
                "Paragraph 1: direct definition or core answer. "
                "Remaining paragraphs: explanation, distinction, significance, example, or key supporting details from the context."
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
                "Prefer a fuller explanation with clear elaboration when the context supports it.\n"
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
        print(f"DEBUG: Gemini API error: {exc}")
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

    print(f"DEBUG: Final Gemini answer: {answer_text}")
    return {
        "answer": answer_text,
        "used": True,
        "reason": "gemini_success",
        "model": model_name,
    }
