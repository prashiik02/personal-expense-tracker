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
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 6, marginTop: 12 }}>
      <h3>Anomaly Explainer</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <input placeholder="Date (YYYY-MM-DD)" value={date} onChange={(e) => setDate(e.target.value)} />
        <input placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <div>
          <button onClick={submit} disabled={loading}>{loading ? "Thinking…" : "Explain"}</button>
        </div>
      </div>

      {result && (
        <div style={{ marginTop: 12 }}>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
