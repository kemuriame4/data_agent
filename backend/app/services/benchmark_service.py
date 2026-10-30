import json
from typing import List, Dict

from app.agent.graph import run_agent


DEFAULT_BENCHMARK = [
    {
        "question": "近 30 天通过 Facebook 广告进入、购买了办公椅类目且配送到美东仓的订单总量、平均客单价和退货率",
        "expected_tables": ["orders", "skus"],
    },
    {
        "question": "上个月 GMV 前 10 的 SKU",
        "expected_tables": ["orders"],
    },
    {
        "question": "美西仓库存低于 50 的爆款沙发",
        "expected_tables": ["inventory", "skus", "orders"],
    },
]


def run_benchmark(role: str = "operator") -> List[Dict]:
    results = []
    for item in DEFAULT_BENCHMARK:
        state = run_agent(item["question"], role=role)
        results.append(
            {
                "question": item["question"],
                "expected_tables": item["expected_tables"],
                "selected_tables": state["selected_tables"],
                "sql": state["validated_sql"],
                "success": not state.get("error_message"),
                "error": state.get("error_message"),
            }
        )
    return results
