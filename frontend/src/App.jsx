import React, { useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Categorize from "./pages/Categorize";
import Assistant from "./pages/Assistant";
import Navbar from "./components/Navbar";
import PublicNavbar from "./components/PublicNavbar";
import { useAuth } from "./hooks/useAuth";

export default function App() {
  const { user } = useAuth();
  const location = useLocation();
  const isAuthPage = ["/login", "/register"].includes(location.pathname);

  useEffect(() => {
    document.body.classList.add("finsight");
    return () => document.body.classList.remove("finsight");
  }, []);

  const mainClass = user
    ? "finsight-app"
    : isAuthPage
      ? "finsight-app finsight-auth-wrap"
      : "finsight-app finsight-app-full";

  return (
    <>
      {user ? (
        <Navbar />
      ) : (
        <PublicNavbar />
      )}
      <main className={mainClass}>
        <Routes>
          <Route path="/" element={user ? <Dashboard /> : <Landing />} />
          <Route path="/categorize" element={user ? <Categorize /> : <Navigate to="/login" />} />
          <Route path="/assistant" element={user ? <Assistant /> : <Navigate to="/login" />} />
          <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
          <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />
          <Route path="/signin" element={<Navigate to="/login" replace />} />
          <Route path="/signup" element={<Navigate to="/register" replace />} />
        </Routes>
      </main>
    </>
  );
}
