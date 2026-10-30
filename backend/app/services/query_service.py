from datetime import datetime, timedelta
import time

from app.agent.graph import run_agent
from app.attribution.attribution_engine import compute_attribution
from app.retrieval.hybrid_search import hybrid_search
from app.services.cache import get_cached_query, set_cached_query
from app.retrieval.elasticsearch_client import index_event
from app.database.models import EventLog
from app.database.mysql_client import get_db_session


def answer_question(question: str, user: dict) -> dict:
    role = user.get("role", "operator")
    warehouse_id = user.get("warehouse_id")

    cached = get_cached_query(question, role)
    if cached:
        cached["from_cache"] = True
        return cached

    start = time.time()
    try:
        state = run_agent(question, role=role, warehouse_id=warehouse_id)
        result = {
            "question": question,
            "sql": state["validated_sql"],
            "result": state["execution_result"],
            "answer": state["final_answer"],
            "reasoning": state["reasoning"],
            "chart_config": state["chart_config"],
            "error": state.get("error_message"),
            "from_cache": False,
        }
        status = "success" if not state.get("error_message") else "error"
    except Exception as e:
        result = {"question": question, "error": str(e), "from_cache": False}
        status = "exception"

    latency_ms = int((time.time() - start) * 1000)
    set_cached_query(question, role, result)

    try:
        with get_db_session() as db:
            db.add(
                EventLog(
                    user_id=user.get("id"),
                    query_text=question,
                    generated_sql=result.get("sql"),
                    execution_status=status,
                    latency_ms=latency_ms,
                )
            )
            db.commit()
        index_event(
            {
                "user_id": user.get("id"),
                "query_text": question,
                "generated_sql": result.get("sql"),
                "execution_status": status,
                "latency_ms": latency_ms,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    except Exception:
        pass

    return result


def attribution_report(model: str, days: int = 30, top_n: int = 10):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return compute_attribution(model, start, end, top_n)


def hybrid_product_search(text: str, sql_filters: str = None, top_k: int = 10):
    return hybrid_search(text, sql_filters=sql_filters, top_k=top_k)
