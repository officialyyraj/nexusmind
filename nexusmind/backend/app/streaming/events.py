"""Event types for streaming."""

from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Event types for real-time streaming."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"

    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_ERROR = "session_error"
    SESSION_STATUS_CHANGED = "session_status_changed"

    # Agent events
    AGENT_ACTIVATED = "agent_activated"
    AGENT_DEACTIVATED = "agent_deactivated"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    AGENT_STATUS_CHANGED = "agent_status_changed"

    # Message events
    MESSAGE_CREATED = "message_created"
    MESSAGE_UPDATED = "message_updated"

    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"

    # Terminal events
    TERMINAL_OUTPUT = "terminal_output"
    TERMINAL_ERROR = "terminal_error"
    TERMINAL_CLOSED = "terminal_closed"

    # Execution events
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_ERROR = "execution_error"

    # Streaming events
    LOG_ENTRY = "log_entry"
    STREAM_CHUNK = "stream_chunk"
    PROGRESS_UPDATE = "progress_update"
    HEARTBEAT = "heartbeat"

    # Task events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"

    # System events
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class StreamEvent:
    """Stream event with data payload."""

    def __init__(
        self,
        event_type: EventType,
        data: dict[str, Any],
        session_id: str | None = None,
        agent_id: str | None = None,
        timestamp: datetime | None = None,
    ):
        self.event_type = event_type
        self.data = data
        self.session_id = session_id
        self.agent_id = agent_id
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "type": self.event_type.value,
            "data": self.data,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat() + "Z",
        }


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RECEIVING = "receiving"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class LogLevel(str, Enum):
    """Log levels for streaming logs."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def create_log_event(
    session_id: str,
    message: str,
    level: LogLevel = LogLevel.INFO,
    agent_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> StreamEvent:
    """Create a log entry event."""
    return StreamEvent(
        event_type=EventType.LOG_ENTRY,
        data={
            "level": level.value,
            "message": message,
            "metadata": metadata or {},
        },
        session_id=session_id,
        agent_id=agent_id,
    )


def create_agent_status_event(
    session_id: str,
    agent_id: str,
    status: AgentStatus,
    message: str | None = None,
) -> StreamEvent:
    """Create an agent status change event."""
    return StreamEvent(
        event_type=EventType.AGENT_STATUS_CHANGED,
        data={
            "status": status.value,
            "message": message,
        },
        session_id=session_id,
        agent_id=agent_id,
    )


def create_message_event(
    session_id: str,
    message_id: str,
    role: str,
    content: str,
    agent_type: str | None = None,
) -> StreamEvent:
    """Create a message created event."""
    return StreamEvent(
        event_type=EventType.MESSAGE_CREATED,
        data={
            "id": message_id,
            "role": role,
            "content": content,
            "agent_type": agent_type,
        },
        session_id=session_id,
    )


def create_execution_event(
    session_id: str,
    execution_id: str,
    status: str,
    result: Any = None,
    error: str | None = None,
) -> StreamEvent:
    """Create an execution event."""
    event_type = {
        "started": EventType.EXECUTION_STARTED,
        "completed": EventType.EXECUTION_COMPLETED,
        "error": EventType.EXECUTION_ERROR,
    }.get(status, EventType.EXECUTION_PROGRESS)

    return StreamEvent(
        event_type=event_type,
        data={
            "execution_id": execution_id,
            "status": status,
            "result": result,
            "error": error,
        },
        session_id=session_id,
    )
