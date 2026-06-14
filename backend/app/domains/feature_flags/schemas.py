import json
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def _validate_rule_combination_mode(v: Optional[str]) -> Optional[str]:
    if v is not None and v not in ('first_match', 'and'):
        raise ValueError("rule_combination_mode must be 'first_match' or 'and'")
    return v


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
    rule_combination_mode: Optional[str] = None

    @field_validator('rule_combination_mode')
    @classmethod
    def validate_rule_combination_mode(cls, v):
        return _validate_rule_combination_mode(v)

    @model_validator(mode='after')
    def validate_scope_target(self):
        """Non-global flags must carry their scope's target column at creation time."""
        if self.scope == 'tenant' and not self.tenant_id:
            raise ValueError("tenant_id is required when scope is 'tenant'")
        if self.scope == 'product' and not self.product_id:
            raise ValueError("product_id is required when scope is 'product'")
        if self.scope == 'company' and not self.company_id:
            raise ValueError("company_id is required when scope is 'company'")
        return self


class FlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[str] = None
    tenant_id: Optional[str] = None
    product_id: Optional[str] = None
    company_id: Optional[str] = None
    enabled: Optional[bool] = None
    default_val: Optional[bool] = None
    complex: Optional[bool] = None
    ttl: Optional[int] = None
    environment: Optional[str] = None
    rollout: Optional[int] = None
    rules: Optional[List[RuleSchema]] = None
    tags: Optional[List[str]] = None
    test_context: Optional[str] = None
    rule_combination_mode: Optional[str] = None

    @field_validator('rule_combination_mode')
    @classmethod
    def validate_rule_combination_mode(cls, v):
        return _validate_rule_combination_mode(v)

    # NOTE: intentionally NO model_validator here — partial updates (e.g. toggling
    # `enabled`) must not be subject to scope/target validation. Merged-state
    # validation happens in router._validate_update_target() when scope/target
    # fields are actually present in the update payload.


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
    rule_combination_mode: str = 'first_match'
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
            if not values.get('rule_combination_mode'):
                values['rule_combination_mode'] = 'first_match'
            return values
        # Handle ORM object without in-place mutation of session attached state
        obj = values
        rules_raw = getattr(obj, 'rules', None)
        tags_raw = getattr(obj, 'tags', None)
        
        rules = json.loads(rules_raw) if isinstance(rules_raw, str) and rules_raw else (rules_raw if isinstance(rules_raw, list) else [])
        tags = json.loads(tags_raw) if isinstance(tags_raw, str) and tags_raw else (tags_raw if isinstance(tags_raw, list) else [])
        rule_combination_mode = getattr(obj, 'rule_combination_mode', None) or 'first_match'
        
        return {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "scope": obj.scope,
            "tenant_id": obj.tenant_id,
            "product_id": obj.product_id,
            "company_id": obj.company_id,
            "enabled": bool(obj.enabled),
            "default_val": bool(obj.default_val),
            "complex": bool(obj.complex),
            "ttl": obj.ttl,
            "environment": obj.environment,
            "rollout": obj.rollout,
            "rules": rules,
            "tags": tags,
            "test_context": obj.test_context,
            "rule_combination_mode": rule_combination_mode,
            "created_by": obj.created_by,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }


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
        # ORM object path without in-place mutation
        obj = values
        members_raw = getattr(obj, 'members', None)
        members = json.loads(members_raw) if isinstance(members_raw, str) and members_raw else (members_raw if isinstance(members_raw, list) else [])
        
        raw_conditions = getattr(obj, 'conditions', None)
        conditions = json.loads(raw_conditions) if isinstance(raw_conditions, str) and raw_conditions else (raw_conditions if isinstance(raw_conditions, list) else [])
        
        segment_type = getattr(obj, 'type', None) or 'manual'
        flag_count = getattr(obj, 'flag_count', 0)
        
        return {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "tenant_id": obj.tenant_id,
            "members": members,
            "type": segment_type,
            "conditions": conditions,
            "test_context": obj.test_context,
            "flag_count": flag_count,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
