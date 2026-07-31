"""Dependency injection for NexusMind.

This module provides the canonical authentication and authorization dependencies.
All API routes should use these dependencies for consistency and security.
"""

import uuid
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.database import async_session_maker
from app.db.session import User, Session
from app.orchestration.executor import ProductionExecutor
from app.agents.reasoning_loop import ReasoningLoop
from app.agents.execution_engine import AgentToolInvoker
from app.memory.chromadb import ChromaMemoryService
from app.tools.registry import ToolRegistry, get_tool_registry
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.sandbox.docker import DockerSandbox
from app.tools.docker_sandbox_tool import DockerSandboxTool
from app.utils.security import (
    decode_access_token,
    decode_access_token_strict,
    ExpiredTokenError,
    InvalidTokenError,
    MalformedTokenError,
    RateLimiter,
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


@lru_cache()
def get_sandbox_manager(settings: AppSettings) -> DockerSandbox:
    """Get a cached SandboxManager instance."""
    return DockerSandbox(settings)


SandboxManager = Annotated[DockerSandbox, Depends(get_sandbox_manager)]


@lru_cache()
def get_docker_sandbox_tool(sandbox_manager: SandboxManager) -> DockerSandboxTool:
    """Get a cached DockerSandboxTool instance."""
    return DockerSandboxTool(sandbox=sandbox_manager)


DockerSandboxToolDep = Annotated[DockerSandboxTool, Depends(get_docker_sandbox_tool)]


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer_security)],
    settings: AppSettings,
) -> str | None:
    """
    Get current user ID from JWT token (optional).
    
    Returns None if no valid token is provided.
    This is for endpoints where authentication is optional.
    """
    if credentials is None:
        return None

    try:
        payload = decode_access_token_strict(credentials.credentials, settings)
        return payload.get("sub")
    except (ExpiredTokenError, InvalidTokenError, MalformedTokenError):
        return None


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer_security)],
    settings: AppSettings,
) -> User | None:
    """
    Get current User object from JWT token (optional).
    
    Returns None if no valid token is provided or user doesn't exist.
    """
    user_id = await get_current_user_id(credentials, settings)
    if user_id is None:
        return None
    
    # Get database session
    async for db in async_session_maker():
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_security)],
    settings: AppSettings,
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
        payload = decode_access_token_strict(credentials.credentials, settings)
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
    settings: AppSettings,
) -> User:
    """
    Require authentication and return the authenticated User object.
    
    Raises HTTPException 401 if not authenticated.
    Raises HTTPException 404 if user doesn't exist.
    """
    user_id = await require_auth(credentials, settings)
    
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
    settings: AppSettings,
) -> User:
    """
    Require authentication with admin privileges.
    
    Raises HTTPException 401 if not authenticated.
    Raises HTTPException 403 if not an admin.
    """
    user = await require_auth_user(credentials, db, settings)
    
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
    settings: AppSettings,
    user_id: str | None = Depends(get_current_user_id),
) -> RequestContext:
    """Get request context with user information."""
    ctx = RequestContext(request, user_id)
    ctx.correlation_id = request.headers.get("X-Correlation-ID")
    return ctx


RequestCtx = Annotated[RequestContext, Depends(get_request_context)]


@lru_cache()
def get_rate_limiter(settings: AppSettings) -> RateLimiter:
    """Get a cached rate limiter instance."""
    return RateLimiter(requests_per_minute=settings.rate_limit_per_minute)

RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


@lru_cache()
def get_memory_service() -> ChromaMemoryService:
    """Get a cached ChromaMemoryService instance."""
    return ChromaMemoryService()

MemoryService = Annotated[ChromaMemoryService, Depends(get_memory_service)]

@lru_cache()
def get_tool_registry_dep() -> ToolRegistry:
    """Get a cached ToolRegistry instance."""
    return get_tool_registry()

ToolsRegistryDep = Annotated[ToolRegistry, Depends(get_tool_registry_dep)]

@lru_cache()
def get_mcp_registry_dep() -> MCPRegistry:
    """Get a cached MCPRegistry instance."""
    return get_mcp_registry()

MCPRegistryDep = Annotated[MCPRegistry, Depends(get_mcp_registry_dep)]


@lru_cache()
def get_agent_tool_invoker(
    tool_registry: ToolsRegistryDep, mcp_registry: MCPRegistryDep
) -> AgentToolInvoker:
    """Get a cached AgentToolInvoker instance."""
    return AgentToolInvoker(tool_registry=tool_registry, mcp_registry=mcp_registry)

AgentToolInvokerDep = Annotated[AgentToolInvoker, Depends(get_agent_tool_invoker)]


@lru_cache()
def get_reasoning_loop(
    tool_invoker: AgentToolInvokerDep, memory_service: MemoryService
) -> ReasoningLoop:
    """Get a cached ReasoningLoop instance."""
    return ReasoningLoop(tool_invoker=tool_invoker, memory_service=memory_service)

ReasoningLoopDep = Annotated[ReasoningLoop, Depends(get_reasoning_loop)]


@lru_cache()
def get_production_executor(
    reasoning_loop: ReasoningLoopDep,
    tool_invoker: AgentToolInvokerDep,
    memory_service: MemoryService,
) -> ProductionExecutor:
    """Get a cached ProductionExecutor instance."""
    return ProductionExecutor(
        reasoning_loop=reasoning_loop,
        tool_invoker=tool_invoker,
        memory_service=memory_service,
    )

ProductionExecutorDep = Annotated[ProductionExecutor, Depends(get_production_executor)]

