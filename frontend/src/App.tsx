import React, { useState } from "react";
import Login from "./components/Login";
import Chat from "./components/Chat";

const App: React.FC = () => {
  const [token, setToken] = useState<string>(localStorage.getItem("token") || "");

  const handleLogin = (t: string) => {
    localStorage.setItem("token", t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken("");
  };

  return (
    <div className="min-h-screen">
      {token ? <Chat token={token} onLogout={handleLogout} /> : <Login onLogin={handleLogin} />}
    </div>
  );
};

export default App;
