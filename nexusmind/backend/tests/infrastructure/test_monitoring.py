"""Infrastructure tests for monitoring and health endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_basic_health(self):
        """Test basic health endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    @pytest.mark.asyncio
    async def test_liveness_probe(self):
        """Test Kubernetes liveness probe endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestMetricsEndpoint:
    """Tests for Prometheus metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test metrics endpoint returns Prometheus format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        # Check that we have some metrics
        content = response.text
        assert "nexusmind" in content.lower()


class TestStructuredLogging:
    """Tests for structured logging functionality."""

    def test_log_context_manager(self):
        """Test LogContext context manager."""
        from app.utils.logger import LogContext, get_request_id, get_session_id

        # Initially no context
        assert get_request_id() is None
        assert get_session_id() is None

        # Set context
        with LogContext(request_id="test-req", session_id="test-sess"):
            assert get_request_id() == "test-req"
            assert get_session_id() == "test-sess"

        # Context cleared after exit
        assert get_request_id() is None
        assert get_session_id() is None

    def test_generate_request_id(self):
        """Test request ID generation."""
        from app.utils.logger import generate_request_id

        id1 = generate_request_id()
        id2 = generate_request_id()

        # IDs should be unique
        assert id1 != id2

        # Should be valid UUID format
        assert len(id1) == 36
        assert id1.count("-") == 4


class TestMetricsService:
    """Tests for metrics service."""

    def test_record_request(self):
        """Test recording request metrics."""
        from app.monitoring.metrics import get_metrics_service

        # Use global service
        service = get_metrics_service()
        service.record_request("GET", "/api/v1/test", 200, 0.5)

        # No assertion needed - just verify it doesn't raise

    def test_record_error(self):
        """Test recording error metrics."""
        from app.monitoring.metrics import get_metrics_service

        service = get_metrics_service()
        service.record_error("ValidationError", "/api/v1/test")

    def test_metrics_format(self):
        """Test that metrics are in Prometheus format."""
        from app.monitoring.metrics import get_metrics_service

        service = get_metrics_service()
        content, content_type = service.get_metrics()

        assert isinstance(content, bytes)
        assert "text/plain" in content_type or "openmetrics" in content_type


class TestRBACSecurity:
    """Tests for RBAC security."""

    def test_role_permissions(self):
        """Test that role permissions are properly configured."""
        from app.security.rbac import Role, ROLE_PERMISSIONS

        # Owner should have all permissions
        owner_perms = ROLE_PERMISSIONS[Role.OWNER]
        assert len(owner_perms) > 0

        # Viewer should have fewer permissions than developer
        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
        developer_perms = ROLE_PERMISSIONS[Role.DEVELOPER]
        assert len(viewer_perms) < len(developer_perms)

    def test_permission_enum(self):
        """Test permission enum values."""
        from app.security.rbac import Permission

        # Check some permissions exist
        assert Permission.PROJECT_READ.value == "project:read"
        assert Permission.PROJECT_WRITE.value == "project:write"
        assert Permission.SESSION_DELETE.value == "session:delete"


class TestInputValidation:
    """Tests for input validation."""

    def test_validate_email(self):
        """Test email validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()

        assert validator.validate_email("test@example.com") is True
        assert validator.validate_email("invalid") is False

    def test_validate_sql_injection(self):
        """Test SQL injection detection."""
        from app.security.validation import InputValidator

        validator = InputValidator()

        # Should detect SQL injection attempts
        assert validator.validate_safe_string("'; DROP TABLE users;--") is False
        assert validator.validate_safe_string("1 OR 1=1") is False

    def test_validate_path_traversal(self):
        """Test path traversal detection."""
        from app.security.validation import InputValidator

        validator = InputValidator()

        # Should detect path traversal
        assert validator.validate_path("../etc/passwd") is False
        assert validator.validate_path("/etc/passwd") is False


class TestSecretsEncryption:
    """Tests for secrets encryption."""

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        from app.security.secrets import SecretsManager

        manager = SecretsManager()
        original = "super-secret-api-key"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)

        assert encrypted != original
        assert decrypted == original

    def test_validate_openai_key(self):
        """Test OpenAI key validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()

        assert validator.validate_openai_key("sk-1234567890") is True
        assert validator.validate_openai_key("invalid") is False


class TestCSRFProtection:
    """Tests for CSRF protection."""

    def test_generate_token(self):
        """Test CSRF token generation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        token = service.generate_token()

        assert token is not None
        assert len(token) > 0

    def test_validate_token(self):
        """Test CSRF token validation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        token = service.generate_token()

        is_valid, error = service.validate_token(token)
        assert is_valid is True
        assert error is None

    def test_invalid_token(self):
        """Test invalid token rejection."""
        from app.security.csrf import CSRFService

        service = CSRFService()

        is_valid, error = service.validate_token("invalid-token")
        assert is_valid is False
        assert error is not None


class TestConfiguration:
    """Tests for configuration."""

    def test_settings_defaults(self):
        """Test default settings values."""
        from app.config import get_settings

        settings = get_settings()

        assert settings.app_name == "NexusMind"
        assert settings.environment in ["development", "staging", "production"]

    def test_environment_detection(self):
        """Test environment detection."""
        from app.config import get_settings

        settings = get_settings()

        assert hasattr(settings, "is_production")
        assert hasattr(settings, "is_development")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
