import React, { useState } from "react";
import { generateBudget } from "../api/assistantApi";

function formatINR(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "—";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

export default function BudgetGenerator() {
  const [loading, setLoading] = useState(false);
  const [budget, setBudget] = useState(null);
  const [showRaw, setShowRaw] = useState(false);

  async function createBudget() {
    setLoading(true);
    setBudget(null);
    try {
      const res = await generateBudget();
      setBudget(res.budget || res);
      setShowRaw(false);
    } catch (e) {
      const msg = e.response?.data?.error || e.message || String(e);
      setBudget({ error: msg });
    } finally {
      setLoading(false);
    }
  }

  const hasBudgets = budget && typeof budget === "object" && budget.budgets && Object.keys(budget.budgets).length > 0;
  const totalBudget = hasBudgets
    ? Object.values(budget.budgets).reduce((s, v) => s + (Number(v) || 0), 0)
    : 0;

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Smart Budget</div>
      <p style={{ fontSize: "11px", color: "var(--finsight-muted)", marginBottom: "12px" }}>
        Uses your monthly income and last 3 months’ spending to suggest a category-wise budget (INR).
      </p>
      <button type="button" className="finsight-btn finsight-btn-primary" onClick={createBudget} disabled={loading}>
        {loading ? "Working…" : "Generate Budget"}
      </button>

      {budget?.error && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", border: "1px solid var(--finsight-danger)", color: "var(--finsight-danger)" }}>
          {budget.error}
        </div>
      )}

      {budget && !budget.error && (
        <div style={{ marginTop: "16px" }}>
          {hasBudgets && (
            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontSize: "10px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px" }}>Suggested monthly budget</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {Object.entries(budget.budgets).map(([cat, amt]) => (
                  <div key={cat} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "var(--finsight-surface2)", borderRadius: "8px", fontSize: "12px" }}>
                    <span style={{ color: "var(--finsight-text)" }}>{cat}</span>
                    <span style={{ fontFamily: "Syne", fontWeight: 600, color: "var(--finsight-accent)" }}>₹{formatINR(Number(amt))}</span>
                  </div>
                ))}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", borderTop: "1px solid var(--finsight-border)", marginTop: "4px", fontSize: "12px", fontWeight: 700 }}>
                  <span>Total</span>
                  <span style={{ color: "var(--finsight-accent)" }}>₹{formatINR(totalBudget)}</span>
                </div>
              </div>
            </div>
          )}
          {budget.explanation && (
            <div style={{ fontSize: "12px", color: "var(--finsight-text)", lineHeight: 1.5, whiteSpace: "pre-wrap", marginBottom: "12px" }}>
              {budget.explanation}
            </div>
          )}
          <button type="button" className="finsight-btn" style={{ fontSize: "11px" }} onClick={() => setShowRaw((v) => !v)}>
            {showRaw ? "Hide" : "Show"} raw JSON
          </button>
          {showRaw && (
            <pre style={{ marginTop: "8px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "8px", fontSize: "11px", overflow: "auto", border: "1px solid var(--finsight-border)" }}>
              {JSON.stringify(budget, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
