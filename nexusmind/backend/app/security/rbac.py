"""Role-Based Access Control (RBAC) system for NexusMind."""

import uuid
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Annotated, Any, Callable

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin


class Role(str, Enum):
    """User roles with decreasing privilege levels."""

    OWNER = "owner"  # Full access, can manage billing and delete organization
    ADMIN = "admin"  # Full access except billing
    DEVELOPER = "developer"  # Can manage projects, sessions, agents
    VIEWER = "viewer"  # Read-only access


class Permission(str, Enum):
    """Granular permissions for resource access."""

    # Projects
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    PROJECT_SHARE = "project:share"

    # Sessions
    SESSION_READ = "session:read"
    SESSION_WRITE = "session:write"
    SESSION_DELETE = "session:delete"

    # Agents
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_EXECUTE = "agent:execute"

    # Plugins
    PLUGIN_READ = "plugin:read"
    PLUGIN_WRITE = "plugin:write"
    PLUGIN_INSTALL = "plugin:install"
    PLUGIN_UNINSTALL = "plugin:uninstall"

    # Memory
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"

    # Docker
    DOCKER_READ = "docker:read"
    DOCKER_EXECUTE = "docker:execute"
    DOCKER_MANAGE = "docker:manage"

    # Terminal
    TERMINAL_READ = "terminal:read"
    TERMINAL_EXECUTE = "terminal:execute"

    # GitHub
    GITHUB_READ = "github:read"
    GITHUB_WRITE = "github:write"
    GITHUB_EXECUTE = "github:execute"

    # MCP
    MCP_READ = "mcp:read"
    MCP_WRITE = "mcp:write"
    MCP_EXECUTE = "mcp:execute"

    # Settings
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    SETTINGS_ADMIN = "settings:admin"

    # Users
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_MANAGE = "user:manage"

    # API Keys
    APIKEY_READ = "apikey:read"
    APIKEY_WRITE = "apikey:write"
    APIKEY_DELETE = "apikey:delete"

    # Workspace
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    WORKSPACE_SHARE = "workspace:share"
    WORKSPACE_ADMIN = "workspace:admin"


# Role hierarchy - which permissions each role has by default
ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.OWNER: [p for p in Permission],  # All permissions
    Role.ADMIN: [
        Permission.PROJECT_READ, Permission.PROJECT_WRITE, Permission.PROJECT_DELETE, Permission.PROJECT_SHARE,
        Permission.SESSION_READ, Permission.SESSION_WRITE, Permission.SESSION_DELETE,
        Permission.AGENT_READ, Permission.AGENT_WRITE, Permission.AGENT_EXECUTE,
        Permission.PLUGIN_READ, Permission.PLUGIN_WRITE, Permission.PLUGIN_INSTALL, Permission.PLUGIN_UNINSTALL,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE, Permission.MEMORY_DELETE,
        Permission.DOCKER_READ, Permission.DOCKER_EXECUTE, Permission.DOCKER_MANAGE,
        Permission.TERMINAL_READ, Permission.TERMINAL_EXECUTE,
        Permission.GITHUB_READ, Permission.GITHUB_WRITE, Permission.GITHUB_EXECUTE,
        Permission.MCP_READ, Permission.MCP_WRITE, Permission.MCP_EXECUTE,
        Permission.SETTINGS_READ, Permission.SETTINGS_WRITE,
        Permission.USER_READ, Permission.USER_WRITE,
        Permission.APIKEY_READ, Permission.APIKEY_WRITE, Permission.APIKEY_DELETE,
        Permission.WORKSPACE_READ, Permission.WORKSPACE_WRITE, Permission.WORKSPACE_SHARE,
    ],
    Role.DEVELOPER: [
        Permission.PROJECT_READ, Permission.PROJECT_WRITE,
        Permission.SESSION_READ, Permission.SESSION_WRITE, Permission.SESSION_DELETE,
        Permission.AGENT_READ, Permission.AGENT_WRITE, Permission.AGENT_EXECUTE,
        Permission.PLUGIN_READ,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE, Permission.MEMORY_DELETE,
        Permission.DOCKER_READ, Permission.DOCKER_EXECUTE,
        Permission.TERMINAL_READ, Permission.TERMINAL_EXECUTE,
        Permission.GITHUB_READ, Permission.GITHUB_WRITE,
        Permission.MCP_READ, Permission.MCP_EXECUTE,
        Permission.SETTINGS_READ,
        Permission.APIKEY_READ, Permission.APIKEY_WRITE, Permission.APIKEY_DELETE,
        Permission.WORKSPACE_READ, Permission.WORKSPACE_WRITE,
    ],
    Role.VIEWER: [
        Permission.PROJECT_READ,
        Permission.SESSION_READ,
        Permission.AGENT_READ,
        Permission.PLUGIN_READ,
        Permission.MEMORY_READ,
        Permission.DOCKER_READ,
        Permission.TERMINAL_READ,
        Permission.GITHUB_READ,
        Permission.MCP_READ,
        Permission.SETTINGS_READ,
        Permission.APIKEY_READ,
        Permission.WORKSPACE_READ,
    ],
}


class WorkspacePermission(str, Enum):
    """Workspace-level permissions."""

    PRIVATE = "private"  # Only owner can access
    SHARED = "shared"  # Shared with specific users
    READ_ONLY = "read_only"  # Shared users can only read
    READ_WRITE = "read_write"  # Shared users can read and write


