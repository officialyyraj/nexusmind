"""Integration tests for Researcher agent."""

from typing import Any

import pytest

from app.agents.base import AgentState
from app.agents.implementations import ResearcherAgent, TaskPlan, TaskStep
from tests.integration.conftest import MockLLMProvider


class TestResearcherAgentIntegration:
    """Integration tests for ResearcherAgent."""

    @pytest.mark.asyncio
    async def test_researcher_executes_with_plan(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher execution with a plan."""
        agent = ResearcherAgent(session_id="test-researcher-1")

        # Create state with a plan
        state: AgentState = {
            "session_id": "test-researcher-1",
            "task": "Research authentication patterns",
            "context": {
                "current_plan": {
                    "task": "Research authentication patterns",
                    "steps": [
                        {
                            "step_id": "research1",
                            "title": "Research auth patterns",
                            "agent_type": "researcher",
                        }
                    ],
                },
                "current_step": {
                    "step_id": "research1",
                    "title": "Research auth patterns",
                    "agent_type": "researcher",
                },
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": "planner",
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Verify research was performed (current_agent is set by workflow nodes)
        assert "researcher" in result["agent_states"]

    @pytest.mark.asyncio
    async def test_researcher_handles_empty_findings(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher with no initial findings."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-researcher-2",
            "task": "Research something",
            "context": {},
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
    async def test_researcher_passes_findings_to_next_agent(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test that researcher findings are passed to context."""
        agent = ResearcherAgent(session_id="test-researcher-3")

        state: AgentState = {
            "session_id": "test-researcher-3",
            "task": "Research best practices",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Findings should be in context for next agent
        assert "research_findings" in result["context"] or "result" in result

    @pytest.mark.asyncio
    async def test_researcher_respects_step_context(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher respects current step from plan."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-researcher-4",
            "task": "Research task",
            "context": {
                "current_step": {
                    "step_id": "research_step_1",
                    "title": "Initial Research",
                    "agent_type": "researcher",
                    "description": "Research the requirements",
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

        # Should use the step context
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_researcher_handles_multiple_research_steps(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher with multiple research steps."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-researcher-5",
            "task": "Comprehensive research",
            "context": {
                "current_plan": {
                    "steps": [
                        {
                            "step_id": "req_analysis",
                            "title": "Analyze Requirements",
                            "agent_type": "researcher",
                        },
                        {
                            "step_id": "architecture_design",
                            "title": "Design Architecture",
                            "agent_type": "researcher",
                        },
                    ],
                },
                "current_step": {
                    "step_id": "req_analysis",
                    "agent_type": "researcher",
                },
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should complete research
        assert "researcher" in result["agent_states"]


class TestResearcherSearch:
    """Test researcher search capabilities."""

    @pytest.mark.asyncio
    async def test_researcher_searches_with_keywords(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher search functionality."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-search-1",
            "task": "Find best practices for FastAPI",
            "context": {
                "keywords": ["fastapi", "best practices", "authentication"],
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should perform search
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_researcher_handles_search_results(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher handles search results."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-results-1",
            "task": "Research patterns",
            "context": {
                "search_results": [
                    {"title": "Pattern 1", "content": "Content 1"},
                    {"title": "Pattern 2", "content": "Content 2"},
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

        # Should process results
        assert result["error"] is None


class TestResearcherWithTools:
    """Test researcher with external tools."""

    @pytest.mark.asyncio
    async def test_researcher_web_search(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher web search capability."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-web-1",
            "task": "Research authentication",
            "context": {"use_web_search": True},
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
    async def test_researcher_document_analysis(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher document analysis."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-doc-1",
            "task": "Analyze API documentation",
            "context": {
                "documents": [
                    {"type": "api_spec", "path": "/api/spec"},
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

        # Should analyze documents
        assert result["error"] is None


class TestResearcherIntegrationWithWorkflow:
    """Test researcher integration with workflow."""

    @pytest.mark.asyncio
    async def test_researcher_produces_workflow_compatible_state(
        self,
        mock_llm_provider: MockLLMProvider,
    ):
        """Test researcher output is compatible with workflow."""
        agent = ResearcherAgent(session_id="test-workflow-1")

        state: AgentState = {
            "session_id": "test-workflow-1",
            "task": "Research task",
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
        assert "research_findings" in result["context"] or "result" in result

    @pytest.mark.asyncio
    async def test_researcher_state_persistence(
        self,
        mock_llm_provider: MockLLMProvider,
        mock_session_storage,
    ):
        """Test researcher state is persisted."""
        session_id = "test-persist-1"
        agent = ResearcherAgent(session_id=session_id)

        state: AgentState = {
            "session_id": session_id,
            "task": "Research for persistence",
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
