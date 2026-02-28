import React from "react";

const CATEGORY_COLORS = {
  groceries: "var(--finsight-success)",
  food_delivery: "var(--finsight-accent4)",
  fuel: "var(--finsight-danger)",
  transport: "var(--finsight-accent)",
  utilities: "var(--finsight-accent)",
  shopping: "var(--finsight-accent)",
  entertainment: "var(--finsight-accent4)",
  emi_loan: "var(--finsight-danger)",
  salary: "var(--finsight-success)",
  default: "var(--finsight-accent)",
};

export default function CategoryBreakdown({ categories }) {
  if (!categories || Object.keys(categories).length === 0) {
    return (
      <div style={{ textAlign: "center", padding: 40, color: "var(--finsight-muted)" }}>
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
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--finsight-text)" }}>
                {category.replace(/_/g, " ")}
              </span>
              <span style={{ fontSize: 13, fontWeight: 700, color: "var(--finsight-text)" }}>
                ₹{amount.toFixed(0)} ({percentage}%)
              </span>
            </div>
            <div
              style={{
                height: 6,
                backgroundColor: "var(--finsight-surface2)",
                borderRadius: 999,
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
