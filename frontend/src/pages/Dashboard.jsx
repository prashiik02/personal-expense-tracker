import React, { useEffect, useState, useMemo } from "react";
import { useAuth } from "../hooks/useAuth";
import { fetchDashboardOverview } from "../api/statementApi";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function formatINR(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "-";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    let isMounted = true;
    setLoading(true);
    setError("");
    fetchDashboardOverview()
      .then((res) => {
        if (!isMounted) return;
        setData(res);
      })
      .catch((err) => {
        if (!isMounted) return;
        const msg =
          err?.response?.data?.error ||
          err?.response?.data?.msg ||
          err?.message ||
          "Failed to load dashboard data";
        setError(msg);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [user]);

  const monthlySeries = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    return months.map((m) => {
      const cats = m.categories || {};
      const total = Object.values(cats).reduce(
        (sum, v) => sum + (v?.total || 0),
        0
      );
      return { period: m.period, total };
    });
  }, [data]);

  const totals = data?.time_aggregates?.totals || {
    total_spend: 0,
    total_income: 0,
    net: 0,
  };

  return (
    <div style={{ padding: "24px" }}>
      <h2 style={{ marginBottom: "16px" }}>Dashboard</h2>

      {!user && <p>You are not signed in.</p>}

      {user && (
        <>
          <p style={{ marginBottom: "16px" }}>
            Signed in as <strong>{user.email}</strong>
          </p>

          {loading && <p>Loading your data…</p>}
          {error && (
            <p style={{ color: "red", marginBottom: "12px" }}>{error}</p>
          )}

          {data && (
            <>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "16px",
                  marginBottom: "24px",
                }}
              >
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    background: "#f9fafb",
                  }}
                >
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>
                    Total transactions
                  </div>
                  <div style={{ fontSize: "20px", fontWeight: 600 }}>
                    {data.transactions_count}
                  </div>
                </div>
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    background: "#f9fafb",
                  }}
                >
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>
                    Total spend
                  </div>
                  <div style={{ fontSize: "20px", fontWeight: 600 }}>
                    ₹ {formatINR(totals.total_spend || 0)}
                  </div>
                </div>
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    background: "#f9fafb",
                  }}
                >
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>
                    Total income
                  </div>
                  <div style={{ fontSize: "20px", fontWeight: 600 }}>
                    ₹ {formatINR(totals.total_income || 0)}
                  </div>
                </div>
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    background: "#f9fafb",
                  }}
                >
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>
                    Net savings
                  </div>
                  <div
                    style={{
                      fontSize: "20px",
                      fontWeight: 600,
                      color: (totals.net || 0) >= 0 ? "#16a34a" : "#dc2626",
                    }}
                  >
                    ₹ {formatINR(totals.net || 0)}
                  </div>
                </div>
              </div>

              <div style={{ height: 260, marginBottom: "32px" }}>
                <h3 style={{ fontSize: "16px", marginBottom: "8px" }}>
                  Monthly spend trend
                </h3>
                {monthlySeries.length === 0 ? (
                  <p style={{ fontSize: "14px", color: "#6b7280" }}>
                    No data yet. Upload a statement or categorize some
                    transactions to see trends here.
                  </p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={monthlySeries}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip
                        formatter={(value) => `₹ ${formatINR(Number(value))}`}
                      />
                      <Legend />
                      <Bar
                        dataKey="total"
                        name="Total spend"
                        fill="#6366F1"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              <div>
                <h3 style={{ fontSize: "16px", marginBottom: "8px" }}>
                  Top merchants by spend
                </h3>
                {data.top_merchants && data.top_merchants.length > 0 ? (
                  <ul style={{ fontSize: "14px", color: "#374151" }}>
                    {data.top_merchants.map((m) => (
                      <li key={m.merchant} style={{ marginBottom: "4px" }}>
                        <strong>{m.merchant}</strong> — ₹{" "}
                        {formatINR(m.total_spend)} ({m.count}{" "}
                        {m.count === 1 ? "txn" : "txns"})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ fontSize: "14px", color: "#6b7280" }}>
                    No merchant data yet.
                  </p>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
