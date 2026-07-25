"""Tool registry for agent tools."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
        }


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._tool_functions: dict[str, Callable] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def register_function(self, name: str, func: Callable, description: str = "") -> None:
        """Register a function as a tool."""
        self._tool_functions[name] = func
        if description:
            self._tool_functions[f"{name}_description"] = description

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_function(self, name: str) -> Callable | None:
        """Get a tool function by name."""
        return self._tool_functions.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools."""
        tools = []
        for tool in self._tools.values():
            tools.append(tool.to_dict())
        for name in self._tool_functions:
            if not name.endswith("_description"):
                tools.append({
                    "name": name,
                    "description": self._tool_functions.get(f"{name}_description", ""),
                })
        return tools


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


def get_tool(name: str) -> BaseTool | None:
    """Get a tool from the global registry."""
    return get_tool_registry().get(name)


def list_all_tools() -> list[dict[str, Any]]:
    """List all tools in the global registry."""
    return get_tool_registry().list_tools()
