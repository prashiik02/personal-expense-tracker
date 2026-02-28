import React, { useEffect, useState, useMemo } from "react";
import { useAuth } from "../hooks/useAuth";
import { fetchDashboardOverview } from "../api/statementApi";
import AnalyticsCard from "../components/AnalyticsCard";
import SectionHeader from "../components/SectionHeader";
import CategoryBreakdown from "../components/CategoryBreakdown";
import QuickActionCard from "../components/QuickActionCard";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  LineChart,
  Line,
} from "recharts";

const COLORS = {
  primary: "#3498db",
  dark: "#2c3e50",
  light: "#fafafa",
  white: "#ffffff",
  gray: "#7f8c8d",
  lightGray: "#ecf0f1",
  border: "#e0e6ed",
  success: "#27ae60",
  warning: "#f39c12",
  danger: "#e74c3c",
  info: "#9b59b6",
  secondary: "#1abc9c",
};

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

  const categoryData = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    if (months.length === 0) return {};
    const latestMonth = months[months.length - 1];
    const cats = latestMonth?.categories || {};
    const result = {};
    Object.entries(cats).forEach(([key, val]) => {
      result[key] = val?.total || 0;
    });
    return result;
  }, [data]);

  const totals = data?.time_aggregates?.totals || {
    total_spend: 0,
    total_income: 0,
    net: 0,
  };

  // Calculate trend for net savings
  const previousMonthTotal = monthlySeries.length >= 2 
    ? monthlySeries[monthlySeries.length - 2].total 
    : 0;
  const currentMonthTotal = monthlySeries.length > 0 
    ? monthlySeries[monthlySeries.length - 1].total 
    : 0;
  const spendTrend = previousMonthTotal > 0 
    ? ((currentMonthTotal - previousMonthTotal) / previousMonthTotal * 100) 
    : 0;

  return (
    <div style={{ 
      minHeight: "100vh", 
      backgroundColor: COLORS.light, 
      padding: "24px",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif"
    }}>
      {!user && (
        <div style={{ textAlign: "center", padding: "48px 24px" }}>
          <h2 style={{ color: COLORS.dark }}>You are not signed in.</h2>
          <p style={{ color: COLORS.gray, marginTop: "12px" }}>Please log in to view your dashboard.</p>
        </div>
      )}

      {user && (
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          {/* Header */}
          <div style={{ marginBottom: "32px" }}>
            <h1 style={{ 
              fontSize: "32px", 
              fontWeight: 700, 
              color: COLORS.dark,
              marginBottom: "8px"
            }}>
              Welcome back, {user.email.split("@")[0]}
            </h1>
            <p style={{ color: COLORS.gray, fontSize: "14px" }}>
              Here's your financial overview
            </p>
          </div>

          {loading && (
            <div style={{ 
              padding: "32px", 
              textAlign: "center", 
              backgroundColor: COLORS.white,
              borderRadius: "12px"
            }}>
              <p style={{ color: COLORS.gray }}>Loading your data…</p>
            </div>
          )}

          {error && (
            <div style={{ 
              padding: "16px", 
              backgroundColor: "#fee", 
              border: `1px solid ${COLORS.danger}`,
              borderRadius: "8px",
              color: COLORS.danger,
              marginBottom: "24px",
              fontSize: "14px"
            }}>
              {error}
            </div>
          )}

          {data && !loading && (
            <>
              {/* Key Metrics Section */}
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", 
                gap: "20px",
                marginBottom: "32px"
              }}>
                <AnalyticsCard 
                  icon="📊"
                  label="Total Transactions"
                  value={data.transactions_count}
                  subtitle="this period"
                  color={COLORS.info}
                />
                <AnalyticsCard 
                  icon="💸"
                  label="Total Spend"
                  value={`₹ ${formatINR(totals.total_spend || 0)}`}
                  subtitle="outflow"
                  trend={spendTrend}
                  color={COLORS.danger}
                />
                <AnalyticsCard 
                  icon="💰"
                  label="Total Income"
                  value={`₹ ${formatINR(totals.total_income || 0)}`}
                  subtitle="inflow"
                  color={COLORS.success}
                />
                <AnalyticsCard 
                  icon="🎯"
                  label="Net Savings"
                  value={`₹ ${formatINR(totals.net || 0)}`}
                  subtitle={(totals.net || 0) >= 0 ? "positive balance" : "deficit"}
                  color={(totals.net || 0) >= 0 ? COLORS.success : COLORS.danger}
                  trend={(totals.net || 0) >= 0 ? 5 : -5}
                />
              </div>

              {/* Monthly Trend Section */}
              {monthlySeries.length > 0 && (
                <div style={{ 
                  backgroundColor: COLORS.white, 
                  borderRadius: "12px", 
                  padding: "24px",
                  marginBottom: "32px",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
                }}>
                  <SectionHeader 
                    icon="📈" 
                    title="Spending Trend" 
                    subtitle="Monthly breakdown"
                  />
                  <div style={{ height: 280, marginTop: "16px" }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={monthlySeries}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.lightGray} />
                        <XAxis dataKey="period" stroke={COLORS.gray} />
                        <YAxis stroke={COLORS.gray} />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: COLORS.white, 
                            border: `1px solid ${COLORS.lightGray}`,
                            borderRadius: "8px"
                          }}
                          formatter={(value) => `₹ ${formatINR(Number(value))}`}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="total" 
                          stroke={COLORS.primary} 
                          dot={{ fill: COLORS.primary, r: 4 }}
                          activeDot={{ r: 6 }}
                          strokeWidth={2}
                          name="Total Spend"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Category Breakdown */}
              {Object.keys(categoryData).length > 0 && (
                <div style={{ 
                  backgroundColor: COLORS.white, 
                  borderRadius: "12px", 
                  padding: "24px",
                  marginBottom: "32px",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
                }}>
                  <SectionHeader 
                    icon="🏷️" 
                    title="Spending by Category" 
                    subtitle="Latest month breakdown"
                  />
                  <div style={{ marginTop: "16px" }}>
                    <CategoryBreakdown categories={categoryData} />
                  </div>
                </div>
              )}

              {/* Top Merchants */}
              {data.top_merchants && data.top_merchants.length > 0 && (
                <div style={{ 
                  backgroundColor: COLORS.white, 
                  borderRadius: "12px", 
                  padding: "24px",
                  marginBottom: "32px",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
                }}>
                  <SectionHeader 
                    icon="🏪" 
                    title="Top Merchants" 
                    subtitle="By total spending"
                  />
                  <ul style={{ 
                    listStyle: "none", 
                    padding: "0", 
                    marginTop: "12px"
                  }}>
                    {data.top_merchants.slice(0, 5).map((m, idx) => (
                      <li 
                        key={m.merchant}
                        style={{
                          padding: "12px 0",
                          borderBottom: idx < Math.min(4, data.top_merchants.length - 1) ? `1px solid ${COLORS.lightGray}` : "none",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          fontSize: "14px"
                        }}
                      >
                        <div>
                          <strong style={{ color: COLORS.dark }}>{m.merchant}</strong>
                          <div style={{ color: COLORS.gray, fontSize: "12px", marginTop: "2px" }}>
                            {m.count} {m.count === 1 ? "transaction" : "transactions"}
                          </div>
                        </div>
                        <div style={{ color: COLORS.danger, fontWeight: 600 }}>
                          ₹{formatINR(m.total_spend)}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Quick Actions Section */}
              <div style={{ 
                backgroundColor: COLORS.white, 
                borderRadius: "12px", 
                padding: "24px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
              }}>
                <SectionHeader 
                  icon="⚡" 
                  title="Quick Actions" 
                  subtitle="Access key features"
                />
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: "16px",
                  marginTop: "16px"
                }}>
                  <QuickActionCard 
                    icon="🏷️"
                    title="Categorize Transactions"
                    description="Organize and tag your expenses"
                    color={COLORS.secondary}
                    link="/categorize"
                  />
                  <QuickActionCard 
                    icon="🤖"
                    title="AI Assistant"
                    description="Get financial insights and advice"
                    color={COLORS.info}
                    link="/assistant"
                  />
                  <QuickActionCard 
                    icon="📄"
                    title="Upload Statement"
                    description="Import your bank statements"
                    color={COLORS.primary}
                    link="/statements"
                  />
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
