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
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(pw)) return "Password must contain at least one special character.";
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
    const income = Number(form.monthly_income);
    if (!Number.isFinite(income) || income <= 0) {
      setError("Please enter a valid monthly income (₹) greater than 0.");
      return;
    }
    setIsSubmitting(true);
    try {
      await register({
        name: form.name,
        email: form.email,
        password: form.password,
        monthly_income: income,
      });
      navigate("/login");
    } catch (err) {
      const message = err?.response?.data?.error || err?.message || "Registration failed. Please try again.";
      setError(typeof message === "string" ? message : "Registration failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="finsight-auth-card">
      <h1 className="finsight-auth-title">Create your account</h1>
      <p className="finsight-auth-subtitle">Start tracking your expenses today</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div className="finsight-form-row">
          <label className="finsight-form-label">Full name</label>
          <input
            className="finsight-input"
            value={form.name}
            placeholder="Your name"
            autoComplete="name"
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </div>
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
          <label className="finsight-form-label">Monthly income (₹)</label>
          <input
            className="finsight-input"
            value={form.monthly_income}
            placeholder="e.g. 50000"
            inputMode="decimal"
            onChange={(e) => setForm({ ...form, monthly_income: e.target.value })}
            required
          />
        </div>
        <div className="finsight-form-row">
          <label className="finsight-form-label">Password</label>
          <input
            className="finsight-input"
            value={form.password}
            type="password"
            placeholder="Min 8 chars, upper, lower, number, special"
            autoComplete="new-password"
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </div>
        <div className="finsight-form-row">
          <label className="finsight-form-label">Confirm password</label>
          <input
            className="finsight-input"
            value={form.confirmPassword}
            type="password"
            placeholder="Repeat password"
            autoComplete="new-password"
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
            required
          />
        </div>

        {error && (
          <div className="finsight-alert-banner deficit" style={{ marginBottom: 0, padding: "12px 16px" }}>
            <span>{error}</span>
          </div>
        )}

        <button type="submit" className="finsight-btn finsight-btn-black" disabled={isSubmitting} style={{ width: "100%", padding: "14px 16px", marginTop: "4px" }}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p style={{ marginTop: "28px", fontSize: "0.9375rem", color: "var(--finsight-muted)", textAlign: "center" }}>
        Already have an account?{" "}
        <Link to="/login" style={{ color: "var(--fs-green)", fontWeight: 600, textDecoration: "none" }}>
          Sign in
        </Link>
      </p>
    </div>
  );
}
