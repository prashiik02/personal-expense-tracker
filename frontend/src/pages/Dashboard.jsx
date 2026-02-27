import { useEffect, useState } from "react";
import axios from "axios";
import TransactionTable from "../components/TransactionTable";
import MonthlyChart from "../components/MonthlyChart";
import SummaryCard from "../components/SummaryCard";
import InsightCard from "../components/InsightCard";
import React from "react";
export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [insight, setInsight] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const tx = await axios.get("http://localhost:5000/transactions");
      const sum = await axios.get("http://localhost:5000/analytics/monthly");
      const ins = await axios.get("http://localhost:5000/insights");

      setTransactions(tx.data);
      setSummary(sum.data);
      setInsight(ins.data);
    };

    fetchData();
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>Dashboard</h2>

      {/* ===== SUMMARY CARDS ===== */}
      {summary && (
        <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
          <SummaryCard title="Total Income" amount={summary.total_income} />
          <SummaryCard title="Total Expense" amount={summary.total_expense} />
          <SummaryCard title="Savings" amount={summary.savings} />
        </div>
      )}

      {/* ===== INSIGHT CARD ===== */}
      {insight && (
        <InsightCard
          title={insight.title}
          message={insight.message}
          type={insight.type}
        />
      )}

      {/* ===== CHART ===== */}
      <MonthlyChart data={transactions} />

      {/* ===== TABLE ===== */}
      <TransactionTable transactions={transactions} />
    </div>
  );
}