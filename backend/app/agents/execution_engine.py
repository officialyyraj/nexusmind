"""Agent Execution Engine - Unified tool invocation for autonomous agents.

This module provides the core execution infrastructure for agents to:
- Execute tools through a unified protocol
- Perform reasoning loops with tool observations
- Handle multi-tool execution chains
- Integrate with memory for context
- Discover and invoke MCP tools
- Gracefully recover from failures

Architecture:
    Agent → ToolInvoker → Tool Registry → Tool Execution
                ↓
           Reasoning Loop
                ↓
         Observation → Continue or Finalize
"""

import asyncio
import json
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from app.tools.registry import (
    BaseTool,
    ToolHealth,
    ToolRegistry,
    get_tool_registry,
)
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.mcp.schemas import MCPToolInvocation


class ToolCallStatus(str, Enum):
    """Status of a tool call."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ToolType(str, Enum):
    """Type of tool being invoked."""
    
    NATIVE = "native"      # Built-in tool from Tool Registry
    FUNCTION = "function"  # Function-based tool
    MCP = "mcp"           # MCP server tool


@dataclass
class ToolPermission:
    """Permission required for a tool."""
    
    name: str
    description: str
    required: bool = True


@dataclass
class ToolCapabilities:
    """Capabilities exposed by a tool."""
    
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    permissions: list[ToolPermission] = field(default_factory=list)
    rate_limit: int | None = None  # Calls per minute


@dataclass
class ToolMetadata:
    """Complete metadata for a tool."""
    
    name: str
    description: str
    tool_type: ToolType
    health: ToolHealth = ToolHealth.UNKNOWN
    capabilities: ToolCapabilities = field(default_factory=ToolCapabilities)
    server_name: str | None = None  # For MCP tools
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime | None = None
    use_count: int = 0
    average_execution_time: float = 0.0


@dataclass
class ToolCall:
    """A single tool call request."""
    
    call_id: str
    tool_name: str
    tool_type: ToolType
    arguments: dict[str, Any]
    timeout: float = 30.0
    metadata: ToolMetadata | None = None
    
    @classmethod
    def create(
        cls,
        tool_name: str,
        tool_type: ToolType,
        arguments: dict[str, Any],
        timeout: float = 30.0,
        metadata: ToolMetadata | None = None,
    ) -> "ToolCall":
        """Create a new tool call with generated ID."""
        return cls(
            call_id=str(uuid.uuid4()),
            tool_name=tool_name,
            tool_type=tool_type,
            arguments=arguments,
            timeout=timeout,
            metadata=metadata,
        )


@dataclass
class ToolResult:
    """Result of a tool execution."""
    
    call_id: str
    tool_name: str
    tool_type: ToolType
    status: ToolCallStatus
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    
    def is_success(self) -> bool:
        """Check if the tool call succeeded."""
        return self.status == ToolCallStatus.SUCCESS
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "tool_type": self.tool_type.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "artifacts": self.artifacts,
        }


@dataclass
class ToolExecutionContext:
    """Context for tool execution including agent info."""
    
    agent_type: str
    session_id: str
    execution_id: str | None = None
    max_tools_per_turn: int = 10
    max_total_tools: int = 100
    tool_count: int = 0
    observations: list[ToolResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentToolInvoker:
    """Unified tool invocation for agents.
    
    This class provides a single interface for agents to:
    - Execute tools through the Tool Registry
    - Invoke MCP tools seamlessly
    - Track execution context
    - Handle errors and timeouts
    - Build execution traces
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        mcp_registry: MCPRegistry | None = None,
    ):
        self._tool_registry = tool_registry or get_tool_registry()
        self._mcp_registry = mcp_registry or get_mcp_registry()
        self._execution_history: dict[str, list[ToolCall]] = {}
        self._result_history: dict[str, list[ToolResult]] = {}
        self._lock = asyncio.Lock()
    
    async def invoke(
        self,
        tool_call: ToolCall,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Invoke a tool and return the result.
        
        Args:
            tool_call: The tool call to execute
            context: Execution context including agent info
            
        Returns:
            ToolResult with execution outcome
        """
        start_time = datetime.utcnow()
        context.tool_count += 1
        
        # Check tool count limits
        if context.tool_count > context.max_total_tools:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.FAILED,
                error=f"Exceeded maximum tool calls: {context.max_total_tools}",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )
        
        try:
            if tool_call.tool_type == ToolType.NATIVE:
                result = await self._invoke_native(tool_call, context)
            elif tool_call.tool_type == ToolType.FUNCTION:
                result = await self._invoke_function(tool_call, context)
            elif tool_call.tool_type == ToolType.MCP:
                result = await self._invoke_mcp(tool_call, context)
            else:
                result = ToolResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.call_id,
                    tool_type=tool_call.tool_type,
                    status=ToolCallStatus.FAILED,
                    error=f"Unknown tool type: {tool_call.tool_type}",
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                )
            
            # Update context with observation
            context.observations.append(result)
            
            # Track execution history
            async with self._lock:
                if context.execution_id:
                    if context.execution_id not in self._execution_history:
                        self._execution_history[context.execution_id] = []
                    self._execution_history[context.execution_id].append(tool_call)
                    
                    if context.execution_id not in self._result_history:
                        self._result_history[context.execution_id] = []
                    self._result_history[context.execution_id].append(result)
            
            return result
            
        except asyncio.TimeoutError:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.TIMEOUT,
                error=f"Tool execution timed out after {tool_call.timeout}s",
                execution_time=tool_call.timeout,
            )
        except Exception as e:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.FAILED,
                error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )
    
    async def _invoke_native(
        self,
        tool_call: ToolCall,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Invoke a native tool from the registry."""
        start_time = datetime.utcnow()
        
        # Get tool from registry
        tool = self._tool_registry.get(tool_call.tool_name)
        if not tool:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.FAILED,
                error=f"Tool not found: {tool_call.tool_name}",
                execution_time=0.0,
            )
        
        # Check health
        health = await tool.health()
        if health == ToolHealth.UNHEALTHY:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.FAILED,
                error=f"Tool is unhealthy: {health}",
                execution_time=0.0,
            )
        
        # Check if tool can execute
        if not await tool.can_execute(**tool_call.arguments):
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.FAILED,
                error="Tool cannot execute with given parameters",
                execution_time=0.0,
            )
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                tool.execute(**tool_call.arguments),
                timeout=tool_call.timeout,
            )
            
            # Handle dict result (from registry execute method)
            if isinstance(result, dict):
                success = result.get("success", True)
                if success:
                    return ToolResult(
                        call_id=tool_call.call_id,
                        tool_name=tool_call.tool_name,
                        tool_type=tool_call.tool_type,
                        status=ToolCallStatus.SUCCESS,
                        result=result.get("result", result),
                        execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    )
                else:
                    return ToolResult(
                        call_id=tool_call.call_id,
                        tool_name=tool_call.tool_name,
                        tool_type=tool_call.tool_type,
                        status=ToolCallStatus.FAILED,
                        error=result.get("error", "Unknown error"),
                        execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    )
            
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.SUCCESS,
                result=result,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.TIMEOUT,
                error=f"Execution timed out after {tool_call.timeout}s",
                execution_time=tool_call.timeout,
            )
    
    async def _invoke_function(
        self,
        tool_call: ToolCall,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Invoke a function-based tool."""
        start_time = datetime.utcnow()
        
        # Get function from registry
        func = self._tool_registry.get_function(tool_call.tool_name)
        if not func:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.FAILED,
                error=f"Function not found: {tool_call.tool_name}",
                execution_time=0.0,
            )
        
        try:
            result = await asyncio.wait_for(
                func(**tool_call.arguments),
                timeout=tool_call.timeout,
            )
            
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.SUCCESS,
                result=result,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.TIMEOUT,
                error=f"Execution timed out after {tool_call.timeout}s",
                execution_time=tool_call.timeout,
            )
    
    async def _invoke_mcp(
        self,
        tool_call: ToolCall,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Invoke an MCP tool."""
        start_time = datetime.utcnow()
        
        # Create MCP invocation
        invocation = MCPToolInvocation(
            tool_name=tool_call.tool_name,
            arguments=tool_call.arguments,
            timeout=tool_call.timeout,
        )
        
        # Execute through MCP registry
        try:
            mcp_result = await asyncio.wait_for(
                self._mcp_registry.invoke_tool(invocation),
                timeout=tool_call.timeout,
            )
            
            if mcp_result.success:
                return ToolResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.tool_name,
                    tool_type=tool_call.tool_type,
                    status=ToolCallStatus.SUCCESS,
                    result=mcp_result.result,
                    execution_time=mcp_result.execution_time,
                )
            else:
                return ToolResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.tool_name,
                    tool_type=tool_call.tool_type,
                    status=ToolCallStatus.FAILED,
                    error=mcp_result.error,
                    execution_time=mcp_result.execution_time,
                )
                
        except asyncio.TimeoutError:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                tool_type=tool_call.tool_type,
                status=ToolCallStatus.TIMEOUT,
                error=f"MCP invocation timed out after {tool_call.timeout}s",
                execution_time=tool_call.timeout,
            )
    
    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a tool."""
        # Check native tools
        tool = self._tool_registry.get(tool_name)
        if tool:
            return {
                "name": tool.name,
                "description": tool.description,
                "type": ToolType.NATIVE.value,
            }
        
        # Check function tools
        if self._tool_registry.get_function(tool_name):
            desc = self._tool_registry._tool_functions.get(f"{tool_name}_description", "")
            return {
                "name": tool_name,
                "description": desc,
                "type": ToolType.FUNCTION.value,
            }
        
        # Check MCP tools
        mcp_tool = self._mcp_registry.get_tool(tool_name)
        if mcp_tool:
            return {
                "name": mcp_tool.name,
                "description": mcp_tool.description,
                "type": ToolType.MCP.value,
                "server": mcp_tool.server_name,
            }
        
        return None
    
    def list_available_tools(self) -> list[dict[str, Any]]:
        """List all available tools from all sources."""
        tools = []
        
        # Native tools
        for tool_dict in self._tool_registry.list_builtin_tools():
            tools.append({
                **tool_dict,
                "type": ToolType.NATIVE.value if "type" not in tool_dict else tool_dict.get("type"),
            })
        
        # MCP tools
        for mcp_tool in self._mcp_registry.list_tools():
            tools.append({
                "name": mcp_tool.name,
                "description": mcp_tool.description,
                "type": ToolType.MCP.value,
                "server": mcp_tool.server_name,
            })
        
        return tools
    
    def get_execution_trace(self, execution_id: str) -> dict[str, Any]:
        """Get the execution trace for an agent execution."""
        calls = self._execution_history.get(execution_id, [])
        results = self._result_history.get(execution_id, [])
        
        return {
            "execution_id": execution_id,
            "total_calls": len(calls),
            "successful_calls": sum(1 for r in results if r.is_success()),
            "failed_calls": sum(1 for r in results if not r.is_success()),
            "total_time": sum(r.execution_time for r in results),
            "calls": [c.arguments for c in calls],
            "results": [r.to_dict() for r in results],
        }


# Global invoker instance
_invoker: AgentToolInvoker | None = None


def get_tool_invoker() -> AgentToolInvoker:
    """Get the global tool invoker instance."""
    global _invoker
    if _invoker is None:
        _invoker = AgentToolInvoker()
    return _invoker
