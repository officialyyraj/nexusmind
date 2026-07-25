"""Audit logging for tracking sensitive actions."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base, TimestampMixin


class AuditAction(str, Enum):
    """Actions that should be audited."""

    # Authentication
    LOGIN = "auth:login"
    LOGOUT = "auth:logout"
    LOGIN_FAILED = "auth:login_failed"
    PASSWORD_CHANGE = "auth:password_change"
    PASSWORD_RESET = "auth:password_reset"

    # User Management
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ROLE_CHANGE = "user:role_change"
    USER_PERMISSION_CHANGE = "user:permission_change"

    # Project
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_SHARE = "project:share"
    PROJECT_UNSHARE = "project:unshare"

    # Session
    SESSION_CREATE = "session:create"
    SESSION_START = "session:start"
    SESSION_STOP = "session:stop"
    SESSION_DELETE = "session:delete"

    # Agent
    AGENT_CREATE = "agent:create"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"

    # Docker
    DOCKER_CONTAINER_START = "docker:container_start"
    DOCKER_CONTAINER_STOP = "docker:container_stop"
    DOCKER_CONTAINER_DELETE = "docker:container_delete"
    DOCKER_IMAGE_PULL = "docker:image_pull"

    # Terminal
    TERMINAL_EXECUTE = "terminal:execute"
    TERMINAL_COMMAND = "terminal:command"

    # GitHub
    GITHUB_CONNECT = "github:connect"
    GITHUB_DISCONNECT = "github:disconnect"
    GITHUB_PUSH = "github:push"
    GITHUB_PULL = "github:pull"
    GITHUB_PR_CREATE = "github:pr_create"
    GITHUB_PR_MERGE = "github:pr_merge"

    # Memory
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    MEMORY_CLEAR = "memory:clear"

    # Plugin
    PLUGIN_INSTALL = "plugin:install"
    PLUGIN_UNINSTALL = "plugin:uninstall"
    PLUGIN_ENABLE = "plugin:enable"
    PLUGIN_DISABLE = "plugin:disable"

    # API Key
    APIKEY_CREATE = "apikey:create"
    APIKEY_REVOKE = "apikey:revoke"
    APIKEY_USE = "apikey:use"

    # MCP
    MCP_SERVER_START = "mcp:server_start"
    MCP_SERVER_STOP = "mcp:server_stop"
    MCP_TOOL_INVOKE = "mcp:tool_invoke"

    # Settings
    SETTINGS_CHANGE = "settings:change"
    SECURITY_CONFIG_CHANGE = "security:config_change"

    # Workspace
    WORKSPACE_CREATE = "workspace:create"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_SHARE = "workspace:share"
    WORKSPACE_PERMISSION_CHANGE = "workspace:permission_change"

    # Security
    SECURITY_EVENT = "security:event"
    RATE_LIMIT_EXCEEDED = "security:rate_limit_exceeded"
    CSRF_FAILURE = "security:csrf_failure"
    AUTH_FAILURE = "security:auth_failure"


class AuditLevel(str, Enum):
    """Severity levels for audit events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Map actions to severity levels
