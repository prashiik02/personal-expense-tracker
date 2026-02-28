import React, { useState, useEffect } from "react";
import { getIncomeAdvice } from "../api/assistantApi";

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
      <div className="finsight-card-title" style={{ marginBottom: "12px" }}>Income vs spending</div>
      {loading ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>Loading advice…</p>
      ) : error ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-danger)" }}>{error}</p>
      ) : incomeAdvice?.message ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>{incomeAdvice.message}</p>
      ) : incomeAdvice?.advice ? (
        <>
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "12px", fontSize: "12px" }}>
            <span>Income: <strong>₹{formatINR(incomeAdvice.monthly_income)}</strong></span>
            <span>Spend ({incomeAdvice.month ?? "month"}): <strong>₹{formatINR(incomeAdvice.monthly_spend)}</strong></span>
            <span style={{ color: incomeAdvice.surplus >= 0 ? "var(--finsight-success)" : "var(--finsight-danger)" }}>
              {incomeAdvice.surplus >= 0 ? "Surplus" : "Overspend"}: <strong>₹{formatINR(Math.abs(incomeAdvice.surplus))}</strong>
            </span>
          </div>
          <div style={{ fontSize: "12px", whiteSpace: "pre-wrap", color: "var(--finsight-text)", lineHeight: 1.5 }}>
            {incomeAdvice.advice}
          </div>
        </>
      ) : incomeAdvice && !incomeAdvice.advice ? (
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>No advice available for this period.</p>
      ) : null}
    </div>
  );
}
