import React from "react";
import { Link } from "react-router-dom";

const FEATURES = [
  {
    icon: "₹",
    title: "Log expenses instantly",
    text: "Add transactions from SMS, CSV, or PDF in seconds.",
  },
  {
    icon: "◎",
    title: "Understand your patterns",
    text: "See category breakdowns and trends across all your spending.",
  },
  {
    icon: "⏱",
    title: "Smart categorization",
    text: "ML plus optional AI to label Indian bank and UPI transactions.",
  },
];

export default function Landing() {
  const monthLabel = new Date().toLocaleString("en-IN", { month: "long", year: "numeric" }).toUpperCase();
  const demoTotal = "12,450";
  const demoRows = [
    { label: "Bills", pct: 85, color: "var(--fs-bar-bills)", amt: "4,500" },
    { label: "Food", pct: 55, color: "var(--fs-bar-food)", amt: "3,200" },
    { label: "Health", pct: 35, color: "var(--fs-bar-health)", amt: "2,100" },
    { label: "Transport", pct: 25, color: "var(--fs-bar-transport)", amt: "1,650" },
  ];

  return (
    <div className="finsight-landing">
      <section className="finsight-hero">
        <div className="finsight-hero-copy">
          <span className="finsight-pill">Personal finance tracker</span>
          <h1 className="finsight-hero-title">
            Know where your <span className="finsight-accent-word">money</span> goes
          </h1>
          <p className="finsight-hero-lead">
            Track spending in INR, categorize bank and UPI transactions, and get AI-powered insights — built for India.
          </p>
          <div className="finsight-hero-actions">
            <Link to="/register" className="finsight-btn finsight-btn-black finsight-btn-lg">
              Start tracking free
            </Link>
            <Link to="/login" className="finsight-btn finsight-btn-outline finsight-btn-lg">
              Sign in
            </Link>
          </div>
        </div>
        <div className="finsight-hero-visual">
          <div className="finsight-preview-card">
            <div className="finsight-preview-head">
              <span className="finsight-preview-month">{monthLabel}</span>
              <span className="finsight-preview-total">₹{demoTotal}</span>
            </div>
            <div className="finsight-preview-rows">
              {demoRows.map((r) => (
                <div key={r.label} className="finsight-preview-row">
                  <span className="finsight-preview-label">{r.label}</span>
                  <div className="finsight-preview-bar-wrap">
                    <div className="finsight-preview-bar" style={{ width: `${r.pct}%`, background: r.color }} />
                  </div>
                  <span className="finsight-preview-amt">₹{r.amt}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="finsight-features">
        <div className="finsight-features-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="finsight-feature-card">
              <div className="finsight-feature-icon">{f.icon}</div>
              <h3 className="finsight-feature-title">{f.title}</h3>
              <p className="finsight-feature-text">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="finsight-cta-block">
        <h2 className="finsight-cta-title">Ready to take control?</h2>
        <p className="finsight-cta-sub">Join people who track their expenses with FinSight.</p>
        <Link to="/register" className="finsight-btn finsight-btn-black finsight-btn-lg">
          Create free account
        </Link>
      </section>

      <footer className="finsight-footer">
        <div className="finsight-logo finsight-logo-serif finsight-footer-logo">
          <span className="finsight-logo-mark" aria-hidden />
          FinSight
        </div>
      </footer>
    </div>
  );
}
