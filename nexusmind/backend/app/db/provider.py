"""BYOK Provider Connection database models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin


class VerificationStatus(str, Enum):
    """Provider verification status."""
    
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class AuditAction(str, Enum):
    """Audit log action types."""
    
    CONNECT = "connect"
    UPDATE = "update"
    DELETE = "delete"
    VERIFY = "verify"
    ENABLE = "enable"
    DISABLE = "disable"
    SET_DEFAULT = "set_default"
    USE = "use"


class UserProviderConnection(Base, TimestampMixin):
    """User's AI provider connection with encrypted API key.
    
    Each authenticated user can connect multiple providers.
    API keys are encrypted using AES-256-GCM with server master key.
    """
    
    __tablename__ = "user_provider_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", "nickname", name="uq_user_provider_nickname"),
        Index("idx_provider_user_id", "user_id"),
        Index("idx_provider_enabled", "user_id", "enabled"),
        Index("idx_provider_default", "user_id", "is_default"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Encrypted API key (AES-256-GCM encrypted)
    encrypted_api_key: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Provider configuration
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Additional configuration (JSON for provider-specific settings)
    metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Verification status
    last_verified: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verification_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    use_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="provider_connections")
    audit_logs = relationship(
        "ProviderAuditLog",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<UserProviderConnection {self.provider}:{self.nickname or 'default'}>"
    
    @property
    def masked_api_key(self) -> str:
        """Return masked API key for display."""
        return "••••••••"
    
    @property
    def is_verified(self) -> bool:
        """Check if provider is verified."""
        return self.verification_status == VerificationStatus.VERIFIED.value
    
    @property
    def days_since_verification(self) -> int | None:
        """Days since last verification."""
        if not self.last_verified:
            return None
        return (datetime.utcnow() - self.last_verified).days


class ProviderAuditLog(Base):
    """Audit log for provider connection changes.
    
    Tracks all modifications to provider connections for security.
    """
    
    __tablename__ = "provider_audit_log"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_connection", "connection_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_created", "created_at"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_provider_connections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="now()",
    )
    
    # Relationships
    user = relationship("User")
    connection = relationship("UserProviderConnection", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<ProviderAuditLog {self.action}:{self.provider}>"


# Update User model to include provider_connections relationship
# This is imported from session.py
