"""Sandbox API endpoints."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.post("/allocate")
async def allocate_sandbox() -> dict[str, Any]:
    """Allocate a sandbox instance."""
    return {"id": "sand_placeholder", "status": "allocated"}


@router.post("/{sandbox_id}/execute")
async def execute_code(
    sandbox_id: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Execute code in sandbox."""
    return {
        "execution_id": "exec_placeholder",
        "stdout": "",
        "stderr": "",
        "exit_code": 0,
    }


@router.post("/{sandbox_id}/terminal")
async def terminal_command(
    sandbox_id: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Execute terminal command."""
    return {"output": "", "exit_code": 0}


@router.get("/{sandbox_id}/files")
async def list_files(sandbox_id: str) -> list[dict[str, Any]]:
    """List files in sandbox."""
    return []


@router.get("/{sandbox_id}/files/{path:path}")
async def read_file(sandbox_id: str, path: str) -> dict[str, Any]:
    """Read file from sandbox."""
    return {"path": path, "content": ""}


@router.post("/{sandbox_id}/files")
async def write_file(
    sandbox_id: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Write file to sandbox."""
    return {"path": data.get("path", ""), "written": True}


@router.delete("/{sandbox_id}")
async def release_sandbox(sandbox_id: str) -> dict[str, Any]:
    """Release sandbox instance."""
    return {"id": sandbox_id, "status": "released"}
