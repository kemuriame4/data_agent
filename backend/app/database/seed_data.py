from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.database.mysql_client import get_db_session
from app.database.models import SKU, Order, AdSpend, Inventory, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


CATEGORY = ["办公椅", "布艺沙发", "真皮沙发", "餐桌", "床垫", "书架"]
WAREHOUSES = {1: "美西仓", 2: "美东仓"}
PLATFORMS = ["Facebook", "Google", "TikTok", "Organic"]


def create_sku_data():
    data = []
    for i in range(1, 51):
        cat = random.choice(CATEGORY)
        sku = f"SKU-{i:04d}"
        cost = Decimal(random.uniform(30, 200)).quantize(Decimal("0.01"))
        price = cost * Decimal(random.uniform(1.5, 2.5))
        data.append(
            SKU(
                sku=sku,
                name=f"{cat} 型号{i}",
                category=cat,
                description=f"现代极简风 {cat}，适合小户型，浅灰色",
                image_url=f"https://example.com/images/{sku}.jpg",
                cost_price=cost,
                sale_price=price.quantize(Decimal("0.01")),
                weight_kg=random.uniform(5, 50),
                is_oversized=random.random() > 0.7,
            )
        )
    return data


def create_order_data(skus, days=90):
    data = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    for i in range(1, 2001):
        sku_obj = random.choice(skus)
        created = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        warehouse_id = random.choice(list(WAREHOUSES.keys()))
        platform = random.choice(PLATFORMS)
        campaign = f"CAMP-{platform}-{random.randint(1, 5)}" if platform != "Organic" else None
        qty = random.randint(1, 3)
        gmv = sku_obj.sale_price * qty
        data.append(
            Order(
                order_sn=f"ORD-{i:08d}",
                sku=sku_obj.sku,
                user_id=random.randint(1, 500),
                warehouse_id=warehouse_id,
                source=platform,
                campaign_id=campaign,
                quantity=qty,
                gmv=gmv,
                discount=Decimal(random.uniform(0, 10)).quantize(Decimal("0.01")),
                shipping_fee=Decimal(random.uniform(10, 80)).quantize(Decimal("0.01")),
                tax=(gmv * Decimal("0.08")).quantize(Decimal("0.01")),
                is_returned=random.random() < 0.05,
                created_at=created,
            )
        )
    return data


def create_ad_spend(days=90):
    data = []
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    cur = start
    while cur <= end:
        for platform in ["Facebook", "Google", "TikTok"]:
            for camp_idx in range(1, 6):
                data.append(
                    AdSpend(
                        date=datetime(cur.year, cur.month, cur.day),
                        platform=platform,
                        campaign_id=f"CAMP-{platform}-{camp_idx}",
                        campaign_name=f"{platform} 推广 {camp_idx}",
                        spend=Decimal(random.uniform(50, 500)).quantize(Decimal("0.01")),
                        impressions=random.randint(1000, 50000),
                        clicks=random.randint(50, 2000),
                        conversions=random.randint(0, 50),
                    )
                )
        cur += timedelta(days=1)
    return data


def create_inventory(skus):
    data = []
    for sku in skus:
        for wid in WAREHOUSES:
            data.append(
                Inventory(
                    sku=sku.sku,
                    warehouse_id=wid,
                    quantity=random.randint(0, 500),
                )
            )
    return data


def create_users():
    return [
        User(username="admin", hashed_password=pwd_context.hash("admin"), role="admin"),
        User(username="west_operator", hashed_password=pwd_context.hash("west"), role="operator", warehouse_id=1),
        User(username="east_operator", hashed_password=pwd_context.hash("east"), role="operator", warehouse_id=2),
        User(username="finance", hashed_password=pwd_context.hash("finance"), role="finance"),
    ]


def seed_all():
    with get_db_session() as db:
        if db.query(User).first():
            print("Data already seeded.")
            return

        users = create_users()
        db.add_all(users)
        db.commit()

        skus = create_sku_data()
        db.add_all(skus)
        db.commit()

        db.add_all(create_order_data(skus))
        db.add_all(create_ad_spend())
        db.add_all(create_inventory(skus))
        db.commit()
        print("Seed data inserted.")


if __name__ == "__main__":
    seed_all()
