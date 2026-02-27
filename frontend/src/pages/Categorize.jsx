import React, { useMemo, useState, useRef } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  categorizeBatch,
  categorizeSingle,
  categorizeSms,
  recordCorrection,
} from "../api/categorizationApi";
import { analyzeStatementPdf } from "../api/statementApi";

const TABS = [
  { id: "raw", label: "Raw transaction" },
  { id: "sms", label: "Bank SMS" },
  { id: "batch", label: "Batch (CSV)" },
  { id: "items", label: "Line items (split)" },
  { id: "pdf", label: "PDF statement" },
];

function safeJsonParse(text) {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (e) {
    return { ok: false, error: "Invalid JSON" };
  }
}

function downloadText(filename, text, mime = "application/json") {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function formatINR(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "-";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function buildCategoryChartData(summary) {
  const categories = summary?.categories || {};
  const totalsByCategory = {};
  Object.entries(categories).forEach(([key, v]) => {
    const cat = key.split(" > ")[0] || key;
    totalsByCategory[cat] = (totalsByCategory[cat] || 0) + (v?.total || 0);
  });
  return Object.entries(totalsByCategory)
    .map(([name, total]) => ({ name, total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 12);
}

function computeSpendSummary(results) {
  let spend = 0;
  let income = 0;
  let needsReview = 0;
  let split = 0;
  results.forEach((r) => {
    const amt = Number(r?.amount || 0);
    if (amt > 0) spend += Math.abs(amt);
    if (amt < 0) income += Math.abs(amt);
    if (r?.needs_review) needsReview += 1;
    if (r?.is_split) split += 1;
  });
  return {
    count: results.length,
    total_spend: spend,
    total_income: income,
    net: income - spend,
    needs_review_count: needsReview,
    split_transactions: split,
  };
}

function groupSpendByMonth(results) {
  const map = {};
  results.forEach((r) => {
    const d = String(r?.date || "");
    if (d.length < 7) return;
    const month = d.slice(0, 7);
    const amt = Number(r?.amount || 0);
    const spend = amt > 0 ? Math.abs(amt) : 0;
    map[month] = (map[month] || 0) + spend;
  });
  return Object.entries(map)
    .map(([month, total]) => ({ month, total }))
    .sort((a, b) => a.month.localeCompare(b.month));
}

function groupSpendByCategory(results) {
  const map = {};
  results.forEach((r) => {
    const cat = r?.category || "Unknown";
    const amt = Number(r?.amount || 0);
    const spend = amt > 0 ? Math.abs(amt) : 0;
    map[cat] = (map[cat] || 0) + spend;
  });
  return Object.entries(map)
    .map(([name, total]) => ({ name, total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 12);
}

function toCsv(rows) {
  const headers = [
    "transaction_id",
    "date",
    "description",
    "amount",
    "category",
    "subcategory",
    "merchant_name",
    "charge_type",
    "categorization_method",
    "categorization_confidence",
    "needs_review",
    "is_split",
    "tags",
  ];
  const esc = (v) => {
    const s = String(v ?? "");
    if (/[\",\n]/.test(s)) return `"${s.replace(/\"/g, '""')}"`;
    return s;
  };
  const lines = [headers.join(",")];
  rows.forEach((r) => {
    const row = [
      r?.transaction_id,
      r?.date,
      r?.description,
      r?.amount,
      r?.category,
      r?.subcategory,
      r?.merchant_name,
      r?.charge_type,
      r?.categorization_method,
      r?.categorization_confidence,
      r?.needs_review,
      r?.is_split,
      (r?.tags || []).join("|"),
    ];
    lines.push(row.map(esc).join(","));
  });
  return lines.join("\n");
}

export default function Categorize() {
  const [tab, setTab] = useState("raw");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [batchMode, setBatchMode] = useState("file"); // file | text
  const [csvFileName, setCsvFileName] = useState("");
  const [pdfFileName, setPdfFileName] = useState("");
  const [pdfBank, setPdfBank] = useState("generic");
  const [pdfMaxPages, setPdfMaxPages] = useState(20);
  const [pdfResponse, setPdfResponse] = useState(null);
  const [pdfAnalyzing, setPdfAnalyzing] = useState(false);
  const [pdfProgress, setPdfProgress] = useState(0);
  const pdfTimerRef = useRef(null);

  const [filters, setFilters] = useState({
    search: "",
    dateFrom: "",
    dateTo: "",
    category: "",
    merchant: "",
    minAmount: "",
    maxAmount: "",
    needsReviewOnly: false,
    splitOnly: false,
    subscriptionOnly: false,
  });

  const [correctionOpen, setCorrectionOpen] = useState(false);
  const [correction, setCorrection] = useState({
    transaction_id: "",
    description: "",
    merchant_name: "",
    old_category: "",
    new_category: "",
    new_subcategory: "",
  });

  const [rawForm, setRawForm] = useState({
    transaction_id: "T001",
    date: "2024-01-15",
    description: "ZOMATO ORDER #789456",
    amount: 450,
  });

  const [smsForm, setSmsForm] = useState({
    bank: "hdfc",
    sms_text:
      "HDFC Bank: Rs.450.00 debited from A/c XX1234 on 15-Jan-24 to VPA ZOMATO@ICICI Ref No 456789. Avl Bal:Rs.12,340.50",
  });

  const [csvText, setCsvText] = useState(
    "transaction_id,date,description,amount\nA1,2024-01-15,BUNDL TECHNOLOGIES UPI,320\nA2,2024-01-16,NETFLIX SUBSCRIPTION JAN,649"
  );

  const [itemsForm, setItemsForm] = useState({
    transaction_id: "T100",
    date: "2024-01-16",
    description: "AMAZON PAY PURCHASE - EARPHONES T-SHIRT PROTEIN POWDER",
    amount: 4599,
    line_items_json:
      '[{"name":"JBL Wireless Earphones","amount":2999},{"name":"Cotton T-Shirt","amount":899},{"name":"Protein Powder","amount":701}]',
  });

  const canSubmit = useMemo(() => !isLoading, [isLoading]);

  const handleCsvFile = async (file) => {
    if (!file) return;
    setCsvFileName(file.name);
    const text = await file.text();
    setCsvText(text);
  };

  const handlePdfFile = (file) => {
    if (!file) return;
    setPdfFileName(file.name);
  };

  const startPdfProgress = () => {
    setPdfAnalyzing(true);
    setPdfProgress(5);
    if (pdfTimerRef.current) {
      clearInterval(pdfTimerRef.current);
    }
    pdfTimerRef.current = setInterval(() => {
      setPdfProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + 5;
      });
    }, 400);
  };

  const stopPdfProgress = () => {
    if (pdfTimerRef.current) {
      clearInterval(pdfTimerRef.current);
      pdfTimerRef.current = null;
    }
    setPdfProgress(100);
    setTimeout(() => {
      setPdfAnalyzing(false);
      setPdfProgress(0);
    }, 600);
  };

  const openCorrection = (processedTxn) => {
    setCorrectionOpen(true);
    setCorrection({
      transaction_id: processedTxn?.transaction_id || "",
      description: processedTxn?.description || "",
      merchant_name: processedTxn?.merchant_name || "",
      old_category: processedTxn?.category || "",
      new_category: processedTxn?.category || "",
      new_subcategory: processedTxn?.subcategory || "",
    });
  };

  const submitCorrection = async () => {
    setError("");
    setIsLoading(true);
    try {
      await recordCorrection(correction);
      setCorrectionOpen(false);
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.msg ||
        err?.message ||
        "Correction failed";
      setError(typeof msg === "string" ? msg : "Correction failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    setError("");
    setResult(null);
    setPdfResponse(null);
    setIsLoading(true);
    try {
      if (tab === "raw") {
        const data = await categorizeSingle(rawForm);
        setResult(data);
        return;
      }

      if (tab === "sms") {
        const data = await categorizeSms(smsForm);
        setResult(data);
        return;
      }

      if (tab === "batch") {
        const data = await categorizeBatch({
          csv_text: csvText,
          include_summary: true,
          return_results: true,
        });
        setResult(data);
        return;
      }

      if (tab === "items") {
        const parsed = safeJsonParse(itemsForm.line_items_json);
        if (!parsed.ok) {
          setError(parsed.error);
          return;
        }
        const payload = {
          transaction_id: itemsForm.transaction_id,
          date: itemsForm.date,
          description: itemsForm.description,
          amount: Number(itemsForm.amount),
          line_items: parsed.value,
        };
        const data = await categorizeSingle(payload);
        setResult(data);
        return;
      }

      if (tab === "pdf") {
        const input = document.getElementById("pdf-file-input");
        const file = input?.files?.[0];
        if (!file) {
          setError("Please select a PDF file.");
          return;
        }
        startPdfProgress();
        const data = await analyzeStatementPdf({
          file,
          bank: pdfBank,
          maxPages: pdfMaxPages,
        });
        setPdfResponse(data);
        return;
      }
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.msg ||
        err?.message ||
        "Request failed";
      setError(typeof msg === "string" ? msg : "Request failed");
    } finally {
      if (tab === "pdf") {
        stopPdfProgress();
      }
      setIsLoading(false);
    }
  };

  const processedSingle =
    tab === "sms" ? result?.result : tab === "batch" ? null : result;
  const batchResults = tab === "batch" ? result?.results || [] : [];
  const batchSummary = tab === "batch" ? result?.summary : null;

  const activeResults = useMemo(() => {
    if (tab === "batch") return batchResults;
    if (tab === "pdf") return pdfResponse?.results || [];
    return [];
  }, [tab, batchResults, pdfResponse]);

  const filteredResults = useMemo(() => {
    const s = filters.search.trim().toLowerCase();
    const df = filters.dateFrom;
    const dt = filters.dateTo;
    const cat = filters.category;
    const merch = filters.merchant.trim().toLowerCase();
    const minA = filters.minAmount === "" ? null : Number(filters.minAmount);
    const maxA = filters.maxAmount === "" ? null : Number(filters.maxAmount);
    return activeResults.filter((r) => {
      const date = String(r?.date || "");
      const amount = Math.abs(Number(r?.amount || 0));

      if (df && date && date < df) return false;
      if (dt && date && date > dt) return false;
      if (cat && r?.category !== cat) return false;
      if (merch && !String(r?.merchant_name || "").toLowerCase().includes(merch)) return false;
      if (minA !== null && amount < minA) return false;
      if (maxA !== null && amount > maxA) return false;
      if (filters.needsReviewOnly && !r?.needs_review) return false;
      if (filters.splitOnly && !r?.is_split) return false;
      if (filters.subscriptionOnly && String(r?.charge_type || "") !== "subscription") return false;

      if (s) {
        const hay = `${r?.description || ""} ${r?.merchant_name || ""} ${r?.category || ""} ${r?.subcategory || ""}`.toLowerCase();
        if (!hay.includes(s)) return false;
      }
      return true;
    });
  }, [activeResults, filters]);

  const filteredSummary = useMemo(() => computeSpendSummary(filteredResults), [filteredResults]);
  const categoryChartData = useMemo(() => groupSpendByCategory(filteredResults), [filteredResults]);
  const monthTrendData = useMemo(() => groupSpendByMonth(filteredResults), [filteredResults]);

  const filterOptions = useMemo(() => {
    const cats = new Set();
    const merchants = new Set();
    activeResults.forEach((r) => {
      if (r?.category) cats.add(r.category);
      if (r?.merchant_name) merchants.add(r.merchant_name);
    });
    return {
      categories: Array.from(cats).sort(),
      merchants: Array.from(merchants).sort(),
    };
  }, [activeResults]);

  return (
    <div style={{ padding: 24, maxWidth: 960, margin: "0 auto" }}>
      <h2 style={{ marginBottom: 8 }}>Categorize transactions</h2>
      <p style={{ marginTop: 0, color: "#555" }}>
        Test raw descriptions, bank SMS, CSV batches, and split line items.
      </p>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              border: "1px solid #ccc",
              padding: "8px 10px",
              background: tab === t.id ? "#eee" : "white",
              cursor: "pointer",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
        {tab === "raw" && (
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              Transaction ID
              <input
                value={rawForm.transaction_id}
                onChange={(e) => setRawForm({ ...rawForm, transaction_id: e.target.value })}
              />
            </label>
            <label>
              Date (YYYY-MM-DD)
              <input value={rawForm.date} onChange={(e) => setRawForm({ ...rawForm, date: e.target.value })} />
            </label>
            <label>
              Description
              <input
                value={rawForm.description}
                onChange={(e) => setRawForm({ ...rawForm, description: e.target.value })}
              />
            </label>
            <label>
              Amount
              <input
                type="number"
                value={rawForm.amount}
                onChange={(e) => setRawForm({ ...rawForm, amount: Number(e.target.value) })}
              />
            </label>
          </div>
        )}

        {tab === "sms" && (
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              Bank
              <select
                value={smsForm.bank}
                onChange={(e) => setSmsForm({ ...smsForm, bank: e.target.value })}
              >
                <option value="hdfc">HDFC</option>
                <option value="sbi">SBI</option>
              </select>
            </label>
            <label>
              SMS text
              <textarea
                rows={5}
                value={smsForm.sms_text}
                onChange={(e) => setSmsForm({ ...smsForm, sms_text: e.target.value })}
              />
            </label>
          </div>
        )}

        {tab === "batch" && (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button
                onClick={() => setBatchMode("file")}
                style={{
                  border: "1px solid #ccc",
                  padding: "6px 10px",
                  background: batchMode === "file" ? "#eee" : "white",
                }}
                type="button"
              >
                Upload CSV
              </button>
              <button
                onClick={() => setBatchMode("text")}
                style={{
                  border: "1px solid #ccc",
                  padding: "6px 10px",
                  background: batchMode === "text" ? "#eee" : "white",
                }}
                type="button"
              >
                Paste CSV text
              </button>
            </div>

            {batchMode === "file" && (
              <div style={{ display: "grid", gap: 8 }}>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(e) => handleCsvFile(e.target.files?.[0])}
                />
                {csvFileName && (
                  <div style={{ color: "#555", fontSize: 13 }}>
                    Selected: <strong>{csvFileName}</strong>
                  </div>
                )}
              </div>
            )}

            {batchMode === "text" && (
              <label>
                CSV text
                <textarea
                  rows={8}
                  value={csvText}
                  onChange={(e) => setCsvText(e.target.value)}
                />
              </label>
            )}

            <div style={{ color: "#555", fontSize: 13 }}>
              Required headers: <code>transaction_id,date,description,amount</code>
            </div>
            <details>
              <summary style={{ cursor: "pointer" }}>Preview (first 15 lines)</summary>
              <pre style={{ background: "#f7f7f7", padding: 12, overflowX: "auto" }}>
                {String(csvText || "")
                  .split(/\r?\n/)
                  .slice(0, 15)
                  .join("\n")}
              </pre>
            </details>
          </div>
        )}

        {tab === "items" && (
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              Transaction ID
              <input
                value={itemsForm.transaction_id}
                onChange={(e) => setItemsForm({ ...itemsForm, transaction_id: e.target.value })}
              />
            </label>
            <label>
              Date (YYYY-MM-DD)
              <input value={itemsForm.date} onChange={(e) => setItemsForm({ ...itemsForm, date: e.target.value })} />
            </label>
            <label>
              Description
              <input
                value={itemsForm.description}
                onChange={(e) => setItemsForm({ ...itemsForm, description: e.target.value })}
              />
            </label>
            <label>
              Amount
              <input
                type="number"
                value={itemsForm.amount}
                onChange={(e) => setItemsForm({ ...itemsForm, amount: Number(e.target.value) })}
              />
            </label>
            <label>
              Line items JSON (array of {"name","amount"})
              <textarea
                rows={6}
                value={itemsForm.line_items_json}
                onChange={(e) => setItemsForm({ ...itemsForm, line_items_json: e.target.value })}
              />
            </label>
          </div>
        )}

        {tab === "pdf" && (
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              Bank format (optional hint)
              <select value={pdfBank} onChange={(e) => setPdfBank(e.target.value)}>
                <option value="generic">Auto-detect</option>
                <option value="hdfc">HDFC</option>
                <option value="sbi">SBI</option>
                <option value="icici">ICICI</option>
                <option value="axis">Axis</option>
              </select>
            </label>
            <label>
              Max pages to scan
              <input
                type="number"
                min={1}
                max={100}
                value={pdfMaxPages}
                onChange={(e) => setPdfMaxPages(Number(e.target.value) || 1)}
              />
            </label>
            <label>
              PDF statement
              <input id="pdf-file-input" type="file" accept="application/pdf" />
            </label>
            {pdfFileName && (
              <div style={{ color: "#555", fontSize: 13 }}>
                Selected: <strong>{pdfFileName}</strong>
              </div>
            )}
            {pdfAnalyzing && (
              <div style={{ marginTop: 8 }}>
                <div style={{ fontSize: 13, color: "#555", marginBottom: 4 }}>
                  Analyzing statement… this can take a few seconds for large PDFs.
                </div>
                <div
                  style={{
                    height: 8,
                    borderRadius: 4,
                    background: "#e5e7eb",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${Math.min(100, pdfProgress)}%`,
                      background: "#6366F1",
                      transition: "width 0.3s ease-out",
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "pdf" && (
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              Bank (parsing hint)
              <select value={pdfBank} onChange={(e) => setPdfBank(e.target.value)}>
                <option value="generic">Generic</option>
                <option value="hdfc">HDFC</option>
                <option value="sbi">SBI</option>
                <option value="icici">ICICI</option>
                <option value="axis">Axis</option>
              </select>
            </label>
            <label>
              Max pages to read (faster for large PDFs)
              <input
                type="number"
                min={1}
                max={200}
                value={pdfMaxPages}
                onChange={(e) => setPdfMaxPages(Number(e.target.value))}
              />
            </label>
            <input
              id="pdf-file-input"
              type="file"
              accept=".pdf,application/pdf"
              onChange={(e) => handlePdfFile(e.target.files?.[0])}
            />
            {pdfFileName && (
              <div style={{ color: "#555", fontSize: 13 }}>
                Selected: <strong>{pdfFileName}</strong>
              </div>
            )}
            <div style={{ color: "#555", fontSize: 13 }}>
              Note: scanned/image PDFs may need OCR (not added yet).
            </div>
          </div>
        )}

        {error && <div style={{ color: "crimson" }}>{error}</div>}

        <div>
          <button onClick={handleSubmit} disabled={!canSubmit}>
            {isLoading ? "Processing..." : "Run categorization"}
          </button>
          {(result || pdfResponse) && (
            <button
              type="button"
              style={{ marginLeft: 8 }}
              onClick={() =>
                downloadText(
                  `categorization_${tab}_${Date.now()}.json`,
                  JSON.stringify(tab === "pdf" ? pdfResponse : result, null, 2)
                )
              }
            >
              Download JSON
            </button>
          )}
          {(tab === "batch" || tab === "pdf") && filteredResults.length > 0 && (
            <button
              type="button"
              style={{ marginLeft: 8 }}
              onClick={() =>
                downloadText(
                  `filtered_${tab}_${Date.now()}.csv`,
                  toCsv(filteredResults),
                  "text/csv"
                )
              }
            >
              Download CSV (filtered)
            </button>
          )}
        </div>

        {processedSingle && (
          <div style={{ marginTop: 12, border: "1px solid #eee", padding: 12 }}>
            <h3 style={{ marginTop: 0, marginBottom: 10 }}>Result (single)</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <div style={{ color: "#666", fontSize: 12 }}>Category</div>
                <div style={{ fontWeight: 600 }}>
                  {processedSingle.category} &gt; {processedSingle.subcategory}
                </div>
              </div>
              <div>
                <div style={{ color: "#666", fontSize: 12 }}>Confidence</div>
                <div style={{ fontWeight: 600 }}>
                  {Math.round((processedSingle.categorization_confidence || 0) * 100)}%
                  {" · "}
                  {processedSingle.categorization_method}
                </div>
              </div>
              <div>
                <div style={{ color: "#666", fontSize: 12 }}>Merchant</div>
                <div>{processedSingle.merchant_name || "-"}</div>
              </div>
              <div>
                <div style={{ color: "#666", fontSize: 12 }}>Amount</div>
                <div>₹{formatINR(Math.abs(processedSingle.amount || 0))}</div>
              </div>
              <div style={{ gridColumn: "1 / -1" }}>
                <div style={{ color: "#666", fontSize: 12 }}>Tags</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {(processedSingle.tags || []).length ? (
                    (processedSingle.tags || []).map((t) => (
                      <span
                        key={t}
                        style={{
                          border: "1px solid #ddd",
                          padding: "2px 8px",
                          borderRadius: 999,
                          fontSize: 12,
                        }}
                      >
                        {t}
                      </span>
                    ))
                  ) : (
                    <span>-</span>
                  )}
                </div>
              </div>
              {processedSingle.is_split && (
                <div style={{ gridColumn: "1 / -1" }}>
                  <div style={{ color: "#666", fontSize: 12 }}>Split items</div>
                  <pre style={{ background: "#f7f7f7", padding: 12, overflowX: "auto" }}>
                    {JSON.stringify(processedSingle.split_items, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            <div style={{ marginTop: 10 }}>
              <button type="button" onClick={() => openCorrection(processedSingle)}>
                Submit correction (optional learning)
              </button>
            </div>
          </div>
        )}

        {(tab === "batch" || tab === "pdf") && (result || pdfResponse) && (
          <div style={{ marginTop: 12 }}>
            <h3 style={{ marginBottom: 8 }}>Analysis</h3>

            <div style={{ border: "1px solid #eee", padding: 12, marginBottom: 12 }}>
              <div style={{ fontWeight: 600, marginBottom: 10 }}>Filters</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                <label>
                  Search
                  <input
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    placeholder="zomato / uber / netflix..."
                  />
                </label>
                <label>
                  Date from
                  <input
                    type="date"
                    value={filters.dateFrom}
                    onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                  />
                </label>
                <label>
                  Date to
                  <input
                    type="date"
                    value={filters.dateTo}
                    onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                  />
                </label>
                <label>
                  Category
                  <select
                    value={filters.category}
                    onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                  >
                    <option value="">All</option>
                    {filterOptions.categories.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Merchant contains
                  <input
                    value={filters.merchant}
                    onChange={(e) => setFilters({ ...filters, merchant: e.target.value })}
                    placeholder="amazon / swiggy..."
                  />
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <label>
                    Min amount
                    <input
                      type="number"
                      value={filters.minAmount}
                      onChange={(e) => setFilters({ ...filters, minAmount: e.target.value })}
                      placeholder="0"
                    />
                  </label>
                  <label>
                    Max amount
                    <input
                      type="number"
                      value={filters.maxAmount}
                      onChange={(e) => setFilters({ ...filters, maxAmount: e.target.value })}
                      placeholder="10000"
                    />
                  </label>
                </div>
              </div>
              <div style={{ display: "flex", gap: 14, marginTop: 10, flexWrap: "wrap" }}>
                <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={filters.needsReviewOnly}
                    onChange={(e) => setFilters({ ...filters, needsReviewOnly: e.target.checked })}
                  />
                  Needs review only
                </label>
                <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={filters.splitOnly}
                    onChange={(e) => setFilters({ ...filters, splitOnly: e.target.checked })}
                  />
                  Split only
                </label>
                <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={filters.subscriptionOnly}
                    onChange={(e) =>
                      setFilters({ ...filters, subscriptionOnly: e.target.checked })
                    }
                  />
                  Subscription only
                </label>
                <button
                  type="button"
                  onClick={() =>
                    setFilters({
                      search: "",
                      dateFrom: "",
                      dateTo: "",
                      category: "",
                      merchant: "",
                      minAmount: "",
                      maxAmount: "",
                      needsReviewOnly: false,
                      splitOnly: false,
                      subscriptionOnly: false,
                    })
                  }
                >
                  Reset filters
                </button>
              </div>
              <div style={{ marginTop: 8, color: "#555", fontSize: 13 }}>
                Showing <strong>{filteredSummary.count}</strong> transactions after filters.
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
              <div style={{ border: "1px solid #eee", padding: 12 }}>
                <div style={{ color: "#666", fontSize: 12 }}>Transactions</div>
                <div style={{ fontWeight: 700, fontSize: 18 }}>{filteredSummary.count}</div>
              </div>
              <div style={{ border: "1px solid #eee", padding: 12 }}>
                <div style={{ color: "#666", fontSize: 12 }}>Total spend</div>
                <div style={{ fontWeight: 700, fontSize: 18 }}>
                  ₹{formatINR(filteredSummary.total_spend)}
                </div>
              </div>
              <div style={{ border: "1px solid #eee", padding: 12 }}>
                <div style={{ color: "#666", fontSize: 12 }}>Needs review</div>
                <div style={{ fontWeight: 700, fontSize: 18 }}>
                  {filteredSummary.needs_review_count}
                </div>
              </div>
              <div style={{ border: "1px solid #eee", padding: 12 }}>
                <div style={{ color: "#666", fontSize: 12 }}>Split txns</div>
                <div style={{ fontWeight: 700, fontSize: 18 }}>
                  {filteredSummary.split_transactions}
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 14 }}>
              <div style={{ height: 320, border: "1px solid #eee", padding: 12 }}>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>Top categories by spend</div>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={categoryChartData}
                    margin={{ top: 8, right: 8, bottom: 24, left: 8 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis />
                    <Tooltip formatter={(v) => `₹${formatINR(Number(v))}`} />
                    <Bar dataKey="total" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ height: 320, border: "1px solid #eee", padding: 12 }}>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>Monthly spend trend</div>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthTrendData} margin={{ top: 8, right: 8, bottom: 24, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis />
                    <Tooltip formatter={(v) => `₹${formatINR(Number(v))}`} />
                    <Legend />
                    <Line type="monotone" dataKey="total" name="Spend" stroke="#82ca9d" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <details style={{ marginTop: 12 }}>
              <summary style={{ cursor: "pointer" }}>Transactions table</summary>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
                  <thead>
                    <tr>
                      {["Date", "Description", "Amount", "Category", "Merchant", "Flags"].map((h) => (
                        <th
                          key={h}
                          style={{
                            textAlign: "left",
                            borderBottom: "1px solid #ddd",
                            padding: "8px 6px",
                            fontSize: 13,
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredResults.slice(0, 200).map((r) => (
                      <tr key={`${r.transaction_id}-${r.date}-${r.amount}`}>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
                          {r.date}
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
                          {r.description}
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
                          ₹{formatINR(Math.abs(Number(r.amount || 0)))}
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
                          {r.category} &gt; {r.subcategory}
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
                          {r.merchant_name || "-"}
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
                          {r.needs_review ? "review " : ""}
                          {r.is_split ? "split " : ""}
                          {r.charge_type === "subscription" ? "sub " : ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredResults.length > 200 && (
                  <div style={{ marginTop: 8, color: "#666", fontSize: 13 }}>
                    Showing first 200 rows. Use filters to narrow down.
                  </div>
                )}
              </div>
            </details>

            <details style={{ marginTop: 12 }}>
              <summary style={{ cursor: "pointer" }}>Results (JSON)</summary>
              <pre style={{ background: "#f7f7f7", padding: 12, overflowX: "auto" }}>
                {JSON.stringify(tab === "pdf" ? pdfResponse : result, null, 2)}
              </pre>
            </details>
          </div>
        )}

        {result && (
          <div style={{ marginTop: 12 }}>
            <h3 style={{ marginBottom: 8 }}>Result</h3>
            <pre style={{ background: "#f7f7f7", padding: 12, overflowX: "auto" }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {correctionOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
          }}
        >
          <div style={{ background: "white", width: "min(720px, 100%)", padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>Submit correction</h3>
            <div style={{ display: "grid", gap: 10 }}>
              <label>
                Transaction ID
                <input
                  value={correction.transaction_id}
                  onChange={(e) => setCorrection({ ...correction, transaction_id: e.target.value })}
                />
              </label>
              <label>
                Description
                <input
                  value={correction.description}
                  onChange={(e) => setCorrection({ ...correction, description: e.target.value })}
                />
              </label>
              <label>
                Merchant (optional)
                <input
                  value={correction.merchant_name}
                  onChange={(e) => setCorrection({ ...correction, merchant_name: e.target.value })}
                />
              </label>
              <label>
                Old category
                <input value={correction.old_category} readOnly />
              </label>
              <label>
                New category
                <input
                  value={correction.new_category}
                  onChange={(e) => setCorrection({ ...correction, new_category: e.target.value })}
                />
              </label>
              <label>
                New subcategory
                <input
                  value={correction.new_subcategory}
                  onChange={(e) => setCorrection({ ...correction, new_subcategory: e.target.value })}
                />
              </label>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 14 }}>
              <button type="button" onClick={() => setCorrectionOpen(false)} disabled={isLoading}>
                Cancel
              </button>
              <button type="button" onClick={submitCorrection} disabled={isLoading}>
                {isLoading ? "Saving..." : "Save correction"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

