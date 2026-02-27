export default function TransactionTable({ transactions }) {
  return (
    <table border="1">
      <thead>
        <tr>
          <th>Date</th>
          <th>Description</th>
          <th>Amount</th>
          <th>Type</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map((t) => (
          <tr key={t.id}>
            <td>{t.transaction_date}</td>
            <td>{t.description}</td>
            <td>{t.amount}</td>
            <td>{t.transaction_type}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}