import formatCurrency from "../utils/formatCurrency";

export default function SummaryCard({ title, amount }) {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        padding: "16px",
        borderRadius: "8px",
        width: "200px",
        textAlign: "center",
      }}
    >
      <h4>{title}</h4>
      <h2>{formatCurrency(amount)}</h2>
    </div>
  );
}