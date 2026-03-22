import React, { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import { generateBudget } from "../api/assistantApi";
import RichAdviceText from "./RichAdviceText";

const CHART_COLORS = ["#166534", "#ca8a04", "#475569", "#7c3aed", "#b91c1c", "#0d9488", "#a16207", "#4f46e5"];

function formatINR(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "—";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

export default function BudgetGenerator() {
  const [loading, setLoading] = useState(false);
  const [budget, setBudget] = useState(null);

  async function createBudget() {
    setLoading(true);
    setBudget(null);
    try {
      const res = await generateBudget();
      setBudget(res.budget || res);
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

  const barData = useMemo(() => {
    if (!hasBudgets) return [];
    return Object.entries(budget.budgets)
      .filter(([, amt]) => Number(amt) > 0)
      .map(([name, value], i) => ({
        name: name.length > 36 ? `${name.slice(0, 34)}…` : name,
        fullName: name,
        value: Number(value),
        fill: CHART_COLORS[i % CHART_COLORS.length],
      }))
      .sort((a, b) => b.value - a.value);
  }, [budget, hasBudgets]);

  return (
    <div>
      <div className="finsight-card-title">Budget</div>
      <p style={{ fontSize: "0.9375rem", color: "var(--finsight-muted)", marginBottom: "16px", lineHeight: 1.5 }}>
        Uses your monthly income and last 3 months&apos; spending to suggest a category-wise budget.
      </p>
      <button type="button" className="finsight-btn finsight-btn-primary" onClick={createBudget} disabled={loading}>
        {loading ? "Working…" : "Generate Budget"}
      </button>

      {budget?.error && (
        <div
          style={{
            marginTop: "16px",
            padding: "12px 16px",
            background: "var(--finsight-surface2)",
            borderRadius: "8px",
            fontSize: "0.875rem",
            border: "1px solid var(--finsight-danger)",
            color: "var(--finsight-danger)",
          }}
        >
          {budget.error}
        </div>
      )}

      {budget && !budget.error && (
        <div style={{ marginTop: "20px" }}>
          {hasBudgets && (
            <>
              <div
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--finsight-muted)",
                  marginBottom: "12px",
                }}
              >
                Budget breakdown
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                <div className="finsight-budget-chart-wrap" style={{ minHeight: Math.max(200, barData.length * 36) }}>
                  <ResponsiveContainer width="100%" height={Math.max(200, barData.length * 36)}>
                    <BarChart
                      data={barData}
                      layout="vertical"
                      margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--finsight-border)" />
                      <XAxis
                        type="number"
                        tickFormatter={(v) => `₹${v >= 1000 ? `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)}k` : v}`}
                        tick={{ fontSize: 11, fill: "var(--finsight-muted)" }}
                        axisLine={false}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={130}
                        tick={{ fontSize: 11, fill: "var(--finsight-text)" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        formatter={(v) => [`₹${formatINR(v)}`, "Budget"]}
                        labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName ?? ""}
                        contentStyle={{
                          background: "var(--finsight-surface)",
                          border: "1px solid var(--finsight-border)",
                          borderRadius: "8px",
                          fontSize: "13px",
                        }}
                      />
                      <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={28}>
                        {barData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {Object.entries(budget.budgets).map(([cat, amt]) => (
                    <div
                      key={cat}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "10px 14px",
                        background: "var(--finsight-surface2)",
                        borderRadius: "8px",
                        fontSize: "0.875rem",
                      }}
                    >
                      <span style={{ color: "var(--finsight-text)" }}>{cat}</span>
                      <span style={{ fontWeight: 600, color: "var(--fs-green)" }}>₹{formatINR(Number(amt))}</span>
                    </div>
                  ))}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px 14px",
                      borderTop: "2px solid var(--finsight-border)",
                      marginTop: "4px",
                      fontSize: "0.875rem",
                      fontWeight: 700,
                    }}
                  >
                    <span>Total</span>
                    <span style={{ color: "var(--fs-green)", fontFamily: "var(--font-display)" }}>
                      ₹{formatINR(totalBudget)}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
          {budget.explanation && (
            <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid var(--finsight-border)" }}>
              <div
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--finsight-muted)",
                  marginBottom: "10px",
                }}
              >
                Notes
              </div>
              <RichAdviceText text={budget.explanation} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
