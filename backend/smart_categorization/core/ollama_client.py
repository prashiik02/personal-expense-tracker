from __future__ import annotations

import json
import os
import re
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class OllamaError(RuntimeError):
    """
    Kept for backwards-compatibility. Now represents DeepSeek-related errors.
    """


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _extract_json_object(text: str) -> Optional[dict]:
    """
    Extract the first JSON object from a text blob (defensive against stray text).
    """
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


class OllamaClient:
    """
    Backwards-compatible client wrapper.

    Historically this talked to a local Ollama HTTP server, then to Groq.
    It is now implemented on top of the DeepSeek chat-completions API while
    preserving the same interface that the rest of the app expects.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: int = 20,
        enabled: bool | None = None,
    ):
        # DeepSeek configuration (OpenAI-compatible client)
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            # If there's no API key we treat the client as disabled.
            self.client = None
            self.enabled = False
        else:
            ds_base = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            self.client = OpenAI(api_key=api_key, base_url=ds_base)
            # Allow overriding default model via env, but keep a sensible default.
            self.model = (
                model
                or os.getenv("DEEPSEEK_JSON_MODEL")
                or os.getenv("DEEPSEEK_MODEL")
                or "deepseek-chat"
            )
            self.enabled = (
                _env_bool("OLLAMA_ENABLED", True) if enabled is None else bool(enabled)
            )

        # Retain timeout attribute in case future logic relies on it.
        self.timeout_s = timeout_s

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Call DeepSeek chat completions and return a parsed JSON object.
        """
        if not self.enabled or not self.client:
            raise OllamaError(
                "DeepSeek client is disabled or DEEPSEEK_API_KEY is missing. "
                "Set DEEPSEEK_API_KEY in your environment and ensure OLLAMA_ENABLED is not false."
            )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            raise OllamaError(f"DeepSeek API request failed: {e}")

        content = (response.choices[0].message.content or "").strip()

        # Be defensive: strip markdown fences if the model adds them.
        if content.startswith("```"):
            # Split off fences and optional "json" language hint
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1].strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()

        obj = _extract_json_object(content)
        if obj is None:
            # Try direct JSON parse as a fallback
            try:
                obj = json.loads(content)
            except Exception as e:
                raise OllamaError(
                    f"Could not parse DeepSeek JSON response: {str(e)} | raw: {content[:200]}"
                )

        if not isinstance(obj, dict):
            raise OllamaError(
                f"DeepSeek JSON response is not an object as expected: {str(obj)[:200]}"
            )

        return obj
