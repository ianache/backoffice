"""
Unit tests for backoffice_sdk.websocket — reconnecting WS loop.

compute_backoff_delay() matches min(30, 2^attempt) + jitter.
ws_reconnect_loop() performs first-message auth, dispatches messages to
on_message, reconnects with exponential backoff on disconnect, and is
cleanly cancellable.
"""
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from websockets.exceptions import ConnectionClosed

from backoffice_sdk.client import FeatureFlagClient
from backoffice_sdk.websocket import compute_backoff_delay, ws_reconnect_loop


class TestComputeBackoffDelay:

    def test_attempt_0_in_range_1_to_2(self):
        delay = compute_backoff_delay(0)
        assert 1.0 <= delay < 2.0

    def test_attempt_5_in_range_30_to_31(self):
        delay = compute_backoff_delay(5)
        assert 30.0 <= delay < 31.0

    def test_attempt_10_capped_at_30_to_31(self):
        delay = compute_backoff_delay(10)
        assert 30.0 <= delay < 31.0


class FakeWebSocket:
    """Fake websocket connection: records sent frames, yields queued messages,
    then raises ConnectionClosed (or a custom exception) when exhausted."""

    def __init__(self, messages=None, close_exc=None):
        self.sent: list[str] = []
        self._messages = list(messages or [])
        self._close_exc = close_exc if close_exc is not None else ConnectionClosed(None, None)

    async def send(self, data):
        self.sent.append(data)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._messages:
            return self._messages.pop(0)
        raise self._close_exc


class FakeConnect:
    """Fake async context manager mimicking websockets.connect(url)."""

    def __init__(self, ws=None, connect_exc=None):
        self._ws = ws
        self._connect_exc = connect_exc

    async def __aenter__(self):
        if self._connect_exc is not None:
            raise self._connect_exc
        return self._ws

    async def __aexit__(self, exc_type, exc, tb):
        return False


class TestWsReconnectLoopAuth:

    @pytest.mark.asyncio
    async def test_sends_sdk_key_as_first_frame(self):
        ws = FakeWebSocket(messages=[])
        stop_event = asyncio.Event()

        def fake_connect(url):
            stop_event.set()  # stop after first connect attempt
            return FakeConnect(ws=ws)

        on_message = lambda msg: None

        with patch("backoffice_sdk.websocket.websockets.connect", side_effect=fake_connect):
            await ws_reconnect_loop("ws://test/sdk/ws/flags/t1", "my_sdk_key", on_message, stop_event=stop_event)

        assert ws.sent == ["my_sdk_key"]


class TestWsReconnectLoopMessageDispatch:

    @pytest.mark.asyncio
    async def test_flag_updated_message_dispatched_before_reconnect(self):
        received = []
        ws = FakeWebSocket(messages=['{"type": "flag_updated", "flag_key": "my_flag"}'])
        stop_event = asyncio.Event()

        call_count = {"n": 0}

        def fake_connect(url):
            call_count["n"] += 1
            if call_count["n"] >= 1:
                stop_event.set()
            return FakeConnect(ws=ws)

        def on_message(msg):
            received.append(msg)

        with patch("backoffice_sdk.websocket.websockets.connect", side_effect=fake_connect):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await ws_reconnect_loop("ws://test/sdk/ws/flags/t1", "sdk_key", on_message, stop_event=stop_event)

        assert received == [{"type": "flag_updated", "flag_key": "my_flag"}]

    @pytest.mark.asyncio
    async def test_ping_message_dispatched_without_special_handling(self):
        received = []
        ws = FakeWebSocket(messages=['{"type": "ping"}'])
        stop_event = asyncio.Event()

        def fake_connect(url):
            stop_event.set()  # stop after first connect attempt's exhaustion
            return FakeConnect(ws=ws)

        def on_message(msg):
            received.append(msg)

        with patch("backoffice_sdk.websocket.websockets.connect", side_effect=fake_connect):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await ws_reconnect_loop("ws://test/sdk/ws/flags/t1", "sdk_key", on_message, stop_event=stop_event)

        assert received == [{"type": "ping"}]


class TestWsReconnectLoopBackoff:

    @pytest.mark.asyncio
    async def test_increasing_backoff_and_attempt_reset_on_success(self):
        # First two connect attempts fail immediately (ConnectionClosed on __aenter__),
        # third succeeds and exhausts immediately (no messages), then we stop.
        attempts = {"n": 0}
        ws_success = FakeWebSocket(messages=[])

        def fake_connect(url):
            attempts["n"] += 1
            if attempts["n"] <= 2:
                return FakeConnect(connect_exc=ConnectionClosed(None, None))
            return FakeConnect(ws=ws_success)

        on_message = lambda msg: None

        sleep_calls = []

        async def fake_sleep(delay):
            sleep_calls.append(delay)
            if len(sleep_calls) >= 2:
                # Stop the loop after capturing both backoff sleeps for attempts 0 and 1
                raise asyncio.CancelledError()

        with patch("backoffice_sdk.websocket.websockets.connect", side_effect=fake_connect):
            with patch("asyncio.sleep", side_effect=fake_sleep):
                with pytest.raises(asyncio.CancelledError):
                    await ws_reconnect_loop("ws://test/sdk/ws/flags/t1", "sdk_key", on_message)

        assert len(sleep_calls) == 2
        # attempt 0 -> [1.0, 2.0)
        assert 1.0 <= sleep_calls[0] < 2.0
        # attempt 1 -> [2.0, 3.0)
        assert 2.0 <= sleep_calls[1] < 3.0