class UserRole(Base, TimestampMixin):
    """User-role assignment for RBAC."""

    __tablename__ = "user_roles"

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
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role}>"


class UserPermission(Base, TimestampMixin):
    """User-specific permission overrides."""

    __tablename__ = "user_permissions"

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
    permission: Mapped[str] = mapped_column(String(100), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<UserPermission user={self.user_id} permission={self.permission} granted={self.granted}>"


class ProjectPermission(Base, TimestampMixin):
    """Project-level permissions."""

    __tablename__ = "project_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    workspace_permission: Mapped[str] = mapped_column(
        String(50),
        default=WorkspacePermission.READ_WRITE.value,
        nullable=False,
    )
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)

    def __repr__(self) -> str:
        return f"<ProjectPermission project={self.project_id} user={self.user_id} role={self.role}>"


class RBACService:
    """Service for managing RBAC."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_roles(self, user_id: uuid.UUID) -> list[Role]:
        """Get all roles assigned to a user."""
        result = await self.db.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        roles = []
        for user_role in result.scalars().all():
            try:
                roles.append(Role(user_role.role))
            except ValueError:
                continue
        return roles

    async def get_user_permissions(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
    ) -> set[Permission]:
        """Get all permissions for a user, considering roles and overrides."""
        permissions: set[Permission] = set()

        # Get global roles
        roles = await self.get_user_roles(user_id)

        # Add role-based permissions
        for role in roles:
            if user_id and role == Role.OWNER:
                permissions.update(ROLE_PERMISSIONS[Role.OWNER])
            else:
                permissions.update(ROLE_PERMISSIONS.get(role, set()))

        # Check for project-specific permissions
        if project_id:
            result = await self.db.execute(
                select(ProjectPermission).where(
                    ProjectPermission.project_id == project_id,
                    ProjectPermission.user_id == user_id,
                )
            )
            project_perm = result.scalar_one_or_none()
            if project_perm:
                # Project-specific permissions override global
                project_role = Role(project_perm.role)
                permissions = set(ROLE_PERMISSIONS[project_role])

                # Add any custom permissions
                for perm_str in project_perm.permissions:
                    try:
                        permissions.add(Permission(perm_str))
                    except ValueError:
                        continue

        # Get user-specific permission overrides
        result = await self.db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        for user_perm in result.scalars().all():
            try:
                perm = Permission(user_perm.permission)
                if user_perm.granted:
                    permissions.add(perm)
                else:
                    permissions.discard(perm)
            except ValueError:
                continue

        return permissions

    async def has_permission(
        self,
        user_id: uuid.UUID,
        permission: Permission,
        project_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if user has a specific permission."""
        permissions = await self.get_user_permissions(user_id, project_id)
        return permission in permissions

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role: Role,
        is_global: bool = True,
    ) -> UserRole:
        """Assign a role to a user."""
        user_role = UserRole(
            user_id=user_id,
            role=role.value,
            is_global=is_global,
        )
        self.db.add(user_role)
        await self.db.flush()
        await self.db.refresh(user_role)
        return user_role

    async def revoke_role(
        self,
        user_id: uuid.UUID,
        role: Role,
    ) -> bool:
        """Revoke a role from a user."""
        result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role == role.value,
            )
        )
        user_role = result.scalar_one_or_none()
        if user_role:
            await self.db.delete(user_role)
            await self.db.flush()
            return True
        return False

    async def grant_permission(
        self,
        user_id: uuid.UUID,
        permission: Permission,
    ) -> UserPermission:
        """Grant a specific permission to a user."""
        user_perm = UserPermission(
            user_id=user_id,
            permission=permission.value,
            granted=True,
        )
        self.db.add(user_perm)
        await self.db.flush()
        await self.db.refresh(user_perm)
        return user_perm

    async def revoke_permission(
        self,
        user_id: uuid.UUID,
        permission: Permission,
    ) -> bool:
        """Revoke a specific permission from a user."""
        result = await self.db.execute(
            select(UserPermission).where(
                UserPermission.user_id == user_id,
                UserPermission.permission == permission.value,
            )
        )
        user_perm = result.scalar_one_or_none()
        if user_perm:
            await self.db.delete(user_perm)
            await self.db.flush()
            return True
        return False


# Global service instance
_rbac_service: RBACService | None = None


def get_rbac_service(db: AsyncSession) -> RBACService:
    """Get RBAC service instance."""
    return RBACService(db)


def check_permission(permission: Permission) -> Callable:
    """Decorator to check if user has permission."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Permission check is handled by the dependency
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def require_permission(
    user_id: uuid.UUID,
    permission: Permission,
    db: AsyncSession,
    project_id: uuid.UUID | None = None,
) -> bool:
    """Require a permission, raise HTTPException if not granted."""
    rbac = RBACService(db)
    has_perm = await rbac.has_permission(user_id, permission, project_id)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}",
        )
    return True


class RequirePermission:
    """Dependency class for requiring permissions."""

    def __init__(
        self,
        permission: Permission,
        project_param: str | None = None,
    ):
        self.permission = permission
        self.project_param = project_param

    async def __call__(
        self,
        user_id: Annotated[str, Depends(lambda: None)],
        db: AsyncSession,
    ) -> bool:
        """Check permission."""
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        user_uuid = uuid.UUID(user_id)
        project_id = None

        # If project_param is specified, it should be extracted from request
        # This is a simplified version

        return await require_permission(
            user_uuid,
            self.permission,
            db,
            project_id,
        )
