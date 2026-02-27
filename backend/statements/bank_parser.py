"""
Multi-Bank Statement Parser
Parses bank statements from different formats into a unified Transaction list.

All parsers output the same unified schema:
  {
    transaction_id, date, description, amount,
    transaction_type (debit/credit), bank, raw_row
  }
"""

import re
import os
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedTransaction:
    transaction_id: str
    date: str
    description: str
    amount: float
    transaction_type: str
    bank: str
    balance: Optional[float] = None
    raw_description: str = ""
    raw_row: dict = field(default_factory=dict)

    def to_pipeline_transaction(self):
        from smart_categorization.core.pipeline import Transaction

        signed_amount = self.amount if self.transaction_type == "debit" else -self.amount
        return Transaction(
            transaction_id=self.transaction_id,
            date=self.date,
            description=self.description,
            amount=signed_amount,
        )


DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%d-%b-%Y",
    "%d-%b-%y",
    "%d %b %y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%Y-%m-%dT%H:%M:%S",
]


def normalize_date(raw: str) -> str:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def normalize_amount(raw: str) -> float:
    raw = re.sub(r"[₹Rs.,\s]", "", str(raw)).strip()
    raw = raw.replace("(", "-").replace(")", "")
    try:
        return abs(float(raw))
    except ValueError:
        return 0.0


def make_id(date: str, desc: str, amount: float) -> str:
    key = f"{date}{desc[:20]}{amount}"
    return hashlib.md5(key.encode()).hexdigest()[:10]


class UCOBankParser:
    BANK_NAME = "UCO"

    DATE_COLS = ["date", "txn date", "transaction date", "value date", "posting date"]
    DESC_COLS = ["description", "narration", "particulars", "transaction details", "remarks"]
    DEBIT_COLS = ["debit", "withdrawal", "dr", "debit amount", "withdrawal amt"]
    CREDIT_COLS = ["credit", "deposit", "cr", "credit amount", "deposit amt"]
    AMOUNT_COLS = ["amount", "txn amount"]
    BALANCE_COLS = ["balance", "closing balance", "available balance"]

    def parse(self, rows: List[dict]) -> List[ParsedTransaction]:
        results: List[ParsedTransaction] = []
        cols = {k.lower().strip(): k for k in rows[0].keys()} if rows else {}

        date_col = self._find_col(cols, self.DATE_COLS)
        desc_col = self._find_col(cols, self.DESC_COLS)
        debit_col = self._find_col(cols, self.DEBIT_COLS)
        credit_col = self._find_col(cols, self.CREDIT_COLS)
        amt_col = self._find_col(cols, self.AMOUNT_COLS)
        bal_col = self._find_col(cols, self.BALANCE_COLS)

        for row in rows:
            try:
                date = normalize_date(str(row.get(date_col, "")))
                desc = self._clean_desc(str(row.get(desc_col, "")))
                bal = normalize_amount(str(row.get(bal_col, 0))) if bal_col else None

                if debit_col and credit_col:
                    dr_val = str(row.get(debit_col, "")).strip()
                    cr_val = str(row.get(credit_col, "")).strip()

                    if dr_val and dr_val not in ("", "0", "0.00", "-", "nan"):
                        amount = normalize_amount(dr_val)
                        txn_type = "debit"
                    elif cr_val and cr_val not in ("", "0", "0.00", "-", "nan"):
                        amount = normalize_amount(cr_val)
                        txn_type = "credit"
                    else:
                        continue

                elif amt_col:
                    raw_amt = str(row.get(amt_col, "0"))
                    amount = normalize_amount(raw_amt)
                    type_col = self._find_col(
                        cols, ["type", "dr/cr", "debit/credit", "txn type"]
                    )
                    if type_col:
                        indicator = str(row.get(type_col, "")).upper()
                        txn_type = "credit" if "CR" in indicator else "debit"
                    else:
                        txn_type = (
                            "credit"
                            if float(raw_amt.replace(",", "").strip() or 0) > 0
                            else "debit"
                        )
                else:
                    continue

                if amount == 0 or not desc:
                    continue

                results.append(
                    ParsedTransaction(
                        transaction_id=make_id(date, desc, amount),
                        date=date,
                        description=desc,
                        amount=amount,
                        transaction_type=txn_type,
                        bank=self.BANK_NAME,
                        balance=bal,
                        raw_description=str(row.get(desc_col, "")),
                        raw_row=dict(row),
                    )
                )
            except Exception:
                continue

        return results

    def _find_col(self, cols_lower: dict, candidates: list) -> Optional[str]:
        for c in candidates:
            if c in cols_lower:
                return cols_lower[c]
        return None

    def _clean_desc(self, desc: str) -> str:
        desc = re.sub(r"\s+", " ", desc).strip()
        desc = re.sub(r"^(UPI|NEFT|IMPS|RTGS)[/\-]", r"\1/", desc, flags=re.I)
        return desc.upper()


