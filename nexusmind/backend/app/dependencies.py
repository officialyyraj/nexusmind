"""Dependency injection for NexusMind."""

from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.database import async_session_maker, get_db_session
from app.utils.security import decode_access_token

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in async_session_maker():
        yield session


# Type alias for database session
DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> str | None:
    """Get current user ID from JWT token."""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None

    return payload.get("sub")


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> str:
    """Require authentication and return user ID."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


# Type alias for authenticated user ID
CurrentUser = Annotated[str, Depends(require_auth)]
OptionalUser = Annotated[str | None, Depends(get_current_user_id)]


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
