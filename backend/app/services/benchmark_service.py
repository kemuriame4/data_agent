"""
SQL 准确率 Benchmark

对每条测试用例：
1. 运行 Agent 得到 SQL + 执行结果
2. 用 ground_truth_sql 执行一次得到 "正确" 结果
3. 比较两份结果集（集合相等，数值允许浮点容差）

最终输出：
- 语法正确率 = 能执行 SQL 的条数 / 总数
- 语义匹配率 = 结果集完全一致的条数 / 总数
- 业务语义匹配率（允许列名/别名不同，但数据值一致）
- 自纠错统计（平均尝试次数）
"""

from __future__ import annotations

import json
import time
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import text

from app.agent.graph import run_agent
from app.database.mysql_client import get_db_session


# ---------------------------------------------------------------------------
# Ground-truth SQL 集合（基于 seed_data.py 2026-08 ~ 2026-10 真实数据分布）
# 所有 ground truth 使用 orders.date 范围：
#   - 近30天：2026-10-05 ~ 2026-10-30（包含）
#   - 上个月 / 上月：2026-10-01 ~ 2026-10-31（当前日期 2026-11-04）
# ---------------------------------------------------------------------------

BENCHMARK_CASES: List[Dict[str, Any]] = [
    # ---- 简单单表 ----
    {
        "id": "S1",
        "difficulty": "easy",
        "question": "近 30 天订单总量是多少？",
        "ground_truth_sql": """
            SELECT COUNT(*) AS order_count
            FROM orders
            WHERE created_at >= '2026-10-05' AND created_at < '2026-11-04'
        """,
    },
    {
        "id": "S2",
        "difficulty": "easy",
        "question": "近 30 天的总 GMV 是多少？",
        "ground_truth_sql": """
            SELECT ROUND(SUM(gmv), 2) AS total_gmv
            FROM orders
            WHERE created_at >= '2026-10-05' AND created_at < '2026-11-04'
        """,
    },
    {
        "id": "S3",
        "difficulty": "easy",
        "question": "美西仓（warehouse_id = 1）目前库存总量是多少？",
        "ground_truth_sql": """
            SELECT SUM(quantity) AS total_stock
            FROM inventory
            WHERE warehouse_id = 1
        """,
    },
    {
        "id": "S4",
        "difficulty": "easy",
        "question": "上个月退货的订单数量是多少？",
        "ground_truth_sql": """
            SELECT COUNT(*) AS returned_count
            FROM orders
            WHERE is_returned = 1
              AND created_at >= '2026-10-01' AND created_at < '2026-11-01'
        """,
    },
    {
        "id": "S5",
        "difficulty": "easy",
        "question": "上个月订单的平均客单价（平均 GMV）是多少？",
        "ground_truth_sql": """
            SELECT ROUND(AVG(gmv), 2) AS avg_gmv
            FROM orders
            WHERE created_at >= '2026-10-01' AND created_at < '2026-11-01'
        """,
    },

    # ---- 中等：分组 + 单 join ----
    {
        "id": "M1",
        "difficulty": "medium",
        "question": "上个月各广告渠道（source）带来的订单量分别是多少？",
        "ground_truth_sql": """
            SELECT source, COUNT(*) AS order_count
            FROM orders
            WHERE created_at >= '2026-10-01' AND created_at < '2026-11-01'
            GROUP BY source
            ORDER BY order_count DESC
        """,
    },
    {
        "id": "M2",
        "difficulty": "medium",
        "question": "上个月各仓库的 GMV 分别是多少？",
        "ground_truth_sql": """
            SELECT warehouse_id, ROUND(SUM(gmv), 2) AS gmv
            FROM orders
            WHERE created_at >= '2026-10-01' AND created_at < '2026-11-01'
            GROUP BY warehouse_id
        """,
    },
    {
        "id": "M3",
        "difficulty": "medium",
        "question": "近 30 天各 SKU 的订单量排名前 10 的是哪些？",
        "ground_truth_sql": """
            SELECT sku, COUNT(*) AS order_count
            FROM orders
            WHERE created_at >= '2026-10-05' AND created_at < '2026-11-04'
            GROUP BY sku
            ORDER BY order_count DESC
            LIMIT 10
        """,
    },
    {
        "id": "M4",
        "difficulty": "medium",
        "question": "上个月各类目的 GMV 分别是多少？",
        "ground_truth_sql": """
            SELECT s.category, ROUND(SUM(o.gmv), 2) AS gmv
            FROM orders o
            JOIN skus s ON s.sku = o.sku
            WHERE o.created_at >= '2026-10-01' AND o.created_at < '2026-11-01'
            GROUP BY s.category
            ORDER BY gmv DESC
        """,
    },
    {
        "id": "M5",
        "difficulty": "medium",
        "question": "Facebook 渠道上个月的平均客单价和订单量",
        "ground_truth_sql": """
            SELECT COUNT(*) AS order_count, ROUND(AVG(gmv), 2) AS avg_aov
            FROM orders
            WHERE source = 'Facebook'
              AND created_at >= '2026-10-01' AND created_at < '2026-11-01'
        """,
    },
    {
        "id": "M6",
        "difficulty": "medium",
        "question": "所有 SKU 当前库存总量最低的前 5 个",
        "ground_truth_sql": """
            SELECT sku, SUM(quantity) AS total_stock
            FROM inventory
            GROUP BY sku
            ORDER BY total_stock ASC
            LIMIT 5
        """,
    },
    {
        "id": "M7",
        "difficulty": "medium",
        "question": "上个月退货率最高的前 5 个 SKU（退货订单数 / 总订单数）",
        "ground_truth_sql": """
            SELECT sku,
                   SUM(CASE WHEN is_returned = 1 THEN 1 ELSE 0 END) / COUNT(*) AS return_rate
            FROM orders
            WHERE created_at >= '2026-10-01' AND created_at < '2026-11-01'
            GROUP BY sku
            HAVING COUNT(*) >= 3
            ORDER BY return_rate DESC
            LIMIT 5
        """,
    },
    {
        "id": "M8",
        "difficulty": "medium",
        "question": "近 30 天广告投放消耗总量（所有平台）",
        "ground_truth_sql": """
            SELECT ROUND(SUM(spend), 2) AS total_spend
            FROM ad_spend
            WHERE date >= '2026-10-05' AND date < '2026-11-04'
        """,
    },

    # ---- 困难：多表 join + 业务口径 ----
    {
        "id": "H1",
        "difficulty": "hard",
        "question": "近 30 天通过 Facebook 广告进入、购买了「办公椅」类目且配送到美东仓的订单总量、平均客单价和退货率",
        "ground_truth_sql": """
            SELECT COUNT(*) AS order_count,
                   ROUND(AVG(o.gmv), 2) AS avg_aov,
                   ROUND(SUM(CASE WHEN o.is_returned = 1 THEN 1 ELSE 0 END) / COUNT(*), 4) AS return_rate
            FROM orders o
            JOIN skus s ON s.sku = o.sku
            WHERE o.source = 'Facebook'
              AND s.category = '办公椅'
              AND o.warehouse_id = 2
              AND o.created_at >= '2026-10-05' AND o.created_at < '2026-11-04'
        """,
    },
    {
        "id": "H2",
        "difficulty": "hard",
        "question": "上个月 GMV 前 10 的 SKU，同时返回它们当前的总库存数量",
        "ground_truth_sql": """
            SELECT o.sku,
                   ROUND(SUM(o.gmv), 2) AS gmv,
                   COALESCE(SUM(i.quantity), 0) AS stock
            FROM orders o
            LEFT JOIN inventory i ON i.sku = o.sku
            WHERE o.created_at >= '2026-10-01' AND o.created_at < '2026-11-01'
            GROUP BY o.sku
            ORDER BY gmv DESC
            LIMIT 10
        """,
    },
    {
        "id": "H3",
        "difficulty": "hard",
        "question": "各广告平台上个月的 ROAS（GMV / spend）分别是多少？",
        "ground_truth_sql": """
            SELECT o.source AS platform,
                   ROUND(SUM(o.gmv), 2) AS gmv,
                   ROUND(t.spend, 2) AS spend,
                   ROUND(SUM(o.gmv) / t.spend, 2) AS roas
            FROM orders o
            JOIN (
                SELECT platform, SUM(spend) AS spend
                FROM ad_spend
                WHERE date >= '2026-10-01' AND date < '2026-11-01'
                GROUP BY platform
            ) t ON t.platform = o.source
            WHERE o.source IN ('Facebook', 'Google', 'TikTok')
              AND o.created_at >= '2026-10-01' AND o.created_at < '2026-11-01'
            GROUP BY o.source, t.spend
            ORDER BY roas DESC
        """,
    },
    {
        "id": "H4",
        "difficulty": "hard",
        "question": "每个仓库的库存价值（库存数量 * 成本价）最高的前 3 个 SKU",
        "ground_truth_sql": """
            SELECT warehouse_id, sku, stock_value
            FROM (
                SELECT i.warehouse_id,
                       i.sku,
                       ROUND(i.quantity * s.cost_price, 2) AS stock_value,
                       ROW_NUMBER() OVER (PARTITION BY i.warehouse_id ORDER BY i.quantity * s.cost_price DESC) AS rn
                FROM inventory i
                JOIN skus s ON s.sku = i.sku
            ) t
            WHERE rn <= 3
        """,
    },
    {
        "id": "H5",
        "difficulty": "hard",
        "question": "近 30 天各广告 campaign 的花费与带来的订单 GMV，按 campaign 分组",
        "ground_truth_sql": """
            SELECT COALESCE(a.campaign_id, o.campaign_id) AS campaign_id,
                   ROUND(SUM(a.spend), 2) AS spend,
                   ROUND(SUM(o.gmv), 2) AS gmv,
                   ROUND(SUM(o.gmv) / NULLIF(SUM(a.spend), 0), 2) AS roas
            FROM ad_spend a
            LEFT JOIN orders o
                ON o.campaign_id = a.campaign_id
               AND o.created_at >= a.date AND o.created_at < DATE_ADD(a.date, INTERVAL 1 DAY)
            WHERE a.date >= '2026-10-05' AND a.date < '2026-11-04'
            GROUP BY COALESCE(a.campaign_id, o.campaign_id)
            ORDER BY spend DESC
        """,
    },
    {
        "id": "H6",
        "difficulty": "hard",
        "question": "美西仓库存低于 50 的所有「沙发」类 SKU",
        "ground_truth_sql": """
            SELECT i.sku, i.quantity, s.category, s.sale_price
            FROM inventory i
            JOIN skus s ON s.sku = i.sku
            WHERE i.warehouse_id = 1
              AND i.quantity < 50
              AND s.category IN ('布艺沙发', '真皮沙发')
            ORDER BY i.quantity ASC
        """,
    },
    {
        "id": "H7",
        "difficulty": "hard",
        "question": "上个月大件（is_oversized=1）商品的订单量和平均物流费",
        "ground_truth_sql": """
            SELECT COUNT(*) AS order_count,
                   ROUND(AVG(o.shipping_fee), 2) AS avg_shipping
            FROM orders o
            JOIN skus s ON s.sku = o.sku
            WHERE s.is_oversized = 1
              AND o.created_at >= '2026-10-01' AND o.created_at < '2026-11-01'
        """,
    },
]


