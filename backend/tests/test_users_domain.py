import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
import httpx
from app.domains.users.schemas import UserCreate, UserUpdate
from app.domains.users import service
from app.services.keycloak_admin import _safe_request

@pytest.mark.asyncio
async def test_safe_request_timeout():
    async def mock_timeout():
        raise httpx.TimeoutException("Timeout")
    with pytest.raises(HTTPException) as exc_info:
        await _safe_request(mock_timeout)
    assert exc_info.value.status_code == 504
    assert exc_info.value.detail == "Keycloak connection timed out"

@pytest.mark.asyncio
async def test_safe_request_connection_failure():
    async def mock_fail():
        raise httpx.RequestError("Connection failed")
    with pytest.raises(HTTPException) as exc_info:
        await _safe_request(mock_fail)
    assert exc_info.value.status_code == 502
    assert "Keycloak service communication failed" in exc_info.value.detail

@pytest.mark.asyncio
@patch("app.domains.users.service.kcAdminPost")
async def test_create_user_conflict(mock_post):
    # Mock Keycloak returning 409 Conflict
    mock_resp = AsyncMock()
    mock_resp.status_code = 409
    mock_resp.text = '{"errorMessage":"User exists with same email"}'
    mock_post.return_value = mock_resp

    payload = UserCreate(
        email="existing@backoffice.dev",
        first_name="Test",
        last_name="User",
        tenant_role="TenantAdmin"
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_user(payload, tenant_id="1", actor_sub="admin-sub", db=AsyncMock())
    
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User already exists with this email"

@pytest.mark.asyncio
@patch("app.domains.users.service.kcAdminGet")
@patch("app.domains.users.service.kcAdminPut")
async def test_update_user_conflict(mock_put, mock_get):
    # Mock current user retrieve
    mock_get_resp = AsyncMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json = lambda: {
        "id": "user-uuid",
        "username": "user@backoffice.dev",
        "email": "user@backoffice.dev",
        "attributes": {"tenant_id": ["1"]}
    }
    mock_get.return_value = mock_get_resp

    # Mock Keycloak returning 409 Conflict during update
    mock_put_resp = AsyncMock()
    mock_put_resp.status_code = 409
    mock_put_resp.text = '{"errorMessage":"User exists with same email"}'
    mock_put.return_value = mock_put_resp

    payload = UserUpdate(
        email="existing@backoffice.dev"
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_user("user-uuid", payload, tenant_id="1", actor_sub="admin-sub", db=AsyncMock())
    
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User already exists with this email"
