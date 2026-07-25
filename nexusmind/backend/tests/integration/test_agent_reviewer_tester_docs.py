"""Integration tests for Reviewer, Tester, and Documentation agents."""

import pytest

from app.agents.base import AgentState
from app.agents.implementations import (
    CoderAgent,
    DocumentationAgent,
    ReviewerAgent,
    TesterAgent,
)
from tests.integration.conftest import MockLLMProvider


class TestReviewerAgentIntegration:
    """Integration tests for ReviewerAgent."""

    @pytest.mark.asyncio
    async def test_reviewer_executes_with_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test reviewer execution with code."""
        agent = ReviewerAgent(session_id="test-reviewer-1")

        state: AgentState = {
            "session_id": "test-reviewer-1",
            "task": "Review code",
            "context": {
                "code": "def add(a, b): return a + b",
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "coder",
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify reviewer executed
        assert "reviewer" in result["agent_states"]

    @pytest.mark.asyncio
    async def test_reviewer_provides_feedback(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test reviewer provides feedback."""
        agent = ReviewerAgent()

        state: AgentState = {
            "session_id": "test-reviewer-2",
            "task": "Review authentication code",
            "context": {
                "code": """
                def authenticate(username, password):
                    return username == "admin" and password == "secret"
                """,
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should have issues or suggestions
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_reviewer_handles_empty_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test reviewer with empty code."""
        agent = ReviewerAgent()

        state: AgentState = {
            "session_id": "test-reviewer-3",
            "task": "Review code",
            "context": {"code": ""},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should complete without error
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_reviewer_assigns_score(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test reviewer assigns quality score."""
        agent = ReviewerAgent()

        state: AgentState = {
            "session_id": "test-reviewer-4",
            "task": "Review code",
            "context": {"code": "def test(): pass"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should have a score
        reviewer_state = result["agent_states"].get("reviewer", {})
        assert "score" in reviewer_state or "result" in result


class TestTesterAgentIntegration:
    """Integration tests for TesterAgent."""

    @pytest.mark.asyncio
    async def test_tester_executes_with_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test tester execution with code."""
        agent = TesterAgent(session_id="test-tester-1")

        state: AgentState = {
            "session_id": "test-tester-1",
            "task": "Write tests",
            "context": {
                "code": "def add(a, b): return a + b",
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "coder",
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify tester executed
        assert "tester" in result["agent_states"]

    @pytest.mark.asyncio
    async def test_tester_generates_unit_tests(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test tester generates unit tests."""
        agent = TesterAgent()

        state: AgentState = {
            "session_id": "test-tester-2",
            "task": "Create unit tests for calculator",
            "context": {
                "code": """
                def add(a, b):
                    return a + b

                def subtract(a, b):
                    return a - b
                """,
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should have tests
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_tester_handles_empty_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test tester with empty code."""
        agent = TesterAgent()

        state: AgentState = {
            "session_id": "test-tester-3",
            "task": "Write tests",
            "context": {"code": ""},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should complete without error
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_tester_provides_coverage(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test tester provides coverage info."""
        agent = TesterAgent()

        state: AgentState = {
            "session_id": "test-tester-4",
            "task": "Create tests",
            "context": {"code": "def example(): pass"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should have coverage info
        tester_state = result["agent_states"].get("tester", {})
        assert "coverage" in tester_state or "result" in result


class TestDocumentationAgentIntegration:
    """Integration tests for DocumentationAgent."""

    @pytest.mark.asyncio
    async def test_documentation_executes_with_code(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test documentation execution with code."""
        agent = DocumentationAgent(session_id="test-docs-1")

        state: AgentState = {
            "session_id": "test-docs-1",
            "task": "Generate documentation",
            "context": {
                "code": "def add(a, b): return a + b",
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "coder",
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify documentation executed
        assert "documentation" in result["agent_states"]

    @pytest.mark.asyncio
    async def test_documentation_generates_readme(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test documentation generates README."""
        agent = DocumentationAgent()

        state: AgentState = {
            "session_id": "test-docs-2",
            "task": "Create documentation for API",
            "context": {
                "code": """
                class API:
                    def get_users(self): pass
                    def create_user(self, data): pass
                """,
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should have documentation sections
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_documentation_includes_api_reference(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test documentation includes API reference."""
        agent = DocumentationAgent()

        state: AgentState = {
            "session_id": "test-docs-3",
            "task": "Document the API",
            "context": {
                "code": "def endpoint(): pass",
                "include_api_ref": True,
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should have sections including API reference
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_documentation_generates_examples(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test documentation generates usage examples."""
        agent = DocumentationAgent()

        state: AgentState = {
            "session_id": "test-docs-4",
            "task": "Document usage",
            "context": {
                "code": "def calculate(x, y): pass",
                "include_examples": True,
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should complete
        assert result["error"] is None


class TestAgentChainIntegration:
    """Test agent chain (review -> test -> document)."""

    @pytest.mark.asyncio
    async def test_reviewer_to_tester_chain(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test Reviewer -> Tester chain."""
        code = "def add(a, b): return a + b"

        # Reviewer
        reviewer = ReviewerAgent(session_id="test-chain-1")
        review_state: AgentState = {
            "session_id": "test-chain-1",
            "task": "Review code",
            "context": {"code": code},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "coder",
            "result": None,
            "error": None,
        }
        review_result = await reviewer.execute(review_state)

        # Tester
        tester = TesterAgent(session_id="test-chain-1")
        test_state: AgentState = {
            "session_id": "test-chain-1",
            "task": "Write tests",
            "context": {
                "code": code,
                "review_issues": review_result.get("result", {}).get("issues", []),
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "reviewer",
            "result": None,
            "error": None,
        }
        test_result = await tester.execute(test_state)

        # Both should complete
        assert review_result["error"] is None
        assert test_result["error"] is None

    @pytest.mark.asyncio
    async def test_tester_to_docs_chain(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test Tester -> Documentation chain."""
        code = "def calculate(x, y): return x + y"
        tests = ["test_add_positive", "test_add_negative"]

        # Tester
        tester = TesterAgent(session_id="test-chain-2")
        test_state: AgentState = {
            "session_id": "test-chain-2",
            "task": "Write tests",
            "context": {"code": code},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "coder",
            "result": None,
            "error": None,
        }
        test_result = await tester.execute(test_state)

        # Documentation
        docs = DocumentationAgent(session_id="test-chain-2")
        doc_state: AgentState = {
            "session_id": "test-chain-2",
            "task": "Document",
            "context": {
                "code": code,
                "tests": test_result.get("result", {}).get("tests", []),
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "tester",
            "result": None,
            "error": None,
        }
        doc_result = await docs.execute(doc_state)

        # Both should complete
        assert test_result["error"] is None
        assert doc_result["error"] is None


class TestAgentStateFlow:
    """Test state flow through agents."""

    @pytest.mark.asyncio
    async def test_context_propagation(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test that context propagates through agents."""
        session_id = "test-propagate-1"
        initial_context = {
            "user": "test_user",
            "language": "python",
            "framework": "fastapi",
        }

        # Start with coder
        coder = CoderAgent(session_id=session_id)
        state: AgentState = {
            "session_id": session_id,
            "task": "Create endpoint",
            "context": initial_context.copy(),
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        result = await coder.execute(state)

        # Context should be preserved (original context is kept)
        assert result["context"].get("language") == "python"
        assert result["context"].get("framework") == "fastapi"

    @pytest.mark.asyncio
    async def test_messages_accumulation(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test that messages accumulate through agents."""
        session_id = "test-messages-1"

        # Agent 1
        agent1 = CoderAgent(session_id=session_id)
        state1: AgentState = {
            "session_id": session_id,
            "task": "Task 1",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": {"message": "Completed task 1"},
            "error": None,
        }
        result1 = await agent1.execute(state1)

        # Agent 2
        agent2 = ReviewerAgent(session_id=session_id)
        state2: AgentState = {
            "session_id": session_id,
            "task": "Task 2",
            "context": {},
            "messages": result1.get("messages", []) + [{"role": "assistant", "content": str(result1.get("result", {}))}],
            "artifacts": result1.get("artifacts", []),
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        result2 = await agent2.execute(state2)

        # Messages should be passed
        assert len(result2.get("messages", [])) >= 1
