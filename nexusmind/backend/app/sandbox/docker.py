"""Docker sandbox for code execution."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import docker

from app.config import get_settings


class SandboxStatus(str, Enum):
    """Sandbox status."""

    ALLOCATED = "allocated"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Result of code execution."""

    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    artifacts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Sandbox:
    """Sandbox instance."""

    id: str
    container_id: str
    status: SandboxStatus
    created_at: datetime


class DockerSandbox:
    """Docker-based sandbox for code execution."""

    def __init__(self):
        self.settings = get_settings()
        self.client = docker.from_env()
        self._sandboxes: dict[str, Sandbox] = {}

    async def allocate(self) -> Sandbox:
        """Allocate a new sandbox."""
        sandbox_id = str(uuid.uuid4())

        try:
            container = self.client.containers.run(
                self.settings.sandbox_docker_image,
                detach=True,
                mem_limit="512m",
                network_disabled=False,
                working_dir="/app/workspace",
            )

            sandbox = Sandbox(
                id=sandbox_id,
                container_id=container.id,
                status=SandboxStatus.ALLOCATED,
                created_at=datetime.utcnow(),
            )
            self._sandboxes[sandbox_id] = sandbox
            return sandbox

        except docker.errors.ImageNotFound:
            container = self.client.containers.run(
                "python:3.11-slim",
                detach=True,
                mem_limit="512m",
                command="sleep infinity",
                working_dir="/app/workspace",
            )

            sandbox = Sandbox(
                id=sandbox_id,
                container_id=container.id,
                status=SandboxStatus.ALLOCATED,
                created_at=datetime.utcnow(),
            )
            self._sandboxes[sandbox_id] = sandbox
            return sandbox

    async def execute(
        self,
        sandbox_id: str,
        code: str,
        language: str = "python",
        timeout: int = 30,
    ) -> ExecutionResult:
        """Execute code in sandbox."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox not found: {sandbox_id}")

        start_time = datetime.utcnow()

        try:
            container = self.client.containers.get(sandbox.container_id)

            # Write code to container
            encoded_code = code.encode().hex()
            container.exec_run(
                f"sh -c 'echo {encoded_code} | xxd -r -p > /tmp/execute.py'"
            )

            # Execute code
            if language == "python":
                exec_result = container.exec_run(
                    f"timeout {timeout} python3 /tmp/execute.py",
                    workdir="/app/workspace",
                )
            else:
                exec_result = container.exec_run(
                    f"timeout {timeout} bash /tmp/execute.py",
                    workdir="/app/workspace",
                )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return ExecutionResult(
                stdout=exec_result.output.decode("utf-8", errors="replace"),
                stderr="",
                exit_code=exec_result.exit_code,
                execution_time=execution_time,
            )

        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                exit_code=124,
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                stdout="",
                stderr=str(e),
                exit_code=1,
                execution_time=execution_time,
            )

    async def release(self, sandbox_id: str) -> bool:
        """Release a sandbox."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return False

        try:
            container = self.client.containers.get(sandbox.container_id)
            container.stop(timeout=5)
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


_sandbox: DockerSandbox | None = None


def get_sandbox() -> DockerSandbox:
    """Get the global sandbox instance."""
    global _sandbox
    if _sandbox is None:
        _sandbox = DockerSandbox()
    return _sandbox
