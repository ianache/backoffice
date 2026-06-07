from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    tenant_role: str           # TenantOwner | TenantAdmin | TenantViewer
    product_roles: dict[str, str] = {}  # {product_id: RoleName | ''}


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    tenant_role: Optional[str] = None
    product_roles: Optional[dict[str, str]] = None


class UserResponse(BaseModel):
    id: str            # Keycloak UUID
    username: str
    email: str
    first_name: str
    last_name: str
    enabled: bool
    tenant_id: str
    tenant_role: Optional[str] = None
    product_roles: dict[str, str] = {}
    created_timestamp: int


class UserEventResponse(BaseModel):
    id: int
    keycloak_user_id: str
    actor_sub: str
    action: str
    context: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
