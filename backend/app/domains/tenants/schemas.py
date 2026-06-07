from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class TenantCreate(BaseModel):
    name: str
    country: str
    default_language: str
    default_currency: str
    default_units: str
    status: str = "active"
    # Whitelabel fields — all optional
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    font_weight: Optional[str] = None
    domain: Optional[str] = None
    products: List[str] = []

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    default_language: Optional[str] = None
    default_currency: Optional[str] = None
    default_units: Optional[str] = None
    status: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    font_weight: Optional[str] = None
    domain: Optional[str] = None
    products: Optional[List[str]] = None

class TenantResponse(TenantCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
