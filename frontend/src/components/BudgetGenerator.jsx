import React, { useState } from "react";
import { generateBudget } from "../api/assistantApi";

export default function BudgetGenerator() {
  const [loading, setLoading] = useState(false);
  const [budget, setBudget] = useState(null);

  async function createBudget() {
    setLoading(true);
    try {
      const res = await generateBudget();
      setBudget(res.budget || res);
    } catch (e) {
      setBudget({ error: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
      <h3>Smart Budget</h3>
      <button onClick={createBudget} disabled={loading}>{loading ? "Working…" : "Generate Budget"}</button>

      {budget && (
        <div style={{ marginTop: 12 }}>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(budget, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
