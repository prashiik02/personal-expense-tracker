from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Literal


BankId = Literal["generic", "hdfc", "sbi", "icici", "axis"]


@dataclass
class ParsedTxn:
    transaction_id: str
    date: str  # YYYY-MM-DD
    description: str
    amount: float  # +debit, -credit
    currency: str = "INR"
    source_line: Optional[str] = None


_DATE_PATTERNS = [
    ("%d/%m/%Y", re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")),
    ("%d/%m/%y", re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2})\b")),
    ("%d-%b-%y", re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{2})\b")),
    ("%d-%b-%Y", re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b")),
    ("%b %d, %Y", re.compile(r"\b([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\b")),
]


def _to_iso_date(s: str) -> Optional[str]:
    s = s.strip()
    for fmt, _rx in _DATE_PATTERNS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _find_date(line: str) -> Optional[str]:
    for _fmt, rx in _DATE_PATTERNS:
        m = rx.search(line)
        if m:
            iso = _to_iso_date(m.group(1))
            if iso:
                return iso
    return None


_PHONEPE_ROW_RX = re.compile(
    r"^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})\s+(.+?)\s+(DEBIT|CREDIT)\s+₹\s*([\d,]+(?:\.\d+)?)$",
    re.I,
)
_PHONEPE_TXN_ID_ANYWHERE_RX = re.compile(r"\bTransaction ID\s+([A-Za-z0-9]+)\b")


def _looks_like_phonepe_statement(lines: List[str]) -> bool:
    head = "\n".join(lines[:120]).lower()
    if "support.phonepe.com/statement" in head:
        return True
    if "transaction statement for" in head:
        return True
    if any("transaction id" in ln.lower() for ln in lines[:200]) and any(
        ("debit" in ln.lower() or "credit" in ln.lower()) and "₹" in ln for ln in lines[:400]
    ):
        return True
    return False


def parse_phonepe_statement(text: str, currency: str = "INR") -> List[ParsedTxn]:
    """
    Parses PhonePe statement PDF text which has a repeated structure:
    Date line (e.g., "Feb 27, 2026") → time line → "DEBIT ₹150 Paid to ..." → "Transaction ID ..."
    """
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: List[ParsedTxn] = []
    last_txn: Optional[ParsedTxn] = None
    seq = 1

    for ln in lines:
        low = ln.lower()

        # Skip obvious non-transaction lines
        if low.startswith(("page ", "-- ")) or low.startswith("date transaction details"):
            continue
        if "system generated statement" in low or "support.phonepe.com/statement" in low:
            continue

        # Combined row line
        m = _PHONEPE_ROW_RX.match(ln)
        if m:
            iso = _to_iso_date(m.group(1))
            if not iso:
                continue
            desc = m.group(2).strip()
            typ = m.group(3).upper()
            amt_raw = m.group(4).replace(",", "")
            try:
                amt = float(amt_raw)
            except ValueError:
                continue
            signed_amt = amt if typ == "DEBIT" else -amt

            txn = ParsedTxn(
                transaction_id=f"PDF_{seq:05d}",
                date=iso,
                description=desc,
                amount=signed_amt,
                currency=currency,
                source_line=ln,
            )
            out.append(txn)
            last_txn = txn
            seq += 1
            continue

        # Transaction ID can appear on the time line
        m = _PHONEPE_TXN_ID_ANYWHERE_RX.search(ln)
        if m and last_txn:
            last_txn.transaction_id = m.group(1)
            continue

        # Description continuation (some merchants wrap to next line)
        if last_txn and not low.startswith(
            ("utr no", "paid by", "credited to", "jio prepaid reference id", "vi prepaid reference id")
        ):
            if len(ln) <= 140 and not _PHONEPE_ROW_RX.match(ln):
                last_txn.description = f"{last_txn.description} {ln}".strip()

    return out


def _parse_amount_token(tok: str) -> Optional[float]:
    t = tok.strip()
    t = t.replace(",", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _extract_numeric_tokens(line: str) -> List[float]:
    # capture numbers like 1,234.56 or 1234 or 1234.5
    raw = re.findall(r"(?<!\w)(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)(?!\w)", line)
    out: List[float] = []
    for r in raw:
        v = _parse_amount_token(r)
        if v is not None:
            out.append(v)
    return out


def _guess_debit_credit(line: str, nums: List[float]) -> Optional[float]:
    """
    Heuristics:
    - If line contains 'Cr'/'credit' => credit (negative)
    - If line contains 'Dr'/'debit' => debit (positive)
    - If 3+ numbers: often [debit, credit, balance] or [amount, balance]
      Choose the first non-zero among last 3 excluding balance-like largest last token.
    - Else: choose last numeric as amount (debit positive).
    """
    low = line.lower()
    is_credit = bool(re.search(r"\b(cr|credit)\b", low))
    is_debit = bool(re.search(r"\b(dr|debit)\b", low))

    if not nums:
        return None

    # Prefer explicit markers
    if is_credit and not is_debit:
        return -abs(nums[-1])
    if is_debit and not is_credit:
        return abs(nums[-1])

    # Common statement format includes running balance as last numeric.
    if len(nums) >= 2:
        # Assume last is balance; pick preceding non-zero as amount
        candidates = list(reversed(nums[:-1]))
        for c in candidates:
            if abs(c) > 0:
                return abs(c)
    return abs(nums[-1])


def parse_statement_text(text: str, bank: BankId = "generic", currency: str = "INR") -> List[ParsedTxn]:
    """
    Best-effort parsing from extracted PDF text.
    This is not perfect across all banks; we provide bank-specific hints via `bank`.
    """
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if _looks_like_phonepe_statement(lines):
        return parse_phonepe_statement(text, currency=currency)
    out: List[ParsedTxn] = []
    seq = 1

    for ln in lines:
        iso = _find_date(ln)
        if not iso:
            continue

        nums = _extract_numeric_tokens(ln)
        amt = _guess_debit_credit(ln, nums)
        if amt is None:
            continue

        # crude description extraction: remove date and trailing numeric columns
        desc = ln
        desc = re.sub(r"^\s*\S+\s+", "", desc)  # drop first token (likely date)
        # remove long runs of numbers at end
        desc = re.sub(r"(\s+[-]?\d[\d,]*(?:\.\d+)?){1,4}\s*$", "", desc).strip()
        if len(desc) < 3:
            continue

        # Bank-specific nudges: strip common noise
        if bank in ("hdfc", "icici", "axis"):
            desc = re.sub(r"\bUPI\b", "", desc, flags=re.I).strip()
        if bank == "sbi":
            desc = re.sub(r"\bIMPS\b|\bNEFT\b|\bUPI\b", "", desc, flags=re.I).strip()

        out.append(
            ParsedTxn(
                transaction_id=f"PDF_{seq:05d}",
                date=iso,
                description=desc,
                amount=amt,
                currency=currency,
                source_line=ln,
            )
        )
        seq += 1

    return out

