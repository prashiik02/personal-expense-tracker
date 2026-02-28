import React, { useState } from "react";
import { uploadLoan } from "../api/assistantApi";

export default function LoanUploader() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function submit() {
    if (!file) return;
    setLoading(true);
    try {
      const res = await uploadLoan(file);
      setResult(res);
    } catch (e) {
      setResult({ error: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Loan Document Analyzer</div>
      <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} style={{ fontSize: "12px", color: "var(--finsight-muted)" }} />
      <div style={{ marginTop: "12px" }}>
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={submit} disabled={loading || !file}>{loading ? "Uploading…" : "Upload & Analyze"}</button>
      </div>

      {result && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid var(--finsight-border)" }}>
          {JSON.stringify(result, null, 2)}
        </div>
      )}
    </div>
  );
}
