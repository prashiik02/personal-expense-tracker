from __future__ import annotations

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from smart_categorization.core.pipeline import Transaction
from llm_providers import categorize_batch_via_llm_chunked, get_chunked_provider, chunked_llm_available
from models import db
from models.transaction_model import TransactionRecord

from .csv_parser import parse_transactions_csv
from .pipeline_service import get_pipeline
from .schemas import (
    RawTransactionSchema,
    CategorizeBatchSchema,
    CategorizeSmsSchema,
    CategorizeCorrectionSchema,
)
from .sms_parsers import parse_hdfc_sms, parse_sbi_sms


categorization_bp = Blueprint("categorization", __name__, url_prefix="/categorize")


def _err(message, status=400):
    return jsonify({"error": message}), status


@categorization_bp.route("", methods=["POST"])
@jwt_required()
def categorize_single():
    try:
        data = RawTransactionSchema(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    pipeline = get_pipeline()
    txn = Transaction(
        transaction_id=data.transaction_id or "txn",
        date=data.date,
        description=data.description,
        amount=data.amount,
        currency=data.currency,
        line_items=[li.model_dump() for li in (data.line_items or [])] or None,
    )
    result = pipeline.process(txn)
    payload = result.to_dict()

    # Persist for this user (avoid duplicates)
    user_id = int(get_jwt_identity())
    record = TransactionRecord.from_processed(
        user_id=user_id,
        processed=payload,
        source="manual",
        bank=None,
    )
    exists = TransactionRecord.query.filter_by(
        user_id=user_id, hash_key=record.hash_key
    ).first()
    if not exists:
        db.session.add(record)
        db.session.commit()

    return jsonify(payload), 200


@categorization_bp.route("/batch", methods=["POST"])
@jwt_required()
def categorize_batch():
    try:
        data = CategorizeBatchSchema(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    txns = []
    if data.csv_text:
        parsed = parse_transactions_csv(data.csv_text)
        txns = [RawTransactionSchema(**p) for p in parsed]
    elif data.transactions:
        txns = data.transactions
    else:
        return _err("Provide either 'transactions' or 'csv_text'.", 400)

    pipeline = get_pipeline()
    processed = []

    use_chunked = getattr(data, "use_llm_chunked", False)
    try:
        has_llm = chunked_llm_available()
        provider = get_chunked_provider() if has_llm else None
    except Exception:
        has_llm = False
        provider = None

    if use_chunked and has_llm and len(txns) > 0:
        # Split data, categorize each chunk via Gemini/DeepSeek, merge and run enrichment.
        txn_dicts = [
            {
                "transaction_id": t.transaction_id or "txn",
                "description": t.description,
                "amount": t.amount,
            }
            for t in txns
        ]
        chunked_results = categorize_batch_via_llm_chunked(txn_dicts)
        method = "gemini_chunked" if provider == "gemini" else "deepseek_chunked"
        for t, res in zip(txns, chunked_results):
            txn = Transaction(
                transaction_id=t.transaction_id or "txn",
                date=t.date,
                description=t.description,
                amount=t.amount,
                currency=t.currency,
                line_items=[li.model_dump() for li in (t.line_items or [])] or None,
            )
            processed.append(
                pipeline.process_with_category(
                    txn,
                    category=res["category"],
                    subcategory=res["subcategory"],
                    confidence=res["confidence"],
                    method=method,
                )
            )
    else:
        for t in txns:
            txn = Transaction(
                transaction_id=t.transaction_id or "txn",
                date=t.date,
                description=t.description,
                amount=t.amount,
                currency=t.currency,
                line_items=[li.model_dump() for li in (t.line_items or [])] or None,
            )
            processed.append(pipeline.process(txn, enable_llm_fallback=False))

    processed_dicts = [p.to_dict() for p in processed]

    # Persist all processed transactions for this user, deduplicated
    user_id = int(get_jwt_identity())
    for row in processed_dicts:
        record = TransactionRecord.from_processed(
            user_id=user_id,
            processed=row,
            source="csv" if data.csv_text else "batch",
            bank=None,
        )
        exists = TransactionRecord.query.filter_by(
            user_id=user_id, hash_key=record.hash_key
        ).first()
        if exists:
            continue
        db.session.add(record)
    db.session.commit()

    payload = {"count": len(processed)}
    if data.return_results:
        payload["results"] = processed_dicts
    if data.include_summary:
        payload["summary"] = pipeline.get_summary(processed)

    return jsonify(payload), 200


@categorization_bp.route("/sms", methods=["POST"])
@jwt_required()
def categorize_sms():
    try:
        data = CategorizeSmsSchema(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    if data.bank == "hdfc":
        parsed = parse_hdfc_sms(data.sms_text)
    else:
        parsed = parse_sbi_sms(data.sms_text)

    pipeline = get_pipeline()
    txn = Transaction(
        transaction_id="sms",
        date=parsed["date"],
        description=parsed["description"],
        amount=parsed["amount"],
    )
    result = pipeline.process(txn)
    result_dict = result.to_dict()

    # Persist SMS-sourced transaction
    user_id = int(get_jwt_identity())
    record = TransactionRecord.from_processed(
        user_id=user_id,
        processed=result_dict,
        source="sms",
        bank=data.bank,
    )
    exists = TransactionRecord.query.filter_by(
        user_id=user_id, hash_key=record.hash_key
    ).first()
    if not exists:
        db.session.add(record)
        db.session.commit()

    return jsonify({"parsed": parsed, "result": result_dict}), 200


@categorization_bp.route("/correction", methods=["POST"])
@jwt_required()
def record_correction():
    """
    Optional endpoint: lets the UI submit a correction so the feedback store learns.
    """
    try:
        data = CategorizeCorrectionSchema(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    pipeline = get_pipeline()
    pipeline.correct_transaction(
        transaction_id=data.transaction_id,
        description=data.description,
        merchant_name=data.merchant_name,
        old_category=data.old_category,
        new_category=data.new_category,
        new_subcategory=data.new_subcategory,
    )
    return jsonify({"ok": True}), 200

