"""Authentication API endpoints."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.db.database import async_session_maker
from app.db.session import User
from app.utils.security import decode_access_token

router = APIRouter()


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in async_session_maker():
        yield session


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class UserResponse(BaseModel):
    """User response."""

    id: str
    email: str
    name: str | None
    is_active: bool


class ApiKeyCreate(BaseModel):
    """API key creation request."""

    name: str
    expires_in_days: int | None = None


class ApiKeyResponse(BaseModel):
    """API key response."""

    id: str
    name: str
    created_at: datetime
    expires_at: datetime | None
    is_active: bool


class ApiKeyCreatedResponse(BaseModel):
    """API key creation response with the key."""

    id: str
    name: str
    api_key: str  # Plain key - only shown once!
    created_at: datetime
    expires_at: datetime | None


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register a new user."""
    service = AuthService(db)

    # Check if user exists
    existing = await service.get_user_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await service.create_user(
        email=request.email,
        password=request.password,
        name=request.name,
    )

    # Create token
    token = await service.create_access_token_for_user(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
        },
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Login with email and password."""
    service = AuthService(db)

    user = await service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = await service.create_access_token_for_user(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
        },
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict[str, Any]:
    """Get current user information."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    service = AuthService(db)
    user = await service.get_user_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
    }


@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    request: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict[str, Any]:
    """Create a new API key."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = uuid.UUID(payload["sub"])
    service = AuthService(db)

    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + datetime.timedelta(days=request.expires_in_days)

    api_key, plain_key = await service.create_api_key(
        user_id=user_id,
        name=request.name,
        expires_at=expires_at,
    )

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "api_key": plain_key,  # Only shown once!
        "created_at": api_key.created_at,
        "expires_at": api_key.expires_at,
    }


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> list[dict[str, Any]]:
    """List all API keys for the current user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = uuid.UUID(payload["sub"])
    service = AuthService(db)
    api_keys = await service.list_api_keys(user_id)

    return [
        {
            "id": str(key.id),
            "name": key.name,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
            "is_active": key.is_active,
        }
        for key in api_keys
    ]


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict[str, Any]:
    """Revoke an API key."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = uuid.UUID(payload["sub"])
    service = AuthService(db)

    success = await service.revoke_api_key(uuid.UUID(api_key_id), user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"status": "revoked"}
