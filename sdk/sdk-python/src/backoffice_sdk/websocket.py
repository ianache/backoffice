"""
Reconnecting WebSocket loop for backoffice_sdk live flag sync.

Connects to {ws_base_url}/sdk/ws/flags/{tenant_id}, performs first-message
auth (sends the raw sdk_key as the first text frame, matching
backend/app/domains/sdk/ws_router.py's protocol), and dispatches each
subsequent JSON message to an on_message callback. On disconnect, reconnects
with exponential backoff + jitter, capped at 30s, resetting the attempt
counter on successful connect.
"""
import asyncio
import json
import logging
import random
from typing import Callable

import websockets

logger = logging.getLogger(__name__)

BASE_DELAY = 1.0
MAX_DELAY = 30.0


def compute_backoff_delay(attempt: int) -> float:
    """Exponential backoff with jitter: min(30, 1 * 2^attempt) + random[0,1).
    Mirrors sdk-js ReconnectingSocket (Plan 08) and STATE.md v1.1 decision.
    """
    exp = min(MAX_DELAY, BASE_DELAY * (2 ** attempt))
    return exp + random.random()


async def ws_reconnect_loop(
    url: str,
    sdk_key: str,
    on_message: Callable[[dict], None],
    stop_event: "asyncio.Event | None" = None,
) -> None:
    """Connect to `url`, send `sdk_key` as the first text frame (first-message auth),
    then dispatch each subsequent JSON message to `on_message`. On disconnect,
    reconnect with exponential backoff + jitter; reset the attempt counter after
    a successful connection. Runs until cancelled or `stop_event` is set.
    """
    attempt = 0
    while stop_event is None or not stop_event.is_set():
        try:
            async with websockets.connect(url) as ws:
                await ws.send(sdk_key)
                attempt = 0  # reset on successful connect (post first-message send)
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except (TypeError, ValueError):
                        continue
                    on_message(msg)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("SDK websocket disconnected: %s", exc)

        if stop_event is not None and stop_event.is_set():
            break

        delay = compute_backoff_delay(attempt)
        attempt += 1
        await asyncio.sleep(delay)
