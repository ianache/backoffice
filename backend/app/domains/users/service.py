"""
Users domain service.

All user operations orchestrate the Keycloak Admin API and write audit
entries to the user_events PostgreSQL table.

IMPORTANT RULES:
- Tenant scoping: always filter by tenant_id from actor_tenant_id parameter,
  never trust tenant_id from the request body for listing.
- Role assignment: GET /roles/{name} first to retrieve the UUID; Keycloak
  returns 400 if you assign by name only.
- User creation returns 201 with no body; extract UUID from Location header:
  location.rstrip("/").split("/")[-1]
- tenant_id is stored as an array in Keycloak attributes:
  write {"tenant_id": [tenant_id]}, read attributes.get("tenant_id", [""])[0]
- context dict is serialized to/from JSON string because user_events.context
  is a TEXT column (MySQL 5.6 does not support the JSON column type).
"""
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.services.keycloak_admin import kcAdminGet, kcAdminPost, kcAdminPut, kcAdminDelete
from app.domains.audit import service as audit_service
from app.domains.audit.schemas import AuditLogCreate, ActionType
from .models import UserEvent
from .schemas import UserCreate, UserUpdate, UserResponse

# Keycloak internal roles to exclude from user role lists
_KC_INTERNAL_ROLES = {"offline_access", "uma_authorization"}


def _is_internal_role(name: str) -> bool:
    if name in _KC_INTERNAL_ROLES:
        return True
    if name.startswith("default-roles-"):
        return True
    return False


def _parse_user(kc_user: dict) -> UserResponse:
    """Convert a Keycloak user representation to UserResponse."""
    attrs = kc_user.get("attributes") or {}
    tenant_id = (attrs.get("tenant_id") or [""])[0]
    return UserResponse(
        id=kc_user["id"],
        username=kc_user.get("username", ""),
        email=kc_user.get("email", ""),
        first_name=kc_user.get("firstName", ""),
        last_name=kc_user.get("lastName", ""),
        enabled=kc_user.get("enabled", True),
        tenant_id=tenant_id,
        tenant_role=None,  # filled in by callers that fetch roles separately
        product_roles={},
        created_timestamp=kc_user.get("createdTimestamp", 0),
    )


async def _get_user_roles(user_id: str) -> tuple[Optional[str], dict[str, str]]:
    """
    Fetch realm role-mappings for a user.
    Returns (tenant_role, product_roles) where tenant_role is the first
    non-internal role matching known tenant role names.
    """
    resp = await kcAdminGet(f"/users/{user_id}/role-mappings/realm")
    if resp.status_code != 200:
        return None, {}
    roles = resp.json()
    tenant_role: Optional[str] = None
    product_roles: dict[str, str] = {}
    for r in roles:
        name = r.get("name", "")
        if _is_internal_role(name):
            continue
        tenant_role = name  # last writer wins but we take first non-internal
        break
    return tenant_role, product_roles


async def _get_role_rep(role_name: str) -> dict:
    """
    Retrieve the Keycloak role representation {id, name} for a realm role.
    Required before assigning or removing roles (Keycloak needs the UUID).
    """
    resp = await kcAdminGet(f"/roles/{role_name}")
    if resp.status_code == 404:
        raise HTTPException(status_code=422, detail=f"Role '{role_name}' not found in Keycloak realm")
    resp.raise_for_status()
    data = resp.json()
    return {"id": data["id"], "name": data["name"]}


