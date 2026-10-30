"""Smoke tests for non-LLM components: sandbox, RBAC, masking, attribution math, cache key.
Run: .venv\\Scripts\\python backend\\tests\\test_smoke.py  (from repo root)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.security.sql_sandbox import SQLSandbox
from app.security.rbac import RBACPolicy
from app.security.masking import mask_result, mask_value

sandbox = SQLSandbox()


def expect_error(sql, desc):
    try:
        sandbox.validate(sql)
    except ValueError:
        print(f"PASS  blocked: {desc}")
        return
    raise AssertionError(f"FAIL  should block: {desc}")


# --- sandbox: DDL/DML interception ---
for sql, desc in [
    ("DROP TABLE orders", "DROP"),
    ("DELETE FROM orders WHERE id=1", "DELETE"),
    ("UPDATE orders SET gmv=0", "UPDATE"),
    ("INSERT INTO orders (id) VALUES (1)", "INSERT"),
    ("SELECT 1; DROP TABLE orders", "multi-statement"),
]:
    expect_error(sql, desc)
sandbox.validate("SELECT sku, SUM(gmv) FROM orders GROUP BY sku")
print("PASS  allows SELECT")

# --- sandbox: LIMIT injection ---
out = sandbox.inject_limit("SELECT * FROM orders")
assert "LIMIT" in out.upper(), out
print("PASS  limit injected:", out)

# --- sandbox: RBAC row-level filter injection (west warehouse) ---
rbac_west = RBACPolicy(role="operator", warehouse_id=1)
safe = sandbox.apply(
    "SELECT sku, gmv FROM orders WHERE created_at >= '2026-01-01'",
    rbac=rbac_west,
    selected_tables=["orders"],
)
assert "warehouse_id = 1" in safe, safe
assert "LIMIT" in safe.upper(), safe
print("PASS  row filter + limit:", safe)

safe2 = sandbox.apply("SELECT sku FROM inventory", rbac=rbac_west, selected_tables=["inventory"])
assert "warehouse_id = 1" in safe2, safe2
print("PASS  inventory filter:", safe2)

# --- RBAC: column-level ---
assert rbac_west.can_access_column("skus", "sale_price") is True
assert rbac_west.can_access_column("skus", "cost_price") is False
assert RBACPolicy(role="finance").can_access_column("skus", "cost_price") is True
print("PASS  column-level RBAC")

# --- masking ---
rows = [{"sku": "SKU-1", "cost_price": "99.00", "customer_email": "zhangsan@gmail.com", "phone": "13812345678"}]
masked = mask_result(rows, rbac_west)
assert masked[0]["cost_price"] == "****", masked
assert "****" in masked[0]["customer_email"], masked
assert masked[0]["phone"] == "138****5678", masked
assert mask_value("address", "123 Main St") == "****"
print("PASS  masking:", masked[0])

# --- attribution math (pure functions) ---
from datetime import datetime
from app.attribution.attribution_engine import last_touch_attribution, first_touch_attribution, linear_attribution


class FakeOrder:
    def __init__(self, user_id, campaign_id, source, gmv, created_at):
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.source = source
        self.gmv = gmv
        self.created_at = created_at


t0 = datetime(2026, 1, 1)
orders = [
    FakeOrder(1, "CAMP-FB-1", "Facebook", 100, t0),
    FakeOrder(1, "CAMP-GG-1", "Google", 200, datetime(2026, 1, 2)),
    FakeOrder(2, "CAMP-FB-1", "Facebook", 50, t0),
]
lt = last_touch_attribution(orders)
assert lt == {"CAMP-FB-1": 150.0, "CAMP-GG-1": 200.0}, lt
ft = first_touch_attribution(orders)
assert lt["CAMP-GG-1"] == 200.0 and ft["CAMP-FB-1"] == 350.0, ft
ln = linear_attribution(orders)
assert abs(ln["CAMP-FB-1"] - 200.0) < 1e-6 and abs(ln["CAMP-GG-1"] - 150.0) < 1e-6, ln
print("PASS  attribution: last_touch / first_touch / linear")

# --- semantic layer ---
from app.semantic.data_dictionary import get_schema_prompt, METRICS

prompt = get_schema_prompt(["orders", "skus"])
assert "orders" in prompt and "skus" in prompt and "GMV" in METRICS
print("PASS  semantic data dictionary")

print("\nALL SMOKE TESTS PASSED")
