import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import React from "react";

const COLORS = {
  primary: "#3498db",
  dark: "#2c3e50",
  light: "#fafafa",
  white: "#ffffff",
  gray: "#7f8c8d",
  lightGray: "#ecf0f1",
  border: "#e0e6ed",
};

export default function Navbar() {
  const { user, logout } = useAuth();

  const navLinkStyle = {
    fontSize: 14,
    color: COLORS.dark,
    textDecoration: "none",
    fontWeight: 500,
    padding: "8px 12px",
    borderRadius: 4,
    transition: "all 0.2s",
    cursor: "pointer",
  };

  return (
    <nav
      style={{
        padding: "0 24px",
        borderBottom: `1px solid ${COLORS.border}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        height: 64,
        backgroundColor: COLORS.white,
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.08)",
      }}
    >
      <Link
        to="/"
        style={{
          fontSize: 18,
          fontWeight: 700,
          color: COLORS.primary,
          textDecoration: "none",
          letterSpacing: -0.5,
        }}
      >
        💰 Expense Tracker
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        {user && (
          <div style={{ display: "flex", gap: 8 }}>
            <Link to="/" style={navLinkStyle} onMouseEnter={(e) => (e.target.style.backgroundColor = COLORS.light)} onMouseLeave={(e) => (e.target.style.backgroundColor = "transparent")}>
              Dashboard
            </Link>
            <Link to="/categorize" style={navLinkStyle} onMouseEnter={(e) => (e.target.style.backgroundColor = COLORS.light)} onMouseLeave={(e) => (e.target.style.backgroundColor = "transparent")}>
              Categorize
            </Link>
            <Link to="/assistant" style={navLinkStyle} onMouseEnter={(e) => (e.target.style.backgroundColor = COLORS.light)} onMouseLeave={(e) => (e.target.style.backgroundColor = "transparent")}>
              AI Assistant
            </Link>
          </div>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: 12, borderLeft: `1px solid ${COLORS.border}`, paddingLeft: 24 }}>
          {user && (
            <span style={{ fontSize: 13, color: COLORS.gray, fontWeight: 500 }}>
              {user.email}
            </span>
          )}
          <button
            onClick={logout}
            style={{
              padding: "8px 16px",
              fontSize: 13,
              fontWeight: 600,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 4,
              backgroundColor: COLORS.white,
              color: COLORS.dark,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.target.backgroundColor = COLORS.light;
              e.target.borderColor = COLORS.primary;
              e.target.color = COLORS.primary;
            }}
            onMouseLeave={(e) => {
              e.target.backgroundColor = COLORS.white;
              e.target.borderColor = COLORS.border;
              e.target.color = COLORS.dark;
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}