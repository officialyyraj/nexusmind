"""Shared test fixtures for autonomous agent testing.

This module provides deterministic, mock-based testing infrastructure for
autonomous agents. All tests using this infrastructure should be:
- Deterministic (no random failures)
- Fast (no network, filesystem, or real services)
- Self-contained (no external dependencies)

Usage:
    from tests.integration.autonomous_fixtures import (
        fake_llm,
        fake_memory,
        fake_tool_invoker,
        fake_reasoning_loop,
    )
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.base import AgentState
from app.agents.execution_engine import (
    AgentToolInvoker,
    ToolCall,
    ToolCallStatus,
    ToolExecutionContext,
    ToolResult,
    ToolType,
)
from app.agents.reasoning_loop import (
    ReasoningLoop,
    ReasoningTrace,
    ToolSelector,
)


# =============================================================================
# Fake LLM
# =============================================================================

class FakeLLMResponse:
    """Deterministic LLM response for testing."""

    def __init__(
        self,
        content: str | dict,
        model: str = "fake-model",
        finish_reason: str = "stop",
    ):
        self.content = json.dumps(content) if isinstance(content, dict) else content
        self.model = model
        self.finish_reason = finish_reason
        self.usage = {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60}

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for compatibility."""
        return getattr(self, key, default)


