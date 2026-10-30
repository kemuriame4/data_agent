from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

from sqlalchemy import func

from app.database.mysql_client import get_db_session
from app.database.models import Order, AdSpend, SKU


MODELS = {"first_touch", "last_touch", "linear"}


def fetch_orders(start: datetime, end: datetime):
    with get_db_session() as db:
        return (
            db.query(Order)
            .filter(Order.created_at >= start, Order.created_at < end)
            .all()
        )


def fetch_ad_spend(start: datetime, end: datetime):
    with get_db_session() as db:
        return db.query(AdSpend).filter(AdSpend.date >= start, AdSpend.date < end).all()


def last_touch_attribution(orders: list) -> Dict[str, float]:
    gmv = defaultdict(float)
    for o in orders:
        key = o.campaign_id or o.source
        gmv[key] += float(o.gmv)
    return dict(gmv)


def first_touch_attribution(orders: list) -> Dict[str, float]:
    gmv = defaultdict(float)
    user_first = {}
    for o in sorted(orders, key=lambda x: x.created_at):
        if o.user_id not in user_first:
            user_first[o.user_id] = o.campaign_id or o.source
        key = user_first[o.user_id]
        gmv[key] += float(o.gmv)
    return dict(gmv)


def linear_attribution(orders: list) -> Dict[str, float]:
    gmv = defaultdict(float)
    user_touch = defaultdict(list)
    for o in orders:
        user_touch[o.user_id].append(o)
    for touches in user_touch.values():
        total = sum(float(t.gmv) for t in touches)
        share = total / len(touches)
        for t in touches:
            key = t.campaign_id or t.source
            gmv[key] += share
    return dict(gmv)


def compute_attribution(
    model: str,
    start: datetime,
    end: datetime,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")

    orders = fetch_orders(start, end)
    ad_spend = fetch_ad_spend(start, end)
    spend_by_campaign = defaultdict(float)
    for a in ad_spend:
        key = a.campaign_id or a.platform
        spend_by_campaign[key] += float(a.spend)

    if model == "last_touch":
        gmv = last_touch_attribution(orders)
    elif model == "first_touch":
        gmv = first_touch_attribution(orders)
    else:
        gmv = linear_attribution(orders)

    results = []
    for key, g in gmv.items():
        spend = spend_by_campaign.get(key, 0)
        results.append(
            {
                "campaign_or_source": key,
                "attributed_gmv": round(g, 2),
                "ad_spend": round(spend, 2),
                "roas": round(g / spend, 2) if spend else None,
            }
        )
    results.sort(key=lambda x: x["attributed_gmv"], reverse=True)
    return results[:top_n]
