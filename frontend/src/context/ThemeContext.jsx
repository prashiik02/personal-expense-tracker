import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";

export const ThemeContext = createContext(null);

const STORAGE_KEY = "finsight-theme";
const THEMES = ["light", "dark"];

function normalizeTheme(value) {
  return THEMES.includes(value) ? value : "light";
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => normalizeTheme(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    const t = normalizeTheme(theme);
    localStorage.setItem(STORAGE_KEY, t);

    const root = document.documentElement;
    root.classList.toggle("finsight-theme-dark", t === "dark");
    root.classList.toggle("finsight-theme-light", t === "light");
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (normalizeTheme(prev) === "dark" ? "light" : "dark"));
  }, []);

  const value = useMemo(() => ({ theme: normalizeTheme(theme), setTheme, toggleTheme }), [theme, toggleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

