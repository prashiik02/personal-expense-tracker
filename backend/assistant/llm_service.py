import os
from typing import Optional

from openai import OpenAI

# Shared wrapper for talking to the DeepSeek LLM via its OpenAI‑compatible API.
# All conversational/report features call through this helper so swapping
# providers only requires changes in this file.

_client: Optional[OpenAI] = None


def _get_client() -> Optional[OpenAI]:
    """Lazy‑initialise a DeepSeek client using DEEPSEEK_API_KEY.

    Returns None when the key is missing so callers can surface a clear
    configuration error to the frontend.
    """

    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def ask(prompt: str, *, temperature: float = 0.1, max_tokens: int = 512) -> str:
    """Send a user-facing prompt to the LLM and return the model's reply.

    This is deliberately minimal; callers are expected to build the system
    / user prompt structure around it.
    """

    client = _get_client()
    if client is None:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the backend environment")

    # Default to DeepSeek chat model; override via env when needed.
    model_name = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # Preserve a simple, user-friendly error surface while logging details server-side.
        # (Flask will log the original exception; we only expose a short message.)
        msg = getattr(e, "message", None) or str(e)
        raise RuntimeError(f"DeepSeek API error: {msg}") from e
