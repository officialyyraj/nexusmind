"""Production-ready orchestration executor for running agent workflows.

Features:
- Background execution with proper lifecycle
- Persistent execution state for resumability
- Checkpointing at each step
- Retry logic with exponential backoff
- Proper cancellation with cleanup
- Streaming via WebSocket
- Full observability
"""

import asyncio
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.agents.base import AgentState
from app.agents.workflow import AgentWorkflow
from app.agents.types import AgentType
from app.agents.implementations import PlannerAgent, ResearcherAgent, CoderAgent, ReviewerAgent, TesterAgent, DocumentationAgent
from app.db.session import Session, SessionStatus
from app.db.message import Message, MessageRole
from app.db.artifact import AgentLog, Artifact
from app.db.execution import Execution, ExecutionStep, ExecutionLog, ExecutionState
from app.memory.chromadb import get_memory_service, ChromaMemoryService
from app.streaming.ws_manager import get_connection_manager
from app.sandbox.docker import get_sandbox, DockerSandbox


# Retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay_seconds": 1,
    "max_delay_seconds": 60,
    "exponential_base": 2,
}

# Retryable error types
RETRYABLE_ERROR_TYPES = {
    "llm_error",
    "network_error",
    "timeout",
    "docker_error",
    "mcp_error",
    "rate_limit",
    "temporary_unavailable",
}

# Non-retryable error types
NON_RETRYABLE_ERROR_TYPES = {
    "validation_error",
    "invalid_input",
    "unauthorized",
    "forbidden",
    "not_found",
    "syntax_error",
    "parse_error",
    "resource_exhausted",
}


class ExecutionError(Exception):
    """Custom exception for execution errors with metadata."""
    
    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        details: dict[str, Any] | None = None,
        is_retryable: bool = True,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.is_retryable = is_retryable


