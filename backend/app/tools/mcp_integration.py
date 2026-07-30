"""MCP Tool Integration - Bridge MCP tools to the Tool Registry.

This module integrates MCP tools into the Tool Registry, making them
discoverable and executable like native tools.

Features:
- Automatic MCP tool registration
- Unified tool interface
- Permission management
- Tool discovery
"""

import asyncio
import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from app.tools.registry import (
    BaseTool,
    ToolHealth,
    ToolRegistry,
    get_tool_registry,
    register_mcp_tool as register_mcp_in_registry,
)
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.mcp.schemas import MCPTool, MCPToolInvocation


class MCPToolWrapper(BaseTool):
    """Wrapper to expose MCP tools through the Tool Registry interface.
    
    This wrapper provides a unified interface for both native tools
    and MCP tools, enabling agents to use them interchangeably.
    """
    
    def __init__(
        self,
        mcp_tool: MCPTool,
        mcp_registry: MCPRegistry,
    ):
        self._mcp_tool = mcp_tool
        self._mcp_registry = mcp_registry
        self._health = ToolHealth.HEALTHY
        self._use_count = 0
        self._last_used: datetime | None = None
    
    @property
    def name(self) -> str:
        """Get tool name."""
        return self._mcp_tool.name
    
    @property
    def description(self) -> str:
        """Get tool description."""
        return self._mcp_tool.description
    
    @property
    def id(self) -> str:
        """Get tool ID."""
        return f"mcp_{self._mcp_tool.server_name}_{self._mcp_tool.name}"
    
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the MCP tool.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        invocation = MCPToolInvocation(
            tool_name=self._mcp_tool.name,
            arguments=kwargs,
            timeout=kwargs.get("_timeout", 30.0),
        )
        
        result = await self._mcp_registry.invoke_tool(invocation)
        
        self._use_count += 1
        self._last_used = datetime.utcnow()
        
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
        }
    
    async def health(self) -> ToolHealth:
        """Check tool health."""
        # MCP tools are assumed healthy if they respond
        try:
            # Could add actual health check here
            return self._health
        except Exception:
            return ToolHealth.UNHEALTHY
    
    async def can_execute(self, **kwargs) -> bool:
        """Check if tool can execute with given parameters."""
        # Check required permissions
        required_perms = getattr(self._mcp_tool, "permissions", [])
        
        # For now, allow all executions
        return True
    
    async def shutdown(self) -> None:
        """Shutdown the tool (no-op for MCP tools)."""
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "id": self.id,
            "type": "mcp",
            "server": self._mcp_tool.server_name,
            "health": self._health.value,
            "input_schema": getattr(self._mcp_tool, "input_schema", {}),
        }
    
    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            "input_schema": getattr(self._mcp_tool, "input_schema", {}),
            "output_schema": getattr(self._mcp_tool, "output_schema", {}),
            "permissions": getattr(self._mcp_tool, "permissions", []),
        }


