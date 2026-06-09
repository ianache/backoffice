"""In-process WebSocket connection manager. Maps tenant_id -> set[WebSocket].
Redis upgrade path: replace broadcast() body — public interface stays the same.
"""
import json
from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # tenant_id -> set of active WebSocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    def register(self, tenant_id: str, ws: WebSocket) -> None:
        self._connections[tenant_id].add(ws)

    def deregister(self, tenant_id: str, ws: WebSocket) -> None:
        self._connections[tenant_id].discard(ws)
        if not self._connections[tenant_id]:
            del self._connections[tenant_id]

    async def broadcast(self, tenant_id: str, message: dict) -> None:
        """Send JSON message to all connections for a tenant.
        Dead connections are removed silently. Never mutate set while iterating."""
        payload = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(tenant_id, set())):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.deregister(tenant_id, ws)
