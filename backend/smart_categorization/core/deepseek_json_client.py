"""
DeepSeek Chat Completions (JSON mode) for transaction categorization fallback.

Uses the OpenAI-compatible API at DEEPSEEK_BASE_URL with DEEPSEEK_API_KEY.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class DeepSeekJsonError(RuntimeError):
    """Errors from DeepSeek JSON chat-completions calls."""


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _extract_json_object(text: str) -> Optional[dict]:
    """Extract the first JSON object from a text blob (defensive against stray text)."""
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


class DeepSeekJsonClient:
    """
    Client for DeepSeek chat completions with JSON response format.
    Used by LLMCategorizer when ML confidence is low or for PDF-only flows.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: int = 20,
        enabled: bool | None = None,
    ):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            self.client = None
            self.enabled = False
        else:
            ds_base = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            timeout_s = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
            self.client = OpenAI(api_key=api_key, base_url=ds_base, timeout=timeout_s)
            self.model = (
                model
                or os.getenv("DEEPSEEK_JSON_MODEL")
                or os.getenv("DEEPSEEK_MODEL")
                or "deepseek-chat"
            )
            # Allow disabling LLM categorization without removing the API key
            if enabled is None:
                self.enabled = _env_bool("LLM_CATEGORIZATION_ENABLED", True)
            else:
                self.enabled = bool(enabled)

        self.timeout_s = timeout_s

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Call DeepSeek chat completions and return a parsed JSON object."""
        if not self.enabled or not self.client:
            raise DeepSeekJsonError(
                "DeepSeek client is disabled or DEEPSEEK_API_KEY is missing. "
                "Set DEEPSEEK_API_KEY and LLM_CATEGORIZATION_ENABLED=true (default)."
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
            raise DeepSeekJsonError(f"DeepSeek API request failed: {e}")

        content = (response.choices[0].message.content or "").strip()

        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1].strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()

        obj = _extract_json_object(content)
        if obj is None:
            try:
                obj = json.loads(content)
            except Exception as e:
                raise DeepSeekJsonError(
                    f"Could not parse DeepSeek JSON response: {str(e)} | raw: {content[:200]}"
                )

        if not isinstance(obj, dict):
            raise DeepSeekJsonError(
                f"DeepSeek JSON response is not an object as expected: {str(obj)[:200]}"
            )

        return obj
