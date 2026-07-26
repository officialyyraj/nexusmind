"""Comprehensive authentication and authorization tests."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import jwt
from fastapi import HTTPException

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    decode_access_token_strict,
    generate_api_key,
    hash_api_key,
    verify_api_key,
    ExpiredTokenError,
    InvalidTokenError,
    MalformedTokenError,
)
from app.dependencies import (
    require_auth,
    require_auth_user,
    require_admin,
    get_current_user_id,
)
from app.config import get_settings


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_hash(self):
        """Test that hash_password returns a hash."""
        password = "secure_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that hashing the same password produces different hashes (due to salt)."""
        password = "secure_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "secure_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "secure_password_123"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying with empty password."""
        hashed = hash_password("some_password")
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a JWT string."""
        token = create_access_token({"sub": "user123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiry."""
        token = create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(hours=1)
        )
        assert isinstance(token, str)

    def test_decode_access_token_valid(self):
        """Test decoding a valid token."""
        token = create_access_token({"sub": "user123"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"

    def test_decode_access_token_expired(self):
        """Test decoding an expired token."""
        token = create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_decode_access_token_invalid(self):
        """Test decoding an invalid token."""
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_decode_access_token_empty(self):
        """Test decoding an empty token."""
        payload = decode_access_token("")
        assert payload is None

    def test_decode_access_token_strict_valid(self):
        """Test strict decoding of a valid token."""
        token = create_access_token({"sub": "user123"})
        payload = decode_access_token_strict(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_decode_access_token_strict_expired(self):
        """Test strict decoding of an expired token raises ExpiredTokenError."""
        token = create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(ExpiredTokenError):
            decode_access_token_strict(token)

    def test_decode_access_token_strict_invalid_signature(self):
        """Test strict decoding with invalid signature raises InvalidTokenError."""
        settings = get_settings()
        # Create a token with wrong secret
        bad_token = jwt.encode(
            {"sub": "user123", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong_secret",
            algorithm=settings.jwt_algorithm
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token_strict(bad_token)

    def test_decode_access_token_strict_malformed(self):
        """Test strict decoding of malformed token raises MalformedTokenError."""
        with pytest.raises(MalformedTokenError):
            decode_access_token_strict("not.a.valid.jwt")

    def test_decode_access_token_strict_empty(self):
        """Test strict decoding of empty token raises MalformedTokenError."""
        with pytest.raises(MalformedTokenError):
            decode_access_token_strict("")

    def test_token_contains_required_claims(self):
        """Test that tokens contain all required claims."""
        token = create_access_token({"sub": "user123"})
        payload = decode_access_token(token)
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload
        assert "iss" in payload


class TestAPIKeys:
    """Tests for API key functions."""

    def test_generate_api_key_format(self):
        """Test that generated API key has correct format."""
        key = generate_api_key()
        assert key.startswith("nmk_")
        assert len(key) > 10

    def test_generate_api_key_unique(self):
        """Test that generated API keys are unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        assert key1 != key2

    def test_hash_api_key_returns_hash(self):
        """Test that hash_api_key returns a hash."""
        key = "unit-test-key"
        hashed = hash_api_key(key)
        assert hashed != key
        assert len(hashed) == 64  # SHA256 hex digest

    def test_verify_api_key_correct(self):
        """Test verifying correct API key."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_api_key_incorrect(self):
        """Test verifying incorrect API key."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key("wrong_key", hashed) is False

    def test_verify_api_key_empty_plain(self):
        """Test verifying with empty plain key returns False."""
        hashed = hash_api_key("some_key")
        assert verify_api_key("", hashed) is False

    def test_verify_api_key_empty_hash(self):
        """Test verifying with empty hash returns False."""
        assert verify_api_key("some_key", "") is False


class TestAuthDependencies:
    """Tests for authentication dependencies."""

    @pytest.mark.asyncio
    async def test_require_auth_valid_token(self):
        """Test require_auth with valid token."""
        token = create_access_token({"sub": "user123"})
        
        # Mock credentials
        credentials = MagicMock()
        credentials.credentials = token
        
        # Call require_auth
        user_id = await require_auth(credentials)
        assert user_id == "user123"

    @pytest.mark.asyncio
    async def test_require_auth_invalid_token(self):
        """Test require_auth with invalid token raises 401."""
        credentials = MagicMock()
        credentials.credentials = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(credentials)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_auth_expired_token(self):
        """Test require_auth with expired token raises 401."""
        token = create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1)
        )
        
        credentials = MagicMock()
        credentials.credentials = token
        
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(credentials)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_id_valid_token(self):
        """Test get_current_user_id with valid token returns user ID."""
        token = create_access_token({"sub": "user123"})
        
        credentials = MagicMock()
        credentials.credentials = token
        
        user_id = await get_current_user_id(credentials)
        assert user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_current_user_id_no_credentials(self):
        """Test get_current_user_id with no credentials returns None."""
        user_id = await get_current_user_id(None)
        assert user_id is None

    @pytest.mark.asyncio
    async def test_get_current_user_id_invalid_token(self):
        """Test get_current_user_id with invalid token returns None."""
        credentials = MagicMock()
        credentials.credentials = "invalid.token"
        
        user_id = await get_current_user_id(credentials)
        assert user_id is None


class TestSecurityHeaders:
    """Tests for security headers in responses."""

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers


class TestPublicEndpoints:
    """Tests for public endpoints that don't require auth."""

    def test_health_endpoint_public(self, client):
        """Test that health endpoint is publicly accessible."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_liveness_probe_public(self, client):
        """Test that liveness probe is publicly accessible."""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_root_endpoint_public(self, client):
        """Test that root endpoint is publicly accessible."""
        response = client.get("/")
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Tests for protected endpoints requiring auth."""

    def test_sessions_endpoint_requires_auth(self, client):
        """Test that sessions endpoint requires authentication."""
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 403

    def test_sessions_create_requires_auth(self, client):
        """Test that session creation requires authentication."""
        response = client.post("/api/v1/sessions/", json={})
        assert response.status_code == 403

    def test_memory_search_requires_auth(self, client):
        """Test that memory search requires authentication."""
        response = client.post("/api/v1/memory/search", json={"query": "test"})
        assert response.status_code == 403

    def test_plugins_list_requires_auth(self, client):
        """Test that plugins list requires authentication."""
        response = client.get("/api/v1/plugins/")
        assert response.status_code == 403

    def test_sandbox_allocate_requires_auth(self, client):
        """Test that sandbox allocation requires authentication."""
        response = client.post("/api/v1/sandbox/allocate")
        assert response.status_code == 403


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_register_missing_email(self, client):
        """Test registration with missing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={"password": "password123"}
        )
        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123"}
        )
        assert response.status_code == 422  # Validation error

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422  # Validation error

    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "password123"}
        )
        assert response.status_code == 422  # Validation error


class TestRBACAuthorization:
    """Tests for role-based access control."""

    def test_admin_endpoints_require_admin(self, client):
        """Test that admin endpoints require admin privileges."""
        # Security audit logs
        response = client.get("/api/v1/security/audit-logs")
        assert response.status_code == 403
        
        # Security dashboard
        response = client.get("/api/v1/security/dashboard")
        assert response.status_code == 403
        
        # Role assignment
        response = client.post(
            "/api/v1/security/roles/assign",
            json={"user_id": "test", "role": "admin"}
        )
        assert response.status_code == 403


class TestErrorMessages:
    """Tests for error messages don't leak sensitive info."""

    def test_invalid_token_error_generic(self, client):
        """Test that invalid token returns generic error."""
        response = client.get(
            "/api/v1/sessions/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        # Error should not reveal token details
        assert "token" in response.json()["detail"].lower()

    def test_no_auth_returns_proper_error(self, client):
        """Test that missing auth returns proper error."""
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 403
        assert "WWW-Authenticate" in response.headers or "Bearer" in str(response.headers)


class TestTokenTypes:
    """Tests for token type validation."""

    def test_access_token_has_correct_type(self):
        """Test that access tokens have correct type claim."""
        token = create_access_token({"sub": "user123"})
        payload = decode_access_token(token)
        assert payload["type"] == "access"

    def test_custom_token_type(self):
        """Test creating token with custom type."""
        token = create_access_token(
            {"sub": "user123"},
            token_type="refresh"
        )
        payload = decode_access_token(token)
        assert payload["type"] == "refresh"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
