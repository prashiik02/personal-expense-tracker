import os
from typing import Optional

from groq import Groq

try:
    from groq import RateLimitError, AuthenticationError, APIError
except ImportError:
    RateLimitError = AuthenticationError = APIError = None  # older SDK

# simple shared wrapper for talking to the Groq LLM; the existing
# statements/llm_fallback module has its own private _get_client(), but
# the new conversational and report features all need to invoke the model
# with custom prompts. moving the client logic into a common helper keeps
# the code DRY and makes it easier to swap out the provider later.

_client: Optional[Groq] = None


def _get_client() -> Optional[Groq]:
    """Lazy initialise a Groq client using GROQ_API_KEY from the
    environment. Returns None when the key is missing so callers can
    gracefully degrade in unit tests or on development machines.
    """

    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    _client = Groq(api_key=api_key)
    return _client


def ask(prompt: str, *, temperature: float = 0.1, max_tokens: int = 512) -> str:
    """Send a user-facing prompt to the LLM and return the model's reply.

    This is deliberately minimal; callers are expected to build the system
    / user prompt structure around it.  If the client isn't configured we raise
    an exception so that the API can return a 500 and the frontend can
    surface a helpful message.
    """

    client = _get_client()
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not set")

    model_name = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        if RateLimitError is not None and isinstance(e, RateLimitError):
            raise RuntimeError(
                "AI rate limit reached for today. Please try again in a few minutes, "
                "or check your Groq account limits at https://console.groq.com/settings/billing"
            ) from e
        if AuthenticationError is not None and isinstance(e, AuthenticationError):
            raise RuntimeError(
                "Invalid or expired Groq API key. Check GROQ_API_KEY in your .env file and https://console.groq.com"
            ) from e
        if getattr(e, "status_code", None) == 429:
            raise RuntimeError("AI rate limit reached. Please try again in a few minutes.") from e
        if getattr(e, "status_code", None) == 401:
            raise RuntimeError("Invalid Groq API key. Check GROQ_API_KEY in .env") from e
        if APIError is not None and isinstance(e, APIError):
            raise RuntimeError(f"Groq API error: {getattr(e, 'message', str(e))}") from e
        raise
