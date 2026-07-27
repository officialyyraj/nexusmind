"""Artifact and AgentLog database models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin


class Artifact(Base, TimestampMixin):
    """Artifact model for files created by agents."""

    __tablename__ = "artifacts"

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
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    session = relationship("Session", back_populates="artifacts")
    message = relationship("Message", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact {self.name}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert artifact to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Task(Base, TimestampMixin):
    """Task model for agent tasks."""

    __tablename__ = "tasks"

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
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    task_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    session = relationship("Session", back_populates="tasks")
    parent = relationship("Task", remote_side=[id], backref="subtasks")
    logs = relationship("AgentLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Task {self.id} ({self.agent_type})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "agent_type": self.agent_type,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentLog(Base, TimestampMixin):
    """Agent log model for tracking agent activities."""

    __tablename__ = "agent_logs"

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
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)

    # Relationships
    session = relationship("Session", back_populates="agent_logs")
    task = relationship("Task", back_populates="logs")

    def __repr__(self) -> str:
        return f"<AgentLog {self.agent_type}:{self.action}>"
