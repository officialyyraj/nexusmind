"""Sessions API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/")
async def list_sessions() -> list[dict[str, Any]]:
    """List all sessions."""
    return []


@router.post("/")
async def create_session(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new session."""
    return {"id": "sess_placeholder", "status": "created"}


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Get session by ID."""
    return {"id": session_id, "status": "created"}


@router.patch("/{session_id}")
async def update_session(session_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Update session."""
    return {"id": session_id, "updated": True}


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict[str, Any]:
    """Delete session."""
    return {"id": session_id, "deleted": True}


@router.post("/{session_id}/execute")
async def execute_task(session_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Execute task in session."""
    return {"execution_id": "exec_placeholder", "status": "started"}


@router.post("/{session_id}/stop")
async def stop_execution(session_id: str) -> dict[str, Any]:
    """Stop session execution."""
    return {"id": session_id, "status": "stopped"}


@router.get("/{session_id}/messages")
async def list_messages(session_id: str) -> list[dict[str, Any]]:
    """List session messages."""
    return []


@router.post("/{session_id}/messages")
async def create_message(session_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Create a message."""
    return {"id": "msg_placeholder", "session_id": session_id}


@router.get("/{session_id}/agents")
async def get_agent_states(session_id: str) -> dict[str, Any]:
    """Get agent states for session."""
    return {"session_id": session_id, "agents": {}}