class SBIParser(UCOBankParser):
    BANK_NAME = "SBI"
    DATE_COLS = ["txn date", "date", "transaction date", "value date"]
    DESC_COLS = ["description", "particulars", "narration", "details"]
    DEBIT_COLS = ["debit", "withdrawal amt(inr)", "withdrawal", "dr"]
    CREDIT_COLS = ["credit", "deposit amt(inr)", "deposit", "cr"]


class PhonePeParser:
    BANK_NAME = "PhonePe"

    def parse(self, rows: List[dict]) -> List[ParsedTransaction]:
        results: List[ParsedTransaction] = []
        cols = {k.lower().strip(): k for k in rows[0].keys()} if rows else {}

        for row in rows:
            try:
                status = str(row.get(cols.get("status", ""), "")).strip().lower()
                if status and status not in ("completed", "success", "successful", ""):
                    continue

                date_raw = str(row.get(cols.get("date", ""), ""))
                date = normalize_date(date_raw)

                desc_key = next(
                    (cols[k] for k in cols if "detail" in k or "merchant" in k), None
                )
                desc = str(row.get(desc_key, "")).strip().upper() if desc_key else ""

                paid_key = next(
                    (cols[k] for k in cols if "paid" in k or "debit" in k or "out" in k),
                    None,
                )
                recv_key = next(
                    (cols[k] for k in cols if "received" in k or "credit" in k or "in" in k),
                    None,
                )

                paid_val = str(row.get(paid_key, "")).strip() if paid_key else ""
                recv_val = str(row.get(recv_key, "")).strip() if recv_key else ""

                if paid_val and paid_val not in ("", "0", "-", "nan", "0.00"):
                    amount = normalize_amount(paid_val)
                    txn_type = "debit"
                elif recv_val and recv_val not in ("", "0", "-", "nan", "0.00"):
                    amount = normalize_amount(recv_val)
                    txn_type = "credit"
                else:
                    continue

                desc = self._enrich_desc(desc, row, cols)
                if amount == 0:
                    continue

                results.append(
                    ParsedTransaction(
                        transaction_id=make_id(date, desc, amount),
                        date=date,
                        description=desc,
                        amount=amount,
                        transaction_type=txn_type,
                        bank=self.BANK_NAME,
                        raw_description=desc,
                        raw_row=dict(row),
                    )
                )
            except Exception:
                continue

        return results

    def _enrich_desc(self, desc: str, row: dict, cols: dict) -> str:
        upi_key = next((cols[k] for k in cols if "upi" in k), None)
        if upi_key:
            upi = str(row.get(upi_key, "")).strip()
            if upi and "@" in upi:
                desc = f"{desc} {upi}".strip()
        return desc.upper()


class HDFCParser(UCOBankParser):
    BANK_NAME = "HDFC"
    DATE_COLS = ["date", "value dt", "value date"]
    DESC_COLS = ["narration", "description", "particulars"]
    DEBIT_COLS = ["withdrawal amt.", "withdrawal amt", "withdrawal", "debit", "dr"]
    CREDIT_COLS = ["deposit amt.", "deposit amt", "deposit", "credit", "cr"]
    BALANCE_COLS = ["closing balance", "balance"]


