import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

export default function MonthlyChart({ data }) {
  return (
    <BarChart width={500} height={300} data={data}>
      <XAxis dataKey="transaction_date" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="amount" />
    </BarChart>
  );
}