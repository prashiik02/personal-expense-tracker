"""
Unified LLM provider for DeepSeek and Gemini.
Supports chunked processing: split data, call LLM per chunk, merge results.
"""
from __future__ import annotations

import os
import re
import json
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------

def prefer_gemini_for_chunked() -> bool:
    """Use Gemini for chunked/batch operations when key is set."""
    return bool(os.getenv("GEMINI_API_KEY"))


def get_chunked_provider() -> str:
    """Return 'gemini' or 'deepseek' for chunked operations. Prefer Gemini when key is set and model loads."""
    if os.getenv("GEMINI_API_KEY") and _get_gemini_model() is not None:
        return "gemini"
    return "deepseek"


def chunked_llm_available() -> bool:
    """True if at least one of Gemini or DeepSeek is configured for chunked use."""
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))


# ---------------------------------------------------------------------------
# DeepSeek (existing)
# ---------------------------------------------------------------------------

_deepseek_client = None


def _get_deepseek_client():
    global _deepseek_client
    if _deepseek_client is not None:
        return _deepseek_client
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    _deepseek_client = OpenAI(api_key=api_key, base_url=base_url)
    return _deepseek_client


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

_gemini_model = None


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        _gemini_model = genai.GenerativeModel(model_name)
        return _gemini_model
    except ImportError:
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Unified complete_text
# ---------------------------------------------------------------------------

def complete_text(
    provider: str,
    prompt: str,
    *,
    system: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> str:
    """
    Call the given provider (gemini | deepseek) and return raw text.
    """
    if provider == "gemini":
        model = _get_gemini_model()
        if model is None:
            raise RuntimeError("GEMINI_API_KEY is not set or Gemini model failed to load")
        full = (system or "") + "\n\n" + prompt if system else prompt
        try:
            response = model.generate_content(
                full,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            if response and response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}") from e

    elif provider == "deepseek":
        client = _get_deepseek_client()
        if client is None:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")
        model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            raise RuntimeError(f"DeepSeek API error: {e}") from e
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _extract_json_array(text: str) -> Optional[list]:
    if not text or not text.strip():
        return None
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts[1:]:
            p = p.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            if p.startswith("["):
                try:
                    return json.loads(p)
                except json.JSONDecodeError:
                    pass
            if p.startswith("{"):
                try:
                    obj = json.loads(p)
                    if isinstance(obj, dict) and "transactions" in obj:
                        return obj["transactions"]
                    if isinstance(obj, list):
                        return obj
                except json.JSONDecodeError:
                    pass
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "transactions" in parsed:
            return parsed["transactions"]
    except json.JSONDecodeError:
        pass
    return None


def complete_json_array(
    provider: str,
    prompt: str,
    *,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 0.1,
) -> list:
    """Call LLM and parse response as a JSON array. Returns [] on parse failure."""
    raw = complete_text(
        provider, prompt, system=system, max_tokens=max_tokens, temperature=temperature
    )
    arr = _extract_json_array(raw)
    return arr if isinstance(arr, list) else []


# ---------------------------------------------------------------------------
# Chunked batch categorization (Gemini or DeepSeek)
# ---------------------------------------------------------------------------

BATCH_CATEGORIZE_CHUNK_SIZE = int(os.getenv("BATCH_CATEGORIZE_CHUNK_SIZE", "15"))


def _taxonomy_summary() -> str:
    """Short taxonomy list for batch prompt."""
    try:
        from smart_categorization.data.taxonomy import CATEGORY_TAXONOMY
        lines = []
        for cat, data in (CATEGORY_TAXONOMY or {}).items():
            subs = (data.get("subcategories") or [])[:12]
            lines.append(f"- {cat}: {', '.join(subs)}")
        return "\n".join(lines) if lines else "Food & Dining, Shopping, Transportation, etc."
    except Exception:
        return "Food & Dining, Shopping, Transportation, Utilities & Bills, Entertainment, Healthcare, Financial Services, Transfers & Payments, etc."


def categorize_batch_via_llm_chunked(
    transactions: list[dict],
    *,
    chunk_size: int = BATCH_CATEGORIZE_CHUNK_SIZE,
) -> list[dict]:
    """
    Split transactions into chunks, send each chunk to LLM (Gemini or DeepSeek),
    get back category/subcategory/confidence per item, merge and return.
    Each element of transactions must have keys: transaction_id (or id), description, amount.
    Returns list of dicts with keys: category, subcategory, confidence (same order as input).
    """
    if not transactions:
        return []
    try:
        provider = get_chunked_provider()
    except Exception:
        provider = "deepseek"
    taxonomy = _taxonomy_summary()
    system = (
        "You are a transaction classifier for Indian personal finance. "
        "You MUST choose Category and Subcategory from the allowed taxonomy only. "
        "Return ONLY a valid JSON array with one object per transaction in the same order. "
        "Each object must have: index (0-based), category, subcategory, confidence (0-1)."
    )
    results = []
    for start in range(0, len(transactions), chunk_size):
        chunk = transactions[start : start + chunk_size]
        numbered = []
        for i, t in enumerate(chunk):
            tid = t.get("transaction_id") or t.get("id") or f"txn_{start + i}"
            desc = t.get("description") or ""
            amt = float(t.get("amount") or 0)
            numbered.append(f"{i}. [{tid}] {desc} | amount: {amt}")
        user = (
            "Classify each of these transactions. Use the same order (index 0, 1, 2, ...).\n\n"
            "Allowed taxonomy:\n" + taxonomy + "\n\n"
            "Rules: UPI/NEFT/IMPS to a person -> Transfers & Payments. Salary/income -> appropriate income bucket. "
            "Amount positive = debit/spend, negative = credit.\n\n"
            "Transactions:\n" + "\n".join(numbered) + "\n\n"
            "Return a JSON array of objects: [{ \"index\": 0, \"category\": \"...\", \"subcategory\": \"...\", \"confidence\": 0.9 }, ...]"
        )
        raw = complete_text(
            provider, user, system=system, max_tokens=2048, temperature=0.1
        )
        arr = _extract_json_array(raw)
        if not isinstance(arr, list):
            for _ in chunk:
                results.append({"category": "Shopping", "subcategory": "Electronics", "confidence": 0.3})
            continue
        by_idx = {int(item.get("index", i)): item for i, item in enumerate(arr) if isinstance(item, dict)}
        for i in range(len(chunk)):
            item = by_idx.get(i, {})
            cat = str(item.get("category") or "Shopping").strip()
            sub = str(item.get("subcategory") or "Electronics").strip()
            try:
                conf = float(item.get("confidence") or 0.5)
            except (TypeError, ValueError):
                conf = 0.5
            results.append({"category": cat, "subcategory": sub, "confidence": max(0, min(1, conf))})
    return results
