"""
engine/gemini_helper.py

Fix 7 (NETRA Fix Guide) — shared Gemini model-selection helper.

Both engine/netra_engine.py (forensic SOS reports, image+text) and
backend/main.py (/api/chat, text-only) import this instead of each
hardcoding its own model name and duplicating the auto-discovery logic.

Uses the 'google-genai' SDK (NOT the deprecated 'google-generativeai'):
  - genai.Client(api_key=...)         instead of genai.configure(api_key=...)
  - client.models.list()              instead of genai.list_models()
  - Model.supported_actions (list[str]) instead of .supported_generation_methods

Same auto-discovery pattern as VyomAcre's ai_api.py:
  1. List every model the API key can currently use.
  2. Rank "flash" models first, newest version number first within that group.
  3. Cache the last model that actually worked; try it first on the next call.
  4. On a 404 "no longer available" error, mark that model dead for this
     process and move on to the next candidate - the same request doesn't
     fail just because one model name aged out.
  5. Bounded retry: max 5 candidates per call.
  6. Non-404 errors (bad key, quota, network) fail fast - other model names
     would fail the exact same way, so there's no point trying them.

Install: pip install google-genai
"""

import logging
import re
from typing import Optional, Sequence, Union

from google import genai
from google.genai import types

logger = logging.getLogger("netra.gemini_helper")

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)?)")

_client = None
_dead_models: set = set()      # model names confirmed 404-retired this process
_working_model_name: str = ""  # last model name that actually succeeded


def get_client(api_key: str):
    """Creates the genai.Client once per process and reuses it."""
    global _client
    if _client is None:
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is empty - make sure load_dotenv() runs "
                "BEFORE this is called, and that .env actually has a valid key."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _ranked_models(client) -> list:
    """Every model supporting generateContent, 'flash' models first, newest
    version number first within that group, excluding anything already
    confirmed dead this process."""
    names = []
    for m in client.models.list():
        actions = getattr(m, "supported_actions", None) or []
        if "generateContent" not in actions:
            continue
        if m.name in _dead_models:
            continue
        names.append(m.name)

    def sort_key(name):
        is_flash = "flash" in name.lower()
        match = _VERSION_RE.search(name)
        version = float(match.group(1)) if match else -1.0
        return (0 if is_flash else 1, -version)  # flash first, newest version first

    names.sort(key=sort_key)
    return names


def _is_retired_error(exc) -> bool:
    text = str(exc).lower()
    return "404" in text and ("no longer available" in text or "not found" in text)


def generate(client, contents: Union[str, Sequence], max_candidates: int = 5):
    """
    Tries the cached working model first, then ranked candidates, skipping
    any that come back 404-retired, up to max_candidates attempts total.

    `contents` follows the normal google-genai shape - a plain string for
    text-only (chatbot), or a list mixing a text prompt with
    types.Part.from_bytes(...) for multimodal (forensic snapshot report).
    Use generate_with_image() below for the image case - it builds this
    list for you.

    Returns (text, model_used, error):
        success -> (answer_text: str, model_name: str, None)
        failure -> (None, None, error_message: str)
    """
    global _working_model_name

    if _working_model_name:
        ordered = [_working_model_name] + [n for n in _ranked_models(client) if n != _working_model_name]
    else:
        ordered = _ranked_models(client)

    if not ordered:
        return None, None, "No usable Gemini models found for this API key."

    last_error = ""
    for model_name in ordered[:max_candidates]:
        try:
            response = client.models.generate_content(model=model_name, contents=contents)
            text = (response.text or "").strip()
            if not text:
                last_error = f"{model_name} returned an empty response."
                continue

            _working_model_name = model_name  # remember what worked
            return text, model_name, None

        except Exception as exc:  # noqa: BLE001
            last_error = f"{exc.__class__.__name__}: {exc}"
            if _is_retired_error(exc):
                logger.warning("Gemini model '%s' is retired - trying the next candidate.", model_name)
                _dead_models.add(model_name)
                if model_name == _working_model_name:
                    _working_model_name = ""
                continue
            # Non-retirement error (bad key, quota, network) - other model
            # names would fail the same way, so stop here instead of
            # burning through the rest of the candidate list.
            logger.exception("Gemini call failed (non-retirement error) for model '%s'.", model_name)
            return None, None, last_error

    return None, None, last_error


def generate_with_image(client, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg", max_candidates: int = 5):
    """Convenience wrapper for netra_engine.py's forensic SOS reports - builds
    the multimodal [text, image] contents list for you."""
    contents = [prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
    return generate(client, contents, max_candidates=max_candidates)


def reset_cache():
    """Mainly for tests - clears the dead-model set and cached working model."""
    global _dead_models, _working_model_name
    _dead_models = set()
    _working_model_name = ""


if __name__ == "__main__":
    import os
    api_key = os.environ.get("GEMINI_API_KEY", "")
    print("GEMINI KEY:", "LOADED" if api_key else "NOT FOUND")
    if api_key:
        c = get_client(api_key)
        text, model, err = generate(c, "Say hello in one short sentence.")
        print(f"model used: {model}")
        print(f"error: {err}")
        print(f"response: {text}")