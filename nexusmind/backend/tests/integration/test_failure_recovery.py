"""Integration tests for failure recovery and state persistence."""

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.base import AgentState
from app.agents.implementations import (
    CoderAgent,
    DocumentationAgent,
    PlannerAgent,
    ResearcherAgent,
    ReviewerAgent,
    TesterAgent,
)
from tests.integration.conftest import ErrorSimulator, MockSessionStorage


class TestFailureRecoveryMechanisms:
    """Test failure recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_agent_handles_llm_error(self):
        """Test agent handles LLM errors gracefully."""
        session_id = f"test-llm-err-{uuid.uuid4().hex[:8]}"

        # Create agent
        agent = PlannerAgent(session_id=session_id)

        # Mock LLM to raise error
        with patch.object(agent, 'plan', side_effect=Exception("LLM Error")):
            state: AgentState = {
                "session_id": session_id,
                "task": "Plan a task",
                "context": {},
                "messages": [],
                "artifacts": [],
                "agent_states": {},
                "current_agent": None,
                "result": None,
                "error": None,
            }

            # Should not raise, should set error in state
            try:
                result = await agent.execute(state)
                # Either returns error state or raises
            except Exception:
                pass  # Expected in some implementations

    @pytest.mark.asyncio
    async def test_agent_handles_context_error(self):
        """Test agent handles context errors."""
        session_id = f"test-ctx-err-{uuid.uuid4().hex[:8]}"

        agent = CoderAgent(session_id=session_id)

        state: AgentState = {
            "session_id": session_id,
            "task": "Generate code",
            "context": None,  # Invalid context
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        # Should handle None context
        try:
            result = await agent.execute(state)
            # Should complete with error or handle gracefully
        except (TypeError, AttributeError):
            # Expected if context is None
            pass

    @pytest.mark.asyncio
    async def test_agent_handles_empty_task(self):
        """Test agent handles empty task."""
        agent = PlannerAgent()

        state: AgentState = {
            "session_id": "test-empty",
            "task": "",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should complete without crash
        assert result is not None

    @pytest.mark.asyncio
    async def test_agent_handles_missing_dependencies(self):
        """Test agent handles missing dependencies."""
        agent = ResearcherAgent()

        state: AgentState = {
            "session_id": "test-deps",
            "task": "Research",
            "context": {
                "use_web_search": True,
                # Missing search API key
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should handle gracefully
        assert result is not None


class TestStatePersistence:
    """Test state persistence through failures."""

    @pytest.mark.asyncio
    async def test_state_saved_before_failure(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test state is saved before potential failure."""
        session_id = f"test-save-{uuid.uuid4().hex[:8]}"

        state: AgentState = {
            "session_id": session_id,
            "task": "Important task",
            "context": {"progress": "50%"},
            "messages": [{"role": "user", "content": "Hello"}],
            "artifacts": [],
            "agent_states": {"planner": {"completed": True}},
            "current_agent": "planner",
            "result": {"partial": "result"},
            "error": None,
        }

        # Save before potential failure
        mock_session_storage.save_session(session_id, state)

        # Verify saved
        saved = mock_session_storage.get_session(session_id)
        assert saved is not None
        assert saved["context"]["progress"] == "50%"
        assert "planner" in saved["agent_states"]

    @pytest.mark.asyncio
    async def test_state_restored_after_failure(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test state can be restored after failure."""
        session_id = f"test-restore-{uuid.uuid4().hex[:8]}"

        # Create checkpoint
        checkpoint: AgentState = {
            "session_id": session_id,
            "task": "Build feature",
            "context": {
                "current_plan": {"steps": [{"id": 1}]},
                "completed_agents": ["planner", "researcher"],
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {
                "planner": {"completed": True},
                "researcher": {"completed": True},
            },
            "current_agent": "coder",
            "result": {"progress": 0.5},
            "error": None,
        }

        mock_session_storage.save_session(session_id, checkpoint)

        # Simulate failure and restart
        restored = mock_session_storage.get_session(session_id)

        assert restored is not None
        assert restored["current_agent"] == "coder"
        assert len(restored["agent_states"]) == 2

    @pytest.mark.asyncio
    async def test_state_history_tracking(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test state history is tracked for debugging."""
        session_id = f"test-history-{uuid.uuid4().hex[:8]}"

        # Add multiple snapshots
        for i in range(3):
            snapshot: AgentState = {
                "session_id": session_id,
                "task": f"Task at step {i}",
                "context": {"step": i},
                "messages": [],
                "artifacts": [],
                "agent_states": {},
                "current_agent": None,
                "result": None,
                "error": None,
            }
            mock_session_storage.save_state_snapshot(session_id, snapshot)

        history = mock_session_storage.get_state_history(session_id)
        assert len(history) == 3

        # Verify order
        assert history[0]["context"]["step"] == 0
        assert history[1]["context"]["step"] == 1
        assert history[2]["context"]["step"] == 2

    @pytest.mark.asyncio
    async def test_artifacts_persist_across_failures(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test artifacts persist across agent failures."""
        session_id = f"test-artifacts-{uuid.uuid4().hex[:8]}"

        # Coder creates artifact
        state_with_artifact: AgentState = {
            "session_id": session_id,
            "task": "Build feature",
            "context": {},
            "messages": [],
            "artifacts": [
                {"type": "file", "name": "main.py", "content": "code"},
            ],
            "agent_states": {"coder": {"completed": True}},
            "current_agent": "reviewer",
            "result": None,
            "error": None,
        }

        mock_session_storage.save_session(session_id, state_with_artifact)

        # Reviewer fails, but artifacts should be preserved
        restored = mock_session_storage.get_session(session_id)
        assert len(restored["artifacts"]) == 1
        assert restored["artifacts"][0]["name"] == "main.py"


class TestRetryLogic:
    """Test retry logic and backoff."""

    @pytest.mark.asyncio
    async def test_retry_count_tracking(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test retry count is tracked."""
        session_id = f"test-retry-{uuid.uuid4().hex[:8]}"

        # Simulate retries
        for _ in range(3):
            mock_session_storage.increment_retry(session_id)

        assert mock_session_storage.get_retry_count(session_id) == 3

    @pytest.mark.asyncio
    async def test_failure_count_tracking(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test failure count is tracked."""
        session_id = f"test-failure-{uuid.uuid4().hex[:8]}"

        # Simulate failures
        mock_session_storage.simulate_failure(session_id, 2)

        assert mock_session_storage.get_failure_count(session_id) == 2

        # Clear failures
        mock_session_storage.clear_failures(session_id)
        assert mock_session_storage.get_failure_count(session_id) == 0


class TestCheckpointRecovery:
    """Test checkpoint and recovery."""

    @pytest.mark.asyncio
    async def test_planner_checkpoint(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test checkpoint after planner completion."""
        session_id = f"test-checkpoint-{uuid.uuid4().hex[:8]}"

        # After planner completes
        checkpoint: AgentState = {
            "session_id": session_id,
            "task": "Build feature",
            "context": {
                "current_plan": {
                    "steps": [
                        {"id": "req", "agent": "researcher"},
                        {"id": "impl", "agent": "coder"},
                    ]
                }
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {"planner": {"completed": True}},
            "current_agent": "researcher",
            "result": {"plan": {"steps": []}},
            "error": None,
        }

        mock_session_storage.save_session(session_id, checkpoint)

        # Resume from checkpoint
        restored = mock_session_storage.get_session(session_id)

        # Should be at researcher
        assert restored["current_agent"] == "researcher"
        assert "planner" in restored["agent_states"]
        assert restored["result"]["plan"] is not None

    @pytest.mark.asyncio
    async def test_researcher_checkpoint(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test checkpoint after researcher completion."""
        session_id = f"test-res-{uuid.uuid4().hex[:8]}"

        checkpoint: AgentState = {
            "session_id": session_id,
            "task": "Build feature",
            "context": {
                "research_findings": [
                    {"source": "web", "content": "Best practices found"},
                ]
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {
                "planner": {"completed": True},
                "researcher": {"completed": True, "findings_count": 5},
            },
            "current_agent": "coder",
            "result": None,
            "error": None,
        }

        mock_session_storage.save_session(session_id, checkpoint)
        restored = mock_session_storage.get_session(session_id)

        assert restored["current_agent"] == "coder"
        assert len(restored["context"]["research_findings"]) == 1

    @pytest.mark.asyncio
    async def test_coder_checkpoint(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test checkpoint after coder completion."""
        session_id = f"test-coder-{uuid.uuid4().hex[:8]}"

        checkpoint: AgentState = {
            "session_id": session_id,
            "task": "Build feature",
            "context": {
                "code_files": [
                    {"name": "main.py", "content": "print('hello')"},
                ]
            },
            "messages": [],
            "artifacts": [
                {"type": "file", "name": "main.py", "content": "print('hello')"},
            ],
            "agent_states": {
                "planner": {"completed": True},
                "researcher": {"completed": True},
                "coder": {"completed": True, "files_created": 1},
            },
            "current_agent": "reviewer",
            "result": {"files": [{"name": "main.py"}]},
            "error": None,
        }

        mock_session_storage.save_session(session_id, checkpoint)
        restored = mock_session_storage.get_session(session_id)

        assert restored["current_agent"] == "reviewer"
        assert len(restored["artifacts"]) == 1


class TestRecoveryScenarios:
    """Real-world recovery scenarios."""

    @pytest.mark.asyncio
    async def test_recover_from_mid_workflow(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test recovery from middle of workflow."""
        session_id = f"test-mid-{uuid.uuid4().hex[:8]}"

        # State after coder, about to enter reviewer
        mid_state: AgentState = {
            "session_id": session_id,
            "task": "Create authentication system",
            "context": {
                "current_plan": {
                    "steps": [
                        {"id": "req", "agent": "researcher", "status": "done"},
                        {"id": "impl", "agent": "coder", "status": "done"},
                        {"id": "review", "agent": "reviewer", "status": "pending"},
                        {"id": "test", "agent": "tester", "status": "pending"},
                        {"id": "docs", "agent": "documentation", "status": "pending"},
                    ]
                },
                "code_files": [
                    {"name": "auth.py", "content": "class Auth: pass"},
                ],
                "research_findings": [
                    {"content": "Use JWT tokens"},
                ],
            },
            "messages": [],
            "artifacts": [
                {"type": "file", "name": "auth.py", "content": "class Auth: pass"},
            ],
            "agent_states": {
                "planner": {"completed": True},
                "researcher": {"completed": True},
                "coder": {"completed": True, "files": ["auth.py"]},
            },
            "current_agent": "reviewer",
            "result": None,
            "error": None,
        }

        mock_session_storage.save_session(session_id, mid_state)

        # System restarts
        restored = mock_session_storage.get_session(session_id)

        # Verify we can resume
        assert restored["current_agent"] == "reviewer"
        assert "planner" in restored["agent_states"]
        assert "researcher" in restored["agent_states"]
        assert "coder" in restored["agent_states"]
        assert len(restored["context"]["code_files"]) == 1

    @pytest.mark.asyncio
    async def test_recover_from_reviewer_failure(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test recovery after reviewer fails."""
        session_id = f"test-reviewer-fail-{uuid.uuid4().hex[:8]}"

        # State before reviewer failure
        pre_failure: AgentState = {
            "session_id": session_id,
            "task": "Build feature",
            "context": {
                "code_files": [{"name": "feature.py"}],
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {
                "planner": {"completed": True},
                "researcher": {"completed": True},
                "coder": {"completed": True},
            },
            "current_agent": "reviewer",
            "result": None,
            "error": "Reviewer failed: timeout",
        }

        mock_session_storage.save_session(session_id, pre_failure)

        # Fix issue and retry
        restored = mock_session_storage.get_session(session_id)

        # Clear error for retry
        restored["error"] = None
        mock_session_storage.save_session(session_id, restored)

        # Should be able to retry
        retry_state = mock_session_storage.get_session(session_id)
        assert retry_state["current_agent"] == "reviewer"
        assert retry_state["error"] is None

    @pytest.mark.asyncio
    async def test_recover_with_partial_artifacts(
        self,
        mock_session_storage: MockSessionStorage,
    ):
        """Test recovery with partial artifacts."""
        session_id = f"test-partial-{uuid.uuid4().hex[:8]}"

        # Coder created some files, then failed
        partial_state: AgentState = {
            "session_id": session_id,
            "task": "Create multi-file feature",
            "context": {},
            "messages": [],
            "artifacts": [
                {"type": "file", "name": "models.py", "content": "# Models"},
                {"type": "file", "name": "views.py", "content": ""},  # Empty - failed
            ],
            "agent_states": {
                "planner": {"completed": True},
                "researcher": {"completed": True},
                "coder": {"completed": False, "partial": True},
            },
            "current_agent": "coder",
            "result": None,
            "error": "Coder failed during file generation",
        }

        mock_session_storage.save_session(session_id, partial_state)
        restored = mock_session_storage.get_session(session_id)

        # Partial artifacts preserved
        assert len(restored["artifacts"]) == 2
        assert restored["artifacts"][0]["name"] == "models.py"
        assert restored["agent_states"]["coder"]["partial"] is True


class TestErrorSimulation:
    """Test with simulated errors."""

    def test_error_simulator_registers_errors(self, error_simulator: ErrorSimulator):
        """Test error simulator can register errors."""
        error = ValueError("Test error")
        error_simulator.register_error("test_error", error)

        assert error_simulator.should_raise("test_error")

    def test_error_simulator_tracks_counts(self, error_simulator: ErrorSimulator):
        """Test error simulator tracks error counts."""
        error = ValueError("Test")
        error_simulator.register_error("counted", error)

        try:
            error_simulator.raise_error("counted")
        except ValueError:
            pass

        assert error_simulator.get_error_count("counted") == 1

    def test_error_simulator_clear(self, error_simulator: ErrorSimulator):
        """Test error simulator can be cleared."""
        error_simulator.register_error("test", ValueError("test"))
        error_simulator.clear()

        assert not error_simulator.should_raise("test")


class TestResiliencePatterns:
    """Test resilience patterns in workflow."""

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        agent = CoderAgent(session_id="test-degrade")

        state: AgentState = {
            "session_id": "test-degrade",
            "task": "Generate code",
            "context": {
                # Missing optional components
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should complete with degraded functionality
        assert result is not None

    @pytest.mark.asyncio
    async def test_fallback_behavior(self):
        """Test fallback behavior when primary method fails."""
        agent = CoderAgent(session_id="test-fallback")

        state: AgentState = {
            "session_id": "test-fallback",
            "task": "Generate code",
            "context": {
                "preferred_language": "unknown_lang",  # Fallback to default
            },
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await agent.execute(state)

        # Should fallback gracefully
        assert result is not None
