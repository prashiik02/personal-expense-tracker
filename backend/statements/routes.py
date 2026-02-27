from __future__ import annotations

import os
import tempfile
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from categorization.pipeline_service import get_pipeline
from smart_categorization.core.pipeline import Transaction

from .analysis import compute_time_aggregates, compute_top_merchants
from .parse_lines import parse_statement_text
from .pdf_extract import extract_text
from models import db
from models.transaction_model import TransactionRecord


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

        parsed = parse_statement_text(text, bank=bank, currency=currency)
        if not parsed:
            return (
                jsonify(
                    {
                        "error": "Could not detect transactions in this PDF with current parser.",
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
            processed_objs.append(pipeline.process(txn))

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

