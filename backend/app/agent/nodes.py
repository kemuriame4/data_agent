import json
from typing import Dict, Any

from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.agent.schema_linking import select_tables
from app.agent.text_to_sql import generate_sql
from app.agent.self_correction import execute_readonly_sql
from app.security.sql_sandbox import SQLSandbox
from app.security.masking import mask_result
from app.security.rbac import RBACPolicy

settings = get_settings()
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=settings.llm_temperature,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

sandbox = SQLSandbox()


def intent_routing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state["question"].lower()
    if any(
        k in question for k in ["归因", "last-touch", "first-touch", "linear", "roas"]
    ):
        intent = "attribution"
    elif any(k in question for k in ["图片", "相似", "沙发", "外观", "风格"]):
        intent = "hybrid_retrieval"
    else:
        intent = "text_to_sql"
    state["intent"] = intent
    state["reasoning"].append(f"Intent detected: {intent}")
    return state


def schema_linking_node(state: Dict[str, Any]) -> Dict[str, Any]:
    tables = select_tables(state["question"])
    state["selected_tables"] = tables
    state["reasoning"].append(f"Selected tables: {tables}")
    return state


def text_to_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    sql = generate_sql(
        state["question"], state["selected_tables"], state.get("error_message", "")
    )
    state["generated_sql"] = sql
    state["reasoning"].append(f"Generated SQL: {sql}")
    return state


def security_injection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    rbac = RBACPolicy(role=state["role"], warehouse_id=state.get("warehouse_id"))
    safe_sql = sandbox.apply(
        state["generated_sql"],
        rbac=rbac,
        selected_tables=state["selected_tables"],
    )
    state["validated_sql"] = safe_sql
    state["reasoning"].append("Security injection applied")
    return state


def execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    ok, result, error = execute_readonly_sql(
        state["validated_sql"], timeout=settings.sql_timeout_seconds
    )
    if ok:
        state["execution_result"] = result
        state["error_message"] = None
    else:
        state["execution_result"] = None
        state["error_message"] = error
    state["reasoning"].append("SQL executed" if ok else f"Execution error: {error}")
    return state


def self_correction_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("error_message") and state["correction_count"] < 3:
        state["correction_count"] += 1
        state["reasoning"].append(
            f"Self-correction attempt {state['correction_count']}"
        )
        return "generate_sql"
    if not state.get("execution_result") and state["correction_count"] < 3:
        state["correction_count"] += 1
        state["error_message"] = "Empty result set"
        state["reasoning"].append(f"Self-correction due to empty result")
        return "generate_sql"
    return "finalize"


def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
    rbac = RBACPolicy(role=state["role"], warehouse_id=state.get("warehouse_id"))
    result = mask_result(state.get("execution_result", []), rbac)
    chart_config = infer_chart(state["question"], result)
    answer_prompt = f"""Given the user question and SQL result, provide a concise Chinese business answer.
Question: {state['question']}
SQL: {state['validated_sql']}
Result: {json.dumps(result, ensure_ascii=False, default=str)}
Answer:"""
    answer = llm.invoke(answer_prompt).content.strip()
    state["final_answer"] = answer
    state["execution_result"] = result
    state["chart_config"] = chart_config
    state["reasoning"].append("Final answer generated")
    return state


def infer_chart(question: str, result: list) -> Dict[str, Any]:
    if not result:
        return None
    keys = list(result[0].keys())
    if len(keys) >= 2:
        return {
            "type": "bar",
            "x_key": keys[0],
            "y_key": keys[1],
            "data": result[:20],
        }
    return None
