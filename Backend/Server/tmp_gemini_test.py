import os
import sys
sys.path.insert(0, os.getcwd())

from main import _call_gemini_api, GEMINI_API_KEY

print('KEY_PRESENT', GEMINI_API_KEY is not None)

try:
    out = _call_gemini_api('Summarize this text: Hello world.')
    print('OUTPUT', repr(out))
except Exception as exc:
    print('ERROR', type(exc).__name__, exc)
    import traceback
    traceback.print_exc()
