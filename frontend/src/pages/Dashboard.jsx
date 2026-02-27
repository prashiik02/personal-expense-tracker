import React from "react";
import { useAuth } from "../hooks/useAuth";

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div style={{ padding: "24px" }}>
      <h2>Welcome</h2>
      {user ? (
        <p>You are signed in as <strong>{user.email}</strong>.</p>
      ) : (
        <p>You are not signed in.</p>
      )}
    </div>
  );
}