# ---------------------------------------------------------------------------
# 结果集比较
# ---------------------------------------------------------------------------

def _normalize(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (int, float, bool)):
        return float(v) if isinstance(v, (float, Decimal)) else v
    return str(v)


def _row_key(row: dict) -> tuple:
    return tuple(sorted((k, _normalize(v)) for k, v in row.items()))


def _float_close(a: float, b: float, tol: float = 0.02) -> bool:
    """允许 2% 相对误差，或 0.01 绝对误差。"""
    if a == b:
        return True
    if abs(b) < 1e-6:
        return abs(a) < 1e-6
    return abs(a - b) / abs(b) <= tol or abs(a - b) <= 0.01


def _rows_equal(gt_rows: List[dict], pred_rows: List[dict], tol: float = 0.02) -> bool:
    """比较两行集合。列数/行数必须相同；数值列逐个元素比较。"""
    if len(gt_rows) != len(pred_rows):
        return False
    if not gt_rows:
        return True

    gt_cols = sorted(gt_rows[0].keys())
    pred_cols = sorted(pred_rows[0].keys())
    if gt_cols != pred_cols:
        # 列名不同但列数相同，尝试按位置比较（简单启发：位置对齐）
        gt_keys = list(gt_rows[0].keys())
        pred_keys = list(pred_rows[0].keys())
    else:
        gt_keys = gt_cols
        pred_keys = gt_cols

    gt_sorted = sorted(
        [tuple(_normalize(r[k]) for k in gt_keys) for r in gt_rows],
        key=lambda t: t,
    )
    pred_sorted = sorted(
        [tuple(_normalize(r[k]) for k in pred_keys) for r in pred_rows],
        key=lambda t: t,
    )

    for gt_tup, pr_tup in zip(gt_sorted, pred_sorted):
        if len(gt_tup) != len(pr_tup):
            return False
        for a, b in zip(gt_tup, pr_tup):
            if isinstance(a, float) and isinstance(b, float):
                if not _float_close(a, b, tol):
                    return False
            elif a != b:
                return False
    return True


