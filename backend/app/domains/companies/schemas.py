from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
import re


class CompanyCreate(BaseModel):
    id: str
    name: str
    status: str = 'active'
    tenant_id: str

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9_]{1,50}$', v):
            raise ValueError("Company id must match ^[a-z0-9_]{1,50}$")
        return v


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    # NO id field — slug is immutable
    # NO tenant_id field — tenant ownership is immutable


class CompanyResponse(BaseModel):
    id: str
    name: str
    status: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
