"""MCP server manager for managing multiple MCP servers."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.mcp.client import MCPClient
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerInfo,
    MCPServerList,
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    MCPConfig,
    ServerStatus,
    TransportType,
)


class MCPServerManager:
    """Manager for MCP servers with auto-discovery and tool registration."""

    def __init__(self, registry: MCPRegistry | None = None):
        self.registry = registry or get_mcp_registry()
        self._servers: dict[str, MCPClient] = {}
        self._configs: dict[str, MCPServerConfig] = {}
        self._server_info: dict[str, MCPServerInfo] = {}
        self._lock = asyncio.Lock()

    async def load_config(self, config_path: str | Path) -> MCPConfig:
        """Load MCP configuration from YAML file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            MCP configuration
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            return MCPConfig()
        
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        
        config = MCPConfig(
            enabled=data.get("enabled", True),
            servers=[
                MCPServerConfig(**server)
                for server in data.get("servers", [])
            ],
            default_timeout=data.get("default_timeout", 30),
            auto_discover=data.get("auto_discover", True),
        )
        
        return config

    async def configure(self, config: MCPConfig) -> None:
        """Configure MCP servers from config.
        
        Args:
            config: MCP configuration
        """
        async with self._lock:
            for server_config in config.servers:
                self._configs[server_config.name] = server_config

    async def start_server(self, server_name: str) -> MCPServerInfo:
        """Start a specific MCP server.
        
        Args:
            server_name: Name of server to start
            
        Returns:
            Server info
        """
        async with self._lock:
            config = self._configs.get(server_name)
            if not config:
                raise ValueError(f"Server not configured: {server_name}")
            
            if server_name in self._servers:
                client = self._servers[server_name]
                if client.status == ServerStatus.RUNNING:
                    return self._server_info[server_name]
                await client.stop()

        # Create client
        client = MCPClient(
            name=config.name,
            transport=config.transport,
            command=config.command,
            args=config.args,
            env=config.env,
            url=config.url,
            headers=config.headers,
        )

        try:
            # Start server
            await client.start()
            
            # Get tools
            tools = await client.list_tools()
            
            # Register tools in registry
            for tool in tools:
                await self.registry.register_tool(tool, self._create_tool_handler(client, tool.name))
            
            # Update info
            info = MCPServerInfo(
                name=server_name,
                status=ServerStatus.RUNNING,
                transport=config.transport,
                tools_count=len(tools),
                started_at=datetime.utcnow(),
            )
            
            async with self._lock:
                self._servers[server_name] = client
                self._server_info[server_name] = info
            
            return info
            
        except Exception as e:
            async with self._lock:
                self._server_info[server_name] = MCPServerInfo(
                    name=server_name,
                    status=ServerStatus.ERROR,
                    transport=config.transport,
                    tools_count=0,
                    last_error=str(e),
                )
            raise

    async def stop_server(self, server_name: str) -> bool:
        """Stop a specific MCP server.
        
        Args:
            server_name: Name of server to stop
            
        Returns:
            True if server was stopped
        """
        async with self._lock:
            if server_name not in self._servers:
                return False
            
            client = self._servers[server_name]
            await client.stop()
            
            # Unregister tools
            await self.registry.unregister_server_tools(server_name)
            
            # Update info
            if server_name in self._server_info:
                self._server_info[server_name].status = ServerStatus.STOPPED
                self._server_info[server_name].tools_count = 0
            
            del self._servers[server_name]
            
            return True

    async def start_all(self) -> list[MCPServerInfo]:
        """Start all configured servers.
        
        Returns:
            List of server info for started servers
        """
        results = []
        
        async with self._lock:
            server_names = list(self._configs.keys())
        
        for server_name in server_names:
            config = self._configs[server_name]
            if config.enabled:
                try:
                    info = await self.start_server(server_name)
                    results.append(info)
                except Exception as e:
                    results.append(MCPServerInfo(
                        name=server_name,
                        status=ServerStatus.ERROR,
                        transport=config.transport,
                        tools_count=0,
                        last_error=str(e),
                    ))
        
        return results

    async def stop_all(self) -> None:
        """Stop all running servers."""
        async with self._lock:
            server_names = list(self._servers.keys())
        
        for server_name in server_names:
            await self.stop_server(server_name)

    async def restart_server(self, server_name: str) -> MCPServerInfo:
        """Restart a server.
        
        Args:
            server_name: Name of server to restart
            
        Returns:
            Updated server info
        """
        await self.stop_server(server_name)
        return await self.start_server(server_name)

    def get_server_info(self, server_name: str) -> MCPServerInfo | None:
        """Get info for a server.
        
        Args:
            server_name: Name of server
            
        Returns:
            Server info or None
        """
        return self._server_info.get(server_name)

    def list_servers(self) -> list[MCPServerInfo]:
        """List all servers.
        
        Returns:
            List of server info
        """
        return list(self._server_info.values())

    def _create_tool_handler(
        self,
        client: MCPClient,
        tool_name: str,
    ) -> callable:
        """Create a handler function for a tool.
        
        Args:
            client: MCP client
            tool_name: Tool name
            
        Returns:
            Async callable handler
        """
        async def handler(**kwargs) -> Any:
            result = await client.call_tool(tool_name, kwargs)
            
            if result.is_error:
                raise RuntimeError(f"Tool error: {result.content}")
            
            # Extract result from content
            if result.content and len(result.content) > 0:
                return result.content[0].get("text", result.content)
            
            return result.content
        
        return handler

    async def invoke_tool(
        self,
        invocation: MCPToolInvocation,
    ) -> MCPToolInvocationResult:
        """Invoke a tool by name.
        
        Args:
            invocation: Tool invocation
            
        Returns:
            Tool invocation result
        """
        return await self.registry.invoke_tool(invocation)

    async def discover_tools(self, server_name: str) -> list[MCPTool]:
        """Manually discover tools from a server.
        
        Args:
            server_name: Name of server
            
        Returns:
            List of discovered tools
        """
        async with self._lock:
            if server_name not in self._servers:
                raise ValueError(f"Server not running: {server_name}")
            
            client = self._servers[server_name]
        
        return await client.list_tools()

    def get_registered_tools(self) -> list[MCPTool]:
        """Get all registered tools.
        
        Returns:
            List of all registered tools
        """
        return self.registry.list_tools()

    def get_tools_for_agent(self, agent_type: str | None = None) -> list[MCPTool]:
        """Get tools suitable for an agent.
        
        Args:
            agent_type: Optional agent type filter
            
        Returns:
            List of tools for the agent
        """
        all_tools = self.registry.list_tools()
        
        if not agent_type:
            return all_tools
        
        # Filter tools by agent type prefix
        prefix = f"{agent_type}_"
        return [t for t in all_tools if t.name.startswith(prefix)] + [
            t for t in all_tools if not t.name.startswith(t.server_name)
        ]


# Global manager instance
_mcp_manager: MCPServerManager | None = None


def get_mcp_manager() -> MCPServerManager:
    """Get the global MCP manager.
    
    Returns:
        MCPServerManager instance
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPServerManager()
    return _mcp_manager
