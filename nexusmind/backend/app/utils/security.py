"""Security utilities for NexusMind."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """Base exception for token errors."""
    pass


class ExpiredTokenError(TokenError):
    """Token has expired."""
    pass


class InvalidTokenError(TokenError):
    """Token is invalid."""
    pass


class MalformedTokenError(TokenError):
    """Token is malformed."""
    pass


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expiration_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
        "iss": settings.app_name,
        "aud": "nexusmind-api",
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require_sub": True,
                "require_exp": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except JWTError:
        return None


def decode_access_token_strict(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token with strict validation.
    
    Raises:
        ExpiredTokenError: If token has expired
        InvalidTokenError: If token signature is invalid
        MalformedTokenError: If token is malformed
    
    Returns:
        Token payload dictionary
    """
    settings = get_settings()
    
    if not token:
        raise MalformedTokenError("Token is empty")
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require_sub": True,
                "require_exp": True,
            },
        )
        
        # Validate token type
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        # Validate issuer
        if payload.get("iss") != settings.app_name:
            raise InvalidTokenError("Invalid token issuer")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError("Token has expired")
    except jwt.InvalidSignatureError:
        raise InvalidTokenError("Invalid token signature")
    except jwt.DecodeError:
        raise MalformedTokenError("Token is malformed")
    except JWTError as e:
        raise InvalidTokenError(f"Token validation failed: {str(e)}")


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"nmk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash using constant-time comparison.
    
    This prevents timing attacks by ensuring the comparison takes
    the same amount of time regardless of where the mismatch occurs.
    """
    if not plain_key or not hashed_key:
        return False
    return hmac.compare_digest(hash_api_key(plain_key), hashed_key)


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"sess_{secrets.token_urlsafe(24)}"


def generate_message_id() -> str:
    """Generate a unique message ID."""
    return f"msg_{secrets.token_urlsafe(24)}"


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return f"task_{secrets.token_urlsafe(24)}"


def generate_sandbox_id() -> str:
    """Generate a unique sandbox ID."""
    return f"sand_{secrets.token_urlsafe(24)}"


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, list[datetime]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for the given identifier."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)

        if identifier not in self._requests:
            self._requests[identifier] = []

        # Remove old requests
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier] if req_time > cutoff
        ]

        # Check if limit exceeded
        if len(self._requests[identifier]) >= self.requests_per_minute:
            return False

        # Add current request
        self._requests[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for the identifier."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)

        if identifier not in self._requests:
            return self.requests_per_minute

        recent_requests = [
            req_time for req_time in self._requests[identifier] if req_time > cutoff
        ]
        return max(0, self.requests_per_minute - len(recent_requests))


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_minute)
    return _rate_limiter
