import json
import re

from google import genai
from google.genai import types

from src import config

_client = None


def _get():
    global _client
    if _client is None:
        _client = genai.Client()  # reads GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment
    return _client


def complete(user: str, system: str = "", max_tokens: int = 2048, temperature: float = 0.0,
             json_mode: bool = False) -> str:
    cfg = types.GenerateContentConfig(
        system_instruction=system or None,
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json" if json_mode else None,
    )
    resp = _get().models.generate_content(model=config.LLM_MODEL, contents=user, config=cfg)
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
