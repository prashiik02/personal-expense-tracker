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
      {suggestions?.error && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", border: "1px solid var(--finsight-danger)", color: "var(--finsight-danger)" }}>
          {suggestions.error}
        </div>
      )}
      {suggestions && !suggestions.error && (
        <div style={{ marginTop: "16px" }}>
          <div style={{ fontSize: "10px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px" }}>Suggestions</div>
          <div style={{ padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", border: "1px solid var(--finsight-border)", lineHeight: 1.6 }}>
            {typeof suggestions === "string" ? (
              <div style={{ whiteSpace: "pre-wrap" }}>{suggestions}</div>
            ) : Array.isArray(suggestions) ? (
              <ul style={{ margin: 0, paddingLeft: "20px" }}>
                {suggestions.map((s, i) => <li key={i}>{typeof s === "string" ? s : s?.text || String(s)}</li>)}
              </ul>
            ) : Array.isArray(suggestions?.suggestions) ? (
              <ul style={{ margin: 0, paddingLeft: "20px" }}>
                {suggestions.suggestions.map((s, i) => <li key={i}>{typeof s === "string" ? s : s?.text || String(s)}</li>)}
              </ul>
            ) : suggestions?.suggestions && typeof suggestions.suggestions === "string" ? (
              <div style={{ whiteSpace: "pre-wrap" }}>{suggestions.suggestions}</div>
            ) : (
              <div style={{ whiteSpace: "pre-wrap" }}>{String(suggestions)}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
