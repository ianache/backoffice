from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


# Canonical action_type string constants — covers Plans 16-02/16-03 instrumentation.
class ActionType:
    CREATE_FLAG = "CREATE_FLAG"
    UPDATE_FLAG = "UPDATE_FLAG"
    DELETE_FLAG = "DELETE_FLAG"
    ENABLE_FLAG = "ENABLE_FLAG"
    DISABLE_FLAG = "DISABLE_FLAG"
    CREATE_SEGMENT = "CREATE_SEGMENT"
    UPDATE_SEGMENT = "UPDATE_SEGMENT"
    DELETE_SEGMENT = "DELETE_SEGMENT"
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    ENABLE_USER = "ENABLE_USER"
    DISABLE_USER = "DISABLE_USER"
    RESET_MFA = "RESET_MFA"
    CREATE_TENANT = "CREATE_TENANT"
    UPDATE_TENANT = "UPDATE_TENANT"
    DELETE_TENANT = "DELETE_TENANT"
    CREATE_COMPANY = "CREATE_COMPANY"
    UPDATE_COMPANY = "UPDATE_COMPANY"


class AuditLogCreate(BaseModel):
    """Internal helper input for write_audit_log() — not exposed via any endpoint."""
    tenant_id: Optional[str] = None
    user_id: str
    user_email: Optional[str] = None
    action_type: str
    environment: str = 'production'
    target_type: str
    target_id: str
    payload_before: Optional[dict] = None
    payload_after: Optional[dict] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    created_at: datetime
    tenant_id: Optional[str] = None
    user_id: str
    user_email: Optional[str] = None
    action_type: str
    environment: str
    target_type: str
    target_id: str
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    limit: int


class AuditLogDiffResponse(BaseModel):
    id: int
    added: Dict[str, Any]
    removed: Dict[str, Any]
    modified: Dict[str, Any]
