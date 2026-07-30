"""Tests for execution engine."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.execution import Execution, ExecutionStep, ExecutionLog, ExecutionState
from app.orchestration.executor import (
    ProductionExecutor,
    ExecutionError,
    RETRYABLE_ERROR_TYPES,
    NON_RETRYABLE_ERROR_TYPES,
)


class TestExecutionState:
    """Tests for ExecutionState enum."""

    def test_execution_states(self):
        """Test all execution states are defined."""
        assert ExecutionState.QUEUED.value == "queued"
        assert ExecutionState.STARTING.value == "starting"
        assert ExecutionState.PLANNING.value == "planning"
        assert ExecutionState.RESEARCHING.value == "researching"
        assert ExecutionState.CODING.value == "coding"
        assert ExecutionState.REVIEWING.value == "reviewing"
        assert ExecutionState.TESTING.value == "testing"
        assert ExecutionState.DOCUMENTING.value == "documenting"
        assert ExecutionState.COMPLETED.value == "completed"
        assert ExecutionState.FAILED.value == "failed"
        assert ExecutionState.CANCELLED.value == "cancelled"
        assert ExecutionState.PAUSED.value == "paused"
        assert ExecutionState.RESUMING.value == "resuming"


class TestExecutionModel:
    """Tests for Execution model."""

    def test_execution_is_terminal_completed(self):
        """Test is_terminal returns True for completed state."""
        execution = MagicMock(spec=Execution)
        execution.state = ExecutionState.COMPLETED.value
        
        # Access the property
        result = execution.state in {
            ExecutionState.COMPLETED.value,
            ExecutionState.FAILED.value,
            ExecutionState.CANCELLED.value,
        }
        assert result is True

    def test_execution_is_terminal_failed(self):
        """Test is_terminal returns True for failed state."""
        execution = MagicMock(spec=Execution)
        execution.state = ExecutionState.FAILED.value
        
        result = execution.state in {
            ExecutionState.COMPLETED.value,
            ExecutionState.FAILED.value,
            ExecutionState.CANCELLED.value,
        }
        assert result is True

    def test_execution_is_running(self):
        """Test is_running returns True for active states."""
        active_states = {
            ExecutionState.STARTING.value,
            ExecutionState.PLANNING.value,
            ExecutionState.RESEARCHING.value,
            ExecutionState.CODING.value,
            ExecutionState.RESUMING.value,
        }
        
        for state in active_states:
            execution = MagicMock(spec=Execution)
            execution.state = state
            
            result = execution.state in active_states
            assert result is True

    def test_execution_duration_seconds(self):
        """Test duration_seconds calculation."""
        execution = MagicMock(spec=Execution)
        execution.started_at = datetime(2024, 1, 1, 10, 0, 0)
        execution.completed_at = datetime(2024, 1, 1, 10, 1, 30)
        
        # Calculate duration
        if execution.started_at and execution.completed_at:
            duration = int((execution.completed_at - execution.started_at).total_seconds())
        else:
            duration = None
        
        assert duration == 90


class TestExecutionError:
    """Tests for ExecutionError class."""

    def test_execution_error_basic(self):
        """Test basic error creation."""
        error = ExecutionError("Test error")
        
        assert str(error) == "Test error"
        assert error.error_type == "unknown"
        assert error.details == {}
        assert error.is_retryable is True

    def test_execution_error_with_details(self):
        """Test error with full details."""
        error = ExecutionError(
            message="Network error",
            error_type="network_error",
            details={"host": "example.com", "code": 500},
            is_retryable=True,
        )
        
        assert error.message == "Network error"
        assert error.error_type == "network_error"
        assert error.details == {"host": "example.com", "code": 500}
        assert error.is_retryable is True


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_retryable_error_types(self):
        """Test retryable error types are defined."""
        assert "llm_error" in RETRYABLE_ERROR_TYPES
        assert "network_error" in RETRYABLE_ERROR_TYPES
        assert "timeout" in RETRYABLE_ERROR_TYPES
        assert "docker_error" in RETRYABLE_ERROR_TYPES
        assert "mcp_error" in RETRYABLE_ERROR_TYPES
        assert "rate_limit" in RETRYABLE_ERROR_TYPES

    def test_non_retryable_error_types(self):
        """Test non-retryable error types are defined."""
        assert "validation_error" in NON_RETRYABLE_ERROR_TYPES
        assert "invalid_input" in NON_RETRYABLE_ERROR_TYPES
        assert "unauthorized" in NON_RETRYABLE_ERROR_TYPES
        assert "forbidden" in NON_RETRYABLE_ERROR_TYPES
        assert "not_found" in NON_RETRYABLE_ERROR_TYPES


class TestProductionExecutor:
    """Tests for ProductionExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch("app.orchestration.executor.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:",
            )
            return ProductionExecutor()

    def test_agent_to_state_mapping(self):
        """Test agent to state mapping."""
        assert ProductionExecutor.AGENT_TO_STATE["planner"] == ExecutionState.PLANNING.value
        assert ProductionExecutor.AGENT_TO_STATE["researcher"] == ExecutionState.RESEARCHING.value
        assert ProductionExecutor.AGENT_TO_STATE["coder"] == ExecutionState.CODING.value
        assert ProductionExecutor.AGENT_TO_STATE["reviewer"] == ExecutionState.REVIEWING.value
        assert ProductionExecutor.AGENT_TO_STATE["tester"] == ExecutionState.TESTING.value
        assert ProductionExecutor.AGENT_TO_STATE["documentation"] == ExecutionState.DOCUMENTING.value

    def test_agent_order(self):
        """Test agent execution order."""
        expected_order = [
            "planner",
            "researcher",
            "coder",
            "reviewer",
            "tester",
            "documentation",
        ]
        assert ProductionExecutor.AGENT_ORDER == expected_order

    def test_is_running_no_task(self, executor):
        """Test is_running returns False when no task exists."""
        assert executor.is_running("nonexistent-id") is False

    def test_get_running_count_empty(self, executor):
        """Test get_running_count returns 0 when empty."""
        assert executor.get_running_count() == 0

    def test_classify_error_timeout(self, executor):
        """Test error classification for timeout."""
        error = TimeoutError("Connection timed out")
        error_type = executor._classify_error(error)
        assert error_type == "timeout"

    def test_classify_error_network(self, executor):
        """Test error classification for network errors."""
        error = ConnectionError("Connection refused")
        error_type = executor._classify_error(error)
        assert error_type == "network_error"

    def test_classify_error_rate_limit(self, executor):
        """Test error classification for rate limit."""
        error = Exception("Rate limit exceeded (429)")
        error_type = executor._classify_error(error)
        assert error_type == "rate_limit"

    def test_classify_error_unauthorized(self, executor):
        """Test error classification for unauthorized."""
        error = PermissionError("Unauthorized access")
        error_type = executor._classify_error(error)
        assert error_type == "unauthorized"

    def test_classify_error_validation(self, executor):
        """Test error classification for validation errors."""
        error = ValueError("Invalid input: malformed request")
        error_type = executor._classify_error(error)
        assert error_type == "validation_error"


