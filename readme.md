# Data Agent — 跨境电商私域数据运营与归因 Agent

本项目为基于**Text-to-SQL + 多模态向量检索**的生产级智能数据分析系统。运营/决策者用自然语言提问，系统自动完成意图路由、Schema-Linking、SQL生成与自纠错、安全沙箱过滤、执行与图表化回答，并支持商品图文混合检索与多渠道广告归因。

- 后端：Python 3.11 / FastAPI / LangChain / LangGraph
- 存储：MySQL 8.0（业务数据）/ Qdrant（向量）/ Elastic Search（商品与日志检索）/ Redis（缓存）
- LLM：kimi-k3（Moonshot，OpenAI 兼容接口）；Embedding：BGE-M3
- 前端：Vue 3 / Vite / TypeScript / Tailwind CSS / ECharts（bun 管理依赖）
- 部署：Docker Compose / Prometheus / Grafana

---

## 1. 功能特性

| 模块 | 说明 |
| :--- | :--- |
| Text-to-SQL Agent | LangGraph状态机：意图路由 → Schema-Linking → SQL生成 → 安全注入 → 执行 → 自纠错（≤3 次）→ 中文业务解读 |
| 语义层 | 统一数据字典与指标口径（GMV / AOV / 毛利率 / ROAS / 退货率），防止口径歧义与SQL幻觉 |
| 混合检索 | BGE-M3向量化商品图文，Qdrant向量召回 + Elastic Search全文召回，RRF融合排序 |
| 归因引擎 | First-Touch / Last-Touch / Linear三种归因模型，输出广告系列GMV与ROAS |
| 安全治理 | SQL沙箱（禁DDL/DML、单语句、强制LIMIT、执行超时）+ RBAC行级过滤（AST注入`warehouse_id`）与列级屏蔽（采购成本价）+ PII脱敏（手机/邮箱/地址） |
| 缓存与监控 | Redis查询结果缓存；Prometheus `/metrics`暴露；查询日志双写MySQL + ES |

## 2. 项目结构

```
data_agent/
├── docker-compose.yml          # 基础设施与应用一键编排
├── .env.example                # 环境变量模板
├── backend/
│   ├── Dockerfile / requirements.txt / alembic.ini
│   ├── alembic/env.py          # 数据库迁移入口
│   ├── tests/test_smoke.py     # 测试（不使用LLM进行沙箱/RBAC/脱敏/归因）
│   └── app/
│       ├── main.py             # FastAPI入口，挂载/metrics
│       ├── config.py           # pydantic-settings配置中心
│       ├── database/           # SQLAlchemy模型、连接池、种子数据
│       ├── semantic/           # 电商语义层（数据字典+指标口径）
│       ├── agent/              # LangGraph状态机与各节点实现
│       ├── retrieval/          # Qdrant / ES / Embedding / RRF混合检索 / 索引器
│       ├── security/           # JWT认证、RBAC、SQL沙箱、PII脱敏
│       ├── attribution/        # 归因计算引擎
│       ├── services/           # Redis缓存、查询编排、Benchmark
│       ├── etl/                # Shopify / Ads / WMS同步管道骨架
│       └── api/routes/         # auth / query / admin路由
├── frontend/                   # Vue 3 + Vite 控制台（登录 + 对话式分析，登录态丢失自动警告并跳转）
├── prometheus/prometheus.yml
└── grafana/dashboards/
```

## 3. 快速开始

### 3.1 环境变量

```bash
cp .env.example .env
```

编辑`.env`，修改适应的LLM配置（此处为kimi-k3）：

```ini
OPENAI_API_KEY=sk-your-moonshot-api-key
OPENAI_BASE_URL=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k3
```

> 本地开发（非 Docker）需将`.env`中各服务的HOST改为`localhost`。

### 3.2 方式一：Docker Compose（推荐）

```bash
docker compose up -d --build
```

- 前端：http://localhost:3000
- 后端：
    - 文档 http://localhost:8000/docs
    - 指标 http://localhost:8000/metrics
- Grafana：http://localhost:3001
- Prometheus：http://localhost:9090

### 3.3 方式二：本地开发

```bash
# 基础设施
docker compose up -d mysql qdrant elasticsearch redis

# 后端推荐使用 uv
uv venv --python 3.11
uv pip install -r backend/requirements.txt
set PYTHONPATH=backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端推荐使用 bun
cd frontend
bun install
bun run dev          # http://localhost:3000（/api 已代理到 :8000）
```

### 3.4 初始化数据与索引

```bash
# 测试数据，建表 + 种子数据（50 SKU / 2000 订单 / 90 天广告消耗 / 分仓库存）
$env:PYTHONPATH="backend"; .\.venv\Scripts\python -m app.database.seed_data

# 商品向量化并写入Qdrant + Elastic Search（首次下载BGE-M3约2.2GB）
$env:PYTHONPATH="backend"; .\.venv\Scripts\python -m app.retrieval.indexer
```

预置账号：`admin/admin`（全量权限）、`west_operator/west`（仅美西仓）、`east_operator/east`、`finance/finance`。

## 4. API 概览

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| POST | `/api/v1/auth/login` | 登录，返回 JWT |
| POST | `/api/v1/query/ask` | 自然语言问答（Text-to-SQL 全链路） |
| POST | `/api/v1/query/attribution?model=last_touch&days=30&top_n=10` | 归因报表 |
| POST | `/api/v1/query/hybrid-search` | 商品混合检索（文本 + SQL 过滤） |
| POST | `/api/v1/admin/seed` | 种子数据（admin） |
| POST | `/api/v1/admin/index-products` | 重建向量/全文索引（admin） |
| POST | `/api/v1/admin/benchmark` | 内置 Benchmark 自测 |
| GET | `/health` / `/metrics` | 健康检查 / Prometheus 指标 |

示例提问：

- `近 30 天通过 Facebook 广告进入、购买了办公椅类目且配送到美东仓的订单总量、平均客单价和退货率`
- `上个月 GMV 前 10 的 SKU`
- `美西仓库存低于 50 的爆款沙发`

## 5. 测试

```bash
# 无需LLM/数据库的测试：沙箱拦截、LIMIT/行过滤注入、列级RBAC、PII脱敏、三种归因、语义层
$env:PYTHONPATH="backend"; .\.venv\Scripts\python backend\tests\test_smoke.py
```

## 6. 环境依赖说明（Windows 实测）

- **uv**：Python 包管理；首次创建venv，若因沙箱无法创建junction，需在非沙箱终端执行
> ```bash
> uv venv --python 3.11
> ```
- **bcrypt 锁定版本4.0.1**：passlib1.7.4与bcrypt5.x不兼容（已在`requirements.txt`固定）
- **hf_xet**：Hugging Face模型加速下载，已加入`requirements.txt`
- **Bun**：安装脚本在沙箱内可能未解压`bun.exe`，需手动解压`~\.bun\bin\bun-windows-x64.zip`；运行`bun run dev`前需将`~\.bun\bin`加入PATH
- **vue-demi postinstall 失败**：本机无 node 时 `bun install` 会因 postinstall 脚本中断，改用 `bun install --ignore-scripts`（vue-demi 默认即链接 Vue 3，无影响）

## 7. 安全说明

- 仅允许只读 SELECT；DDL/DML/多语句在沙箱层直接拒绝
- 行级隔离：按用户`warehouse_id`在 SQL查询中强制注入过滤条件
- 列级屏蔽：`cost_price`等敏感列对非`admin/finance`角色返回`****`
- PII脱敏：手机号/邮箱/地址在响应层统一掩码
- 数据库账号建议配置为只读权限（生产环境）
