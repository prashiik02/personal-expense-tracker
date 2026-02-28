import React, { useState } from "react";
import { uploadLoan } from "../api/assistantApi";

function formatINR(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

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

  const parsed = result?.parsed && typeof result.parsed === "object" ? result.parsed : null;

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Loan Document Analyzer</div>
      <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} style={{ fontSize: "12px", color: "var(--finsight-muted)" }} />
      <div style={{ marginTop: "12px" }}>
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={submit} disabled={loading || !file}>{loading ? "Uploading…" : "Upload & Analyze"}</button>
      </div>

      {result?.error && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", border: "1px solid var(--finsight-danger)", color: "var(--finsight-danger)" }}>
          {result.error}
        </div>
      )}

      {parsed && (
        <div style={{ marginTop: "16px" }}>
          <div style={{ fontSize: "10px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "12px" }}>Extracted loan summary</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "12px" }}>
            {[
              { label: "Principal", value: parsed.principal != null ? `₹${formatINR(parsed.principal)}` : "—" },
              { label: "Interest rate", value: parsed.interest_rate ?? "—" },
              { label: "Tenure (months)", value: parsed.tenure_months ?? "—" },
              { label: "EMI", value: parsed.emi != null ? `₹${formatINR(parsed.emi)}` : "—" },
              { label: "Sanction date", value: parsed.sanction_date ?? "—" },
              { label: "Lender", value: parsed.lender ?? "—" },
            ].map(({ label, value }) => (
              <div key={label} style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", border: "1px solid var(--finsight-border)" }}>
                <div style={{ fontSize: "10px", color: "var(--finsight-muted)", marginBottom: "4px" }}>{label}</div>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--finsight-text)" }}>{value}</div>
              </div>
            ))}
          </div>
          {parsed.prepayment_clause && (
            <div style={{ marginTop: "12px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", border: "1px solid var(--finsight-border)", fontSize: "12px", color: "var(--finsight-text)" }}>
              <div style={{ fontSize: "10px", color: "var(--finsight-muted)", marginBottom: "4px" }}>Prepayment / foreclosure</div>
              {parsed.prepayment_clause}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