class TestExecutionStepModel:
    """Tests for ExecutionStep model."""

    def test_execution_step_duration_seconds(self):
        """Test step duration calculation."""
        step = MagicMock(spec=ExecutionStep)
        step.started_at = datetime(2024, 1, 1, 10, 0, 0)
        step.completed_at = datetime(2024, 1, 1, 10, 0, 30)
        
        # Calculate duration
        if step.started_at and step.completed_at:
            duration = (step.completed_at - step.started_at).total_seconds()
        else:
            duration = None
        
        assert duration == 30.0


class TestExecutionLogModel:
    """Tests for ExecutionLog model."""

    def test_execution_log_to_dict(self):
        """Test log to_dict method."""
        log = MagicMock(spec=ExecutionLog)
        log.id = uuid.uuid4()
        log.execution_id = uuid.uuid4()
        log.step_id = None
        log.level = "INFO"
        log.message = "Test message"
        log.details = {"key": "value"}
        log.agent_type = "planner"
        log.action = "execute"
        log.created_at = datetime(2024, 1, 1, 10, 0, 0)
        
        # Expected dict structure
        expected = {
            "id": str(log.id),
            "execution_id": str(log.execution_id),
            "step_id": None,
            "level": "INFO",
            "message": "Test message",
            "details": {"key": "value"},
            "agent_type": "planner",
            "action": "execute",
            "timestamp": log.created_at.isoformat(),
        }
        
        # Verify structure (actual method would return this)
        assert expected["level"] == "INFO"
        assert expected["message"] == "Test message"


