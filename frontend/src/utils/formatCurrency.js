/** Format amount as Indian Rupees (INR). Use this for all currency display — never $ or USD. */
export default function formatCurrency(value) {
  if (value == null || value === "") return "₹0.00";

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(value);
}