class TestWsReconnectLoopCancellation:

    @pytest.mark.asyncio
    async def test_loop_is_cleanly_cancellable(self):
        ws = FakeWebSocket(messages=[])

        def fake_connect(url):
            return FakeConnect(ws=ws)

        on_message = lambda msg: None

        real_sleep = asyncio.sleep

        async def fake_sleep(delay):
            await real_sleep(0)  # yield control, allow cancellation

        with patch("backoffice_sdk.websocket.websockets.connect", side_effect=fake_connect):
            with patch("asyncio.sleep", side_effect=fake_sleep):
                task = asyncio.create_task(
                    ws_reconnect_loop("ws://test/sdk/ws/flags/t1", "sdk_key", on_message)
                )
                await asyncio.sleep(0)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task

        assert task.cancelled()


def make_client(**overrides):
    kwargs = dict(
        tenant_id="t1",
        product_id="p1",
        environment="qa",
        api_base_url="https://api.example.com",
        sdk_key="sdk_key_123",
    )
    kwargs.update(overrides)
    return FeatureFlagClient(**kwargs)


BOOTSTRAP_FIXTURE = {
    "my_flag": {
        "enabled": True,
        "rules": [],
        "segments": [],
        "default_val": False,
        "scope": "global",
    },
}


async def _mock_initialize_http(client):
    """Patch httpx.AsyncClient.get to return BOOTSTRAP_FIXTURE for initialize()."""
    mock_response = Mock()
    mock_response.json.return_value = BOOTSTRAP_FIXTURE
    mock_response.raise_for_status = Mock()
    return mock_response


class TestWsBaseUrlDerivation:

    def test_derives_ws_from_http(self):
        client = make_client(api_base_url="http://localhost:4000")
        assert client.ws_base_url == "ws://localhost:4000"

    def test_derives_wss_from_https(self):
        client = make_client(api_base_url="https://api.example.com")
        assert client.ws_base_url == "wss://api.example.com"

    def test_explicit_ws_base_url_overrides_default(self):
        client = make_client(api_base_url="https://api.example.com", ws_base_url="wss://override.example.com")
        assert client.ws_base_url == "wss://override.example.com"


class TestInitializeSpawnsWsTask:

    @pytest.mark.asyncio
    async def test_initialize_spawns_ws_reconnect_task(self):
        client = make_client(api_base_url="http://localhost:4000")

        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()

        async def fake_ws_loop(*args, **kwargs):
            return None

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            with patch("backoffice_sdk.client.ws_reconnect_loop", side_effect=fake_ws_loop) as mock_loop:
                await client.initialize()

        assert client._ws_task is not None
        await client.close()

        # Verify the URL/sdk_key/on_message args passed to ws_reconnect_loop
        call_args = mock_loop.call_args
        assert call_args.args[0] == "ws://localhost:4000/sdk/ws/flags/t1"
        assert call_args.args[1] == "sdk_key_123"
        assert call_args.kwargs["on_message"] == client._handle_ws_message


class TestHandleWsMessage:

    def test_flag_updated_invalidates_cache(self):
        client = make_client()
        client.cache = {"my_flag": {"enabled": True}}

        client._handle_ws_message({"type": "flag_updated", "flag_key": "my_flag"})

        assert "my_flag" not in client.cache

    def test_ping_is_noop(self):
        client = make_client()
        client.cache = {"my_flag": {"enabled": True}}

        client._handle_ws_message({"type": "ping"})

        assert client.cache == {"my_flag": {"enabled": True}}


class TestClose:

    @pytest.mark.asyncio
    async def test_close_cancels_ws_task(self):
        client = make_client(api_base_url="http://localhost:4000")

        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()

        async def slow_ws_loop(*args, **kwargs):
            await asyncio.sleep(100)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            with patch("backoffice_sdk.client.ws_reconnect_loop", side_effect=slow_ws_loop):
                await client.initialize()

        await client.close()
        assert client._ws_task is None

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self):
        client = make_client(api_base_url="http://localhost:4000")

        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()

        async def slow_ws_loop(*args, **kwargs):
            await asyncio.sleep(100)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            with patch("backoffice_sdk.client.ws_reconnect_loop", side_effect=slow_ws_loop):
                await client.initialize()

        await client.close()
        await client.close()  # second call must not raise


class TestAsyncContextManager:

    @pytest.mark.asyncio
    async def test_async_with_calls_initialize_and_close(self):
        client = make_client(api_base_url="http://localhost:4000")

        mock_response = Mock()
        mock_response.json.return_value = BOOTSTRAP_FIXTURE
        mock_response.raise_for_status = Mock()

        async def slow_ws_loop(*args, **kwargs):
            await asyncio.sleep(100)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            with patch("backoffice_sdk.client.ws_reconnect_loop", side_effect=slow_ws_loop):
                async with client as c:
                    assert c is client
                    assert client.cache == BOOTSTRAP_FIXTURE
                    assert client._ws_task is not None

        # __aexit__ should have closed the task
        assert client._ws_task is None
