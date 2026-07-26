"""Sessions API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import AuthenticatedUser, DbSession
from app.db.session import Session

router = APIRouter()


async def get_session_or_404(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> Session:
    """Get session by ID or raise 404."""
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
    
    # Ownership verification - users can only access their own sessions
    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this session",
        )
    
    return session


@router.get("/")
async def list_sessions(
    user: AuthenticatedUser,
    db: DbSession,
) -> list[dict[str, Any]]:
    """List all sessions for the authenticated user."""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": str(session.id),
            "title": session.title,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }
        for session in sessions
    ]


@router.post("/")
async def create_session(
    data: dict[str, Any],
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Create a new session."""
    session = Session(
        user_id=user.id,
        title=data.get("title"),
        status="created",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    
    return {
        "id": str(session.id),
        "title": session.title,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get session by ID."""
    session = await get_session_or_404(session_id, user, db)
    
    return {
        "id": str(session.id),
        "title": session.title,
        "status": session.status,
        "agent_states": session.agent_states,
        "context": session.context,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@router.patch("/{session_id}")
async def update_session(
    session_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Update session."""
    session = await get_session_or_404(session_id, user, db)
    
    if "title" in data:
        session.title = data["title"]
    if "status" in data:
        session.status = data["status"]
    if "context" in data:
        session.context = data["context"]
    
    await db.flush()
    
    return {
        "id": str(session.id),
        "updated": True,
        "title": session.title,
        "status": session.status,
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Delete session."""
    session = await get_session_or_404(session_id, user, db)
    
    await db.delete(session)
    await db.flush()
    
    return {"id": session_id, "deleted": True}


@router.post("/{session_id}/execute")
async def execute_task(
    session_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Execute task in session."""
    session = await get_session_or_404(session_id, user, db)
    
    # Update session status
    session.status = "running"
    await db.flush()
    
    return {
        "execution_id": f"exec_{uuid.uuid4().hex[:8]}",
        "session_id": session_id,
        "status": "started",
    }


@router.post("/{session_id}/stop")
async def stop_execution(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Stop session execution."""
    session = await get_session_or_404(session_id, user, db)
    
    session.status = "cancelled"
    await db.flush()
    
    return {"id": session_id, "status": "stopped"}


@router.get("/{session_id}/messages")
async def list_messages(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> list[dict[str, Any]]:
    """List session messages."""
    session = await get_session_or_404(session_id, user, db)
    
    # Messages would be fetched from the Message model
    # For now, return empty list as placeholder
    return []


@router.post("/{session_id}/messages")
async def create_message(
    session_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Create a message."""
    session = await get_session_or_404(session_id, user, db)
    
    return {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "session_id": session_id,
        "content": data.get("content", ""),
    }


@router.get("/{session_id}/agents")
async def get_agent_states(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get agent states for session."""
    session = await get_session_or_404(session_id, user, db)
    
    return {
        "session_id": session_id,
        "agents": session.agent_states or {},
    }
