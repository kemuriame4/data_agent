import { reactive } from "vue";

export const auth = reactive({
  /** 登录失效警告文案，非空时 App 弹出警告框 */
  warning: "",

  get token(): string {
    return localStorage.getItem("token") || "";
  },

  setToken(token: string) {
    localStorage.setItem("token", token);
  },

  clear() {
    localStorage.removeItem("token");
  },

  /** 登录信息丢失/过期：清除本地 token 并触发警告弹窗 */
  expire(message: string) {
    this.clear();
    this.warning = message;
  },
});
