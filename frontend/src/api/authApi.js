import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:5000",
});

// Register
export const registerUser = async (data) => {
  const response = await API.post("/auth/register", data);
  return response.data;
};

// Login
export const loginUser = async (data) => {
  const response = await API.post("/auth/login", data);
  return response.data;
};