async def _write_event(
    db: AsyncSession,
    *,
    keycloak_user_id: str,
    tenant_id: str,
    actor_sub: str,
    action: str,
    context: Optional[dict] = None,
) -> None:
    """Append an audit row to user_events. context dict is JSON-serialized to TEXT."""
    context_str: Optional[str] = json.dumps(context) if context is not None else None
    event = UserEvent(
        keycloak_user_id=keycloak_user_id,
        tenant_id=tenant_id,
        actor_sub=actor_sub,
        action=action,
        context=context_str,
    )
    db.add(event)
    await db.commit()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def list_users(tenant_id: str, db: AsyncSession) -> list[UserResponse]:
    """
    List all users belonging to the given tenant.
    Uses Keycloak attribute search: q=tenant_id:{tenant_id}.
    """
    resp = await kcAdminGet(
        "/users",
        params={"q": f"tenant_id:{tenant_id}", "max": 500},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to list users from Keycloak")

    users = []
    for kc_user in resp.json():
        user = _parse_user(kc_user)
        # Only return users that strictly belong to this tenant
        if user.tenant_id != tenant_id:
            continue
        tenant_role, product_roles = await _get_user_roles(kc_user["id"])
        user.tenant_role = tenant_role
        user.product_roles = product_roles
        users.append(user)
    return users


async def create_user(
    payload: UserCreate,
    tenant_id: str,
    actor_sub: str,
    db: AsyncSession,
) -> UserResponse:
    """
    Create a user in Keycloak with tenant_id attribute, assign tenant_role,
    and write a user.created audit event.
    """
    body = {
        "username": payload.email,
        "email": payload.email,
        "firstName": payload.first_name,
        "lastName": payload.last_name,
        "enabled": True,
        "attributes": {"tenant_id": [tenant_id]},
    }
    resp = await kcAdminPost("/users", json=body)
    if resp.status_code == 409:
        raise HTTPException(status_code=409, detail="User already exists with this email")
    if resp.status_code != 201:
        detail = resp.text or "Failed to create user in Keycloak"
        raise HTTPException(status_code=502, detail=detail)

    # Extract new user UUID from Location header
    location = resp.headers.get("Location", "")
    user_id = location.rstrip("/").split("/")[-1]
    if not user_id:
        raise HTTPException(status_code=502, detail="Keycloak did not return user location")

    # Assign tenant role
    role_rep = await _get_role_rep(payload.tenant_role)
    role_resp = await kcAdminPost(
        f"/users/{user_id}/role-mappings/realm",
        json=[role_rep],
    )
    if role_resp.status_code not in (200, 204):
        raise HTTPException(status_code=502, detail="Failed to assign tenant role in Keycloak")

    await _write_event(
        db,
        keycloak_user_id=user_id,
        tenant_id=tenant_id,
        actor_sub=actor_sub,
        action="user.created",
        context={"email": payload.email, "tenant_role": payload.tenant_role},
    )

    # Fetch and return the full user representation
    get_resp = await kcAdminGet(f"/users/{user_id}")
    get_resp.raise_for_status()
    user = _parse_user(get_resp.json())
    user.tenant_role = payload.tenant_role

    # user_email=None is a deliberate, documented limitation — users/service.py
    # operates purely via the Keycloak Admin API with no FastAPI Request/Header
    # context. If the BFF forwards X-User-Email and the router is later extended
    # to pass it through as a new actor_email parameter, this can populate
    # user_email for the ACTOR (not the target user).
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=tenant_id,
        user_id=actor_sub,
        user_email=None,
        action_type=ActionType.CREATE_USER,
        environment='production',
        target_type="USER",
        target_id=user_id,
        payload_before=None,
        payload_after=user.model_dump(mode='json'),
    ))

    return user


async def update_user(
    user_id: str,
    payload: UserUpdate,
    tenant_id: str,
    actor_sub: str,
    db: AsyncSession,
) -> UserResponse:
    """
    Update user profile (email, first/last name) and perform role delta
    (remove old tenant role, assign new one). Writes user.updated audit event.
    """
    # Fetch current user to validate tenant ownership
    get_resp = await kcAdminGet(f"/users/{user_id}")
    if get_resp.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    get_resp.raise_for_status()
    kc_user = get_resp.json()

    attrs = kc_user.get("attributes") or {}
    current_tenant = (attrs.get("tenant_id") or [""])[0]
    if current_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="User does not belong to this tenant")

    payload_before = _parse_user(kc_user).model_dump(mode='json')

    # Build profile update payload
    update_body: dict = {}
    if payload.first_name is not None:
        update_body["firstName"] = payload.first_name
    if payload.last_name is not None:
        update_body["lastName"] = payload.last_name
    if payload.email is not None:
        update_body["email"] = payload.email
        update_body["username"] = payload.email

    if update_body:
        put_resp = await kcAdminPut(f"/users/{user_id}", json=update_body)
        if put_resp.status_code == 409:
            raise HTTPException(status_code=409, detail="User already exists with this email")
        if put_resp.status_code not in (200, 204):
            raise HTTPException(status_code=502, detail="Failed to update user in Keycloak")

    # Role delta: remove old tenant role, assign new one
    if payload.tenant_role is not None:
        existing_roles_resp = await kcAdminGet(f"/users/{user_id}/role-mappings/realm")
        existing_roles_resp.raise_for_status()
        existing = [
            {"id": r["id"], "name": r["name"]}
            for r in existing_roles_resp.json()
            if not _is_internal_role(r["name"])
        ]
        if existing:
            del_resp = await kcAdminDelete(
                f"/users/{user_id}/role-mappings/realm",
                json=existing,
            )
            if del_resp.status_code not in (200, 204):
                raise HTTPException(status_code=502, detail="Failed to remove old role in Keycloak")

        new_role = await _get_role_rep(payload.tenant_role)
        assign_resp = await kcAdminPost(
            f"/users/{user_id}/role-mappings/realm",
            json=[new_role],
        )
        if assign_resp.status_code not in (200, 204):
            raise HTTPException(status_code=502, detail="Failed to assign new role in Keycloak")

    await _write_event(
        db,
        keycloak_user_id=user_id,
        tenant_id=tenant_id,
        actor_sub=actor_sub,
        action="user.updated",
        context=payload.model_dump(exclude_none=True),
    )

    # Return refreshed user
    refreshed_resp = await kcAdminGet(f"/users/{user_id}")
    refreshed_resp.raise_for_status()
    user = _parse_user(refreshed_resp.json())
    if payload.tenant_role is not None:
        user.tenant_role = payload.tenant_role
    else:
        tenant_role, product_roles = await _get_user_roles(user_id)
        user.tenant_role = tenant_role
        user.product_roles = product_roles

    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=tenant_id,
        user_id=actor_sub,
        user_email=None,
        action_type=ActionType.UPDATE_USER,
        environment='production',
        target_type="USER",
        target_id=user_id,
        payload_before=payload_before,
        payload_after=user.model_dump(mode='json'),
    ))

    return user


