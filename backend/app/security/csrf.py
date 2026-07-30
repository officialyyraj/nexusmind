"""CSRF protection for state-changing requests."""

import secrets
import time
from typing import Any

from pydantic import BaseModel


class CSRFToken(BaseModel):
    """CSRF token model."""

    token: str
    created_at: float
    expires_at: float


class CSRFService:
    """Service for CSRF token generation and validation."""

    def __init__(self, token_ttl: int = 3600):
        """
        Initialize CSRF service.
        
        Args:
            token_ttl: Token time-to-live in seconds (default 1 hour)
        """
        self._token_ttl = token_ttl
        self._tokens: dict[str, CSRFToken] = {}

    def generate_token(self, user_id: str | None = None) -> str:
        """
        Generate a new CSRF token.
        
        Args:
            user_id: Optional user ID to associate with the token
            
        Returns:
            The generated CSRF token
        """
        token = secrets.token_urlsafe(32)
        now = time.time()

        self._tokens[token] = CSRFToken(
            token=token,
            created_at=now,
            expires_at=now + self._token_ttl,
        )

        # Clean up expired tokens
        self._cleanup_expired()

        return token

    def validate_token(
        self,
        token: str,
        expected_origin: str | None = None,
        expected_referrer: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            expected_origin: Expected Origin header value
            expected_referrer: Expected Referer header value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not token:
            return False, "Missing CSRF token"

        # Check if token exists
        if token not in self._tokens:
            return False, "Invalid CSRF token"

        csrf_token = self._tokens[token]

        # Check if token is expired
        if time.time() > csrf_token.expires_at:
            del self._tokens[token]
            return False, "CSRF token expired"

        # Validate origin if provided
        if expected_origin:
            # In production, validate against allowed origins
            pass

        # Validate referrer if provided
        if expected_referrer:
            # In production, validate against allowed referrers
            pass

        return True, None

    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a CSRF token.
        
        Args:
            token: The token to invalidate
            
        Returns:
            True if token was invalidated, False if not found
        """
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False

    def _cleanup_expired(self) -> None:
        """Remove expired tokens from storage."""
        now = time.time()
        expired = [
            token for token, csrf in self._tokens.items()
            if now > csrf.expires_at
        ]
        for token in expired:
            del self._tokens[token]

    def get_token_for_user(self, user_id: str) -> str | None:
        """
        Get an existing valid token for a user, or generate a new one.
        
        Note: In a real implementation, you would store tokens per-user.
        This simplified version just generates new tokens.
        """
        return self.generate_token(user_id)


class CSRFProtection:
    """CSRF protection middleware/component."""

    # HTTP methods that require CSRF protection
    PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # HTTP methods that don't require CSRF protection
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, service: CSRFService):
        self._service = service

    def requires_protection(self, method: str) -> bool:
        """Check if a method requires CSRF protection."""
        return method.upper() in self.PROTECTED_METHODS

    def is_safe_method(self, method: str) -> bool:
        """Check if a method is considered safe."""
        return method.upper() in self.SAFE_METHODS

    async def validate_request(
        self,
        method: str,
        token: str | None,
        origin: str | None = None,
        referer: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Validate a request for CSRF.
        
        Args:
            method: HTTP method
            token: CSRF token from request
            origin: Origin header
            referer: Referer header
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Safe methods don't need validation
        if self.is_safe_method(method):
            return True, None

        # Protected methods require CSRF token
        if not self.requires_protection(method):
            return True, None

        # Validate the token
        return self._service.validate_token(token, origin, referer)


class CSRFTokenResponse(BaseModel):
    """Response model for CSRF token endpoint."""

    csrf_token: str
    expires_in: int


# Global CSRF service instance
_csrf_service: CSRFService | None = None


def get_csrf_service() -> CSRFService:
    """Get CSRF service instance."""
    global _csrf_service
    if _csrf_service is None:
        _csrf_service = CSRFService()
    return _csrf_service
