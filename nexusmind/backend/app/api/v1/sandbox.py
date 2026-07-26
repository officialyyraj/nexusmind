"""Sandbox API endpoints."""

from typing import Any

from fastapi import APIRouter

from app.dependencies import AuthenticatedUser

router = APIRouter()


@router.post("/allocate")
async def allocate_sandbox(
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Allocate a sandbox instance."""
    sandbox_id = f"sand_{uuid.uuid4().hex[:12]}"
    return {"id": sandbox_id, "status": "allocated"}


@router.post("/{sandbox_id}/execute")
async def execute_code(
    sandbox_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Execute code in sandbox."""
    return {
        "execution_id": f"exec_{uuid.uuid4().hex[:8]}",
        "sandbox_id": sandbox_id,
        "stdout": "",
        "stderr": "",
        "exit_code": 0,
    }


@router.post("/{sandbox_id}/terminal")
async def terminal_command(
    sandbox_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Execute terminal command."""
    return {"sandbox_id": sandbox_id, "output": "", "exit_code": 0}


@router.get("/{sandbox_id}/files")
async def list_files(
    sandbox_id: str,
    user: AuthenticatedUser,
) -> list[dict[str, Any]]:
    """List files in sandbox."""
    return []


@router.get("/{sandbox_id}/files/{path:path}")
async def read_file(
    sandbox_id: str,
    path: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Read file from sandbox."""
    return {"sandbox_id": sandbox_id, "path": path, "content": ""}


@router.post("/{sandbox_id}/files")
async def write_file(
    sandbox_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Write file to sandbox."""
    return {"sandbox_id": sandbox_id, "path": data.get("path", ""), "written": True}


@router.delete("/{sandbox_id}")
async def release_sandbox(
    sandbox_id: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Release sandbox instance."""
    return {"id": sandbox_id, "status": "released"}
