from typing import Optional, List

from app.semantic.data_dictionary import get_table_columns


class RBACPolicy:
    def __init__(self, role: str, warehouse_id: Optional[int] = None):
        self.role = role
        self.warehouse_id = warehouse_id

    def can_access_column(self, table: str, column: str) -> bool:
        cols = get_table_columns(table)
        meta = cols.get(column, {})
        if not meta.get("sensitive"):
            return True
        allowed = meta.get("allowed_roles", [])
        return self.role in allowed

    def get_allowed_columns(self, table: str) -> List[str]:
        return [c for c, _ in get_table_columns(table).items() if self.can_access_column(table, c)]

    def get_row_filter(self, table: str) -> Optional[str]:
        if table == "orders" and self.warehouse_id is not None:
            return f"warehouse_id = {self.warehouse_id}"
        if table == "inventory" and self.warehouse_id is not None:
            return f"warehouse_id = {self.warehouse_id}"
        return None
