"""Tests for LangGraph agent workflow."""

import asyncio
import json

import pytest

from app.agents.base import AgentState
from app.agents.implementations import (
    CoderAgent,
    PlannerAgent,
    ResearcherAgent,
    TaskPlan,
    TaskStep,
)
from app.agents.types import AgentType
from app.agents.workflow import AgentWorkflow, create_planner_researcher_coder_workflow


class TestTaskPlan:
    """Test TaskPlan JSON structure."""

    def test_task_step_to_dict(self):
        """Test TaskStep serialization."""
        step = TaskStep(
            step_id="test_step",
            title="Test Step",
            description="A test step",
            agent_type="coder",
            dependencies=["prev_step"],
            estimated_duration="5 min",
            priority=5,
        )
        
        result = step.to_dict()
        
        assert result["step_id"] == "test_step"
        assert result["title"] == "Test Step"
        assert result["agent_type"] == "coder"
        assert result["dependencies"] == ["prev_step"]
        assert result["priority"] == 5

    def test_task_plan_to_json(self):
        """Test TaskPlan JSON serialization."""
        steps = [
            TaskStep(
                step_id="step1",
                title="Step 1",
                description="First step",
                agent_type="researcher",
            ),
            TaskStep(
                step_id="step2",
                title="Step 2",
                description="Second step",
                agent_type="coder",
                dependencies=["step1"],
            ),
        ]
        
        plan = TaskPlan(task="Test task", steps=steps)
        json_str = plan.to_json()
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["task"] == "Test task"
        assert len(parsed["steps"]) == 2
        assert parsed["steps"][0]["step_id"] == "step1"
        assert parsed["steps"][1]["dependencies"] == ["step1"]

    def test_get_ready_steps(self):
        """Test getting ready steps based on dependencies."""
        steps = [
            TaskStep(step_id="s1", title="S1", description="", agent_type="researcher"),
            TaskStep(step_id="s2", title="S2", description="", agent_type="coder", dependencies=["s1"]),
            TaskStep(step_id="s3", title="S3", description="", agent_type="reviewer", dependencies=["s2"]),
        ]
        
        plan = TaskPlan(task="Test", steps=steps)
        
        # No steps completed - only s1 is ready
        ready = plan.get_ready_steps(set())
        assert len(ready) == 1
        assert ready[0].step_id == "s1"
        
        # s1 completed - s2 is ready
        ready = plan.get_ready_steps({"s1"})
        assert len(ready) == 1
        assert ready[0].step_id == "s2"
        
        # s1 and s2 completed - s3 is ready
        ready = plan.get_ready_steps({"s1", "s2"})
        assert len(ready) == 1
        assert ready[0].step_id == "s3"


class TestPlannerAgent:
    """Test PlannerAgent JSON task decomposition."""

    @pytest.mark.asyncio
    async def test_plan_implementation_task(self):
        """Test planning for implementation task."""
        planner = PlannerAgent()
        state: AgentState = {
            "session_id": "test",
            "task": "Create a REST API for user management",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        
        result = await planner.execute(state)
        
        # Check result contains plan
        assert "result" in result
        plan = result["result"].get("plan", {})
        assert "steps" in plan
        assert len(plan["steps"]) > 0
        
        # Verify JSON format
        plan_json = result["result"].get("plan_json", "{}")
        parsed = json.loads(plan_json)
        assert "id" in parsed
        assert "task" in parsed
        assert "steps" in parsed

    @pytest.mark.asyncio
    async def test_plan_bug_fix_task(self):
        """Test planning for bug fix task."""
        planner = PlannerAgent()
        state: AgentState = {
            "session_id": "test",
            "task": "Fix the login bug",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        
        result = await planner.execute(state)
        plan = result["result"].get("plan", {})
        
        # Bug fix should have bug_analysis and root_cause steps
        step_ids = [s["step_id"] for s in plan["steps"]]
        assert "bug_analysis" in step_ids
        assert "root_cause" in step_ids

    def test_infer_task_type(self):
        """Test task type inference."""
        planner = PlannerAgent()
        
        assert planner._infer_task_type("Create a new feature") == "implementation"
        assert planner._infer_task_type("Build a REST API") == "implementation"
        assert planner._infer_task_type("Fix the bug") == "bug_fix"
        assert planner._infer_task_type("Research the topic") == "research"
        assert planner._infer_task_type("Review the code") == "review"


class TestResearcherAgent:
    """Test ResearcherAgent."""

    @pytest.mark.asyncio
    async def test_research(self):
        """Test research execution."""
        researcher = ResearcherAgent()
        state: AgentState = {
            "session_id": "test",
            "task": "Research authentication patterns",
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        
        result = await researcher.execute(state)
        
        assert "agent_states" in result
        assert "researcher" in result["agent_states"]
        assert "findings" in result["agent_states"]["researcher"]


class TestCoderAgent:
    """Test CoderAgent."""

    @pytest.mark.asyncio
    async def test_write_python_code(self):
        """Test Python code generation."""
        coder = CoderAgent()
        state: AgentState = {
            "session_id": "test",
            "task": "Implement user authentication",
            "context": {"language": "python"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        
        result = await coder.execute(state)
        
        assert "result" in result
        assert "code" in result["result"]
        assert "python" in result["result"]["language"]
        assert "files" in result["result"]

    @pytest.mark.asyncio
    async def test_write_typescript_code(self):
        """Test TypeScript code generation."""
        coder = CoderAgent()
        state: AgentState = {
            "session_id": "test",
            "task": "Implement user service",
            "context": {"language": "typescript"},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        
        result = await coder.execute(state)
        
        assert "typescript" in result["result"]["language"]


class TestWorkflow:
    """Test LangGraph workflow."""

    @pytest.mark.asyncio
    async def test_planner_researcher_coder_workflow(self):
        """Test the three-agent workflow."""
        workflow = AgentWorkflow(workflow_type="planner_researcher_coder")
        
        result = await workflow.run(
            task="Build a user registration API",
            session_id="test-session",
            context={"language": "python"},
        )
        
        # Verify workflow completed
        assert "agent_states" in result
        assert "planner" in result["agent_states"]
        assert "researcher" in result["agent_states"]
        assert "coder" in result["agent_states"]
        
        # Verify plan was created
        plan = result["agent_states"]["planner"].get("plan", {})
        assert "steps" in plan

    def test_get_plan_json(self):
        """Test getting plan JSON without execution."""
        workflow = AgentWorkflow()
        
        plan_json = workflow.get_plan_json("Create a web scraper")
        
        parsed = json.loads(plan_json)
        assert "steps" in parsed
        assert len(parsed["steps"]) > 0
