from __future__ import annotations

import os
import tempfile
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from categorization.pipeline_service import get_pipeline
from smart_categorization.core.pipeline import Transaction

from .analysis import compute_time_aggregates, compute_top_merchants, UNCATEGORIZED_CATEGORY
from .parse_lines import (
    parse_statement_text,
    ParsedTxn,
    try_parse_tables,
    _is_valid_date,
    _is_valid_description,
)
from .pdf_extract import extract_text, extract_tables
from .llm_fallback import parse_bank_statement_with_llm
from models import db
from models.transaction_model import TransactionRecord
from models.user_model import User


statements_bp = Blueprint("statements", __name__, url_prefix="/statements")


@statements_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze_pdf_statement():
    """
    Upload a PDF bank statement and get categorized analytics.

    Multipart form fields:
    - file: PDF
    - bank: generic|hdfc|sbi|icici|axis (optional, default generic)
    - currency: (optional, default INR)
    - max_pages: (optional int, default 20)
    - return_results: true|false (optional, default true)
    """
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    f = request.files["file"]
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only .pdf files are supported"}), 400

    bank = (request.form.get("bank") or "generic").lower()
    currency = request.form.get("currency") or "INR"
    try:
        max_pages = int(request.form.get("max_pages") or 20)
    except ValueError:
        max_pages = 20

    return_results = (request.form.get("return_results") or "true").lower() in (
        "true",
        "1",
        "yes",
        "y",
    )

    tmpdir = tempfile.gettempdir()
    tmp_path = os.path.join(tmpdir, f"statement_{next(tempfile._get_candidate_names())}.pdf")
    f.save(tmp_path)

    try:
        text = extract_text(tmp_path, max_pages=max_pages)
        if not text or not text.strip():
            return (
                jsonify(
                    {
                        "error": "No text extracted from PDF. If this is a scanned statement, OCR is needed.",
                        "hint": "Try exporting a text-based statement PDF from your bank portal.",
                    }
                ),
                400,
            )

        parsed: list[ParsedTxn] = []

        # 1) Try table extraction first (UCO, HDFC, SBI-style tabular statements).
        try:
            tables = extract_tables(tmp_path, max_pages=max_pages)
            parsed = try_parse_tables(tables, currency=currency)
        except Exception:
            pass

        # 2) Fall back to text line parsing if table parsing failed or found nothing.
        if not parsed:
            parsed = parse_statement_text(text, bank=bank, currency=currency)

        # 3) If that fails (or found very few rows), try Groq LLM parser.
        # Regex can partially match header/noise; LLM often extracts more from varied formats.
        if not parsed or (len(parsed) < 3 and len(text.strip()) > 500):
            llm_txns = parse_bank_statement_with_llm(text)
            llm_parsed = []
            for idx, t in enumerate(llm_txns, start=1):
                try:
                    date = str(t.get("date") or "").strip()
                    narration = (
                        str(t.get("narration") or t.get("description") or "").strip()
                    )
                    if not date:
                        continue
                    if not narration:
                        narration = str(t.get("particulars") or t.get("remarks") or "").strip()
                    if not narration:
                        continue

                    raw_amount = float(t.get("amount") or 0.0)
                    t_type = str(t.get("type") or "").strip().lower()
                    if t_type == "credit":
                        amount = -abs(raw_amount)
                    else:
                        amount = abs(raw_amount)

                    txn_id = (
                        str(t.get("reference") or "").strip()
                        or f"LLM_{idx:05d}"
                    )

                    # Reject invalid dates (e.g. 2025-12-84) and numeric-only descriptions
                    if not _is_valid_date(date) or not _is_valid_description(narration):
                        continue

                    llm_parsed.append(
                        ParsedTxn(
                            transaction_id=txn_id,
                            date=date,
                            description=narration,
                            amount=amount,
                            currency=currency,
                            source_line=None,
                        )
                    )
                except Exception:
                    # Skip any malformed rows from the LLM output.
                    continue

            # Use LLM result if it found more transactions; else keep regex result
            if llm_parsed:
                parsed = llm_parsed
            # else: parsed stays as regex result (may be empty or 1–2 items)

        # 4) Final validation: drop invalid transactions before categorization
        parsed = [
            p
            for p in parsed
            if _is_valid_date(p.date) and _is_valid_description(p.description)
        ]

        if not parsed:
            return (
                jsonify(
                    {
                        "error": "Could not detect transactions in this PDF with available parsers.",
                        "hint": "Try selecting the correct bank, or share a sample (with sensitive data removed) to improve the parser.",
                    }
                ),
                400,
            )

        pipeline = get_pipeline()
        processed_objs = []
        for p in parsed:
            txn = Transaction(
                transaction_id=p.transaction_id,
                date=p.date,
                description=p.description,
                amount=p.amount,
                currency=p.currency,
            )
            # PDF transactions: use Groq LLM only (skip ML model)
            processed_objs.append(pipeline.process(txn, use_llm_only=True))

        processed = [o.to_dict() for o in processed_objs]

        # Persist processed transactions for the current user (id from JWT)
        user_id = int(get_jwt_identity())
        for row in processed:
            # Build record and check for duplicates via hash_key
            record = TransactionRecord.from_processed(
                user_id=user_id,
                processed=row,
                source="pdf",
                bank=bank,
            )
            exists = TransactionRecord.query.filter_by(
                user_id=user_id, hash_key=record.hash_key
            ).first()
            if exists:
                continue
            db.session.add(record)
        db.session.commit()
        time_aggs = compute_time_aggregates(processed)
        summary = pipeline.get_summary(processed_objs)

        response = {
            "bank": bank,
            "currency": currency,
            "parsed_count": len(parsed),
            "summary": summary,
            "time_aggregates": time_aggs,
            "top_merchants": compute_top_merchants(processed, limit=12),
            "filters": {
                "categories": sorted({r["category"] for r in processed if r.get("category")}),
                "subcategories": sorted(
                    {
                        f"{(r.get('category') or 'Unknown')} > {(r.get('subcategory') or 'Unknown')}"
                        for r in processed
                        if r.get("category")
                    }
                ),
                "charge_types": sorted({r.get("charge_type") for r in processed if r.get("charge_type")}),
                "tags": sorted({t for r in processed for t in (r.get("tags") or [])}),
            },
        }
        if return_results:
            response["results"] = processed
            response["raw_preview"] = [
                {
                    "transaction_id": p.transaction_id,
                    "date": p.date,
                    "description": p.description,
                    "amount": p.amount,
                }
                for p in parsed[:50]
            ]

        return jsonify(response), 200
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@statements_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard_overview():
    """
    Return aggregated analytics for all stored transactions
    belonging to the current user.
    """
    user_id = int(get_jwt_identity())

    records = (
        TransactionRecord.query.filter_by(user_id=user_id)
        .order_by(TransactionRecord.date, TransactionRecord.id)
        .all()
    )

    processed_like = []
    for r in records:
        try:
            tags = json.loads(r.tags_json) if r.tags_json else []
        except Exception:
            tags = []
        processed_like.append(
            {
                "transaction_id": r.external_id or str(r.id),
                "date": r.date,
                "description": r.description,
                "amount": float(r.amount or 0.0),
                "currency": r.currency,
                "category": r.category,
                "subcategory": r.subcategory,
                "merchant_name": r.merchant_name,
                "charge_type": r.charge_type,
                "is_p2p": bool(r.is_p2p),
                "p2p_direction": r.p2p_direction,
                "p2p_counterparty": r.p2p_counterparty,
                "tags": tags,
            }
        )

    time_aggs = compute_time_aggregates(processed_like)
    top_merchants = compute_top_merchants(processed_like, limit=12)

    user = User.query.get(user_id)
    monthly_income = float(user.monthly_income or 0) if user else 0

    categories = sorted({r["category"] for r in processed_like if r.get("category")})
    subcategories = sorted(
        {
            f"{(r.get('category') or 'Unknown')} > {(r.get('subcategory') or 'Unknown')}"
            for r in processed_like
            if r.get("category")
        }
    )
    charge_types = sorted({r.get("charge_type") for r in processed_like if r.get("charge_type")})
    tags_all = sorted({t for r in processed_like for t in (r.get("tags") or [])})

    return jsonify(
        {
            "transactions_count": len(processed_like),
            "monthly_income": monthly_income if monthly_income > 0 else None,
            "time_aggregates": time_aggs,
            "top_merchants": top_merchants,
            "filters": {
                "categories": categories,
                "subcategories": subcategories,
                "charge_types": charge_types,
                "tags": tags_all,
            },
        }
    ), 200


