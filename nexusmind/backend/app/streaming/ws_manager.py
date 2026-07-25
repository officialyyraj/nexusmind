"""WebSocket connection manager."""

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.streaming.events import EventType, StreamEvent


class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""

    def __init__(self):
        # session_id -> list of connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        # connection -> session_id mapping
        self._connection_sessions: dict[int, str] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        connection_id = id(websocket)

        async with self._lock:
            self._connections[session_id].append(websocket)
            self._connection_sessions[connection_id] = session_id

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        connection_id = id(websocket)

        async with self._lock:
            session_id = self._connection_sessions.pop(connection_id, None)
            if session_id and session_id in self._connections:
                self._connections[session_id] = [
                    ws for ws in self._connections[session_id] if ws != websocket
                ]
                if not self._connections[session_id]:
                    del self._connections[session_id]

    async def send_to_session(
        self, session_id: str, message: dict[str, Any]
    ) -> None:
        """Send message to all connections in a session."""
        if session_id not in self._connections:
            return

        disconnected = []
        async with self._lock:
            connections = list(self._connections[session_id])

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def send_to_connection(
        self, websocket: WebSocket, message: dict[str, Any]
    ) -> None:
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)

    async def broadcast_event(self, event: StreamEvent) -> None:
        """Broadcast an event to all connections in the session."""
        if event.session_id:
            await self.send_to_session(event.session_id, event.to_dict())

    async def broadcast_log(
        self,
        session_id: str,
        message: str,
        level: str = "INFO",
        agent_id: str | None = None,
    ) -> None:
        """Broadcast a log entry to session connections."""
        await self.send_to_session(
            session_id,
            {
                "type": EventType.LOG_ENTRY.value,
                "data": {
                    "level": level,
                    "message": message,
                    "agent_id": agent_id,
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    def get_connection_count(self, session_id: str | None = None) -> int:
        """Get the number of active connections."""
        if session_id:
            return len(self._connections.get(session_id, []))
        return sum(len(conns) for conns in self._connections.values())

    def get_active_sessions(self) -> list[str]:
        """Get list of sessions with active connections."""
        return list(self._connections.keys())


# Global connection manager instance
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
