"""Docker Sandbox Tool - Production sandbox integration.

This module provides a production-ready sandbox tool that integrates
with the Docker sandbox for secure code execution.

Features:
- Real code execution with Docker
- Structured result capture
- stdout/stderr collection
- Resource limits
- Security hardening
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.tools.registry import BaseTool, ToolHealth
from app.sandbox.docker import DockerSandbox, get_sandbox, ExecutionResult


class SandboxStatus(str, Enum):
    """Sandbox status for the tool."""
    
    IDLE = "idle"
    ALLOCATING = "allocating"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class SandboxSession:
    """Represents a sandbox execution session."""
    
    session_id: str
    sandbox_id: str | None
    status: SandboxStatus
    created_at: datetime
    last_used: datetime
    executions: int = 0


@dataclass
class ExecutionResult_:
    """Enhanced execution result."""
    
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    sandbox_id: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "sandbox_id": self.sandbox_id,
            "artifacts": self.artifacts,
            "error": self.error,
        }


class DockerSandboxTool(BaseTool):
    """Production sandbox tool with Docker integration.
    
    This tool provides:
    - Secure code execution in Docker containers
    - File system operations within sandbox
    - Structured result capture
    - Session management
    """
    
    def __init__(
        self,
        sandbox: DockerSandbox | None = None,
        default_timeout: float = 30.0,
        max_sessions: int = 10,
    ):
        super().__init__(
            name="docker_sandbox",
            description="Execute code in an isolated Docker container with security hardening",
        )
        self._sandbox = sandbox or get_sandbox()
        self._default_timeout = default_timeout
        self._max_sessions = max_sessions
        self._sessions: dict[str, SandboxSession] = {}
        self._lock = asyncio.Lock()
        self._health = ToolHealth.HEALTHY
    
    @property
    def capabilities(self) -> list[str]:
        """Get tool capabilities."""
        return [
            "code_execution",
            "file_operations",
            "terminal_commands",
            "sandbox_isolation",
            "resource_limits",
            "stdout_capture",
            "stderr_capture",
        ]
    
    async def health(self) -> ToolHealth:
        """Check tool health."""
        try:
            # Try to get sandbox status
            if self._sandbox:
                return ToolHealth.HEALTHY
            return ToolHealth.UNHEALTHY
        except Exception:
            return ToolHealth.UNHEALTHY
    
    async def can_execute(self, **kwargs) -> bool:
        """Check if tool can execute."""
        if len(self._sessions) >= self._max_sessions:
            return False
        return self._health == ToolHealth.HEALTHY
    
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute sandbox action.
        
        Supported actions:
        - allocate: Create a new sandbox session
        - release: Release a sandbox session
        - execute: Execute code in sandbox
        - write_file: Write file to sandbox
        - read_file: Read file from sandbox
        - run_command: Run shell command
        """
        action = kwargs.get("action", "execute")
        
        if action == "allocate":
            return await self._allocate_sandbox(kwargs)
        elif action == "release":
            return await self._release_sandbox(kwargs)
        elif action == "execute":
            return await self._execute_code(kwargs)
        elif action == "write_file":
            return await self._write_file(kwargs)
        elif action == "read_file":
            return await self._read_file(kwargs)
        elif action == "run_command":
            return await self._run_command(kwargs)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _allocate_sandbox(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Allocate a new sandbox session."""
        session_id = kwargs.get("session_id") or str(uuid.uuid4())
        image = kwargs.get("image", "python:3.11-slim")
        allow_network = kwargs.get("allow_network", False)
        
        # Check session limit
        async with self._lock:
            if len(self._sessions) >= self._max_sessions:
                return {
                    "success": False,
                    "error": f"Maximum sessions reached: {self._max_sessions}",
                }
        
        try:
            # Allocate sandbox
            sandbox_id, error = await self._sandbox.allocate(
                image=image,
                allow_network=allow_network,
            )
            
            if error:
                return {"success": False, "error": error}
            
            # Create session
            session = SandboxSession(
                session_id=session_id,
                sandbox_id=sandbox_id,
                status=SandboxStatus.READY,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
            )
            
            async with self._lock:
                self._sessions[session_id] = session
            
            return {
                "success": True,
                "session_id": session_id,
                "sandbox_id": sandbox_id,
                "status": session.status.value,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _release_sandbox(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Release a sandbox session."""
        session_id = kwargs.get("session_id")
        
        if not session_id:
            return {"success": False, "error": "session_id required"}
        
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if not session.sandbox_id:
                del self._sessions[session_id]
                return {"success": True, "session_id": session_id, "status": "released"}
        
        try:
            success, error = await self._sandbox.release(session.sandbox_id)
            
            async with self._lock:
                if session_id in self._sessions:
                    if success:
                        self._sessions[session_id].status = SandboxStatus.IDLE
                        self._sessions[session_id].sandbox_id = None
                    else:
                        self._sessions[session_id].status = SandboxStatus.ERROR
            
            return {
                "success": success,
                "session_id": session_id,
                "error": error,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_code(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Execute code in sandbox."""
        session_id = kwargs.get("session_id")
        code = kwargs.get("code", "")
        language = kwargs.get("language", "python")
        timeout = kwargs.get("timeout", self._default_timeout)
        
        # Get or create session
        session = None
        if session_id:
            async with self._lock:
                session = self._sessions.get(session_id)
        
        if not session or not session.sandbox_id:
            # Auto-allocate sandbox
            alloc_result = await self._allocate_sandbox(kwargs)
            if not alloc_result.get("success"):
                return alloc_result
            
            session_id = alloc_result["session_id"]
            session = self._sessions.get(session_id)
        
        if not session:
            return {"success": False, "error": "Failed to get session"}
        
        try:
            # Update session
            async with self._lock:
                session.status = SandboxStatus.BUSY
                session.last_used = datetime.utcnow()
                session.executions += 1
            
            # Determine command based on language
            if language == "python":
                command = ["python", "-c", code]
            elif language == "javascript" or language == "node":
                command = ["node", "-e", code]
            elif language == "bash" or language == "shell":
                command = ["bash", "-c", code]
            else:
                command = ["sh", "-c", code]
            
            # Execute
            result: ExecutionResult = await self._sandbox.execute(
                sandbox_id=session.sandbox_id,
                command=command,
                timeout=timeout,
            )
            
            # Format result
            execution_result = ExecutionResult_(
                success=result.exit_code == 0 and not result.timed_out,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
                execution_time=result.execution_time,
                sandbox_id=session.sandbox_id,
                timed_out=result.timed_out,
                error=f"Execution timed out after {timeout}s" if result.timed_out else None,
            )
            
            # Update session
            async with self._lock:
                session.status = SandboxStatus.READY
            
            return {
                "success": execution_result.success,
                "result": execution_result.to_dict(),
            }
            
        except Exception as e:
            async with self._lock:
                if session_id in self._sessions:
                    self._sessions[session_id].status = SandboxStatus.ERROR
            
            return {"success": False, "error": str(e)}
    
    async def _write_file(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Write file to sandbox."""
        session_id = kwargs.get("session_id")
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        
        if not session_id:
            return {"success": False, "error": "session_id required"}
        
        async with self._lock:
            session = self._sessions.get(session_id)
        
        if not session or not session.sandbox_id:
            return {"success": False, "error": "Session not found or not allocated"}
        
        try:
            success, error = await self._sandbox.write_file(
                sandbox_id=session.sandbox_id,
                path=path,
                content=content,
            )
            
            return {"success": success, "error": error}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _read_file(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Read file from sandbox."""
        session_id = kwargs.get("session_id")
        path = kwargs.get("path", "")
        
        if not session_id:
            return {"success": False, "error": "session_id required"}
        
        async with self._lock:
            session = self._sessions.get(session_id)
        
        if not session or not session.sandbox_id:
            return {"success": False, "error": "Session not found or not allocated"}
        
        try:
            content, error = await self._sandbox.read_file(
                sandbox_id=session.sandbox_id,
                path=path,
            )
            
            if error:
                return {"success": False, "error": error}
            
            return {"success": True, "content": content}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_command(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Run shell command in sandbox."""
        session_id = kwargs.get("session_id")
        command = kwargs.get("command", "")
        timeout = kwargs.get("timeout", self._default_timeout)
        
        if not session_id:
            return {"success": False, "error": "session_id required"}
        
        async with self._lock:
            session = self._sessions.get(session_id)
        
        if not session or not session.sandbox_id:
            return {"success": False, "error": "Session not found or not allocated"}
        
        try:
            result = await self._sandbox.execute(
                sandbox_id=session.sandbox_id,
                command=["sh", "-c", command],
                timeout=timeout,
            )
            
            return {
                "success": result.exit_code == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "timed_out": result.timed_out,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown and clean up all sessions."""
        async with self._lock:
            for session_id in list(self._sessions.keys()):
                if self._sessions[session_id].sandbox_id:
                    try:
                        await self._sandbox.release(self._sessions[session_id].sandbox_id)
                    except Exception:
                        pass
                del self._sessions[session_id]
    
    def get_session_info(self, session_id: str) -> dict[str, Any] | None:
        """Get information about a session."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "sandbox_id": session.sandbox_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_used": session.last_used.isoformat(),
            "executions": session.executions,
        }
    
    def list_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions."""
        return [
            self.get_session_info(sid)
            for sid in self._sessions
        ]


# Global instance
_docker_sandbox_tool: DockerSandboxTool | None = None


def get_docker_sandbox_tool() -> DockerSandboxTool:
    """Get the global Docker sandbox tool instance."""
    global _docker_sandbox_tool
    if _docker_sandbox_tool is None:
        _docker_sandbox_tool = DockerSandboxTool()
    return _docker_sandbox_tool
