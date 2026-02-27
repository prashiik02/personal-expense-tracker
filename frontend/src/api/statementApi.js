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

