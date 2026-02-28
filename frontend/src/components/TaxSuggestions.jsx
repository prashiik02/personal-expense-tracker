import React, { useState } from "react";
import { getTaxSuggestions } from "../api/assistantApi";

export default function TaxSuggestions() {
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);

  async function fetch() {
    setLoading(true);
    try {
      const res = await getTaxSuggestions();
      setSuggestions(res.suggestions || res);
    } catch (e) {
      setSuggestions({ error: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Tax Saving Suggestions</div>
      <button type="button" className="finsight-btn finsight-btn-primary" onClick={fetch} disabled={loading}>{loading ? "Thinking…" : "Get Suggestions"}</button>
      {suggestions && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid var(--finsight-border)" }}>
          {typeof suggestions === "string" ? suggestions : JSON.stringify(suggestions, null, 2)}
        </div>
      )}
    </div>
  );
}
