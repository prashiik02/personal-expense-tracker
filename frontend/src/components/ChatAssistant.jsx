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
      const msg = e.response?.data?.error || e.message || String(e);
      setAnswer({ error: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="finsight-card-title" style={{ marginBottom: "16px" }}>Assistant Chat</div>
      <textarea
        className="finsight-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={4}
        style={{ width: "100%", marginBottom: "12px", resize: "vertical" }}
        placeholder="Ask about your spending, budgets, or taxes"
      />
      <div style={{ display: "flex", gap: "8px" }}>
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={send} disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </button>
        <button type="button" className="finsight-btn" onClick={() => { setQuestion(""); setAnswer(null); }}>
          Clear
        </button>
      </div>

      {answer && (
        <div style={{ marginTop: "16px", padding: "12px", background: "var(--finsight-surface2)", borderRadius: "10px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid var(--finsight-border)" }}>
          {typeof answer === "string" ? answer : (answer.error ? String(answer.error) : JSON.stringify(answer, null, 2))}
        </div>
      )}
    </div>
  );
}
