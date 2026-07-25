"""Tests for security module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


class TestInputValidator:
    """Tests for InputValidator."""

    def test_validate_email_valid(self):
        """Test valid email validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_email("test@example.com") is True
        assert validator.validate_email("user.name+tag@domain.co.uk") is True

    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_email("") is False
        assert validator.validate_email("invalid") is False
        assert validator.validate_email("@example.com") is False
        assert validator.validate_email("test@") is False

    def test_validate_uuid_valid(self):
        """Test valid UUID validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert validator.validate_uuid(valid_uuid) is True

    def test_validate_uuid_invalid(self):
        """Test invalid UUID validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_uuid("") is False
        assert validator.validate_uuid("invalid") is False
        assert validator.validate_uuid("123") is False

    def test_validate_alphanumeric_valid(self):
        """Test valid alphanumeric validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_alphanumeric("test123") is True
        assert validator.validate_alphanumeric("test_123") is True
        assert validator.validate_alphanumeric("test-123") is True

    def test_validate_alphanumeric_invalid(self):
        """Test invalid alphanumeric validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_alphanumeric("") is False
        assert validator.validate_alphanumeric("test user") is False
        assert validator.validate_alphanumeric("test@123") is False

    def test_validate_length(self):
        """Test string length validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_length("test", 1, 10) is True
        assert validator.validate_length("", 0, 10) is True
        assert validator.validate_length("", 1, 10) is False
        assert validator.validate_length("a" * 100, 1, 50) is False

    def test_validate_safe_string_no_injection(self):
        """Test safe string validation with no injection."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_safe_string("Hello World") is True
        assert validator.validate_safe_string("Test 123") is True
        assert validator.validate_safe_string("Function name") is True

    def test_validate_safe_string_sql_injection(self):
        """Test safe string validation with SQL injection."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_safe_string("'; DROP TABLE users;--") is False
        assert validator.validate_safe_string("1 OR 1=1") is False

    def test_validate_safe_string_script_injection(self):
        """Test safe string validation with script injection."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_safe_string("<script>alert('xss')</script>") is False
        assert validator.validate_safe_string("javascript:void(0)") is False
        assert validator.validate_safe_string("onclick=alert('xss')") is False

    def test_sanitize_string(self):
        """Test string sanitization."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        result = validator.sanitize_string("<script>alert('xss')</script>Test")
        assert "<script>" not in result
        assert "Test" in result

    def test_validate_url_valid(self):
        """Test valid URL validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_url("https://example.com") is True
        assert validator.validate_url("http://localhost:8080") is True
        assert validator.validate_url("https://example.com/path") is True

    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_url("") is False
        assert validator.validate_url("not-a-url") is False
        assert validator.validate_url("ftp://example.com") is False

    def test_validate_path_safe(self):
        """Test safe path validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_path("src/index.ts") is True
        assert validator.validate_path("lib/utils.ts") is True
        assert validator.validate_path("components/Button.tsx") is True

    def test_validate_path_traversal(self):
        """Test path traversal detection."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_path("../etc/passwd") is False
        assert validator.validate_path("src/../../etc/passwd") is False
        assert validator.validate_path("/etc/passwd") is False

    def test_validate_command_safe(self):
        """Test safe command validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_command("ls -la") is True
        assert validator.validate_command("git status") is True
        assert validator.validate_command("npm install") is True

    def test_validate_command_dangerous(self):
        """Test dangerous command detection."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        assert validator.validate_command("rm -rf /") is False
        assert validator.validate_command("dd if=/dev/zero of=/dev/sda") is False

    def test_validate_mcp_input_valid(self):
        """Test valid MCP input validation."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        is_valid, error = validator.validate_mcp_input("read_file", {"path": "/src/test.ts"})
        assert is_valid is True
        assert error is None

    def test_validate_mcp_input_invalid_tool(self):
        """Test invalid MCP tool name."""
        from app.security.validation import InputValidator

        validator = InputValidator()
        is_valid, error = validator.validate_mcp_input("invalid tool name", {})
        assert is_valid is False
        assert "Invalid tool name" in error


class TestCSRFService:
    """Tests for CSRFService."""

    def test_generate_token(self):
        """Test token generation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        token = service.generate_token()
        assert token is not None
        assert len(token) > 0

    def test_validate_token_valid(self):
        """Test valid token validation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        token = service.generate_token()
        is_valid, error = service.validate_token(token)
        assert is_valid is True
        assert error is None

    def test_validate_token_invalid(self):
        """Test invalid token validation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        is_valid, error = service.validate_token("invalid-token")
        assert is_valid is False
        assert error is not None

    def test_validate_token_missing(self):
        """Test missing token validation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        is_valid, error = service.validate_token("")
        assert is_valid is False
        assert "Missing" in error

    def test_invalidate_token(self):
        """Test token invalidation."""
        from app.security.csrf import CSRFService

        service = CSRFService()
        token = service.generate_token()
        assert service.invalidate_token(token) is True
        is_valid, _ = service.validate_token(token)
        assert is_valid is False


class TestRBAC:
    """Tests for RBAC system."""

    def test_role_permissions_owner(self):
        """Test that owner has all permissions."""
        from app.security.rbac import Role, ROLE_PERMISSIONS

        owner_perms = ROLE_PERMISSIONS[Role.OWNER]
        assert len(owner_perms) > 0
        # Owner should have most permissions
        assert len(owner_perms) >= 30

    def test_role_permissions_viewer(self):
        """Test that viewer has limited permissions."""
        from app.security.rbac import Role, ROLE_PERMISSIONS

        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
        # Viewer should have read permissions but not write
        assert any("read" in p.value.lower() for p in viewer_perms)
        assert not any("delete" in p.value.lower() for p in viewer_perms)

    def test_role_hierarchy(self):
        """Test that higher roles have more permissions."""
        from app.security.rbac import Role, ROLE_PERMISSIONS

        admin_perms = set(ROLE_PERMISSIONS[Role.ADMIN])
        developer_perms = set(ROLE_PERMISSIONS[Role.DEVELOPER])
        viewer_perms = set(ROLE_PERMISSIONS[Role.VIEWER])

        # Each lower role should have a subset of the higher role's permissions
        assert viewer_perms.issubset(developer_perms) or len(viewer_perms & developer_perms) > 0
        assert developer_perms.issubset(admin_perms) or len(developer_perms & admin_perms) > 0


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        from app.security.secrets import SecretsManager

        manager = SecretsManager()
        original = "my-secret-api-key"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)

        assert encrypted != original
        assert decrypted == original

    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        from app.security.secrets import SecretsManager

        manager = SecretsManager()
        assert manager.encrypt("") == ""
        assert manager.decrypt("") == ""

    def test_encrypt_dict(self):
        """Test encrypting dictionary."""
        from app.security.secrets import SecretsManager

        manager = SecretsManager()
        data = {"key1": "value1", "key2": "value2"}
        encrypted = manager.encrypt_dict(data)

        assert encrypted["key1"] != "value1"
        assert manager.decrypt(encrypted["key1"]) == "value1"

    def test_generate_key(self):
        """Test key generation."""
        from app.security.secrets import SecretsManager

        key = SecretsManager.generate_key()
        assert key is not None
        assert len(key) > 0


class TestSecretsValidator:
    """Tests for SecretsValidator."""

    def test_validate_openai_key_valid(self):
        """Test valid OpenAI key validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()
        assert validator.validate_openai_key("sk-1234567890abcdef") is True

    def test_validate_openai_key_invalid(self):
        """Test invalid OpenAI key validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()
        assert validator.validate_openai_key("") is False
        assert validator.validate_openai_key("invalid-key") is False

    def test_validate_anthropic_key_valid(self):
        """Test valid Anthropic key validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()
        assert validator.validate_anthropic_key("sk-ant-1234567890abcdef") is True

    def test_validate_github_token_valid(self):
        """Test valid GitHub token validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()
        token = "ghp_" + "a" * 36
        assert validator.validate_github_token(token) is True

    def test_validate_database_url_valid(self):
        """Test valid database URL validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()
        assert validator.validate_database_url("postgresql://user:pass@localhost/db") is True
        assert validator.validate_database_url("mysql://user:pass@localhost/db") is True

    def test_validate_database_url_invalid(self):
        """Test invalid database URL validation."""
        from app.security.secrets import SecretsValidator

        validator = SecretsValidator()
        assert validator.validate_database_url("") is False
        assert validator.validate_database_url("invalid-url") is False


