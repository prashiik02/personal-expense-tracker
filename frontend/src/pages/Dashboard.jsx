import React, { useEffect, useState, useMemo } from "react";
import { useAuth } from "../hooks/useAuth";
import { fetchDashboardOverview, fetchTransactions, excludeTransactionFromAnalysis } from "../api/statementApi";
import { getIncomeAdvice } from "../api/assistantApi";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from "recharts";

const CHART_COLORS = ["#7c6af7", "#4ad8a0", "#f7c26a", "#f7706a", "#9b8cf9", "#6ae0f7", "#f7907a", "#c4b5fd"];
const PIE_COLORS = ["#7c6af7", "#4ad8a0", "#f7c26a", "#f7706a", "#9b8cf9", "#6ae0f7"];

function formatINR(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "-";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function loadDashboard(setData, setError, setLoading) {
  setLoading(true);
  setError("");
  fetchDashboardOverview()
    .then((res) => setData(res))
    .catch((err) => {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.msg ||
        err?.message ||
        "Failed to load dashboard data";
      setError(msg);
    })
    .finally(() => setLoading(false));
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [transactionsList, setTransactionsList] = useState(null);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  const [excludingId, setExcludingId] = useState(null);
  const [incomeAdvice, setIncomeAdvice] = useState(null);
  const [loadingIncomeAdvice, setLoadingIncomeAdvice] = useState(false);

  useEffect(() => {
    if (!user) return;
    let isMounted = true;
    loadDashboard(
      (res) => { if (isMounted) setData(res); },
      (msg) => { if (isMounted) setError(msg); },
      (v) => { if (isMounted) setLoading(v); }
    );
    return () => { isMounted = false; };
  }, [user]);

  const handleRefresh = () => {
    if (!user) return;
    loadDashboard(setData, setError, setLoading);
    setTransactionsList(null);
  };

  const latestMonth = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    return months.length > 0 ? months[months.length - 1].period : null;
  }, [data]);

  useEffect(() => {
    if (!user) return;
    const month = latestMonth || new Date().toISOString().slice(0, 7);
    setLoadingIncomeAdvice(true);
    getIncomeAdvice(month)
      .then((res) => setIncomeAdvice(res))
      .catch(() => setIncomeAdvice(null))
      .finally(() => setLoadingIncomeAdvice(false));
  }, [user, latestMonth]);

  const loadTransactionsList = () => {
    if (!latestMonth) return;
    setLoadingTransactions(true);
    setTransactionsList(null);
    fetchTransactions({ month: latestMonth, limit: 100 })
      .then((res) => setTransactionsList(res.transactions || []))
      .catch(() => setTransactionsList([]))
      .finally(() => setLoadingTransactions(false));
  };

  const handleExcludeFromAnalysis = (txnId) => {
    setExcludingId(txnId);
    excludeTransactionFromAnalysis(txnId)
      .then(() => { handleRefresh(); setTransactionsList((prev) => (prev || []).filter((t) => t.id !== txnId)); })
      .finally(() => setExcludingId(null));
  };

  const monthlySeries = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    return months.map((m) => {
      const cats = m.categories || {};
      const total = Object.values(cats).reduce((sum, v) => sum + (v?.total || 0), 0);
      return { period: m.period, total };
    });
  }, [data]);

  const categoryData = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    if (months.length === 0) return {};
    const latest = months[months.length - 1];
    const cats = latest?.categories || {};
    const result = {};
    Object.entries(cats).forEach(([key, val]) => {
      result[key] = val?.total ?? 0;
    });
    return result;
  }, [data]);

  const categoryListWithCount = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    if (months.length === 0) return [];
    const latest = months[months.length - 1];
    const cats = latest?.categories || {};
    return Object.entries(cats)
      .map(([key, val]) => ({ key, total: val?.total ?? 0, count: val?.count ?? 0 }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 8);
  }, [data]);

  const pieData = useMemo(() => {
    return categoryListWithCount.map((item, i) => ({
      name: item.key.split(" > ")[0] || item.key,
      value: item.total,
      fill: PIE_COLORS[i % PIE_COLORS.length],
    }));
  }, [categoryListWithCount]);

  const totals = data?.time_aggregates?.totals || { total_spend: 0, total_income: 0, net: 0 };
  const totalSpend = Number(totals.total_spend) || 0;
  const totalIncomeFromTxns = Number(totals.total_income) || 0;
  const referenceIncome = data?.monthly_income != null && Number(data.monthly_income) > 0 ? Number(data.monthly_income) : null;
  const totalIncome = referenceIncome != null ? referenceIncome : totalIncomeFromTxns;
  const net = totalIncome - totalSpend;
  const catTotal = categoryListWithCount.reduce((s, c) => s + c.total, 0);
  const maxCat = Math.max(...categoryListWithCount.map((c) => c.total), 1);

  if (!user) {
    return (
      <div className="finsight-card" style={{ textAlign: "center", padding: "48px 24px" }}>
        <p style={{ color: "var(--finsight-muted)" }}>You are not signed in.</p>
        <p style={{ color: "var(--finsight-muted)", marginTop: "8px" }}>Please log in to view your dashboard.</p>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <header className="finsight-header">
        <div>
          <div style={{ fontSize: "11px", color: "var(--finsight-muted)", marginTop: "4px" }}>
            Personal Finance Intelligence
          </div>
        </div>
        <div className="finsight-header-meta">
          {data && (
            <>
              Parsed: {data.transactions_count ?? 0} transactions
              {latestMonth && (
                <div className="finsight-period-badge">📅 {latestMonth}</div>
              )}
            </>
          )}
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            className="finsight-btn"
            style={{ marginTop: "8px" }}
          >
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>
      </header>

      {error && (
        <div className="finsight-alert-banner" style={{ borderColor: "var(--finsight-danger)" }}>
          <span className="finsight-alert-icon">⚠️</span>
          <div className="finsight-alert-text">{error}</div>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Alert: deficit/surplus — uses reference monthly income when set */}
          {totalSpend > 0 && (
            <div className={`finsight-alert-banner ${net < 0 ? "deficit" : "surplus"}`}>
              <span className="finsight-alert-icon">{net < 0 ? "⚠️" : "✓"}</span>
              <div className="finsight-alert-text">
                You spent <strong>₹{formatINR(totalSpend)}</strong> this period.
                {referenceIncome != null ? (
                  <> Your monthly income (reference) is <strong>₹{formatINR(totalIncome)}</strong>. </>
                ) : (
                  <> Recorded income from transactions: <strong>₹{formatINR(totalIncomeFromTxns)}</strong>. </>
                )}
                {net < 0 ? (
                  <> You are <strong>₹{formatINR(-net)} in deficit</strong> — spending exceeds income.</>
                ) : (
                  <> Net savings: <strong>₹{formatINR(net)}</strong>.</>
                )}
              </div>
            </div>
          )}

          {/* Income vs spending – personalized advice */}
          <div className="finsight-card" style={{ marginBottom: "20px" }}>
            <div className="finsight-card-title">Income vs spending</div>
            {loadingIncomeAdvice ? (
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>Loading advice…</p>
            ) : incomeAdvice?.message ? (
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>{incomeAdvice.message}</p>
            ) : incomeAdvice?.advice ? (
              <>
                <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "12px", fontSize: "12px" }}>
                  <span>Income: <strong>₹{formatINR(incomeAdvice.monthly_income)}</strong></span>
                  <span>Spend ({incomeAdvice.month ?? "month"}): <strong>₹{formatINR(incomeAdvice.monthly_spend)}</strong></span>
                  <span style={{ color: incomeAdvice.surplus >= 0 ? "var(--finsight-success)" : "var(--finsight-danger)" }}>
                    {incomeAdvice.surplus >= 0 ? "Surplus" : "Overspend"}: <strong>₹{formatINR(Math.abs(incomeAdvice.surplus))}</strong>
                  </span>
                </div>
                <div style={{ fontSize: "12px", whiteSpace: "pre-wrap", color: "var(--finsight-text)", lineHeight: 1.5 }}>
                  {incomeAdvice.advice}
                </div>
              </>
            ) : incomeAdvice && !incomeAdvice.advice ? (
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>No advice available for this period.</p>
            ) : null}
          </div>

          {/* KPI Grid — Total Income from analysis (reference monthly income when set) */}
          <div className="finsight-kpi-grid">
            <div className="finsight-kpi-card income">
              <div className="finsight-kpi-label">Total Income</div>
              <div className="finsight-kpi-value">₹{formatINR(totalIncome)}</div>
              <div className="finsight-kpi-sub">
                {referenceIncome != null ? "From your profile (reference)" : `${data.transactions_count ?? 0} transactions`}
              </div>
            </div>
            <div className="finsight-kpi-card spend">
              <div className="finsight-kpi-label">Total Spent</div>
              <div className="finsight-kpi-value">₹{formatINR(totalSpend)}</div>
              <div className="finsight-kpi-sub">Across {categoryListWithCount.length} categories</div>
            </div>
            <div className={`finsight-kpi-card net ${net >= 0 ? "surplus" : "deficit"}`}>
              <div className="finsight-kpi-label">Net Balance</div>
              <div className="finsight-kpi-value">{net >= 0 ? "₹" + formatINR(net) : "-₹" + formatINR(-net)}</div>
              <div className="finsight-kpi-sub">{net >= 0 ? "Surplus" : "Deficit"}</div>
            </div>
            <div className="finsight-kpi-card txn">
              <div className="finsight-kpi-label">Transactions</div>
              <div className="finsight-kpi-value">{data.transactions_count ?? 0}</div>
              <div className="finsight-kpi-sub">This period</div>
            </div>
          </div>

          {/* Main grid: Categories (horizontal bar chart) + Donut */}
          <div className="finsight-main-grid">
            <div className="finsight-card finsight-chart-card">
              <div className="finsight-card-title">Spending by Category</div>
              {categoryListWithCount.length === 0 ? (
                <p className="finsight-chart-empty">No spending data for latest month.</p>
              ) : (
                <div className="finsight-bar-chart-wrap">
                  <ResponsiveContainer width="100%" height={Math.max(200, categoryListWithCount.length * 48)}>
                    <BarChart
                      data={categoryListWithCount.map((item, i) => ({
                        name: item.key.length > 32 ? item.key.slice(0, 30) + "…" : item.key,
                        fullName: item.key,
                        value: item.total,
                        count: item.count,
                        fill: CHART_COLORS[i % CHART_COLORS.length],
                      }))}
                      layout="vertical"
                      margin={{ top: 8, right: 16, left: 4, bottom: 8 }}
                    >
                      <XAxis type="number" hide />
                      <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11, fill: "var(--finsight-muted)" }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: "var(--finsight-surface2)", border: "1px solid var(--finsight-border)", borderRadius: "10px" }}
                        formatter={(v) => [`₹${formatINR(v)}`, "Spent"]}
                        labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName}
                      />
                      <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={32} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="finsight-card finsight-chart-card">
              <div className="finsight-card-title">Spend Distribution</div>
              {pieData.length > 0 ? (
                <div className="finsight-donut-wrap">
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="45%"
                        innerRadius={52}
                        outerRadius={76}
                        paddingAngle={3}
                        dataKey="value"
                        nameKey="name"
                        stroke="var(--finsight-surface)"
                        strokeWidth={2}
                      >
                        {pieData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: "var(--finsight-surface2)", border: "1px solid var(--finsight-border)", borderRadius: "10px" }}
                        formatter={(v) => [`₹${formatINR(v)}`, "Spent"]}
                      />
                      <Legend
                        layout="vertical"
                        align="right"
                        verticalAlign="middle"
                        formatter={(value, entry) => (
                          <span style={{ color: "var(--finsight-text)", fontSize: "11px" }}>
                            {value} — ₹{formatINR(entry.payload?.value ?? 0)}
                          </span>
                        )}
                        iconType="circle"
                        iconSize={8}
                        wrapperStyle={{ paddingLeft: "16px" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="finsight-donut-total">
                    <span className="finsight-donut-total-label">Total spend</span>
                    <span className="finsight-donut-total-value">₹{formatINR(catTotal)}</span>
                  </div>
                </div>
              ) : (
                <p className="finsight-chart-empty">No data</p>
              )}

              {/* Exclude from analysis — compact */}
              {latestMonth && (
                <div style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--finsight-border)" }}>
                  <div className="finsight-card-title" style={{ marginBottom: "12px" }}>Exclude from analysis</div>
                  <p style={{ fontSize: "11px", color: "var(--finsight-muted)", marginBottom: "10px" }}>
                    Miscategorized? Move a transaction to Uncategorized so it’s not included in charts or totals.
                  </p>
                  {transactionsList === null && !loadingTransactions && (
                    <button type="button" onClick={loadTransactionsList} className="finsight-btn finsight-btn-primary" style={{ fontSize: "11px" }}>
                      Show transactions for {latestMonth}
                    </button>
                  )}
                  {loadingTransactions && <p style={{ fontSize: "11px", color: "var(--finsight-muted)" }}>Loading…</p>}
                  {transactionsList && transactionsList.length > 0 && (
                    <div style={{ maxHeight: 200, overflow: "auto", marginTop: "8px" }}>
                      {transactionsList.slice(0, 5).map((t) => (
                        <div key={t.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", fontSize: "11px", borderBottom: "1px solid var(--finsight-border)" }}>
                          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 180 }}>{t.description || t.merchant_name || "—"}</span>
                          <span style={{ marginLeft: "8px" }}>₹{formatINR(t.amount)}</span>
                          {t.category !== "Uncategorized" ? (
                            <button type="button" onClick={() => handleExcludeFromAnalysis(t.id)} disabled={excludingId === t.id} className="finsight-btn" style={{ padding: "2px 8px", fontSize: "10px", marginLeft: "8px" }}>
                              {excludingId === t.id ? "…" : "Exclude"}
                            </button>
                          ) : (
                            <span style={{ color: "var(--finsight-muted)", fontSize: "10px" }}>Excluded</span>
                          )}
                        </div>
                      ))}
                      {transactionsList.length > 5 && (
                        <button type="button" onClick={loadTransactionsList} className="finsight-btn" style={{ width: "100%", marginTop: "8px", fontSize: "11px" }}>
                          Show all ({transactionsList.length})
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Second row: Timeline + Merchants */}
          <div className="finsight-main-grid">
            {monthlySeries.length > 0 && (
              <div className="finsight-card finsight-chart-card">
                <div className="finsight-card-title">Monthly Spend Trend</div>
                <div className="finsight-line-chart-wrap">
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={monthlySeries} margin={{ top: 12, right: 12, left: 0, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--finsight-border)" vertical={false} opacity={0.6} />
                      <XAxis dataKey="period" stroke="var(--finsight-muted)" fontSize={11} tickLine={false} />
                      <YAxis stroke="var(--finsight-muted)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${v >= 1000 ? (v / 1000) + "k" : v}`} width={44} />
                      <Tooltip
                        contentStyle={{ background: "var(--finsight-surface2)", border: "1px solid var(--finsight-border)", borderRadius: "10px" }}
                        formatter={(v) => [`₹${formatINR(v)}`, "Spend"]}
                        labelStyle={{ color: "var(--finsight-muted)" }}
                      />
                      <Line type="monotone" dataKey="total" stroke="var(--finsight-accent)" strokeWidth={2.5} dot={{ fill: "var(--finsight-accent)", r: 4, strokeWidth: 0 }} activeDot={{ r: 6, fill: "var(--finsight-accent)", stroke: "var(--finsight-surface)" }} name="Spend" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            <div className="finsight-card">
              <div className="finsight-card-title">Top Merchants</div>
              {data.top_merchants && data.top_merchants.length > 0 ? (
                <div className="finsight-merchant-list">
                  {data.top_merchants.slice(0, 5).map((m, idx) => (
                    <div key={m.merchant} className="finsight-merchant-row">
                      <div className="finsight-merchant-rank">#{idx + 1}</div>
                      <div className="finsight-merchant-name">{m.merchant}</div>
                      <div className="finsight-merchant-count">{m.count} txns</div>
                      <div className="finsight-merchant-amount">₹{formatINR(m.total_spend)}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>No merchant data.</p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="finsight-card" style={{ marginTop: "20px" }}>
            <div className="finsight-card-title">Quick Actions</div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <Link to="/categorize" className="finsight-btn">🏷️ Categorize</Link>
              <Link to="/assistant" className="finsight-btn">🤖 AI Assistant</Link>
            </div>
          </div>
        </>
      )}

      {loading && !data && (
        <div className="finsight-card" style={{ textAlign: "center", padding: "48px" }}>
          <p style={{ color: "var(--finsight-muted)" }}>Loading your data…</p>
        </div>
      )}
    </>
  );
}
