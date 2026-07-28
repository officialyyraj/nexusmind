"""Agent registry for dynamic agent registration and discovery."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from app.agents.types import AgentType


class AgentHealth(str, Enum):
    """Agent health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AgentPriority(int, Enum):
    """Agent execution priority."""

    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3
    BACKGROUND = 1


@dataclass
class AgentMetadata:
    """Metadata for a registered agent."""

    agent_type: AgentType
    name: str
    description: str
    capabilities: list[str]
    priority: AgentPriority
    health: AgentHealth
    registered_at: datetime
    last_used: datetime | None = None
    use_count: int = 0
    dependencies: list[AgentType] = field(default_factory=list)
    max_concurrent: int = 5
    current_load: int = 0


@dataclass
class AgentRegistration:
    """Registration info for an agent factory."""

    agent_type: AgentType
    factory: Callable
    metadata: AgentMetadata


class AgentRegistry:
    """Registry for managing agents with dependency injection.

    Features:
    - Registration and lookup
    - Capabilities discovery
    - Priority-based selection
    - Health tracking
    - Dependency injection
    - Concurrent execution limits
    """

    def __init__(self):
        self._agents: dict[AgentType, AgentRegistration] = {}
        self._factories: dict[AgentType, Callable] = {}
        self._metadata: dict[AgentType, AgentMetadata] = {}
        self._lock = asyncio.Lock()
        self._instances: dict[AgentType, list[Any]] = {}

    async def register(
        self,
        agent_type: AgentType,
        factory: Callable,
        name: str | None = None,
        description: str = "",
        capabilities: list[str] | None = None,
        priority: AgentPriority = AgentPriority.NORMAL,
        dependencies: list[AgentType] | None = None,
        max_concurrent: int = 5,
    ) -> None:
        """Register an agent type with the registry.

        Args:
            agent_type: Type of agent to register
            factory: Callable that creates agent instances
            name: Optional custom name
            description: Agent description
            capabilities: List of agent capabilities
            priority: Execution priority
            dependencies: Agent types this agent depends on
            max_concurrent: Maximum concurrent instances
        """
        async with self._lock:
            from app.agents.types import get_agent_capabilities

            caps = capabilities or get_agent_capabilities(agent_type).get("tools", [])
            agent_name = name or f"{agent_type.value.capitalize()}Agent"

            metadata = AgentMetadata(
                agent_type=agent_type,
                name=agent_name,
                description=description or get_agent_capabilities(agent_type).get("description", ""),
                capabilities=caps,
                priority=priority,
                health=AgentHealth.HEALTHY,
                registered_at=datetime.utcnow(),
                dependencies=dependencies or [],
                max_concurrent=max_concurrent,
            )

            registration = AgentRegistration(
                agent_type=agent_type,
                factory=factory,
                metadata=metadata,
            )

            self._agents[agent_type] = registration
            self._factories[agent_type] = factory
            self._metadata[agent_type] = metadata
            self._instances[agent_type] = []

    async def unregister(self, agent_type: AgentType) -> bool:
        """Unregister an agent type.

        Args:
            agent_type: Type of agent to unregister

        Returns:
            True if agent was unregistered
        """
        async with self._lock:
            if agent_type not in self._agents:
                return False

            del self._agents[agent_type]
            del self._factories[agent_type]
            del self._metadata[agent_type]
            self._instances.pop(agent_type, None)
            return True

    def get(self, agent_type: AgentType) -> Callable | None:
        """Get agent factory by type.

        Args:
            agent_type: Type of agent to get

        Returns:
            Agent factory or None if not found
        """
        return self._factories.get(agent_type)

    def get_metadata(self, agent_type: AgentType) -> AgentMetadata | None:
        """Get agent metadata.

        Args:
            agent_type: Type of agent

        Returns:
            Agent metadata or None
        """
        return self._metadata.get(agent_type)

    def list_agents(self) -> list[AgentMetadata]:
        """List all registered agents.

        Returns:
            List of agent metadata
        """
        return list(self._metadata.values())

    def list_by_priority(self) -> list[AgentMetadata]:
        """List agents sorted by priority (highest first).

        Returns:
            List of agent metadata sorted by priority
        """
        agents = list(self._metadata.values())
        return sorted(agents, key=lambda a: a.priority.value, reverse=True)

    def find_by_capability(self, capability: str) -> list[AgentMetadata]:
        """Find agents with a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agents with the capability
        """
        return [
            meta for meta in self._metadata.values()
            if capability in meta.capabilities
        ]

    def find_dependencies_met(
        self,
        agent_type: AgentType,
        completed: set[AgentType],
    ) -> list[AgentType]:
        """Find agents whose dependencies are satisfied.

        Args:
            agent_type: Agent type to check
            completed: Set of completed agent types

        Returns:
            List of agent types ready to execute
        """
        results = []
        for atype, meta in self._metadata.items():
            if atype not in completed:
                if all(dep in completed for dep in meta.dependencies):
                    results.append(atype)
        return results

    async def can_execute(self, agent_type: AgentType) -> bool:
        """Check if agent can accept new executions.

        Args:
            agent_type: Type of agent

        Returns:
            True if agent can execute
        """
        metadata = self._metadata.get(agent_type)
        if not metadata:
            return False
        return metadata.current_load < metadata.max_concurrent

    async def record_use(self, agent_type: AgentType) -> None:
        """Record that an agent was used.

        Args:
            agent_type: Type of agent used
        """
        async with self._lock:
            if agent_type in self._metadata:
                meta = self._metadata[agent_type]
                meta.use_count += 1
                meta.last_used = datetime.utcnow()
                meta.current_load = min(meta.current_load + 1, meta.max_concurrent)

    async def record_completion(self, agent_type: AgentType) -> None:
        """Record that an agent completed execution.

        Args:
            agent_type: Type of agent that completed
        """
        async with self._lock:
            if agent_type in self._metadata:
                meta = self._metadata[agent_type]
                meta.current_load = max(meta.current_load - 1, 0)

    async def update_health(self, agent_type: AgentType, health: AgentHealth) -> None:
        """Update agent health status.

        Args:
            agent_type: Type of agent
            health: New health status
        """
        async with self._lock:
            if agent_type in self._metadata:
                self._metadata[agent_type].health = health

    async def health_check(self) -> dict[AgentType, AgentHealth]:
        """Get health status of all agents.

        Returns:
            Map of agent type to health status
        """
        health_status = {}
        for agent_type in self._metadata:
            health_status[agent_type] = self._metadata[agent_type].health
        return health_status

    def has_agent(self, agent_type: AgentType) -> bool:
        """Check if agent is registered.

        Args:
            agent_type: Type of agent

        Returns:
            True if agent is registered
        """
        return agent_type in self._agents

    def count(self) -> int:
        """Get number of registered agents.

        Returns:
            Number of registered agents
        """
        return len(self._agents)


# Global registry instance
_agent_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry.

    Returns:
        AgentRegistry instance
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


async def register_agent(
    agent_type: AgentType,
    factory: Callable,
    **kwargs,
) -> None:
    """Register an agent with the global registry."""
    await get_agent_registry().register(agent_type, factory, **kwargs)


async def get_agent(agent_type: AgentType) -> Callable | None:
    """Get an agent factory from the global registry."""
    return get_agent_registry().get(agent_type)


async def list_agents() -> list[AgentMetadata]:
    """List all agents from the global registry."""
    return get_agent_registry().list_agents()