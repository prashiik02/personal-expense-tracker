import React, { useState, useEffect } from "react";
import { getIncomeAdvice } from "../api/assistantApi";
import RichAdviceText from "./RichAdviceText";

function formatINR(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "-";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

export default function IncomeAdviceCard({ month }) {
  const [incomeAdvice, setIncomeAdvice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const m = month || new Date().toISOString().slice(0, 7);
    setLoading(true);
    setError(null);
    getIncomeAdvice(m)
      .then((res) => { setIncomeAdvice(res); setError(null); })
      .catch((e) => {
        setIncomeAdvice(null);
        setError(e.response?.data?.error || e.message || "Failed to load advice.");
      })
      .finally(() => setLoading(false));
  }, [month]);

  return (
    <div>
      <div className="finsight-card-title">Income vs spending</div>
      {loading ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>Loading advice…</p>
      ) : error ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-danger)" }}>{error}</p>
      ) : incomeAdvice?.message ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>{incomeAdvice.message}</p>
      ) : incomeAdvice?.advice ? (
        <>
          <p className="finsight-income-section-hint">
            Uses profile income and spend for <strong>{incomeAdvice.month ?? "the selected month"}</strong> (not all-time totals).
          </p>
          <div className="finsight-stat-chips">
            <div className="finsight-stat-chip">
              <span className="finsight-stat-chip-label">Monthly income (reference)</span>
              <span className="finsight-stat-chip-value">₹{formatINR(incomeAdvice.monthly_income)}</span>
            </div>
            <div className="finsight-stat-chip">
              <span className="finsight-stat-chip-label">Spend in {incomeAdvice.month ?? "month"}</span>
              <span className="finsight-stat-chip-value">₹{formatINR(incomeAdvice.monthly_spend)}</span>
            </div>
            <div className="finsight-stat-chip">
              <span className="finsight-stat-chip-label">{incomeAdvice.surplus >= 0 ? "Surplus" : "Overspend"}</span>
              <span
                className="finsight-stat-chip-value"
                style={{ color: incomeAdvice.surplus >= 0 ? "var(--finsight-success)" : "var(--finsight-danger)" }}
              >
                ₹{formatINR(Math.abs(incomeAdvice.surplus))}
              </span>
            </div>
          </div>
          <RichAdviceText text={incomeAdvice.advice} />
        </>
      ) : incomeAdvice && !incomeAdvice.advice ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>No advice available for this period.</p>
      ) : null}
    </div>
  );
}
