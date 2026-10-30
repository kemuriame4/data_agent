<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../services/api";
import { auth } from "../stores/auth";

const router = useRouter();
const username = ref("admin");
const password = ref("admin");
const error = ref("");

async function submit() {
  error.value = "";
  try {
    const res = await login(username.value, password.value);
    auth.setToken(res.data.access_token);
    router.push("/");
  } catch {
    error.value = "登录失败，请检查用户名和密码";
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center">
    <form class="w-96 rounded bg-white p-8 shadow-md" @submit.prevent="submit">
      <h1 class="mb-4 text-2xl font-bold">Data Agent 登录</h1>
      <p v-if="error" class="mb-2 text-red-500">{{ error }}</p>
      <input
        v-model="username"
        class="mb-3 w-full rounded border p-2"
        placeholder="用户名"
      />
      <input
        v-model="password"
        type="password"
        class="mb-3 w-full rounded border p-2"
        placeholder="密码"
      />
      <button
        class="w-full rounded bg-blue-600 p-2 text-white hover:bg-blue-700"
        type="submit"
      >
        登录
      </button>
    </form>
  </div>
</template>
