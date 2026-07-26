"""Execution database models for persistent execution tracking."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin


class ExecutionState(str, Enum):
    """Execution lifecycle states."""
    
    QUEUED = "queued"           # Waiting to start
    STARTING = "starting"       # Initializing
    PLANNING = "planning"       # Planner agent running
    RESEARCHING = "researching" # Researcher agent running
    CODING = "coding"           # Coder agent running
    REVIEWING = "reviewing"      # Reviewer agent running
    TESTING = "testing"          # Tester agent running
    DOCUMENTING = "documenting"  # Documentation agent running
    COMPLETED = "completed"     # Successfully completed
    FAILED = "failed"           # Failed with error
    CANCELLED = "cancelled"     # Cancelled by user
    PAUSED = "paused"           # Paused for user input
    RESUMING = "resuming"       # Resuming from checkpoint


class Execution(Base, TimestampMixin):
    """Execution model for tracking agent workflow executions.
    
    This provides:
    - Persistent execution state (survives restarts)
    - Resumability (can resume from checkpoint)
    - Observability (timings, retries, failures)
    - Proper cancellation support
    """
    
    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Task details
    task: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_types: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # State tracking
    state: Mapped[str] = mapped_column(
        String(50),
        default=ExecutionState.QUEUED.value,
        nullable=False,
        index=True,
    )
    previous_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    state_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Current step tracking
    current_agent: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    current_step_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_steps: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Checkpoint for resumability
    checkpoint_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    last_checkpoint_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Result
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Retry tracking
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )
    last_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    retry_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    estimated_duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Agent timings
    agent_timings: Mapped[dict[str, dict[str, Any]]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    
    # Cancellation
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    cancelled_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Cleanup tracking
    cleanup_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Metadata
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Relationships
    session = relationship("Session", back_populates="executions")
    steps = relationship(
        "ExecutionStep",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="ExecutionStep.step_order",
    )
    logs = relationship(
        "ExecutionLog",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Execution {self.id} ({self.state})>"

    @property
    def duration_seconds(self) -> int | None:
        """Calculate execution duration in seconds."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return int((end - self.started_at).total_seconds())

    @property
    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.state in {
            ExecutionState.COMPLETED.value,
            ExecutionState.FAILED.value,
            ExecutionState.CANCELLED.value,
        }

    @property
    def is_running(self) -> bool:
        """Check if execution is actively running."""
        return self.state in {
            ExecutionState.STARTING.value,
            ExecutionState.PLANNING.value,
            ExecutionState.RESEARCHING.value,
            ExecutionState.CODING.value,
            ExecutionState.REVIEWING.value,
            ExecutionState.TESTING.value,
            ExecutionState.DOCUMENTING.value,
            ExecutionState.RESUMING.value,
        }

    @property
    def can_retry(self) -> bool:
        """Check if execution can be retried."""
        return (
            self.state == ExecutionState.FAILED.value
            and self.retry_count < self.max_retries
            and self.error is not None
            and not self._is_permanent_failure()
        )

    def _is_permanent_failure(self) -> bool:
        """Check if the error is a permanent failure that shouldn't be retried."""
        if self.error_details:
            error_type = self.error_details.get("type", "")
            # These error types should not be retried
            permanent_errors = {
                "validation_error",
                "invalid_input",
                "unauthorized",
                "forbidden",
                "not_found",
                "syntax_error",
                "parse_error",
            }
            if error_type in permanent_errors:
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert execution to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "workflow_id": self.workflow_id,
            "task": self.task,
            "state": self.state,
            "current_agent": self.current_agent,
            "progress": f"{self.current_step_index}/{self.total_steps}" if self.total_steps > 0 else "0/0",
            "retry_count": self.retry_count,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "is_cancelled": self.is_cancelled,
        }


class ExecutionStep(Base, TimestampMixin):
    """Individual step within an execution for granular tracking."""
    
    __tablename__ = "execution_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    step_id: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # Step state
    state: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Retry
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Result
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Output reference
    output_artifacts: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Checkpoint data
    checkpoint_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    execution = relationship("Execution", back_populates="steps")

    def __repr__(self) -> str:
        return f"<ExecutionStep {self.step_order}:{self.agent_type} ({self.state})>"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate step duration in seconds."""
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()


class ExecutionLog(Base, TimestampMixin):
    """Detailed log for execution observability."""
    
    __tablename__ = "execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("execution_steps.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Log entry
    level: Mapped[str] = mapped_column(
        String(20),
        default="INFO",
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Context
    agent_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    action: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # For streaming
    is_streamed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    execution = relationship("Execution", back_populates="logs")
    step = relationship("ExecutionStep", backref="logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog {self.level}:{self.message[:50]}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert log to dictionary for streaming."""
        return {
            "id": str(self.id),
            "execution_id": str(self.execution_id),
            "step_id": str(self.step_id) if self.step_id else None,
            "level": self.level,
            "message": self.message,
            "details": self.details,
            "agent_type": self.agent_type,
            "action": self.action,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }
