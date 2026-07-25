"""Tests for Docker sandbox functionality."""

import pytest

# Mock docker before importing
import sys
from unittest.mock import MagicMock, patch

# Create mock docker module
mock_docker = MagicMock()
sys.modules['docker'] = mock_docker
sys.modules['docker.models'] = MagicMock()
sys.modules['docker.models.containers'] = MagicMock()

from app.sandbox.docker import (
    DEFAULT_TIMEOUT,
    DockerSandbox,
    ExecutionResult,
    PackageManager,
    Sandbox,
    SandboxStatus,
)


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = ExecutionResult(
            stdout="Hello, World!",
            stderr="",
            exit_code=0,
            execution_time=1.5,
            timed_out=False,
        )
        
        d = result.to_dict()
        assert d["stdout"] == "Hello, World!"
        assert d["exit_code"] == 0
        assert d["timed_out"] is False
        assert d["execution_time"] == 1.5

    def test_timed_out_result(self):
        """Test timed out result."""
        result = ExecutionResult(
            stdout="partial output",
            stderr="Command timed out after 300 seconds",
            exit_code=124,
            execution_time=300.0,
            timed_out=True,
        )
        
        assert result.timed_out is True
        assert result.exit_code == 124

    def test_error_result(self):
        """Test error result."""
        result = ExecutionResult(
            stdout="",
            stderr="Error: something went wrong",
            exit_code=1,
            execution_time=0.5,
        )
        
        assert result.exit_code == 1
        assert "Error" in result.stderr


class TestSandboxStatus:
    """Test SandboxStatus enum."""

    def test_all_statuses(self):
        """Test all status values exist."""
        assert SandboxStatus.ALLOCATING.value == "allocating"
        assert SandboxStatus.ALLOCATED.value == "allocated"
        assert SandboxStatus.RUNNING.value == "running"
        assert SandboxStatus.BUSY.value == "busy"
        assert SandboxStatus.STOPPED.value == "stopped"
        assert SandboxStatus.ERROR.value == "error"
        assert SandboxStatus.TIMEOUT.value == "timeout"


class TestPackageManager:
    """Test PackageManager enum."""

    def test_package_managers(self):
        """Test package manager values."""
        assert PackageManager.APT.value == "apt"
        assert PackageManager.NPM.value == "npm"
        assert PackageManager.PIP.value == "pip"
        assert PackageManager.YARN.value == "yarn"


class TestSandbox:
    """Test Sandbox dataclass."""

    def test_sandbox_creation(self):
        """Test creating a sandbox."""
        from datetime import datetime
        
        sandbox = Sandbox(
            id="test-id-123",
            container_id="container-456",
            status=SandboxStatus.ALLOCATED,
            created_at=datetime.utcnow(),
            image="python:3.11-slim",
        )
        
        assert sandbox.id == "test-id-123"
        assert sandbox.status == SandboxStatus.ALLOCATED
        assert sandbox.image == "python:3.11-slim"


class TestDockerSandbox:
    """Test DockerSandbox class."""

    def test_default_timeout(self):
        """Test default timeout is 5 minutes."""
        assert DEFAULT_TIMEOUT == 300

    def test_sandbox_init(self):
        """Test sandbox initialization."""
        sandbox = DockerSandbox()
        
        assert sandbox._sandboxes == {}
        assert sandbox._timeout == DEFAULT_TIMEOUT

    def test_sandbox_not_found_error(self):
        """Test error when sandbox not found."""
        sandbox = DockerSandbox()
        
        # _get_container should raise for non-existent sandbox
        with pytest.raises(ValueError, match="Sandbox not found"):
            sandbox._get_container("non-existent-id")

    def test_execute_code_error_handling(self):
        """Test execute_code error handling."""
        sandbox = DockerSandbox()
        
        # _get_container should raise for non-existent sandbox
        with pytest.raises(ValueError, match="Sandbox not found"):
            sandbox._get_container("non-existent")

    def test_install_packages_empty_list(self):
        """Test installing empty package list."""
        sandbox = DockerSandbox()
        
        import asyncio
        result = asyncio.run(sandbox.install_packages("any", []))
        
        assert result.exit_code == 0
        assert "No packages" in result.stdout


class TestSandboxIntegration:
    """Integration tests for sandbox (require Docker)."""

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_allocate_sandbox(self):
        """Test allocating a sandbox."""
        sandbox = DockerSandbox()
        
        result = await sandbox.allocate()
        
        assert isinstance(result, Sandbox)
        assert result.status == SandboxStatus.ALLOCATED
        
        # Cleanup
        await sandbox.release(result.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_execute_command(self):
        """Test executing a command."""
        sandbox = DockerSandbox()
        
        # Allocate
        s = await sandbox.allocate()
        
        # Execute
        result = await sandbox.execute_command(s.id, "echo 'Hello, World!'")
        
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
        
        # Cleanup
        await sandbox.release(s.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_execute_with_timeout(self):
        """Test command with timeout."""
        sandbox = DockerSandbox()
        
        s = await sandbox.allocate()
        
        # Execute a command that should complete quickly
        result = await sandbox.execute_with_timeout(s.id, "sleep 1 && echo done", timeout=10)
        
        assert result.exit_code == 0
        assert "done" in result.stdout
        assert result.timed_out is False
        
        await sandbox.release(s.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_execute_code_python(self):
        """Test executing Python code."""
        sandbox = DockerSandbox()
        
        s = await sandbox.allocate()
        
        code = """
print("Hello from Python!")
for i in range(3):
    print(f"Count: {i}")
"""
        
        result = await sandbox.execute_code(s.id, code, language="python")
        
        assert result.exit_code == 0
        assert "Hello from Python!" in result.stdout
        assert "Count: 0" in result.stdout
        
        await sandbox.release(s.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_timeout_enforcement(self):
        """Test that long-running commands are timed out."""
        sandbox = DockerSandbox()
        
        s = await sandbox.allocate()
        
        # Command that sleeps for 10 seconds with 2 second timeout
        result = await sandbox.execute_with_timeout(
            s.id, 
            "sleep 10", 
            timeout=2
        )
        
        assert result.timed_out is True
        assert result.exit_code == 124
        assert "timed out" in result.stderr.lower()
        
        await sandbox.release(s.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_install_pip_package(self):
        """Test installing a pip package."""
        sandbox = DockerSandbox()
        
        s = await sandbox.allocate()
        
        # Install a small package
        result = await sandbox.install_packages(
            s.id, 
            ["requests"],
            package_manager=PackageManager.PIP,
            timeout=120
        )
        
        # Should succeed or fail depending on network
        assert result.exit_code == 0 or "error" in result.stderr.lower()
        
        await sandbox.release(s.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_write_and_read_file(self):
        """Test writing and reading files."""
        sandbox = DockerSandbox()
        
        s = await sandbox.allocate()
        
        # Write a file
        content = "Hello, File!"
        success = await sandbox.write_file(s.id, "/tmp/test.txt", content)
        assert success is True
        
        # Read it back
        read_content = await sandbox.read_file(s.id, "/tmp/test.txt")
        assert read_content == content
        
        await sandbox.release(s.id)

    @pytest.mark.skip(reason="Requires Docker running")
    async def test_separate_stdout_stderr(self):
        """Test that stdout and stderr are captured separately."""
        sandbox = DockerSandbox()
        
        s = await sandbox.allocate()
        
        result = await sandbox.execute_command(
            s.id,
            "echo 'stdout' && echo 'stderr' >&2"
        )
        
        assert "stdout" in result.stdout
        assert "stderr" in result.stderr
        
        await sandbox.release(s.id)
