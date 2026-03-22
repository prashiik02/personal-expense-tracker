import React from "react";
import { useTheme } from "../hooks/useTheme";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const label = isDark ? "Switch to light mode" : "Switch to dark mode";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="finsight-theme-btn finsight-theme-btn-icon"
      aria-label={label}
      title={label}
    >
      <span className="finsight-theme-btn-emoji" aria-hidden>
        {isDark ? "☀️" : "🌙"}
      </span>
    </button>
  );
}
