from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import List

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.transaction_model import TransactionRecord
from statements.analysis import compute_time_aggregates

from models.assistant_models import LoanDocument, BudgetSuggestion, AnomalyRecord
from models import db
from .schemas import LoanParsed, BudgetSuggestionModel, AnomalyExplanation

from .llm_service import ask


assistant_bp = Blueprint("assistant", __name__, url_prefix="/assistant")


def _transactions_for_user(user_id: int, since: str | None = None) -> List[TransactionRecord]:
    """Helper to fetch a user's transactions, optionally filtering by
    date prefix (YYYY-MM or YYYY-MM-DD).
    """

    q = TransactionRecord.query.filter_by(user_id=user_id)
    if since:
        q = q.filter(TransactionRecord.date.startswith(since))  # type: ignore[attr-defined]
    return q.order_by(TransactionRecord.date).all()


@assistant_bp.route("/query", methods=["POST"])
@jwt_required()
def conversational_query():
    """Simple natural‑language query interface backed by the user's own
    transaction history.

    The frontend can POST a JSON body of the form {"question": "..."} and
    receive an answer in the response.  For performance we only send a few
    thousand characters of recent history to the LLM; if the application
    grows it would make sense to cache a summarised representation.
    """

    data = request.get_json() or {}
    question = data.get("question")
    if not question or not isinstance(question, str):
        return jsonify({"error": "question is required"}), 400

    user_id = int(get_jwt_identity())
    txns = _transactions_for_user(user_id)

    # build a lightweight context string; each line is one transaction
    context_lines = []
    for t in txns[-500:]:  # limit to last 500 rows
        context_lines.append(
            f"{t.date} \t {t.description} \t {t.amount} \t {t.category}/{t.subcategory}"
        )
    context = "\n".join(context_lines)
    if len(context) > 10000:
        context = context[-10000:]

    prompt = (
        "You are a helpful personal finance assistant. "
        "Use the transaction history below to answer the user's question. "
        "Be concise and do not hallucinate amounts.\n\n"
        f"TRANSACTIONS:\n{context}\n\n"
        f"QUESTION: {question}\nANSWER:"
    )

    try:
        answer = ask(prompt, max_tokens=1024)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"answer": answer})


@assistant_bp.route("/report", methods=["GET"])
@jwt_required()
def monthly_report():
    """Generate a human‑readable financial health report for a given month.

    Query parameters:
    - month: optional YYYY‑MM string (defaults to current month)
    """

    month = request.args.get("month")
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")
    user_id = int(get_jwt_identity())

    txns = _transactions_for_user(user_id, since=month)
    processed = [
        {
            "date": t.date,
            "amount": float(t.amount),
            "category": t.category,
            "subcategory": t.subcategory,
        }
        for t in txns
    ]
    aggregates = compute_time_aggregates(processed)

    # use triple-quoted string to avoid broken quotes
    prompt = (
        "You are a financial analyst. "
        "Write a concise monthly report based on the following aggregated data. "
        "Mention total spend, income, main categories, and suggest one or two improvements. "
        "Return plain text.\n\n"
        f"DATA: {json.dumps(aggregates)}\n"
    )
    try:
        report_text = ask(prompt, max_tokens=1024)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"month": month, "report": report_text, "data": aggregates})


@assistant_bp.route("/budget", methods=["POST"])
@jwt_required()
def smart_budget():
    """Generate a proposed monthly budget based on a user's past behaviour.

    Currently this simply averages the last three months of spending per
    category and asks the LLM to format it in a friendly way.
    """

    user_id = int(get_jwt_identity())
    # pull last 3 months of data
    today = datetime.utcnow()
    since_date = (today - timedelta(days=90)).strftime("%Y-%m")
    txns = _transactions_for_user(user_id, since=since_date)
    processed = [
        {"date": t.date, "amount": float(t.amount), "category": t.category}
        for t in txns
    ]
    aggregates = compute_time_aggregates(processed)

    prompt = (
        "You are a budgeting assistant. The user has the following monthly spend aggregates: "
        f"{json.dumps(aggregates.get('by_month', []))}. "
        "Propose a sensible budget for the coming month, allocating amounts to each category and giving the reasoning. "
        "Return JSON where keys are categories and values are suggested budgets. Include a brief human-readable explanation as well."
    )
    try:
        budget_answer = ask(prompt, max_tokens=1024)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # try parse JSON suggestion, otherwise store as text
    parsed_budget_raw = None
    try:
        parsed_budget_raw = json.loads(budget_answer)
    except Exception:
        parsed_budget_raw = {"text": budget_answer}

    # Validate budget: if model returned a dict of category->amount, normalize
    budget_model = None
    try:
        # Accept both {'category': amount, ...} or {'budgets': {...}, 'explanation': '...'}
        if isinstance(parsed_budget_raw, dict) and "budgets" not in parsed_budget_raw:
            budgets = {k: float(v) for k, v in parsed_budget_raw.items() if isinstance(v, (int, float, str))}
            budget_model = BudgetSuggestionModel(budgets=budgets, explanation=None)
        else:
            budget_model = BudgetSuggestionModel(**(parsed_budget_raw or {}))
    except Exception:
        # Fallback: store model text in explanation
        budget_model = BudgetSuggestionModel(budgets={}, explanation=str(budget_answer))

    month = datetime.utcnow().strftime("%Y-%m")
    bs = BudgetSuggestion(user_id=user_id, month=month, suggestion_json=budget_model.json())
    db.session.add(bs)
    db.session.commit()

    return jsonify({"budget": budget_model.dict(), "id": bs.id})


