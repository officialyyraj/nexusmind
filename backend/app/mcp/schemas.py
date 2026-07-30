"""MCP schemas for request/response models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TransportType(str, Enum):
    """MCP transport types."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class ServerStatus(str, Enum):
    """MCP server status."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


# ==================== Server Configuration ====================


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    name: str = Field(..., description="Server name")
    transport: TransportType = Field(TransportType.STDIO, description="Transport type")
    command: str | None = Field(None, description="Command for stdio transport")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    url: str | None = Field(None, description="URL for HTTP transport")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    enabled: bool = Field(True, description="Whether server is enabled")
    trusted: bool = Field(True, description="Whether server is trusted")
    auto_reconnect: bool = Field(True, description="Auto-reconnect on disconnect")
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    timeout: int = Field(30, description="Default timeout for tool invocations")
    allowlist: list[str] = Field(default_factory=list, description="Allowed tool names (empty = all)")
    blocklist: list[str] = Field(default_factory=list, description="Blocked tool names")


class MCPServerList(BaseModel):
    """List of MCP server configurations."""

    servers: list[MCPServerConfig]


# ==================== Server State ====================


class MCPServerInfo(BaseModel):
    """Information about a running MCP server."""

    name: str
    status: ServerStatus
    transport: TransportType
    tools_count: int
    started_at: datetime | None = None
    last_error: str | None = None
    trusted: bool = True
    allowlist: list[str] = Field(default_factory=list)
    blocklist: list[str] = Field(default_factory=list)


class MCPServerHealth(BaseModel):
    """Health check result for an MCP server."""

    server_name: str
    healthy: bool
    latency_ms: float | None = None
    last_check: datetime | None = None
    error: str | None = None


# ==================== Tool Definitions ====================


class MCPToolParameter(BaseModel):
    """Parameter definition for an MCP tool."""

    name: str
    type: str
    description: str | None = None
    required: bool = False
    default: Any = None
    enum: list[Any] | None = None


class MCPTool(BaseModel):
    """MCP tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server_name: str = Field(..., description="Server providing this tool")
    input_schema: dict[str, Any] = Field(default_factory=dict, description="JSON Schema for input")
    parameters: list[MCPToolParameter] = Field(default_factory=list, description="Tool parameters")
    version: str | None = Field(None, description="Tool version")
    tags: list[str] = Field(default_factory=list, description="Tool tags for categorization")
    permissions: list[str] = Field(default_factory=list, description="Required permissions")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MCPToolList(BaseModel):
    """List of available MCP tools."""

    tools: list[MCPTool]


# ==================== Tool Invocation ====================


class MCPToolInvocation(BaseModel):
    """Request to invoke an MCP tool."""

    tool_name: str = Field(..., description="Name of tool to invoke")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    timeout: int = Field(30, description="Timeout in seconds")


class MCPToolInvocationResult(BaseModel):
    """Result of tool invocation."""

    success: bool
    tool_name: str
    result: Any = None
    error: str | None = None
    execution_time: float
    server_name: str


# ==================== MCP Protocol Messages ====================


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: Any = None
    error: dict[str, Any] | None = None


class MCPError(BaseModel):
    """MCP error object."""

    code: int
    message: str
    data: Any = None


# ==================== MCP Methods ====================


class InitializeRequest(BaseModel):
    """MCP initialize request."""

    protocol_version: str
    capabilities: dict[str, Any]
    client_info: dict[str, str]


class InitializeResult(BaseModel):
    """MCP initialize result."""

    protocol_version: str
    capabilities: dict[str, Any]
    server_info: dict[str, str]


class ListToolsResult(BaseModel):
    """MCP list tools result."""

    tools: list[dict[str, Any]]


class CallToolRequest(BaseModel):
    """MCP call tool request."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class CallToolResult(BaseModel):
    """MCP call tool result."""

    content: list[dict[str, Any]]
    is_error: bool = False


# ==================== Registry ====================


class MCPRegistryEntry(BaseModel):
    """Entry in the MCP tool registry."""

    tool: MCPTool
    server_name: str
    registered_at: datetime


class MCPRegistry(BaseModel):
    """Registry of all available MCP tools."""

    tools: dict[str, MCPTool] = Field(default_factory=dict, description="tool_name -> tool")
    servers: dict[str, MCPServerInfo] = Field(default_factory=dict, description="server_name -> info")


# ==================== Configuration ====================


class MCPConfig(BaseModel):
    """MCP configuration."""

    enabled: bool = Field(True, description="Enable MCP integration")
    servers: list[MCPServerConfig] = Field(default_factory=list, description="Server configurations")
    default_timeout: int = Field(30, description="Default tool invocation timeout")
    auto_discover: bool = Field(True, description="Auto-discover tools on server start")
