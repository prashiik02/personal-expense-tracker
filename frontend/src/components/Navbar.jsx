import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import React from "react";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="finsight-header" style={{ padding: "16px 24px", borderBottom: "1px solid var(--finsight-border)", background: "var(--finsight-surface)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
        <Link to="/" className="finsight-logo" style={{ textDecoration: "none", color: "var(--finsight-text)" }}>
          Fin<span>Sight</span>
        </Link>
        {user && (
          <nav style={{ display: "flex", gap: "4px" }}>
            <NavLink to="/" end className={({ isActive }) => "finsight-nav-link" + (isActive ? " active" : "")}>
              Dashboard
            </NavLink>
            <NavLink to="/categorize" className={({ isActive }) => "finsight-nav-link" + (isActive ? " active" : "")}>
              Categorize
            </NavLink>
            <NavLink to="/assistant" className={({ isActive }) => "finsight-nav-link" + (isActive ? " active" : "")}>
              AI Assistant
            </NavLink>
          </nav>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        {user && (
          <span style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>
            {user.email}
          </span>
        )}
        <ThemeToggle />
        <button
          type="button"
          onClick={logout}
          className="finsight-btn"
          style={{ padding: "6px 14px", fontSize: "11px" }}
        >
          Logout
        </button>
      </div>
    </header>
  );
}
