"""
Keycloak Admin API service.

Provides a singleton admin token cache with 30-second refresh buffer,
and thin async helpers that inject the Authorization header automatically.

Usage:
    from app.services.keycloak_admin import kcAdminGet, kcAdminPost, ...
"""
import time
import httpx
from app.config import settings

_admin_token: str | None = None
_token_expiry: float = 0.0


async def _get_admin_token() -> str:
    """Return a valid admin access token, refreshing if within 30s of expiry."""
    global _admin_token, _token_expiry
    now = time.time()
    if _admin_token and _token_expiry - now > 30:
        return _admin_token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.keycloak_admin_client_id,
                "client_secret": settings.keycloak_admin_client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        _admin_token = data["access_token"]
        _token_expiry = now + data["expires_in"]
    return _admin_token


def _kc_base() -> str:
    return f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"


async def kcAdminGet(path: str, **kwargs) -> httpx.Response:
    token = await _get_admin_token()
    async with httpx.AsyncClient() as client:
        return await client.get(
            _kc_base() + path,
            headers={"Authorization": f"Bearer {token}"},
            **kwargs,
        )


async def kcAdminPost(path: str, **kwargs) -> httpx.Response:
    token = await _get_admin_token()
    async with httpx.AsyncClient() as client:
        return await client.post(
            _kc_base() + path,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            **kwargs,
        )


async def kcAdminPut(path: str, **kwargs) -> httpx.Response:
    token = await _get_admin_token()
    async with httpx.AsyncClient() as client:
        return await client.put(
            _kc_base() + path,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            **kwargs,
        )


async def kcAdminPatch(path: str, **kwargs) -> httpx.Response:
    token = await _get_admin_token()
    async with httpx.AsyncClient() as client:
        return await client.patch(
            _kc_base() + path,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            **kwargs,
        )


async def kcAdminDelete(path: str, **kwargs) -> httpx.Response:
    token = await _get_admin_token()
    async with httpx.AsyncClient() as client:
        return await client.delete(
            _kc_base() + path,
            headers={"Authorization": f"Bearer {token}"},
            **kwargs,
        )
