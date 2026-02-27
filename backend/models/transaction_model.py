import hashlib
import json

from models import db


class TransactionRecord(db.Model):
    """
    Persisted, user-specific view of a processed transaction.
    Stores the key fields needed for analytics and dashboard views.
    """

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)

    # Ownership
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False)

    # Source / identity
    external_id = db.Column(db.String(64), nullable=True)
    source = db.Column(db.String(20), nullable=False, default="unspecified")  # pdf | csv | sms | manual | other
    bank = db.Column(db.String(32), nullable=True)

    # Deduplication key (user_id + hash_key is unique)
    hash_key = db.Column(db.String(40), nullable=False)

    # Core transaction data
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD (matches pipeline)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="INR")

    # Categorization snapshot
    category = db.Column(db.String(120), nullable=False)
    subcategory = db.Column(db.String(160), nullable=False)
    merchant_name = db.Column(db.String(255), nullable=True)
    charge_type = db.Column(db.String(50), nullable=True)

    # P2P snapshot
    is_p2p = db.Column(db.Boolean, nullable=False, default=False)
    p2p_direction = db.Column(db.String(12), nullable=True)
    p2p_counterparty = db.Column(db.String(255), nullable=True)

    # Misc
    tags_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("user_id", "hash_key", name="uq_user_txn_hash"),
    )

    @staticmethod
    def _normalize_description(desc: str) -> str:
        if not desc:
            return ""
        return " ".join(str(desc).strip().upper().split())

    @classmethod
    def compute_hash_key(cls, user_id: int, processed: dict) -> str:
        """
        Build a stable hash for deduplication based on:
        - user_id
        - date
        - absolute amount
        - normalized description
        This keeps the same transaction from any source (PDF, CSV, SMS, manual)
        from being stored multiple times.
        """
        date = str(processed.get("date") or "").strip()
        try:
            amt = float(processed.get("amount") or 0.0)
        except (TypeError, ValueError):
            amt = 0.0
        desc = cls._normalize_description(processed.get("description") or "")
        key = f"{user_id}|{date}|{abs(amt):.2f}|{desc}"
        return hashlib.sha1(key.encode("utf-8")).hexdigest()

    @classmethod
    def from_processed(cls, user_id: int, processed: dict, *, source: str, bank: str | None = None):
        """
        Build a TransactionRecord instance (not added to the session yet)
        from a ProcessedTransaction dict.
        """
        hash_key = cls.compute_hash_key(user_id, processed)

        try:
            amt = float(processed.get("amount") or 0.0)
        except (TypeError, ValueError):
            amt = 0.0

        tags = processed.get("tags") or []

        return cls(
            user_id=user_id,
            external_id=str(processed.get("transaction_id") or ""),
            source=source or "unspecified",
            bank=(bank or None),
            hash_key=hash_key,
            date=str(processed.get("date") or ""),
            description=str(processed.get("description") or ""),
            amount=amt,
            currency=str(processed.get("currency") or "INR"),
            category=str(processed.get("category") or "Unknown"),
            subcategory=str(processed.get("subcategory") or "Unknown"),
            merchant_name=processed.get("merchant_name"),
            charge_type=processed.get("charge_type"),
            is_p2p=bool(processed.get("is_p2p") or False),
            p2p_direction=processed.get("p2p_direction"),
            p2p_counterparty=processed.get("p2p_counterparty"),
            tags_json=json.dumps(tags),
        )

