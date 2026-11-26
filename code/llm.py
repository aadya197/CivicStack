import json
import re

from google import genai
from google.genai import types

from src import config

_client = None


def _get():
    global _client
    if _client is None:
        _client = genai.Client(http_options=types.HttpOptions(api_version="v1beta"))  # reads GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment
    return _client


def complete(user: str, system: str = "", max_tokens: int = 8192, temperature: float = 0.0,
             json_mode: bool = False) -> str:
    cfg = types.GenerateContentConfig(
        system_instruction=system or None,
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json" if json_mode else None,
    )
    resp = None
    for i, mdl in enumerate([config.LLM_MODEL] * 3 + ["gemini-3.5-flash-lite"]):
        try:
            resp = _get().models.generate_content(model=mdl, contents=user, config=cfg)
            break
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and i < 3:
                import time
                time.sleep(2 * (i + 1))
                continue
            raise
    return (resp.text or "").strip()


def extract_json(text: str):
    """Parse JSON from a model reply, tolerating code fences and stray prose."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"(\{.*\}|\[.*\])", t, flags=re.S)
        if m:
            return json.loads(m.group(1))
        raise


def json_call(user: str, system: str = "", max_tokens: int = 4096):
    return extract_json(complete(user, system=system, max_tokens=max_tokens, json_mode=True))
