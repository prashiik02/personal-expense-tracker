import os
import json
import re

from groq import Groq
from dotenv import load_dotenv


load_dotenv()

_client = None


def _get_client() -> Groq | None:
    """Lazy Groq client using GROQ_API_KEY."""
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    _client = Groq(api_key=api_key)
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


def parse_bank_statement_with_llm(raw_text: str) -> list[dict]:
    """
    Uses Groq LLM as fallback parser for unknown bank statement formats.
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
        print("Groq API error: GROQ_API_KEY is not set.")
        return []

    model_name = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"

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
            print("Groq LLM: could not extract JSON array from model output")
            return []

        if not isinstance(transactions, list):
            return []

        return transactions

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"Groq API error: {e}")
        return []


def categorize_transaction_with_llm(narration: str) -> dict:
    """
    Uses Groq to categorize a transaction when rule-based categorization fails.
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
            print("Categorization error: GROQ_API_KEY is not set.")
            return {
                "category": "others",
                "subcategory": "unknown",
                "merchant_name": None,
                "is_p2p": False,
                "confidence": 0.0,
            }

        model_name = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"

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

