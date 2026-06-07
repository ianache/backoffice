import json
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, model_validator


class RuleSchema(BaseModel):
    attribute: str
    operator: str  # equals | in | notIn | contains | regex
    value: Any
    result: bool


class FlagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str  # global | tenant | product | company
    tenant_id: Optional[str] = None
    product_id: Optional[str] = None
    company_id: Optional[str] = None
    enabled: bool = True
    default_val: bool = False
    complex: bool = False
    ttl: Optional[int] = None
    environment: str = 'production'
    rollout: int = 100
    rules: List[RuleSchema] = []
    tags: List[str] = []


class FlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    default_val: Optional[bool] = None
    complex: Optional[bool] = None
    ttl: Optional[int] = None
    environment: Optional[str] = None
    rollout: Optional[int] = None
    rules: Optional[List[RuleSchema]] = None
    tags: Optional[List[str]] = None


class FlagResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    scope: str
    tenant_id: Optional[str]
    product_id: Optional[str]
    company_id: Optional[str]
    enabled: bool
    default_val: bool
    complex: bool
    ttl: Optional[int]
    environment: str
    rollout: int
    rules: List[RuleSchema]
    tags: List[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def parse_text_fields(cls, values):
        # Handle dict input (e.g. direct construction in tests or API responses)
        if isinstance(values, dict):
            for field in ('rules', 'tags'):
                v = values.get(field)
                if isinstance(v, str):
                    values[field] = json.loads(v) if v else []
                elif v is None:
                    values[field] = []
            return values
        # Handle ORM object
        obj = values
        rules_raw = getattr(obj, 'rules', None)
        tags_raw = getattr(obj, 'tags', None)
        obj.rules = json.loads(rules_raw) if rules_raw else []
        obj.tags = json.loads(tags_raw) if tags_raw else []
        return obj


class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    members: List[str] = []  # list of user UUIDs


class SegmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    members: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def parse_members(cls, values):
        if isinstance(values, dict):
            m = values.get('members')
            if isinstance(m, str):
                values['members'] = json.loads(m) if m else []
            elif m is None:
                values['members'] = []
            return values
        obj = values
        members_raw = getattr(obj, 'members', None)
        obj.members = json.loads(members_raw) if members_raw else []
        return obj
