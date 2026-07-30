"""Security API endpoints for audit logs and security management."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import AdminUser, DbSession
from app.security.audit import ACTION_SEVERITY, AuditAction, AuditLevel, AuditLog, AuditService
from app.security.rbac import RBACService, Permission, Role


router = APIRouter()


# Response models
class AuditLogResponse(BaseModel):
    """Audit log response model."""

    id: str
    timestamp: datetime
    action: str
    level: str
    user_id: str | None
    ip_address: str | None
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any]
    status: str
    error_message: str | None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Audit log list response."""

    logs: list[AuditLogResponse]
    total: int


class SecurityEventResponse(BaseModel):
    """Security event summary."""

    event_type: str
    count: int
    last_occurrence: datetime | None


class SecurityDashboardResponse(BaseModel):
    """Security dashboard data."""

    failed_logins: int
    api_key_usage: int
    permission_changes: int
    security_events: int
    recent_events: list[AuditLogResponse]


class RoleAssignmentRequest(BaseModel):
    """Request to assign a role to a user."""

    user_id: str
    role: str
    is_global: bool = True


class PermissionGrantRequest(BaseModel):
    """Request to grant a permission to a user."""

    user_id: str
    permission: str
    granted: bool = True


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    user: AdminUser,
    db: DbSession,
    action: str | None = Query(None, description="Filter by action"),
    user_id_filter: str | None = Query(None, alias="userId", description="Filter by user ID"),
    project_id: str | None = Query(None, description="Filter by project ID"),
    start_time: datetime | None = Query(None, description="Start time filter"),
    end_time: datetime | None = Query(None, description="End time filter"),
    level: str | None = Query(None, description="Filter by severity level"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> dict[str, Any]:
    """
    Get audit logs with filtering and pagination.
    
    Requires authentication. Admins can see all logs, users can only see their own.
    """
    audit_service = AuditService(db)

    # Parse filters
    audit_action = None
    if action:
        try:
            audit_action = AuditAction(action)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}",
            )

    user_uuid = uuid.UUID(user_id) if user_id_filter else None
    project_uuid = uuid.UUID(project_id) if project_id else None

    # Get logs
    logs = await audit_service.get_logs(
        user_id=user_uuid,
        action=audit_action,
        project_id=project_uuid,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    return {
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp,
                "action": log.action,
                "level": log.level,
                "user_id": str(log.user_id) if log.user_id else None,
                "ip_address": log.ip_address,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details,
                "status": log.status,
                "error_message": log.error_message,
            }
            for log in logs
        ],
        "total": len(logs),  # In production, this would be a separate count query
    }


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get a specific audit log entry."""
    from sqlalchemy import select

    result = await db.execute(select(AuditLog).where(AuditLog.id == uuid.UUID(log_id)))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return {
        "id": str(log.id),
        "timestamp": log.timestamp,
        "action": log.action,
        "level": log.level,
        "user_id": str(log.user_id) if log.user_id else None,
        "ip_address": log.ip_address,
        "resource_type": log.resource_type,
        "resource_id": str(log.resource_id) if log.resource_id else None,
        "details": log.details,
        "status": log.status,
        "error_message": log.error_message,
    }


@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get security dashboard data. Requires admin privileges."""
    audit_service = AuditService(db)

    # Calculate time ranges
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Get various security metrics
    failed_logins = await audit_service.get_logs(
        action=AuditAction.LOGIN_FAILED,
        start_time=last_24h,
        limit=1000,
    )

    api_key_usage = await audit_service.get_logs(
        action=AuditAction.APIKEY_USE,
        start_time=last_24h,
        limit=1000,
    )

    permission_changes = await audit_service.get_logs(
        action=AuditAction.USER_ROLE_CHANGE,
        start_time=last_7d,
        limit=1000,
    )

    security_events = await audit_service.get_logs(
        start_time=last_24h,
        limit=1000,
    )
    security_events = [
        e for e in security_events
        if e.level in [AuditLevel.WARNING.value, AuditLevel.ERROR.value, AuditLevel.CRITICAL.value]
    ]

    # Get recent events
    recent = await audit_service.get_logs(
        start_time=last_24h,
        limit=10,
    )

    return {
        "failed_logins": len(failed_logins),
        "api_key_usage": len(api_key_usage),
        "permission_changes": len(permission_changes),
        "security_events": len(security_events),
        "recent_events": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp,
                "action": log.action,
                "level": log.level,
                "user_id": str(log.user_id) if log.user_id else None,
                "ip_address": log.ip_address,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details,
                "status": log.status,
                "error_message": log.error_message,
            }
            for log in recent
        ],
    }


