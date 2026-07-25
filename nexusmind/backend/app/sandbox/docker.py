"""Docker sandbox for code execution with command execution, package installation, and timeout support."""

import asyncio
import base64
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator

import docker
from docker.models.containers import Container

from app.config import get_settings


# Default timeout: 5 minutes (300 seconds)
DEFAULT_TIMEOUT = 300


class SandboxStatus(str, Enum):
    """Sandbox status."""

    ALLOCATING = "allocating"
    ALLOCATED = "allocated"
    RUNNING = "running"
    BUSY = "busy"
    STOPPED = "stopped"
    ERROR = "error"
    TIMEOUT = "timeout"


class PackageManager(str, Enum):
    """Supported package managers."""

    APT = "apt"
    NPM = "npm"
    PIP = "pip"
    YARN = "yarn"


@dataclass
class ExecutionResult:
    """Result of code/command execution."""

    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timed_out: bool = False
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "timed_out": self.timed_out,
            "artifacts": self.artifacts,
        }


@dataclass
class Sandbox:
    """Sandbox instance."""

    id: str
    container_id: str
    status: SandboxStatus
    created_at: datetime
    image: str


class DockerSandbox:
    """Docker-based sandbox for code execution with full capabilities."""

    def __init__(self):
        self.settings = get_settings()
        self.client = docker.from_env()
        self._sandboxes: dict[str, Sandbox] = {}
        self._timeout = DEFAULT_TIMEOUT

    def _get_container(self, sandbox_id: str) -> Container:
        """Get container by sandbox ID."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox not found: {sandbox_id}")
        return self.client.containers.get(sandbox.container_id)

    async def allocate(
        self,
        image: str | None = None,
        workspace: str = "/app/workspace",
    ) -> Sandbox:
        """Allocate a new sandbox container."""
        sandbox_id = str(uuid.uuid4())
        image = image or self.settings.sandbox_docker_image

        try:
            container = self.client.containers.run(
                image,
                detach=True,
                mem_limit="1g",
                cpu_period=100000,
                cpu_quota=100000,
                network_disabled=False,
                working_dir=workspace,
                command="sleep infinity",
            )

            sandbox = Sandbox(
                id=sandbox_id,
                container_id=container.id,
                status=SandboxStatus.ALLOCATED,
                created_at=datetime.utcnow(),
                image=image,
            )
            self._sandboxes[sandbox_id] = sandbox
            return sandbox

        except docker.errors.ImageNotFound:
            # Fall back to Python image
            container = self.client.containers.run(
                "python:3.11-slim",
                detach=True,
                mem_limit="1g",
                network_disabled=False,
                working_dir=workspace,
                command="sleep infinity",
            )

            sandbox = Sandbox(
                id=sandbox_id,
                container_id=container.id,
                status=SandboxStatus.ALLOCATED,
                created_at=datetime.utcnow(),
                image="python:3.11-slim",
            )
            self._sandboxes[sandbox_id] = sandbox
            return sandbox

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
        workdir: str = "/app/workspace",
    ) -> ExecutionResult:
        """Execute a shell command and capture stdout/stderr.
        
        Args:
            sandbox_id: The sandbox ID
            command: Shell command to execute
            timeout: Timeout in seconds (default: 300 = 5 minutes)
            workdir: Working directory for the command
            
        Returns:
            ExecutionResult with stdout, stderr, exit_code, and timing
        """
        start_time = datetime.utcnow()

        try:
            container = self._get_container(sandbox_id)

            # Use exec_run with stream=False to capture output
            result = container.exec_run(
                f"bash -c '{command}'",
                workdir=workdir,
                demux=True,
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Handle demuxed output (separate stdout/stderr)
            stdout = ""
            stderr = ""
            if result.output:
                if isinstance(result.output, tuple):
                    stdout_bytes, stderr_bytes = result.output
                    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
                else:
                    stdout = result.output.decode("utf-8", errors="replace")

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=result.exit_code,
                execution_time=execution_time,
                timed_out=False,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=execution_time,
                timed_out=False,
            )

    async def execute_with_timeout(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
        workdir: str = "/app/workspace",
    ) -> ExecutionResult:
        """Execute a command with timeout enforcement.
        
        Uses the `timeout` command internally to enforce timeout.
        Returns special result if command times out.
        """
        start_time = datetime.utcnow()

        try:
            container = self._get_container(sandbox_id)

            # Wrap command with timeout
            timeout_command = f"timeout {timeout} bash -c '{command}'"

            result = container.exec_run(
                timeout_command,
                workdir=workdir,
                demux=True,
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Check if timed out (exit code 124 from timeout command)
            timed_out = result.exit_code == 124

            stdout = ""
            stderr = ""
            if result.output:
                if isinstance(result.output, tuple):
                    stdout_bytes, stderr_bytes = result.output
                    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
                else:
                    stdout = result.output.decode("utf-8", errors="replace")

            if timed_out:
                stderr = f"Command timed out after {timeout} seconds\n" + stderr

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=result.exit_code,
                execution_time=execution_time,
                timed_out=timed_out,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=execution_time,
            )

    async def execute_code(
        self,
        sandbox_id: str,
        code: str,
        language: str = "python",
        timeout: int = DEFAULT_TIMEOUT,
        workdir: str = "/app/workspace",
    ) -> ExecutionResult:
        """Execute code in the sandbox.
        
        Args:
            sandbox_id: The sandbox ID
            code: Code to execute
            language: Programming language (python, bash, node)
            timeout: Timeout in seconds (default: 300 = 5 minutes)
            workdir: Working directory
            
        Returns:
            ExecutionResult with stdout/stderr captured
        """
        start_time = datetime.utcnow()

        # Encode code to safe format
        encoded_code = base64.b64encode(code.encode()).decode()

        try:
            container = self._get_container(sandbox_id)

            # Decode and write code, then execute with timeout
            if language == "python":
                cmd = f"echo '{encoded_code}' | base64 -d > /tmp/execute.py && timeout {timeout} python3 /tmp/execute.py"
            elif language == "bash":
                cmd = f"echo '{encoded_code}' | base64 -d > /tmp/execute.sh && chmod +x /tmp/execute.sh && timeout {timeout} bash /tmp/execute.sh"
            elif language == "node":
                cmd = f"echo '{encoded_code}' | base64 -d > /tmp/execute.js && timeout {timeout} node /tmp/execute.js"
            elif language == "typescript":
                cmd = f"echo '{encoded_code}' | base64 -d > /tmp/execute.ts && timeout {timeout} npx ts-node /tmp/execute.ts"
            else:
                cmd = f"echo '{encoded_code}' | base64 -d > /tmp/execute && chmod +x /tmp/execute && timeout {timeout} /tmp/execute"

            result = container.exec_run(
                f"bash -c '{cmd}'",
                workdir=workdir,
                demux=True,
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            timed_out = result.exit_code == 124

            stdout = ""
            stderr = ""
            if result.output:
                if isinstance(result.output, tuple):
                    stdout_bytes, stderr_bytes = result.output
                    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
                else:
                    stdout = result.output.decode("utf-8", errors="replace")

            if timed_out:
                stderr = f"Execution timed out after {timeout} seconds\n" + stderr

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=result.exit_code,
                execution_time=execution_time,
                timed_out=timed_out,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=execution_time,
            )

    async def install_packages(
        self,
        sandbox_id: str,
        packages: list[str],
        package_manager: PackageManager = PackageManager.PIP,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ExecutionResult:
        """Install packages in the sandbox.
        
        Args:
            sandbox_id: The sandbox ID
            packages: List of package names to install
            package_manager: Package manager to use (apt, npm, pip, yarn)
            timeout: Timeout in seconds
            
        Returns:
            ExecutionResult with installation output
        """
        start_time = datetime.utcnow()

        if not packages:
            return ExecutionResult(
                stdout="No packages to install",
                stderr="",
                exit_code=0,
                execution_time=0,
            )

        try:
            container = self._get_container(sandbox_id)

            if package_manager == PackageManager.PIP:
                cmd = f"pip install {' '.join(packages)} --quiet"
            elif package_manager == PackageManager.NPM:
                cmd = f"npm install {' '.join(packages)}"
            elif package_manager == PackageManager.YARN:
                cmd = f"yarn add {' '.join(packages)}"
            elif package_manager == PackageManager.APT:
                # Update and install
                cmd = f"apt-get update -qq && apt-get install -y -qq {' '.join(packages)}"
            else:
                return ExecutionResult(
                    stdout="",
                    stderr=f"Unknown package manager: {package_manager}",
                    exit_code=1,
                    execution_time=0,
                )

            # Wrap with timeout
            result = container.exec_run(
                f"timeout {timeout} bash -c '{cmd}'",
                demux=True,
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            timed_out = result.exit_code == 124

            stdout = ""
            stderr = ""
            if result.output:
                if isinstance(result.output, tuple):
                    stdout_bytes, stderr_bytes = result.output
                    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
                else:
                    stdout = result.output.decode("utf-8", errors="replace")

            if timed_out:
                stderr = f"Installation timed out after {timeout} seconds\n" + stderr

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=result.exit_code,
                execution_time=execution_time,
                timed_out=timed_out,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                stdout="",
                stderr=f"Installation error: {str(e)}",
                exit_code=1,
                execution_time=execution_time,
            )

    async def stream_execute(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream command output line by line.
        
        Yields events with stdout/stderr chunks.
        """
        try:
            container = self._get_container(sandbox_id)

            # Create exec instance for streaming
            exec_id = container.exec_create(
                f"timeout {timeout} bash -c '{command}'",
                demux=True,
                stream=True,
            )

            # Get output stream
            socket = container.client.api.exec_start(exec_id, socket=True)

            import select

            # Stream with non-blocking reads
            start_time = datetime.utcnow()
            while True:
                readable, _, _ = select.select([socket], [], [], 1.0)

                if readable:
                    data = socket.recv(4096)
                    if not data:
                        break

                    # Yield chunk
                    yield {
                        "type": "output",
                        "data": data.decode("utf-8", errors="replace"),
                        "time": (datetime.utcnow() - start_time).total_seconds(),
                    }

                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > timeout:
                    yield {
                        "type": "timeout",
                        "message": f"Execution timed out after {timeout} seconds",
                        "time": elapsed,
                    }
                    break

            socket.close()

            yield {
                "type": "complete",
                "time": (datetime.utcnow() - start_time).total_seconds(),
            }

        except Exception as e:
            yield {
                "type": "error",
                "message": str(e),
            }

    async def write_file(
        self,
        sandbox_id: str,
        path: str,
        content: str,
    ) -> bool:
        """Write a file to the sandbox."""
        try:
            container = self._get_container(sandbox_id)
            encoded = base64.b64encode(content.encode()).decode()
            cmd = f"echo '{encoded}' | base64 -d > {path}"
            container.exec_run(cmd)
            return True
        except Exception:
            return False

    async def read_file(
        self,
        sandbox_id: str,
        path: str,
    ) -> str | None:
        """Read a file from the sandbox."""
        try:
            container = self._get_container(sandbox_id)
            result = container.exec_run(f"cat {path}")
            return result.output.decode("utf-8", errors="replace")
        except Exception:
            return None

    async def list_files(
        self,
        sandbox_id: str,
        path: str = "/app/workspace",
    ) -> list[dict[str, Any]]:
        """List files in a directory."""
        try:
            container = self._get_container(sandbox_id)
            cmd = f"find {path} -type f -o -type d | head -100"
            result = container.exec_run(cmd)
            files = result.output.decode("utf-8", errors="replace").strip().split("\n")
            return [{"path": f, "type": "dir" if f.endswith("/") else "file"} for f in files if f]
        except Exception:
            return []

    async def release(self, sandbox_id: str) -> bool:
        """Release a sandbox (stop and remove container)."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return False

        try:
            container = self.client.containers.get(sandbox.container_id)
            container.stop(timeout=10)
            container.remove(force=True)
            del self._sandboxes[sandbox_id]
            return True
        except Exception:
            return False

    async def get_status(self, sandbox_id: str) -> SandboxStatus | None:
        """Get sandbox status."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return None

        try:
            container = self.client.containers.get(sandbox.container_id)
            if container.status == "running":
                sandbox.status = SandboxStatus.RUNNING
            elif container.status == "exited":
                sandbox.status = SandboxStatus.STOPPED
            return sandbox.status
        except Exception:
            sandbox.status = SandboxStatus.ERROR
            return sandbox.status

    async def pause(self, sandbox_id: str) -> bool:
        """Pause a sandbox."""
        try:
            container = self._get_container(sandbox_id)
            container.pause()
            return True
        except Exception:
            return False

    async def unpause(self, sandbox_id: str) -> bool:
        """Unpause a sandbox."""
        try:
            container = self._get_container(sandbox_id)
            container.unpause()
            return True
        except Exception:
            return False

    def list_sandboxes(self) -> list[Sandbox]:
        """List all allocated sandboxes."""
        return list(self._sandboxes.values())


_sandbox: DockerSandbox | None = None


def get_sandbox() -> DockerSandbox:
    """Get the global sandbox instance."""
    global _sandbox
    if _sandbox is None:
        _sandbox = DockerSandbox()
    return _sandbox
