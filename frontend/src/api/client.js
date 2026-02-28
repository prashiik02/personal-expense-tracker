import axios from "axios";

// Use 127.0.0.1 by default to avoid Windows resolving localhost to IPv6 (::1)
const baseURL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const API = axios.create({ baseURL });

API.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem("user");
    if (!stored) return config;
    const user = JSON.parse(stored);
    const token = user?.token;
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    // ignore malformed storage
  }
  return config;
});
export { API };
export default API;
