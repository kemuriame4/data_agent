import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = (username: string, password: string) =>
  api.post("/auth/login", { username, password });

export const askQuestion = (question: string) =>
  api.post("/query/ask", { question });

export const getAttribution = (model: string, days: number, topN: number) =>
  api.post("/query/attribution", null, { params: { model, days, top_n: topN } });
