import React from "react";
import { Link } from "react-router-dom";

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
  info: "#9b59b6",
  secondary: "#1abc9c",
};

export default function QuickActionCard({ title, description, icon, color, link, onClick }) {
  const Component = link ? Link : "div";

  return (
    <Component
      to={link}
      onClick={onClick}
      style={{
        backgroundColor: COLORS.white,
        border: `1.5px solid ${color}22`,
        borderRadius: 8,
        padding: 20,
        textDecoration: "none",
        color: "inherit",
        cursor: link ? "pointer" : "auto",
        transition: "all 0.2s",
        flex: "1 1 calc(50% - 8px)",
        minWidth: 180,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 4px 12px ${color}22`;
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
      <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.dark, marginBottom: 4 }}>
        {title}
      </div>
      <div style={{ fontSize: 12, color: COLORS.gray }}>
        {description}
      </div>
    </Component>
  );
}
