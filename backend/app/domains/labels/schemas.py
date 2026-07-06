import json
import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


VALID_LOCALES = ('es_PE', 'en_US')
VALID_LABEL_TYPES = ('LABEL', 'PLACEHOLDER', 'VALIDATION', 'TOOLTIP')


class NamespaceCreate(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    strategy: str = 'lazy'  # 'eager' | 'lazy'
    description: Optional[str] = None

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9_]{1,100}$', v):
            raise ValueError("Namespace id must match ^[a-z0-9_]{1,100}$")
        return v

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        if v not in ('eager', 'lazy'):
            raise ValueError("strategy must be 'eager' or 'lazy'")
        return v


class NamespaceUpdate(BaseModel):
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    strategy: Optional[str] = None
    description: Optional[str] = None

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r'^[a-z0-9_]{1,100}$', v):
            raise ValueError("Namespace id must match ^[a-z0-9_]{1,100}$")
        return v

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ('eager', 'lazy'):
            raise ValueError("strategy must be 'eager' or 'lazy'")
        return v


class NamespaceResponse(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    strategy: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabelCreate(BaseModel):
    tenant_id: str
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    namespace: str
    label_key: str
    label_type: Optional[str] = None
    params: List[str] = []
    description: Optional[str] = None
    # values keyed by locale, e.g. {"es_PE": "Aceptar", "en_US": "Accept"}
    values: dict[str, str] = {}

    @field_validator('label_type')
    @classmethod
    def validate_label_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LABEL_TYPES:
            raise ValueError(f"label_type must be one of {VALID_LABEL_TYPES}")
        return v

    @field_validator('values')
    @classmethod
    def validate_locales(cls, v: dict[str, str]) -> dict[str, str]:
        for locale in v:
            if locale not in VALID_LOCALES:
                raise ValueError(f"locale must be one of {VALID_LOCALES}")
        return v


class LabelUpdate(BaseModel):
    """Full structure edit — PlatformAdmin/TenantAdmin/ProductManager only."""
    label_type: Optional[str] = None
    params: Optional[List[str]] = None
    description: Optional[str] = None
    values: Optional[dict[str, str]] = None
    version: int  # required for optimistic concurrency check

    @field_validator('label_type')
    @classmethod
    def validate_label_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LABEL_TYPES:
            raise ValueError(f"label_type must be one of {VALID_LABEL_TYPES}")
        return v


class LabelValueUpdate(BaseModel):
    """Narrow value-only edit — UXWriter-allowed (Pitfall 3). No structure fields."""
    locale: str
    label_value: str
    version: int

    @field_validator('locale')
    @classmethod
    def validate_locale(cls, v: str) -> str:
        if v not in VALID_LOCALES:
            raise ValueError(f"locale must be one of {VALID_LOCALES}")
        return v


class LocalizedLabelResponse(BaseModel):
    id: int
    tenant_id: str
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    namespace: str
    locale: str
    label_key: str
    label_value: str
    label_type: Optional[str] = None
    params: List[str] = []
    description: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def parse_params(cls, values):
        if isinstance(values, dict):
            v = values.get('params')
            if isinstance(v, str):
                values['params'] = json.loads(v) if v else []
            elif v is None:
                values['params'] = []
            return values
        obj = values
        params_raw = getattr(obj, 'params', None)
        params = json.loads(params_raw) if isinstance(params_raw, str) and params_raw else (params_raw if isinstance(params_raw, list) else [])
        return {
            "id": obj.id,
            "tenant_id": obj.tenant_id,
            "company_id": obj.company_id,
            "product_id": obj.product_id,
            "namespace": obj.namespace,
            "locale": obj.locale,
            "label_key": obj.label_key,
            "label_value": obj.label_value,
            "label_type": obj.label_type,
            "params": params,
            "description": obj.description,
            "version": obj.version,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }


class MissingLabelReportCreate(BaseModel):
    tenant_id: str
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    namespace: str
    label_key: str
    locale: str


class MissingLabelReportResponse(BaseModel):
    id: int
    tenant_id: str
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    namespace: str
    label_key: str
    locale: str
    hits: int
    created_at: datetime
    last_reported_at: datetime

    model_config = ConfigDict(from_attributes=True)
