import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import React from "react";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  const { user, logout } = useAuth();
  const firstName = (user?.name || user?.email || "?").split(" ")[0];

  return (
    <header className="finsight-nav">
      <div className="finsight-nav-inner">
        <Link to="/" className="finsight-logo finsight-logo-serif">
          <span className="finsight-logo-mark" aria-hidden />
          FinSight
        </Link>
        {user && (
          <nav className="finsight-nav-links">
            <NavLink to="/" end className={({ isActive }) => "finsight-nav-link" + (isActive ? " active" : "")}>
              Dashboard
            </NavLink>
            <NavLink to="/categorize" className={({ isActive }) => "finsight-nav-link" + (isActive ? " active" : "")}>
              Categorize
            </NavLink>
            <NavLink to="/assistant" className={({ isActive }) => "finsight-nav-link" + (isActive ? " active" : "")}>
              Assistant
            </NavLink>
          </nav>
        )}
      </div>
      <div className="finsight-nav-right">
        {user && <span className="finsight-nav-email">{firstName}</span>}
        <ThemeToggle />
        {user && (
          <button type="button" onClick={logout} className="finsight-btn finsight-btn-black" style={{ padding: "8px 16px", fontSize: "0.875rem" }}>
            Log out
          </button>
        )}
      </div>
    </header>
  );
}