@statements_bp.route("/transactions", methods=["GET"])
@jwt_required()
def list_transactions():
    """
    List stored transactions for the current user.
    Query params: category (e.g. "Shopping"), subcategory (e.g. "Electronics"),
    month (YYYY-MM), limit (default 100, max 500).
    """
    user_id = int(get_jwt_identity())
    category = request.args.get("category", "").strip() or None
    subcategory = request.args.get("subcategory", "").strip() or None
    month = request.args.get("month", "").strip() or None
    try:
        limit = min(500, max(1, int(request.args.get("limit", 100))))
    except ValueError:
        limit = 100

    q = TransactionRecord.query.filter_by(user_id=user_id)
    if category:
        q = q.filter(TransactionRecord.category == category)
    if subcategory:
        q = q.filter(TransactionRecord.subcategory == subcategory)
    if month and len(month) >= 7:
        q = q.filter(TransactionRecord.date.startswith(month))  # type: ignore[attr-defined]
    records = q.order_by(TransactionRecord.date.desc(), TransactionRecord.id.desc()).limit(limit).all()

    out = []
    for r in records:
        try:
            tags = json.loads(r.tags_json) if r.tags_json else []
        except Exception:
            tags = []
        out.append({
            "id": r.id,
            "transaction_id": r.external_id or str(r.id),
            "date": r.date,
            "description": r.description,
            "amount": float(r.amount or 0.0),
            "currency": r.currency,
            "category": r.category,
            "subcategory": r.subcategory,
            "merchant_name": r.merchant_name,
        })
    return jsonify({"transactions": out}), 200


@statements_bp.route("/transactions/<int:txn_id>", methods=["PATCH"])
@jwt_required()
def update_transaction(txn_id):
    """
    Update a transaction's category (e.g. move to Uncategorized to exclude from analysis).
    Body: { "category": "Uncategorized", "subcategory": "Uncategorized" }
    or { "exclude_from_analytics": true } as shorthand.
    """
    user_id = int(get_jwt_identity())
    record = TransactionRecord.query.filter_by(id=txn_id, user_id=user_id).first()
    if not record:
        return jsonify({"error": "Transaction not found"}), 404

    data = request.get_json() or {}
    if data.get("exclude_from_analytics") is True:
        record.category = UNCATEGORIZED_CATEGORY
        record.subcategory = UNCATEGORIZED_CATEGORY
    else:
        if "category" in data and data["category"] is not None:
            record.category = str(data["category"]).strip() or UNCATEGORIZED_CATEGORY
        if "subcategory" in data and data["subcategory"] is not None:
            record.subcategory = str(data["subcategory"]).strip() or UNCATEGORIZED_CATEGORY
    db.session.commit()
    return jsonify({
        "id": record.id,
        "category": record.category,
        "subcategory": record.subcategory,
    }), 200

