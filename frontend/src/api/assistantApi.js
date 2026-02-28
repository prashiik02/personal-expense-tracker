import client from "./client";

export async function askAssistant(question) {
  const res = await client.post("/assistant/query", { question });
  return res.data;
}

export async function getReport(month) {
  const res = await client.get("/assistant/report", { params: { month } });
  return res.data;
}

export async function generateBudget() {
  const res = await client.post("/assistant/budget");
  return res.data;
}

export async function uploadLoan(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await client.post("/assistant/loan/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function getTaxSuggestions() {
  const res = await client.get("/assistant/tax/suggestions");
  return res.data;
}

export async function explainAnomaly(details) {
  const res = await client.post("/assistant/anomaly/explain", details);
  return res.data;
}
