"""Tool registry for agent tools."""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ToolHealth(str, Enum):
    """Tool health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""

    name: str
    description: str
    id: str
    health: ToolHealth = ToolHealth.HEALTHY
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime | None = None
    use_count: int = 0
    capabilities: list[str] = field(default_factory=list)


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._health = ToolHealth.HEALTHY
        self._use_count = 0

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool."""
        pass

    async def health(self) -> ToolHealth:
        """Get tool health status.

        Returns:
            ToolHealth status
        """
        return self._health

    async def can_execute(self, **kwargs) -> bool:
        """Check if tool can execute with given parameters.

        Args:
            **kwargs: Execution parameters

        Returns:
            True if tool can execute
        """
        return True

    async def shutdown(self) -> None:
        """Shutdown the tool and release resources."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "id": getattr(self, 'id', self.name),
            "health": self._health.value,
        }


class ToolRegistry:
    """Registry for managing tools with MCP integration."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._tool_functions: dict[str, Callable] = {}
        self._mcp_tools: dict[str, dict[str, Any]] = {}  # name -> MCP tool info
        self._lock = asyncio.Lock()

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if tool was unregistered
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def register_function(self, name: str, func: Callable, description: str = "") -> None:
        """Register a function as a tool."""
        self._tool_functions[name] = func
        if description:
            self._tool_functions[f"{name}_description"] = description

    def register_mcp_tool(self, name: str, server_name: str, description: str,
                           input_schema: dict[str, Any] | None = None,
                           permissions: list[str] | None = None) -> None:
        """Register an MCP tool for discovery.

        Args:
            name: Tool name
            server_name: MCP server providing the tool
            description: Tool description
            input_schema: Optional input schema
            permissions: Required permissions
        """
        self._mcp_tools[name] = {
            "name": name,
            "server_name": server_name,
            "description": description,
            "input_schema": input_schema or {},
            "permissions": permissions or [],
            "type": "mcp",
        }

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_function(self, name: str) -> Callable | None:
        """Get a tool function by name."""
        return self._tool_functions.get(name)

    def get_mcp_tool(self, name: str) -> dict[str, Any] | None:
        """Get an MCP tool by name."""
        return self._mcp_tools.get(name)

    async def health_check(self, name: str) -> ToolHealth:
        """Check health of a specific tool.

        Args:
            name: Tool name

        Returns:
            ToolHealth status
        """
        tool = self._tools.get(name)
        if tool:
            return await tool.health()
        return ToolHealth.UNKNOWN

    async def health_check_all(self) -> dict[str, ToolHealth]:
        """Check health of all tools.

        Returns:
            Map of tool name to health status
        """
        results = {}
        for name in self._tools:
            results[name] = await self.health_check(name)
        return results

    async def can_execute(self, name: str, **kwargs) -> bool:
        """Check if tool can execute with given parameters.

        Args:
            name: Tool name
            **kwargs: Execution parameters

        Returns:
            True if tool can execute
        """
        tool = self._tools.get(name)
        if tool:
            return await tool.can_execute(**kwargs)
        return False

    async def execute(self, name: str, **kwargs) -> dict[str, Any]:
        """Execute a tool by name through registry dispatch.

        Args:
            name: Tool name
            **kwargs: Execution parameters

        Returns:
            Tool execution result
        """
        tool = self._tools.get(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {name}",
            }

        try:
            result = await tool.execute(**kwargs)
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def shutdown(self, name: str | None = None) -> dict[str, str]:
        """Shutdown tools and release resources.

        Args:
            name: Optional tool name. If None, shutdown all tools.

        Returns:
            Map of tool name to shutdown status
        """
        results = {}

        if name:
            tool = self._tools.get(name)
            if tool:
                try:
                    await tool.shutdown()
                    results[name] = "success"
                except Exception as e:
                    results[name] = f"error: {str(e)}"
            else:
                results[name] = "not_found"
        else:
            for tool_name, tool in self._tools.items():
                try:
                    await tool.shutdown()
                    results[tool_name] = "success"
                except Exception as e:
                    results[tool_name] = f"error: {str(e)}"

        return results

    def has_tool(self, name: str) -> bool:
        """Check if tool is registered.

        Args:
            name: Tool name

        Returns:
            True if tool is registered
        """
        return name in self._tools

    def list_tools(self, include_mcp: bool = True) -> list[dict[str, Any]]:
        """List all registered tools.
        
        Args:
            include_mcp: Whether to include MCP tools
        """
        tools = []
        for tool in self._tools.values():
            tools.append(tool.to_dict())
        for name in self._tool_functions:
            if not name.endswith("_description"):
                tools.append({
                    "name": name,
                    "description": self._tool_functions.get(f"{name}_description", ""),
                    "type": "function",
                })
        if include_mcp:
            tools.extend(self._mcp_tools.values())
        return tools

    def list_mcp_tools(self) -> list[dict[str, Any]]:
        """List all MCP tools."""
        return list(self._mcp_tools.values())

    def list_builtin_tools(self) -> list[dict[str, Any]]:
        """List all built-in tools (non-MCP)."""
        return [
            tool.to_dict()
            for tool in self._tools.values()
        ] + [
            {"name": name, "description": self._tool_functions.get(f"{name}_description", ""), "type": "function"}
            for name in self._tool_functions
            if not name.endswith("_description")
        ]


# Global tool registry
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool: BaseTool) -> None:
    """Register a tool with the global registry."""
    get_tool_registry().register(tool)


def register_tool_function(name: str, func: Callable, description: str = "") -> None:
    """Register a tool function with the global registry."""
    get_tool_registry().register_function(name, func, description)


def register_mcp_tool(name: str, server_name: str, description: str,
                       input_schema: dict[str, Any] | None = None,
                       permissions: list[str] | None = None) -> None:
    """Register an MCP tool for discovery."""
    get_tool_registry().register_mcp_tool(name, server_name, description, input_schema, permissions)


def get_tool(name: str) -> BaseTool | None:
    """Get a tool from the global registry."""
    return get_tool_registry().get(name)


def get_mcp_tool(name: str) -> dict[str, Any] | None:
    """Get an MCP tool by name."""
    return get_tool_registry().get_mcp_tool(name)


def list_all_tools(include_mcp: bool = True) -> list[dict[str, Any]]:
    """List all tools in the global registry."""
    return get_tool_registry().list_tools(include_mcp)


def list_mcp_tools() -> list[dict[str, Any]]:
    """List all MCP tools."""
    return get_tool_registry().list_mcp_tools()


def list_builtin_tools() -> list[dict[str, Any]]:
    """List all built-in tools."""
    return get_tool_registry().list_builtin_tools()
