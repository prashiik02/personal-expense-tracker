import { API, LLM_TIMEOUT_MS } from "./client";

export const categorizeSingle = async (payload) => {
  const res = await API.post("/categorize", payload, { timeout: LLM_TIMEOUT_MS });
  return res.data;
};

export const categorizeBatch = async (payload) => {
  const res = await API.post("/categorize/batch", payload, { timeout: LLM_TIMEOUT_MS });
  return res.data;
};

export const categorizeSms = async (payload) => {
  const res = await API.post("/categorize/sms", payload, { timeout: LLM_TIMEOUT_MS });
  return res.data;
};

export const recordCorrection = async (payload) => {
  const res = await API.post("/categorize/correction", payload);
  return res.data;
};

