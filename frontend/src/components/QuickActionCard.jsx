import React from "react";
import { Link } from "react-router-dom";

export default function QuickActionCard({ title, description, icon, color, link, onClick }) {
  const Component = link ? Link : "div";

  return (
    <Component
      to={link}
      onClick={onClick}
      style={{
        backgroundColor: "var(--finsight-surface)",
        border: `1.5px solid ${color}22`,
        borderRadius: 12,
        padding: 20,
        textDecoration: "none",
        color: "inherit",
        cursor: link ? "pointer" : "auto",
        transition: "all 0.2s",
        flex: "1 1 calc(50% - 8px)",
        minWidth: 180,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "var(--finsight-shadow)";
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.borderColor = color;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.borderColor = `${color}22`;
      }}
    >
      <div style={{ fontSize: 32, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 14, fontWeight: 800, color: "var(--finsight-text)", marginBottom: 4 }}>
        {title}
      </div>
      <div style={{ fontSize: 12, color: "var(--finsight-muted)" }}>
        {description}
      </div>
    </Component>
  );
}
