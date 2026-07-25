"""Server-Sent Events (SSE) streaming."""

import asyncio
import json
from typing import Any, AsyncGenerator

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.streaming.events import EventType, StreamEvent
from app.streaming.ws_manager import get_connection_manager


async def sse_generator(
    session_id: str,
    request: Request,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for a session."""
    settings = get_settings()
    manager = get_connection_manager()

    # Send initial connected event
    yield f"event: {EventType.CONNECTED.value}\ndata: {json.dumps({'session_id': session_id})}\n\n"

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Send heartbeat
            yield f"event: {EventType.HEARTBEAT.value}\ndata: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"

            # Wait before next heartbeat
            await asyncio.sleep(settings.sse_heartbeat_seconds)

    except asyncio.CancelledError:
        pass
    finally:
        # Send disconnected event
        yield f"event: {EventType.DISCONNECTED.value}\ndata: {json.dumps({'session_id': session_id})}\n\n"


async def event_to_sse(event: StreamEvent) -> str:
    """Convert a StreamEvent to SSE format."""
    return f"event: {event.event_type.value}\ndata: {json.dumps(event.to_dict())}\n\n"


async def broadcast_to_sse(session_id: str, event: StreamEvent) -> None:
    """Broadcast event to all SSE clients for a session."""
    manager = get_connection_manager()
    # Note: SSE uses a different mechanism than WebSocket
    # This would integrate with the SSE connection tracking
    pass


class SSEManager:
    """Manager for SSE connections."""

    def __init__(self):
        self._connections: dict[str, set] = {}

    def add_connection(self, session_id: str) -> None:
        """Add an SSE connection."""
        if session_id not in self._connections:
            self._connections[session_id] = set()

    def remove_connection(self, session_id: str) -> None:
        """Remove an SSE connection."""
        if session_id in self._connections:
            del self._connections[session_id]

    def get_connection_count(self, session_id: str | None = None) -> int:
        """Get number of SSE connections."""
        if session_id:
            return len(self._connections.get(session_id, set()))
        return sum(len(conns) for conns in self._connections.values())
