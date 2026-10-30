from typing import List, Dict

SCHEMA_DEFINITIONS = {
    "skus": {
        "description": "商品 SKU 主数据，包含采购成本、售价、类目、重量与图片",
        "columns": {
            "sku": {"type": "VARCHAR", "description": "SKU 编码", "sensitive": False},
            "name": {"type": "VARCHAR", "description": "商品名称", "sensitive": False},
            "category": {"type": "VARCHAR", "description": "类目", "sensitive": False},
            "description": {"type": "TEXT", "description": "商品描述", "sensitive": False},
            "image_url": {"type": "VARCHAR", "description": "图片地址", "sensitive": False},
            "cost_price": {"type": "DECIMAL", "description": "采购成本价", "sensitive": True, "allowed_roles": ["admin", "finance"]},
            "sale_price": {"type": "DECIMAL", "description": "销售价", "sensitive": False},
            "weight_kg": {"type": "FLOAT", "description": "重量 kg", "sensitive": False},
            "is_oversized": {"type": "BOOLEAN", "description": "是否超大件", "sensitive": False},
        },
    },
    "orders": {
        "description": "Shopify 订单事实表",
        "columns": {
            "order_sn": {"type": "VARCHAR", "description": "订单号", "sensitive": False},
            "sku": {"type": "VARCHAR", "description": "SKU 编码", "sensitive": False},
            "user_id": {"type": "INT", "description": "用户 ID", "sensitive": True},
            "warehouse_id": {"type": "INT", "description": "发货仓库 ID", "sensitive": False},
            "source": {"type": "VARCHAR", "description": "流量来源", "sensitive": False},
            "campaign_id": {"type": "VARCHAR", "description": "广告系列 ID", "sensitive": False},
            "quantity": {"type": "INT", "description": "数量", "sensitive": False},
            "gmv": {"type": "DECIMAL", "description": "商品成交额", "sensitive": False},
            "discount": {"type": "DECIMAL", "description": "优惠金额", "sensitive": False},
            "shipping_fee": {"type": "DECIMAL", "description": "运费", "sensitive": False},
            "tax": {"type": "DECIMAL", "description": "税费", "sensitive": False},
            "is_returned": {"type": "BOOLEAN", "description": "是否退货", "sensitive": False},
            "created_at": {"type": "DATETIME", "description": "创建时间", "sensitive": False},
        },
    },
    "ad_spend": {
        "description": "广告平台每日消耗表",
        "columns": {
            "date": {"type": "DATETIME", "description": "日期", "sensitive": False},
            "platform": {"type": "VARCHAR", "description": "广告平台", "sensitive": False},
            "campaign_id": {"type": "VARCHAR", "description": "系列 ID", "sensitive": False},
            "campaign_name": {"type": "VARCHAR", "description": "系列名称", "sensitive": False},
            "spend": {"type": "DECIMAL", "description": "消耗金额", "sensitive": False},
            "impressions": {"type": "BIGINT", "description": "曝光", "sensitive": False},
            "clicks": {"type": "BIGINT", "description": "点击", "sensitive": False},
            "conversions": {"type": "INT", "description": "转化数", "sensitive": False},
        },
    },
    "inventory": {
        "description": "分仓库存表",
        "columns": {
            "sku": {"type": "VARCHAR", "description": "SKU", "sensitive": False},
            "warehouse_id": {"type": "INT", "description": "仓库 ID", "sensitive": False},
            "quantity": {"type": "INT", "description": "库存数量", "sensitive": False},
            "updated_at": {"type": "DATETIME", "description": "更新时间", "sensitive": False},
        },
    },
}

METRICS = {
    "GMV": "SUM(orders.gmv)",
    "AOV": "SUM(orders.gmv) / COUNT(DISTINCT orders.order_sn)",
    "GrossMargin": "SUM(orders.gmv - skus.cost_price * orders.quantity) / SUM(orders.gmv)",
    "ReturnRate": "SUM(CASE WHEN orders.is_returned THEN 1 ELSE 0 END) / COUNT(*)",
    "ROAS": "SUM(orders.gmv) / SUM(ad_spend.spend)",
}

WAREHOUSE_NAMES = {1: "美西仓", 2: "美东仓"}


def get_schema_prompt(tables: List[str]) -> str:
    parts = []
    for t in tables:
        meta = SCHEMA_DEFINITIONS.get(t)
        if not meta:
            continue
        cols = ", ".join([f"{c} {v['type']}" for c, v in meta["columns"].items()])
        parts.append(f"Table {t}: {meta['description']}. Columns: {cols}")
    return "\n".join(parts)


def get_all_tables() -> List[str]:
    return list(SCHEMA_DEFINITIONS.keys())


def get_table_columns(table: str) -> Dict[str, dict]:
    return SCHEMA_DEFINITIONS.get(table, {}).get("columns", {})
