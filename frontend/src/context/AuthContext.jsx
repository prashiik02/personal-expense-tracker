import React from "react";
import { createContext, useState, useEffect } from "react";
import axios from "axios";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) setUser(JSON.parse(stored));
  }, []);

  const login = async (email, password) => {
    const res = await axios.post("http://localhost:5000/auth/login", {
      email,
      password,
    });
    setUser(res.data);
    localStorage.setItem("user", JSON.stringify(res.data));
  };

  const register = async (data) => {
    await axios.post("http://localhost:5000/auth/register", data);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};