# ---------------------------------------------------------------------------
# 执行器
# ---------------------------------------------------------------------------

def _execute_sql(sql: str) -> List[dict] | None:
    """执行只读 SQL，返回 dict 列表；失败返回 None。"""
    if not sql:
        return None
    try:
        with get_db_session() as db:
            rows = db.execute(text(sql)).mappings().all()
            return [dict(r) for r in rows]
    except Exception:
        return None


def run_benchmark(role: str = "admin", limit: int | None = None) -> Dict[str, Any]:
    """完整 benchmark，返回汇总报告。"""
    cases = BENCHMARK_CASES[:limit] if limit else BENCHMARK_CASES
    results: List[Dict[str, Any]] = []

    syntax_ok = 0
    semantic_ok = 0
    total_self_corrections = 0

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} ({case['difficulty']}) {case['question'][:40]}...")
        t0 = time.time()

        gt_rows = _execute_sql(case["ground_truth_sql"])
        try:
            state = run_agent(case["question"], role=role)
        except Exception as e:
            state = {
                "validated_sql": "",
                "execution_result": None,
                "correction_count": 0,
                "error_message": f"Agent: crash: {e}",
                "selected_tables": [],
            }
        agent_sql = state.get("validated_sql") or ""
        agent_exec = state.get("execution_result")
        corrections = state.get("correction_count", 0) or 0
        total_self_corrections += corrections

        # execution_result 可能是 list[dict] 或 None/异常字符串
        agent_rows_norm = None
        if isinstance(agent_exec, list):
            agent_rows_norm = [dict(r) for r in agent_exec]
        syntax_success = agent_rows_norm is not None

        semantic_match = False
        if gt_rows is not None and agent_rows_norm is not None:
            semantic_match = _rows_equal(gt_rows, agent_rows_norm)

        if syntax_success:
            syntax_ok += 1
        if semantic_match:
            semantic_ok += 1

        results.append(
            {
                "id": case["id"],
                "difficulty": case["difficulty"],
                "question": case["question"],
                "ground_truth_sql": case["ground_truth_sql"].strip(),
                "ground_truth_rows": gt_rows,
                "agent_sql": agent_sql,
                "agent_rows": agent_rows_norm,
                "syntax_success": syntax_success,
                "semantic_match": semantic_match,
                "correction_attempts": corrections,
                "latency_s": round(time.time() - t0, 2),
                "error": state.get("error_message"),
                "selected_tables": state.get("selected_tables"),
            }
        )

    n = len(cases)
    summary = {
        "total": n,
        "syntax_ok": syntax_ok,
        "syntax_accuracy": round(syntax_ok / n * 100, 1) if n else 0.0,
        "semantic_ok": semantic_ok,
        "semantic_accuracy": round(semantic_ok / n * 100, 1) if n else 0.0,
        "avg_self_corrections": round(total_self_corrections / n, 2) if n else 0.0,
        "results": results,
    }
    return summary


