from typing import AsyncGenerator
import hmac
from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionFactory
from .config import settings

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session

async def verify_internal_secret(x_internal_secret: str | None = Header(default=None)) -> None:
    if not x_internal_secret or not hmac.compare_digest(x_internal_secret, settings.internal_secret):
        raise HTTPException(status_code=403, detail="Forbidden")


async def verify_sdk_secret(authorization: str | None = Header(default=None)) -> None:
    """SDK Bearer token auth. Uses hmac.compare_digest for timing-safe comparison."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing SDK authorization")
    token = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, settings.sdk_secret_key):
        raise HTTPException(status_code=401, detail="Invalid SDK key")
