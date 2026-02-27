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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setIsSubmitting(true);
    try {
      const payload = {
        name: form.name,
        email: form.email,
        password: form.password,
        monthly_income:
          form.monthly_income === "" ? null : Number(form.monthly_income),
      };
      await register(payload);
      navigate("/");
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

  return (
    <div style={{ maxWidth: 420, margin: "48px auto", padding: 16 }}>
      <h2 style={{ marginBottom: 16 }}>Sign up</h2>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Name</span>
          <input
            value={form.name}
            placeholder="Your name"
            autoComplete="name"
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Email</span>
          <input
            value={form.email}
            placeholder="you@example.com"
            autoComplete="email"
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Monthly income (optional)</span>
          <input
            value={form.monthly_income}
            placeholder="e.g. 50000"
            inputMode="decimal"
            onChange={(e) => setForm({ ...form, monthly_income: e.target.value })}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Password</span>
          <input
            value={form.password}
            type="password"
            placeholder="Create a password"
            autoComplete="new-password"
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Confirm password</span>
          <input
            value={form.confirmPassword}
            type="password"
            placeholder="Repeat password"
            autoComplete="new-password"
            onChange={(e) =>
              setForm({ ...form, confirmPassword: e.target.value })
            }
            required
          />
        </label>

        {error && (
          <div style={{ color: "crimson", fontSize: 14 }}>{error}</div>
        )}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p style={{ marginTop: 12 }}>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}