def print_report(summary: Dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("SQL Accuracy Benchmark Report")
    print("=" * 70)
    print(f"  Total cases:             {summary['total']}")
    print(f"  Syntax accuracy:         {summary['syntax_accuracy']}%  ({summary['syntax_ok']}/{summary['total']})")
    print(f"  Semantic accuracy:       {summary['semantic_accuracy']}%  ({summary['semantic_ok']}/{summary['total']})")
    print(f"  Avg self-corrections:    {summary['avg_self_corrections']}")
    print("-" * 70)

    for r in summary["results"]:
        flag = "PASS" if r["semantic_match"] else ("SYNTAX-ONLY" if r["syntax_success"] else "FAIL")
        print(f"  [{flag:10s}] {r['id']} {r['difficulty']:7s} ({r['latency_s']:5.1f}s) {r['question'][:60]}")
        if not r["semantic_match"]:
            if r.get("error"):
                print(f"              error: {r['error']}")
            elif r.get("agent_sql"):
                print(f"              agent_sql:   {r['agent_sql'][:140]}")
            if r.get("agent_rows") is not None and r.get("ground_truth_rows") is not None:
                print(f"              GT rows={len(r['ground_truth_rows']):3d}  Agent rows={len(r['agent_rows']):3d}")


if __name__ == "__main__":
    summary = run_benchmark(limit=None)
    print_report(summary)