class AxisParser(UCOBankParser):
    BANK_NAME = "Axis"
    DATE_COLS = ["tran date", "date", "transaction date", "value date"]
    DESC_COLS = ["particulars", "narration", "description"]
    DEBIT_COLS = ["debit", "dr", "withdrawal"]
    CREDIT_COLS = ["credit", "cr", "deposit"]


class ICICIParser(UCOBankParser):
    BANK_NAME = "ICICI"
    DATE_COLS = ["value date", "date", "transaction date"]
    DESC_COLS = ["transaction remarks", "narration", "description", "particulars"]
    DEBIT_COLS = ["withdrawal amount (inr )", "withdrawal amount", "debit", "dr"]
    CREDIT_COLS = ["deposit amount (inr )", "deposit amount", "credit", "cr"]


class KotakParser(UCOBankParser):
    BANK_NAME = "Kotak"
    DATE_COLS = ["transaction date", "date", "value date"]
    DESC_COLS = ["description", "narration", "particulars"]
    DEBIT_COLS = ["debit amount", "debit", "dr"]
    CREDIT_COLS = ["credit amount", "credit", "cr"]


class SMSParser:
    AMT_PATTERN = re.compile(r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)", re.I)
    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}[-/]\w{2,3}[-/]\d{2,4}|\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b"
    )
    TO_PATTERN = re.compile(
        r"(?:to|at|toward)\s+([A-Z0-9][A-Z0-9\s@._\-]{2,40}?)(?:\s+on|\s+ref|\s+for|\.|\Z)",
        re.I,
    )
    FROM_PATTERN = re.compile(
        r"(?:from)\s+([A-Z0-9][A-Z0-9\s@._\-]{2,40}?)(?:\s+on|\s+ref|\s+for|\.|\Z)",
        re.I,
    )

    DEBIT_SIGNALS = [
        "debited",
        "debit",
        "withdrawn",
        "withdrawal",
        "paid",
        "spent",
        "sent",
    ]
    CREDIT_SIGNALS = [
        "credited",
        "credit",
        "received",
        "deposited",
        "added",
        "refund",
    ]

    def parse_sms(self, sms: str, bank: str = "Unknown") -> Optional[ParsedTransaction]:
        sms_lower = sms.lower()
        txn_type = "unknown"
        for s in self.DEBIT_SIGNALS:
            if s in sms_lower:
                txn_type = "debit"
                break
        if txn_type == "unknown":
            for s in self.CREDIT_SIGNALS:
                if s in sms_lower:
                    txn_type = "credit"
                    break

        if txn_type == "unknown":
            return None

        amt_match = self.AMT_PATTERN.search(sms)
        if not amt_match:
            return None
        amount = normalize_amount(amt_match.group(1))

        date_match = self.DATE_PATTERN.search(sms)
        date = (
            normalize_date(date_match.group(1))
            if date_match
            else datetime.now().strftime("%Y-%m-%d")
        )

        if txn_type == "debit":
            name_match = self.TO_PATTERN.search(sms)
        else:
            name_match = self.FROM_PATTERN.search(sms)

        desc = name_match.group(1).strip().upper() if name_match else sms[:60].upper()

        upi_in_desc = re.search(r"[a-z0-9._]+@[a-z]+", sms, re.I)
        if upi_in_desc:
            desc = f"{desc} {upi_in_desc.group(0)}".strip()

        return ParsedTransaction(
            transaction_id=make_id(date, desc, amount),
            date=date,
            description=desc.upper(),
            amount=amount,
            transaction_type=txn_type,
            bank=bank,
            raw_description=sms[:200],
        )

    def parse_many(self, sms_list: List[str], bank: str = "Unknown") -> List[ParsedTransaction]:
        results: List[ParsedTransaction] = []
        for sms in sms_list:
            r = self.parse_sms(sms, bank)
            if r:
                results.append(r)
        return results


