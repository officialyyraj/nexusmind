"""Base agent class for all agents."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, TypedDict

from app.agents.types import AgentType, get_agent_capabilities


class AgentState(TypedDict):
    """State shared between agents in a workflow."""

    session_id: str
    task: str
    context: dict[str, Any]
    messages: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    agent_states: dict[str, dict[str, Any]]
    current_agent: str | None
    result: dict[str, Any] | None
    error: str | None


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        agent_type: AgentType,
        session_id: str | None = None,
        llm_provider: str | None = None,
    ):
        self.agent_type = agent_type
        self.session_id = session_id or str(uuid.uuid4())
        self.llm_provider = llm_provider
        self.capabilities = get_agent_capabilities(agent_type)

    @property
    def name(self) -> str:
        """Get agent name."""
        return f"{self.agent_type.value.capitalize()}Agent"

    @property
    def description(self) -> str:
        """Get agent description."""
        return self.capabilities.get("description", "")

    @property
    def tools(self) -> list[str]:
        """Get agent tools."""
        return self.capabilities.get("tools", [])

    @property
    def model(self) -> str:
        """Get recommended model type."""
        return self.capabilities.get("model", "reasoning")

    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """Execute the agent's task."""
        pass

    @abstractmethod
    async def plan(self, task: str, context: dict[str, Any]) -> list[str]:
        """Plan steps for completing a task."""
        pass

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return f"""You are {self.name}, a specialized AI agent.
        
Your role: {self.description}

You have access to the following tools:
{', '.join(self.tools)}

When working on tasks:
1. Analyze the request carefully
2. Use appropriate tools to gather information
3. Execute the task systematically
4. Report results clearly

Always maintain context and be thorough in your work."""

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "model": self.model,
        }