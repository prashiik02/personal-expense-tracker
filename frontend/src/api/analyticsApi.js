import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:5000",
});

// Monthly Summary
export const getMonthlySummary = async () => {
  const response = await API.get("/analytics/monthly");
  return response.data;
};

// Insights
export const getInsights = async () => {
  const response = await API.get("/insights");
  return response.data;
};