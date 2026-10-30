<script setup lang="ts">
import { useRouter } from "vue-router";
import { auth } from "./stores/auth";

const router = useRouter();

function confirmWarning() {
  auth.warning = "";
  router.push("/login");
}
</script>

<template>
  <!-- 登录信息丢失警告弹窗 -->
  <div
    v-if="auth.warning"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
  >
    <div class="w-80 rounded-lg bg-white p-6 text-center shadow-xl">
      <h3 class="mb-2 text-lg font-bold text-amber-600">警告</h3>
      <p class="mb-4 text-sm text-gray-700">{{ auth.warning }}</p>
      <button
        class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        @click="confirmWarning"
      >
        去登录
      </button>
    </div>
  </div>

  <router-view />
</template>