class FakeLLM:
    """Deterministic fake LLM for testing autonomous agents.
    
    This mock provides predictable responses based on the last message content.
    It can be configured with specific responses for specific tasks.
    """

    def __init__(self, responses: dict[str, Any] | None = None):
        """Initialize with optional response mappings.
        
        Args:
            responses: Dict mapping patterns (in last message) to responses.
                      If None, uses default pattern matching.
        """
        self._responses = responses or {}
        self._call_history: list[dict[str, Any]] = []
        self.model = "fake-model"
        
        # Default structured responses for common patterns
        self._default_responses = {
            "plan": self._plan_response,
            "research": self._research_response,
            "code": self._code_response,
            "implement": self._code_response,
            "build": self._code_response,
            "create": self._code_response,
            "default": self._default_response,
        }

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> FakeLLMResponse:
        """Return a deterministic response based on message content."""
        self._call_history.append({
            "messages": messages,
            "kwargs": kwargs,
        })

        last_message = messages[-1]["content"] if messages else ""
        
        # Check explicit responses first
        for pattern, response in self._responses.items():
            if pattern.lower() in last_message.lower():
                return FakeLLMResponse(response)
        
        # Check default patterns
        for pattern, generator in self._default_responses.items():
            if pattern.lower() in last_message.lower():
                return generator(last_message)
        
        return self._default_response(last_message)

    def _plan_response(self, message: str) -> FakeLLMResponse:
        """Generate a deterministic plan response."""
        return FakeLLMResponse({
            "steps": [
                {
                    "step_id": "step_1",
                    "title": "Analyze requirements",
                    "description": f"Analyze requirements for: {message[:50]}",
                    "agent_type": "researcher",
                    "dependencies": [],
                    "priority": 10,
                    "estimated_duration": "5-10 min",
                },
                {
                    "step_id": "step_2",
                    "title": "Implement solution",
                    "description": "Implement the solution",
                    "agent_type": "coder",
                    "dependencies": ["step_1"],
                    "priority": 8,
                    "estimated_duration": "30-60 min",
                },
                {
                    "step_id": "step_3",
                    "title": "Write tests",
                    "description": "Write and run tests",
                    "agent_type": "tester",
                    "dependencies": ["step_2"],
                    "priority": 6,
                    "estimated_duration": "15-20 min",
                },
            ],
            "metadata": {
                "task_type": "implementation",
                "total_steps": 3,
            },
        })

    def _research_response(self, message: str) -> FakeLLMResponse:
        """Generate a deterministic research response."""
        return FakeLLMResponse({
            "findings": [
                {"source": "web", "content": f"Research finding for: {message[:30]}"},
                {"source": "docs", "content": "Documentation reference found"},
            ],
            "summary": "Research complete",
        })

    def _code_response(self, message: str) -> FakeLLMResponse:
        """Generate a deterministic code response."""
        return FakeLLMResponse({
            "files": [
                {
                    "name": "solution.py",
                    "path": "/workspace/solution.py",
                    "content": f"# Solution for: {message[:30]}\ndef solve(): pass",
                    "language": "python",
                }
            ],
            "status": "success",
        })

    def _default_response(self, message: str) -> FakeLLMResponse:
        """Generate a default response."""
        return FakeLLMResponse({
            "status": "success",
            "message": "Task completed",
        })

    async def stream(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> AsyncMock:
        """Return a streaming generator."""
        response = await self.chat(messages, **kwargs)
        async def generator():
            for char in response.content:
                yield char
        return generator()

    def get_call_history(self) -> list[dict[str, Any]]:
        """Get the history of all calls."""
        return self._call_history.copy()

    def reset_history(self) -> None:
        """Clear the call history."""
        self._call_history.clear()


# =============================================================================
# Fake Memory
# =============================================================================

class FakeMemory:
    """In-memory implementation of memory service for testing.
    
    This provides a deterministic, fast memory service without external dependencies.
    """

    def __init__(self):
        self._memories: dict[str, list[dict[str, Any]]] = {}

    async def store(
        self,
        session_id: str,
        memory_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a memory."""
        memory_id = f"mem_{len(self._memories.get(session_id, []))}"
        memory = {
            "id": memory_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        
        if session_id not in self._memories:
            self._memories[session_id] = []
        self._memories[session_id].append(memory)
        
        return memory_id

    async def search(
        self,
        session_id: str,
        query: str,
        memory_types: list[str] | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search memories by query."""
        memories = self._memories.get(session_id, [])
        
        # Simple substring matching for testing
        results = []
        for memory in memories:
            if memory_types and memory["memory_type"] not in memory_types:
                continue
            if query.lower() in memory["content"].lower():
                results.append(memory)
        
        return results[:top_k]

    async def get(
        self,
        session_id: str,
        memory_id: str,
    ) -> dict[str, Any] | None:
        """Get a specific memory by ID."""
        memories = self._memories.get(session_id, [])
        for memory in memories:
            if memory["id"] == memory_id:
                return memory
        return None

    async def delete(
        self,
        session_id: str,
        memory_id: str,
    ) -> bool:
        """Delete a memory."""
        memories = self._memories.get(session_id, [])
        for i, memory in enumerate(memories):
            if memory["id"] == memory_id:
                memories.pop(i)
                return True
        return False

    async def clear(self, session_id: str) -> None:
        """Clear all memories for a session."""
        self._memories.pop(session_id, None)

    def get_all(self, session_id: str) -> list[dict[str, Any]]:
        """Get all memories for a session."""
        return self._memories.get(session_id, []).copy()

    def reset(self) -> None:
        """Reset all memories."""
        self._memories.clear()


# =============================================================================
# Fake Tool Invoker
# =============================================================================

class FakeToolInvoker:
    """Deterministic tool invoker for testing.
    
    This provides predictable tool execution without external dependencies.
    """

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}
        self._call_history: list[dict[str, Any]] = []
        
        # Register built-in fake tools
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """Register built-in fake tools."""
        self.register("file_write", {
            "description": "Write to a file",
            "parameters": {"file_path": "string", "content": "string"},
            "execute": self._fake_file_write,
        })
        self.register("file_read", {
            "description": "Read from a file",
            "parameters": {"file_path": "string"},
            "execute": self._fake_file_read,
        })
        self.register("web_search", {
            "description": "Search the web",
            "parameters": {"query": "string"},
            "execute": self._fake_web_search,
        })
        self.register("memory_store", {
            "description": "Store in memory",
            "parameters": {"content": "string", "memory_type": "string"},
            "execute": self._fake_memory_store,
        })
        self.register("memory_search", {
            "description": "Search memory",
            "parameters": {"query": "string"},
            "execute": self._fake_memory_search,
        })

    def register(
        self,
        tool_name: str,
        tool_config: dict[str, Any],
    ) -> None:
        """Register a tool."""
        self._tools[tool_name] = tool_config

    async def invoke(
        self,
        tool_call: ToolCall,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Invoke a tool and return deterministic result."""
        self._call_history.append({
            "tool_name": tool_call.tool_name,
            "arguments": tool_call.arguments,
            "timestamp": datetime.utcnow().isoformat(),
        })

        tool_name = tool_call.tool_name
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                status=ToolCallStatus.FAILED,
                result=None,
                error=f"Tool '{tool_name}' not found",
                execution_time=0.0,
            )

        tool = self._tools[tool_name]
        
        try:
            result = await tool["execute"](**tool_call.arguments)
            return ToolResult(
                tool_name=tool_name,
                status=ToolCallStatus.SUCCESS,
                result=result,
                error=None,
                execution_time=0.1,
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                status=ToolCallStatus.FAILED,
                result=None,
                error=str(e),
                execution_time=0.1,
            )

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools."""
        return [
            {"name": name, "description": tool["description"]}
            for name, tool in self._tools.items()
        ]

    def list_available_tools(self) -> list[dict[str, Any]]:
        """List all available tools (alias for list_tools)."""
        return self.list_tools()

    async def _fake_file_write(self, file_path: str, content: str) -> dict:
        """Fake file write."""
        return {"path": file_path, "status": "written", "bytes": len(content)}

    async def _fake_file_read(self, file_path: str) -> dict:
        """Fake file read."""
        return {"path": file_path, "content": f"# Content of {file_path}", "bytes": 100}

    async def _fake_web_search(self, query: str) -> dict:
        """Fake web search."""
        return {
            "results": [
                {"title": f"Result for {query}", "url": "https://example.com", "snippet": "..."}
            ],
            "query": query,
        }

    async def _fake_memory_store(self, content: str, memory_type: str) -> dict:
        """Fake memory store."""
        return {"status": "stored", "memory_type": memory_type, "content_length": len(content)}

    async def _fake_memory_search(self, query: str) -> dict:
        """Fake memory search."""
        return {"results": [], "query": query, "count": 0}

    def get_call_history(self) -> list[dict[str, Any]]:
        """Get the history of tool calls."""
        return self._call_history.copy()

    def reset_history(self) -> None:
        """Clear the call history."""
        self._call_history.clear()


# =============================================================================
# Fake Reasoning Loop
# =============================================================================

class FakeReasoningLoop:
    """Deterministic reasoning loop for testing.
    
    This provides a predictable reasoning loop without external dependencies.
    """

    def __init__(
        self,
        tool_invoker: FakeToolInvoker | None = None,
        max_iterations: int = 10,
        max_tools_per_step: int = 3,
    ):
        self._tool_invoker = tool_invoker or FakeToolInvoker()
        self._max_iterations = max_iterations
        self._max_tools_per_step = max_tools_per_step
        self._execution_traces: list[ReasoningTrace] = []

    async def execute(
        self,
        task: str,
        session_id: str,
        context: dict[str, Any] | None = None,
        agent_type: str = "agent",
    ) -> ReasoningTrace:
        """Execute a task and return a deterministic trace."""
        context = context or {}
        trace = ReasoningTrace(
            trace_id=str(uuid.uuid4()),
            task=task,
            session_id=session_id,
            agent_type=agent_type,
            started_at=datetime.utcnow(),
            completed_at=None,
            steps=[],
            error=None,
            final_result=None,
        )

        # Generate deterministic tool calls based on task
        if "plan" in task.lower():
            result = {
                "plan": {
                    "steps": [
                        {"step_id": "p1", "title": "Plan step 1"},
                        {"step_id": "p2", "title": "Plan step 2"},
                    ]
                }
            }
        elif "research" in task.lower():
            result = {"findings": [{"content": "Research finding"}]}
        elif "code" in task.lower() or "implement" in task.lower():
            result = {"code": "# Generated code", "files": []}
        else:
            result = {"status": "success"}

        trace.final_result = result
        trace.completed_at = datetime.utcnow()
        self._execution_traces.append(trace)
        
        return trace

    def get_last_trace(self) -> ReasoningTrace | None:
        """Get the last execution trace."""
        return self._execution_traces[-1] if self._execution_traces else None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fake_llm() -> FakeLLM:
    """Create a fake LLM for testing.
    
    Returns:
        FakeLLM: A deterministic LLM mock.
    """
    return FakeLLM()


@pytest.fixture
def fake_memory() -> FakeMemory:
    """Create a fake memory service for testing.
    
    Returns:
        FakeMemory: An in-memory implementation of memory service.
    """
    return FakeMemory()


@pytest.fixture
def fake_tool_invoker() -> FakeToolInvoker:
    """Create a fake tool invoker for testing.
    
    Returns:
        FakeToolInvoker: A deterministic tool invoker mock.
    """
    return FakeToolInvoker()


@pytest.fixture
def fake_reasoning_loop(
    fake_tool_invoker: FakeToolInvoker,
) -> FakeReasoningLoop:
    """Create a fake reasoning loop for testing.
    
    Args:
        fake_tool_invoker: The tool invoker to use.
        
    Returns:
        FakeReasoningLoop: A deterministic reasoning loop mock.
    """
    return FakeReasoningLoop(tool_invoker=fake_tool_invoker)


@pytest.fixture
def fake_session_id() -> str:
    """Generate a deterministic session ID for testing.
    
    Returns:
        str: A test session ID.
    """
    return "test-session-12345"


@pytest.fixture
def fake_context() -> dict[str, Any]:
    """Create a test context.
    
    Returns:
        dict: A test context dictionary.
    """
    return {
        "language": "python",
        "framework": "fastapi",
        "task_type": "implementation",
    }


@pytest.fixture
def fake_execution_context(
    fake_session_id: str,
) -> ToolExecutionContext:
    """Create a fake execution context.
    
    Args:
        fake_session_id: The session ID to use.
        
    Returns:
        ToolExecutionContext: A test execution context.
    """
    return ToolExecutionContext(
        agent_type="test",
        session_id=fake_session_id,
        execution_id=str(uuid.uuid4()),
    )


# =============================================================================
# Deterministic Agent Fixtures
# =============================================================================

@pytest.fixture
def autonomous_agent_with_fakes(
    fake_llm: FakeLLM,
    fake_memory: FakeMemory,
    fake_tool_invoker: FakeToolInvoker,
    fake_reasoning_loop: FakeReasoningLoop,
):
    """Create an autonomous agent with all fakes injected.
    
    This fixture provides a fully mocked autonomous agent for testing.
    """
    from app.agents.autonomous import (
        ToolUsingPlannerAgent,
        ToolUsingResearcherAgent,
        ToolUsingCoderAgent,
    )
    
    class FullyMockedPlanner(ToolUsingPlannerAgent):
        async def get_llm(self):
            return fake_llm
    
    class FullyMockedResearcher(ToolUsingResearcherAgent):
        async def get_llm(self):
            return fake_llm
    
    class FullyMockedCoder(ToolUsingCoderAgent):
        async def get_llm(self):
            return fake_llm
    
    return {
        "planner": FullyMockedPlanner(
            tool_invoker=fake_tool_invoker,
            reasoning_loop=fake_reasoning_loop,
            memory_service=fake_memory,
        ),
        "researcher": FullyMockedResearcher(
            tool_invoker=fake_tool_invoker,
            reasoning_loop=fake_reasoning_loop,
            memory_service=fake_memory,
        ),
        "coder": FullyMockedCoder(
            tool_invoker=fake_tool_invoker,
            reasoning_loop=fake_reasoning_loop,
            memory_service=fake_memory,
        ),
        "llm": fake_llm,
        "memory": fake_memory,
        "tool_invoker": fake_tool_invoker,
        "reasoning_loop": fake_reasoning_loop,
    }


# =============================================================================
# Migration Helper
# =============================================================================

class TestMigrationHelper:
    """Helper class for migrating legacy tests to autonomous agent tests.
    
    This provides utility methods for common migration patterns.
    """

    @staticmethod
    def legacy_state_to_context(
        legacy_state: AgentState,
    ) -> dict[str, Any]:
        """Convert a legacy AgentState to autonomous agent context.
        
        Args:
            legacy_state: The legacy agent state.
            
        Returns:
            dict: The autonomous agent context.
        """
        return {
            "task": legacy_state.get("task", ""),
            "context": legacy_state.get("context", {}),
            "session_id": legacy_state.get("session_id", str(uuid.uuid4())),
        }

    @staticmethod
    def assert_plan_structure(plan: dict[str, Any]) -> None:
        """Assert that a plan has the expected structure.
        
        Args:
            plan: The plan to check.
        """
        assert isinstance(plan, dict), "Plan should be a dict"
        assert "steps" in plan, "Plan should have 'steps'"
        assert isinstance(plan["steps"], list), "Steps should be a list"
        assert "metadata" in plan, "Plan should have 'metadata'"

    @staticmethod
    def assert_trace_success(trace: ReasoningTrace) -> None:
        """Assert that a trace represents successful execution.
        
        Args:
            trace: The trace to check.
        """
        assert trace is not None, "Trace should not be None"
        assert trace.error is None or trace.final_result is not None, \
            "Either no error or partial result"

    @staticmethod
    def assert_context_preserved(
        original_context: dict[str, Any],
        result_context: dict[str, Any],
        keys: list[str],
    ) -> None:
        """Assert that context keys are preserved through execution.
        
        Args:
            original_context: The original context.
            result_context: The result context.
            keys: The keys that should be preserved.
        """
        for key in keys:
            assert key in result_context, f"Key '{key}' should be in result context"
            assert result_context[key] == original_context.get(key), \
                f"Key '{key}' should match original"


@pytest.fixture
def migration_helper() -> TestMigrationHelper:
    """Create a migration helper instance.
    
    Returns:
        TestMigrationHelper: A helper for migrating tests.
    """
    return TestMigrationHelper()
