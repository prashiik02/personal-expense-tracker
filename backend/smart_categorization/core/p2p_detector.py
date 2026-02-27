"""
P2P (Peer-to-Peer) Transaction Detector
────────────────────────────────────────
Identifies transactions between individuals (friends, family, colleagues)
vs merchant payments. Works on raw UPI/NEFT/IMPS description strings.
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class P2PResult:
    is_p2p: bool
    confidence: float
    direction: str                  # "sent" | "received"
    relationship: str               # "personal" | "obligation" | "income" | "gift" | "unknown"
    relationship_detail: str        # "friend" | "family" | "landlord" | "employer" | etc.
    transfer_mode: str              # "upi" | "neft" | "imps" | "rtgs" | "other"
    counterparty_name: str
    counterparty_upi: Optional[str]
    counterparty_phone: Optional[str]
    subcategory: str
    category: str
    p2p_reason: str

    @property
    def suggested_subcategory(self):
        return self.subcategory


UPI_ID_PATTERN = re.compile(
    r"\b([a-z0-9._+\-]{3,}@(?:okaxis|oksbi|okicici|okhdfcbank|ybl|axl|"
    r"ibl|upi|paytm|apl|waaxis|waicici|wahdfcbank|wasbi|naviaxis|"
    r"freecharge|kotak|indus|rbl|federal|equitas|barodampay|aubank|"
    r"idfc|dbs|citi|hsbc|sc|boi|cub|kvb|tmb|dcb|ucb|uco|pnb|cnrb|"
    r"sib|jkb|kbl|nsdl|idbi|axisbank|hdfcbank|icicibank|sbibank|"
    r"fifederal|airtel|jio|phonepe|gpay|bhim|slice|jupiter|fi|"
    r"postbank|airtelpaymentsbank|jiopay|amazonpay))\b",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(r"\b([6-9]\d{9})\b")

NEFT_NAME_PATTERN = re.compile(
    r"(?:NEFT|IMPS|RTGS)[/\-\s]+(?:\d+[/\-\s]+)?([A-Z][A-Z\s]{3,30}?)(?:[/\-]|$)",
    re.IGNORECASE,
)

UPI_NAME_PATTERN = re.compile(
    r"UPI[/\-\s]+([A-Z][A-Z\s]{2,25}?)(?:[/\-@])",
    re.IGNORECASE,
)

P2P_APP_PATTERNS = [
    re.compile(r"(?:phonepe|gpay|google pay|paytm|bhim)\s*(?:p2p|send|transfer|upi)", re.I),
    re.compile(r"pay to\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", re.I),
    re.compile(r"(?:sent to|received from|transfer (?:to|from))\s+([A-Z][a-z\s]+)", re.I),
]

P2P_KEYWORDS = [
    "lent",
    "borrowed",
    "borrow",
    "lend",
    "settle",
    "settlement",
    "split",
    "share",
    "birthday",
    "gift",
    "shaadi gift",
    "wedding gift",
    "loan repay",
    "owe",
    "friend",
    "bro",
    "sis",
    "mama",
    "chacha",
    "didi",
    "bhai",
    "papa",
    "mom",
    "dad",
    "maa",
    "wife",
    "husband",
    "rent paid to",
    "room rent",
    "pg rent",
    "flat rent",
]

SALARY_INCOME_KEYWORDS = [
    "salary",
    "sal ",
    "sal/",
    "payroll",
    "stipend",
    "wages",
    "monthly pay",
    "pay slip",
    "hr dept",
    "accounts dept",
]

FREELANCE_KEYWORDS = [
    "invoice",
    "payment for",
    "project",
    "freelance",
    "consulting",
    "client",
    "service charge",
    "professional fee",
]

NOT_P2P_SIGNALS = [
    "pvt ltd",
    "private limited",
    "limited",
    "llp",
    "inc",
    "store",
    "shop",
    "mart",
    "enterprises",
    "traders",
    "agency",
    "services",
    "solutions",
    "technologies",
    "tech",
    "digital",
    "foods",
    "restaurant",
    "hotel",
    "school",
    "college",
    "hospital",
    "clinic",
    "pharmacy",
    "medical",
    "petrol",
    "pump",
    "motors",
    "amazon",
    "flipkart",
    "swiggy",
    "zomato",
    "razorpay",
    "cashfree",
    "instamojo",
    "billdesk",
]

FAMILY_KEYWORDS = [
    "mom",
    "maa",
    "mother",
    "dad",
    "papa",
    "father",
    "bhai",
    "brother",
    "didi",
    "sister",
    "sis",
    "bro",
    "wife",
    "husband",
    "beta",
    "beti",
    "son",
    "daughter",
    "chacha",
    "chachi",
    "mama",
    "mami",
    "nana",
    "nani",
    "dada",
    "dadi",
    "jiju",
    "family",
]

FRIEND_KEYWORDS = [
    "friend",
    "yaar",
    "dost",
    "buddy",
    "roommate",
    "flatmate",
    "colleague",
]

RENT_KEYWORDS = [
    "rent",
    "landlord",
    "owner",
    "flat",
    "house rent",
    "pg rent",
    "room rent",
]

LOAN_KEYWORDS = [
    "lent",
    "lend",
    "borrowed",
    "borrow",
    "loan",
    "loan repay",
    "settle",
    "settlement",
    "split",
    "owe",
]

GIFT_KEYWORDS = [
    "gift",
    "birthday",
    "anniversary",
    "wedding gift",
    "shaadi gift",
    "festival",
    "diwali",
    "eid",
    "holi",
    "navratri",
    "rakhi",
    "christmas",
]

TRANSFER_MODE_PATTERNS = {
    "upi": re.compile(r"\b(upi|vpa|gpay|phonepe|bhim|paytm\s*upi)\b", re.I),
    "neft": re.compile(r"\b(neft)\b", re.I),
    "imps": re.compile(r"\b(imps)\b", re.I),
    "rtgs": re.compile(r"\b(rtgs)\b", re.I),
}


def build_subcategory(direction: str, transfer_mode: str, relationship: str, relationship_detail: str) -> str:
    mode = transfer_mode.upper()
    dir_label = "Sent" if direction == "sent" else "Received"

    relationship_labels = {
        ("personal", "friend"): "Friends & Family",
        ("personal", "family"): "Friends & Family",
        ("personal", "unknown"): "Friends & Family",
        ("obligation", "landlord"): "Rent",
        ("obligation", "loan"): "Lending & Settling",
        ("obligation", "settle"): "Lending & Settling",
        ("income", "employer"): "Salary",
        ("income", "freelance"): "Freelance Income",
        ("income", "unknown"): "Money Received",
        ("gift", "family"): "Gift",
        ("gift", "friend"): "Gift",
        ("gift", "unknown"): "Gift",
        ("unknown", "unknown"): "P2P Transfer",
    }

    rel_label = relationship_labels.get(
        (relationship, relationship_detail),
        relationship_labels.get((relationship, "unknown"), "P2P Transfer"),
    )

    return f"{mode} {dir_label} – {rel_label}"


INDIVIDUAL_UPI_HANDLES = {
    "okaxis",
    "oksbi",
    "okicici",
    "okhdfcbank",
    "ybl",
    "axl",
    "ibl",
    "apl",
    "waaxis",
    "naviaxis",
    "freecharge",
    "kotak",
    "indus",
    "rbl",
    "federal",
    "aubank",
    "idfc",
}

BUSINESS_UPI_HANDLES = {
    "razorpay",
    "cashfree",
    "paytmqr",
    "sbiepay",
    "hdfcbankltd",
}


class P2PDetector:
    """
    Detects P2P (peer-to-peer) transactions from raw bank description strings.
    Works with UCO Bank, SBI, HDFC, Axis, PhonePe statement formats.
    """

    def __init__(self):
        try:
            from ..data.merchant_db import MERCHANT_LOOKUP
            self._merchant_names = set(MERCHANT_LOOKUP.keys())
        except Exception:
            self._merchant_names = set()

    def detect(self, description: str, amount: float, transaction_type: str = "debit") -> P2PResult:
        desc = description.strip()
        desc_lower = desc.lower()
        confidence = 0.0
        reasons = []

        counterparty_upi = None
        counterparty_phone = None
        counterparty_name = "Unknown Person"
        direction = "received" if transaction_type == "credit" else "sent"

        relationship = "unknown"
        relationship_detail = "unknown"
        transfer_mode = "other"

        for mode, pattern in TRANSFER_MODE_PATTERNS.items():
            if pattern.search(desc):
                transfer_mode = mode
                break

        if transfer_mode == "other":
            prefix = desc_lower[:8]
            if prefix.startswith("neft") or "neft" in desc_lower:
                transfer_mode = "neft"
            elif prefix.startswith("imps") or "imps" in desc_lower:
                transfer_mode = "imps"
            elif prefix.startswith("rtgs") or "rtgs" in desc_lower:
                transfer_mode = "rtgs"
            elif prefix.startswith("upi") or "upi" in desc_lower:
                transfer_mode = "upi"

        for signal in NOT_P2P_SIGNALS:
            if signal in desc_lower:
                return self._not_p2p("Merchant signal")

        words = desc_lower.split()
        first_two = " ".join(words[:2])
        if first_two in self._merchant_names or (words and words[0] in self._merchant_names):
            return self._not_p2p("Known merchant in DB")

        for kw in SALARY_INCOME_KEYWORDS:
            if kw in desc_lower:
                name = self._extract_org_name(desc)
                return P2PResult(
                    is_p2p=True,
                    confidence=0.93,
                    direction="received",
                    relationship="income",
                    relationship_detail="employer",
                    transfer_mode=transfer_mode,
                    counterparty_name=name,
                    counterparty_upi=None,
                    counterparty_phone=None,
                    subcategory=build_subcategory("received", transfer_mode, "income", "employer"),
                    category="Transfers & Payments",
                    p2p_reason=f"Salary keyword: '{kw}'",
                )

        for kw in FREELANCE_KEYWORDS:
            if kw in desc_lower:
                confidence = max(confidence, 0.8)
                relationship = "income"
                relationship_detail = "freelance"
                reasons.append(f"Freelance keyword: '{kw}'")
                break

        upi_match = UPI_ID_PATTERN.search(desc)
        if upi_match:
            upi_id = upi_match.group(1).lower()
            counterparty_upi = upi_id
            transfer_mode = "upi"
            handle = upi_id.split("@")[-1] if "@" in upi_id else ""

            if handle in BUSINESS_UPI_HANDLES:
                confidence = max(confidence, 0.15)
            elif handle in INDIVIDUAL_UPI_HANDLES:
                confidence = max(confidence, 0.88)
                reasons.append(f"Individual UPI handle: {upi_id}")
            else:
                confidence = max(confidence, 0.72)
                reasons.append(f"UPI ID: {upi_id}")

            upi_prefix = upi_id.split("@")[0]
            if not any(c.isdigit() for c in upi_prefix):
                counterparty_name = self._upi_to_name(upi_prefix)

        phone_match = PHONE_PATTERN.search(desc)
        if phone_match:
            phone = phone_match.group(1)
            counterparty_phone = phone
            if counterparty_name == "Unknown Person":
                counterparty_name = f"Contact {phone[-4:]}"
            if upi_match and phone in (counterparty_upi or ""):
                confidence = max(confidence, 0.91)
                transfer_mode = "upi"
                reasons.append(f"Phone-based UPI: {phone}")
            else:
                confidence = max(confidence, 0.7)
                reasons.append(f"Phone number: {phone}")

        neft_match = NEFT_NAME_PATTERN.search(desc)
        if neft_match:
            name = neft_match.group(1).strip().title()
            if self._looks_like_person_name(name):
                counterparty_name = name
                confidence = max(confidence, 0.8)
                reasons.append(f"NEFT/IMPS name: {name}")

        upi_name_match = UPI_NAME_PATTERN.search(desc)
        if upi_name_match:
            name = upi_name_match.group(1).strip().title()
            if self._looks_like_person_name(name):
                counterparty_name = name
                confidence = max(confidence, 0.82)
                reasons.append(f"UPI name: {name}")

        for pattern in P2P_APP_PATTERNS:
            m = pattern.search(desc)
            if m:
                confidence = max(confidence, 0.75)
                transfer_mode = "upi"
                if m.lastindex and m.group(1):
                    name = m.group(1).strip().title()
                    if self._looks_like_person_name(name):
                        counterparty_name = name
                reasons.append("P2P app pattern")
                break

        for kw in FAMILY_KEYWORDS:
            if kw in desc_lower:
                relationship = "personal"
                relationship_detail = "family"
                if counterparty_name in ("Unknown Person", ""):
                    counterparty_name = kw.title()
                confidence = max(confidence, 0.72)
                reasons.append(f"Family keyword: '{kw}'")
                break

        if relationship == "unknown":
            for kw in FRIEND_KEYWORDS:
                if kw in desc_lower:
                    relationship = "personal"
                    relationship_detail = "friend"
                    confidence = max(confidence, 0.68)
                    reasons.append(f"Friend keyword: '{kw}'")
                    break

        for kw in RENT_KEYWORDS:
            if kw in desc_lower:
                relationship = "obligation"
                relationship_detail = "landlord"
                confidence = max(confidence, 0.7)
                reasons.append(f"Rent keyword: '{kw}'")
                break

        for kw in LOAN_KEYWORDS:
            if kw in desc_lower:
                if relationship not in ("obligation",):
                    relationship = "obligation"
                    relationship_detail = "loan"
                confidence = max(confidence, 0.68)
                reasons.append(f"Loan/settle keyword: '{kw}'")
                break

        for kw in GIFT_KEYWORDS:
            if kw in desc_lower:
                relationship = "gift"
                relationship_detail = "family" if any(f in desc_lower for f in FAMILY_KEYWORDS) else "friend"
                confidence = max(confidence, 0.7)
                reasons.append(f"Gift keyword: '{kw}'")
                break

        if confidence >= 0.5 and relationship == "unknown":
            relationship = "personal"
            relationship_detail = "unknown"

        if re.search(r"^(NEFT|IMPS|UPI|RTGS)[/\-\s]+\d+", desc, re.I) and confidence < 0.4:
            confidence = 0.45
            reasons.append("Bare transfer reference — needs review")

        if relationship == "income":
            direction = "received"

        is_p2p = confidence >= 0.5
        if not is_p2p:
            return self._not_p2p(" | ".join(reasons) or "Low confidence")

        subcategory = build_subcategory(direction, transfer_mode, relationship, relationship_detail)

        return P2PResult(
            is_p2p=True,
            confidence=round(confidence, 3),
            direction=direction,
            relationship=relationship,
            relationship_detail=relationship_detail,
            transfer_mode=transfer_mode,
            counterparty_name=counterparty_name,
            counterparty_upi=counterparty_upi,
            counterparty_phone=counterparty_phone,
            subcategory=subcategory,
            category="Transfers & Payments",
            p2p_reason=" | ".join(reasons),
        )

    def _not_p2p(self, reason: str) -> "P2PResult":
        return P2PResult(
            is_p2p=False,
            confidence=0.05,
            direction="sent",
            relationship="unknown",
            relationship_detail="unknown",
            transfer_mode="other",
            counterparty_name="",
            counterparty_upi=None,
            counterparty_phone=None,
            subcategory="",
            category="Shopping",
            p2p_reason=reason,
        )

    def _upi_to_name(self, upi_prefix: str) -> str:
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", upi_prefix)
        name = re.sub(r"[._\-]", " ", name)
        parts = [p.capitalize() for p in name.split() if len(p) > 1]
        return " ".join(parts[:3]) if parts else upi_prefix.title()

    def _looks_like_person_name(self, text: str) -> bool:
        text = text.strip()
        words = text.split()
        if not (1 <= len(words) <= 4):
            return False
        for w in words:
            if sum(c.isdigit() for c in w) > 1:
                return False
        text_lower = text.lower()
        for signal in NOT_P2P_SIGNALS:
            if signal in text_lower:
                return False
        return len(text) >= 3

    def _extract_org_name(self, desc: str) -> str:
        cleaned = re.sub(
            r"^(NEFT|IMPS|RTGS|UPI|CR|DR)[/\-\s]+\d*[/\-\s]*", "", desc, flags=re.I
        ).strip()
        words = cleaned.split()[:4]
        return " ".join(w.capitalize() for w in words) if words else "Employer"

