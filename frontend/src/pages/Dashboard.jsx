import React, { useEffect, useState, useMemo } from "react";
import { useAuth } from "../hooks/useAuth";
import { fetchDashboardOverview, fetchTransactions, excludeTransactionFromAnalysis } from "../api/statementApi";
import { getIncomeAdvice } from "../api/assistantApi";
import { Link } from "react-router-dom";
import RichAdviceText from "../components/RichAdviceText";
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

const CHART_COLORS = ["#166534", "#ca8a04", "#475569", "#7c3aed", "#b91c1c", "#0d9488", "#a16207", "#4f46e5"];
const PIE_COLORS = ["#166534", "#ca8a04", "#475569", "#7c3aed", "#b91c1c", "#0d9488"];

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

  /** e.g. "February 2025" — latest month that has transaction data */
  const latestMonthFormatted = useMemo(() => {
    if (!latestMonth) return null;
    try {
      const d = new Date(`${latestMonth}-01`);
      return d.toLocaleString("en-IN", { month: "long", year: "numeric" });
    } catch {
      return latestMonth;
    }
  }, [latestMonth]);

  /** Total spend in that latest calendar month only */
  const latestMonthSpend = useMemo(() => {
    if (!monthlySeries.length) return 0;
    const last = monthlySeries[monthlySeries.length - 1];
    return Number(last?.total) || 0;
  }, [monthlySeries]);

  // Aggregate categories across ALL months so charts match KPI totals (all-time)
  const categoryListWithCount = useMemo(() => {
    const months = data?.time_aggregates?.by_month || [];
    const merged = {};
    months.forEach((m) => {
      Object.entries(m?.categories || {}).forEach(([key, val]) => {
        if (!merged[key]) merged[key] = { total: 0, count: 0 };
        merged[key].total += val?.total ?? 0;
        merged[key].count += val?.count ?? 0;
      });
    });
    return Object.entries(merged)
      .map(([key, val]) => ({ key, total: val.total, count: val.count }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10);
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
  const topCategoryLabel =
    categoryListWithCount.length > 0
      ? (categoryListWithCount[0].key.split(" > ")[0] || categoryListWithCount[0].key)
      : "—";

  const memberSinceLabel = useMemo(() => {
    const first = data?.time_aggregates?.by_month?.[0]?.period;
    if (!first || first.length < 7) return null;
    try {
      const d = new Date(`${first}-01`);
      return d.toLocaleString("en-IN", { month: "long", year: "numeric" });
    } catch {
      return null;
    }
  }, [data]);

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
      <header className="finsight-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 className="finsight-header-title">Dashboard</h1>
          <p className="finsight-header-subtitle">
            {data ? (
              <>
                {data.transactions_count ?? 0} transactions · All-time spend <strong>₹{formatINR(totalSpend)}</strong>
                {latestMonthFormatted ? (
                  <> · Latest month in data: <strong>{latestMonthFormatted}</strong></>
                ) : null}
              </>
            ) : (
              "Your financial overview"
            )}
          </p>
        </div>
        <button type="button" onClick={handleRefresh} disabled={loading} className="finsight-btn">
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      {error && (
        <div className="finsight-alert-banner deficit">
          <div className="finsight-alert-text">{error}</div>
        </div>
      )}

      {data && !loading && (
        <>
          <div className="finsight-card finsight-profile-card">
            <div className="finsight-profile-avatar" aria-hidden>
              {(user?.name || user?.email || "?").charAt(0).toUpperCase()}
            </div>
            <div className="finsight-profile-meta">
              <h2>{user?.name || "Account"}</h2>
              <p>{user?.email}</p>
              {memberSinceLabel && (
                <span className="finsight-profile-badge">Member since {memberSinceLabel}</span>
              )}
            </div>
          </div>

          <div className="finsight-spend-summary" aria-label="Spending summary">
            <div className="finsight-spend-summary-card">
              <div className="finsight-spend-summary-label">Month &amp; year (latest data)</div>
              <div className="finsight-spend-summary-main">
                {latestMonthFormatted ? (
                  <>
                    <span className="finsight-spend-summary-period">{latestMonthFormatted}</span>
                    <span className="finsight-spend-summary-sub">Spend this month</span>
                    <span className="finsight-spend-summary-amount">₹{formatINR(latestMonthSpend)}</span>
                  </>
                ) : (
                  <span className="finsight-spend-summary-empty">No monthly data yet</span>
                )}
              </div>
            </div>
            <div className="finsight-spend-summary-card finsight-spend-summary-card--wide">
              <div className="finsight-spend-summary-label">All-time spending</div>
              <div className="finsight-spend-summary-main">
                <span className="finsight-spend-summary-amount finsight-spend-summary-amount--lg">₹{formatINR(totalSpend)}</span>
                <span className="finsight-spend-summary-sub">Across all recorded months</span>
              </div>
            </div>
          </div>

          {/* Alert: deficit/surplus — uses reference monthly income when set */}
          {totalSpend > 0 && (
            <div className={`finsight-alert-banner ${net < 0 ? "deficit" : "surplus"}`}>
              <div className="finsight-alert-text">
                You spent <strong>₹{formatINR(totalSpend)}</strong> all time.
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

          <div className="finsight-kpi-grid">
            <div className="finsight-kpi-card spend">
              <div className="finsight-kpi-label">Total spent</div>
              <div className="finsight-kpi-value">₹{formatINR(totalSpend)}</div>
              <div className="finsight-kpi-sub">All time</div>
            </div>
            <div className="finsight-kpi-card txn">
              <div className="finsight-kpi-label">Transactions</div>
              <div className="finsight-kpi-value">{data.transactions_count ?? 0}</div>
              <div className="finsight-kpi-sub">All time</div>
            </div>
            <div className="finsight-kpi-card">
              <div className="finsight-kpi-label">Top category</div>
              <div className="finsight-kpi-value" style={{ fontSize: "1.35rem" }}>
                {topCategoryLabel}
              </div>
              <div className="finsight-kpi-sub">By spend</div>
            </div>
          </div>

          <div className="finsight-kpi-grid finsight-kpi-grid-2" style={{ marginTop: "-8px" }}>
            <div className="finsight-kpi-card income">
              <div className="finsight-kpi-label">Monthly income</div>
              <div className="finsight-kpi-value">₹{formatINR(totalIncome)}</div>
              <div className="finsight-kpi-sub">
                {referenceIncome != null ? "From your profile" : "From transactions"}
              </div>
            </div>
            <div className={`finsight-kpi-card net ${net >= 0 ? "surplus" : "deficit"}`}>
              <div className="finsight-kpi-label">Net balance</div>
              <div className="finsight-kpi-value">{net >= 0 ? "₹" + formatINR(net) : "-₹" + formatINR(-net)}</div>
              <div className="finsight-kpi-sub">{net >= 0 ? "Surplus vs income" : "Deficit"}</div>
            </div>
          </div>

          {/* Main grid: Categories (horizontal bar chart) + Donut */}
          <div className="finsight-main-grid">
            <div className="finsight-card finsight-chart-card">
              <div className="finsight-card-title">Spending by Category</div>
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)", marginBottom: "12px", marginTop: "-8px" }}>All time · Top 10 categories</p>
              {categoryListWithCount.length === 0 ? (
                <p className="finsight-chart-empty">No spending data yet.</p>
              ) : (
                <div className="finsight-bar-chart-wrap">
                  <ResponsiveContainer width="100%" height={Math.max(220, categoryListWithCount.length * 40)}>
                    <BarChart
                      data={categoryListWithCount.map((item, i) => ({
                        name: item.key.length > 28 ? item.key.slice(0, 26) + "…" : item.key,
                        fullName: item.key,
                        value: item.total,
                        count: item.count,
                        fill: CHART_COLORS[i % CHART_COLORS.length],
                      }))}
                      layout="vertical"
                      margin={{ top: 8, right: 55, left: 4, bottom: 8 }}
                    >
                      <XAxis type="number" tickFormatter={(v) => `₹${v >= 1000 ? (v / 1000) + "k" : v}`} tick={{ fontSize: 11, fill: "var(--finsight-muted)" }} axisLine={false} tickLine={false} width={50} />
                      <YAxis type="category" dataKey="name" width={180} tick={{ fontSize: 12, fill: "var(--finsight-text)" }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: "var(--finsight-surface2)", border: "1px solid var(--finsight-border)", borderRadius: "10px" }}
                        formatter={(v) => [`₹${formatINR(v)}`, "Spent"]}
                        labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName}
                      />
                      <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={36} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="finsight-card finsight-chart-card">
              <div className="finsight-card-title">Spend Distribution</div>
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)", marginBottom: "12px", marginTop: "-8px" }}>All time</p>
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
                    <span className="finsight-donut-total-value">₹{formatINR(totalSpend)}</span>
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

          <div className="finsight-card" style={{ marginTop: "24px" }}>
            <div className="finsight-card-title">Income vs spending</div>
            <p className="finsight-income-section-hint">
              Figures below use your <strong>profile income</strong> and <strong>spend for one calendar month</strong> (not the same as &ldquo;Total spent&rdquo; all time in the KPIs above).
            </p>
            {loadingIncomeAdvice ? (
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>Loading advice…</p>
            ) : incomeAdvice?.message ? (
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>{incomeAdvice.message}</p>
            ) : incomeAdvice?.advice ? (
              <>
                <div className="finsight-stat-chips">
                  <div className="finsight-stat-chip">
                    <span className="finsight-stat-chip-label">Monthly income (reference)</span>
                    <span className="finsight-stat-chip-value">₹{formatINR(incomeAdvice.monthly_income)}</span>
                  </div>
                  <div className="finsight-stat-chip">
                    <span className="finsight-stat-chip-label">Spend in {incomeAdvice.month ?? "selected month"}</span>
                    <span className="finsight-stat-chip-value">₹{formatINR(incomeAdvice.monthly_spend)}</span>
                  </div>
                  <div className="finsight-stat-chip">
                    <span className="finsight-stat-chip-label">{incomeAdvice.surplus >= 0 ? "Surplus" : "Overspend"}</span>
                    <span
                      className="finsight-stat-chip-value"
                      style={{ color: incomeAdvice.surplus >= 0 ? "var(--finsight-success)" : "var(--finsight-danger)" }}
                    >
                      ₹{formatINR(Math.abs(incomeAdvice.surplus))}
                    </span>
                  </div>
                </div>
                <RichAdviceText text={incomeAdvice.advice} />
              </>
            ) : incomeAdvice && !incomeAdvice.advice ? (
              <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>No advice available for this period.</p>
            ) : null}
          </div>

          <div className="finsight-card" style={{ marginTop: "24px" }}>
            <div className="finsight-card-title">Quick actions</div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <Link to="/categorize" className="finsight-btn">Categorize</Link>
              <Link to="/assistant" className="finsight-btn">Assistant</Link>
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
