from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime
from typing import Optional


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # user-defined slug, immutable
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default='active', nullable=False)
    labels: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as TEXT — MySQL 5.6 safe
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"

    tenant_id: Mapped[str] = mapped_column(String(100), primary_key=True)  # String, no FK constraint
    product_id: Mapped[str] = mapped_column(String(50), ForeignKey("products.id"), primary_key=True)
    subscribed_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    # NO onupdate — append-only join row


class FlagProduct(Base):
    __tablename__ = "flag_products"

    flag_id: Mapped[int] = mapped_column(Integer, ForeignKey("feature_flags.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(50), ForeignKey("products.id"), primary_key=True)
    # NO timestamps — pure join table
