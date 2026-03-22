import { Link } from "react-router-dom";
import React from "react";
import ThemeToggle from "./ThemeToggle";

export default function PublicNavbar() {
  return (
    <header className="finsight-nav finsight-nav-public">
      <div className="finsight-nav-inner">
        <Link to="/" className="finsight-logo finsight-logo-serif">
          <span className="finsight-logo-mark" aria-hidden />
          FinSight
        </Link>
      </div>
      <div className="finsight-nav-right">
        <Link to="/login" className="finsight-nav-text-link">
          Sign in
        </Link>
        <Link to="/register" className="finsight-btn finsight-btn-black">
          Get started
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
}
