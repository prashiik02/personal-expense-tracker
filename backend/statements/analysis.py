from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Iterable


def _month_key(d: str) -> str:
    # d is YYYY-MM-DD
    return d[:7]


def _year_key(d: str) -> str:
    return d[:4]


def compute_time_aggregates(processed: List[dict]) -> dict:
    """
    processed: list of ProcessedTransaction dicts
    Returns totals by day/month/year and category-wise breakdown.
    """
    by_day = defaultdict(lambda: defaultdict(lambda: {"total": 0.0, "count": 0}))
    by_month = defaultdict(lambda: defaultdict(lambda: {"total": 0.0, "count": 0}))
    by_year = defaultdict(lambda: defaultdict(lambda: {"total": 0.0, "count": 0}))

    total_spend = 0.0
    total_income = 0.0

    for r in processed:
        date = r.get("date") or ""
        if len(date) < 10:
            continue

        amount = float(r.get("amount") or 0.0)
        spend = abs(amount) if amount > 0 else 0.0
        income = abs(amount) if amount < 0 else 0.0
        total_spend += spend
        total_income += income

        cat = r.get("category") or "Unknown"
        sub = r.get("subcategory") or "Unknown"
        key = f"{cat} > {sub}"

        by_day[date][key]["total"] += spend
        by_day[date][key]["count"] += 1

        mk = _month_key(date)
        by_month[mk][key]["total"] += spend
        by_month[mk][key]["count"] += 1

        yk = _year_key(date)
        by_year[yk][key]["total"] += spend
        by_year[yk][key]["count"] += 1

    def _to_sorted_list(grouped):
        out = []
        for period, cats in grouped.items():
            out.append(
                {
                    "period": period,
                    "categories": {
                        k: {"total": round(v["total"], 2), "count": v["count"]}
                        for k, v in cats.items()
                    },
                }
            )
        out.sort(key=lambda x: x["period"])
        return out

    return {
        "totals": {
            "total_spend": round(total_spend, 2),
            "total_income": round(total_income, 2),
            "net": round(total_income - total_spend, 2),
        },
        "by_day": _to_sorted_list(by_day),
        "by_month": _to_sorted_list(by_month),
        "by_year": _to_sorted_list(by_year),
    }


def compute_top_merchants(processed: List[dict], limit: int = 10) -> List[dict]:
    totals = defaultdict(float)
    counts = defaultdict(int)
    for r in processed:
        m = r.get("merchant_name") or "Unknown"
        amt = float(r.get("amount") or 0.0)
        spend = abs(amt) if amt > 0 else 0.0
        totals[m] += spend
        counts[m] += 1
    items = [
        {"merchant": m, "total_spend": round(t, 2), "count": counts[m]}
        for m, t in totals.items()
    ]
    items.sort(key=lambda x: x["total_spend"], reverse=True)
    return items[:limit]

