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
    test_context: Optional[str] = None


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
    test_context: Optional[str] = None
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
    type: str = 'manual'                    # 'manual' | 'rule_based'
    conditions: List[RuleSchema] = []       # same shape as flag rules
    test_context: Optional[str] = None


class SegmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    members: List[str] = []
    type: str = 'manual'                    # NULL DB value treated as 'manual'
    conditions: List[RuleSchema] = []       # NULL DB value treated as []
    test_context: Optional[str] = None
    flag_count: int = 0                     # injected at query time via list_segments()
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def parse_json_fields(cls, values):
        if isinstance(values, dict):
            for field in ('members', 'conditions'):
                v = values.get(field)
                if isinstance(v, str):
                    values[field] = json.loads(v) if v else []
                elif v is None:
                    values[field] = []
            if not values.get('type'):
                values['type'] = 'manual'
            return values
        # ORM object path
        obj = values
        obj.members = json.loads(obj.members) if getattr(obj, 'members', None) else []
        raw_conditions = getattr(obj, 'conditions', None)
        obj.conditions = json.loads(raw_conditions) if raw_conditions else []
        if not getattr(obj, 'type', None):
            obj.type = 'manual'
        return obj
