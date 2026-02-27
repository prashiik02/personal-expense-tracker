from __future__ import annotations

import os
import tempfile
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from categorization.pipeline_service import get_pipeline
from smart_categorization.core.pipeline import Transaction

from .analysis import compute_time_aggregates, compute_top_merchants
from .parse_lines import parse_statement_text
from .pdf_extract import extract_text


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

