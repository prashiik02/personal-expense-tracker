import React, { useState } from "react";
import { explainAnomaly } from "../api/assistantApi";

export default function AnomalyExplainer() {
  const [date, setDate] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function submit() {
    setLoading(true);
    try {
      const payload = { details: { date, amount: Number(amount || 0), description } };
      const res = await explainAnomaly(payload);
      setResult(res);
    } catch (e) {
      setResult({ error: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Anomaly Explainer</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <input className="finsight-input" placeholder="Date (YYYY-MM-DD)" value={date} onChange={(e) => setDate(e.target.value)} />
        <input className="finsight-input" placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <input className="finsight-input" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={submit} disabled={loading}>{loading ? "Thinking…" : "Explain"}</button>
      </div>

      {result && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid var(--finsight-border)" }}>
          {JSON.stringify(result, null, 2)}
        </div>
      )}
    </div>
  );
}
