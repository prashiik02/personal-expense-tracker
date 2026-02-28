import os
import json
import re

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client: OpenAI | None = None

# Chunk size for splitting long PDF text (chars). Gemini/DeepSeek context is large; we split to avoid timeouts.
PDF_PARSE_CHUNK_CHARS = int(os.getenv("PDF_PARSE_CHUNK_CHARS", "35000"))


def _get_client() -> OpenAI | None:
    """Lazy DeepSeek client using DEEPSEEK_API_KEY."""
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def _extract_json_array(text: str) -> list | None:
    """
    Extract a JSON array from model output. Handles markdown fences, extra text,
    wrapped objects like {"transactions": [...]}, and raw arrays.
    """
    if not text or not text.strip():
        return None
    text = text.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if "```" in text:
        parts = text.split("```")
        for p in parts[1:]:  # skip part before first ```
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
                    if isinstance(obj, list):
                        return obj
                    if isinstance(obj, dict) and "transactions" in obj:
                        return obj["transactions"]
                    if isinstance(obj, dict):
                        return [obj]
                except json.JSONDecodeError:
                    pass

    # Try to find first JSON array in text
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Try parsing whole text as JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "transactions" in parsed:
            return parsed["transactions"]
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    return None


def _parse_one_chunk(raw_chunk: str, provider: str) -> list[dict]:
    """Parse a single chunk of statement text with the given provider (gemini | deepseek)."""
    system_prompt = """You are a financial document parser for Indian bank statements (SBI, HDFC, ICICI, Axis, Kotak, UCO, etc.).
Extract every transaction from the text. Return ONLY a valid JSON array—no explanation, no markdown, no code blocks.
Handle tables, multi-column layouts, and varying formats."""
    user_prompt = """Extract ALL transactions from this bank statement text.

Return a JSON array. Each transaction must have:
- date: string in YYYY-MM-DD format
- amount: float (always positive)
- type: "debit" or "credit"
- narration: string (full description)
- balance: float or null
- reference: string or null (UTR/ref if present)

Handle Indian number format (1,23,456.78 = 123456.78). Dr/Cr = debit/credit.

Bank statement text:
""" + raw_chunk
    try:
        from llm_providers import complete_text
        raw_output = complete_text(
            provider, user_prompt, system=system_prompt, max_tokens=8192, temperature=0.1
        )
        transactions = _extract_json_array(raw_output)
        return transactions if isinstance(transactions, list) else []
    except Exception as e:
        print(f"LLM parse chunk error ({provider}): {e}")
        return []


def parse_bank_statement_with_llm_chunked(raw_text: str) -> list[dict]:
    """
    Split long statement text into chunks, parse each chunk with LLM (Gemini or DeepSeek), merge and dedupe.
    Uses Gemini when GEMINI_API_KEY is set; otherwise DeepSeek.
    """
    if not raw_text or not raw_text.strip():
        return []
    try:
        from llm_providers import get_chunked_provider
        provider = get_chunked_provider()
    except Exception:
        provider = "deepseek"
    text = raw_text.strip()
    if len(text) <= PDF_PARSE_CHUNK_CHARS:
        return _parse_one_chunk(text, provider)
    all_txns = []
    seen = set()
    start = 0
    while start < len(text):
        end = min(start + PDF_PARSE_CHUNK_CHARS, len(text))
        chunk = text[start:end]
        if end < len(text):
            # Try to break at a newline to avoid cutting mid-line
            last_nl = chunk.rfind("\n")
            if last_nl > PDF_PARSE_CHUNK_CHARS // 2:
                end = start + last_nl + 1
                chunk = text[start:end]
        chunk_txns = _parse_one_chunk(chunk, provider)
        for t in chunk_txns:
            key = (
                str(t.get("date") or ""),
                float(t.get("amount") or 0),
                str(t.get("narration") or t.get("description") or ""),
            )
            if key not in seen:
                seen.add(key)
                all_txns.append(t)
        start = end
    return all_txns


def parse_bank_statement_with_llm(raw_text: str) -> list[dict]:
    """
    Uses DeepSeek LLM as fallback parser for unknown bank statement formats.
    Works with any PDF whose text has been extracted (SBI, HDFC, ICICI, Axis, etc.).
    Returns list of normalized transaction dicts.
    """
    if not raw_text or not raw_text.strip():
        return []

    # Truncate very long text to avoid token limits; keep first N chars
    max_chars = 120_000
    text_to_send = raw_text.strip()
    if len(text_to_send) > max_chars:
        text_to_send = text_to_send[:max_chars] + "\n\n[... text truncated ...]"

    system_prompt = """You are a financial document parser for Indian bank statements (SBI, HDFC, ICICI, Axis, Kotak, UCO, etc.).
Extract every transaction from the text. Return ONLY a valid JSON array—no explanation, no markdown, no code blocks.
Handle tables, multi-column layouts, and varying formats."""

    user_prompt = f"""Extract ALL transactions from this bank statement text.

Return a JSON array. Each transaction must have:
- date: string in YYYY-MM-DD format
- amount: float (always positive)
- type: "debit" or "credit"
- narration: string (full description)
- balance: float or null
- reference: string or null (UTR/ref if present)

Handle Indian number format (1,23,456.78 = 123456.78). Dr/Cr = debit/credit.

Bank statement text:
{text_to_send}"""

    client = _get_client()
    if client is None:
        print("DeepSeek API error: DEEPSEEK_API_KEY is not set.")
        return []

    model_name = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=8192,
        )

        raw_output = (response.choices[0].message.content or "").strip()
        transactions = _extract_json_array(raw_output)

        if transactions is None:
            print("DeepSeek LLM: could not extract JSON array from model output")
            return []

        if not isinstance(transactions, list):
            return []

        return transactions

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        return []


def categorize_transaction_with_llm(narration: str) -> dict:
    """
    Uses DeepSeek to categorize a transaction when rule-based categorization fails.
    """

    system_prompt = """You are an Indian personal finance categorization engine.
    Return ONLY valid JSON, no explanation."""

    user_prompt = f"""Categorize this Indian bank transaction narration.

Narration: "{narration}"

Return JSON with exactly these fields:
- category: one of [groceries, food_delivery, fuel, transport, ott_subscription, 
  utilities, emi_loan, medical, education, investments, shopping, rent, 
  salary, atm_withdrawal, p2p_transfer, others]
- subcategory: string (more specific label, e.g. "netflix" or "swiggy" or "home_loan_emi")
- merchant_name: string or null (cleaned merchant name)
- is_p2p: boolean (true if this looks like a transfer to a person, not a business)
- confidence: float between 0.0 and 1.0"""

    try:
        client = _get_client()
        if client is None:
            print("Categorization error: DEEPSEEK_API_KEY is not set.")
            return {
                "category": "others",
                "subcategory": "unknown",
                "merchant_name": None,
                "is_p2p": False,
                "confidence": 0.0,
            }

        model_name = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=256,
        )

        raw_output = response.choices[0].message.content.strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]

        return json.loads(raw_output)

    except Exception as e:
        print(f"Categorization error: {e}")
        return {
            "category": "others",
            "subcategory": "unknown",
            "merchant_name": None,
            "is_p2p": False,
            "confidence": 0.0,
        }

