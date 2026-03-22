import React, { useState } from "react";
import { getTaxSuggestions } from "../api/assistantApi";
import RichAdviceText from "./RichAdviceText";

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
      <div className="finsight-card-title">Tax suggestions</div>
      <button type="button" className="finsight-btn finsight-btn-primary" onClick={fetch} disabled={loading}>{loading ? "Thinking…" : "Get Suggestions"}</button>
      {suggestions?.error && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", border: "1px solid var(--finsight-danger)", color: "var(--finsight-danger)" }}>
          {suggestions.error}
        </div>
      )}
      {suggestions && !suggestions.error && (
        <div style={{ marginTop: "16px" }}>
          <div style={{ fontSize: "10px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px" }}>Suggestions</div>
          <div className="finsight-tax-suggestions-box" style={{ padding: "14px 16px", background: "var(--finsight-surface2)", borderRadius: "10px", border: "1px solid var(--finsight-border)" }}>
            {typeof suggestions === "string" ? (
              <RichAdviceText text={suggestions} />
            ) : Array.isArray(suggestions) ? (
              <div className="finsight-stacked-advice">
                {suggestions.map((s, i) => {
                  const raw = typeof s === "string" ? s : s?.text || String(s);
                  return (
                    <div key={i} className="finsight-stacked-advice-item">
                      <RichAdviceText text={raw} />
                    </div>
                  );
                })}
              </div>
            ) : Array.isArray(suggestions?.suggestions) ? (
              <div className="finsight-stacked-advice">
                {suggestions.suggestions.map((s, i) => {
                  const raw = typeof s === "string" ? s : s?.text || String(s);
                  return (
                    <div key={i} className="finsight-stacked-advice-item">
                      <RichAdviceText text={raw} />
                    </div>
                  );
                })}
              </div>
            ) : suggestions?.suggestions && typeof suggestions.suggestions === "string" ? (
              <RichAdviceText text={suggestions.suggestions} />
            ) : (
              <RichAdviceText text={String(suggestions)} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
