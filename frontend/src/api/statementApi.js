import { API } from "./client";

export const analyzeStatementPdf = async ({ file, bank = "generic", maxPages = 20 }) => {
  const form = new FormData();
  form.append("file", file);
  form.append("bank", bank);
  form.append("max_pages", String(maxPages));
  form.append("return_results", "true");

  const res = await API.post("/statements/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const fetchDashboardOverview = async () => {
  const res = await API.get("/statements/dashboard");
  return res.data;
};

export const fetchTransactions = async ({ category, subcategory, month, limit = 100 } = {}) => {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (subcategory) params.set("subcategory", subcategory);
  if (month) params.set("month", month);
  if (limit) params.set("limit", String(limit));
  const res = await API.get(`/statements/transactions?${params.toString()}`);
  return res.data;
};

export const excludeTransactionFromAnalysis = async (txnId) => {
  const res = await API.patch(`/statements/transactions/${txnId}`, {
    exclude_from_analytics: true,
  });
  return res.data;
};

