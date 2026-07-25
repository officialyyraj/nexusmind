"""LangGraph workflow for multi-agent orchestration."""

from typing import Any, Literal

from langgraph.graph import END, StateGraph

from app.agents.base import AgentState
from app.agents.implementations import (
    CoderAgent,
    DocumentationAgent,
    ManagerAgent,
    PlannerAgent,
    ResearcherAgent,
    ReviewerAgent,
    TesterAgent,
    create_agent,
)
from app.agents.types import AgentType


def create_agent_workflow() -> StateGraph:
    """Create the main agent workflow graph."""
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

    # Define routing logic
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "coder")
    workflow.add_edge("coder", "reviewer")
    workflow.add_edge("reviewer", END)

    return workflow.compile()


async def planner_node(state: AgentState) -> AgentState:
    """Execute planner agent."""
    planner = PlannerAgent(session_id=state.get("session_id"))
    return await planner.execute(state)


async def researcher_node(state: AgentState) -> AgentState:
    """Execute researcher agent."""
    researcher = ResearcherAgent(session_id=state.get("session_id"))
    return await researcher.execute(state)


async def coder_node(state: AgentState) -> AgentState:
    """Execute coder agent."""
    coder = CoderAgent(session_id=state.get("session_id"))
    return await coder.execute(state)


async def reviewer_node(state: AgentState) -> AgentState:
    """Execute reviewer agent."""
    reviewer = ReviewerAgent(session_id=state.get("session_id"))
    return await reviewer.execute(state)


async def tester_node(state: AgentState) -> AgentState:
    """Execute tester agent."""
    tester = TesterAgent(session_id=state.get("session_id"))
    return await tester.execute(state)


async def documentation_node(state: AgentState) -> AgentState:
    """Execute documentation agent."""
    docs = DocumentationAgent(session_id=state.get("session_id"))
    return await docs.execute(state)


async def manager_node(state: AgentState) -> AgentState:
    """Execute manager agent."""
    manager = ManagerAgent(session_id=state.get("session_id"))
    return await manager.execute(state)


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
    """Workflow manager for running agent tasks."""

    def __init__(self, llm_provider: str | None = None):
        self.llm_provider = llm_provider
        self.workflow = create_agent_workflow()

    async def run(self, task: str, session_id: str, context: dict[str, Any] | None = None) -> AgentState:
        """Run the workflow for a task."""
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
