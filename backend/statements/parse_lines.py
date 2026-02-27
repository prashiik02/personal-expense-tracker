from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Literal, Tuple


BankId = Literal["generic", "hdfc", "sbi", "icici", "axis", "uco"]


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
    ("%d-%m-%Y", re.compile(r"\b(\d{1,2}-\d{1,2}-\d{4})\b")),
    ("%d-%m-%y", re.compile(r"\b(\d{1,2}-\d{1,2}-\d{2})\b")),
    ("%d-%b-%y", re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{2})\b")),
    ("%d-%b-%Y", re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b")),
    ("%d%b,%Y", re.compile(r"\b(\d{1,2}[A-Za-z]{3},\d{4})\b")),
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


def _is_valid_date(iso: str) -> bool:
    """Reject invalid dates like 2025-12-84 (day > 31)."""
    if not iso or len(iso) < 10:
        return False
    try:
        parts = iso.split("-")
        if len(parts) != 3:
            return False
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        if m < 1 or m > 12 or d < 1 or d > 31:
            return False
        datetime(y, m, d)  # raises if invalid (e.g. Feb 30)
        return True
    except (ValueError, TypeError):
        return False


def _is_valid_description(desc: str) -> bool:
    """Reject descriptions that are purely numeric (amounts misparsed as description)."""
    if not desc or len(desc.strip()) < 3:
        return False
    stripped = re.sub(r"[\s,.]", "", desc)
    if not stripped:
        return False
    return not stripped.isdigit()


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


def _looks_like_gpay_statement(lines: List[str]) -> bool:
    head = "\n".join(lines[:80]).lower()
    if "transaction statement" in head and "gpay" in head:
        return True
    if "transaction statement" in head and "upitransactionid" in head:
        return True
    if "receivedfrom" in head or "paidto" in head:
        if "upitransactionid" in head or "transaction statement" in head:
            return True
    return False


_GPAY_ROW_RX = re.compile(
    r"(\d{1,2}[A-Za-z]{3},\d{4})\s+(Receivedfrom|Paidto)(.+?)\s*[₹Rs.]?\s*([\d,]+(?:\.\d+)?)",
    re.I,
)


def parse_gpay_statement(text: str, currency: str = "INR") -> List[ParsedTxn]:
    """
    Parses Google Pay (GPay) UCO Bank style statement.
    Format: 09Jan,2026 ReceivedfromSakshiDivekar ₹100
            or 09Jan,2026 PaidtoMRYOGESHSHIVKANTHBIRAJDAR ₹60
    """
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out: List[ParsedTxn] = []
    seq = 1

    for ln in lines:
        if "Date&time" in ln or "Transactionstatementperiod" in ln:
            continue
        if "Note:" in ln or "Page" in ln.lower():
            continue

        m = _GPAY_ROW_RX.search(ln)
        if not m:
            continue

        date_raw = m.group(1).strip()
        txn_type = m.group(2).strip().lower()
        desc = m.group(3).strip()
        amt_raw = m.group(4).replace(",", "")

        iso = _to_iso_date(date_raw)
        if not iso or not _is_valid_date(iso):
            continue

        try:
            amt = float(amt_raw)
        except ValueError:
            continue

        if amt <= 0:
            continue

        signed_amt = -amt if txn_type == "receivedfrom" else amt
        full_desc = f"{txn_type.upper()} {desc}".strip()
        if not _is_valid_description(full_desc):
            continue

        out.append(
            ParsedTxn(
                transaction_id=f"PDF_{seq:05d}",
                date=iso,
                description=full_desc,
                amount=signed_amt,
                currency=currency,
                source_line=ln,
            )
        )
        seq += 1

    return out


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


_UCO_HEADER_ALIASES = {
    "date": ["date", "txn date", "transaction date", "value date"],
    "particulars": ["particulars", "description", "narration", "remarks", "details"],
    "withdrawals": ["withdrawals", "withdrawal", "debit", "dr", "withdrawal amt"],
    "deposits": ["deposits", "deposit", "credit", "cr", "deposit amt"],
    "balance": ["balance", "closing balance", "available balance"],
}


def _find_col_index(headers: List[str], aliases: List[str]) -> int | None:
    for i, h in enumerate(headers):
        h_lower = (h or "").strip().lower()
        if h_lower in aliases or any(a in h_lower for a in aliases):
            return i
    return None


def parse_uco_table_rows(rows: List[List[str | None]], currency: str = "INR") -> List[ParsedTxn]:
    """
    Parse UCO / similar bank statement table: Date | Particulars | Withdrawals | Deposits | Balance.
    Returns list of ParsedTxn; skips invalid dates and numeric-only descriptions.
    """
    if not rows or len(rows) < 2:
        return []
    header_row = [str(c or "").strip() for c in rows[0]]
    date_idx = _find_col_index(header_row, _UCO_HEADER_ALIASES["date"])
    part_idx = _find_col_index(header_row, _UCO_HEADER_ALIASES["particulars"])
    wdr_idx = _find_col_index(header_row, _UCO_HEADER_ALIASES["withdrawals"])
    dep_idx = _find_col_index(header_row, _UCO_HEADER_ALIASES["deposits"])

    if date_idx is None or part_idx is None:
        return []
    if wdr_idx is None and dep_idx is None:
        return []

    def _amount(val: str | None) -> float:
        if val is None:
            return 0.0
        cleaned = re.sub(r"[₹Rs,\s]", "", str(val)).strip()
        try:
            return abs(float(cleaned))
        except ValueError:
            return 0.0

    out: List[ParsedTxn] = []
    seq = 1
    max_col = max(i for i in [date_idx, part_idx, wdr_idx, dep_idx] if i is not None)
    for row in rows[1:]:
        if not row or len(row) <= max_col:
            continue
        date_raw = str(row[date_idx] or "").strip()
        particulars = str(row[part_idx] or "").strip()
        wdr_val = _amount(row[wdr_idx]) if wdr_idx is not None and wdr_idx < len(row) else 0.0
        dep_val = _amount(row[dep_idx]) if dep_idx is not None and dep_idx < len(row) else 0.0

        iso = _to_iso_date(date_raw)
        if not iso or not _is_valid_date(iso):
            continue
        if not _is_valid_description(particulars):
            continue
        if wdr_val > 0 and dep_val > 0:
            continue  # skip ambiguous row
        if wdr_val <= 0 and dep_val <= 0:
            continue
        amount = wdr_val if wdr_val > 0 else -dep_val
        out.append(
            ParsedTxn(
                transaction_id=f"PDF_{seq:05d}",
                date=iso,
                description=particulars,
                amount=amount,
                currency=currency,
                source_line=None,
            )
        )
        seq += 1
    return out


def parse_sbi_yono_table_rows(rows: List[List[str | None]], currency: str = "INR") -> List[ParsedTxn]:
    """
    Parse SBI Yono statement table: 7 columns -
    Col 0: Date, Col 1: Value date, Col 2: Description (WDL TFR / DEP TFR / ATM WDL),
    Col 3: "-", Col 4: Debit, Col 5: Credit, Col 6: Balance.
    """
    if not rows or len(rows) < 2:
        return []
    out: List[ParsedTxn] = []
    seq = 1

    def _amount(v: str | None) -> float:
        if not v:
            return 0.0
        # Remove currency symbols and thousands commas, but keep decimal point
        cleaned = re.sub(r"[₹Rs,\s]", "", str(v)).strip()
        try:
            return abs(float(cleaned))
        except ValueError:
            return 0.0

    for row in rows[1:]:
        if not row or len(row) < 6:
            continue
        date_raw = str(row[0] or row[1] or "").strip()
        desc_raw = str(row[2] or "").strip().replace("\n", " ")
        debit_val = str(row[4] or "").strip() if len(row) > 4 else ""
        credit_val = str(row[5] or "").strip() if len(row) > 5 else ""

        if not date_raw or not desc_raw:
            continue

        iso = _to_iso_date(date_raw)
        if not iso or not _is_valid_date(iso):
            continue

        # WDL TFR, ATM WDL = debit; DEP TFR = credit
        desc_upper = desc_raw.upper()
        if "WDL TFR" in desc_upper or "ATM WDL" in desc_upper or "WDL" in desc_upper:
            amt = _amount(debit_val)
            if amt <= 0:
                continue
            signed_amt = amt
        elif "DEP TFR" in desc_upper or "DEP" in desc_upper:
            amt = _amount(credit_val)
            if amt <= 0:
                continue
            signed_amt = -amt
        else:
            continue

        if not _is_valid_description(desc_raw):
            continue

        out.append(
            ParsedTxn(
                transaction_id=f"PDF_{seq:05d}",
                date=iso,
                description=desc_raw,
                amount=signed_amt,
                currency=currency,
                source_line=None,
            )
        )
        seq += 1

    return out


def _looks_like_sbi_yono_table(rows: List[List[str | None]]) -> bool:
    """Detect SBI Yono table: 7 cols, WDL TFR or DEP TFR in col 2, dates in col 0/1."""
    if not rows or len(rows) < 2:
        return False
    first_data = rows[1]
    if len(first_data) < 6:
        return False
    desc = str(first_data[2] or "").upper()
    date0 = str(first_data[0] or "").strip()
    return ("WDL TFR" in desc or "DEP TFR" in desc or "ATM WDL" in desc) and bool(
        re.match(r"\d{1,2}/\d{1,2}/\d{4}", date0)
    )


def try_parse_tables(tables: List[List[List[str | None]]], currency: str = "INR") -> List[ParsedTxn]:
    """Try to parse any table as UCO-style or SBI Yono bank statement."""
    sbi_yono_all: List[ParsedTxn] = []
    for table in tables:
        if _looks_like_sbi_yono_table(table):
            parsed = parse_sbi_yono_table_rows(table, currency=currency)
            if parsed:
                # Re-number transaction IDs across pages
                base = len(sbi_yono_all) + 1
                for i, p in enumerate(parsed):
                    sbi_yono_all.append(
                        ParsedTxn(
                            transaction_id=f"PDF_{base + i:05d}",
                            date=p.date,
                            description=p.description,
                            amount=p.amount,
                            currency=p.currency,
                            source_line=p.source_line,
                        )
                    )
    if sbi_yono_all:
        return sbi_yono_all
    for table in tables:
        parsed = parse_uco_table_rows(table, currency=currency)
        if parsed:
            return parsed
    return []


def parse_statement_text(text: str, bank: BankId = "generic", currency: str = "INR") -> List[ParsedTxn]:
    """
    Best-effort parsing from extracted PDF text.
    This is not perfect across all banks; we provide bank-specific hints via `bank`.
    """
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if _looks_like_phonepe_statement(lines):
        return parse_phonepe_statement(text, currency=currency)
    if _looks_like_gpay_statement(lines):
        return parse_gpay_statement(text, currency=currency)
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

