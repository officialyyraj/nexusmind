"""Integration test configuration and fixtures."""

import asyncio
import json
import tempfile
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.agents.base import AgentState
from app.agents.implementations import (
    CoderAgent,
    DocumentationAgent,
    PlannerAgent,
    ResearcherAgent,
    ReviewerAgent,
    TaskPlan,
    TaskStep,
    TesterAgent,
)
from app.agents.workflow import AgentWorkflow, create_full_workflow
from app.db.session import Session, User
from app.memory.chromadb import ChromaMemoryService


# ============================================================================
# Mock LLM Fixtures
# ============================================================================

class MockLLMResponse:
    """Mock LLM response for testing."""

    def __init__(self, content: str, model: str = "mock-model"):
        self.content = content
        self.model = model
        self.usage = {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60}
        self.finish_reason = "stop"


class MockLLMProvider:
    """Mock LLM provider for integration tests."""

    def __init__(self, responses: dict[str, str] | None = None):
        self._responses = responses or {}
        self._call_history: list[dict[str, Any]] = []
        self.model = "mock-model"

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> MockLLMResponse:
        """Mock chat completion."""
        # Record call
        self._call_history.append({
            "messages": messages,
            "kwargs": kwargs,
        })

        # Build response based on last message content
        last_message = messages[-1]["content"] if messages else ""

        # Check for specific patterns
        for pattern, response in self._responses.items():
            if pattern.lower() in last_message.lower():
                return MockLLMResponse(response)

        # Default responses based on content patterns
        if "plan" in last_message.lower() or "decompos" in last_message.lower():
            return MockLLMResponse(self._generate_plan_response())
        elif "research" in last_message.lower() or "search" in last_message.lower():
            return MockLLMResponse(self._generate_research_response())
        elif "implement" in last_message.lower() or "code" in last_message.lower():
            return MockLLMResponse(self._generate_code_response())
        elif "review" in last_message.lower():
            return MockLLMResponse(self._generate_review_response())
        elif "test" in last_message.lower():
            return MockLLMResponse(self._generate_test_response())
        elif "document" in last_message.lower():
            return MockLLMResponse(self._generate_doc_response())
        else:
            return MockLLMResponse('{"status": "success", "message": "Completed"}')

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Mock streaming response."""
        response = await self.chat(messages, **kwargs)
        for char in response.content:
            yield char

    def _generate_plan_response(self) -> str:
        """Generate a mock plan response."""
        plan = {
            "task": "Build a calculator",
            "steps": [
                {
                    "step_id": "req_analysis",
                    "title": "Analyze Requirements",
                    "description": "Analyze requirements for calculator",
                    "agent_type": "researcher",
                    "estimated_duration": "5-10 min",
                    "priority": 10,
                },
                {
                    "step_id": "core_implementation",
                    "title": "Implement Core Functionality",
                    "description": "Write the calculator implementation",
                    "agent_type": "coder",
                    "dependencies": ["req_analysis"],
                    "estimated_duration": "30-60 min",
                    "priority": 8,
                },
                {
                    "step_id": "testing",
                    "title": "Write and Run Tests",
                    "description": "Create test cases",
                    "agent_type": "tester",
                    "dependencies": ["core_implementation"],
                    "estimated_duration": "15-20 min",
                    "priority": 6,
                },
            ],
        }
        return json.dumps(plan)

    def _generate_research_response(self) -> str:
        """Generate a mock research response."""
        return json.dumps({
            "findings": [
                {"source": "web", "content": "Python is great for calculators"},
                {"source": "docs", "content": "Use eval carefully for security"},
            ],
            "summary": "Research complete",
        })

    def _generate_code_response(self) -> str:
        """Generate a mock code response."""
        return json.dumps({
            "files": [
                {
                    "name": "calculator.py",
                    "path": "/workspace/calculator.py",
                    "content": "def add(a, b): return a + b\ndef subtract(a, b): return a - b",
                    "language": "python",
                }
            ],
            "status": "success",
        })

    def _generate_review_response(self) -> str:
        """Generate a mock review response."""
        return json.dumps({
            "issues": [],
            "score": 9,
            "suggestions": ["Code looks good!"],
            "status": "success",
        })

    def _generate_test_response(self) -> str:
        """Generate a mock test response."""
        return json.dumps({
            "tests": ["test_add", "test_subtract"],
            "coverage": 85,
            "passed": True,
            "status": "success",
        })

    def _generate_doc_response(self) -> str:
        """Generate a mock documentation response."""
        return json.dumps({
            "sections": ["Overview", "Usage", "API Reference"],
            "readme": "# Calculator\nA simple calculator.",
            "status": "success",
        })

    @property
    def call_history(self) -> list[dict[str, Any]]:
        """Get call history."""
        return self._call_history

    def reset_history(self) -> None:
        """Reset call history."""
        self._call_history = []


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_llm_responses() -> dict[str, str]:
    """Default mock LLM responses."""
    return {
        "plan": '{"steps": []}',
        "research": '{"findings": []}',
        "code": '{"files": []}',
        "review": '{"issues": [], "score": 10}',
        "test": '{"tests": [], "coverage": 100}',
        "document": '{"sections": []}',
    }


# ============================================================================
# Mock Session Storage Fixtures
# ============================================================================

class MockSessionStorage:
    """Mock session storage for testing."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._state_history: dict[str, list[AgentState]] = {}
        self._failures: dict[str, int] = {}
        self._retry_counts: dict[str, int] = {}

    def save_session(self, session_id: str, state: dict[str, Any]) -> None:
        """Save session state."""
        self._sessions[session_id] = state.copy()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session state."""
        return self._sessions.get(session_id)

    def save_state_snapshot(self, session_id: str, state: AgentState) -> None:
        """Save state snapshot for persistence testing."""
        if session_id not in self._state_history:
            self._state_history[session_id] = []
        self._state_history[session_id].append(state.copy())

    def get_state_history(self, session_id: str) -> list[AgentState]:
        """Get state history for persistence testing."""
        return self._state_history.get(session_id, [])

    def simulate_failure(self, session_id: str, fail_count: int = 1) -> None:
        """Simulate failures for testing."""
        self._failures[session_id] = fail_count

    def get_failure_count(self, session_id: str) -> int:
        """Get failure count."""
        return self._failures.get(session_id, 0)

    def clear_failures(self, session_id: str) -> None:
        """Clear failures."""
        self._failures[session_id] = 0

    def increment_retry(self, session_id: str) -> int:
        """Increment and return retry count."""
        self._retry_counts[session_id] = self._retry_counts.get(session_id, 0) + 1
        return self._retry_counts[session_id]

    def get_retry_count(self, session_id: str) -> int:
        """Get retry count."""
        return self._retry_counts.get(session_id, 0)

    def reset(self) -> None:
        """Reset all data."""
        self._sessions.clear()
        self._state_history.clear()
        self._failures.clear()
        self._retry_counts.clear()


@pytest.fixture
def mock_session_storage() -> MockSessionStorage:
    """Create a mock session storage."""
    return MockSessionStorage()


# ============================================================================
# State Fixtures
# ============================================================================

@pytest.fixture
def initial_agent_state() -> AgentState:
    """Create initial agent state for testing."""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "task": "Build a simple calculator",
        "context": {},
        "messages": [],
        "artifacts": [],
        "agent_states": {},
        "current_agent": None,
        "result": None,
        "error": None,
    }


@pytest.fixture
def task_with_context() -> dict[str, Any]:
    """Task with additional context."""
    return {
        "task": "Create a REST API for user management",
        "context": {
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql",
            "task_type": "implementation",
        },
    }


# ============================================================================
# Temp Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture
def temp_memory_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for memory storage."""
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir


# ============================================================================
# Workflow Fixtures
# ============================================================================

@pytest.fixture
def workflow_with_mock_llm(mock_llm_provider: MockLLMProvider) -> AgentWorkflow:
    """Create workflow with mocked LLM."""
    with patch("app.agents.implementations.LLMService") as MockLLM:
        mock_instance = MagicMock()
        mock_instance.chat = AsyncMock(return_value=MockLLMResponse('{"status": "success"}'))
        MockLLM.return_value = mock_instance

        workflow = AgentWorkflow(workflow_type="full")
        return workflow


@pytest.fixture
def full_workflow_graph():
    """Get the compiled full workflow graph."""
    return create_full_workflow()


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock LLM Service Patch
# ============================================================================

@pytest.fixture
def patch_llm_service(mock_llm_provider: MockLLMProvider):
    """Patch the LLM service for all agents."""
    with patch("app.llm.service.LLMService.chat", new=mock_llm_provider.chat):
        with patch("app.llm.service.LLMService.stream", new=mock_llm_provider.stream):
            yield mock_llm_provider


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_implementation_task() -> str:
    """Sample implementation task."""
    return "Create a REST API for managing todo items with CRUD operations"


@pytest.fixture
def sample_bug_fix_task() -> str:
    """Sample bug fix task."""
    return "Fix the login bug where users cannot log in with special characters in password"


@pytest.fixture
def sample_research_task() -> str:
    """Sample research task."""
    return "Research the best practices for implementing authentication in FastAPI"


# ============================================================================
# Error Simulation Fixtures
# ============================================================================

class ErrorSimulator:
    """Helper class to simulate various error conditions."""

    def __init__(self):
        self._errors: dict[str, Exception] = {}
        self._error_counts: dict[str, int] = {}

    def register_error(self, key: str, error: Exception) -> None:
        """Register an error to be raised."""
        self._errors[key] = error
        self._error_counts[key] = 0

    def should_raise(self, key: str) -> bool:
        """Check if we should raise the error."""
        return key in self._errors

    def raise_error(self, key: str) -> None:
        """Raise the registered error."""
        if key in self._errors:
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
            raise self._errors[key]

    def get_error_count(self, key: str) -> int:
        """Get how many times an error was raised."""
        return self._error_counts.get(key, 0)

    def clear(self) -> None:
        """Clear all errors."""
        self._errors.clear()
        self._error_counts.clear()


@pytest.fixture
def error_simulator() -> ErrorSimulator:
    """Create an error simulator for testing."""
    return ErrorSimulator()


# ============================================================================
# Retry Configuration Fixtures
# ============================================================================

@pytest.fixture
def retry_config() -> dict[str, Any]:
    """Default retry configuration."""
    return {
        "max_retries": 3,
        "retry_delay": 0.1,
        "exponential_backoff": True,
        "retryable_errors": ["ConnectionError", "TimeoutError", "HTTPError"],
    }


@pytest.fixture
def failure_recovery_config() -> dict[str, Any]:
    """Configuration for failure recovery testing."""
    return {
        "checkpoint_interval": 5,
        "recovery_timeout": 30,
        "state_persistence": True,
    }
