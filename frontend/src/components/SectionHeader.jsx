import React from "react";

export default function SectionHeader({ title, subtitle, icon }) {
  return (
    <div style={{ marginBottom: 24, borderBottom: "1px solid var(--finsight-border)", paddingBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        {icon && <span style={{ fontSize: 24 }}>{icon}</span>}
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--finsight-text)", margin: 0 }}>
          {title}
        </h2>
      </div>
      {subtitle && (
        <p style={{ fontSize: 13, color: "var(--finsight-muted)", margin: 0, marginTop: 4 }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}
