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
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 6, marginTop: 12 }}>
      <h3>Tax Saving Suggestions</h3>
      <button onClick={fetch} disabled={loading}>{loading ? "Thinking…" : "Get Suggestions"}</button>
      {suggestions && (
        <div style={{ marginTop: 12 }}>
          <pre style={{ whiteSpace: "pre-wrap" }}>{typeof suggestions === 'string' ? suggestions : JSON.stringify(suggestions, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
