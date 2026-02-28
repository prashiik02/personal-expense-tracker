import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import React from "react";
import { Link } from "react-router-dom";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    monthly_income: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateStrongPassword = (pw) => {
    if (!pw || pw.length < 8) return "Password must be at least 8 characters.";
    if (!/[A-Z]/.test(pw)) return "Password must contain at least one uppercase letter.";
    if (!/[a-z]/.test(pw)) return "Password must contain at least one lowercase letter.";
    if (!/\d/.test(pw)) return "Password must contain at least one number.";
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(pw)) return "Password must contain at least one special character (!@#$%^&* etc.).";
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const pwErr = validateStrongPassword(form.password);
    if (pwErr) {
      setError(pwErr);
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setIsSubmitting(true);
    const income = Number(form.monthly_income);
    if (!Number.isFinite(income) || income <= 0) {
      setError("Please enter a valid monthly income (₹) greater than 0.");
      return;
    }
    try {
      const payload = {
        name: form.name,
        email: form.email,
        password: form.password,
        monthly_income: income,
      };
      await register(payload);
      navigate("/login");
    } catch (err) {
      const message =
        err?.response?.data?.error ||
        err?.message ||
        "Registration failed. Please try again.";
      setError(typeof message === "string" ? message : "Registration failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const labelStyle = { fontSize: "11px", color: "var(--finsight-muted)", textTransform: "uppercase", letterSpacing: "1px" };

  return (
    <div className="finsight-card" style={{ maxWidth: 420, width: "100%" }}>
      <div style={{ marginBottom: "24px" }}>
        <div className="finsight-logo" style={{ fontSize: "24px", marginBottom: "4px" }}>Fin<span>Sight</span></div>
        <p style={{ fontSize: "12px", color: "var(--finsight-muted)" }}>Create your account</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "16px" }}>
        <label style={{ display: "grid", gap: "6px" }}>
          <span style={labelStyle}>Name</span>
          <input
            className="finsight-input"
            value={form.name}
            placeholder="Your name"
            autoComplete="name"
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: "6px" }}>
          <span style={labelStyle}>Email</span>
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
          <span style={labelStyle}>Monthly income (₹) *</span>
          <input
            className="finsight-input"
            value={form.monthly_income}
            placeholder="e.g. 50000"
            inputMode="decimal"
            onChange={(e) => setForm({ ...form, monthly_income: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: "6px" }}>
          <span style={labelStyle}>Password</span>
          <input
            className="finsight-input"
            value={form.password}
            type="password"
            placeholder="Min 8 chars, upper, lower, number, special"
            autoComplete="new-password"
            title="Min 8 characters, at least one uppercase, lowercase, number, and special character"
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: "6px" }}>
          <span style={labelStyle}>Confirm password</span>
          <input
            className="finsight-input"
            value={form.confirmPassword}
            type="password"
            placeholder="Repeat password"
            autoComplete="new-password"
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
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
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p style={{ marginTop: "20px", fontSize: "12px", color: "var(--finsight-muted)" }}>
        Already have an account? <Link to="/login" style={{ color: "var(--finsight-accent)" }}>Sign in</Link>
      </p>
    </div>
  );
}
