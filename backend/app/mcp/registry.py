"""MCP tool registry for dynamic tool registration."""

import asyncio
from datetime import datetime
from typing import Any, Callable

from app.mcp.schemas import (
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    MCPRegistryEntry,
)


class MCPRegistry:
    """Registry for MCP tools with dynamic registration."""

    def __init__(self):
        self._tools: dict[str, MCPTool] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._server_tools: dict[str, set[str]] = {}  # server_name -> set of tool names
        self._lock = asyncio.Lock()

    async def register_tool(
        self,
        tool: MCPTool,
        handler: Callable[..., Any],
    ) -> None:
        """Register an MCP tool.
        
        Args:
            tool: Tool definition
            handler: Async callable to handle tool invocations
        """
        async with self._lock:
            # Store tool definition
            self._tools[tool.name] = tool

            # Store handler
            self._handlers[tool.name] = handler

            # Track which server owns this tool
            if tool.server_name not in self._server_tools:
                self._server_tools[tool.server_name] = set()
            self._server_tools[tool.server_name].add(tool.name)

    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister an MCP tool.
        
        Args:
            tool_name: Name of tool to unregister
            
        Returns:
            True if tool was unregistered
        """
        async with self._lock:
            if tool_name not in self._tools:
                return False

            tool = self._tools.pop(tool_name)
            self._handlers.pop(tool_name, None)

            # Remove from server tracking
            if tool.server_name in self._server_tools:
                self._server_tools[tool.server_name].discard(tool_name)

            return True

    async def unregister_server_tools(self, server_name: str) -> list[str]:
        """Unregister all tools from a server.
        
        Args:
            server_name: Name of server
            
        Returns:
            List of tool names that were unregistered
        """
        async with self._lock:
            tool_names = list(self._server_tools.get(server_name, set()))

            for tool_name in tool_names:
                self._tools.pop(tool_name, None)
                self._handlers.pop(tool_name, None)

            self._server_tools.pop(server_name, None)

            return tool_names

    def get_tool(self, tool_name: str) -> MCPTool | None:
        """Get tool definition.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Tool definition or None
        """
        return self._tools.get(tool_name)

    def get_tools_by_server(self, server_name: str) -> list[MCPTool]:
        """Get all tools from a server.
        
        Args:
            server_name: Name of server
            
        Returns:
            List of tools from server
        """
        tool_names = self._server_tools.get(server_name, set())
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_tools(self) -> list[MCPTool]:
        """List all registered tools.
        
        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def list_tools_by_prefix(self, prefix: str) -> list[MCPTool]:
        """List tools with names starting with prefix.
        
        Args:
            prefix: Tool name prefix
            
        Returns:
            List of matching tools
        """
        return [
            tool for name, tool in self._tools.items()
            if name.startswith(prefix)
        ]

    async def invoke_tool(
        self,
        invocation: MCPToolInvocation,
    ) -> MCPToolInvocationResult:
        """Invoke an MCP tool.
        
        Args:
            invocation: Tool invocation request
            
        Returns:
            Tool invocation result
        """
        start_time = datetime.utcnow()

        tool = self._tools.get(invocation.tool_name)
        if not tool:
            return MCPToolInvocationResult(
                success=False,
                tool_name=invocation.tool_name,
                error=f"Tool not found: {invocation.tool_name}",
                execution_time=0.0,
                server_name="",
            )

        handler = self._handlers.get(invocation.tool_name)
        if not handler:
            return MCPToolInvocationResult(
                success=False,
                tool_name=invocation.tool_name,
                error=f"No handler for tool: {invocation.tool_name}",
                execution_time=0.0,
                server_name=tool.server_name,
            )

        try:
            result = await asyncio.wait_for(
                handler(**invocation.arguments),
                timeout=invocation.timeout,
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return MCPToolInvocationResult(
                success=True,
                tool_name=invocation.tool_name,
                result=result,
                execution_time=execution_time,
                server_name=tool.server_name,
            )

        except asyncio.TimeoutError:
            return MCPToolInvocationResult(
                success=False,
                tool_name=invocation.tool_name,
                error=f"Tool invocation timed out after {invocation.timeout}s",
                execution_time=invocation.timeout,
                server_name=tool.server_name,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return MCPToolInvocationResult(
                success=False,
                tool_name=invocation.tool_name,
                error=str(e),
                execution_time=execution_time,
                server_name=tool.server_name,
            )

    def has_tool(self, tool_name: str) -> bool:
        """Check if tool is registered.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            True if tool is registered
        """
        return tool_name in self._tools

    def count_tools(self) -> int:
        """Get total number of registered tools.
        
        Returns:
            Number of tools
        """
        return len(self._tools)

    def get_servers(self) -> list[str]:
        """Get list of server names with registered tools.
        
        Returns:
            List of server names
        """
        return list(self._server_tools.keys())


# Global registry instance
_mcp_registry: MCPRegistry | None = None


def get_mcp_registry() -> MCPRegistry:
    """Get the global MCP registry.
    
    Returns:
        MCPRegistry instance
    """
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry
