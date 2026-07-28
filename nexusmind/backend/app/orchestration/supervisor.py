"""Supervisor for coordinating multi-agent execution."""

import asyncio
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from app.agents.base import AgentState
from app.agents.registry import AgentRegistry, get_agent_registry, AgentHealth, AgentPriority
from app.agents.types import AgentType
from app.tools.registry import ToolRegistry, get_tool_registry
from app.streaming.ws_manager import get_connection_manager


class SupervisorStatus(str, Enum):
    """Supervisor execution status."""

    IDLE = "idle"
    COORDINATING = "coordinating"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """A task assigned to an agent."""

    task_id: str
    agent_type: AgentType
    task: str
    context: dict[str, Any]
    priority: AgentPriority
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ExecutionContext:
    """Context for multi-agent execution."""

    execution_id: str
    session_id: str
    task: str
    context: dict[str, Any]
    state: AgentState
    tasks: dict[str, AgentTask] = field(default_factory=dict)
    completed_tasks: set[str] = field(default_factory=set)
    failed_tasks: set[str] = field(default_factory=set)
    status: SupervisorStatus = SupervisorStatus.IDLE
    created_at: datetime = field(default_factory=datetime.utcnow)


class Supervisor:
    """Supervisor for coordinating multi-agent execution.

    Responsibilities:
    - Coordinating agents
    - Dispatching work
    - Tracking execution
    - Collecting results
    - Forwarding failures
    - Cancellation propagation
    """

    def __init__(
        self,
        agent_registry: AgentRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self._agent_registry = agent_registry or get_agent_registry()
        self._tool_registry = tool_registry or get_tool_registry()
        self._active_executions: dict[str, ExecutionContext] = {}
        self._cancellation_tokens: dict[str, asyncio.Event] = {}

    async def submit_task(
        self,
        execution_id: str,
        session_id: str,
        task: str,
        context: dict[str, Any] | None = None,
        agent_types: list[AgentType] | None = None,
    ) -> str:
        """Submit a task for multi-agent execution.

        Args:
            execution_id: Execution ID
            session_id: Session ID
            task: Task description
            context: Additional context
            agent_types: Optional list of agent types to use

        Returns:
            Execution context ID
        """
        ctx = ExecutionContext(
            execution_id=execution_id,
            session_id=session_id,
            task=task,
            context=context or {},
            state=AgentState(
                session_id=session_id,
                task=task,
                context=context or {},
                messages=[],
                artifacts=[],
                agent_states={},
                current_agent=None,
                result=None,
                error=None,
            ),
        )

        self._active_executions[execution_id] = ctx
        self._cancellation_tokens[execution_id] = asyncio.Event()

        # Broadcast start
        manager = get_connection_manager()
        await manager.broadcast_execution_update(
            session_id,
            {
                "type": "supervisor_started",
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return execution_id

    async def add_agent_task(
        self,
        execution_id: str,
        agent_type: AgentType,
        task: str,
        priority: AgentPriority = AgentPriority.NORMAL,
        dependencies: list[str] | None = None,
    ) -> str:
        """Add a task for a specific agent.

        Args:
            execution_id: Execution ID
            agent_type: Type of agent
            task: Task description
            priority: Task priority
            dependencies: Task IDs this depends on

        Returns:
            Task ID
        """
        if execution_id not in self._active_executions:
            raise ValueError(f"Execution not found: {execution_id}")

        task_id = str(uuid.uuid4())
        agent_task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            task=task,
            context={},
            priority=priority,
            dependencies=dependencies or [],
        )

        self._active_executions[execution_id].tasks[task_id] = agent_task

        # Broadcast task added
        manager = get_connection_manager()
        ctx = self._active_executions[execution_id]
        await manager.broadcast_execution_update(
            ctx.session_id,
            {
                "type": "task_added",
                "execution_id": execution_id,
                "task_id": task_id,
                "agent_type": agent_type.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return task_id

    async def dispatch_task(
        self,
        execution_id: str,
        task_id: str,
    ) -> dict[str, Any]:
        """Dispatch a specific task to an agent.

        Args:
            execution_id: Execution ID
            task_id: Task ID

        Returns:
            Task result
        """
        if execution_id not in self._active_executions:
            raise ValueError(f"Execution not found: {execution_id}")

        ctx = self._active_executions[execution_id]
        task = ctx.tasks.get(task_id)

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Check cancellation
        if execution_id in self._cancellation_tokens:
            if self._cancellation_tokens[execution_id].is_set():
                task.status = "cancelled"
                return {"success": False, "error": "Cancelled"}

        # Check dependencies
        for dep_id in task.dependencies:
            if dep_id not in ctx.completed_tasks:
                task.status = "waiting"
                return {"success": False, "error": "Dependencies not met"}

        # Get agent from registry
        agent_factory = self._agent_registry.get(task.agent_type)
        if not agent_factory:
            task.status = "failed"
            task.error = f"Agent not registered: {task.agent_type}"
            ctx.failed_tasks.add(task_id)
            return {"success": False, "error": task.error}

        # Check if agent can execute
        if not await self._agent_registry.can_execute(task.agent_type):
            task.status = "waiting"
            return {"success": False, "error": "Agent at capacity"}

        # Record agent usage
        await self._agent_registry.record_use(task.agent_type)

        try:
            task.status = "running"
            task.started_at = datetime.utcnow()

            # Broadcast task start
            manager = get_connection_manager()
            await manager.broadcast_execution_update(
                ctx.session_id,
                {
                    "type": "task_started",
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "agent_type": task.agent_type.value,
                    "timestamp": task.started_at.isoformat(),
                },
            )

            # Create agent instance and execute
            agent = agent_factory(session_id=ctx.session_id)

            # Update state with current task
            ctx.state["current_agent"] = task.agent_type.value
            ctx.state["task"] = task.task
            ctx.state["context"].update(task.context)

            # Execute agent
            result_state = await agent.execute(ctx.state)

            # Update task result
            task.result = result_state.get("result", {})
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            ctx.completed_tasks.add(task_id)

            # Update context state
            ctx.state = result_state

            # Broadcast task completion
            await manager.broadcast_execution_update(
                ctx.session_id,
                {
                    "type": "task_completed",
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "timestamp": task.completed_at.isoformat(),
                },
            )

            return {
                "success": True,
                "result": task.result,
            }

        except asyncio.CancelledError:
            task.status = "cancelled"
            task.error = "Task was cancelled"
            ctx.failed_tasks.add(task_id)
            raise

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            ctx.failed_tasks.add(task_id)

            # Broadcast task failure
            manager = get_connection_manager()
            await manager.broadcast_execution_update(
                ctx.session_id,
                {
                    "type": "task_failed",
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return {
                "success": False,
                "error": str(e),
            }

        finally:
            # Record completion
            await self._agent_registry.record_completion(task.agent_type)

    async def dispatch_next_ready(
        self,
        execution_id: str,
    ) -> list[str]:
        """Dispatch all tasks that are ready to execute.

        Args:
            execution_id: Execution ID

        Returns:
            List of dispatched task IDs
        """
        if execution_id not in self._active_executions:
            return []

        ctx = self._active_executions[execution_id]
        dispatched = []

        for task_id, task in ctx.tasks.items():
            if task.status != "pending":
                continue

            # Check if dependencies are met
            deps_met = all(dep in ctx.completed_tasks for dep in task.dependencies)
            if deps_met:
                result = await self.dispatch_task(execution_id, task_id)
                dispatched.append(task_id)

        return dispatched

    async def wait_for_completion(
        self,
        execution_id: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Wait for all tasks in an execution to complete.

        Args:
            execution_id: Execution ID
            timeout: Optional timeout in seconds

        Returns:
            Execution result
        """
        if execution_id not in self._active_executions:
            raise ValueError(f"Execution not found: {execution_id}")

        ctx = self._active_executions[execution_id]

        # Process tasks until all are done or failed
        while True:
            # Check cancellation
            if execution_id in self._cancellation_tokens:
                if self._cancellation_tokens[execution_id].is_set():
                    ctx.status = SupervisorStatus.CANCELLED
                    break

            # Check if all tasks are done
            all_done = all(
                t.status in ("completed", "failed", "cancelled")
                for t in ctx.tasks.values()
            )

            if all_done:
                if ctx.failed_tasks:
                    ctx.status = SupervisorStatus.FAILED
                else:
                    ctx.status = SupervisorStatus.COMPLETED
                break

            # Dispatch ready tasks
            await self.dispatch_next_ready(execution_id)

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

        # Build result
        return {
            "execution_id": execution_id,
            "status": ctx.status.value,
            "completed_tasks": list(ctx.completed_tasks),
            "failed_tasks": list(ctx.failed_tasks),
            "state": ctx.state,
        }

    async def cancel(self, execution_id: str) -> bool:
        """Cancel an execution.

        Args:
            execution_id: Execution ID

        Returns:
            True if cancelled
        """
        if execution_id not in self._active_executions:
            return False

        if execution_id in self._cancellation_tokens:
            self._cancellation_tokens[execution_id].set()

        ctx = self._active_executions[execution_id]
        ctx.status = SupervisorStatus.CANCELLED

        # Cancel running tasks
        for task in ctx.tasks.values():
            if task.status == "running":
                task.status = "cancelled"

        # Broadcast cancellation
        manager = get_connection_manager()
        await manager.broadcast_execution_update(
            ctx.session_id,
            {
                "type": "execution_cancelled",
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return True

    def get_status(self, execution_id: str) -> dict[str, Any] | None:
        """Get execution status.

        Args:
            execution_id: Execution ID

        Returns:
            Status dict or None
        """
        if execution_id not in self._active_executions:
            return None

        ctx = self._active_executions[execution_id]
        return {
            "execution_id": execution_id,
            "status": ctx.status.value,
            "task_count": len(ctx.tasks),
            "completed_tasks": len(ctx.completed_tasks),
            "failed_tasks": len(ctx.failed_tasks),
            "pending_tasks": sum(1 for t in ctx.tasks.values() if t.status == "pending"),
            "running_tasks": sum(1 for t in ctx.tasks.values() if t.status == "running"),
        }

    def cleanup(self, execution_id: str) -> bool:
        """Clean up execution resources.

        Args:
            execution_id: Execution ID

        Returns:
            True if cleaned up
        """
        if execution_id in self._active_executions:
            del self._active_executions[execution_id]

        if execution_id in self._cancellation_tokens:
            del self._cancellation_tokens[execution_id]

        return True


# Global supervisor instance
_supervisor: Supervisor | None = None


def get_supervisor() -> Supervisor:
    """Get the global supervisor instance.

    Returns:
        Supervisor instance
    """
    global _supervisor
    if _supervisor is None:
        _supervisor = Supervisor()
    return _supervisor
