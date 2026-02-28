import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import React from "react";
import { Link } from "react-router-dom";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login(form.email, form.password);
      navigate("/");
    } catch (err) {
      const message =
        err?.response?.data?.error ||
        err?.message ||
        "Login failed. Please try again.";
      setError(typeof message === "string" ? message : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="finsight-card" style={{ maxWidth: 420, width: "100%" }}>
      <div style={{ marginBottom: "24px" }}>
        <div className="finsight-logo" style={{ fontSize: "24px", marginBottom: "4px" }}>Fin<span>Sight</span></div>
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>Sign in to your account</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "16px" }}>
        <label style={{ display: "grid", gap: "6px" }}>
          <span style={{ fontSize: "11px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>Email</span>
          <input
            className="finsight-input"
            value={form.email}
            placeholder="you@example.com"
            autoComplete="email"
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: "6px" }}>
          <span style={{ fontSize: "11px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>Password</span>
          <input
            className="finsight-input"
            value={form.password}
            type="password"
            placeholder="Your password"
            autoComplete="current-password"
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </label>

        {error && (
          <div className="finsight-alert-banner" style={{ marginBottom: 0, padding: "10px 14px" }}>
            <span className="finsight-alert-icon">⚠️</span>
            <div className="finsight-alert-text" style={{ fontSize: "12px" }}>{error}</div>
          </div>
        )}

        <button type="submit" className="finsight-btn finsight-btn-primary" disabled={isSubmitting} style={{ padding: "12px" }}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p style={{ marginTop: "20px", fontSize: "12px", color: "var(--finsight-muted)" }}>
        New here? <Link to="/register" style={{ color: "var(--finsight-accent)" }}>Create an account</Link>
      </p>
    </div>
  );
}
