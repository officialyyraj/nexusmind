"""Tests for advanced workflow."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.advanced_workflow import (
    AdvancedAgentWorkflow,
    AdvancedWorkflowState,
    PhaseConfig,
    PhaseResult,
    PhaseType,
    ParallelTaskExecutor,
    TaskStatus,
    WorkflowProgress,
    create_advanced_workflow,
    create_phase_node,
    get_advanced_workflow,
)
from app.agents.types import AgentType


class TestPhaseType:
    """Test PhaseType enum."""

    def test_phase_values(self):
        """Test phase type values."""
        assert PhaseType.PLANNING.value == "planning"
        assert PhaseType.RESEARCH.value == "research"
        assert PhaseType.BACKEND.value == "backend"
        assert PhaseType.FRONTEND.value == "frontend"
        assert PhaseType.DATABASE.value == "database"
        assert PhaseType.DOCUMENTATION.value == "documentation"
        assert PhaseType.REVIEW.value == "review"
        assert PhaseType.TEST.value == "test"
        assert PhaseType.MANAGER.value == "manager"


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRYING.value == "retrying"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestPhaseResult:
    """Test PhaseResult dataclass."""

    def test_phase_result_defaults(self):
        """Test PhaseResult default values."""
        result = PhaseResult(phase=PhaseType.PLANNING, status=TaskStatus.PENDING)
        assert result.phase == PhaseType.PLANNING
        assert result.status == TaskStatus.PENDING
        assert result.result == {}
        assert result.error is None
        assert result.retry_count == 0
        assert result.started_at is None
        assert result.completed_at is None
        assert result.duration == 0.0

    def test_phase_result_with_data(self):
        """Test PhaseResult with data."""
        now = datetime.utcnow()
        result = PhaseResult(
            phase=PhaseType.RESEARCH,
            status=TaskStatus.COMPLETED,
            result={"findings": ["item1", "item2"]},
            retry_count=1,
            started_at=now,
            completed_at=now,
            duration=5.5,
        )
        assert result.result["findings"] == ["item1", "item2"]
        assert result.duration == 5.5


class TestWorkflowProgress:
    """Test WorkflowProgress dataclass."""

    def test_progress_defaults(self):
        """Test WorkflowProgress default values."""
        progress = WorkflowProgress(
            workflow_id="test-123",
            task="Test task",
            total_phases=5,
        )
        assert progress.workflow_id == "test-123"
        assert progress.task == "Test task"
        assert progress.total_phases == 5
        assert progress.completed_phases == 0
        assert progress.current_phase is None
        assert progress.phase_results == {}
        assert progress.errors == []
        assert progress.completed_at is None

    def test_progress_percent(self):
        """Test progress percentage calculation."""
        progress = WorkflowProgress(
            workflow_id="test-123",
            task="Test task",
            total_phases=4,
            completed_phases=2,
        )
        assert progress.progress_percent == 50.0

    def test_progress_percent_zero(self):
        """Test progress percentage with zero total."""
        progress = WorkflowProgress(
            workflow_id="test-123",
            task="Test task",
            total_phases=0,
        )
        assert progress.progress_percent == 0.0

    def test_is_complete(self):
        """Test is_complete property."""
        progress = WorkflowProgress(
            workflow_id="test-123",
            task="Test task",
            total_phases=3,
            completed_phases=3,
        )
        assert progress.is_complete is True

        progress.completed_phases = 2
        assert progress.is_complete is False

    def test_get_failed_phases(self):
        """Test getting failed phases."""
        progress = WorkflowProgress(
            workflow_id="test-123",
            task="Test task",
            total_phases=5,
        )
        progress.phase_results = {
            PhaseType.PLANNING: PhaseResult(phase=PhaseType.PLANNING, status=TaskStatus.COMPLETED),
            PhaseType.RESEARCH: PhaseResult(phase=PhaseType.RESEARCH, status=TaskStatus.FAILED),
            PhaseType.BACKEND: PhaseResult(phase=PhaseType.BACKEND, status=TaskStatus.COMPLETED),
        }

        failed = progress.get_failed_phases()
        assert len(failed) == 1
        assert PhaseType.RESEARCH in failed


class TestPhaseConfig:
    """Test PhaseConfig dataclass."""

    def test_phase_config_defaults(self):
        """Test PhaseConfig default values."""
        config = PhaseConfig(
            phase=PhaseType.PLANNING,
            agent_type=AgentType.PLANNER,
        )
        assert config.required is True
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout == 300.0
        assert config.depends_on == []
        assert config.parallel_with == []

    def test_phase_config_with_deps(self):
        """Test PhaseConfig with dependencies."""
        config = PhaseConfig(
            phase=PhaseType.BACKEND,
            agent_type=AgentType.CODER,
            depends_on=[PhaseType.PLANNING, PhaseType.RESEARCH],
            parallel_with=[PhaseType.FRONTEND, PhaseType.DATABASE],
        )
        assert PhaseType.PLANNING in config.depends_on
        assert PhaseType.FRONTEND in config.parallel_with


class TestAdvancedWorkflowState:
    """Test AdvancedWorkflowState."""

    def test_state_creation(self):
        """Test state creation."""
        state: AdvancedWorkflowState = {
            "session_id": "test-session",
            "task": "Build a web app",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
            "workflow_id": "wf-123",
            "progress": {"total_phases": 5, "completed_phases": 0},
            "phase_results": {},
            "task_priorities": {"backend": 1, "frontend": 2},
            "dependencies": {"backend": ["planning"]},
            "failed_phases": [],
            "retry_counts": {},
        }
        assert state["workflow_id"] == "wf-123"
        assert state["task_priorities"]["frontend"] == 2


class TestCreateAdvancedWorkflow:
    """Test workflow creation."""

    def test_create_full_workflow(self):
        """Test creating full workflow."""
        workflow = create_advanced_workflow()
        assert workflow is not None

    def test_create_partial_workflow(self):
        """Test creating partial workflow with specific phases."""
        workflow = create_advanced_workflow([
            PhaseType.PLANNING,
            PhaseType.RESEARCH,
            PhaseType.REVIEW,
        ])
        assert workflow is not None

    def test_create_minimal_workflow(self):
        """Test creating minimal workflow."""
        workflow = create_advanced_workflow([PhaseType.PLANNING])
        assert workflow is not None


class TestAdvancedAgentWorkflow:
    """Test AdvancedAgentWorkflow class."""

    def test_workflow_creation(self):
        """Test workflow creation."""
        wf = AdvancedAgentWorkflow()
        assert wf.workflow is not None
        assert wf.max_retries == 3
        assert wf.retry_delay == 1.0

    def test_workflow_custom_config(self):
        """Test workflow with custom configuration."""
        wf = AdvancedAgentWorkflow(
            max_retries=5,
            retry_delay=2.0,
        )
        assert wf.max_retries == 5
        assert wf.retry_delay == 2.0

    def test_get_advanced_workflow_singleton(self):
        """Test singleton pattern."""
        wf1 = get_advanced_workflow()
        wf2 = get_advanced_workflow()
        assert wf1 is wf2

    def test_list_active_workflows(self):
        """Test listing active workflows."""
        wf = AdvancedAgentWorkflow()
        assert wf.list_active_workflows() == []


class TestParallelTaskExecutor:
    """Test ParallelTaskExecutor class."""

    @pytest.mark.asyncio
    async def test_execute_empty(self):
        """Test executing empty task list."""
        executor = ParallelTaskExecutor()
        results = await executor.execute([])
        assert results == {}

    @pytest.mark.asyncio
    async def test_execute_single_task(self):
        """Test executing single task."""
        executor = ParallelTaskExecutor()

        async def task_func():
            return {"result": "success"}

        tasks = [{"id": "task1", "func": task_func}]
        results = await executor.execute(tasks)

        assert "task1" in results
        assert results["task1"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_execute_parallel_tasks(self):
        """Test executing tasks in parallel."""
        executor = ParallelTaskExecutor()

        async def slow_task(delay: float):
            async def func():
                await asyncio.sleep(delay)
                return {"done": True}
            return func

        tasks = [
            {"id": "task1", "func": await slow_task(0.01)},
            {"id": "task2", "func": await slow_task(0.01)},
            {"id": "task3", "func": await slow_task(0.01)},
        ]

        import time
        start = time.time()
        results = await executor.execute(tasks)
        elapsed = time.time() - start

        # All tasks should complete in roughly the same time (parallel)
        assert elapsed < 0.1
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_execute_with_dependencies(self):
        """Test executing tasks with dependencies."""
        executor = ParallelTaskExecutor()
        execution_order = []

        async def make_task(task_id: str, delay: float = 0):
            async def func():
                if delay:
                    await asyncio.sleep(delay)
                execution_order.append(task_id)
                return {"id": task_id}
            return func

        tasks = [
            {"id": "task1", "func": await make_task("task1")},
            {"id": "task2", "func": await make_task("task2")},
            {"id": "task3", "func": await make_task("task3")},
        ]

        dependencies = {
            "task3": ["task1"],
            "task2": ["task1"],
        }

        results = await executor.execute(tasks, dependencies)

        assert execution_order[0] == "task1"
        # task2 and task3 should run after task1
        assert set(execution_order[1:]) == {"task2", "task3"}

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """Test handling task errors."""
        executor = ParallelTaskExecutor()

        async def error_task():
            raise ValueError("Task failed")

        async def success_task():
            return {"success": True}

        tasks = [
            {"id": "error", "func": error_task},
            {"id": "success", "func": success_task},
        ]

        results = await executor.execute(tasks)

        assert "error" in results
        assert "error" in results["error"]
        assert results["success"]["success"] is True


class TestAgentTypeImport:
    """Test AgentType import."""

    def test_agent_type_values(self):
        """Test AgentType enum values."""
        from app.agents.types import AgentType

        assert AgentType.PLANNER.value == "planner"
        assert AgentType.RESEARCHER.value == "researcher"
        assert AgentType.CODER.value == "coder"
        assert AgentType.REVIEWER.value == "reviewer"
        assert AgentType.TESTER.value == "tester"
        assert AgentType.DOCUMENTATION.value == "documentation"
        assert AgentType.MANAGER.value == "manager"