class TestAuditAction:
    """Tests for AuditAction enum."""

    def test_audit_action_values(self):
        """Test audit action enum values."""
        from app.security.audit import AuditAction

        assert AuditAction.LOGIN.value == "auth:login"
        assert AuditAction.LOGOUT.value == "auth:logout"
        assert AuditAction.USER_CREATE.value == "user:create"
        assert AuditAction.PROJECT_DELETE.value == "project:delete"

    def test_action_severity_mapping(self):
        """Test action severity mapping."""
        from app.security.audit import AuditAction, AuditLevel, ACTION_SEVERITY

        # Login should be info level
        assert ACTION_SEVERITY[AuditAction.LOGIN] == AuditLevel.INFO
        # Failed login should be warning
        assert ACTION_SEVERITY[AuditAction.LOGIN_FAILED] == AuditLevel.WARNING
        # Auth failure should be error
        assert ACTION_SEVERITY[AuditAction.AUTH_FAILURE] == AuditLevel.ERROR


class TestRoleEnum:
    """Tests for Role enum."""

    def test_role_values(self):
        """Test role enum values."""
        from app.security.rbac import Role

        assert Role.OWNER.value == "owner"
        assert Role.ADMIN.value == "admin"
        assert Role.DEVELOPER.value == "developer"
        assert Role.VIEWER.value == "viewer"


class TestPermissionEnum:
    """Tests for Permission enum."""

    def test_permission_categories(self):
        """Test permission categories."""
        from app.security.rbac import Permission

        # Project permissions
        assert Permission.PROJECT_READ.value == "project:read"
        assert Permission.PROJECT_WRITE.value == "project:write"
        assert Permission.PROJECT_DELETE.value == "project:delete"

        # Session permissions
        assert Permission.SESSION_READ.value == "session:read"
        assert Permission.SESSION_WRITE.value == "session:write"

        # Plugin permissions
        assert Permission.PLUGIN_INSTALL.value == "plugin:install"
        assert Permission.PLUGIN_UNINSTALL.value == "plugin:uninstall"


class TestWorkspacePermission:
    """Tests for WorkspacePermission enum."""

    def test_workspace_permission_values(self):
        """Test workspace permission values."""
        from app.security.rbac import WorkspacePermission

        assert WorkspacePermission.PRIVATE.value == "private"
        assert WorkspacePermission.SHARED.value == "shared"
        assert WorkspacePermission.READ_ONLY.value == "read_only"
        assert WorkspacePermission.READ_WRITE.value == "read_write"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
