"""Advanced LangGraph workflow with parallel execution, dependency graph, and recovery."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from langgraph.graph import END, StateGraph

from app.agents.base import AgentState
from app.agents.autonomous import create_autonomous_agent
from app.agents.types import AgentType


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class PhaseType(str, Enum):
    """Workflow phase types."""

    PLANNING = "planning"
    RESEARCH = "research"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    TEST = "test"
    MANAGER = "manager"


@dataclass
class PhaseResult:
    """Result of a phase execution."""

    phase: PhaseType
    status: TaskStatus
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration: float = 0.0


@dataclass
class WorkflowProgress:
    """Progress tracking for workflow execution."""

    workflow_id: str
    task: str
    total_phases: int
    completed_phases: int = 0
    current_phase: PhaseType | None = None
    phase_results: dict[PhaseType, PhaseResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_phases == 0:
            return 0.0
        return (self.completed_phases / self.total_phases) * 100

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.completed_phases >= self.total_phases

    def get_failed_phases(self) -> list[PhaseType]:
        """Get list of failed phases."""
        return [
            phase for phase, result in self.phase_results.items()
            if result.status == TaskStatus.FAILED
        ]


@dataclass
class PhaseConfig:
    """Configuration for a workflow phase."""

    phase: PhaseType
    agent_type: AgentType
    required: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 300.0
    depends_on: list[PhaseType] = field(default_factory=list)
    parallel_with: list[PhaseType] = field(default_factory=list)


class AdvancedWorkflowState(AgentState):
    """Extended state for advanced workflow."""

    workflow_id: str = ""
    progress: dict[str, Any] = field(default_factory=dict)
    phase_results: dict[str, Any] = field(default_factory=dict)
    task_priorities: dict[str, int] = field(default_factory=dict)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    failed_phases: list[str] = field(default_factory=list)
    retry_counts: dict[str, int] = field(default_factory=dict)


def create_phase_node(phase_type: PhaseType, agent_type: AgentType):
    """Create a node function for a phase using autonomous agents."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service

    async def node(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
        phase_key = phase_type.value

        # Initialize phase result
        if "phase_results" not in state:
            state["phase_results"] = {}

        state["phase_results"][phase_key] = PhaseResult(
            phase=phase_type,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        # Update progress
        if "progress" in state:
            state["progress"]["current_phase"] = phase_type.value

        try:
            # Create autonomous agent with dependencies
            agent = create_autonomous_agent(
                agent_type,
                tool_invoker=get_tool_invoker(),
                reasoning_loop=get_reasoning_loop(),
                memory_service=get_memory_service(),
                session_id=state.get("session_id"),
            )
            
            # Execute using reasoning loop
            trace = await agent.execute_with_tools(
                task=state.get("task", ""),
                session_id=state.get("session_id", ""),
                context=state.get("context", {}),
            )

            # Extract result
            phase_result = PhaseResult(
                phase=phase_type,
                status=TaskStatus.COMPLETED,
                result=trace.final_result or {},
                completed_at=datetime.utcnow(),
            )
            phase_result.duration = (
                phase_result.completed_at - phase_result.started_at
            ).total_seconds() if phase_result.started_at else 0

            state["phase_results"][phase_key] = phase_result

            # Update progress
            if "progress" in state:
                state["progress"]["completed_phases"] += 1

            # Store trace in agent_states
            state["agent_states"][phase_key] = {"trace": trace.to_dict()}
            state["result"] = trace.final_result

        except Exception as e:
            # Handle failure
            retry_count = state.get("retry_counts", {}).get(phase_key, 0)
            state["retry_counts"][phase_key] = retry_count

            phase_result = PhaseResult(
                phase=phase_type,
                status=TaskStatus.FAILED,
                error=str(e),
                retry_count=retry_count,
                completed_at=datetime.utcnow(),
            )
            phase_result.duration = (
                phase_result.completed_at - phase_result.started_at
            ).total_seconds() if phase_result.started_at else 0

            state["phase_results"][phase_key] = phase_result
            state["failed_phases"].append(phase_key)

            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"{phase_key}: {str(e)}")

        state["current_agent"] = phase_type.value
        return state

    return node


def create_parallel_phase_node(phase_types: list[PhaseType], agent_type: AgentType):
    """Create a node that executes multiple phases in parallel using autonomous agents."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service

    async def node(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
        if "phase_results" not in state:
            state["phase_results"] = {}

        # Run phases in parallel
        tasks = []
        for phase_type in phase_types:
            phase_key = phase_type.value

            state["phase_results"][phase_key] = PhaseResult(
                phase=phase_type,
                status=TaskStatus.RUNNING,
                started_at=datetime.utcnow(),
            )

            # Set current step context
            state["context"]["current_phase"] = phase_key

            # Create agent task using autonomous agent
            async def run_phase():
                agent = create_autonomous_agent(
                    agent_type,
                    tool_invoker=get_tool_invoker(),
                    reasoning_loop=get_reasoning_loop(),
                    memory_service=get_memory_service(),
                    session_id=state.get("session_id"),
                )
                trace = await agent.execute_with_tools(
                    task=state.get("task", ""),
                    session_id=state.get("session_id", ""),
                    context=state.get("context", {}),
                )
                return PhaseResult(
                    phase=phase_type,
                    status=TaskStatus.COMPLETED,
                    result=trace.final_result or {},
                    completed_at=datetime.utcnow(),
                )
            tasks.append(run_phase())

        # Execute all phases in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            phase_type = phase_types[i]
            phase_key = phase_type.value

            if isinstance(result, Exception):
                phase_result = PhaseResult(
                    phase=phase_type,
                    status=TaskStatus.FAILED,
                    error=str(result),
                    completed_at=datetime.utcnow(),
                )
                state["failed_phases"].append(phase_key)
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(f"{phase_key}: {str(result)}")
            else:
                phase_result = result

            phase_result.duration = (
                phase_result.completed_at - phase_result.started_at
            ).total_seconds() if phase_result.started_at else 0

            state["phase_results"][phase_key] = phase_result

        # Update progress
        if "progress" in state:
            state["progress"]["completed_phases"] += len(phase_types)

        state["current_agent"] = "parallel"
        return state

    return node



def create_advanced_workflow(
    include_phases: list[PhaseType] | None = None,
) -> StateGraph:
    """Create the advanced workflow graph with parallel execution and dependencies.

    Workflow structure:
        Planner
           ↓
    ┌──────────────────────────────┐
    │  Research  Backend  Frontend│
    │  Database  Documentation   │
    └──────────────────────────────┘
                  ↓
              Reviewer
                  ↓
              Tester
                  ↓
              Manager
    """
    if include_phases is None:
        include_phases = [
            PhaseType.PLANNING,
            PhaseType.RESEARCH,
            PhaseType.BACKEND,
            PhaseType.FRONTEND,
            PhaseType.DATABASE,
            PhaseType.DOCUMENTATION,
            PhaseType.REVIEW,
            PhaseType.TEST,
            PhaseType.MANAGER,
        ]

    workflow = StateGraph(AdvancedWorkflowState)

    # Phase to agent type mapping
    phase_to_agent = {
        PhaseType.PLANNING: AgentType.PLANNER,
        PhaseType.RESEARCH: AgentType.RESEARCHER,
        PhaseType.BACKEND: AgentType.CODER,
        PhaseType.FRONTEND: AgentType.CODER,
        PhaseType.DATABASE: AgentType.CODER,
        PhaseType.DOCUMENTATION: AgentType.DOCUMENTATION,
        PhaseType.REVIEW: AgentType.REVIEWER,
        PhaseType.TEST: AgentType.TESTER,
        PhaseType.MANAGER: AgentType.MANAGER,
    }

    # Add planning phase (always first)
    if PhaseType.PLANNING in include_phases:
        workflow.add_node(
            PhaseType.PLANNING.value,
            create_phase_node(PhaseType.PLANNING, AgentType.PLANNER),
        )

    # Define parallel phases
    parallel_phases = [
        PhaseType.RESEARCH,
        PhaseType.BACKEND,
        PhaseType.FRONTEND,
        PhaseType.DATABASE,
        PhaseType.DOCUMENTATION,
    ]

    # Add parallel phases
    active_parallel = [p for p in parallel_phases if p in include_phases]
    if active_parallel:
        workflow.add_node(
            "parallel_execution",
            create_parallel_phase_node(active_parallel, AgentType.CODER),
        )

    # Add review phase
    if PhaseType.REVIEW in include_phases:
        workflow.add_node(
            PhaseType.REVIEW.value,
            create_phase_node(PhaseType.REVIEW, AgentType.REVIEWER),
        )

    # Add test phase
    if PhaseType.TEST in include_phases:
        workflow.add_node(
            PhaseType.TEST.value,
            create_phase_node(PhaseType.TEST, AgentType.TESTER),
        )

    # Add manager phase (always last)
    if PhaseType.MANAGER in include_phases:
        workflow.add_node(
            PhaseType.MANAGER.value,
            create_phase_node(PhaseType.MANAGER, AgentType.MANAGER),
        )

    # Set entry point
    workflow.set_entry_point(PhaseType.PLANNING.value)

    # Connect phases
    if PhaseType.PLANNING in include_phases:
        if active_parallel:
            workflow.add_edge(PhaseType.PLANNING.value, "parallel_execution")
        elif PhaseType.REVIEW in include_phases:
            workflow.add_edge(PhaseType.PLANNING.value, PhaseType.REVIEW.value)
        elif PhaseType.TEST in include_phases:
            workflow.add_edge(PhaseType.PLANNING.value, PhaseType.TEST.value)
        elif PhaseType.MANAGER in include_phases:
            workflow.add_edge(PhaseType.PLANNING.value, PhaseType.MANAGER.value)

    # Connect parallel to review
    if active_parallel:
        if PhaseType.REVIEW in include_phases:
            workflow.add_edge("parallel_execution", PhaseType.REVIEW.value)
        elif PhaseType.TEST in include_phases:
            workflow.add_edge("parallel_execution", PhaseType.TEST.value)
        elif PhaseType.MANAGER in include_phases:
            workflow.add_edge("parallel_execution", PhaseType.MANAGER.value)

    # Connect review to test
    if PhaseType.REVIEW in include_phases and PhaseType.TEST in include_phases:
        workflow.add_edge(PhaseType.REVIEW.value, PhaseType.TEST.value)
    elif PhaseType.REVIEW in include_phases and PhaseType.MANAGER in include_phases:
        workflow.add_edge(PhaseType.REVIEW.value, PhaseType.MANAGER.value)

    # Connect test to manager
    if PhaseType.TEST in include_phases and PhaseType.MANAGER in include_phases:
        workflow.add_edge(PhaseType.TEST.value, PhaseType.MANAGER.value)

    # End at manager or last phase
    if PhaseType.MANAGER in include_phases:
        workflow.add_edge(PhaseType.MANAGER.value, END)
    elif PhaseType.TEST in include_phases:
        workflow.add_edge(PhaseType.TEST.value, END)
    elif PhaseType.REVIEW in include_phases:
        workflow.add_edge(PhaseType.REVIEW.value, END)
    elif active_parallel:
        workflow.add_edge("parallel_execution", END)
    elif PhaseType.PLANNING in include_phases:
        workflow.add_edge(PhaseType.PLANNING.value, END)

    return workflow.compile()


class AdvancedAgentWorkflow:
    """Advanced workflow manager with parallel execution, retries, and progress tracking."""

    def __init__(
        self,
        llm_provider: str | None = None,
        include_phases: list[PhaseType] | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.llm_provider = llm_provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.workflow = create_advanced_workflow(include_phases)
        self._active_workflows: dict[str, WorkflowProgress] = {}

    async def run(
        self,
        task: str,
        session_id: str,
        context: dict[str, Any] | None = None,
        priorities: dict[str, int] | None = None,
        dependencies: dict[str, list[str]] | None = None,
    ) -> tuple[AdvancedWorkflowState, WorkflowProgress]:
        """Run the advanced workflow for a task.

        Args:
            task: Task description
            session_id: Session ID
            context: Additional context
            priorities: Task priorities (higher = more important)
            dependencies: Task dependencies

        Returns:
            Tuple of (result state, workflow progress)
        """
        workflow_id = str(uuid.uuid4())

        # Create initial state
        initial_state: AdvancedWorkflowState = {
            "session_id": session_id,
            "task": task,
            "context": context or {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
            "workflow_id": workflow_id,
            "progress": {
                "total_phases": 9,  # Total phases in full workflow
                "completed_phases": 0,
                "current_phase": None,
            },
            "phase_results": {},
            "task_priorities": priorities or {},
            "dependencies": dependencies or {},
            "failed_phases": [],
            "retry_counts": {},
        }

        # Track progress
        progress = WorkflowProgress(
            workflow_id=workflow_id,
            task=task,
            total_phases=initial_state["progress"]["total_phases"],
        )
        self._active_workflows[workflow_id] = progress

        try:
            result = await self.workflow.ainvoke(initial_state)

            # Update progress with results
            for phase, phase_result in result.get("phase_results", {}).items():
                progress.phase_results[PhaseType(phase)] = phase_result

            progress.completed_phases = result.get("progress", {}).get("completed_phases", 0)
            progress.completed_at = datetime.utcnow()
            progress.errors = result.get("errors", [])

            return result, progress

        finally:
            # Cleanup
            self._active_workflows.pop(workflow_id, None)

    async def run_with_recovery(
        self,
        task: str,
        session_id: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[AdvancedWorkflowState, WorkflowProgress]:
        """Run workflow with automatic failure recovery.

        Retries failed phases up to max_retries times.
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                result, progress = await self.run(task, session_id, context)

                # Check if any phases failed
                failed = progress.get_failed_phases()
                if not failed:
                    return result, progress

                # If this is not the last attempt, retry failed phases
                if attempt < self.max_retries:
                    last_error = f"Attempt {attempt + 1}: Failed phases: {[p.value for p in failed]}"
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    context = context or {}
                    context["retry_attempt"] = attempt + 1
                    context["failed_phases"] = [p.value for p in failed]
                    continue

                return result, progress

            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue

        # All retries failed
        return {
            "error": last_error or "Workflow failed after all retries",
            "failed_phases": [],
        }, WorkflowProgress(
            workflow_id="failed",
            task=task,
            total_phases=0,
            errors=[last_error] if last_error else ["Unknown error"],
        )

    def get_progress(self, workflow_id: str) -> WorkflowProgress | None:
        """Get progress for a workflow."""
        return self._active_workflows.get(workflow_id)

    def list_active_workflows(self) -> list[WorkflowProgress]:
        """List all active workflows."""
        return list(self._active_workflows.values())


class ParallelTaskExecutor:
    """Execute multiple tasks in parallel with dependency management."""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(
        self,
        tasks: list[dict[str, Any]],
        dependencies: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """Execute tasks in parallel with dependency management.

        Args:
            tasks: List of task dicts with 'id' and 'func' keys
            dependencies: Map of task_id to list of dependent task_ids

        Returns:
            Dict of task_id to result
        """
        dependencies = dependencies or {}
        results: dict[str, Any] = {}
        completed: set[str] = set()
        pending = {task["id"]: task for task in tasks}

        async def run_task(task_id: str, func: Callable) -> tuple[str, Any]:
            async with self._semaphore:
                # Wait for dependencies
                deps = dependencies.get(task_id, [])
                for dep_id in deps:
                    while dep_id not in completed:
                        if dep_id in pending:
                            await asyncio.sleep(0.1)
                        else:
                            break

                try:
                    result = await func()
                    completed.add(task_id)
                    return task_id, result
                except Exception as e:
                    completed.add(task_id)
                    return task_id, {"error": str(e)}

        # Create all tasks
        task_coroutines = [
            run_task(task["id"], task["func"])
            for task in tasks
            if task["id"] in pending
        ]

        # Execute all tasks
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Collect results
        for i, result in enumerate(task_results):
            task_id = tasks[i]["id"]
            if isinstance(result, Exception):
                results[task_id] = {"error": str(result)}
            else:
                task_key, task_result = result
                results[task_key] = task_result

        return results


# Default workflow instance
_default_workflow: AdvancedAgentWorkflow | None = None


def get_advanced_workflow() -> AdvancedAgentWorkflow:
    """Get the default advanced workflow instance."""
    global _default_workflow
    if _default_workflow is None:
        _default_workflow = AdvancedAgentWorkflow()
    return _default_workflow
