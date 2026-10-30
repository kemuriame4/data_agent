import { createRouter, createWebHistory } from "vue-router";
import { auth } from "./stores/auth";
import Login from "./views/Login.vue";
import Chat from "./views/Chat.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: Login },
    { path: "/", component: Chat },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  if (to.path !== "/login" && !token) {
    // 丢失登录信息：弹出警告并跳转登录页
    auth.expire("登录信息已丢失，请重新登录");
    return "/login";
  }
  if (to.path === "/login" && token) return "/";
  return true;
});

export default router;
