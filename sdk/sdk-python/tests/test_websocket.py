"""
Unit tests for backoffice_sdk.websocket — reconnecting WS loop.

compute_backoff_delay() matches min(30, 2^attempt) + jitter.
ws_reconnect_loop() performs first-message auth, dispatches messages to
on_message, reconnects with exponential backoff on disconnect, and is
cleanly cancellable.
"""
import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from websockets.exceptions import ConnectionClosed

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
