"""Tests for authentication module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone


class TestAuthService:
    """Test authentication service."""

    def test_auth_service_init(self) -> None:
        """Test AuthService initialization."""
        from app.auth.service import AuthService

        mock_db = AsyncMock()
        service = AuthService(mock_db)
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_get_user_by_email(self) -> None:
        """Test getting user by email."""
        from app.auth.service import AuthService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service.get_user_by_email("test@example.com")
        assert user is None

    @pytest.mark.asyncio
    async def test_create_user(self) -> None:
        """Test creating a new user."""
        from app.auth.service import AuthService

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        user = await service.create_user(
            email="new@example.com",
            password="password123",
            name="New User"
        )

        assert user.email == "new@example.com"
        assert user.name == "New User"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self) -> None:
        """Test authentication with non-existent user."""
        from app.auth.service import AuthService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service.authenticate_user("nonexistent@example.com", "password")
        assert user is None

    @pytest.mark.asyncio
    async def test_create_access_token(self) -> None:
        """Test creating access token for user."""
        from app.auth.service import AuthService
        from app.db.session import User

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        mock_user = MagicMock(spec=User)
        mock_user.id = "test-uuid"
        mock_user.email = "test@example.com"

        token = await service.create_access_token_for_user(mock_user)
        assert token is not None
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_create_api_key(self) -> None:
        """Test creating API key."""
        from app.auth.service import AuthService
        import uuid

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        api_key, plain_key = await service.create_api_key(
            user_id=uuid.uuid4(),
            name="Test Key",
            expires_at=None
        )

        assert plain_key is not None
        assert len(plain_key) > 0
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_api_keys(self) -> None:
        """Test listing API keys."""
        from app.auth.service import AuthService
        import uuid

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        keys = await service.list_api_keys(uuid.uuid4())
        assert isinstance(keys, list)


class TestAuthRoutes:
    """Test authentication routes."""

    def test_register_request_validation(self) -> None:
        """Test RegisterRequest model validation."""
        from app.auth.routes import RegisterRequest

        # Valid request
        request = RegisterRequest(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        assert request.email == "test@example.com"

    def test_login_request_validation(self) -> None:
        """Test LoginRequest model validation."""
        from app.auth.routes import LoginRequest

        request = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert request.email == "test@example.com"

    def test_token_response_model(self) -> None:
        """Test TokenResponse model."""
        from app.auth.routes import TokenResponse

        response = TokenResponse(
            access_token="test-token",
            user={"id": "123", "email": "test@example.com"}
        )
        assert response.token_type == "bearer"
        assert response.access_token == "test-token"


class TestJWTSecurity:
    """Test JWT security utilities."""

    def test_create_access_token(self) -> None:
        """Test creating JWT access token."""
        from app.utils.security import create_access_token

        token = create_access_token(
            data={"sub": "test-user", "email": "test@example.com"},
            expires_delta=timedelta(hours=1)
        )
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token(self) -> None:
        """Test decoding JWT access token."""
        from app.utils.security import create_access_token, decode_access_token

        token = create_access_token(data={"sub": "test-user"})
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == "test-user"

    def test_decode_invalid_token(self) -> None:
        """Test decoding invalid token returns None."""
        from app.utils.security import decode_access_token

        payload = decode_access_token("invalid-token")
        assert payload is None

    def test_hash_password(self) -> None:
        """Test password hashing."""
        from app.utils.security import hash_password, verify_password

        password = "test-password-123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong-password", hashed) is False

    def test_generate_api_key(self) -> None:
        """Test API key generation."""
        from app.utils.security import generate_api_key, hash_api_key

        key = generate_api_key()
        assert key is not None
        assert len(key) >= 32

        hashed = hash_api_key(key)
        assert hashed != key


class TestApiKeyModel:
    """Test API key model."""

    def test_api_key_is_expired_false(self) -> None:
        """Test API key not expired when no expiration."""
        from app.db.session import ApiKey
        import uuid

        api_key = ApiKey(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Key",
            key_hash="hash123",
            expires_at=None
        )

        assert api_key.is_expired is False

    def test_api_key_is_expired_true(self) -> None:
        """Test API key is expired when past expiration."""
        from app.db.session import ApiKey
        import uuid

        api_key = ApiKey(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Key",
            key_hash="hash123",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )

        assert api_key.is_expired is True


class TestUserModel:
    """Test user model."""

    def test_user_repr(self) -> None:
        """Test user string representation."""
        from app.db.session import User

        user = User(email="test@example.com")
        assert "test@example.com" in repr(user)

    def test_user_defaults(self) -> None:
        """Test user default values."""
        from app.db.session import User

        user = User(email="test@example.com")
        assert user.is_active is True
        assert user.is_superuser is False
