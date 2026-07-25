"""MCP (Model Context Protocol) integration module."""

from app.mcp.client import MCPClient
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerInfo,
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    MCPRegistryEntry,
    MCPConfig,
    ServerStatus,
    TransportType,
)
from app.mcp.server_manager import MCPServerManager, get_mcp_manager

__all__ = [
    # Client
    "MCPClient",
    # Registry
    "MCPRegistry",
    "get_mcp_registry",
    # Manager
    "MCPServerManager",
    "get_mcp_manager",
    # Schemas
    "MCPServerConfig",
    "MCPServerInfo",
    "MCPTool",
    "MCPToolInvocation",
    "MCPToolInvocationResult",
    "MCPRegistryEntry",
    "MCPConfig",
    "ServerStatus",
    "TransportType",
]