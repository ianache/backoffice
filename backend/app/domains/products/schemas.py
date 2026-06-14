import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
import re


class ProductCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str = 'active'
    labels: List[str] = []

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9_]{1,50}$', v):
            raise ValueError("Product id must match ^[a-z0-9_]{1,50}$")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    labels: Optional[List[str]] = None
    # NO id field — slug is immutable


class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    labels: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def parse_text_fields(cls, values):
        # Handle dict input (e.g. direct construction in tests or API responses)
        if isinstance(values, dict):
            v = values.get('labels')
            if isinstance(v, str):
                values['labels'] = json.loads(v) if v else []
            elif v is None:
                values['labels'] = []
            return values
        # Handle ORM object without in-place mutation of session attached state
        obj = values
        labels_raw = getattr(obj, 'labels', None)
        labels = json.loads(labels_raw) if isinstance(labels_raw, str) and labels_raw else (labels_raw if isinstance(labels_raw, list) else [])
        return {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "status": obj.status,
            "labels": labels,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }


class TenantSubscriptionResponse(BaseModel):
    tenant_id: str
    product_id: str
    subscribed_at: datetime

    model_config = ConfigDict(from_attributes=True)
