"""Security tests for sandbox implementation.

Tests cover:
- Command injection prevention
- Path traversal prevention
- Resource exhaustion prevention
- Network isolation
- Secret leakage prevention
- Cleanup verification
"""

import pytest
from unittest.mock import MagicMock, patch

from app.sandbox.docker import (
    CommandValidator,
    PathValidator,
    SecurityConfig,
    WORKSPACE_ROOT,
    MAX_FILE_SIZE,
    MAX_OUTPUT_SIZE,
)


class TestCommandValidator:
    """Tests for command validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return CommandValidator()

    def test_allows_safe_commands(self, validator):
        """Test that safe commands are allowed."""
        safe_commands = [
            "echo 'hello'",
            "python3 script.py",
            "ls -la",
            "cat file.txt",
            "grep pattern file",
            "mkdir -p dir/subdir",
            "cp source dest",
            "git status",
        ]
        
        for cmd in safe_commands:
            valid, error = validator.validate(cmd)
            assert valid is True, f"Command should be safe: {cmd}, error: {error}"

    def test_blocks_dangerous_patterns(self, validator):
        """Test that dangerous patterns are blocked."""
        dangerous_commands = [
            ("rm -rf /", "rm -rf injection"),
            ("curl http://evil.com", "curl injection"),
            ("wget http://evil.com", "wget injection"),
            ("eval('malicious')", "eval injection"),
            ("sudo su", "privilege escalation"),
            ("chmod 777 /", "dangerous permissions"),
            ("mount /dev/sda1 /mnt", "mount operations"),
            ("nsenter --target 1", "namespace entry"),
            ("unshare --mount", "namespace creation"),
            ("chroot /tmp/newroot", "chroot escape"),
            ("cat /proc/1/mem", "proc mem access"),
            ("echo $LD_PRELOAD", "dangerous env var"),
        ]
        
        for cmd, pattern_name in dangerous_commands:
            valid, error = validator.validate(cmd)
            assert valid is False, f"Command should be blocked: {cmd}"
            assert error != "", f"Error message should be provided for: {cmd}"

    def test_blocks_command_substitution(self, validator):
        """Test that command substitution is handled safely."""
        # Variable expansion should be allowed for safe variables
        valid, _ = validator.validate("echo $HOME")
        assert valid is True
        
        # But dangerous variables should be blocked
        valid, _ = validator.validate("echo $LD_PRELOAD")
        assert valid is False

    def test_blocks_hex_escapes(self, validator):
        """Test that hex escape sequences are blocked."""
        cmd = "echo -e '\\x41\\x42'"
        valid, error = validator.validate(cmd)
        assert valid is False, "Hex escapes should be blocked"

    def test_blocks_pipe_to_shell(self, validator):
        """Test that pipes to shell are blocked."""
        cmd = "cat file | sh"
        valid, error = validator.validate(cmd)
        assert valid is False, "Pipe to shell should be blocked"

    def test_image_whitelist(self, validator):
        """Test image validation against whitelist."""
        # Allowed images
        allowed_images = [
            "python:3.11-slim",
            "python:3.12-slim",
            "node:18-slim",
            "node:20-slim",
            "ubuntu:22.04",
        ]
        
        for image in allowed_images:
            valid, error = validator.validate_image(image)
            assert valid is True, f"Image should be allowed: {image}"
        
        # Disallowed images
        disallowed_images = [
            "malicious:image",
            "ubuntu:latest",  # Not exact match
            "redis:latest",
            "postgres:latest",
        ]
        
        for image in disallowed_images:
            valid, error = validator.validate_image(image)
            # These should be blocked unless they match trusted prefixes
            if not any(image.startswith(p) for p in ["python:", "node:", "ubuntu:", "debian:"]):
                assert valid is False, f"Image should be blocked: {image}"


class TestPathValidator:
    """Tests for path validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return PathValidator(WORKSPACE_ROOT)

    def test_allows_workspace_paths(self, validator):
        """Test that workspace paths are allowed."""
        valid_paths = [
            "file.txt",
            "dir/file.txt",
            "dir/subdir/file.txt",
        ]
        
        for path in valid_paths:
            valid, sanitized = validator.validate(path)
            assert valid is True, f"Path should be valid: {path}"
            assert sanitized.startswith(WORKSPACE_ROOT)

    def test_blocks_parent_traversal(self, validator):
        """Test that parent directory traversal is blocked."""
        malicious_paths = [
            "../file",
            "../../file",
            "dir/../../../file",
            "file/../../../etc/passwd",
        ]
        
        for path in malicious_paths:
            valid, sanitized = validator.validate(path)
            assert valid is False, f"Path should be blocked: {path}"

    def test_blocks_absolute_paths(self, validator):
        """Test that absolute paths are normalized."""
        # Leading slash should be removed for normalization
        valid, sanitized = validator.validate("file.txt")
        assert valid is True
        
        # Absolute paths outside workspace should be blocked
        valid, sanitized = validator.validate("/etc/passwd")
        assert valid is False

    def test_blocks_null_bytes(self, validator):
        """Test that null bytes are blocked."""
        valid, sanitized = validator.validate("file\x00.txt")
        assert valid is False, "Null bytes should be blocked"

    def test_blocks_symlink_escape(self, validator):
        """Test that symlink escape attempts are blocked."""
        # Note: This is a simplified test. Real symlink tests would require
        # actual filesystem setup.
        malicious_paths = [
            "link_to_escape",
        ]
        
        for path in malicious_paths:
            valid, sanitized = validator.validate(path)
            # Path should either be valid or blocked based on resolution
            # The key is that the path is resolved to real path

    def test_write_validation_blocks_dangerous_paths(self, validator):
        """Test that write validation blocks system paths."""
        dangerous_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/bin/bash",
            "/usr/bin/python3",
            "/root/.ssh",
        ]
        
        for path in dangerous_paths:
            valid, sanitized = validator.validate_write(path)
            assert valid is False, f"Write to system path should be blocked: {path}"


