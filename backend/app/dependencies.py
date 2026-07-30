"""Dependency injection for NexusMind.

This module provides the canonical authentication and authorization dependencies.
All API routes should use these dependencies for consistency and security.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.database import async_session_maker
from app.db.session import User, Session
from app.utils.security import (
    decode_access_token,
    decode_access_token_strict,
    ExpiredTokenError,
    InvalidTokenError,
    MalformedTokenError,
)
from sqlalchemy import select

# HTTP Bearer security scheme - auto_error=True for required auth
# Use this dependency for endpoints that require authentication
bearer_security = HTTPBearer(auto_error=True)

# HTTP Bearer with auto_error=False for optional auth
optional_bearer_security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in async_session_maker():
        yield session


# Type alias for database session
DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer_security)]
) -> str | None:
    """
    Get current user ID from JWT token (optional).
    
    Returns None if no valid token is provided.
    This is for endpoints where authentication is optional.
    """
    if credentials is None:
        return None

    try:
        payload = decode_access_token_strict(credentials.credentials)
        return payload.get("sub")
    except (ExpiredTokenError, InvalidTokenError, MalformedTokenError):
        return None


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer_security)]
) -> User | None:
    """
    Get current User object from JWT token (optional).
    
    Returns None if no valid token is provided or user doesn't exist.
    """
    user_id = await get_current_user_id(credentials)
    if user_id is None:
        return None
    
    # Get database session
    async for db in async_session_maker():
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_security)],
) -> str:
    """
    Require authentication and return user ID.
    
    Raises HTTPException 401 if:
    - No credentials provided
    - Token is invalid
    - Token is expired
    - Token payload is malformed
    """
    try:
        payload = decode_access_token_strict(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )
        return user_id
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer error="token_expired"'},
        )
    except MalformedTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )


async def require_auth_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_security)],
    db: DbSession,
) -> User:
    """
    Require authentication and return the authenticated User object.
    
    Raises HTTPException 401 if not authenticated.
    Raises HTTPException 404 if user doesn't exist.
    """
    user_id = await require_auth(credentials)
    
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_security)],
    db: DbSession,
) -> User:
    """
    Require authentication with admin privileges.
    
    Raises HTTPException 401 if not authenticated.
    Raises HTTPException 403 if not an admin.
    """
    user = await require_auth_user(credentials, db)
    
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return user


# Type aliases for dependency injection
CurrentUser = Annotated[str, Depends(require_auth)]
CurrentUserOptional = Annotated[str | None, Depends(get_current_user_id)]
AuthenticatedUser = Annotated[User, Depends(require_auth_user)]
AdminUser = Annotated[User, Depends(require_admin)]


class RequestContext:
    """Request context with user information."""

    def __init__(self, request: Request, user_id: str | None = None):
        self.request = request
        self.user_id = user_id
        self.session_id: str | None = None
        self.correlation_id: str | None = None


async def get_request_context(
    request: Request,
    user_id: str | None = Depends(get_current_user_id),
) -> RequestContext:
    """Get request context with user information."""
    ctx = RequestContext(request, user_id)
    ctx.correlation_id = request.headers.get("X-Correlation-ID")
    return ctx


RequestCtx = Annotated[RequestContext, Depends(get_request_context)]
