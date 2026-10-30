import React, { useState } from "react";
import { login } from "../services/api";

interface Props {
  onLogin: (token: string) => void;
}

const Login: React.FC<Props> = ({ onLogin }) => {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await login(username, password);
      onLogin(res.data.access_token);
    } catch (err: any) {
      setError("登录失败，请检查用户名和密码");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <form onSubmit={submit} className="bg-white p-8 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Data Agent 登录</h1>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        <input
          className="w-full border p-2 mb-3 rounded"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="用户名"
        />
        <input
          className="w-full border p-2 mb-3 rounded"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码"
        />
        <button className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
          登录
        </button>
      </form>
    </div>
  );
};

export default Login;
