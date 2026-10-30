from typing import Tuple, Any

from app.database.mysql_client import get_db_session


def execute_readonly_sql(sql: str, timeout: int = 30) -> Tuple[bool, Any, str]:
    lowered = sql.lower().strip()
    forbidden = ["drop", "delete", "update", "insert", "alter", "create", "truncate"]
    if any(lowered.startswith(f) or f" {f} " in lowered for f in forbidden):
        return False, None, "Forbidden statement detected"

    if ";" in sql.rstrip(";"):
        return False, None, "Multiple statements are not allowed"

    try:
        with get_db_session() as session:
            result = session.connection().exec_driver_sql(
                f"SET SESSION MAX_EXECUTION_TIME={timeout * 1000}"
            )
            rows = session.connection().exec_driver_sql(sql).mappings().all()
            return True, [dict(row) for row in rows], ""
    except Exception as e:
        return False, None, str(e)
