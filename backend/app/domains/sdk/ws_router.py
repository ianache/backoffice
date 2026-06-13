"""WebSocket endpoint for real-time flag invalidation.

Auth pattern: first-message (NOT Depends()) — browser WebSocket API does not
support custom Authorization headers. Client sends SDK key as first text message.
Auth failure: send error JSON, close with code 4001.
"""
import asyncio
import hmac
import json
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


async def ws_flags_endpoint(websocket: WebSocket, tenant_id: str = None):
    if tenant_id is None:
        tenant_id = websocket.path_params.get("tenant_id")
    await websocket.accept()
    manager = websocket.app.state.ws_manager  # Accessed at request time, NOT at import time

    # First-message auth — 10 second window
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        token = raw.strip()
    except asyncio.TimeoutError:
        await websocket.send_text(json.dumps({
            "type": "error", "code": "auth_failed", "message": "auth timeout"
        }))
        await websocket.close(code=4001)
        return

    # Validate SDK key — constant-time comparison avoids timing attacks
    from app.config import settings
    if not hmac.compare_digest(token, settings.sdk_secret_key):
        await websocket.send_text(json.dumps({
            "type": "error", "code": "auth_failed", "message": "invalid credentials"
        }))
        await websocket.close(code=4001)
        return

    # Auth passed — register and maintain connection
    manager.register(tenant_id, websocket)
    try:
        while True:
            # Drain incoming frames; 30s timeout triggers heartbeat ping
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        manager.deregister(tenant_id, websocket)
