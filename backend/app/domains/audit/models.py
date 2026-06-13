from sqlalchemy import String, Text, Integer, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # no FK — Keycloak-managed, NULL for platform-level actions
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, server_default='production')
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_before: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string — MySQL 5.6 has no native JSON
    payload_after: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON string
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index('ix_audit_logs_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_audit_logs_action_type', 'action_type'),
    )
