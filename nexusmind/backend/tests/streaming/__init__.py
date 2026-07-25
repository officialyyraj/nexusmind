"""Streaming tests module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestStreamingEvents:
    """Test streaming event types."""

    def test_event_type_enum(self) -> None:
        """Test EventType enum values."""
        from app.streaming.events import EventType

        assert EventType.TEXT.value == "text"
        assert EventType.TOOL_CALL.value == "tool_call"
        assert EventType.TOOL_RESULT.value == "tool_result"
        assert EventType.AGENT_STATE.value == "agent_state"
        assert EventType.ERROR.value == "error"
        assert EventType.DONE.value == "done"

    def test_agent_event_creation(self) -> None:
        """Test creating agent events."""
        from app.streaming.events import AgentEvent, EventType

        event = AgentEvent(
            type=EventType.TEXT,
            content="test message"
        )
        assert event.type == EventType.TEXT
        assert event.content == "test message"

    def test_session_event_creation(self) -> None:
        """Test creating session events."""
        from app.streaming.events import SessionEvent, EventType

        event = SessionEvent(
            type=EventType.AGENT_STATE,
            session_id="test-session"
        )
        assert event.session_id == "test-session"


class TestSSEManager:
    """Test Server-Sent Events manager."""

    def test_sse_manager_init(self) -> None:
        """Test SSE manager initialization."""
        from app.streaming.sse import SSEManager

        manager = SSEManager()
        assert manager is not None

    def test_sse_event_format(self) -> None:
        """Test SSE event formatting."""
        from app.streaming.sse import format_sse_event

        event = format_sse_event("test_event", {"data": "value"})
        assert "event: test_event" in event
        assert "data: {\"data\": \"value\"}" in event

    def test_sse_event_with_id(self) -> None:
        """Test SSE event with ID."""
        from app.streaming.sse import format_sse_event

        event = format_sse_event("test", {"msg": "hello"}, event_id=1)
        assert "id: 1" in event

    def test_sse_retry_format(self) -> None:
        """Test SSE retry formatting."""
        from app.streaming.sse import format_sse_retry

        retry = format_sse_retry(5000)
        assert "retry: 5000" in retry


class TestWSManager:
    """Test WebSocket manager."""

    @pytest.mark.asyncio
    async def test_ws_manager_init(self) -> None:
        """Test WebSocket manager initialization."""
        from app.streaming.ws_manager import WSManager

        manager = WSManager()
        assert manager is not None
        assert hasattr(manager, "connections")

    @pytest.mark.asyncio
    async def test_ws_send_message(self) -> None:
        """Test sending WebSocket message."""
        from app.streaming.ws_manager import WSManager

        manager = WSManager()
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.send_message(mock_ws, {"type": "test"})

    @pytest.mark.asyncio
    async def test_ws_broadcast(self) -> None:
        """Test broadcasting to connections."""
        from app.streaming.ws_manager import WSManager

        manager = WSManager()
        await manager.broadcast({"type": "test"})


class TestStreamingIntegration:
    """Integration tests for streaming."""

    def test_event_serialization(self) -> None:
        """Test event serialization."""
        from app.streaming.events import AgentEvent, EventType
        import json

        event = AgentEvent(
            type=EventType.TEXT,
            content="test",
            metadata={"key": "value"}
        )
        json_str = json.dumps(event.model_dump())
        assert "test" in json_str
