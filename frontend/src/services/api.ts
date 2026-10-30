import axios from "axios";
import { auth } from "../stores/auth";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api/v1",
});

api.interceptors.request.use((config) => {
  // 登录接口本身无需 token
  if (config.url?.includes("/auth/login")) return config;
  const token = localStorage.getItem("token");
  if (!token) {
    auth.expire("登录信息已丢失，请重新登录");
    return Promise.reject(new Error("No token"));
  }
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      auth.expire("登录已过期，请重新登录");
    }
    return Promise.reject(error);
  }
);

export const login = (username: string, password: string) =>
  api.post("/auth/login", { username, password });

export const askQuestion = (question: string) =>
  api.post("/query/ask", { question });

export const getAttribution = (model: string, days: number, topN: number) =>
  api.post(
    `/query/attribution?model=${model}&days=${days}&top_n=${topN}`
  );
