import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import React from "react";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav style={{ padding: "12px 16px", borderBottom: "1px solid #ddd", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ fontWeight: 600 }}>Personal Expense Tracker</div>
        <Link to="/categorize" style={{ fontSize: 14 }}>Categorize</Link>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {user && <span style={{ fontSize: 14 }}>{user.email}</span>}
        <button onClick={logout}>Logout</button>
      </div>
    </nav>
  );
}