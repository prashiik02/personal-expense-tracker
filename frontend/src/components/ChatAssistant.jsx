import React, { useState } from "react";
import { askAssistant } from "../api/assistantApi";
import RichAdviceText from "./RichAdviceText";

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
      <div className="finsight-card-title">Chat</div>
      <textarea
        className="finsight-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={3}
        style={{ width: "100%", marginBottom: "12px", resize: "vertical" }}
        placeholder="Ask about your spending, budgets, or taxes…"
      />
      <div style={{ display: "flex", gap: "12px" }}>
        <button type="button" className="finsight-btn finsight-btn-primary" onClick={send} disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </button>
        <button type="button" className="finsight-btn" onClick={() => { setQuestion(""); setAnswer(null); }}>
          Clear
        </button>
      </div>
      {answer && (
        <div style={{ marginTop: "16px", padding: "16px", background: "var(--finsight-surface2)", borderRadius: "var(--finsight-radius-sm)", fontSize: "14px", border: "1px solid var(--finsight-border)", lineHeight: 1.6 }}>
          {typeof answer === "string" ? (
            <RichAdviceText text={answer} />
          ) : answer.error ? (
            <div style={{ color: "var(--finsight-danger)" }}>{String(answer.error)}</div>
          ) : answer.answer ? (
            <RichAdviceText text={typeof answer.answer === "string" ? answer.answer : String(answer.answer)} />
          ) : (
            <RichAdviceText text={String(answer)} />
          )}
        </div>
      )}
    </div>
  );
}
