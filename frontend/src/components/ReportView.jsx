import React, { useState } from "react";
import { getReport } from "../api/assistantApi";

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

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Monthly Health Report</div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        <input className="finsight-input" placeholder="YYYY-MM (optional)" value={month} onChange={(e) => setMonth(e.target.value)} style={{ flex: "1", minWidth: 140 }} />
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={fetchReport} disabled={loading}>{loading ? "Loading…" : "Generate"}</button>
      </div>

      {report && (
        <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid var(--finsight-border)" }}>
          {report.report || JSON.stringify(report.data, null, 2)}
        </div>
      )}
    </div>
  );
}
