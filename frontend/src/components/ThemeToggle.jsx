import React from "react";
import { useTheme } from "../hooks/useTheme";

export default function ThemeToggle({ size = "sm" }) {
  const { theme, toggleTheme } = useTheme();
  const nextLabel = theme === "dark" ? "Light" : "Night";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="finsight-btn"
      style={{
        padding: size === "md" ? "8px 14px" : "6px 12px",
        fontSize: size === "md" ? "12px" : "11px",
        whiteSpace: "nowrap",
      }}
      aria-label={`Switch to ${nextLabel} theme`}
      title={`Switch to ${nextLabel} theme`}
    >
      {nextLabel} theme
    </button>
  );
}

