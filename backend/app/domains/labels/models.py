from sqlalchemy import String, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime
from typing import Optional


class Namespace(Base):
    __tablename__ = "namespaces"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # user-defined slug, e.g. "common", "page_dashboard"
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    strategy: Mapped[str] = mapped_column(String(10), server_default='lazy', nullable=False)  # 'eager' | 'lazy'
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class LocalizedLabel(Base):
    __tablename__ = "localized_labels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    namespace: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)  # 'es_PE' | 'en_US'
    label_key: Mapped[str] = mapped_column(String(150), nullable=False)
    label_value: Mapped[str] = mapped_column(Text, nullable=False)
    label_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # LABEL|PLACEHOLDER|VALIDATION|TOOLTIP
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as TEXT, e.g. '["min"]' — MySQL 5.6 safe
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, server_default='1', nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class MissingLabelReport(Base):
    __tablename__ = "missing_label_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    namespace: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    label_key: Mapped[str] = mapped_column(String(150), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    hits: Mapped[int] = mapped_column(Integer, server_default='1', nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    last_reported_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
