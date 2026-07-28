"""BYOK Provider API Endpoints.

REST API for managing user AI provider connections.
All endpoints require authentication and are scoped by user_id.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.dependencies import AuthenticatedUser, DbSession
from app.llm.byok.service import (
    DuplicateProviderError,
    ProviderLimitExceededError,
    ProviderNotFoundError,
    ProviderService,
)
from app.llm.byok.adapters import VerificationResult


router = APIRouter(prefix="/providers", tags=["providers"])


# ==================== REQUEST/RESPONSE SCHEMAS ====================

class ProviderConnectionCreate(BaseModel):
    """Request to create a provider connection."""
    
    provider: str = Field(..., description="Provider name (e.g., 'openai')")
    api_key: str = Field(..., description="API key (will be encrypted)")
    nickname: str | None = Field(None, description="Optional friendly name")
    base_url: str | None = Field(None, description="Custom API endpoint")
    default_model: str | None = Field(None, description="Default model")
    enabled: bool = Field(True, description="Enable immediately")
    metadata: dict[str, Any] | None = Field(None, description="Additional config")


class ProviderConnectionUpdate(BaseModel):
    """Request to update a provider connection."""
    
    api_key: str | None = Field(None, description="New API key")
    nickname: str | None = Field(None, description="New nickname")
    base_url: str | None = Field(None, description="New base URL")
    default_model: str | None = Field(None, description="New default model")
    enabled: bool | None = Field(None, description="Enable/disable")
    metadata: dict[str, Any] | None = Field(None, description="New config")


class ProviderConnectionResponse(BaseModel):
    """Response for a provider connection."""
    
    id: str
    provider: str
    nickname: str | None
    base_url: str | None
    default_model: str | None
    enabled: bool
    is_default: bool
    verification_status: str | None
    last_verified: datetime | None
    verification_error: str | None
    use_count: int
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Masked API key for display
    masked_api_key: str = "••••••••"
    
    class Config:
        from_attributes = True


class ProviderInfo(BaseModel):
    """Information about a supported provider."""
    
    name: str
    display_name: str
    website: str | None
    logo_url: str | None
    supported_models: list[str]


class VerificationResponse(BaseModel):
    """Response for provider verification."""
    
    success: bool
    message: str
    verified_models: list[str]
    rate_limit_remaining: int | None
    error_code: str | None


class ModelInfoResponse(BaseModel):
    """Response for a model."""
    
    id: str
    name: str
    description: str
    context_length: int
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    input_cost_per_1k: float
    output_cost_per_1k: float


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str
    detail: str | None = None


# ==================== ENDPOINTS ====================

@router.get("/", response_model=list[ProviderConnectionResponse])
async def list_providers(
    user: AuthenticatedUser,
    db: DbSession,
    enabled_only: bool = False,
) -> list[ProviderConnectionResponse]:
    """List all provider connections for the authenticated user.
    
    Args:
        user: Authenticated user.
        db: Database session.
        enabled_only: Only return enabled connections.
        
    Returns:
        List of provider connections.
    """
    service = ProviderService(db)
    connections = await service.list_connections(user.id, enabled_only)
    
    return [
        ProviderConnectionResponse(
            id=str(conn.id),
            provider=conn.provider,
            nickname=conn.nickname,
            base_url=conn.base_url,
            default_model=conn.default_model,
            enabled=conn.enabled,
            is_default=conn.is_default,
            verification_status=conn.verification_status,
            last_verified=conn.last_verified,
            verification_error=conn.verification_error,
            use_count=conn.use_count,
            last_used_at=conn.last_used_at,
            created_at=conn.created_at,
            updated_at=conn.updated_at,
        )
        for conn in connections
    ]


@router.get("/supported", response_model=list[ProviderInfo])
async def list_supported_providers(
    user: AuthenticatedUser,
    db: DbSession,
) -> list[ProviderInfo]:
    """List all supported BYOK providers.
    
    Args:
        user: Authenticated user.
        db: Database session.
        
    Returns:
        List of supported providers.
    """
    service = ProviderService(db)
    providers = service.list_supported_providers()
    
    return [ProviderInfo(**p) for p in providers]


@router.post("/", response_model=ProviderConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderConnectionCreate,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> ProviderConnectionResponse:
    """Create a new provider connection.
    
    The API key will be encrypted using AES-256-GCM before storage.
    
    Args:
        data: Provider connection data.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
        
    Returns:
        Created provider connection.
    """
    service = ProviderService(db)
    
    # Build request context for audit
    request_context = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    try:
        connection = await service.create_connection(
            user_id=user.id,
            provider=data.provider,
            api_key=data.api_key,
            nickname=data.nickname,
            base_url=data.base_url,
            default_model=data.default_model,
            enabled=data.enabled,
            metadata=data.metadata,  # API parameter name stays the same
            request_context=request_context,
        )
        
        return ProviderConnectionResponse(
            id=str(connection.id),
            provider=connection.provider,
            nickname=connection.nickname,
            base_url=connection.base_url,
            default_model=connection.default_model,
            enabled=connection.enabled,
            is_default=connection.is_default,
            verification_status=connection.verification_status,
            last_verified=connection.last_verified,
            verification_error=connection.verification_error,
            use_count=connection.use_count,
            last_used_at=connection.last_used_at,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ProviderLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DuplicateProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/{provider_id}", response_model=ProviderConnectionResponse)
async def get_provider(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> ProviderConnectionResponse:
    """Get a specific provider connection.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        
    Returns:
        Provider connection.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    connection = await service.get_connection(user.id, conn_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )
    
    return ProviderConnectionResponse(
        id=str(connection.id),
        provider=connection.provider,
        nickname=connection.nickname,
        base_url=connection.base_url,
        default_model=connection.default_model,
        enabled=connection.enabled,
        is_default=connection.is_default,
        verification_status=connection.verification_status,
        last_verified=connection.last_verified,
        verification_error=connection.verification_error,
        use_count=connection.use_count,
        last_used_at=connection.last_used_at,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.patch("/{provider_id}", response_model=ProviderConnectionResponse)
async def update_provider(
    provider_id: str,
    data: ProviderConnectionUpdate,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> ProviderConnectionResponse:
    """Update a provider connection.
    
    Args:
        provider_id: Provider connection UUID.
        data: Update data.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
        
    Returns:
        Updated provider connection.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    # Build updates dict (exclude None values)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    
    request_context = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    try:
        connection = await service.update_connection(
            user_id=user.id,
            connection_id=conn_id,
            updates=updates,
            request_context=request_context,
        )
        
        return ProviderConnectionResponse(
            id=str(connection.id),
            provider=connection.provider,
            nickname=connection.nickname,
            base_url=connection.base_url,
            default_model=connection.default_model,
            enabled=connection.enabled,
            is_default=connection.is_default,
            verification_status=connection.verification_status,
            last_verified=connection.last_verified,
            verification_error=connection.verification_error,
            use_count=connection.use_count,
            last_used_at=connection.last_used_at,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
        
    except ProviderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )
    except DuplicateProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> None:
    """Delete a provider connection.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    request_context = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    deleted = await service.delete_connection(
        user_id=user.id,
        connection_id=conn_id,
        request_context=request_context,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )


@router.post("/{provider_id}/verify", response_model=VerificationResponse)
async def verify_provider(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> VerificationResponse:
    """Verify a provider connection by making a test API call.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
        
    Returns:
        Verification result.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    try:
        result = await service.verify_connection(user.id, conn_id)
        
        return VerificationResponse(
            success=result.success,
            message=result.message,
            verified_models=result.verified_models,
            rate_limit_remaining=result.rate_limit_remaining,
            error_code=result.error_code,
        )
        
    except ProviderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )


@router.get("/{provider_id}/models", response_model=list[ModelInfoResponse])
async def get_provider_models(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> list[ModelInfoResponse]:
    """Get available models for a provider connection.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        
    Returns:
        List of available models.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    try:
        models = await service.get_available_models(user.id, conn_id)
        
        return [
            ModelInfoResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                context_length=m.context_length,
                supports_streaming=m.supports_streaming,
                supports_tools=m.supports_tools,
                supports_vision=m.supports_vision,
                input_cost_per_1k=m.input_cost_per_1k,
                output_cost_per_1k=m.output_cost_per_1k,
            )
            for m in models
        ]
        
    except ProviderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )


@router.post("/{provider_id}/default", response_model=ProviderConnectionResponse)
async def set_default_provider(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> ProviderConnectionResponse:
    """Set a provider connection as the default.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
        
    Returns:
        Updated provider connection.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    request_context = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    try:
        connection = await service.set_default(
            user_id=user.id,
            connection_id=conn_id,
            request_context=request_context,
        )
        
        return ProviderConnectionResponse(
            id=str(connection.id),
            provider=connection.provider,
            nickname=connection.nickname,
            base_url=connection.base_url,
            default_model=connection.default_model,
            enabled=connection.enabled,
            is_default=connection.is_default,
            verification_status=connection.verification_status,
            last_verified=connection.last_verified,
            verification_error=connection.verification_error,
            use_count=connection.use_count,
            last_used_at=connection.last_used_at,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
        
    except ProviderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )


@router.post("/{provider_id}/enable", response_model=ProviderConnectionResponse)
async def enable_provider(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> ProviderConnectionResponse:
    """Enable a provider connection.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
        
    Returns:
        Updated provider connection.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    request_context = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    try:
        connection = await service.enable(
            user_id=user.id,
            connection_id=conn_id,
            request_context=request_context,
        )
        
        return ProviderConnectionResponse(
            id=str(connection.id),
            provider=connection.provider,
            nickname=connection.nickname,
            base_url=connection.base_url,
            default_model=connection.default_model,
            enabled=connection.enabled,
            is_default=connection.is_default,
            verification_status=connection.verification_status,
            last_verified=connection.last_verified,
            verification_error=connection.verification_error,
            use_count=connection.use_count,
            last_used_at=connection.last_used_at,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
        
    except ProviderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )


@router.post("/{provider_id}/disable", response_model=ProviderConnectionResponse)
async def disable_provider(
    provider_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    request: Request,
) -> ProviderConnectionResponse:
    """Disable a provider connection.
    
    Args:
        provider_id: Provider connection UUID.
        user: Authenticated user.
        db: Database session.
        request: FastAPI request for audit context.
        
    Returns:
        Updated provider connection.
    """
    service = ProviderService(db)
    
    try:
        conn_id = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format",
        )
    
    request_context = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    try:
        connection = await service.disable(
            user_id=user.id,
            connection_id=conn_id,
            request_context=request_context,
        )
        
        return ProviderConnectionResponse(
            id=str(connection.id),
            provider=connection.provider,
            nickname=connection.nickname,
            base_url=connection.base_url,
            default_model=connection.default_model,
            enabled=connection.enabled,
            is_default=connection.is_default,
            verification_status=connection.verification_status,
            last_verified=connection.last_verified,
            verification_error=connection.verification_error,
            use_count=connection.use_count,
            last_used_at=connection.last_used_at,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
        
    except ProviderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )
