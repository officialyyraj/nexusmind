"""MCP API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.mcp import (
    MCPServerConfig,
    MCPServerHealth,
    MCPServerInfo,
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    get_mcp_manager,
)
from app.mcp.schemas import TransportType

router = APIRouter()


def get_manager():
    """Get MCP manager instance."""
    return get_mcp_manager()


# ==================== Server Management ====================


@router.get("/servers", response_model=list[MCPServerInfo])
async def list_servers() -> list[MCPServerInfo]:
    """List all MCP servers."""
    manager = get_manager()
    return manager.list_servers()


@router.get("/servers/configs", response_model=list[MCPServerConfig])
async def list_server_configs() -> list[MCPServerConfig]:
    """List all MCP server configurations."""
    manager = get_manager()
    return manager.list_server_configs()


@router.get("/servers/{server_name}", response_model=MCPServerInfo)
async def get_server(server_name: str) -> MCPServerInfo:
    """Get MCP server details."""
    manager = get_manager()
    info = manager.get_server_info(server_name)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )
    return info


@router.post("/servers", response_model=MCPServerInfo, status_code=status.HTTP_201_CREATED)
async def add_server(config: MCPServerConfig) -> MCPServerInfo:
    """Add a new MCP server configuration."""
    manager = get_manager()

    # Check if server already exists
    if config.name in manager._configs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server '{config.name}' already exists",
        )

    await manager.add_server(config)

    # Start server if enabled
    if config.enabled:
        return await manager.start_server(config.name)

    # Return info for unstarted server
    return MCPServerInfo(
        name=config.name,
        status="stopped",
        transport=config.transport,
        tools_count=0,
        trusted=config.trusted,
        allowlist=config.allowlist,
        blocklist=config.blocklist,
    )


@router.delete("/servers/{server_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_server(server_name: str) -> None:
    """Remove an MCP server."""
    manager = get_manager()

    if server_name not in manager._configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    await manager.remove_server(server_name)


@router.post("/servers/{server_name}/start", response_model=MCPServerInfo)
async def start_server(server_name: str) -> MCPServerInfo:
    """Start an MCP server."""
    manager = get_manager()

    if server_name not in manager._configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not configured",
        )

    try:
        return await manager.start_server(server_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/servers/{server_name}/stop", status_code=status.HTTP_204_NO_CONTENT)
async def stop_server(server_name: str) -> None:
    """Stop an MCP server."""
    manager = get_manager()

    if server_name not in manager._configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not configured",
        )

    await manager.stop_server(server_name)


@router.post("/servers/{server_name}/restart", response_model=MCPServerInfo)
async def restart_server(server_name: str) -> MCPServerInfo:
    """Restart an MCP server."""
    manager = get_manager()

    if server_name not in manager._configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not configured",
        )

    try:
        return await manager.restart_server(server_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/servers/{server_name}/enable", response_model=MCPServerInfo)
async def enable_server(server_name: str) -> MCPServerInfo:
    """Enable an MCP server."""
    manager = get_manager()

    config = manager.get_server_config(server_name)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not configured",
        )

    config.enabled = True
    return await manager.start_server(server_name)


@router.post("/servers/{server_name}/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_server(server_name: str) -> None:
    """Disable an MCP server."""
    manager = get_manager()

    config = manager.get_server_config(server_name)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not configured",
        )

    config.enabled = False
    await manager.stop_server(server_name)


# ==================== Tool Discovery ====================


@router.get("/tools", response_model=list[MCPTool])
async def list_tools(server_name: str | None = None) -> list[MCPTool]:
    """List all available MCP tools."""
    manager = get_manager()

    if server_name:
        return manager.registry.get_tools_by_server(server_name)

    return manager.get_registered_tools()


@router.get("/tools/{tool_name}", response_model=MCPTool)
async def get_tool(tool_name: str) -> MCPTool:
    """Get MCP tool details."""
    manager = get_manager()

    tool = manager.registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )
    return tool


@router.post("/tools/{tool_name}/discover", response_model=list[MCPTool])
async def discover_tools(server_name: str) -> list[MCPTool]:
    """Discover tools from a server."""
    manager = get_manager()

    try:
        return await manager.discover_tools(server_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ==================== Tool Execution ====================


@router.post("/tools/{tool_name}/execute", response_model=MCPToolInvocationResult)
async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    timeout: int | None = None,
) -> MCPToolInvocationResult:
    """Execute an MCP tool."""
    manager = get_manager()

    invocation = MCPToolInvocation(
        tool_name=tool_name,
        arguments=arguments or {},
        timeout=timeout or 30,
    )

    try:
        return await manager.invoke_tool(invocation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        return MCPToolInvocationResult(
            success=False,
            tool_name=tool_name,
            error=str(e),
            execution_time=0.0,
            server_name="",
        )


# ==================== Health & Status ====================


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Get MCP system status."""
    manager = get_manager()

    servers = manager.list_servers()
    tools = manager.get_registered_tools()

    running_count = sum(1 for s in servers if s.status.value == "running")
    error_count = sum(1 for s in servers if s.status.value == "error")

    return {
        "enabled": manager._enabled,
        "initialized": manager.initialized,
        "servers": {
            "total": len(servers),
            "running": running_count,
            "error": error_count,
        },
        "tools": {
            "total": len(tools),
            "by_server": {
                server: len(manager.registry.get_tools_by_server(server))
                for server in manager.registry.get_servers()
            },
        },
    }


@router.get("/health", response_model=list[MCPServerHealth])
async def get_health(server_name: str | None = None) -> MCPServerHealth | list[MCPServerHealth]:
    """Get health status for server(s)."""
    manager = get_manager()
    return await manager.health_check(server_name)


# ==================== Configuration ====================


@router.get("/config", response_model=dict[str, Any])
async def get_config() -> dict[str, Any]:
    """Get current MCP configuration."""
    manager = get_manager()

    configs = []
    for name, config in manager._configs.items():
        configs.append({
            "name": config.name,
            "transport": config.transport.value,
            "command": config.command,
            "args": config.args,
            "url": config.url,
            "enabled": config.enabled,
            "trusted": config.trusted,
            "auto_reconnect": config.auto_reconnect,
        })

    return {
        "enabled": manager._enabled,
        "servers": configs,
    }


@router.post("/start-all", response_model=list[MCPServerInfo])
async def start_all_servers() -> list[MCPServerInfo]:
    """Start all configured MCP servers."""
    manager = get_manager()
    return await manager.start_all()


@router.post("/stop-all", status_code=status.HTTP_204_NO_CONTENT)
async def stop_all_servers() -> None:
    """Stop all running MCP servers."""
    manager = get_manager()
    await manager.stop_all()
