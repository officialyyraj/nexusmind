"""Authentication service."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.exceptions import RedisError
from redis.asyncio import Redis

from app.config import Settings
from app.db.session import ApiKey, User
from app.utils.security import (
    create_access_token,
    decode_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_api_key,
    verify_password,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db: AsyncSession, settings: Settings, redis_client: Redis):
        self.db = db
        self.settings = settings
        self.redis = redis_client

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        name: str | None = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User | None:
        """Authenticate user with email and password."""
        lockout_key = f"lockout:{email}"
        failure_key = f"failed_attempts:{email}"

        try:
            # 1. Check if the user is currently locked out
            if await self.redis.exists(lockout_key):
                return None  # Fail silently if locked out
        except RedisError:
            logger.warning("Redis connection failed. Bypassing lockout check.", exc_info=True)
            # Fail open: If Redis is down, proceed with auth attempt.

        user = await self.get_user_by_email(email)

        # 2. Verify user and password
        # This block runs for invalid users or invalid passwords to prevent user enumeration.
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            try:
                # Increment failure count for the email address
                current_failures = await self.redis.incr(failure_key)
                await self.redis.expire(failure_key, self.settings.auth_lockout_seconds)
                # If max attempts reached, set lockout
                if current_failures >= self.settings.auth_max_failed_attempts:
                    await self.redis.set(
                        lockout_key, "locked", ex=self.settings.auth_lockout_seconds
                    )
                    await self.redis.delete(failure_key)
            except RedisError:
                logger.warning("Redis connection failed. Could not track failed login attempt.", exc_info=True)
            return None

        if not user.is_active:
            return None

        # 3. Successful login
        try:
            # On success, reset failure counter and clear any potential lockout
            # Use a pipeline for atomicity
            async with self.redis.pipeline() as pipe:
                pipe.delete(failure_key)
                pipe.delete(lockout_key)
                await pipe.execute()
        except RedisError:
            # If Redis is down on successful login, we can't clear the counters.
            # This is acceptable; the counters will expire naturally.
            # Log the issue and continue.
            logger.warning(
                "Redis connection failed. Could not clear lockout counters for successful login.", exc_info=True
            )

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        await self.db.flush()

        return user

    async def create_access_token_for_user(
        self,
        user: User,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create access token for user."""
        return create_access_token(
            data={"sub": str(user.id), "email": user.email},
            settings=self.settings,
            expires_delta=expires_delta,
        )

    async def create_api_key(
        self,
        user_id: uuid.UUID,
        name: str,
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        """Create an API key for a user. Returns the key record and the plain key."""
        plain_key = generate_api_key()
        api_key = ApiKey(
            user_id=user_id,
            name=name,
            key_hash=hash_api_key(plain_key),
            expires_at=expires_at,
            is_active=True,
        )
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key, plain_key

    async def verify_api_key(self, plain_key: str) -> ApiKey | None:
        """Verify an API key and return the key record."""
        key_hash = hash_api_key(plain_key)
        result = await self.db.execute(
            select(ApiKey)
            .where(ApiKey.key_hash == key_hash)
            .where(ApiKey.is_active == True)
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            return None
        # Check expiration
        if api_key.is_expired:
            return None
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        await self.db.flush()
        return api_key

    async def revoke_api_key(self, api_key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Revoke an API key."""
        result = await self.db.execute(
            select(ApiKey)
            .where(ApiKey.id == api_key_id)
            .where(ApiKey.user_id == user_id)
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            return False
        api_key.is_active = False
        await self.db.flush()
        return True

    async def list_api_keys(self, user_id: uuid.UUID) -> list[ApiKey]:
        """List all API keys for a user."""
        result = await self.db.execute(
            select(ApiKey)
            .where(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_user(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        """Update user details."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        if name is not None:
            user.name = name
        if is_active is not None:
            user.is_active = is_active
        await self.db.flush()
        return user

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        if not user.password_hash:
            return False
        if not verify_password(old_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        await self.db.flush()
        return True
