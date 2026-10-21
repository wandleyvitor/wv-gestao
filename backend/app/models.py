from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, CheckConstraint, UniqueConstraint
from .db import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    code = Column(String(40), nullable=False, unique=True)
    name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False)
    price_cents = Column(Integer, nullable=False)
    minimum_stock = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint('price_cents >= 0'), CheckConstraint('minimum_stock >= 0'))

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    occurred_at = Column(String(32), nullable=False)
    total_cents = Column(Integer, nullable=False)
    canceled_at = Column(String(32))
    __table_args__ = (CheckConstraint('total_cents >= 0'),)

class SaleItem(Base):
    __tablename__ = 'sale_items'
    id = Column(Integer, primary_key=True)
    sale_id = Column(ForeignKey('sales.id'), nullable=False, index=True)
    product_id = Column(ForeignKey('products.id'), nullable=False)
    product_name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)
    subtotal_cents = Column(Integer, nullable=False)
    __table_args__ = (CheckConstraint('quantity > 0'), CheckConstraint('unit_price_cents >= 0'),
                     CheckConstraint('subtotal_cents = quantity * unit_price_cents'),
                     UniqueConstraint('sale_id', 'product_id'))

class Movement(Base):
    __tablename__ = 'movements'
    id = Column(Integer, primary_key=True)
    product_id = Column(ForeignKey('products.id'), nullable=False, index=True)
    sale_id = Column(ForeignKey('sales.id'), index=True)
    quantity = Column(Integer, nullable=False)  # positivo: entrada; negativo: saída
    kind = Column(String(20), nullable=False)
    reason = Column(String(240), nullable=False)
    occurred_at = Column(String(32), nullable=False)
    __table_args__ = (CheckConstraint('quantity != 0'),
                     UniqueConstraint('sale_id', 'product_id', 'kind'))