class BankStatementParser:
    PARSERS = {
        "UCO": UCOBankParser,
        "SBI": SBIParser,
        "PhonePe": PhonePeParser,
        "HDFC": HDFCParser,
        "Axis": AxisParser,
        "ICICI": ICICIParser,
        "Kotak": KotakParser,
    }

    BANK_SIGNATURES = {
        "PhonePe": {"transaction details", "paid out", "received in"},
        "HDFC": {"narration", "withdrawal amt.", "deposit amt.", "closing balance"},
        "SBI": {"txn date", "value date", "withdrawal amt(inr)", "deposit amt(inr)"},
        "Axis": {"tran date", "particulars"},
        "ICICI": {"transaction remarks", "withdrawal amount (inr )"},
        "Kotak": {"transaction date", "debit amount", "credit amount"},
        "UCO": {"narration", "debit", "credit", "balance"},
    }

    def detect_bank(self, columns: List[str]) -> str:
        cols_lower = {c.lower().strip() for c in columns}
        best_bank = "UCO"
        best_score = 0

        for bank, sig_cols in self.BANK_SIGNATURES.items():
            score = len(sig_cols & cols_lower)
            if score > best_score:
                best_score = score
                best_bank = bank

        return best_bank

    def parse_csv(self, filepath: str, bank: str = None, encoding: str = "utf-8") -> List[ParsedTransaction]:
        import csv

        rows: List[Dict[str, str]] = []
        for enc in [encoding, "utf-8", "latin-1", "cp1252", "utf-8-sig"]:
            try:
                with open(filepath, "r", encoding=enc) as f:
                    content = f.read()
                reader = csv.DictReader(content.splitlines())
                rows = [r for r in reader if any((v or "").strip() for v in r.values())]
                break
            except (UnicodeDecodeError, Exception):
                continue

        if not rows:
            raise ValueError(f"Could not parse CSV: {filepath}")

        if not bank:
            bank = self.detect_bank(list(rows[0].keys()))

        parser_cls = self.PARSERS.get(bank, UCOBankParser)
        return parser_cls().parse(rows)

    def parse_excel(
        self, filepath: str, bank: str = None, sheet: int = 0, skip_rows: int = 0
    ) -> List[ParsedTransaction]:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.worksheets[sheet]
            data = list(ws.values)
        except ImportError:
            raise ImportError("Install openpyxl: pip install openpyxl")

        if not data:
            return []

        header_idx = skip_rows
        if not skip_rows:
            for i, row in enumerate(data[:10]):
                row_str = " ".join(str(c or "").lower() for c in row)
                if any(
                    k in row_str for k in ["date", "narration", "debit", "amount", "description"]
                ):
                    header_idx = i
                    break

        headers = [str(c or "").strip() for c in data[header_idx]]
        rows: List[Dict[str, str]] = []
        for row in data[header_idx + 1 :]:
            if any(cell for cell in row):
                rows.append(
                    dict(zip(headers, [str(c or "").strip() for c in row]))
                )

        if not bank:
            bank = self.detect_bank(headers)

        parser_cls = self.PARSERS.get(bank, UCOBankParser)
        return parser_cls().parse(rows)

    def parse_from_dataframe(self, df, bank: str = None) -> List[ParsedTransaction]:
        rows = df.fillna("").astype(str).to_dict("records")
        if not rows:
            return []
        if not bank:
            bank = self.detect_bank(list(rows[0].keys()))
        parser_cls = self.PARSERS.get(bank, UCOBankParser)
        return parser_cls().parse(rows)

    def parse_sms_list(self, sms_messages: List[str], bank: str = "Unknown") -> List[ParsedTransaction]:
        return SMSParser().parse_many(sms_messages, bank)


def load_and_parse(filepath: str, bank: str = None) -> List[ParsedTransaction]:
    parser = BankStatementParser()
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".xlsx", ".xls"):
        return parser.parse_excel(filepath, bank=bank)
    return parser.parse_csv(filepath, bank=bank)

