"""
FeatureFlagClient — async feature flag client for backoffice_sdk.

initialize() is the only async setup call (httpx bootstrap fetch -> in-memory cache).
evaluate() is synchronous, cache-only, DB-free (<1ms, no network).
evaluate_remote() is async — fallback that calls POST /sdk/evaluate via httpx.

initialize() also spawns a background asyncio.Task running ws_reconnect_loop,
which keeps the cache in sync with backend flag changes via WebSocket push.
close() (or the async context manager) cancels that task cleanly.
"""
import asyncio
from typing import Any

import httpx

from .evaluator import evaluate_flag
from .websocket import ws_reconnect_loop


class FeatureFlagClient:
    """Async feature flag client.

    initialize() is the only async setup call; evaluate() is synchronous
    (cache-only, <1ms); evaluate_remote() is async (fallback).
    """

    def __init__(
        self,
        tenant_id: str,
        product_id: str,
        environment: str,
        api_base_url: str,
        sdk_key: str,
        ws_base_url: str | None = None,
    ):
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.environment = environment
        self.api_base_url = api_base_url.rstrip('/')
        self.sdk_key = sdk_key
        self.cache: dict[str, Any] = {}
        self.ws_base_url = (ws_base_url or self.api_base_url).replace('https://', 'wss://').replace('http://', 'ws://')
        self._ws_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Fetch the bootstrap payload, populate the in-memory cache, and
        spawn the background WebSocket reconnect loop for live sync."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.api_base_url}/sdk/bootstrap",
                params={
                    "tenant_id": self.tenant_id,
                    "product_id": self.product_id,
                    "environment": self.environment,
                },
                headers={"Authorization": f"Bearer {self.sdk_key}"},
            )
            resp.raise_for_status()
            self.cache = resp.json()

        ws_url = f"{self.ws_base_url}/sdk/ws/flags/{self.tenant_id}"
        self._ws_task = asyncio.create_task(
            ws_reconnect_loop(ws_url, self.sdk_key, on_message=self._handle_ws_message)
        )

    def evaluate(self, flag_key: str, user: dict) -> bool:
        """Synchronous, cache-only flag evaluation. Returns False on cache-miss."""
        entry = self.cache.get(flag_key)
        if entry is None:
            return False
        return evaluate_flag(entry, user)

    async def evaluate_remote(self, flag_key: str, user: dict) -> bool:
        """Async fallback — evaluate a flag server-side via POST /sdk/evaluate."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_base_url}/sdk/evaluate",
                json={"flag_key": flag_key, "user": user},
                headers={"Authorization": f"Bearer {self.sdk_key}"},
            )
            resp.raise_for_status()
            return bool(resp.json()["result"])

    def invalidate(self, flag_key: str) -> None:
        """Remove a single flag entry from the cache."""
        self.cache.pop(flag_key, None)

    def replace_cache(self, new_cache: dict) -> None:
        """Replace the entire cache (e.g. on WS update push)."""
        self.cache = new_cache

    def _handle_ws_message(self, msg: dict) -> None:
        """Dispatch a parsed WS message. flag_updated invalidates the cache
        entry; ping (and any other unrecognized type) is a no-op."""
        if msg.get('type') == 'flag_updated':
            flag_key = msg.get('flag_key')
            if flag_key:
                self.invalidate(flag_key)

    async def close(self) -> None:
        """Cancel the background WS reconnect task and await its completion.
        Idempotent — safe to call multiple times."""
        if self._ws_task is not None and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._ws_task = None

    async def __aenter__(self) -> "FeatureFlagClient":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
