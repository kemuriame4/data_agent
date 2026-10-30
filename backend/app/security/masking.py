import re
from typing import List, Dict, Any

from app.security.rbac import RBACPolicy
from app.semantic.data_dictionary import get_all_tables, get_table_columns


def mask_value(key: str, value: Any) -> Any:
    if value is None:
        return None
    lower_key = key.lower()
    if "phone" in lower_key or "mobile" in lower_key:
        return re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", str(value))
    if "email" in lower_key:
        parts = str(value).split("@")
        if len(parts) == 2:
            return parts[0][:2] + "****@" + parts[1]
    if "address" in lower_key:
        return "****"
    return value


def mask_result(rows: List[Dict[str, Any]], rbac: RBACPolicy) -> List[Dict[str, Any]]:
    if not rows:
        return rows
    first_keys = list(rows[0].keys())
    table_guess = None
    for t in get_all_tables():
        cols = set(get_table_columns(t).keys())
        if set(first_keys) & cols:
            table_guess = t
            break

    masked = []
    for row in rows:
        new_row = {}
        for k, v in row.items():
            if table_guess and not rbac.can_access_column(table_guess, k):
                new_row[k] = "****"
            else:
                new_row[k] = mask_value(k, v)
        masked.append(new_row)
    return masked
