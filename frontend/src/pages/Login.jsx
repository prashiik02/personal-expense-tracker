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
    <div className="finsight-auth-card">
      <h1 className="finsight-auth-title">Welcome back</h1>
      <p className="finsight-auth-subtitle">Sign in to your account</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div className="finsight-form-row">
          <label className="finsight-form-label">Email address</label>
          <input
            className="finsight-input"
            value={form.email}
            placeholder="you@example.com"
            autoComplete="email"
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </div>
        <div className="finsight-form-row">
          <label className="finsight-form-label">Password</label>
          <input
            className="finsight-input"
            value={form.password}
            type="password"
            placeholder="Your password"
            autoComplete="current-password"
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </div>

        {error && (
          <div className="finsight-alert-banner deficit" style={{ marginBottom: 0, padding: "12px 16px" }}>
            <span>{error}</span>
          </div>
        )}

        <button type="submit" className="finsight-btn finsight-btn-black" disabled={isSubmitting} style={{ width: "100%", padding: "14px 16px", marginTop: "4px" }}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p style={{ marginTop: "28px", fontSize: "0.9375rem", color: "var(--finsight-muted)", textAlign: "center" }}>
        New here?{" "}
        <Link to="/register" style={{ color: "var(--fs-green)", fontWeight: 600, textDecoration: "none" }}>
          Create an account
        </Link>
      </p>
    </div>
  );
}
