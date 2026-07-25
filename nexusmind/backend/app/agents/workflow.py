"""LangGraph workflow for multi-agent orchestration with JSON task plans."""

import json
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.base import AgentState
from app.agents.implementations import (
    CoderAgent,
    DocumentationAgent,
    ManagerAgent,
    PlannerAgent,
    ResearcherAgent,
    ReviewerAgent,
    TaskPlan,
    TesterAgent,
    create_agent,
)
from app.agents.types import AgentType


def create_planner_researcher_coder_workflow() -> StateGraph:
    """Create workflow: Planner → Researcher → Coder with JSON task decomposition."""
    workflow = StateGraph(AgentState)

    # Add nodes for the three-agent pipeline
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Sequential flow: Planner decomposes task into JSON → Researcher gathers info → Coder implements
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "coder")
    workflow.add_edge("coder", END)

    return workflow.compile()


async def planner_node(state: AgentState) -> AgentState:
    """Execute planner agent - decomposes task into structured JSON plan."""
    planner = PlannerAgent(session_id=state.get("session_id"))
    result_state = await planner.execute(state)
    
    # Extract the JSON plan for the next agents
    plan_data = result_state.get("result", {}).get("plan", {})
    result_state["context"]["current_plan"] = plan_data
    result_state["context"]["plan_json"] = result_state.get("result", {}).get("plan_json", "{}")
    result_state["current_agent"] = "planner"
    
    return result_state


async def researcher_node(state: AgentState) -> AgentState:
    """Execute researcher agent - gathers information based on plan."""
    researcher = ResearcherAgent(session_id=state.get("session_id"))
    
    # Get the current step from plan if available
    plan_data = state.get("context", {}).get("current_plan", {})
    if plan_data:
        steps = plan_data.get("steps", [])
        # Get steps assigned to researcher
        research_steps = [s for s in steps if s.get("agent_type") == "researcher"]
        if research_steps:
            state["context"]["current_step"] = research_steps[0]
    
    result_state = await researcher.execute(state)
    result_state["current_agent"] = "researcher"
    
    # Store research findings in context for coder
    findings = result_state.get("agent_states", {}).get("researcher", {}).get("findings", [])
    result_state["context"]["research_findings"] = findings
    
    return result_state


async def coder_node(state: AgentState) -> AgentState:
    """Execute coder agent - implements based on plan and research."""
    coder = CoderAgent(session_id=state.get("session_id"))
    
    # Get the current step from plan if available
    plan_data = state.get("context", {}).get("current_plan", {})
    if plan_data:
        steps = plan_data.get("steps", [])
        # Get steps assigned to coder
        coding_steps = [s for s in steps if s.get("agent_type") == "coder"]
        if coding_steps:
            state["context"]["current_step"] = coding_steps[0]
    
    # Add research findings to context
    research_findings = state.get("context", {}).get("research_findings", [])
    if research_findings:
        state["context"]["research_context"] = research_findings
    
    result_state = await coder.execute(state)
    result_state["current_agent"] = "coder"
    
    return result_state


async def reviewer_node(state: AgentState) -> AgentState:
    """Execute reviewer agent."""
    reviewer = ReviewerAgent(session_id=state.get("session_id"))
    result_state = await reviewer.execute(state)
    result_state["current_agent"] = "reviewer"
    return result_state


async def tester_node(state: AgentState) -> AgentState:
    """Execute tester agent."""
    tester = TesterAgent(session_id=state.get("session_id"))
    result_state = await tester.execute(state)
    result_state["current_agent"] = "tester"
    return result_state


async def documentation_node(state: AgentState) -> AgentState:
    """Execute documentation agent."""
    docs = DocumentationAgent(session_id=state.get("session_id"))
    result_state = await docs.execute(state)
    result_state["current_agent"] = "documentation"
    return result_state


async def manager_node(state: AgentState) -> AgentState:
    """Execute manager agent."""
    manager = ManagerAgent(session_id=state.get("session_id"))
    result_state = await manager.execute(state)
    result_state["current_agent"] = "manager"
    return result_state


def create_full_workflow() -> StateGraph:
    """Create the full agent workflow graph with all agents."""
    workflow = StateGraph(AgentState)

    # Add nodes for each agent
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("documentation", documentation_node)
    workflow.add_node("manager", manager_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Full pipeline flow
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "coder")
    workflow.add_edge("coder", "reviewer")
    workflow.add_edge("reviewer", END)

    return workflow.compile()


def create_parallel_workflow(agent_types: list[AgentType]) -> StateGraph:
    """Create a workflow that runs agents in parallel."""
    workflow = StateGraph(AgentState)

    # Add all agent nodes
    for agent_type in agent_types:
        node_name = agent_type.value
        workflow.add_node(node_name, create_agent_node(agent_type))

    # Set entry point
    if agent_types:
        workflow.set_entry_point(agent_types[0].value)

    # Connect agents sequentially
    for i in range(len(agent_types) - 1):
        workflow.add_edge(agent_types[i].value, agent_types[i + 1].value)

    # End after last agent
    workflow.add_edge(agent_types[-1].value, END)

    return workflow.compile()


def create_agent_node(agent_type: AgentType):
    """Create a node function for an agent type."""
    async def node(state: AgentState) -> AgentState:
        agent = create_agent(agent_type, session_id=state.get("session_id"))
        return await agent.execute(state)

    return node


class AgentWorkflow:
    """Workflow manager for running agent tasks with JSON task plans."""

    def __init__(self, llm_provider: str | None = None, workflow_type: str = "planner_researcher_coder"):
        self.llm_provider = llm_provider
        self.workflow_type = workflow_type
        
        if workflow_type == "planner_researcher_coder":
            self.workflow = create_planner_researcher_coder_workflow()
        elif workflow_type == "full":
            self.workflow = create_full_workflow()
        else:
            self.workflow = create_planner_researcher_coder_workflow()

    async def run(self, task: str, session_id: str, context: dict[str, Any] | None = None) -> AgentState:
        """Run the workflow for a task with JSON task decomposition."""
        initial_state: AgentState = {
            "session_id": session_id,
            "task": task,
            "context": context or {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await self.workflow.ainvoke(initial_state)
        return result

    async def run_parallel(self, task: str, session_id: str, agent_types: list[AgentType]) -> AgentState:
        """Run agents in parallel for a task."""
        workflow = create_parallel_workflow(agent_types)

        initial_state: AgentState = {
            "session_id": session_id,
            "task": task,
            "context": {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }

        result = await workflow.ainvoke(initial_state)
        return result

    def get_plan_json(self, task: str, context: dict[str, Any] | None = None) -> str:
        """Get the JSON plan for a task without executing."""
        planner = PlannerAgent()
        import asyncio
        state: AgentState = {
            "session_id": "preview",
            "task": task,
            "context": context or {},
            "messages": [],
            "artifacts": [],
            "agent_states": {},
            "current_agent": None,
            "result": None,
            "error": None,
        }
        result = asyncio.run(planner.execute(state))
        return result.get("result", {}).get("plan_json", "{}")
