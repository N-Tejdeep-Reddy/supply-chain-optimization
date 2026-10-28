from datetime import date
from sqlalchemy import String, ForeignKey, Date, Float, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(150), unique=True)

class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(150))
    unit_cost: Mapped[float] = mapped_column(Float)
    lead_time_days: Mapped[int] = mapped_column(Integer)
    safety_stock: Mapped[int] = mapped_column(Integer, default=10)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (CheckConstraint('unit_cost >= 0'), CheckConstraint('lead_time_days >= 0'), CheckConstraint('safety_stock >= 0'))

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    po_id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey('suppliers.supplier_id'))
    order_date: Mapped[date] = mapped_column(Date)
    expected_date: Mapped[date] = mapped_column(Date)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='pending')
    supplier: Mapped[Supplier] = relationship()

class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.product_id'))
    transaction_date: Mapped[date] = mapped_column(Date)
    transaction_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint('quantity > 0'),)

class DemandRecord(Base):
    __tablename__ = "demand_records"
    demand_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.product_id'))
    demand_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint('quantity >= 0'),)
