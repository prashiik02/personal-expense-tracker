import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import React from "react"; 
export default function Navbar() {
  const { logout } = useAuth();

  return (
    <nav>
      <Link to="/">Dashboard</Link> |{" "}
      <Link to="/upload">Upload</Link> |{" "}
      <button onClick={logout}>Logout</button>
    </nav>
  );
}