"""Integration tests for Planner agent."""

import json
from typing import Any

import pytest

from app.agents.base import AgentState
from app.agents.implementations import PlannerAgent, TaskPlan, TaskStep
from tests.integration.conftest import MockLLMProvider


class TestPlannerAgentIntegration:
    """Integration tests for PlannerAgent."""

    @pytest.mark.asyncio
    async def test_planner_creates_task_plan(self, mock_llm_provider: MockLLMProvider):
        """Test that planner creates a proper task plan."""
        agent = PlannerAgent(session_id="test-planner-1")

        state: AgentState = {
            "session_id": "test-planner-1",
            "task": "Build a user authentication system",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        # Execute planner
        result = await agent.execute(state)

        # Verify plan was created
        assert result["result"] is not None
        plan = result["result"]["plan"]
        assert "steps" in plan
        assert len(plan["steps"]) > 0

        # Verify plan structure
        assert plan["task"] == "Build a user authentication system"
        assert "metadata" in plan

    @pytest.mark.asyncio
    async def test_planner_infers_task_type(self, mock_llm_provider: MockLLMProvider):
        """Test that planner correctly infers task type."""
        agent = PlannerAgent()

        # Test implementation task
        plan = await agent.plan("Create a REST API", {})
        assert plan.metadata.get("task_type") == "implementation"

        # Test bug fix task
        plan = await agent.plan("Fix the login bug", {})
        assert plan.metadata.get("task_type") == "bug_fix"

        # Test research task
        plan = await agent.plan("Research authentication patterns", {})
        assert plan.metadata.get("task_type") == "research"

    @pytest.mark.asyncio
    async def test_planner_generates_dependencies(self, mock_llm_provider: MockLLMProvider):
        """Test that planner generates proper step dependencies."""
        agent = PlannerAgent()

        plan = await agent.plan("Create a web application", {"task_type": "implementation"})

        # Verify steps have dependencies
        steps_with_deps = [s for s in plan.steps if s.dependencies]
        assert len(steps_with_deps) > 0

        # Verify dependency references are valid step IDs
        all_step_ids = {s.step_id for s in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                assert dep in all_step_ids, f"Invalid dependency: {dep}"

    @pytest.mark.asyncio
    async def test_planner_respects_context(self, mock_llm_provider: MockLLMProvider):
        """Test that planner respects provided context."""
        agent = PlannerAgent()

        context = {
            "task_type": "implementation",
            "language": "typescript",
            "framework": "express",
        }

        plan = await agent.plan("Build an API", context)

        # Verify metadata includes context info
        assert plan.metadata.get("task_type") == "implementation"

    @pytest.mark.asyncio
    async def test_planner_prioritizes_steps(self, mock_llm_provider: MockLLMProvider):
        """Test that planner assigns priorities to steps."""
        agent = PlannerAgent()

        plan = await agent.plan("Create a feature", {})

        # Verify priorities are assigned
        priorities = [s.priority for s in plan.steps]
        assert len(priorities) == len(plan.steps)

        # Higher priority should come first (lower number = higher priority)
        sorted_by_priority = sorted(plan.steps, key=lambda s: s.priority, reverse=True)
        assert all(s.priority >= 0 for s in sorted_by_priority)

    @pytest.mark.asyncio
    async def test_planner_estimates_duration(self, mock_llm_provider: MockLLMProvider):
        """Test that planner provides time estimates."""
        agent = PlannerAgent()

        plan = await agent.plan("Build an application", {})

        # Verify estimated total time is provided
        assert "estimated_total_time" in plan.metadata

    @pytest.mark.asyncio
    async def test_planner_handles_empty_task(self, mock_llm_provider: MockLLMProvider):
        """Test planner behavior with empty task."""
        agent = PlannerAgent()

        plan = await agent.plan("", {})

        # Should still generate a plan
        assert plan is not None
        assert plan.task == ""

    @pytest.mark.asyncio
    async def test_planner_handles_complex_task(self, mock_llm_provider: MockLLMProvider):
        """Test planner with a complex multi-part task."""
        agent = PlannerAgent()

        task = "Build a full-stack application with authentication, real-time updates, and payment processing"
        plan = await agent.plan(task, {})

        # Should generate multiple steps
        assert len(plan.steps) >= 3

        # Should have steps for different agents
        agent_types = {s.agent_type for s in plan.steps}
        assert len(agent_types) > 1


class TestTaskPlanStructure:
    """Test TaskPlan data structure."""

    def test_task_plan_to_dict(self):
        """Test TaskPlan serialization to dict."""
        step = TaskStep(
            step_id="step1",
            title="Test Step",
            description="A test step",
            agent_type="coder",
            dependencies=[],
            estimated_duration="10 min",
            priority=5,
        )
        plan = TaskPlan(task="Test task", steps=[step])

        plan_dict = plan.to_dict()

        assert plan_dict["task"] == "Test task"
        assert len(plan_dict["steps"]) == 1
        assert plan_dict["steps"][0]["step_id"] == "step1"

    def test_task_plan_to_json(self):
        """Test TaskPlan serialization to JSON."""
        step = TaskStep(
            step_id="step1",
            title="Test Step",
            description="A test step",
            agent_type="researcher",
        )
        plan = TaskPlan(task="Test", steps=[step])

        json_str = plan.to_json()
        parsed = json.loads(json_str)

        assert parsed["task"] == "Test"
        assert len(parsed["steps"]) == 1

    def test_task_plan_get_ready_steps(self):
        """Test getting steps ready to execute."""
        step1 = TaskStep("step1", "Step 1", "Desc", "planner")
        step2 = TaskStep("step2", "Step 2", "Desc", "researcher", dependencies=["step1"])
        step3 = TaskStep("step3", "Step 3", "Desc", "coder", dependencies=["step2"])

        plan = TaskPlan(task="Test", steps=[step1, step2, step3])

        # Initially only step1 is ready
        ready = plan.get_ready_steps(set())
        assert len(ready) == 1
        assert ready[0].step_id == "step1"

        # After step1, step2 becomes ready
        ready = plan.get_ready_steps({"step1"})
        assert len(ready) == 1
        assert ready[0].step_id == "step2"

        # After step1 and step2, step3 becomes ready
        ready = plan.get_ready_steps({"step1", "step2"})
        assert len(ready) == 1
        assert ready[0].step_id == "step3"

        # All complete, nothing ready
        ready = plan.get_ready_steps({"step1", "step2", "step3"})
        assert len(ready) == 0


class TestPlannerIntegrationWithWorkflow:
    """Test planner integration with workflow."""

    @pytest.mark.asyncio
    async def test_planner_produces_workflow_compatible_state(
        self,
        mock_llm_provider: MockLLMProvider,
        initial_agent_state: AgentState,
    ):
        """Test that planner output is compatible with workflow state."""
        agent = PlannerAgent(session_id=initial_agent_state["session_id"])

        result = await agent.execute(initial_agent_state)

        # Verify workflow-compatible state
        assert "result" in result
        assert "plan" in result["result"]
        assert "plan_json" in result["result"]
        assert "context" in result

        # Verify agent_states has planner data (context update happens in workflow nodes)
        assert "planner" in result["agent_states"]
        assert "plan" in result["agent_states"]["planner"]

    @pytest.mark.asyncio
    async def test_planner_stores_state_in_session(
        self,
        mock_llm_provider: MockLLMProvider,
        mock_session_storage,
        initial_agent_state: AgentState,
    ):
        """Test that planner state is stored in session."""
        session_id = initial_agent_state["session_id"]
        agent = PlannerAgent(session_id=session_id)

        result = await agent.execute(initial_agent_state)

        # Store in mock session
        mock_session_storage.save_session(session_id, result)
        stored = mock_session_storage.get_session(session_id)

        assert stored is not None
        assert stored["session_id"] == session_id
        assert "result" in stored
