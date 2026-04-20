import os
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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

def test_gemini_api():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_KEY")
    if not api_key:
        print("ERROR: No Gemini API key found in environment variables.")
        return

    print(f"API Key present: {bool(api_key)}")

    request_body = {
        "system_instruction": {
            "parts": [{"text": "You are a helpful assistant."}]
        },
        "contents": [
            {
                "parts": [{"text": "Say 'Hello, Gemini API is working!'"}]
            }
        ],
        "generationConfig": {
            "candidateCount": 1,
            "maxOutputTokens": 50,
            "temperature": 0.2,
        },
    }

    request_url = GEMINI_API_URL + "?" + urlencode({"key": api_key})
    request = Request(
        request_url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        answer = _extract_answer_text(payload)
        print(f"SUCCESS: Gemini API responded: {answer}")
    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}")

if __name__ == "__main__":
    test_gemini_api()