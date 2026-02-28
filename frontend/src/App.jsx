import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Categorize from "./pages/Categorize";
import Assistant from "./pages/Assistant";
import Navbar from "./components/Navbar";
import { useAuth } from "./hooks/useAuth";
import ThemeToggle from "./components/ThemeToggle";

function App() {
  const { user } = useAuth();

  useEffect(() => {
    document.body.classList.add("finsight");
    return () => document.body.classList.remove("finsight");
  }, []);

  return (
    <>
      {user && <Navbar />}
      {!user && (
        <div style={{ position: "fixed", top: 16, right: 16, zIndex: 5 }}>
          <ThemeToggle />
        </div>
      )}
      <main className={user ? "finsight-app" : "finsight-app finsight-auth-wrap"}>
        <Routes>
          <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
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

export default App;