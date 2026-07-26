"""Orchestration executor for running agent workflows."""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import AgentState
from app.agents.workflow import AgentWorkflow
from app.agents.types import AgentType
from app.db.session import Session, SessionStatus
from app.db.message import Message, MessageRole
from app.db.artifact import AgentLog
from app.memory.chromadb import get_memory_service
from app.streaming.ws_manager import get_connection_manager


class ExecutionStatus(str):
    """Execution status values."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationExecutor:
    """Executor for agent workflows with state persistence and streaming."""

    def __init__(self):
        self._running_executions: dict[str, asyncio.Task] = {}
        self._workflow = AgentWorkflow()

    async def execute(
        self,
        session_id: str,
        task: str,
        db: AsyncSession,
        prompt: str | None = None,
        agent_types: list[str] | None = None,
    ) -> str:
        """Execute a task in the session.
        
        Args:
            session_id: Session UUID
            task: Task description
            db: Database session
            prompt: Optional prompt override
            agent_types: Optional list of agent types to use
            
        Returns:
            Execution ID
        """
        execution_id = str(uuid.uuid4())
        
        # Store execution info
        self._running_executions[execution_id] = None
        
        # Start execution in background
        task_handle = asyncio.create_task(
            self._execute_workflow(
                execution_id=execution_id,
                session_id=session_id,
                task=task,
                db=db,
                prompt=prompt,
                agent_types=agent_types,
            )
        )
        self._running_executions[execution_id] = task_handle
        
        return execution_id

    async def _execute_workflow(
        self,
        execution_id: str,
        session_id: str,
        task: str,
        db: AsyncSession,
        prompt: str | None = None,
        agent_types: list[str] | None = None,
    ) -> None:
        """Execute the agent workflow.
        
        This runs the full planner → researcher → coder → reviewer → tester pipeline.
        """
        try:
            # Get session
            session_uuid = uuid.UUID(session_id)
            result = await db.execute(
                select(Session).where(Session.id == session_uuid)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return
            
            # Update session status
            session.status = SessionStatus.RUNNING.value
            session.context = session.context or {}
            session.context["execution_id"] = execution_id
            await db.flush()
            
            # Initialize agent states
            agent_states: dict[str, dict[str, Any]] = {}
            for agent_type in ["planner", "researcher", "coder", "reviewer", "tester", "documentation"]:
                agent_states[agent_type] = {"status": "pending", "attempts": 0}
            
            # Create initial state
            initial_state: AgentState = {
                "session_id": session_id,
                "task": task,
                "context": {
                    "execution_id": execution_id,
                    "prompt": prompt,
                    "agent_types": agent_types,
                },
                "messages": [],
                "artifacts": [],
                "agent_states": agent_states,
                "current_agent": None,
                "result": None,
                "error": None,
            }
            
            # Store user message
            user_message = Message(
                session_id=session.id,
                role=MessageRole.USER.value,
                content=task,
            )
            db.add(user_message)
            await db.flush()
            
            # Broadcast start event
            manager = get_connection_manager()
            await manager.broadcast_log(
                session_id,
                f"Starting execution {execution_id}",
                level="INFO",
            )
            
            # Execute workflow based on agent types
            if agent_types and len(agent_types) > 0:
                # Use specified agents
                workflow = AgentWorkflow(workflow_type="planner_researcher_coder")
                final_state = await workflow.run(task, session_id, initial_state["context"])
            else:
                # Use default full workflow
                workflow = AgentWorkflow(workflow_type="planner_researcher_coder")
                final_state = await workflow.run(task, session_id, initial_state["context"])
            
            # Store result
            if final_state.get("error"):
                session.status = SessionStatus.ERROR.value
                
                # Log error
                log = AgentLog(
                    session_id=session.id,
                    agent_type="system",
                    action="error",
                    details={"error": final_state["error"]},
                    level="ERROR",
                )
                db.add(log)
                
                await manager.broadcast_log(
                    session_id,
                    f"Execution failed: {final_state['error']}",
                    level="ERROR",
                )
            else:
                session.status = SessionStatus.COMPLETED.value
                
                # Log completion
                log = AgentLog(
                    session_id=session.id,
                    agent_type="system",
                    action="completed",
                    details={"result": str(final_state.get("result", {}))[:500]},
                    level="INFO",
                )
                db.add(log)
                
                await manager.broadcast_log(
                    session_id,
                    "Execution completed successfully",
                    level="INFO",
                )
            
            # Update agent states
            session.agent_states = final_state.get("agent_states", agent_states)
            
            # Store assistant response
            result_content = str(final_state.get("result", {}).get("output", "Task completed"))
            assistant_message = Message(
                session_id=session.id,
                role=MessageRole.ASSISTANT.value,
                content=result_content,
                agent_type="manager",
            )
            db.add(assistant_message)
            
            await db.commit()
            
        except Exception as e:
            # Update session with error
            try:
                session_uuid = uuid.UUID(session_id)
                result = await db.execute(
                    select(Session).where(Session.id == session_uuid)
                )
                session = result.scalar_one_or_none()
                if session:
                    session.status = SessionStatus.ERROR.value
                    await db.commit()
            except Exception:
                pass
            
            # Broadcast error
            manager = get_connection_manager()
            await manager.broadcast_log(
                session_id,
                f"Execution error: {str(e)}",
                level="ERROR",
            )
            
        finally:
            # Clean up
            if execution_id in self._running_executions:
                del self._running_executions[execution_id]

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        if execution_id in self._running_executions:
            task = self._running_executions[execution_id]
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self._running_executions[execution_id]
            return True
        return False

    def is_running(self, execution_id: str) -> bool:
        """Check if an execution is running.
        
        Args:
            execution_id: Execution ID to check
            
        Returns:
            True if running, False otherwise
        """
        if execution_id not in self._running_executions:
            return False
        task = self._running_executions[execution_id]
        return task is not None and not task.done()

    def get_running_count(self) -> int:
        """Get count of running executions."""
        return sum(
            1 for t in self._running_executions.values()
            if t and not t.done()
        )


# Global executor instance
_executor: OrchestrationExecutor | None = None


def get_executor() -> OrchestrationExecutor:
    """Get the global orchestration executor."""
    global _executor
    if _executor is None:
        _executor = OrchestrationExecutor()
    return _executor