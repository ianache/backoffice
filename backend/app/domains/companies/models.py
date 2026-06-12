from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # user-defined slug, immutable
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default='active', nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # no FK — Keycloak-managed
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
