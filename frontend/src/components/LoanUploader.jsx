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
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 6, marginTop: 12 }}>
      <h3>Loan Document Analyzer</h3>
      <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <div style={{ marginTop: 8 }}>
        <button onClick={submit} disabled={loading || !file}>{loading ? "Uploading…" : "Upload & Analyze"}</button>
      </div>

      {result && (
        <div style={{ marginTop: 12 }}>
          <h4>Parsed Result</h4>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
