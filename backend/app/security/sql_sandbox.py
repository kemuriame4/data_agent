import re
import sqlparse
from sqlparse.tokens import DML, DDL

from app.config import get_settings
from app.security.rbac import RBACPolicy
from app.semantic.data_dictionary import get_all_tables

settings = get_settings()


class SQLSandbox:
    FORBIDDEN_KEYWORDS = {
        "drop",
        "delete",
        "update",
        "insert",
        "alter",
        "create",
        "truncate",
    }

    def validate(self, sql: str) -> None:
        lowered = sql.lower()
        for kw in self.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", lowered):
                raise ValueError(f"Forbidden keyword detected: {kw}")
        if ";" in sql.rstrip(";"):
            raise ValueError("Multiple SQL statements are not allowed")
        parsed = sqlparse.parse(sql)
        for stmt in parsed:
            first = stmt.token_first(skip_cm=True)
            if first and first.ttype in (DML, DDL) and first.value.lower() != "select":
                raise ValueError("Only SELECT statements are allowed")

    def inject_limit(self, sql: str) -> str:
        lowered = sql.lower()
        if "limit" not in lowered:
            sql = sql.rstrip(";") + f" LIMIT {settings.max_sql_results}"
        return sql

    def inject_row_filter(
        self, sql: str, rbac: RBACPolicy, selected_tables: list
    ) -> str:
        filters = []
        for t in selected_tables:
            if t in get_all_tables():
                f = rbac.get_row_filter(t)
                if f:
                    filters.append(f)
        if not filters:
            return sql
        clause = " AND ".join(f"({f})" for f in filters)
        sql = sql.rstrip().rstrip(";")

        tail = re.search(
            r"\b(group\s+by|having|order\s+by|limit)\b", sql, re.IGNORECASE
        )
        tail_start = tail.start() if tail else len(sql)

        where = re.search(r"\bwhere\b", sql, re.IGNORECASE)
        if where and where.start() < tail_start:
            insert_pos = tail_start
            sql = (
                sql[:insert_pos].rstrip()
                + f" AND {clause} "
                + sql[insert_pos:].lstrip()
            )
        else:
            insert_pos = tail_start
            sql = (
                sql[:insert_pos].rstrip()
                + f" WHERE {clause} "
                + sql[insert_pos:].lstrip()
            )
        return sql.strip()

    def apply(self, sql: str, rbac: RBACPolicy, selected_tables: list) -> str:
        self.validate(sql)
        sql = self.inject_row_filter(sql, rbac, selected_tables)
        sql = self.inject_limit(sql)
        return sql
