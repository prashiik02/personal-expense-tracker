export default function InsightCard({ title, message, type }) {
  const getColor = () => {
    if (type === "warning") return "#f39c12";
    if (type === "danger") return "#e74c3c";
    return "#2ecc71";
  };

  return (
    <div
      style={{
        border: `2px solid ${getColor()}`,
        padding: "16px",
        borderRadius: "8px",
        marginBottom: "12px",
      }}
    >
      <h4 style={{ margin: 0 }}>{title}</h4>
      <p style={{ marginTop: "8px" }}>{message}</p>
    </div>
  );
}