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
