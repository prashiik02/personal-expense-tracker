import React, { useState } from "react";
import { askAssistant } from "../api/assistantApi";

export default function ChatAssistant() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null);

  async function send() {
    if (!question) return;
    setLoading(true);
    try {
      const res = await askAssistant(question);
      setAnswer(res.answer || res);
    } catch (e) {
      setAnswer({ error: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
      <h3>Assistant Chat</h3>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={4}
        style={{ width: "100%", marginBottom: 8 }}
        placeholder="Ask about your spending, budgets, or taxes"
      />
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={send} disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </button>
        <button onClick={() => { setQuestion(""); setAnswer(null); }}>
          Clear
        </button>
      </div>

      {answer && (
        <div style={{ marginTop: 12, whiteSpace: "pre-wrap" }}>
          <strong>Answer:</strong>
          <div style={{ marginTop: 8 }}>{typeof answer === "string" ? answer : JSON.stringify(answer, null, 2)}</div>
        </div>
      )}
    </div>
  );
}
