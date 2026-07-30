"""Sandbox API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.dependencies import AuthenticatedUser
from app.sandbox.docker import DockerSandbox, get_sandbox, SandboxStatus
from app.api.v1.schemas import (
    SandboxAllocateRequest,
    SandboxResponse,
    ExecutionResultResponse,
    TerminalRequest,
    FileListResponse,
    FileReadResponse,
    FileWriteRequest,
    FileWriteResponse,
)

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.post("/allocate", response_model=SandboxResponse)
async def allocate_sandbox(
    data: SandboxAllocateRequest,
    user: AuthenticatedUser,
) -> SandboxResponse:
    """Allocate a new sandbox instance."""
    sandbox_service = get_sandbox()
    
    try:
        sandbox = await sandbox_service.allocate(
            image=data.image,
            workspace=data.workspace,
        )
        
        return SandboxResponse(
            id=sandbox.id,
            status=sandbox.status.value,
            container_id=sandbox.container_id,
            created_at=sandbox.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to allocate sandbox: {str(e)}",
        )


@router.get("/", response_model=list[SandboxResponse])
async def list_sandboxes(
    user: AuthenticatedUser,
) -> list[SandboxResponse]:
    """List all allocated sandbox instances."""
    sandbox_service = get_sandbox()
    sandboxes = sandbox_service.list_sandboxes()
    
    return [
        SandboxResponse(
            id=s.id,
            status=s.status.value,
            container_id=s.container_id,
            created_at=s.created_at,
        )
        for s in sandboxes
    ]


@router.post("/{sandbox_id}/execute", response_model=ExecutionResultResponse)
async def execute_code(
    sandbox_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> ExecutionResultResponse:
    """Execute code in sandbox."""
    sandbox_service = get_sandbox()
    
    # Validate sandbox exists
    sandbox_status = await sandbox_service.get_status(sandbox_id)
    if sandbox_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    command = data.get("command", "")
    timeout = data.get("timeout", 300)
    
    try:
        result = await sandbox_service.execute_with_timeout(
            sandbox_id=sandbox_id,
            command=command,
            timeout=timeout,
            workdir=data.get("workdir", "/app/workspace"),
        )
        
        return ExecutionResultResponse(
            execution_id=str(uuid.uuid4()),
            sandbox_id=sandbox_id,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            execution_time=result.execution_time,
            timed_out=result.timed_out,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}",
        )


@router.post("/{sandbox_id}/terminal")
async def terminal_command(
    sandbox_id: str,
    data: TerminalRequest,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Execute terminal command in sandbox."""
    sandbox_service = get_sandbox()
    
    # Validate sandbox exists
    sandbox_status = await sandbox_service.get_status(sandbox_id)
    if sandbox_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    try:
        result = await sandbox_service.execute_with_timeout(
            sandbox_id=sandbox_id,
            command=data.command,
            timeout=data.timeout,
            workdir=data.workdir,
        )
        
        return {
            "sandbox_id": sandbox_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "timed_out": result.timed_out,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command failed: {str(e)}",
        )


@router.get("/{sandbox_id}/files", response_model=FileListResponse)
async def list_files(
    sandbox_id: str,
    user: AuthenticatedUser,
    path: str = "/workspace",
) -> FileListResponse:
    """List files in sandbox."""
    sandbox_service = get_sandbox()
    
    # Validate sandbox exists
    sandbox_status = await sandbox_service.get_status(sandbox_id)
    if sandbox_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    try:
        files, error = await sandbox_service.list_files(sandbox_id, path)
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )
        return FileListResponse(files=files)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}",
        )


@router.get("/{sandbox_id}/files/{path:path}", response_model=FileReadResponse)
async def read_file(
    sandbox_id: str,
    path: str,
    user: AuthenticatedUser,
) -> FileReadResponse:
    """Read file from sandbox."""
    sandbox_service = get_sandbox()
    
    # Validate sandbox exists
    sandbox_status = await sandbox_service.get_status(sandbox_id)
    if sandbox_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    try:
        content, error = await sandbox_service.read_file(sandbox_id, path)
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {path}",
            )
        return FileReadResponse(
            sandbox_id=sandbox_id,
            path=path,
            content=content,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}",
        )


@router.post("/{sandbox_id}/files", response_model=FileWriteResponse)
async def write_file(
    sandbox_id: str,
    data: FileWriteRequest,
    user: AuthenticatedUser,
) -> FileWriteResponse:
    """Write file to sandbox."""
    sandbox_service = get_sandbox()
    
    # Validate sandbox exists
    sandbox_status = await sandbox_service.get_status(sandbox_id)
    if sandbox_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    try:
        success, error = await sandbox_service.write_file(
            sandbox_id=sandbox_id,
            path=data.path,
            content=data.content,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to write file",
            )
        
        return FileWriteResponse(
            sandbox_id=sandbox_id,
            path=data.path,
            written=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file: {str(e)}",
        )


@router.delete("/{sandbox_id}", response_model=SandboxResponse)
async def release_sandbox(
    sandbox_id: str,
    user: AuthenticatedUser,
) -> SandboxResponse:
    """Release sandbox instance."""
    sandbox_service = get_sandbox()
    
    try:
        success = await sandbox_service.release(sandbox_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sandbox not found: {sandbox_id}",
            )
        
        return SandboxResponse(
            id=sandbox_id,
            status="released",
            container_id=None,
            created_at=None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release sandbox: {str(e)}",
        )


@router.get("/{sandbox_id}/status")
async def get_sandbox_status(
    sandbox_id: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Get sandbox status."""
    sandbox_service = get_sandbox()
    
    status = await sandbox_service.get_status(sandbox_id)
    if status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    return {
        "id": sandbox_id,
        "status": status.value,
    }


@router.post("/{sandbox_id}/install")
async def install_packages(
    sandbox_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Install packages in sandbox."""
    sandbox_service = get_sandbox()
    
    # Validate sandbox exists
    sandbox_status = await sandbox_service.get_status(sandbox_id)
    if sandbox_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sandbox not found: {sandbox_id}",
        )
    
    packages = data.get("packages", [])
    package_manager = data.get("package_manager", "pip")
    timeout = data.get("timeout", 300)
    
    if not packages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No packages specified",
        )
    
    try:
        from app.sandbox.docker import PackageManager
        pm = PackageManager(package_manager.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package manager: {package_manager}",
        )
    
    try:
        result = await sandbox_service.install_packages(
            sandbox_id=sandbox_id,
            packages=packages,
            package_manager=pm,
            timeout=timeout,
        )
        
        return {
            "sandbox_id": sandbox_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "timed_out": result.timed_out,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Installation failed: {str(e)}",
        )
