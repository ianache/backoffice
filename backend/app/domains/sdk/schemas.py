from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class BootstrapSegment(BaseModel):
    id: int
    type: str = 'manual'
    conditions: list[dict] = []
    members: list[str] = []


class BootstrapFlagEntry(BaseModel):
    enabled: bool
    rules: list[dict] = []
    segments: list[BootstrapSegment] = []
    default_val: bool
    scope: str


# BootstrapResponse is a plain dict — no fixed schema needed since keys are flag names
# Return type annotated as dict[str, BootstrapFlagEntry] in router


class EvaluateRequest(BaseModel):
    flag_key: str
    user: dict[str, Any]


class EvaluateResponse(BaseModel):
    flag_key: str
    result: bool


class EvalEventItem(BaseModel):
    flag_key: str
    user_id: str
    result: bool
    evaluated_at: str  # ISO8601


class EvalEventBatch(BaseModel):
    events: list[EvalEventItem]
    product_id: Optional[str] = None


class EvalEventResponse(BaseModel):
    inserted: int
    skipped: int
