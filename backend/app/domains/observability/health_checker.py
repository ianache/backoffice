import asyncio
import time
import httpx
from typing import Optional
from sqlalchemy import text
from fastapi import FastAPI
from app.database import AsyncSessionFactory
from app.config import settings
from app.domains.observability.service import write_sample, prune_old_samples

POLL_INTERVAL_SECONDS = 15
DEGRADED_THRESHOLD_MS = 100


def _classify(latency_ms: float) -> str:
    return "UP" if latency_ms < DEGRADED_THRESHOLD_MS else "DEGRADED"


async def _check_fastapi(app: FastAPI) -> tuple[str, float, Optional[str]]:
    start = time.monotonic()
    # Trivial self-check: process responsive
    latency_ms = (time.monotonic() - start) * 1000
    return _classify(latency_ms), latency_ms, None


async def _check_mysql(app: FastAPI) -> tuple[str, float, Optional[str]]:
    start = time.monotonic()
    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))
    latency_ms = (time.monotonic() - start) * 1000
    return _classify(latency_ms), latency_ms, None


async def _check_bff(app: FastAPI) -> tuple[str, float, Optional[str]]:
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{settings.bff_internal_url}/health")
        resp.raise_for_status()
    latency_ms = (time.monotonic() - start) * 1000
    return _classify(latency_ms), latency_ms, None


async def _check_keycloak(app: FastAPI) -> tuple[str, float, Optional[str]]:
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/.well-known/openid-configuration"
        )
        resp.raise_for_status()
    latency_ms = (time.monotonic() - start) * 1000
    return _classify(latency_ms), latency_ms, None


async def _check_ws_gateway(app: FastAPI) -> tuple[str, float, Optional[str]]:
    start = time.monotonic()
    manager = getattr(app.state, "ws_manager", None)
    if not manager:
        raise ValueError("ws_manager not initialized on app.state")
    
    # connections count
    active_connections = sum(len(s) for s in manager._connections.values())
    latency_ms = (time.monotonic() - start) * 1000
    return _classify(latency_ms), latency_ms, str(active_connections)


async def health_checker_loop(app: FastAPI) -> None:
    """Infinite loop for the Health Checker Engine. Runs every 15 seconds.
    Prunes old data (>30 days) every hour (~240 iterations)."""
    iteration = 0
    while True:
        for check in (_check_fastapi, _check_mysql, _check_bff, _check_keycloak, _check_ws_gateway):
            service_name = check.__name__.removeprefix("_check_")
            try:
                status, latency_ms, details = await check(app)
                async with AsyncSessionFactory() as session:
                    await write_sample(session, service_name, status, latency_ms, details)
            except Exception as e:
                # Store error details truncated to 500 chars per Threat Register T-17-02
                err_str = str(e)[:500]
                try:
                    async with AsyncSessionFactory() as session:
                        await write_sample(session, service_name, "DOWN", None, err_str)
                except Exception:
                    pass  # Fail-safe: DB failure must not abort loop (PRD §10.2)
        
        # Prune once per hour (~240 iterations)
        iteration += 1
        if iteration >= 240:
            iteration = 0
            try:
                async with AsyncSessionFactory() as session:
                    await prune_old_samples(session)
            except Exception:
                pass

        try:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            break