class MCPToolIntegrator:
    """Manages integration between MCP Registry and Tool Registry.
    
    This class ensures MCP tools are:
    - Registered with the Tool Registry
    - Kept in sync with MCP server status
    - Discoverable by agents
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        mcp_registry: MCPRegistry | None = None,
    ):
        self._tool_registry = tool_registry or get_tool_registry()
        self._mcp_registry = mcp_registry or get_mcp_registry()
        self._wrappers: dict[str, MCPToolWrapper] = {}
        self._lock = asyncio.Lock()
    
    async def register_mcp_tool(
        self,
        tool: MCPTool,
        handler: Callable[..., Any],
    ) -> None:
        """Register an MCP tool in both MCP and Tool registries.
        
        Args:
            tool: MCP tool definition
            handler: Tool handler function
        """
        # Register with MCP registry
        await self._mcp_registry.register_tool(tool, handler)
        
        # Create wrapper
        wrapper = MCPToolWrapper(tool, self._mcp_registry)
        
        async with self._lock:
            self._wrappers[tool.name] = wrapper
        
        # Register with Tool registry
        self._tool_registry.register(wrapper)
        
        # Also register with global function for discovery
        register_mcp_in_registry(
            name=tool.name,
            server_name=tool.server_name,
            description=tool.description,
            input_schema=getattr(tool, "input_schema", None),
            permissions=getattr(tool, "permissions", None),
        )
    
    async def unregister_mcp_tool(self, tool_name: str) -> bool:
        """Unregister an MCP tool from both registries.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was unregistered
        """
        # Unregister from MCP registry
        success = await self._mcp_registry.unregister_tool(tool_name)
        
        # Remove wrapper
        async with self._lock:
            if tool_name in self._wrappers:
                del self._wrappers[tool_name]
        
        # Unregister from Tool registry
        return self._tool_registry.unregister(tool_name) and success
    
    async def sync_tools(self) -> dict[str, int]:
        """Sync MCP tools with Tool Registry.
        
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "registered": 0,
            "unregistered": 0,
            "errors": 0,
        }
        
        # Get current MCP tools
        mcp_tools = self._mcp_registry.list_tools()
        
        # Get current tool registry tools
        registry_tools = {
            t["name"] for t in self._tool_registry.list_tools(include_mcp=False)
        }
        
        # Add MCP tools to registry
        for mcp_tool in mcp_tools:
            if mcp_tool.name not in registry_tools:
                try:
                    wrapper = MCPToolWrapper(mcp_tool, self._mcp_registry)
                    self._tool_registry.register(wrapper)
                    stats["registered"] += 1
                except Exception:
                    stats["errors"] += 1
        
        # Remove tools that no longer exist in MCP
        for tool_name in list(self._wrappers.keys()):
            if not self._mcp_registry.has_tool(tool_name):
                try:
                    self._tool_registry.unregister(tool_name)
                    async with self._lock:
                        del self._wrappers[tool_name]
                    stats["unregistered"] += 1
                except Exception:
                    stats["errors"] += 1
        
        return stats
    
    def get_mcp_tool(self, tool_name: str) -> MCPTool | None:
        """Get MCP tool definition.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            MCPTool or None if not found
        """
        return self._mcp_registry.get_tool(tool_name)
    
    def list_mcp_tools(self) -> list[dict[str, Any]]:
        """List all MCP tools with their status.
        
        Returns:
            List of MCP tools with metadata
        """
        tools = []
        
        for mcp_tool in self._mcp_registry.list_tools():
            wrapper = self._wrappers.get(mcp_tool.name)
            tools.append({
                "name": mcp_tool.name,
                "description": mcp_tool.description,
                "server_name": mcp_tool.server_name,
                "registered": wrapper is not None,
                "input_schema": getattr(mcp_tool, "input_schema", {}),
                "permissions": getattr(mcp_tool, "permissions", []),
            })
        
        return tools
    
    def get_unified_tool_list(self) -> list[dict[str, Any]]:
        """Get combined list of all tools (native + MCP).
        
        Returns:
            List of all available tools
        """
        tools = []
        
        # Add native tools
        for tool_dict in self._tool_registry.list_builtin_tools():
            tools.append({
                **tool_dict,
                "source": "native" if tool_dict.get("type") != "function" else "function",
            })
        
        # Add MCP tools
        for mcp_tool in self.list_mcp_tools():
            tools.append({
                "name": mcp_tool["name"],
                "description": mcp_tool["description"],
                "type": "mcp",
                "source": "mcp",
                "server": mcp_tool["server_name"],
            })
        
        return tools
    
    def get_tools_by_capability(self, capability: str) -> list[dict[str, Any]]:
        """Find tools that provide a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of tools with the capability
        """
        tools = []
        
        for tool in self.get_unified_tool_list():
            # Check description for capability
            desc = tool.get("description", "").lower()
            if capability.lower() in desc:
                tools.append(tool)
            
            # Check input schema for capability
            schema = tool.get("input_schema", {})
            if capability.lower() in str(schema).lower():
                if tool not in tools:
                    tools.append(tool)
        
        return tools


# Global integrator instance
_mcp_integrator: MCPToolIntegrator | None = None


def get_mcp_integrator() -> MCPToolIntegrator:
    """Get the global MCP tool integrator."""
    global _mcp_integrator
    if _mcp_integrator is None:
        _mcp_integrator = MCPToolIntegrator()
    return _mcp_integrator
