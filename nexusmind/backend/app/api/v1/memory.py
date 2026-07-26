"""Memory API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import AuthenticatedUser, DbSession
from app.db.session import Session

router = APIRouter()


async def verify_session_ownership(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> Session:
    """Verify user owns the session for memory operations."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )
    
    result = await db.execute(
        select(Session).where(Session.id == session_uuid)
    )
    session = result.scalar_one_or_none()
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this session",
        )
    
    return session


@router.post("/search")
async def search_memory(
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Search memory."""
    # Memory search would query ChromaDB here
    # For now, return placeholder
    return {"results": [], "query": data.get("query", "")}


@router.post("/store")
async def store_memory(
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Store memory."""
    # Memory storage would store to ChromaDB here
    # For now, return placeholder
    return {"id": f"mem_{uuid.uuid4().hex[:8]}", "stored": True}


@router.get("/{session_id}")
async def get_session_memory(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get session memory."""
    # Verify ownership first
    await verify_session_ownership(session_id, user, db)
    return {"session_id": session_id, "memories": []}


@router.delete("/{session_id}")
async def clear_session_memory(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Clear session memory."""
    # Verify ownership first
    await verify_session_ownership(session_id, user, db)
    return {"session_id": session_id, "cleared": True}