async def set_enabled(
    user_id: str,
    enabled: bool,
    tenant_id: str,
    actor_sub: str,
    db: AsyncSession,
) -> None:
    """
    Enable or disable a Keycloak user. Validates tenant ownership first.
    Writes user.enabled or user.disabled audit event.
    """
    # Validate tenant ownership
    get_resp = await kcAdminGet(f"/users/{user_id}")
    if get_resp.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    get_resp.raise_for_status()
    kc_user = get_resp.json()
    attrs = kc_user.get("attributes") or {}
    current_tenant = (attrs.get("tenant_id") or [""])[0]
    if current_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="User does not belong to this tenant")

    put_resp = await kcAdminPut(f"/users/{user_id}", json={"enabled": enabled})
    if put_resp.status_code not in (200, 204):
        raise HTTPException(status_code=502, detail="Failed to update user enabled state in Keycloak")

    action = "user.enabled" if enabled else "user.disabled"
    await _write_event(
        db,
        keycloak_user_id=user_id,
        tenant_id=tenant_id,
        actor_sub=actor_sub,
        action=action,
    )

    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=tenant_id,
        user_id=actor_sub,
        user_email=None,
        action_type=ActionType.ENABLE_USER if enabled else ActionType.DISABLE_USER,
        environment='production',
        target_type="USER",
        target_id=user_id,
        payload_before={"enabled": not enabled},
        payload_after={"enabled": enabled},
    ))


async def reset_mfa(
    user_id: str,
    tenant_id: str,
    actor_sub: str,
    db: AsyncSession,
) -> None:
    """
    Delete all OTP and WebAuthn credentials for a user.
    Validates tenant ownership first. Writes user.mfa_reset audit event.
    """
    # Validate tenant ownership
    get_resp = await kcAdminGet(f"/users/{user_id}")
    if get_resp.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    get_resp.raise_for_status()
    kc_user = get_resp.json()
    attrs = kc_user.get("attributes") or {}
    current_tenant = (attrs.get("tenant_id") or [""])[0]
    if current_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="User does not belong to this tenant")

    # Fetch all credentials
    creds_resp = await kcAdminGet(f"/users/{user_id}/credentials")
    creds_resp.raise_for_status()
    credentials = creds_resp.json()

    mfa_types = {"otp", "webauthn-two-factor"}
    deleted_count = 0
    for cred in credentials:
        cred_type = cred.get("type", "")
        if cred_type in mfa_types:
            del_resp = await kcAdminDelete(f"/users/{user_id}/credentials/{cred['id']}")
            if del_resp.status_code in (200, 204):
                deleted_count += 1

    await _write_event(
        db,
        keycloak_user_id=user_id,
        tenant_id=tenant_id,
        actor_sub=actor_sub,
        action="user.mfa_reset",
        context={"deleted_credentials": deleted_count},
    )

    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=tenant_id,
        user_id=actor_sub,
        user_email=None,
        action_type=ActionType.RESET_MFA,
        environment='production',
        target_type="USER",
        target_id=user_id,
        payload_before=None,
        payload_after=None,  # MFA reset has no before/after config snapshot — action itself is the record
    ))


async def list_user_events(user_id: str, db: AsyncSession) -> list:
    """
    Return audit events for a given Keycloak user ID, newest first.
    Deserializes the context TEXT column back to dict.
    """
    result = await db.execute(
        select(UserEvent)
        .where(UserEvent.keycloak_user_id == user_id)
        .order_by(UserEvent.created_at.desc())
    )
    events = result.scalars().all()

    # Deserialize context TEXT → dict for the response schema
    output = []
    for e in events:
        ctx = None
        if e.context:
            try:
                ctx = json.loads(e.context)
            except (json.JSONDecodeError, TypeError):
                ctx = None
        output.append({
            "id": e.id,
            "keycloak_user_id": e.keycloak_user_id,
            "actor_sub": e.actor_sub,
            "action": e.action,
            "context": ctx,
            "created_at": e.created_at,
        })
    return output
