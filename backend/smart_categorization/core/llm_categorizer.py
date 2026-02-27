from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from ..data.taxonomy import CATEGORY_TAXONOMY, CATEGORY_ALIASES
from .ollama_client import OllamaClient, OllamaError


@dataclass
class LLMCategoryResult:
    category: str
    subcategory: str
    confidence: float
    reasoning: str = ""


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _all_valid_pairs() -> set[tuple[str, str]]:
    pairs = set()
    for cat, data in CATEGORY_TAXONOMY.items():
        for sub in data.get("subcategories") or []:
            pairs.add((cat, sub))
    return pairs


_VALID_PAIRS = _all_valid_pairs()


def _apply_aliases(cat: str, sub: str) -> Optional[Tuple[str, str]]:
    """
    Map fuzzy aliases like "groceries" -> "Food & Dining > Groceries"
    """
    key = (cat or "").strip().lower()
    if key in CATEGORY_ALIASES:
        mapped = CATEGORY_ALIASES[key]
        if " > " in mapped:
            mc, ms = mapped.split(" > ", 1)
            return mc, ms
        # category-only alias
        if mapped in CATEGORY_TAXONOMY:
            # pick the first subcategory as fallback
            subs = CATEGORY_TAXONOMY[mapped]["subcategories"]
            return mapped, subs[0] if subs else "Unknown"
    return None


def _candidate_categories(description: str, limit: int = 6) -> List[str]:
    """
    Pick a small set of likely categories by keyword overlap to keep the LLM prompt small.
    Always includes Transfers & Payments and Shopping as common buckets.
    """
    desc = (description or "").lower()
    scored: List[Tuple[int, str]] = []
    for cat, data in CATEGORY_TAXONOMY.items():
        kws = data.get("keywords") or []
        score = sum(1 for k in kws if k and k.lower() in desc)
        scored.append((score, cat))
    scored.sort(key=lambda x: x[0], reverse=True)

    out = []
    for score, cat in scored:
        if cat not in out and (score > 0 or len(out) < 3):
            out.append(cat)
        if len(out) >= limit:
            break

    for must in ("Transfers & Payments", "Shopping"):
        if must in CATEGORY_TAXONOMY and must not in out:
            out.append(must)
    return out[:limit]


class LLMCategorizer:
    """
    Ollama-backed categorizer constrained to the existing taxonomy.
    Intended as a fallback when ML confidence is low.
    """

    def __init__(self):
        self.client = OllamaClient()
        self.min_confidence = _env_float("OLLAMA_MIN_CONFIDENCE", 0.62)

    def enabled(self) -> bool:
        return bool(self.client.enabled)

    def categorize(self, description: str, amount: float) -> Optional[LLMCategoryResult]:
        candidates = _candidate_categories(description, limit=6)
        candidate_lines = []
        for cat in candidates:
            subs = CATEGORY_TAXONOMY.get(cat, {}).get("subcategories") or []
            candidate_lines.append(f"- {cat}: {', '.join(subs[:18])}")

        system = (
            "You are a transaction classifier for Indian personal finance. "
            "You MUST choose a Category and Subcategory from the provided allowed taxonomy only. "
            "Return ONLY a JSON object with keys: category, subcategory, confidence, reasoning. "
            "confidence must be a number from 0 to 1."
        )

        prompt = (
            "Classify this transaction into the best Category and Subcategory.\n\n"
            f"Description: {description}\n"
            f"Amount: {amount} (positive=debit/spend, negative=credit/income)\n\n"
            "Allowed taxonomy (choose exactly one pair):\n"
            + "\n".join(candidate_lines)
            + "\n\n"
            "Rules:\n"
            "- If it is salary / income credit, choose the most suitable income-like bucket in taxonomy.\n"
            "- If it is a UPI/NEFT/IMPS transfer to a person, use Transfers & Payments.\n"
            "- If unsure, choose the closest match and reduce confidence.\n"
        )

        try:
            obj = self.client.generate_json(prompt, system=system, temperature=0.1)
        except OllamaError:
            return None

        cat = str(obj.get("category") or "").strip()
        sub = str(obj.get("subcategory") or "").strip()
        try:
            conf = float(obj.get("confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        reasoning = str(obj.get("reasoning") or "").strip()

        alias = _apply_aliases(cat, sub)
        if alias:
            cat, sub = alias

        if (cat, sub) not in _VALID_PAIRS:
            # If the model picked a valid category but wrong subcategory, fall back to first subcategory
            if cat in CATEGORY_TAXONOMY:
                subs = CATEGORY_TAXONOMY[cat].get("subcategories") or []
                if subs:
                    sub = subs[0]
            if (cat, sub) not in _VALID_PAIRS:
                return None

        if conf < self.min_confidence:
            return None

        return LLMCategoryResult(category=cat, subcategory=sub, confidence=max(0.0, min(1.0, conf)), reasoning=reasoning)

