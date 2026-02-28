import React from "react";

const COLORS = {
  primary: "#3498db",
  dark: "#2c3e50",
  light: "#fafafa",
  white: "#ffffff",
  gray: "#7f8c8d",
  lightGray: "#ecf0f1",
  border: "#e0e6ed",
  success: "#27ae60",
  warning: "#f39c12",
  danger: "#e74c3c",
};

export default function AnalyticsCard({ icon, label, value, subtitle, trend, color = COLORS.primary }) {
  return (
    <div
      style={{
        backgroundColor: COLORS.white,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 8,
        padding: 20,
        flex: 1,
        minWidth: 200,
        transition: "all 0.2s",
        cursor: "pointer",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.1)";
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 13, color: COLORS.gray, fontWeight: 600, marginBottom: 8 }}>
            {label}
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.dark, marginBottom: 8 }}>
            {value}
          </div>
          {subtitle && (
            <div style={{ fontSize: 12, color: COLORS.gray }}>
              {subtitle}
            </div>
          )}
          {trend && (
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: trend > 0 ? COLORS.danger : COLORS.success,
                marginTop: 4,
              }}
            >
              {trend > 0 ? "↑" : "↓"} {Math.abs(trend).toFixed(1)}% from last month
            </div>
          )}
        </div>
        <div
          style={{
            fontSize: 32,
            opacity: 0.2,
            color: color,
          }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