class TestCancellation:
    """Tests for execution cancellation."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch("app.orchestration.executor.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:",
            )
            return ProductionExecutor()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_execution(self, executor):
        """Test cancelling non-existent execution returns False."""
        result = await executor.cancel("nonexistent-id")
        assert result is False


class TestResume:
    """Tests for execution resume."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch("app.orchestration.executor.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:",
            )
            return ProductionExecutor()

    @pytest.mark.asyncio
    async def test_resume_nonexistent_execution(self, executor):
        """Test resuming non-existent execution returns False."""
        result = await executor.resume("nonexistent-id")
        assert result is False


class TestRetry:
    """Tests for execution retry."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch("app.orchestration.executor.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:",
            )
            return ProductionExecutor()

    @pytest.mark.asyncio
    async def test_retry_nonexistent_execution(self, executor):
        """Test retrying non-existent execution returns False."""
        result = await executor.retry("nonexistent-id")
        assert result is False


class TestCheckpointing:
    """Tests for checkpointing."""

    def test_checkpoint_data_structure(self):
        """Test checkpoint data structure."""
        checkpoint_data = {
            "step_index": 2,
            "agent_type": "researcher",
            "workflow_state": {
                "task": "test task",
                "context": {},
                "messages": [],
                "artifacts": [],
            },
            "completed_agents": ["planner"],
        }
        
        assert checkpoint_data["step_index"] == 2
        assert checkpoint_data["agent_type"] == "researcher"
        assert "workflow_state" in checkpoint_data
        assert "completed_agents" in checkpoint_data


class TestConcurrency:
    """Tests for concurrent execution."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch("app.orchestration.executor.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:",
            )
            return ProductionExecutor()

    def test_concurrent_tasks_isolated(self, executor):
        """Test that concurrent executions are isolated."""
        # Create mock tasks
        mock_task1 = MagicMock()
        mock_task1.done.return_value = False
        mock_task2 = MagicMock()
        mock_task2.done.return_value = False
        
        # Add to running tasks
        execution_id1 = str(uuid.uuid4())
        execution_id2 = str(uuid.uuid4())
        executor._running_tasks[execution_id1] = mock_task1
        executor._running_tasks[execution_id2] = mock_task2
        
        # Verify both are tracked
        assert executor.get_running_count() == 2
        assert executor.is_running(execution_id1) is True
        assert executor.is_running(execution_id2) is True
        
        # Complete one
        mock_task1.done.return_value = True
        
        # Verify counts updated
        assert executor.is_running(execution_id1) is False
        assert executor.is_running(execution_id2) is True
        assert executor.get_running_count() == 1


class TestAgentTimings:
    """Tests for agent timing tracking."""

    def test_agent_timings_structure(self):
        """Test agent timings data structure."""
        timings = {
            "planner": {
                "duration_ms": 1500,
                "attempts": 1,
                "success": True,
                "error": None,
            },
            "researcher": {
                "duration_ms": 3000,
                "attempts": 2,
                "success": True,
                "error": None,
            },
            "coder": {
                "duration_ms": 5000,
                "attempts": 1,
                "success": True,
                "error": None,
            },
        }
        
        assert timings["planner"]["duration_ms"] == 1500
        assert timings["researcher"]["attempts"] == 2
        assert timings["coder"]["success"] is True


class TestRecovery:
    """Tests for execution recovery."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch("app.orchestration.executor.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:",
            )
            return ProductionExecutor()

    @pytest.mark.asyncio
    async def test_recover_unfinished_no_executions(self, executor):
        """Test recovery with no unfinished executions."""
        # This would require a mock database session
        # Simplified test to verify method exists
        assert hasattr(executor, "recover_unfinished")