ACTION_SEVERITY: dict[AuditAction, AuditLevel] = {
    AuditAction.LOGIN: AuditLevel.INFO,
    AuditAction.LOGOUT: AuditLevel.INFO,
    AuditAction.LOGIN_FAILED: AuditLevel.WARNING,
    AuditAction.PASSWORD_CHANGE: AuditLevel.INFO,
    AuditAction.USER_CREATE: AuditLevel.INFO,
    AuditAction.USER_DELETE: AuditLevel.WARNING,
    AuditAction.USER_ROLE_CHANGE: AuditLevel.WARNING,
    AuditAction.PROJECT_DELETE: AuditLevel.WARNING,
    AuditAction.SESSION_DELETE: AuditLevel.INFO,
    AuditAction.DOCKER_CONTAINER_START: AuditLevel.INFO,
    AuditAction.DOCKER_CONTAINER_STOP: AuditLevel.INFO,
    AuditAction.DOCKER_CONTAINER_DELETE: AuditLevel.WARNING,
    AuditAction.TERMINAL_EXECUTE: AuditLevel.INFO,
    AuditAction.GITHUB_PUSH: AuditLevel.INFO,
    AuditAction.MEMORY_DELETE: AuditLevel.WARNING,
    AuditAction.PLUGIN_INSTALL: AuditLevel.INFO,
    AuditAction.PLUGIN_UNINSTALL: AuditLevel.WARNING,
    AuditAction.APIKEY_CREATE: AuditLevel.INFO,
    AuditAction.APIKEY_REVOKE: AuditLevel.WARNING,
    AuditAction.SETTINGS_CHANGE: AuditLevel.WARNING,
    AuditAction.SECURITY_CONFIG_CHANGE: AuditLevel.WARNING,
    AuditAction.RATE_LIMIT_EXCEEDED: AuditLevel.WARNING,
    AuditAction.CSRF_FAILURE: AuditLevel.WARNING,
    AuditAction.AUTH_FAILURE: AuditLevel.ERROR,
}


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking sensitive actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), default=AuditLevel.INFO.value, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    __table_args__ = (
        Index("ix_audit_logs_user_action", "user_id", "action"),
        Index("ix_audit_logs_timestamp_action", "timestamp", "action"),
        Index("ix_audit_logs_project_timestamp", "project_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} user={self.user_id} status={self.status}>"


class AuditService:
    """Service for audit logging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: AuditAction,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        status: str = "success",
        error_message: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Log an audit event."""
        level = ACTION_SEVERITY.get(action, AuditLevel.INFO).value

        audit_log = AuditLog(
            action=action.value,
            level=level,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            project_id=project_id,
            session_id=session_id,
            details=details or {},
            status=status,
            error_message=error_message,
            request_id=request_id,
        )
        self.db.add(audit_log)
        await self.db.flush()
        await self.db.refresh(audit_log)
        return audit_log

    async def log_login(
        self,
        user_id: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditLog:
        """Log a login attempt."""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        return await self.log(
            action=action,
            user_id=user_id if success else None,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failure",
            error_message=error_message,
        )

    async def log_api_key_use(
        self,
        api_key_id: uuid.UUID,
        user_id: uuid.UUID,
        action: AuditAction,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log API key usage."""
        return await self.log(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="api_key",
            resource_id=api_key_id,
            details=details,
        )

    async def log_permission_change(
        self,
        admin_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        action: AuditAction,
        old_role: str | None = None,
        new_role: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log permission or role changes."""
        return await self.log(
            action=action,
            user_id=admin_user_id,
            ip_address=ip_address,
            resource_type="user",
            resource_id=target_user_id,
            details={
                "old_role": old_role,
                "new_role": new_role,
                "target_user_id": str(target_user_id),
            },
        )

    async def log_docker_action(
        self,
        user_id: uuid.UUID,
        action: AuditAction,
        container_id: str | None = None,
        image: str | None = None,
        ip_address: str | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> AuditLog:
        """Log Docker-related actions."""
        return await self.log(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="docker_container" if container_id else "docker_image",
            resource_id=uuid.UUID(container_id) if container_id else None,
            details={
                "container_id": container_id,
                "image": image,
            },
            status=status,
            error_message=error_message,
        )

    async def log_terminal_execution(
        self,
        user_id: uuid.UUID,
        command: str,
        ip_address: str | None = None,
        session_id: uuid.UUID | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> AuditLog:
        """Log terminal command execution."""
        # Sanitize command to avoid logging sensitive data
        sanitized_command = self._sanitize_command(command)
        return await self.log(
            action=AuditAction.TERMINAL_EXECUTE,
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            details={
                "command": sanitized_command,
                "full_command": command[:500] if len(command) > 500 else command,
            },
            status=status,
            error_message=error_message,
        )

    async def log_github_action(
        self,
        user_id: uuid.UUID,
        action: AuditAction,
        repository: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
        ip_address: str | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> AuditLog:
        """Log GitHub-related actions."""
        return await self.log(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="github",
            details={
                "repository": repository,
                "branch": branch,
                "commit_sha": commit_sha,
            },
            status=status,
            error_message=error_message,
        )

    async def get_logs(
        self,
        user_id: uuid.UUID | None = None,
        action: AuditAction | None = None,
        project_id: uuid.UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query audit logs with filters."""
        from sqlalchemy import select, and_

        query = select(AuditLog)
        conditions = []

        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action.value)
        if project_id:
            conditions.append(AuditLog.project_id == project_id)
        if start_time:
            conditions.append(AuditLog.timestamp >= start_time)
        if end_time:
            conditions.append(AuditLog.timestamp <= end_time)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _sanitize_command(self, command: str) -> str:
        """Sanitize command to mask sensitive data."""
        import re

        # Mask potential API keys
        patterns = [
            (r'(api[_-]?key["\']?\s*[:=]\s*["\']?)[^"\'\s]+', r'\1***REDACTED***'),
            (r'(token["\']?\s*[:=]\s*["\']?)[^"\'\s]+', r'\1***REDACTED***'),
            (r'(secret["\']?\s*[:=]\s*["\']?)[^"\'\s]+', r'\1***REDACTED***'),
            (r'(password["\']?\s*[:=]\s*["\']?)[^"\'\s]+', r'\1***REDACTED***'),
        ]

        sanitized = command
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized


# Global service instance
_audit_service: AuditService | None = None


def get_audit_service(db: AsyncSession) -> AuditService:
    """Get audit service instance."""
    return AuditService(db)
