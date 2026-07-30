"""Execution API endpoints for managing agent workflow executions."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func

from app.dependencies import AuthenticatedUser, DbSession
from app.orchestration.executor import get_executor
from app.api.v1.schemas import (
    ExecutionResponse,
    ExecutionDetailResponse,
    ExecutionStepResponse,
    ExecutionLogResponse,
    ExecutionListResponse,
    ExecutionCreateRequest,
    ExecutionCancelRequest,
    ExecutionRetryResponse,
)


router = APIRouter(prefix="/executions", tags=["executions"])


async def get_execution_or_404(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
):
    """Get execution by ID or raise 404."""
    try:
        execution_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid execution ID format",
        )
    
    # Import here to avoid circular import
    from app.db.execution import Execution
    from app.db.session import Session
    
    # Get execution with session to verify ownership
    result = await db.execute(
        select(Execution, Session)
        .join(Session, Execution.session_id == Session.id)
        .where(Execution.id == execution_uuid)
    )
    row = result.first()
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    
    execution, session = row
    
    # Ownership verification
    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this execution",
        )
    
    return execution


def execution_to_response(execution) -> ExecutionResponse:
    """Convert execution model to response."""
    progress = int(
        (execution.current_step_index / max(execution.total_steps, 1)) * 100
    ) if execution.total_steps > 0 else 0
    
    return ExecutionResponse(
        id=str(execution.id),
        session_id=str(execution.session_id),
        workflow_id=execution.workflow_id,
        task=execution.task,
        state=execution.state,
        current_agent=execution.current_agent,
        current_step_index=execution.current_step_index,
        total_steps=execution.total_steps,
        progress_percent=progress,
        retry_count=execution.retry_count,
        max_retries=execution.max_retries,
        duration_seconds=execution.duration_seconds,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        error=execution.error,
        error_type=execution.error_details.get("type") if execution.error_details else None,
        is_cancelled=execution.is_cancelled,
        can_retry=execution.can_retry,
        created_at=execution.created_at,
    )


def execution_to_detail_response(execution) -> ExecutionDetailResponse:
    """Convert execution model to detailed response."""
    from app.db.execution import Execution
    
    response = execution_to_response(execution)
    
    return ExecutionDetailResponse(
        **response.model_dump(),
        prompt=execution.prompt,
        agent_types=execution.agent_types,
        previous_state=execution.previous_state,
        state_changed_at=execution.state_changed_at,
        last_checkpoint_at=execution.last_checkpoint_at,
        checkpoint_data=execution.checkpoint_data,
        result=execution.result,
        error_details=execution.error_details,
        retry_history=execution.retry_history,
        agent_timings=execution.agent_timings,
        cancelled_at=execution.cancelled_at,
        cancelled_by=execution.cancelled_by,
        metadata=execution.exec_metadata,
    )


@router.post("/", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    data: ExecutionCreateRequest,
    user: AuthenticatedUser,
    db: DbSession,
) -> ExecutionResponse:
    """Create and start a new execution.
    
    This endpoint creates an execution record and starts the workflow
    in the background. The execution runs asynchronously and can be
    monitored via WebSocket or polling the GET endpoint.
    """
    from app.db.execution import Execution, ExecutionState
    from app.db.session import Session
    
    # Validate session exists and user owns it
    try:
        session_uuid = uuid.UUID(data.session_id) if hasattr(data, 'session_id') and data.session_id else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )
    
    if session_uuid:
        result = await db.execute(
            select(Session).where(Session.id == session_uuid)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        if session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    
    # Create execution using the executor
    executor = get_executor()
    
    execution_id = await executor.execute(
        session_id=str(session_uuid) if session_uuid else data.session_id,
        task=data.task,
        db=db,
        prompt=data.prompt,
        agent_types=data.agent_types,
        max_retries=data.max_retries,
        workflow_id=data.workflow_id,
    )
    
    # Get the created execution
    execution = await executor.get_execution(execution_id)
    
    return execution_to_response(execution)


@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    user: AuthenticatedUser,
    db: DbSession,
    session_id: str | None = None,
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ExecutionListResponse:
    """List executions for the authenticated user.
    
    Can filter by session_id or state.
    """
    from app.db.execution import Execution
    from app.db.session import Session
    
    # Build query
    query = select(Execution, Session).join(Session, Execution.session_id == Session.id)
    
    # Filter by user
    query = query.where(Session.user_id == user.id)
    
    # Filter by session
    if session_id:
        try:
            session_uuid = uuid.UUID(session_id)
            query = query.where(Execution.session_id == session_uuid)
        except ValueError:
            pass
    
    # Filter by state
    if state:
        query = query.where(Execution.state == state)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(Execution.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    
    executions = [execution_to_response(execution) for execution, _ in rows]
    
    return ExecutionListResponse(
        executions=executions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> ExecutionDetailResponse:
    """Get execution details by ID."""
    execution = await get_execution_or_404(execution_id, user, db)
    
    return execution_to_detail_response(execution)


@router.get("/{execution_id}/steps", response_model=list[ExecutionStepResponse])
async def get_execution_steps(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> list[ExecutionStepResponse]:
    """Get all steps for an execution."""
    execution = await get_execution_or_404(execution_id, user, db)
    
    executor = get_executor()
    steps = await executor.get_execution_steps(execution_id)
    
    return [
        ExecutionStepResponse(
            id=str(step.id),
            execution_id=str(step.execution_id),
            step_order=step.step_order,
            agent_type=step.agent_type,
            description=step.description,
            state=step.state,
            started_at=step.started_at,
            completed_at=step.completed_at,
            duration_ms=step.duration_ms,
            retry_count=step.retry_count,
            result=step.result,
            error=step.error,
        )
        for step in steps
    ]


@router.get("/{execution_id}/logs", response_model=list[ExecutionLogResponse])
async def get_execution_logs(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    limit: int = 100,
    offset: int = 0,
) -> list[ExecutionLogResponse]:
    """Get execution logs with pagination."""
    execution = await get_execution_or_404(execution_id, user, db)
    
    executor = get_executor()
    logs = await executor.get_execution_logs(execution_id, limit, offset)
    
    return [
        ExecutionLogResponse(
            id=str(log.id),
            execution_id=str(log.execution_id),
            step_id=str(log.step_id) if log.step_id else None,
            level=log.level,
            message=log.message,
            details=log.details,
            agent_type=log.agent_type,
            action=log.action,
            timestamp=log.created_at,
        )
        for log in logs
    ]


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    data: ExecutionCancelRequest | None = None,
) -> ExecutionResponse:
    """Cancel a running execution.
    
    This will stop the execution and update its state to cancelled.
    """
    execution = await get_execution_or_404(execution_id, user, db)
    
    cancelled_by = data.cancelled_by if data else "user"
    
    executor = get_executor()
    success = await executor.cancel(execution_id, cancelled_by)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel execution in current state",
        )
    
    # Get updated execution
    execution = await executor.get_execution(execution_id)
    
    return execution_to_response(execution)


@router.post("/{execution_id}/pause", response_model=ExecutionResponse)
async def pause_execution(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> ExecutionResponse:
    """Pause a running execution for user input."""
    execution = await get_execution_or_404(execution_id, user, db)
    
    executor = get_executor()
    success = await executor.pause(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pause execution in current state",
        )
    
    execution = await executor.get_execution(execution_id)
    
    return execution_to_response(execution)


@router.post("/{execution_id}/resume", response_model=ExecutionResponse)
async def resume_execution(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> ExecutionResponse:
    """Resume a paused execution.
    
    This will continue execution from the last checkpoint.
    """
    execution = await get_execution_or_404(execution_id, user, db)
    
    executor = get_executor()
    success = await executor.resume(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resume execution in current state",
        )
    
    execution = await executor.get_execution(execution_id)
    
    return execution_to_response(execution)


@router.post("/{execution_id}/retry", response_model=ExecutionRetryResponse)
async def retry_execution(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> ExecutionRetryResponse:
    """Retry a failed execution.
    
    This will restart the execution from the beginning or last checkpoint.
    """
    execution = await get_execution_or_404(execution_id, user, db)
    
    executor = get_executor()
    
    if not execution.can_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution cannot be retried (not in failed state or max retries exceeded)",
        )
    
    success = await executor.retry(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start retry",
        )
    
    # Get updated execution
    execution = await executor.get_execution(execution_id)
    
    return ExecutionRetryResponse(
        execution_id=execution_id,
        retry_count=execution.retry_count,
        success=True,
        message=f"Retry #{execution.retry_count} started",
    )


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: str,
    user: AuthenticatedUser,
    db: DbSession,
):
    """Get SSE stream for execution updates.
    
    This endpoint provides Server-Sent Events for real-time
    execution updates without WebSocket.
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    execution = await get_execution_or_404(execution_id, user, db)
    executor = get_executor()
    
    async def event_generator():
        """Generate SSE events for execution updates."""
        last_state = execution.state
        last_step = execution.current_step_index
        
        while True:
            # Get current execution state
            current = await executor.get_execution(execution_id)
            
            if current is None:
                yield "data: {\"type\": \"error\", \"message\": \"Execution not found\"}\n\n"
                break
            
            # Check for state changes
            if current.state != last_state or current.current_step_index != last_step:
                progress = int(
                    (current.current_step_index / max(current.total_steps, 1)) * 100
                ) if current.total_steps > 0 else 0
                
                data = {
                    "type": "update",
                    "state": current.state,
                    "current_agent": current.current_agent or "",
                    "progress": progress,
                    "step": current.current_step_index,
                    "total_steps": current.total_steps,
                }
                import json
                yield f"data: {json.dumps(data)}\n\n"
                
                last_state = current.state
                last_step = current.current_step_index
            
            # Check for terminal state
            if current.is_terminal:
                complete_data = {
                    "type": "complete",
                    "state": current.state,
                    "error": current.error,
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
                break
            
            # Wait before next check
            await asyncio.sleep(0.5)
        
        yield "data: {\"type\": \"done\"}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
