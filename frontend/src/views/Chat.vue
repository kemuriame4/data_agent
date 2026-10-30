<script setup lang="ts">
import { nextTick, ref } from "vue";
import { useRouter } from "vue-router";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { askQuestion } from "../services/api";
import { auth } from "../stores/auth";
import Chart from "../components/Chart.vue";

interface Msg {
  role: "user" | "agent";
  text: string;
  sql?: string;
  result?: Record<string, any>[] | null;
  chart?: any;
}

const router = useRouter();
const input = ref("");
const messages = ref<Msg[]>([]);
const loading = ref(false);
const bottom = ref<HTMLElement | null>(null);

const quicks = [
  "近 30 天 GMV 是多少？",
  "上个月退货率最高的 5 个 SKU",
  "美西仓库存低于 50 的沙发",
];

function renderMd(text: string): string {
  return DOMPurify.sanitize(marked.parse(text, { async: false }) as string);
}

async function scrollToBottom() {
  await nextTick();
  bottom.value?.scrollIntoView({ behavior: "smooth" });
}

async function send() {
  const q = input.value.trim();
  if (!q || loading.value) return;
  messages.value.push({ role: "user", text: q });
  input.value = "";
  loading.value = true;
  await scrollToBottom();
  try {
    const res = await askQuestion(q);
    const d = res.data;
    messages.value.push({
      role: "agent",
      text: d.answer || "暂无结论",
      sql: d.sql,
      result: d.result,
      chart: d.chart_config,
    });
  } catch (err: any) {
    messages.value.push({
      role: "agent",
      text: "请求出错：" + (err?.message || String(err)),
    });
  }
  loading.value = false;
  await scrollToBottom();
}

function logout() {
  auth.clear();
  router.push("/login");
}
</script>

<template>
  <div class="mx-auto max-w-5xl p-4">
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">Data Agent 控制台</h1>
      <button class="text-sm text-gray-600 underline" @click="logout">
        退出
      </button>
    </div>

    <div class="mb-4 h-[60vh] overflow-y-auto rounded bg-white p-4 shadow">
      <div
        v-for="(m, idx) in messages"
        :key="idx"
        class="mb-4"
        :class="m.role === 'user' ? 'text-right' : 'text-left'"
      >
        <div
          class="inline-block max-w-[80%] rounded p-3 text-left"
          :class="m.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'"
        >
          <div v-if="m.role === 'user'" class="whitespace-pre-wrap">
            {{ m.text }}
          </div>
          <div
            v-else
            class="text-sm leading-relaxed [&_table]:border-collapse [&_td]:border [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:bg-gray-200 [&_th]:px-2 [&_th]:py-1"
            v-html="renderMd(m.text)"
          ></div>

          <pre
            v-if="m.sql"
            class="mt-2 overflow-x-auto rounded bg-gray-800 p-2 text-xs text-white"
            >{{ m.sql }}</pre
          >

          <Chart v-if="m.chart" :config="m.chart" />

          <div
            v-if="m.result && m.result.length"
            class="mt-2 overflow-x-auto"
          >
            <table class="border-collapse text-xs">
              <thead>
                <tr class="bg-gray-200">
                  <th
                    v-for="k in Object.keys(m.result[0])"
                    :key="k"
                    class="border px-2 py-1"
                  >
                    {{ k }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in m.result.slice(0, 10)" :key="i">
                  <td
                    v-for="(v, j) in Object.values(row)"
                    :key="j"
                    class="border px-2 py-1"
                  >
                    {{ String(v) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <p v-if="loading" class="text-gray-500">Agent 思考中...</p>
      <div ref="bottom"></div>
    </div>

    <div class="mb-2 flex gap-2">
      <button
        v-for="q in quicks"
        :key="q"
        class="rounded border bg-white px-2 py-1 text-xs hover:bg-gray-50"
        @click="
          input = q;
          send();
        "
      >
        {{ q }}
      </button>
    </div>

    <div class="flex gap-2">
      <input
        v-model="input"
        class="flex-1 rounded border p-2"
        placeholder="输入业务问题..."
        @keydown.enter="send"
      />
      <button
        class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        :disabled="loading"
        @click="send"
      >
        发送
      </button>
    </div>
  </div>
</template>
