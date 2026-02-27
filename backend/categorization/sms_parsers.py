from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _to_iso_date(s: str) -> str:
    s = s.strip()
    for fmt in ("%d-%b-%y", "%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s  # best-effort


def parse_hdfc_sms(sms: str) -> dict:
    """
    Example:
    "HDFC Bank: Rs.450.00 debited from A/c XX1234 on 15-Jan-24 to VPA ZOMATO@ICICI Ref No 456789"
    """
    amount_match = re.search(r"Rs\.?([\d,]+(?:\.\d+)?)", sms, re.I)
    desc_match = re.search(r"to (?:VPA )?([A-Z0-9@]+)", sms, re.I)
    date_match = re.search(r"on (\d{2}-\w{3}-\d{2}|\d{2}/\d{2}/\d{2,4})", sms, re.I)

    amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0.0
    description = (
        desc_match.group(1)
        .replace("@", " ")
        .replace("ICICI", "")
        .replace("AXISBANK", "")
        .strip()
        if desc_match
        else sms[:60]
    )
    date = _to_iso_date(date_match.group(1)) if date_match else datetime.now().date().isoformat()
    return {"description": description, "amount": amount, "date": date}


def parse_sbi_sms(sms: str) -> dict:
    """
    Example:
    "SBI: Your A/c XX5678 is debited by Rs.1,200.00 on 16/01/24 to BIGBASKET ORDER."
    """
    amount_match = re.search(r"Rs\.?([\d,]+(?:\.\d+)?)", sms, re.I)
    date_match = re.search(r"on (\d{1,2}/\d{1,2}/\d{2,4})", sms, re.I)
    # SBI sometimes uses "to <DESC>" or "trf to <DESC>"
    desc_match = re.search(r"\bto\b\s+(.+?)(?:\.|Available|Avl|Bal|Ref|$)", sms, re.I)

    amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0.0
    description = desc_match.group(1).strip() if desc_match else sms[:60]
    date = _to_iso_date(date_match.group(1)) if date_match else datetime.now().date().isoformat()
    return {"description": description, "amount": amount, "date": date}