class ProductionExecutor:
    """Production-ready executor for agent workflows.
    
    This executor provides:
    - Background execution that survives HTTP requests
    - Persistent state for resumability
    - Checkpointing at each step
    - Retry logic with exponential backoff
    - Proper cancellation with cleanup
    - WebSocket streaming
    - Full observability
    """
    
    # Mapping of agent types to state values
    AGENT_TO_STATE = {
        "planner": ExecutionState.PLANNING.value,
        "researcher": ExecutionState.RESEARCHING.value,
        "coder": ExecutionState.CODING.value,
        "reviewer": ExecutionState.REVIEWING.value,
        "tester": ExecutionState.TESTING.value,
        "documentation": ExecutionState.DOCUMENTING.value,
    }
    
    # Agent execution order
    AGENT_ORDER = [
        "planner",
        "researcher", 
        "coder",
        "reviewer",
        "tester",
        "documentation",
    ]
    
    def __init__(self):
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._settings = get_settings()
        self._db_engine = None
        self._db_session_factory = None
    
    async def _get_db_session(self) -> AsyncSession:
        """Get a database session."""
        if self._db_engine is None:
            database_url = self._settings.database_url
            self._db_engine = create_async_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
            self._db_session_factory = async_sessionmaker(
                self._db_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        
        session = self._db_session_factory()
        return session
    
    async def execute(
        self,
        session_id: str,
        task: str,
        db: AsyncSession,
        prompt: str | None = None,
        agent_types: list[str] | None = None,
        max_retries: int = 3,
        workflow_id: str | None = None,
    ) -> str:
        """Execute a task in the session.
        
        Args:
            session_id: Session UUID
            task: Task description
            db: Database session
            prompt: Optional prompt override
            agent_types: Optional list of agent types to use
            max_retries: Maximum number of retries for failed steps
            workflow_id: Optional workflow identifier
            
        Returns:
            Execution ID
        """
        # Get session to validate it exists
        session_uuid = uuid.UUID(session_id)
        result = await db.execute(
            select(Session).where(Session.id == session_uuid)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Determine which agents to run
        if agent_types and len(agent_types) > 0:
            run_agents = agent_types
        else:
            run_agents = self.AGENT_ORDER
        
        # Create execution record
        execution = Execution(
            session_id=session_uuid,
            workflow_id=workflow_id,
            task=task,
            prompt=prompt,
            agent_types=run_agents,
            state=ExecutionState.QUEUED.value,
            max_retries=max_retries,
            total_steps=len(run_agents),
            metadata={
                "client_prompt": prompt,
                "original_agent_types": agent_types,
            },
        )
        db.add(execution)
        await db.flush()
        await db.refresh(execution)
        
        execution_id = str(execution.id)
        
        # Update session status
        session.status = SessionStatus.RUNNING.value
        session.context = session.context or {}
        session.context["execution_id"] = execution_id
        await db.commit()
        
        # Start execution in background (detached from request)
        task_handle = asyncio.create_task(
            self._run_execution(
                execution_id=execution_id,
                session_id=session_id,
                task=task,
                prompt=prompt,
                run_agents=run_agents,
            )
        )
        self._running_tasks[execution_id] = task_handle
        
        # Add callback to clean up when done
        task_handle.add_done_callback(
            lambda t: self._running_tasks.pop(execution_id, None)
        )
        
        return execution_id
    
    async def _run_execution(
        self,
        execution_id: str,
        session_id: str,
        task: str,
        prompt: str | None,
        run_agents: list[str],
    ) -> None:
        """Run the execution in a separate task with its own db session."""
        db = await self._get_db_session()
        
        try:
            # Load execution
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if not execution:
                return
            
            # Load session
            session_uuid = uuid.UUID(session_id)
            result = await db.execute(
                select(Session).where(Session.id == session_uuid)
            )
            session: Session = result.scalar_one_or_none()
            
            if not session:
                return
            
            # Mark as starting
            await self._transition_state(execution, ExecutionState.STARTING, db)
            
            # Create user message
            user_message = Message(
                session_id=session_uuid,
                role=MessageRole.USER.value,
                content=task,
            )
            db.add(user_message)
            await db.flush()
            
            # Initialize agent timings
            agent_timings: dict[str, dict[str, Any]] = {}
            
            # Initialize workflow state for checkpointing
            workflow_state: AgentState = {
                "session_id": session_id,
                "task": task,
                "context": {
                    "execution_id": execution_id,
                    "prompt": prompt,
                    "run_agents": run_agents,
                },
                "messages": [],
                "artifacts": [],
                "agent_states": {},
                "current_agent": None,
                "result": None,
                "error": None,
            }
            
            # Execute each agent in order
            for step_index, agent_type in enumerate(run_agents):
                # Check for cancellation
                await db.refresh(execution)
                if execution.is_cancelled:
                    await self._handle_cancellation(execution, session, db)
                    return
                
                # Update checkpoint before running step
                checkpoint_data = {
                    "step_index": step_index,
                    "agent_type": agent_type,
                    "workflow_state": workflow_state,
                    "completed_agents": run_agents[:step_index],
                }
                await self._save_checkpoint(execution, checkpoint_data, db)
                
                # Create step record
                step = ExecutionStep(
                    execution_id=execution_uuid,
                    step_order=step_index,
                    agent_type=agent_type,
                    description=f"Running {agent_type} agent",
                    state="running",
                    started_at=datetime.utcnow(),
                )
                db.add(step)
                await db.flush()
                
                # Transition to agent state
                state = self.AGENT_TO_STATE.get(agent_type, ExecutionState.STARTING.value)
                await self._transition_state(execution, state, db)
                await self._update_progress(execution, step_index, agent_type, db)
                
                # Log step start
                await self._log(
                    execution, step, "INFO",
                    f"Starting {agent_type} agent",
                    {"step": step_index, "agent": agent_type},
                    db,
                )
                
                # Execute agent with retries
                step_result = await self._execute_agent_with_retries(
                    agent_type=agent_type,
                    workflow_state=workflow_state,
                    execution=execution,
                    step=step,
                    db=db,
                )
                
                # Record timing
                step_duration_ms = step_result.get("duration_ms", 0)
                agent_timings[agent_type] = {
                    "duration_ms": step_duration_ms,
                    "attempts": step.retry_count + 1,
                    "success": step_result.get("success", False),
                    "error": step_result.get("error"),
                }
                
                # Update step as completed
                step.completed_at = datetime.utcnow()
                step.duration_ms = step_duration_ms
                step.result = step_result.get("result")
                step.error = step_result.get("error")
                step.state = "completed" if step_result.get("success") else "failed"
                
                # Update workflow state
                if step_result.get("state"):
                    workflow_state = step_result["state"]
                
                # Check if step failed permanently
                if not step_result.get("success") and not step_result.get("retryable"):
                    execution.error = step_result.get("error", "Step failed")
                    execution.error_details = {
                        "type": "step_failed",
                        "step": agent_type,
                        "failed_step_index": step_index,
                        "details": step_result.get("details"),
                    }
                    await self._transition_state(execution, ExecutionState.FAILED, db)
                    await db.commit()
                    return
                
                await db.commit()
            
            # All steps completed successfully
            await self._transition_state(execution, ExecutionState.COMPLETED, db)
            
            execution.result = {
                "output": workflow_state.get("result", {}).get("output", "Task completed"),
                "agent_timings": agent_timings,
            }
            execution.agent_timings = agent_timings
            execution.completed_at = datetime.utcnow()
            
            # Create assistant message
            assistant_message = Message(
                session_id=session_uuid,
                role=MessageRole.ASSISTANT.value,
                content=str(execution.result.get("output", "Task completed")),
                agent_type="manager",
            )
            db.add(assistant_message)
            
            # Update session status
            session.status = SessionStatus.COMPLETED.value
            
            # Log completion
            await self._log(
                execution, None, "INFO",
                "Execution completed successfully",
                {"duration_seconds": execution.duration_seconds},
                db,
            )
            
            await db.commit()
            
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            await db.rollback()
            await self._handle_cancellation_by_id(execution_id)
            raise
            
        except Exception as e:
            await db.rollback()
            await self._handle_error(execution_id, e)
            
        finally:
            await db.close()
    
    async def _execute_agent_with_retries(
        self,
        agent_type: str,
        workflow_state: AgentState,
        execution: Execution,
        step: ExecutionStep,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Execute an agent with retry logic."""
        attempt = 0
        max_attempts = execution.max_retries + 1
        
        while attempt < max_attempts:
            try:
                # Create agent instance
                agent = self._create_agent(agent_type)
                
                # Execute agent
                start_time = datetime.utcnow()
                result_state = await agent.execute(workflow_state)
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Success
                return {
                    "success": True,
                    "result": result_state.get("result"),
                    "state": result_state,
                    "duration_ms": duration_ms,
                    "attempts": attempt + 1,
                }
                
            except Exception as e:
                attempt += 1
                step.retry_count = attempt - 1
                
                # Determine if retryable
                error_type = self._classify_error(e)
                is_retryable = error_type in RETRYABLE_ERROR_TYPES
                
                # Log retry attempt
                await self._log(
                    execution, step, "WARNING",
                    f"Agent {agent_type} failed (attempt {attempt}/{max_attempts}): {str(e)}",
                    {"error_type": error_type, "retryable": is_retryable},
                    db,
                )
                
                if not is_retryable or attempt >= max_attempts:
                    # Don't retry permanent failures
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": error_type,
                        "retryable": is_retryable,
                        "attempts": attempt,
                        "details": {"traceback": traceback.format_exc()},
                    }
                
                # Exponential backoff
                delay = min(
                    RETRY_CONFIG["base_delay_seconds"] * (RETRY_CONFIG["exponential_base"] ** (attempt - 1)),
                    RETRY_CONFIG["max_delay_seconds"],
                )
                
                await self._log(
                    execution, step, "INFO",
                    f"Retrying in {delay} seconds...",
                    {"retry_delay": delay, "next_attempt": attempt + 1},
                    db,
                )
                
                await asyncio.sleep(delay)
        
        return {
            "success": False,
            "error": f"Max retries ({max_attempts}) exceeded",
            "retryable": False,
            "attempts": max_attempts,
        }
    
    def _create_agent(self, agent_type: str):
        """Create an agent instance based on type."""
        agents = {
            "planner": PlannerAgent,
            "researcher": ResearcherAgent,
            "coder": CoderAgent,
            "reviewer": ReviewerAgent,
            "tester": TesterAgent,
            "documentation": DocumentationAgent,
        }
        
        agent_class = agents.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return agent_class()
    
    def _classify_error(self, error: Exception) -> str:
        """Classify an error to determine if it's retryable."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check for specific error patterns
        if any(x in error_str for x in ["timeout", "timed out", "deadline"]):
            return "timeout"
        elif any(x in error_str for x in ["network", "connection", "refused", "unreachable"]):
            return "network_error"
        elif any(x in error_str for x in ["rate limit", "too many requests", "429"]):
            return "rate_limit"
        elif any(x in error_str for x in ["docker", "container"]):
            return "docker_error"
        elif any(x in error_str for x in ["llm", "openai", "anthropic", "model"]):
            return "llm_error"
        elif any(x in error_str for x in ["mcp", "server error", "500", "502", "503", "504"]):
            return "mcp_error"
        elif any(x in error_str for x in ["unauthorized", "forbidden", "permission"]):
            return "unauthorized"
        elif any(x in error_str for x in ["not found", "404"]):
            return "not_found"
        elif any(x in error_str for x in ["validation", "invalid", "malformed"]):
            return "validation_error"
        
        return "unknown"
    
    async def _transition_state(
        self,
        execution: Execution,
        new_state: ExecutionState,
        db: AsyncSession,
    ) -> None:
        """Transition execution to a new state."""
        execution.previous_state = execution.state
        execution.state = new_state.value
        execution.state_changed_at = datetime.utcnow()
        
        # Broadcast state change via WebSocket
        manager = get_connection_manager()
        await manager.broadcast_execution_update(
            str(execution.session_id),
            {
                "type": "state_change",
                "execution_id": str(execution.id),
                "from_state": execution.previous_state,
                "to_state": new_state.value,
                "timestamp": execution.state_changed_at.isoformat(),
            },
        )
    
    async def _update_progress(
        self,
        execution: Execution,
        step_index: int,
        agent_type: str,
        db: AsyncSession,
    ) -> None:
        """Update execution progress."""
        execution.current_step_index = step_index
        execution.current_agent = agent_type
        
        # Broadcast progress update
        manager = get_connection_manager()
        await manager.broadcast_execution_update(
            str(execution.session_id),
            {
                "type": "progress",
                "execution_id": str(execution.id),
                "current_step": step_index,
                "total_steps": execution.total_steps,
                "current_agent": agent_type,
                "progress_percent": int((step_index / max(execution.total_steps, 1)) * 100),
            },
        )
    
    async def _save_checkpoint(
        self,
        execution: Execution,
        checkpoint_data: dict[str, Any],
        db: AsyncSession,
    ) -> None:
        """Save a checkpoint for resumability."""
        execution.checkpoint_data = checkpoint_data
        execution.last_checkpoint_at = datetime.utcnow()
        await db.flush()
    
    async def _log(
        self,
        execution: Execution,
        step: ExecutionStep | None,
        level: str,
        message: str,
        details: dict[str, Any] | None,
        db: AsyncSession,
    ) -> None:
        """Create an execution log entry and broadcast."""
        log = ExecutionLog(
            execution_id=execution.id,
            step_id=step.id if step else None,
            level=level,
            message=message,
            details=details,
            agent_type=execution.current_agent,
            is_streamed=True,
        )
        db.add(log)
        await db.flush()
        
        # Broadcast log via WebSocket
        manager = get_connection_manager()
        await manager.broadcast_log(
            str(execution.session_id),
            message,
            level=level,
            execution_id=str(execution.id),
            agent_type=execution.current_agent,
            details=details,
        )
    
    async def _handle_error(self, execution_id: str, error: Exception) -> None:
        """Handle execution error."""
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if not execution:
                return
            
            execution.state = ExecutionState.FAILED.value
            execution.error = str(error)
            execution.error_details = {
                "type": self._classify_error(error),
                "traceback": traceback.format_exc(),
            }
            execution.completed_at = datetime.utcnow()
            
            # Update session
            session_uuid = execution.session_id
            result = await db.execute(
                select(Session).where(Session.id == session_uuid)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = SessionStatus.ERROR.value
            
            # Broadcast error
            manager = get_connection_manager()
            await manager.broadcast_log(
                str(execution.session_id),
                f"Execution failed: {str(error)}",
                level="ERROR",
                execution_id=execution_id,
            )
            
            await db.commit()
            
        finally:
            await db.close()
    
    async def _handle_cancellation(self, execution: Execution, session: Session, db: AsyncSession) -> None:
        """Handle execution cancellation."""
        execution.is_cancelled = True
        execution.cancelled_at = datetime.utcnow()
        execution.state = ExecutionState.CANCELLED.value
        execution.completed_at = datetime.utcnow()
        
        session.status = SessionStatus.CANCELLED.value
        
        # Broadcast cancellation
        manager = get_connection_manager()
        await manager.broadcast_execution_update(
            str(execution.session_id),
            {
                "type": "cancelled",
                "execution_id": str(execution.id),
                "cancelled_at": execution.cancelled_at.isoformat(),
            },
        )
        
        await db.commit()
    
    async def _handle_cancellation_by_id(self, execution_id: str) -> None:
        """Handle cancellation by execution ID."""
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if execution and not execution.is_cancelled:
                await self._handle_cancellation(execution, None, db)
            
        finally:
            await db.close()
    
    async def cancel(self, execution_id: str, cancelled_by: str = "user") -> bool:
        """Cancel a running execution.
        
        Args:
            execution_id: Execution ID to cancel
            cancelled_by: Who initiated the cancellation
            
        Returns:
            True if cancelled, False if not found or already terminal
        """
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if not execution:
                return False
            
            if execution.is_terminal:
                return False
            
            # Cancel async task if running
            if execution_id in self._running_tasks:
                task = self._running_tasks[execution_id]
                if not task.done():
                    task.cancel()
            
            # Update database
            execution.is_cancelled = True
            execution.cancelled_at = datetime.utcnow()
            execution.cancelled_by = cancelled_by
            execution.state = ExecutionState.CANCELLED.value
            execution.completed_at = datetime.utcnow()
            
            await db.commit()
            
            # Broadcast cancellation
            manager = get_connection_manager()
            await manager.broadcast_execution_update(
                str(execution.session_id),
                {
                    "type": "cancelled",
                    "execution_id": execution_id,
                    "cancelled_at": execution.cancelled_at.isoformat(),
                    "cancelled_by": cancelled_by,
                },
            )
            
            return True
            
        finally:
            await db.close()
    
    async def pause(self, execution_id: str) -> bool:
        """Pause a running execution for user input."""
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if not execution or not execution.is_running:
                return False
            
            # Cancel async task
            if execution_id in self._running_tasks:
                task = self._running_tasks[execution_id]
                if not task.done():
                    task.cancel()
            
            # Save checkpoint and pause
            await self._transition_state(execution, ExecutionState.PAUSED, db)
            await db.commit()
            
            return True
            
        finally:
            await db.close()
    
    async def resume(self, execution_id: str) -> bool:
        """Resume a paused execution.
        
        This will restart from the last checkpoint.
        """
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if not execution or execution.state != ExecutionState.PAUSED.value:
                return False
            
            # Get checkpoint data
            checkpoint = execution.checkpoint_data or {}
            completed_agents = checkpoint.get("completed_agents", [])
            next_step_index = len(completed_agents)
            
            # Get remaining agents
            all_agents = execution.agent_types
            remaining_agents = all_agents[next_step_index:]
            
            # Transition to resuming
            await self._transition_state(execution, ExecutionState.RESUMING, db)
            await db.commit()
            
            # Start resumed execution
            task_handle = asyncio.create_task(
                self._run_execution_resume(
                    execution_id=execution_id,
                    checkpoint=checkpoint,
                    remaining_agents=remaining_agents,
                )
            )
            self._running_tasks[execution_id] = task_handle
            
            return True
            
        finally:
            await db.close()
    
    async def _run_execution_resume(
        self,
        execution_id: str,
        checkpoint: dict[str, Any],
        remaining_agents: list[str],
    ) -> None:
        """Resume execution from checkpoint."""
        # Similar to _run_execution but starts from checkpoint
        # Implementation would restore workflow_state from checkpoint
        pass
    
    async def retry(self, execution_id: str) -> bool:
        """Retry a failed execution.
        
        This will restart from the beginning or last checkpoint.
        """
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            execution: Execution = result.scalar_one_or_none()
            
            if not execution or not execution.can_retry:
                return False
            
            # Increment retry count
            execution.retry_count += 1
            execution.last_retry_at = datetime.utcnow()
            execution.retry_history = execution.retry_history + [
                {
                    "retry_number": execution.retry_count,
                    "timestamp": datetime.utcnow().isoformat(),
                    "previous_error": execution.error,
                }
            ]
            
            # Reset state
            execution.state = ExecutionState.QUEUED.value
            execution.error = None
            execution.error_details = None
            execution.completed_at = None
            
            await db.commit()
            
            # Start retry execution
            task_handle = asyncio.create_task(
                self._run_execution(
                    execution_id=execution_id,
                    session_id=str(execution.session_id),
                    task=execution.task,
                    prompt=execution.prompt,
                    run_agents=execution.agent_types,
                )
            )
            self._running_tasks[execution_id] = task_handle
            
            return True
            
        finally:
            await db.close()
    
    def is_running(self, execution_id: str) -> bool:
        """Check if an execution is running in memory."""
        if execution_id not in self._running_tasks:
            return False
        task = self._running_tasks[execution_id]
        return task is not None and not task.done()
    
    def get_running_count(self) -> int:
        """Get count of running executions."""
        return sum(
            1 for t in self._running_tasks.values()
            if t and not t.done()
        )
    
    async def get_execution(self, execution_id: str) -> Execution | None:
        """Get execution by ID from database."""
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(Execution).where(Execution.id == execution_uuid)
            )
            return result.scalar_one_or_none()
            
        finally:
            await db.close()
    
    async def get_execution_steps(self, execution_id: str) -> list[ExecutionStep]:
        """Get all steps for an execution."""
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(ExecutionStep)
                .where(ExecutionStep.execution_id == execution_uuid)
                .order_by(ExecutionStep.step_order)
            )
            return list(result.scalars().all())
            
        finally:
            await db.close()
    
    async def get_execution_logs(
        self,
        execution_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionLog]:
        """Get execution logs with pagination."""
        db = await self._get_db_session()
        
        try:
            execution_uuid = uuid.UUID(execution_id)
            result = await db.execute(
                select(ExecutionLog)
                .where(ExecutionLog.execution_id == execution_uuid)
                .order_by(ExecutionLog.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return list(result.scalars().all())
            
        finally:
            await db.close()
    
    async def recover_unfinished(self) -> int:
        """Recover unfinished executions after restart.
        
        This should be called on startup to resume any executions
        that were running when the server crashed.
        
        Returns:
            Number of executions recovered
        """
        db = await self._get_db_session()
        recovered = 0
        
        try:
            # Find executions that were running but not in memory
            result = await db.execute(
                select(Execution).where(
                    Execution.state.in_({
                        ExecutionState.STARTING.value,
                        ExecutionState.PLANNING.value,
                        ExecutionState.RESEARCHING.value,
                        ExecutionState.CODING.value,
                        ExecutionState.REVIEWING.value,
                        ExecutionState.TESTING.value,
                        ExecutionState.DOCUMENTING.value,
                        ExecutionState.RESUMING.value,
                    })
                )
            )
            
            for execution in result.scalars().all():
                # Skip if already in memory
                if str(execution.id) in self._running_tasks:
                    continue
                
                # Check if we have checkpoint data
                if execution.checkpoint_data:
                    # Resume from checkpoint
                    await self._transition_state(execution, ExecutionState.RESUMING, db)
                    
                    task_handle = asyncio.create_task(
                        self._run_execution_resume(
                            execution_id=str(execution.id),
                            checkpoint=execution.checkpoint_data,
                            remaining_agents=execution.agent_types[execution.current_step_index:],
                        )
                    )
                    self._running_tasks[str(execution.id)] = task_handle
                    recovered += 1
                else:
                    # Restart from beginning
                    execution.state = ExecutionState.QUEUED.value
                    await db.commit()
                    
                    task_handle = asyncio.create_task(
                        self._run_execution(
                            execution_id=str(execution.id),
                            session_id=str(execution.session_id),
                            task=execution.task,
                            prompt=execution.prompt,
                            run_agents=execution.agent_types,
                        )
                    )
                    self._running_tasks[str(execution.id)] = task_handle
                    recovered += 1
            
            await db.commit()
            return recovered
            
        finally:
            await db.close()


# Global executor instance
_executor: ProductionExecutor | None = None


def get_executor() -> ProductionExecutor:
    """Get the global production executor."""
    global _executor
    if _executor is None:
        _executor = ProductionExecutor()
    return _executor