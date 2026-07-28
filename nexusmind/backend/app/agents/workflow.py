"""LangGraph workflow for multi-agent orchestration with JSON task plans."""

import json
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.base import AgentState
from app.agents.autonomous import (
    ToolUsingCoderAgent,
    ToolUsingDocumentationAgent,
    ToolUsingManagerAgent,
    ToolUsingPlannerAgent,
    ToolUsingResearcherAgent,
    ToolUsingReviewerAgent,
    ToolUsingTesterAgent,
    create_autonomous_agent,
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
    """Execute planner agent - decomposes task into structured JSON plan using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    planner = ToolUsingPlannerAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )
    
    trace = await planner.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )

    # Extract the JSON plan for the next agents
    plan_data = trace.final_result.get("plan", {}) if trace.final_result else {}
    state["context"]["current_plan"] = plan_data
    state["context"]["plan_json"] = json.dumps(plan_data, indent=2)
    state["current_agent"] = "planner"
    state["agent_states"]["planner"] = {"trace": trace.to_dict()}

    return state


async def researcher_node(state: AgentState) -> AgentState:
    """Execute researcher agent - gathers information based on plan using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    from app.tools.web_search.service import get_search_service
    
    researcher = ToolUsingResearcherAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )
    researcher._search_service = get_search_service()

    # Get the current step from plan if available
    plan_data = state.get("context", {}).get("current_plan", {})
    if plan_data:
        steps = plan_data.get("steps", [])
        research_steps = [s for s in steps if s.get("agent_type") == "researcher"]
        if research_steps:
            state["context"]["current_step"] = research_steps[0]

    trace = await researcher.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )

    state["current_agent"] = "researcher"
    
    # Extract findings from trace
    findings = []
    if trace.final_result and isinstance(trace.final_result, dict):
        findings = trace.final_result.get("findings", [])
    
    state["agent_states"]["researcher"] = {"trace": trace.to_dict(), "findings": findings}
    state["context"]["research_findings"] = findings

    return state


async def coder_node(state: AgentState) -> AgentState:
    """Execute coder agent - implements based on plan and research using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    coder = ToolUsingCoderAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )

    # Get the current step from plan if available
    plan_data = state.get("context", {}).get("current_plan", {})
    if plan_data:
        steps = plan_data.get("steps", [])
        coding_steps = [s for s in steps if s.get("agent_type") == "coder"]
        if coding_steps:
            state["context"]["current_step"] = coding_steps[0]

    # Add research findings to context
    research_findings = state.get("context", {}).get("research_findings", [])
    if research_findings:
        state["context"]["research_context"] = research_findings

    trace = await coder.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )

    state["current_agent"] = "coder"
    state["agent_states"]["coder"] = {"trace": trace.to_dict()}

    return state


async def reviewer_node(state: AgentState) -> AgentState:
    """Execute reviewer agent using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    reviewer = ToolUsingReviewerAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )
    
    trace = await reviewer.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )
    
    state["current_agent"] = "reviewer"
    state["agent_states"]["reviewer"] = {"trace": trace.to_dict()}
    return state


async def tester_node(state: AgentState) -> AgentState:
    """Execute tester agent using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    tester = ToolUsingTesterAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )
    
    trace = await tester.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )
    
    state["current_agent"] = "tester"
    state["agent_states"]["tester"] = {"trace": trace.to_dict()}
    return state


async def documentation_node(state: AgentState) -> AgentState:
    """Execute documentation agent using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    docs = ToolUsingDocumentationAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )
    
    trace = await docs.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )
    
    state["current_agent"] = "documentation"
    state["agent_states"]["documentation"] = {"trace": trace.to_dict()}
    return state


async def manager_node(state: AgentState) -> AgentState:
    """Execute manager agent using autonomous agent."""
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    manager = ToolUsingManagerAgent(
        tool_invoker=get_tool_invoker(),
        reasoning_loop=get_reasoning_loop(),
        memory_service=get_memory_service(),
    )
    
    trace = await manager.execute_with_tools(
        task=state.get("task", ""),
        session_id=state.get("session_id", ""),
        context=state.get("context", {}),
    )
    
    state["current_agent"] = "manager"
    state["agent_states"]["manager"] = {"trace": trace.to_dict()}
    return state


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
    from app.agents.execution_engine import get_tool_invoker
    from app.agents.reasoning_loop import get_reasoning_loop
    from app.memory.chromadb import get_memory_service
    
    async def node(state: AgentState) -> AgentState:
        agent = create_autonomous_agent(
            agent_type,
            tool_invoker=get_tool_invoker(),
            reasoning_loop=get_reasoning_loop(),
            memory_service=get_memory_service(),
            session_id=state.get("session_id"),
        )
        
        trace = await agent.execute_with_tools(
            task=state.get("task", ""),
            session_id=state.get("session_id", ""),
            context=state.get("context", {}),
        )
        
        state["agent_states"][agent_type.value] = {"trace": trace.to_dict()}
        return state

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
        from app.agents.execution_engine import get_tool_invoker
        from app.agents.reasoning_loop import get_reasoning_loop
        from app.memory.chromadb import get_memory_service
        import asyncio
        
        planner = ToolUsingPlannerAgent(
            tool_invoker=get_tool_invoker(),
            reasoning_loop=get_reasoning_loop(),
            memory_service=get_memory_service(),
        )
        
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
        
        async def get_plan():
            trace = await planner.execute_with_tools(
                task=task,
                session_id="preview",
                context=context or {},
            )
            return trace.final_result.get("plan_json", "{}") if trace.final_result else "{}"
        
        return asyncio.run(get_plan())
