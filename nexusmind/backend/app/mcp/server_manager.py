"""MCP server manager - backwards compatibility module.

This module re-exports from the new manager module for backwards compatibility.
"""

# Re-export from the new manager module
from app.mcp.manager import (
    MCPServerManager,
    get_mcp_manager,
)

__all__ = [
    "MCPServerManager",
    "get_mcp_manager",
]
