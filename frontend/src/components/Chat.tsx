import React, { useState, useRef } from "react";
import ReactECharts from "echarts-for-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { askQuestion, getAttribution } from "../services/api";

interface Props {
  token: string;
  onLogout: () => void;
}

interface Message {
  role: "user" | "agent";
  text: string;
  sql?: string;
  result?: any[];
  chart?: any;
  reasoning?: string[];
}

const Chat: React.FC<Props> = ({ onLogout }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = async () => {
    if (!input.trim()) return;
    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);
    try {
      const res = await askQuestion(question);
      const data = res.data;
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: data.answer || "暂无结论",
          sql: data.sql,
          result: data.result,
          chart: data.chart_config,
          reasoning: data.reasoning,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "agent", text: "请求出错：" + err.message }]);
    }
    setLoading(false);
  };

  const quickAsk = (text: string) => {
    setInput(text);
  };

  return (
    <div className="max-w-5xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Data Agent 控制台</h1>
        <button onClick={onLogout} className="text-sm text-gray-600 underline">
          退出
        </button>
      </div>
      <div className="bg-white rounded shadow p-4 h-[60vh] overflow-y-auto mb-4">
        {messages.map((m, idx) => (
          <div key={idx} className={`mb-4 ${m.role === "user" ? "text-right" : "text-left"}`}>
            <div
              className={`inline-block p-3 rounded max-w-[80%] ${
                m.role === "user" ? "bg-blue-100" : "bg-gray-100"
              }`}
            >
              {m.role === "user" ? (
                <p className="whitespace-pre-wrap">{m.text}</p>
              ) : (
                <div className="text-sm leading-relaxed [&_table]:border-collapse [&_td]:border [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:px-2 [&_th]:py-1 [&_th]:bg-gray-200">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                </div>
              )}
              {m.sql && (
                <pre className="mt-2 text-xs bg-gray-800 text-white p-2 rounded overflow-x-auto">
                  {m.sql}
                </pre>
              )}
              {m.chart && (
                <div className="mt-2">
                  <ReactECharts
                    option={{
                      xAxis: { type: "category", data: m.chart.data.map((d: any) => d[m.chart.x_key]) },
                      yAxis: { type: "value" },
                      series: [{ data: m.chart.data.map((d: any) => d[m.chart.y_key]), type: "bar" }],
                    }}
                    style={{ height: 250 }}
                  />
                </div>
              )}
              {m.result && (
                <div className="mt-2 overflow-x-auto">
                  <table className="text-xs border">
                    <thead>
                      <tr className="bg-gray-200">
                        {Object.keys(m.result[0]).map((k) => (
                          <th key={k} className="px-2 py-1 border">
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {m.result.slice(0, 10).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((v: any, j) => (
                            <td key={j} className="px-2 py-1 border">
                              {String(v)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-gray-500">Agent 思考中...</p>}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 mb-2">
        {[
          "近 30 天 GMV 是多少？",
          "上个月退货率最高的 5 个 SKU",
          "美西仓库存低于 50 的沙发",
        ].map((q) => (
          <button
            key={q}
            onClick={() => quickAsk(q)}
            className="text-xs bg-white border px-2 py-1 rounded hover:bg-gray-50"
          >
            {q}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border p-2 rounded"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="输入业务问题..."
        />
        <button
          onClick={send}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          发送
        </button>
      </div>
    </div>
  );
};

export default Chat;
