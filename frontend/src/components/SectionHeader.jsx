import React from "react";

const COLORS = {
  primary: "#3498db",
  dark: "#2c3e50",
  gray: "#7f8c8d",
  lightGray: "#ecf0f1",
  border: "#e0e6ed",
};

export default function SectionHeader({ title, subtitle, icon }) {
  return (
    <div style={{ marginBottom: 24, borderBottom: `1px solid ${COLORS.border}`, paddingBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        {icon && <span style={{ fontSize: 24 }}>{icon}</span>}
        <h2 style={{ fontSize: 20, fontWeight: 700, color: COLORS.dark, margin: 0 }}>
          {title}
        </h2>
      </div>
      {subtitle && (
        <p style={{ fontSize: 13, color: COLORS.gray, margin: 0, marginTop: 4 }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}
