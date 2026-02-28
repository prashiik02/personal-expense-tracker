import React, { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { getReport } from "../api/assistantApi";

function formatINR(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

export default function ReportView() {
  const [month, setMonth] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);

  async function fetchReport() {
    setLoading(true);
    try {
      const res = await getReport(month || undefined);
      setReport(res);
    } catch (e) {
      setReport({ error: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  const data = report?.data;
  const byMonth = data?.by_month || [];
  const totals = data?.totals || {};
  const chartData = Array.isArray(byMonth) ? byMonth.map((m) => ({ period: m?.period || m?.month || "—", total_spend: m?.total_spend ?? 0, total_income: m?.total_income ?? 0 })) : [];

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Monthly Health Report</div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        <input className="finsight-input" placeholder="YYYY-MM (optional)" value={month} onChange={(e) => setMonth(e.target.value)} style={{ flex: "1", minWidth: 140 }} />
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={fetchReport} disabled={loading}>{loading ? "Loading…" : "Generate"}</button>
      </div>

      {report?.error && (
        <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", border: "1px solid var(--finsight-danger)", color: "var(--finsight-danger)" }}>
          {report.error}
        </div>
      )}

      {report && !report.error && report.report && (
        <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid var(--finsight-border)", marginBottom: "16px" }}>
          {report.report}
        </div>
      )}

      {report && !report.error && data && (
        <div style={{ marginTop: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "16px" }}>
            <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", border: "1px solid var(--finsight-border)" }}>
              <div style={{ fontSize: "10px", color: "var(--finsight-muted)", marginBottom: "4px" }}>Total spend</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--finsight-accent2)" }}>₹{formatINR(totals.total_spend)}</div>
            </div>
            <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", border: "1px solid var(--finsight-border)" }}>
              <div style={{ fontSize: "10px", color: "var(--finsight-muted)", marginBottom: "4px" }}>Total income</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--finsight-accent3)" }}>₹{formatINR(totals.total_income)}</div>
            </div>
            <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", border: "1px solid var(--finsight-border)" }}>
              <div style={{ fontSize: "10px", color: "var(--finsight-muted)", marginBottom: "4px" }}>Net</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: (totals.net ?? 0) >= 0 ? "var(--finsight-success)" : "var(--finsight-danger)" }}>₹{formatINR(totals.net)}</div>
            </div>
          </div>
          {chartData.length > 0 && (
            <div style={{ height: 240, marginTop: "8px" }}>
              <div style={{ fontSize: "10px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px" }}>Spend vs income by month</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 24, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--finsight-border)" />
                  <XAxis dataKey="period" tick={{ fontSize: 11, fill: "var(--finsight-muted)" }} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--finsight-muted)" }} tickFormatter={(v) => `₹${v >= 1000 ? (v / 1000) + "k" : v}`} />
                  <Tooltip formatter={(v) => `₹${formatINR(v)}`} />
                  <Bar dataKey="total_spend" name="Spend" fill="var(--finsight-accent2)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total_income" name="Income" fill="var(--finsight-accent3)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