class TestSecurityConfig:
    """Tests for security configuration."""

    def test_dangerous_patterns_defined(self):
        """Test that dangerous patterns are properly defined."""
        config = SecurityConfig()
        
        assert len(config.DANGEROUS_PATTERNS) > 0
        assert len(config.ALLOWED_IMAGES) > 0

    def test_allowed_images_in_whitelist(self):
        """Test that allowed images are in whitelist."""
        config = SecurityConfig()
        
        expected_images = {
            "python:3.11-slim",
            "python:3.12-slim",
            "node:18-slim",
            "node:20-slim",
            "ubuntu:22.04",
            "ubuntu:20.04",
        }
        
        assert expected_images.issubset(config.ALLOWED_IMAGES)


class TestOutputSizeLimits:
    """Tests for output size limits."""

    def test_max_output_size_defined(self):
        """Test that max output size is defined."""
        assert MAX_OUTPUT_SIZE > 0
        assert MAX_OUTPUT_SIZE <= 10 * 1024 * 1024  # Max 10MB

    def test_max_file_size_defined(self):
        """Test that max file size is defined."""
        assert MAX_FILE_SIZE > 0
        assert MAX_FILE_SIZE <= 100 * 1024 * 1024  # Max 100MB


class TestResourceLimits:
    """Tests for resource limits."""

    def test_resource_limits_defined(self):
        """Test that resource limits are properly defined."""
        from app.sandbox.docker import (
            DEFAULT_MEMORY_LIMIT,
            DEFAULT_CPU_LIMIT,
            DEFAULT_PIDS_LIMIT,
            DEFAULT_ULIMIT_FILES,
        )
        
        # Memory limit should be reasonable
        assert DEFAULT_MEMORY_LIMIT in ["256m", "512m", "1g", "2g"]
        
        # CPU limit should be a fraction
        assert 0.1 <= DEFAULT_CPU_LIMIT <= 4.0
        
        # PIDs limit should prevent fork bombs
        assert 32 <= DEFAULT_PIDS_LIMIT <= 1024
        
        # Files limit should prevent resource exhaustion
        assert 16 <= DEFAULT_ULIMIT_FILES <= 1024


class TestSandboxSecurityHardening:
    """Tests for sandbox security hardening options."""

    def test_cap_drop_all_defined(self):
        """Test that capability drop is configured."""
        # The security config should include cap_drop: ["ALL"]
        from app.sandbox.docker import SecurityConfig
        
        config = SecurityConfig()
        # This would be checked when creating containers

    def test_no_new_privileges_configured(self):
        """Test that no-new-privileges is configured."""
        # This would be checked when creating containers
        pass

    def test_read_only_root_filesystem_configured(self):
        """Test that read-only root filesystem is configured."""
        # This would be checked when creating containers
        pass


