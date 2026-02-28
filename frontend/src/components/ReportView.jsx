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
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
      <h3>Monthly Health Report</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input placeholder="YYYY-MM (optional)" value={month} onChange={(e) => setMonth(e.target.value)} />
        <button onClick={fetchReport} disabled={loading}>{loading ? "Loading…" : "Generate"}</button>
      </div>

      {report && (
        <div>
          <h4>Report</h4>
          <pre style={{ whiteSpace: "pre-wrap" }}>{report.report || JSON.stringify(report.data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
