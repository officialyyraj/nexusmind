"""Authentication API endpoints."""

import re
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from app.auth.service import AuthService
from app.db.session import User
from app.dependencies import AuthenticatedUser, DbSession

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


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
    db: DbSession,
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
    db: DbSession,
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
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Get current user information."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
    }


@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    request: ApiKeyCreate,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Create a new API key."""
    service = AuthService(db)

    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    api_key, plain_key = await service.create_api_key(
        user_id=user.id,
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
    user: AuthenticatedUser,
    db: DbSession,
) -> list[dict[str, Any]]:
    """List all API keys for the current user."""
    service = AuthService(db)
    api_keys = await service.list_api_keys(user.id)

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
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Revoke an API key."""
    service = AuthService(db)

    success = await service.revoke_api_key(uuid.UUID(api_key_id), user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"status": "revoked"}