@assistant_bp.route("/anomaly/explain", methods=["POST"])
@jwt_required()
def explain_anomaly():
    """Let the LLM compose a human‑friendly explanation for an unusual
    transaction. The request can either supply a transaction_id or a small
    dictionary with date/amount/description.
    """

    data = request.get_json() or {}
    txn_id = data.get("transaction_id")
    details = data.get("details")
    if txn_id:
        t = TransactionRecord.query.filter_by(id=txn_id, user_id=int(get_jwt_identity())).first()
        if not t:
            return jsonify({"error": "transaction not found"}), 404
        details = {
            "date": t.date,
            "amount": float(t.amount),
            "description": t.description,
            "category": t.category,
        }
    if not details or not isinstance(details, dict):
        return jsonify({"error": "transaction details required"}), 400

    prompt = (
        "You are an anomaly detector assistant. A user has an unusual transaction with these fields: "
        f"{json.dumps(details)}. "
        "Write a short, non-technical explanation of what might have happened and any steps the user could take (e.g. verify with bank)."
    )
    try:
        explanation = ask(prompt, max_tokens=512)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # try to parse/structure the explanation
    parsed_explanation = None
    try:
        parsed_explanation = json.loads(explanation)
    except Exception:
        # if the model returned plain text, wrap it
        parsed_explanation = {"text": explanation}

    # Validate with AnomalyExplanation
    try:
        ae = AnomalyExplanation(**(parsed_explanation if isinstance(parsed_explanation, dict) else {}))
    except Exception:
        ae = AnomalyExplanation(likely_cause=None, recommended_steps=None, raw=parsed_explanation)

    ar = AnomalyRecord(
        user_id=int(get_jwt_identity()),
        transaction_id=(txn_id if txn_id else None),
        description=(details.get("description") if isinstance(details, dict) else None),
        amount=(float(details.get("amount")) if isinstance(details, dict) and details.get("amount") is not None else None),
        explanation=ae.json(),
    )
    db.session.add(ar)
    db.session.commit()

    return jsonify({"explanation": explanation, "id": ar.id})


@assistant_bp.route("/loan/upload", methods=["POST"])
@jwt_required()
def analyze_loan_document():
    """Upload a loan sanction letter PDF; LLM extracts key terms and
    returns a parsed summary.  We don't yet persist anything but we could
    store the raw text / parsed JSON in the database for future queries.
    """

    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400
    f = request.files["file"]
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF allowed"}), 400

    # reuse the statement extraction code
    from statements.pdf_extract import extract_text

    user_id = int(get_jwt_identity())
    import tempfile, os
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tf.name
    tf.close()
    f.save(tmp_path)
    text = extract_text(tmp_path, max_pages=20)
    if not text:
        return jsonify({"error": "could not read PDF"}), 400

    prompt = (
        "You are a loan document analyst. Extract principal amount, interest rate, tenure, EMI, sanction date, lender name and any prepayment or foreclosure clauses from the following letter. "
        "Return strictly valid JSON with those keys (use null when a field is missing). Do not include any explanatory text.\n\n"
        + text[:20000]
    )
    try:
        parsed = ask(prompt, max_tokens=1024)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Try to parse JSON from the model; fall back to raw text
    parsed_json_raw = None
    try:
        parsed_json_raw = json.loads(parsed)
    except Exception:
        parsed_json_raw = {"text": parsed}

    # Validate against LoanParsed where possible
    loan_obj = None
    try:
        loan_obj = LoanParsed(**(parsed_json_raw if isinstance(parsed_json_raw, dict) else {}))
    except Exception:
        loan_obj = LoanParsed(raw=parsed_json_raw)

    # persist loan document (store validated or raw JSON)
    filename = os.path.basename(getattr(f, "filename", "loan.pdf"))
    doc = LoanDocument(user_id=user_id, filename=filename, parsed_json=loan_obj.json())
    db.session.add(doc)
    db.session.commit()

    # cleanup temp file
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return jsonify({"parsed": json.loads(doc.parsed_json), "id": doc.id})


@assistant_bp.route("/tax/suggestions", methods=["GET"])
@jwt_required()
def tax_suggestions():
    """Simple endpoint that asks the LLM to look through all of a user's
    transactions and suggest possible tax‑saving opportunities.
    """

    user_id = int(get_jwt_identity())
    txns = _transactions_for_user(user_id)
    data = [
        {"date": t.date, "amount": float(t.amount), "category": t.category}
        for t in txns
    ]
    prompt = (
        "You are a personal finance advisor familiar with Indian tax deductions (Section 80C, 80D, HRA, etc.). "
        "Given the user's transaction history below, suggest categories of spending where the user may be able to claim deductions or save tax. Return a bullet-list in plain text.\n\n"
        + json.dumps(data)
    )
    try:
        advice = ask(prompt, max_tokens=1024)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"suggestions": advice})


@assistant_bp.route("/whatsapp-sms", methods=["POST"])
@jwt_required()
def parse_whatsapp_sms():
    """Parses a WhatsApp‑forwarded bank SMS. These messages typically include
    metadata like sender number, timestamp and maybe a short extra line.

    We strip common prefixes and then delegate to the normal SMS parser.
    """

    from categorization.schemas import CategorizeSmsSchema
    from categorization.pipeline_service import get_pipeline

    try:
        data = CategorizeSmsSchema(**(request.get_json() or {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    sms = data.sms_text
    # simple clean‑up: remove anything before the first numeric block
    import re
    sms = re.sub(r"^.*?(\d{2,})", r"\1", sms)

    # fall back to existing categorization pipeline
    pipeline = get_pipeline()
    from smart_categorization.core.pipeline import Transaction as Tx

    txn_obj = Tx(transaction_id="sms", date="", description=sms, amount=0)
    result = pipeline.process(txn_obj)
    return jsonify({"parsed": result.to_dict()})
