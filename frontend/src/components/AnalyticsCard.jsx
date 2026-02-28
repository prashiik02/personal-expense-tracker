import React from "react";

export default function AnalyticsCard({ icon, label, value, subtitle, trend, color = "var(--finsight-accent)" }) {
  return (
    <div
      style={{
        backgroundColor: "var(--finsight-surface)",
        border: "1px solid var(--finsight-border)",
        borderRadius: 12,
        padding: 20,
        flex: 1,
        minWidth: 200,
        transition: "all 0.2s",
        cursor: "pointer",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "var(--finsight-shadow)";
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--finsight-muted)", fontWeight: 700, marginBottom: 8, letterSpacing: 0.2 }}>
            {label}
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--finsight-text)", marginBottom: 8, fontFamily: "'Syne', sans-serif" }}>
            {value}
          </div>
          {subtitle && (
            <div style={{ fontSize: 12, color: "var(--finsight-muted)" }}>
              {subtitle}
            </div>
          )}
          {trend && (
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: trend > 0 ? "var(--finsight-danger)" : "var(--finsight-success)",
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
