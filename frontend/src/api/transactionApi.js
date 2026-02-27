import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:5000",
});

// Get All Transactions
export const getTransactions = async () => {
  const response = await API.get("/transactions");
  return response.data;
};

// Delete Transaction (optional)
export const deleteTransaction = async (id) => {
  const response = await API.delete(`/transactions/${id}`);
  return response.data;
};