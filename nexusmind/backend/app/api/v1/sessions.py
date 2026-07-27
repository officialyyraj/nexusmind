"""Sessions API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import AuthenticatedUser, DbSession
from app.db.session import Session, SessionStatus
from app.db.message import Message, MessageRole
from app.api.v1.schemas import (
    SessionResponse,
    SessionDetailResponse,
    SessionCreate,
    SessionUpdate,
    ExecutionRequest,
    ExecutionResponse,
    MessageResponse,
    MessageCreate,
    AgentStatesResponse,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


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


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    user: AuthenticatedUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[SessionResponse]:
    """List all sessions for the authenticated user."""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return [
        SessionResponse(
            id=str(session.id),
            title=session.title,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        for session in sessions
    ]


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    user: AuthenticatedUser,
    db: DbSession,
) -> SessionResponse:
    """Create a new session."""
    session = Session(
        user_id=user.id,
        title=data.title,
        status=SessionStatus.CREATED.value,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> SessionDetailResponse:
    """Get session by ID."""
    session = await get_session_or_404(session_id, user, db)
    
    return SessionDetailResponse(
        id=str(session.id),
        title=session.title,
        status=session.status,
        agent_states=session.agent_states or {},
        context=session.context or {},
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    user: AuthenticatedUser,
    db: DbSession,
) -> SessionResponse:
    """Update session."""
    session = await get_session_or_404(session_id, user, db)
    
    if data.title is not None:
        session.title = data.title
    if data.status is not None:
        session.status = data.status
    if data.context is not None:
        session.context = data.context
    
    await db.flush()
    await db.refresh(session)
    
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> None:
    """Delete session and all associated data (messages, artifacts, etc.)."""
    session = await get_session_or_404(session_id, user, db)
    
    await db.delete(session)
    await db.flush()


@router.post("/{session_id}/execute", response_model=ExecutionResponse)
async def execute_task(
    session_id: str,
    data: ExecutionRequest,
    user: AuthenticatedUser,
    db: DbSession,
) -> ExecutionResponse:
    """Execute a task in the session using the agent workflow.
    
    This endpoint triggers the full agent orchestration pipeline:
    - Planner: decomposes task into steps
    - Researcher: gathers context and information
    - Coder: implements the solution
    - Reviewer: reviews code quality
    - Tester: validates functionality
    
    The execution runs asynchronously and results are persisted to the database.
    Progress can be monitored via WebSocket connection.
    """
    session = await get_session_or_404(session_id, user, db)
    
    # Import the executor
    from app.orchestration.executor import get_executor
    
    executor = get_executor()
    
    # Execute the task asynchronously
    execution_id = await executor.execute(
        session_id=session_id,
        task=data.task,
        db=db,
        prompt=data.prompt,
        agent_types=data.agent_types,
    )
    
    return ExecutionResponse(
        execution_id=execution_id,
        session_id=session_id,
        status="started",
    )


@router.post("/{session_id}/stop", response_model=SessionResponse)
async def stop_execution(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    execution_id: str | None = None,
) -> SessionResponse:
    """Stop session execution.
    
    If execution_id is provided, cancels that specific execution.
    Otherwise, cancels any running execution for this session.
    """
    session = await get_session_or_404(session_id, user, db)
    
    # Try to cancel via executor if execution_id provided
    if execution_id:
        from app.orchestration.executor import get_executor
        executor = get_executor()
        await executor.cancel(execution_id)
    
    # Update session status
    session.status = SessionStatus.CANCELLED.value
    await db.flush()
    await db.refresh(session)
    
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    limit: int = 100,
    offset: int = 0,
) -> list[MessageResponse]:
    """List session messages with pagination."""
    session = await get_session_or_404(session_id, user, db)
    
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        MessageResponse(
            id=str(msg.id),
            session_id=session_id,
            role=msg.role,
            content=msg.content,
            agent_type=msg.agent_type,
            metadata=msg.msg_metadata or {},
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_id: str,
    data: MessageCreate,
    user: AuthenticatedUser,
    db: DbSession,
) -> MessageResponse:
    """Create a message in the session."""
    session = await get_session_or_404(session_id, user, db)
    
    # Validate role
    try:
        MessageRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {data.role}. Must be one of: {[r.value for r in MessageRole]}",
        )
    
    message = Message(
        session_id=session.id,
        role=data.role,
        content=data.content,
        agent_type=data.agent_type,
        msg_metadata=data.metadata,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    
    return MessageResponse(
        id=str(message.id),
        session_id=session_id,
        role=message.role,
        content=message.content,
        agent_type=message.agent_type,
        metadata=message.msg_metadata or {},
        created_at=message.created_at,
    )


@router.get("/{session_id}/agents", response_model=AgentStatesResponse)
async def get_agent_states(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> AgentStatesResponse:
    """Get agent states for session."""
    session = await get_session_or_404(session_id, user, db)
    
    return AgentStatesResponse(
        session_id=session_id,
        agents=session.agent_states or {},
    )


@router.patch("/{session_id}/agents/{agent_type}", response_model=SessionResponse)
async def update_agent_state(
    session_id: str,
    agent_type: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
    db: DbSession,
) -> SessionResponse:
    """Update a specific agent's state in the session."""
    session = await get_session_or_404(session_id, user, db)
    
    # Initialize agent_states if needed
    if session.agent_states is None:
        session.agent_states = {}
    
    # Update the specific agent's state
    if agent_type not in session.agent_states:
        session.agent_states[agent_type] = {}
    session.agent_states[agent_type].update(data)
    
    await db.flush()
    await db.refresh(session)
    
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
