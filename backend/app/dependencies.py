from typing import AsyncGenerator
import hmac
from fastapi import Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionFactory
from .config import settings

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session

async def verify_internal_secret(x_internal_secret: str | None = Header(default=None)) -> None:
    if not x_internal_secret or not hmac.compare_digest(x_internal_secret, settings.internal_secret):
        raise HTTPException(status_code=403, detail="Forbidden")


async def verify_sdk_secret(
    authorization: str | None = Header(default=None),
    sdk_key: str | None = Query(default=None),
) -> None:
    """SDK Bearer token auth. Uses hmac.compare_digest for timing-safe comparison.

    Accepts either an `Authorization: Bearer <key>` header (existing routes,
    takes precedence if present) or an `?sdk_key=<key>` query param fallback
    (for navigator.sendBeacon(), which cannot send custom headers).
    """
    if authorization is not None:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing SDK authorization")
        token = authorization.removeprefix("Bearer ").strip()
        if not hmac.compare_digest(token, settings.sdk_secret_key):
            raise HTTPException(status_code=401, detail="Invalid SDK key")
        return
    if sdk_key is not None:
        if not hmac.compare_digest(sdk_key, settings.sdk_secret_key):
            raise HTTPException(status_code=401, detail="Invalid SDK key")
        return
    raise HTTPException(status_code=401, detail="Missing SDK authorization")
