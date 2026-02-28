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
  info: "#9b59b6",
  secondary: "#1abc9c",
};

const CATEGORY_COLORS = {
  groceries: COLORS.success,
  food_delivery: COLORS.warning,
  fuel: COLORS.danger,
  transport: COLORS.secondary,
  utilities: COLORS.info,
  shopping: COLORS.primary,
  entertainment: COLORS.warning,
  emi_loan: COLORS.danger,
  salary: COLORS.success,
  default: COLORS.primary,
};

export default function CategoryBreakdown({ categories }) {
  if (!categories || Object.keys(categories).length === 0) {
    return (
      <div style={{ textAlign: "center", padding: 40, color: COLORS.gray }}>
        <p>No spending data available</p>
      </div>
    );
  }

  const total = Object.values(categories).reduce((sum, val) => sum + val, 0);
  const sorted = Object.entries(categories)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {sorted.map(([category, amount]) => {
        const percentage = ((amount / total) * 100).toFixed(1);
        const color =
          CATEGORY_COLORS[category.toLowerCase()] || CATEGORY_COLORS.default;

        return (
          <div key={category}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 6,
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.dark }}>
                {category.replace(/_/g, " ")}
              </span>
              <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.dark }}>
                ₹{amount.toFixed(0)} ({percentage}%)
              </span>
            </div>
            <div
              style={{
                height: 6,
                backgroundColor: COLORS.lightGray,
                borderRadius: 3,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${percentage}%`,
                  backgroundColor: color,
                  transition: "width 0.3s",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