@router.get("/events/failed-logins")
async def get_failed_logins(
    user: AdminUser,
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Get recent failed login attempts. Requires admin privileges."""
    audit_service = AuditService(db)

    logs = await audit_service.get_logs(
        action=AuditAction.LOGIN_FAILED,
        limit=limit,
    )

    return {
        "count": len(logs),
        "events": [
            {
                "timestamp": log.timestamp,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "error_message": log.error_message,
            }
            for log in logs
        ],
    }


@router.get("/events/api-key-usage")
async def get_api_key_usage(
    user: AdminUser,
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Get recent API key usage. Requires admin privileges."""
    audit_service = AuditService(db)

    logs = await audit_service.get_logs(
        action=AuditAction.APIKEY_USE,
        limit=limit,
    )

    return {
        "count": len(logs),
        "events": [
            {
                "timestamp": log.timestamp,
                "user_id": str(log.user_id) if log.user_id else None,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "ip_address": log.ip_address,
            }
            for log in logs
        ],
    }


@router.get("/events/permission-changes")
async def get_permission_changes(
    user: AdminUser,
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Get recent permission changes. Requires admin privileges."""
    audit_service = AuditService(db)

    logs = await audit_service.get_logs(
        action=AuditAction.USER_ROLE_CHANGE,
        limit=limit,
    )

    return {
        "count": len(logs),
        "events": [
            {
                "timestamp": log.timestamp,
                "user_id": str(log.user_id) if log.user_id else None,
                "target_user_id": log.details.get("target_user_id"),
                "old_role": log.details.get("old_role"),
                "new_role": log.details.get("new_role"),
            }
            for log in logs
        ],
    }


@router.post("/roles/assign")
async def assign_role(
    request: RoleAssignmentRequest,
    user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """Assign a role to a user. Requires admin privileges."""
    rbac = RBACService(db)

    try:
        role = Role(request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {request.role}",
        )

    user_role = await rbac.assign_role(
        uuid.UUID(request.user_id),
        role,
        request.is_global,
    )

    # Audit the action
    audit_service = AuditService(db)
    await audit_service.log_permission_change(
        admin_user_id=user.id,
        target_user_id=uuid.UUID(request.user_id),
        action=AuditAction.USER_ROLE_CHANGE,
        old_role=None,
        new_role=role.value,
    )

    return {
        "status": "success",
        "user_id": request.user_id,
        "role": role.value,
    }


@router.post("/permissions/grant")
async def grant_permission(
    request: PermissionGrantRequest,
    user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """Grant or revoke a permission for a user. Requires admin privileges."""
    rbac = RBACService(db)

    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {request.permission}",
        )

    if request.granted:
        await rbac.grant_permission(uuid.UUID(request.user_id), permission)
    else:
        await rbac.revoke_permission(uuid.UUID(request.user_id), permission)

    # Audit the action
    audit_service = AuditService(db)
    await audit_service.log(
        action=AuditAction.USER_PERMISSION_CHANGE,
        user_id=user.id,
        resource_type="user",
        resource_id=uuid.UUID(request.user_id),
        details={
            "permission": permission.value,
            "granted": request.granted,
        },
    )

    return {
        "status": "success",
        "user_id": request.user_id,
        "permission": permission.value,
        "granted": request.granted,
    }


@router.get("/roles/{user_id}")
async def get_user_roles(
    user_id: str,
    user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get all roles assigned to a user. Requires admin privileges."""
    rbac = RBACService(db)

    roles = await rbac.get_user_roles(uuid.UUID(user_id))

    return {
        "user_id": user_id,
        "roles": [role.value for role in roles],
    }


@router.get("/permissions/{user_id}")
async def get_user_permissions(
    user_id: str,
    user: AdminUser,
    db: DbSession,
    project_id: str | None = Query(None, description="Project-specific permissions"),
) -> dict[str, Any]:
    """Get all permissions for a user. Requires admin privileges."""
    rbac = RBACService(db)

    project_uuid = uuid.UUID(project_id) if project_id else None
    permissions = await rbac.get_user_permissions(uuid.UUID(user_id), project_uuid)

    return {
        "user_id": user_id,
        "project_id": project_id,
        "permissions": [perm.value for perm in permissions],
    }