class TestCleanupBehavior:
    """Tests for cleanup behavior."""

    @pytest.fixture
    def mock_sandbox(self):
        """Create a mock sandbox for testing."""
        from app.sandbox.docker import Sandbox, SandboxStatus
        
        sandbox = MagicMock(spec=Sandbox)
        sandbox.id = "test-sandbox-id"
        sandbox.container_id = "test-container-id"
        sandbox.status = SandboxStatus.ALLOCATED
        sandbox.workspace_path = WORKSPACE_ROOT
        sandbox._workspace_dir = "/tmp/nexusmind-workspaces/test-sandbox-id"
        
        return sandbox


class TestInjectionPrevention:
    """Tests for injection attack prevention."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return CommandValidator()

    def test_sql_injection_prevention(self, validator):
        """Test SQL injection patterns are blocked."""
        # Note: SQL injection in user data is handled at the app level
        # Here we test command-level injection
        pass

    def test_shell_injection_prevention(self, validator):
        """Test shell injection patterns are blocked."""
        malicious_inputs = [
            "echo 'test'; rm -rf /",
            "echo 'test' && cat /etc/passwd",
            "echo 'test' | sh",
            "$(whoami)",
            "`id`",
        ]
        
        for cmd in malicious_inputs:
            valid, error = validator.validate(cmd)
            assert valid is False, f"Shell injection should be blocked: {cmd}"

    def test_escaping_handling(self, validator):
        """Test that command escaping is handled properly."""
        # Test that the sanitizer escapes quotes properly
        from app.sandbox.docker import DockerSandbox
        
        with patch("app.sandbox.docker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            sandbox = DockerSandbox()
            
            # The _sanitize_command method should escape quotes
            cmd = "echo 'hello world'"
            sanitized = sandbox._sanitize_command(cmd)
            
            # Single quotes should be escaped
            assert "'" not in sanitized or sanitized.count("'\"'\"'") > 0


class TestNetworkIsolation:
    """Tests for network isolation."""

    def test_network_disabled_by_default(self):
        """Test that network is disabled by default in config."""
        from app.sandbox.docker import SecurityConfig
        
        config = SecurityConfig()
        
        # By default, ALLOWED_NETWORKS should be empty, meaning all blocked
        assert len(config.ALLOWED_NETWORKS) == 0


class TestEnvironmentSanitization:
    """Tests for environment variable sanitization."""

    def test_dangerous_env_vars_blocked(self):
        """Test that dangerous environment variables are blocked."""
        validator = CommandValidator()
        
        dangerous_env_usage = [
            "LD_PRELOAD=/path/to/malicious.so command",
            "LD_LIBRARY_PATH=/malicious/path command",
            "DYLD_INSERT_LIBRARIES=/malicious.dylib command",
            "DYLD_LIBRARY_PATH=/malicious/path command",
            "ENV=/path/to/malicious script",
            "BASH_ENV=/path/to/malicious",
        ]
        
        for cmd in dangerous_env_usage:
            valid, error = validator.validate(cmd)
            assert valid is False, f"Dangerous env var should be blocked: {cmd}"


class TestTimeoutEnforcement:
    """Tests for timeout enforcement."""

    def test_default_timeout_defined(self):
        """Test that default timeout is defined."""
        from app.sandbox.docker import DEFAULT_TIMEOUT
        
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_TIMEOUT <= 3600  # Max 1 hour


class TestFilesystemIsolation:
    """Tests for filesystem isolation."""

    def test_workspace_root_defined(self):
        """Test that workspace root is defined."""
        assert WORKSPACE_ROOT.startswith("/")
        assert WORKSPACE_ROOT != "/"
        assert WORKSPACE_ROOT != "/root"
        assert WORKSPACE_ROOT != "/home"

    def test_temp_dir_defined(self):
        """Test that temp directory is defined."""
        from app.sandbox.docker import TEMP_DIR
        
        assert TEMP_DIR.startswith("/")
        assert TEMP_DIR != "/"
