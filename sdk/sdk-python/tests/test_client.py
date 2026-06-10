"""
Unit tests for backoffice_sdk.client.FeatureFlagClient.

initialize() is the only async setup call (httpx bootstrap fetch -> cache).
evaluate() is synchronous, cache-only, DB-free.
evaluate_remote() is async, calls POST /sdk/evaluate via httpx.

initialize() also spawns a background WS reconnect task (Plan 10) — patch
backoffice_sdk.client.ws_reconnect_loop in all initialize()-calling tests so
no real network connection is attempted and no task is left dangling.
"""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from backoffice_sdk.client import FeatureFlagClient


async def _noop_ws_loop(*args, **kwargs):
    """Stand-in for ws_reconnect_loop that returns immediately."""
    return None


@pytest.fixture(autouse=True)
def _mock_ws_reconnect_loop():
    with patch("backoffice_sdk.client.ws_reconnect_loop", side_effect=_noop_ws_loop) as mock:
        yield mock


BOOTSTRAP_FIXTURE = {
    "my_flag": {
        "enabled": True,
        "rules": [
            {"attribute": "country", "operator": "equals", "value": "PE", "result": True},
        ],
        "segments": [],
        "default_val": False,
        "scope": "global",
    },
    "always_on": {
        "enabled": True,
        "rules": [],
        "segments": [],
        "default_val": True,
        "scope": "global",
    },
}


def make_client():
    return FeatureFlagClient(
        tenant_id="t1",
        product_id="p1",
        environment="qa",
        api_base_url="https://api.example.com",
        sdk_key="sdk_key_123",
    )


class TestInitialize:

    @pytest.mark.asyncio
    async def test_initialize_fetches_bootstrap_and_populates_cache(self):
        client = make_client()

        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            await client.initialize()

        assert client.cache == BOOTSTRAP_FIXTURE
        called_url = mock_get.call_args.args[0]
        assert called_url == "https://api.example.com/sdk/bootstrap"
        called_kwargs = mock_get.call_args.kwargs
        assert called_kwargs["params"] == {
            "tenant_id": "t1",
            "product_id": "p1",
            "environment": "qa",
        }
        assert called_kwargs["headers"] == {"Authorization": "Bearer sdk_key_123"}


class TestEvaluate:

    @pytest.mark.asyncio
    async def test_evaluate_after_initialize_returns_rule_result(self):
        client = make_client()

        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            await client.initialize()

        assert client.evaluate("my_flag", {"country": "PE"}) is True
        assert client.evaluate("my_flag", {"country": "US"}) is False
        assert client.evaluate("always_on", {}) is True

    def test_evaluate_unknown_flag_returns_false_no_network(self):
        client = make_client()
        # cache is empty - no initialize() called
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            result = client.evaluate("unknown_flag", {})
            mock_get.assert_not_called()
        assert result is False


class TestEvaluateRemote:

    @pytest.mark.asyncio
    async def test_evaluate_remote_posts_and_returns_result(self):
        client = make_client()

        mock_response = Mock()
        mock_response.json.return_value = {"flag_key": "my_flag", "result": True}
        mock_response.raise_for_status = Mock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.evaluate_remote("my_flag", {"country": "PE"})

        assert result is True
        called_url = mock_post.call_args.args[0]
        assert called_url == "https://api.example.com/sdk/evaluate"
        called_kwargs = mock_post.call_args.kwargs
        assert called_kwargs["json"] == {"flag_key": "my_flag", "user": {"country": "PE"}}
        assert called_kwargs["headers"] == {"Authorization": "Bearer sdk_key_123"}

    @pytest.mark.asyncio
    async def test_evaluate_remote_returns_false_result(self):
        client = make_client()

        mock_response = Mock()
        mock_response.json.return_value = {"flag_key": "my_flag", "result": False}
        mock_response.raise_for_status = Mock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.evaluate_remote("my_flag", {"country": "US"})

        assert result is False


class TestCacheHelpers:

    @pytest.mark.asyncio
    async def test_invalidate_removes_flag_from_cache(self):
        client = make_client()
        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            await client.initialize()

        client.invalidate("my_flag")
        assert client.evaluate("my_flag", {"country": "PE"}) is False

    def test_replace_cache_overwrites_entire_cache(self):
        client = make_client()
        new_cache = {"flag_a": {"enabled": True, "rules": [], "segments": [], "default_val": True, "scope": "global"}}
        client.replace_cache(new_cache)
        assert client.cache == new_cache
        assert client.evaluate("flag_a", {}) is True
