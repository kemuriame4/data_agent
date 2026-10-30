from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    DECIMAL,
    Boolean,
    BigInteger,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(64), default="operator")
    warehouse_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SKU(Base):
    __tablename__ = "skus"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(128), nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String(512))
    cost_price = Column(DECIMAL(12, 2), nullable=False)
    sale_price = Column(DECIMAL(12, 2), nullable=False)
    weight_kg = Column(Float)
    is_oversized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"
    id = Column(BigInteger, primary_key=True, index=True)
    order_sn = Column(String(128), unique=True, nullable=False, index=True)
    sku = Column(String(128), ForeignKey("skus.sku"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    warehouse_id = Column(Integer, nullable=False, index=True)
    source = Column(String(64), nullable=False, index=True)
    campaign_id = Column(String(128), index=True)
    quantity = Column(Integer, nullable=False)
    gmv = Column(DECIMAL(12, 2), nullable=False)
    discount = Column(DECIMAL(12, 2), default=0)
    shipping_fee = Column(DECIMAL(12, 2), default=0)
    tax = Column(DECIMAL(12, 2), default=0)
    is_returned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sku_ref = relationship("SKU", back_populates="orders")


SKU.orders = relationship("Order", back_populates="sku_ref")


class AdSpend(Base):
    __tablename__ = "ad_spend"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    platform = Column(String(64), nullable=False, index=True)
    campaign_id = Column(String(128), nullable=False, index=True)
    campaign_name = Column(String(255))
    spend = Column(DECIMAL(12, 2), nullable=False)
    impressions = Column(BigInteger, default=0)
    clicks = Column(BigInteger, default=0)
    conversions = Column(Integer, default=0)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(128), ForeignKey("skus.sku"), nullable=False, index=True)
    warehouse_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), index=True)
    user_id = Column(Integer, nullable=True)
    query_text = Column(Text)
    generated_sql = Column(Text)
    execution_status = Column(String(64))
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


Index("idx_orders_created_warehouse", Order.created_at, Order.warehouse_id)
Index("idx_inventory_sku_warehouse", Inventory.sku, Inventory.warehouse_id)
