from sqlalchemy import String, Text, SmallInteger, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime
from typing import Optional


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)  # global|tenant|product|company
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enabled: Mapped[int] = mapped_column(SmallInteger, server_default='1', nullable=False)
    default_val: Mapped[int] = mapped_column(SmallInteger, server_default='0', nullable=False)
    complex: Mapped[int] = mapped_column(SmallInteger, server_default='0', nullable=False)
    ttl: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    environment: Mapped[str] = mapped_column(String(20), server_default='production', nullable=False)
    rollout: Mapped[int] = mapped_column(Integer, server_default='100', nullable=False)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON array as TEXT — MySQL 5.6 safe
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # JSON array as TEXT — MySQL 5.6 safe
    test_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object as TEXT — Live Simulator saved example (Phase 13)
    rule_combination_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'first_match' | 'and'; NULL = 'first_match' (Phase 15)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    members: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of user UUIDs as TEXT
    type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)        # 'manual' | 'rule_based'; NULL treated as 'manual'
    conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)        # JSON array TEXT (same shape as flag rules)
    test_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object as TEXT — Live Simulator saved example (Phase 13)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class FlagSegment(Base):
    __tablename__ = "flag_segments"

    flag_id: Mapped[int] = mapped_column(Integer, ForeignKey("feature_flags.id"), primary_key=True)
    segment_id: Mapped[int] = mapped_column(Integer, ForeignKey("segments.id"), primary_key=True)


class EvalEvent(Base):
    __tablename__ = "eval_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    flag_key: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    result: Mapped[int] = mapped_column(SmallInteger(), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
