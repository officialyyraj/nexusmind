"""Webhook database models."""

import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin


class Webhook(Base, TimestampMixin):
    """Webhook model for event subscriptions."""

    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="custom", nullable=False)
    secret_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_key_expr: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_header: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivery_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    headers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    webhook_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    user = relationship("User", backref="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Webhook {self.name} ({self.source})>"

    def set_secret(self, secret: str) -> None:
        """Set the webhook secret (stores hashed)."""
        self.secret_hash = hashlib.sha256(secret.encode()).hexdigest()

    def verify_secret(self, secret: str) -> bool:
        """Verify a webhook secret."""
        if not self.secret_hash:
            return True  # No secret set means anything works
        return self.secret_hash == hashlib.sha256(secret.encode()).hexdigest()

    @staticmethod
    def generate_secret() -> str:
        """Generate a new webhook secret."""
        return f"whsec_{secrets.token_urlsafe(32)}"

    def to_dict(self) -> dict[str, Any]:
        """Convert webhook to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "name": self.name,
            "url": self.url,
            "source": self.source,
            "event_key_expr": self.event_key_expr,
            "signature_header": self.signature_header,
            "is_enabled": self.is_enabled,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "delivery_count": self.delivery_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookDelivery(Base, TimestampMixin):
    """Webhook delivery model for tracking delivery attempts."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    webhook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    response_status: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(default=1, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<WebhookDelivery {self.id} ({self.event_type})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert delivery to dictionary."""
        return {
            "id": str(self.id),
            "webhook_id": str(self.webhook_id),
            "event_type": self.event_type,
            "payload": self.payload,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "error": self.error,
            "attempt": self.attempt,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
