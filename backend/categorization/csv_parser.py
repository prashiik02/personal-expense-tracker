from __future__ import annotations

import csv
import json
from io import StringIO
from typing import List, Dict, Any


def _get(row: Dict[str, Any], *keys: str):
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def parse_transactions_csv(csv_text: str) -> List[dict]:
    """
    Parses CSV into a list of RawTransaction-like dicts.

    Expected headers (flexible):
    - transaction_id / id
    - date
    - description / narration
    - amount
    - currency (optional)
    - line_items (optional JSON)
    """
    f = StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    out: List[dict] = []
    for i, row in enumerate(reader):
        transaction_id = _get(row, "transaction_id", "id") or f"ROW_{i+1}"
        date = _get(row, "date", "txn_date", "transaction_date") or ""
        description = _get(row, "description", "narration", "remarks") or ""
        amount_raw = _get(row, "amount", "debit", "value") or "0"
        currency = _get(row, "currency") or "INR"

        try:
            amount = float(str(amount_raw).replace(",", "").strip())
        except ValueError:
            amount = 0.0

        line_items = None
        li_raw = _get(row, "line_items")
        if li_raw:
            try:
                line_items = json.loads(li_raw)
            except Exception:
                line_items = None

        out.append(
            {
                "transaction_id": str(transaction_id),
                "date": str(date),
                "description": str(description),
                "amount": amount,
                "currency": str(currency),
                "line_items": line_items,
            }
        )
    return out

