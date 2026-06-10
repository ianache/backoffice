"""
FeatureFlagClient — async feature flag client for backoffice_sdk.

initialize() is the only async setup call (httpx bootstrap fetch -> in-memory cache).
evaluate() is synchronous, cache-only, DB-free (<1ms, no network).
evaluate_remote() is async — fallback that calls POST /sdk/evaluate via httpx.
"""
from typing import Any

import httpx

from .evaluator import evaluate_flag


class FeatureFlagClient:
    """Async feature flag client.

    initialize() is the only async setup call; evaluate() is synchronous
    (cache-only, <1ms); evaluate_remote() is async (fallback).
    """

    def __init__(self, tenant_id: str, product_id: str, environment: str, api_base_url: str, sdk_key: str):
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.environment = environment
        self.api_base_url = api_base_url.rstrip('/')
        self.sdk_key = sdk_key
        self.cache: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Fetch the bootstrap payload and populate the in-memory cache."""
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
