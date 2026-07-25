"""Memory API endpoints."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.post("/search")
async def search_memory(data: dict[str, Any]) -> dict[str, Any]:
    """Search memory."""
    return {"results": [], "query": data.get("query", "")}


@router.post("/store")
async def store_memory(data: dict[str, Any]) -> dict[str, Any]:
    """Store memory."""
    return {"id": "mem_placeholder", "stored": True}


@router.get("/{session_id}")
async def get_session_memory(session_id: str) -> dict[str, Any]:
    """Get session memory."""
    return {"session_id": session_id, "memories": []}


@router.delete("/{session_id}")
async def clear_session_memory(session_id: str) -> dict[str, Any]:
    """Clear session memory."""
    return {"session_id": session_id, "cleared": True}
