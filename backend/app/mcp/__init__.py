"""MCP (Model Context Protocol) integration module."""

from app.mcp.client import MCPClient
from app.mcp.exceptions import (
    MCPError,
    MCPConnectionError,
    MCPTimeoutError,
    MCPToolNotFoundError,
    MCPToolExecutionError,
    MCPServerError,
    MCPProtocolError,
    MCPTransportError,
    MCPInvalidConfigError,
    MCPPermissionError,
    MCPHealthCheckError,
)
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerInfo,
    MCPServerHealth,
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    MCPRegistryEntry,
    MCPConfig,
    ServerStatus,
    TransportType,
)
from app.mcp.manager import MCPServerManager, get_mcp_manager
from app.mcp.transports import StdioTransport, HTTPTransport

__all__ = [
    # Client
    "MCPClient",
    # Exceptions
    "MCPError",
    "MCPConnectionError",
    "MCPTimeoutError",
    "MCPToolNotFoundError",
    "MCPToolExecutionError",
    "MCPServerError",
    "MCPProtocolError",
    "MCPTransportError",
    "MCPInvalidConfigError",
    "MCPPermissionError",
    "MCPHealthCheckError",
    # Registry
    "MCPRegistry",
    "get_mcp_registry",
    # Manager
    "MCPServerManager",
    "get_mcp_manager",
    # Schemas
    "MCPServerConfig",
    "MCPServerInfo",
    "MCPServerHealth",
    "MCPTool",
    "MCPToolInvocation",
    "MCPToolInvocationResult",
    "MCPRegistryEntry",
    "MCPConfig",
    "ServerStatus",
    "TransportType",
    # Transports
    "StdioTransport",
    "HTTPTransport",
]
