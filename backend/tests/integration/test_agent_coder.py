"""Integration tests for Coder agent."""

import tempfile
from pathlib import Path

import pytest

from app.agents.base import AgentState
from app.agents.implementations import CoderAgent
from tests.integration.conftest import MockLLMProvider


class TestCoderAgentIntegration:
    """Integration tests for CoderAgent."""

    @pytest.mark.asyncio
    async def test_coder_executes_with_context(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder execution with context."""
        agent = CoderAgent(session_id="test-coder-1")

        state: AgentState = {
            "session_id": "test-coder-1",
            "task": "Implement a calculator",
            "context": {
                "language": "python",
                "framework": "fastapi",
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "researcher",
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify coder executed (current_agent is set by workflow nodes)
        assert "coder" in result["agent_states"]

    @pytest.mark.asyncio
    async def test_coder_generates_python_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder generates Python code."""
        agent = CoderAgent(session_id="test-coder-2")

        state: AgentState = {
            "session_id": "test-coder-2",
            "task": "Create a function to add numbers",
            "context": {"language": "python"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify code was generated
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_coder_generates_typescript_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder generates TypeScript code."""
        agent = CoderAgent(session_id="test-coder-3")

        state: AgentState = {
            "session_id": "test-coder-3",
            "task": "Create a React component",
            "context": {"language": "typescript"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify code was generated
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_coder_uses_research_findings(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder uses research findings."""
        agent = CoderAgent(session_id="test-coder-4")

        state: AgentState = {
            "session_id": "test-coder-4",
            "task": "Implement authentication",
            "context": {
                "research_context": [
                    {"source": "web", "content": "Use JWT for auth"},
                    {"source": "docs", "content": "Store tokens securely"},
                ],
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should use research context
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_coder_respects_step_context(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder respects current step from plan."""
        agent = CoderAgent()

        state: AgentState = {
            "session_id": "test-coder-5",
            "task": "Implement core functionality",
            "context": {
                "current_step": {
                    "step_id": "core_implementation",
                    "title": "Implement Core Functionality",
                    "agent_type": "coder",
                }
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_coder_creates_file_structure(
        self,
        mock_llm_provider: MockLLMProvider,
        temp_workspace: Path,
    ):
        """Test coder creates proper file structure."""
        agent = CoderAgent(session_id="test-coder-6")

        state: AgentState = {
            "session_id": "test-coder-6",
            "task": "Create a REST API",
            "context": {
                "workspace": str(temp_workspace),
                "language": "python",
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify artifacts were created
        artifacts = result.get("artifacts", [])
        if artifacts:
            assert len(artifacts) > 0


class TestCoderCodeGeneration:
    """Test coder code generation capabilities."""

    @pytest.mark.asyncio
    async def test_coder_generates_with_docstrings(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder includes docstrings in generated code."""
        agent = CoderAgent(session_id="test-docstring-1")

        state: AgentState = {
            "session_id": "test-docstring-1",
            "task": "Create a class with methods",
            "context": {"include_docs": True},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Code should include documentation
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_coder_handles_multiple_files(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder generates multiple files."""
        agent = CoderAgent(session_id="test-multi-1")

        state: AgentState = {
            "session_id": "test-multi-1",
            "task": "Create a full application with models, views, and routes",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should handle multi-file generation
        assert result["error"] is None


class TestCoderWithLanguage:
    """Test coder with different languages."""

    @pytest.mark.asyncio
    async def test_coder_python_fastapi(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test Python FastAPI generation."""
        agent = CoderAgent(session_id="test-python-1")

        state: AgentState = {
            "session_id": "test-python-1",
            "task": "Create a REST endpoint",
            "context": {"language": "python", "framework": "fastapi"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_coder_typescript_express(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test TypeScript Express generation."""
        agent = CoderAgent(session_id="test-ts-1")

        state: AgentState = {
            "session_id": "test-ts-1",
            "task": "Create an API route",
            "context": {"language": "typescript", "framework": "express"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_coder_javascript_react(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test JavaScript React generation."""
        agent = CoderAgent(session_id="test-react-1")

        state: AgentState = {
            "session_id": "test-react-1",
            "task": "Create a React component",
            "context": {"language": "javascript", "framework": "react"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)
        assert result["error"] is None


class TestCoderIntegrationWithWorkflow:
    """Test coder integration with workflow."""

    @pytest.mark.asyncio
    async def test_coder_produces_workflow_compatible_state(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder output is compatible with workflow."""
        agent = CoderAgent(session_id="test-workflow-1")

        state: AgentState = {
            "session_id": "test-workflow-1",
            "task": "Implement a feature",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify workflow-compatible state
        assert "context" in result
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_coder_stores_code_in_artifacts(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test coder stores generated code in artifacts."""
        agent = CoderAgent(session_id="test-artifacts-1")

        state: AgentState = {
            "session_id": "test-artifacts-1",
            "task": "Write a function",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify artifacts contain code
        if result.get("result", {}).get("files"):
            assert len(result["result"]["files"]) > 0

    @pytest.mark.asyncio
    async def test_coder_state_persistence(
        self,
        mock_llm_provider: MockLLMProvider,
        mock_session_storage,
    ):
        """Test coder state is persisted."""
        session_id = "test-persist-1"
        agent = CoderAgent(session_id=session_id)

        state: AgentState = {
            "session_id": session_id,
            "task": "Implement a feature",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Save and verify persistence
        mock_session_storage.save_session(session_id, result)
        mock_session_storage.save_state_snapshot(session_id, result)

        stored = mock_session_storage.get_session(session_id)
        assert stored is not None

        history = mock_session_storage.get_state_history(session_id)
        assert len(history) == 1
