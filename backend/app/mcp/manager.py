"""MCP server manager with lifecycle, health checks, and auto-reconnect."""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.mcp.client import MCPClient
from app.mcp.exceptions import (
    MCPError,
    MCPToolNotFoundError,
    MCPToolExecutionError,
    MCPPermissionError,
)
from app.mcp.registry import MCPRegistry, get_mcp_registry
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerInfo,
    MCPServerHealth,
    MCPServerList,
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    MCPConfig,
    ServerStatus,
    TransportType,
)
from app.mcp.utils import get_logger

logger = get_logger(__name__)


class MCPServerManager:
    """Manager for MCP servers with lifecycle, health checks, and auto-reconnect."""

    def __init__(self, registry: MCPRegistry | None = None):
        self.registry = registry or get_mcp_registry()
        self._servers: dict[str, MCPClient] = {}
        self._configs: dict[str, MCPServerConfig] = {}
        self._server_info: dict[str, MCPServerInfo] = {}
        self._health_status: dict[str, MCPServerHealth] = {}
        self._health_check_tasks: dict[str, asyncio.Task] = {}
        self._reconnect_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._enabled = True
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized

    async def load_config(self, config_path: str | Path) -> MCPConfig:
        """Load MCP configuration from YAML file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            MCP configuration
        """
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"MCP config file not found: {config_path}")
            return MCPConfig()

        try:
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

            logger.info(f"Loaded MCP config with {len(config.servers)} servers")
            return config

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            return MCPConfig()

    async def configure(self, config: MCPConfig) -> None:
        """Configure MCP servers from config.
        
        Args:
            config: MCP configuration
        """
        async with self._lock:
            self._enabled = config.enabled
            self._configs.clear()

            for server_config in config.servers:
                self._configs[server_config.name] = server_config
                logger.info(f"Configured MCP server: {server_config.name}")

    async def initialize(self, config: MCPConfig | None = None) -> None:
        """Initialize the manager and optionally start servers.
        
        Args:
            config: Optional MCP configuration to load
        """
        if self._initialized:
            return

        if config:
            await self.configure(config)

        self._initialized = True
        logger.info("MCP server manager initialized")

    async def shutdown(self) -> None:
        """Shutdown all servers and cleanup."""
        logger.info("Shutting down MCP server manager")

        # Cancel all health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()
        self._health_check_tasks.clear()

        # Cancel all reconnect tasks
        for task in self._reconnect_tasks.values():
            task.cancel()
        self._reconnect_tasks.clear()

        # Stop all servers
        await self.stop_all()

        self._initialized = False
        logger.info("MCP server manager shutdown complete")

    async def add_server(self, config: MCPServerConfig) -> None:
        """Add a new server configuration.
        
        Args:
            config: Server configuration
        """
        async with self._lock:
            self._configs[config.name] = config
            logger.info(f"Added MCP server: {config.name}")

    async def remove_server(self, server_name: str) -> bool:
        """Remove a server configuration.
        
        Args:
            server_name: Name of server to remove
            
        Returns:
            True if server was removed
        """
        async with self._lock:
            # Stop if running
            if server_name in self._servers:
                await self.stop_server(server_name)

            # Remove config
            if server_name in self._configs:
                del self._configs[server_name]
                logger.info(f"Removed MCP server: {server_name}")
                return True

            return False

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
            timeout=config.timeout,
        )

        try:
            # Start server
            await client.start()

            # Get tools with filtering
            tools = await client.list_tools()
            tools = self._filter_tools(tools, config)

            # Register tools in registry
            for tool in tools:
                await self.registry.register_tool(
                    tool,
                    self._create_tool_handler(client, tool.name)
                )

            # Update info
            info = MCPServerInfo(
                name=server_name,
                status=ServerStatus.RUNNING,
                transport=config.transport,
                tools_count=len(tools),
                started_at=datetime.utcnow(),
                trusted=config.trusted,
                allowlist=config.allowlist,
                blocklist=config.blocklist,
            )

            async with self._lock:
                self._servers[server_name] = client
                self._server_info[server_name] = info

            # Start health check
            self._start_health_check(server_name, config)

            logger.info(f"Started MCP server '{server_name}' with {len(tools)} tools")
            return info

        except Exception as e:
            info = MCPServerInfo(
                name=server_name,
                status=ServerStatus.ERROR,
                transport=config.transport,
                tools_count=0,
                last_error=str(e),
                trusted=config.trusted,
            )
            async with self._lock:
                self._server_info[server_name] = info
            logger.error(f"Failed to start MCP server '{server_name}': {e}")
            raise

    def _filter_tools(self, tools: list[MCPTool], config: MCPServerConfig) -> list[MCPTool]:
        """Filter tools based on allowlist/blocklist.
        
        Args:
            tools: List of tools
            config: Server configuration
            
        Returns:
            Filtered list of tools
        """
        filtered = []
        for tool in tools:
            # Check blocklist
            if config.blocklist and tool.name in config.blocklist:
                continue

            # Check allowlist
            if config.allowlist and tool.name not in config.allowlist:
                continue

            filtered.append(tool)

        return filtered

    async def stop_server(self, server_name: str) -> bool:
        """Stop a specific MCP server.
        
        Args:
            server_name: Name of server to stop
            
        Returns:
            True if server was stopped
        """
        # Cancel health check
        if server_name in self._health_check_tasks:
            self._health_check_tasks[server_name].cancel()
            del self._health_check_tasks[server_name]

        # Cancel reconnect task
        if server_name in self._reconnect_tasks:
            self._reconnect_tasks[server_name].cancel()
            del self._reconnect_tasks[server_name]

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

            logger.info(f"Stopped MCP server: {server_name}")
            return True

    async def start_all(self) -> list[MCPServerInfo]:
        """Start all configured servers.
        
        Returns:
            List of server info for started servers
        """
        if not self._enabled:
            logger.info("MCP is disabled, skipping server start")
            return []

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

    def get_server_config(self, server_name: str) -> MCPServerConfig | None:
        """Get configuration for a server.
        
        Args:
            server_name: Name of server
            
        Returns:
            Server config or None
        """
        return self._configs.get(server_name)

    def list_server_configs(self) -> list[MCPServerConfig]:
        """List all server configurations.
        
        Returns:
            List of server configs
        """
        return list(self._configs.values())

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
                raise MCPToolExecutionError(tool_name, str(result.content), client.name)

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
        return self.registry.list_tools()

    def _start_health_check(self, server_name: str, config: MCPServerConfig) -> None:
        """Start health check task for a server.
        
        Args:
            server_name: Name of server
            config: Server configuration
        """
        async def health_check_loop():
            while True:
                try:
                    await asyncio.sleep(config.health_check_interval)

                    async with self._lock:
                        if server_name not in self._servers:
                            break
                        client = self._servers[server_name]

                    start_time = time.time()
                    healthy = await client.health_check()
                    latency = (time.time() - start_time) * 1000

                    self._health_status[server_name] = MCPServerHealth(
                        server_name=server_name,
                        healthy=healthy,
                        latency_ms=latency,
                        last_check=datetime.utcnow(),
                    )

                    if not healthy and config.auto_reconnect:
                        logger.warning(f"Server '{server_name}' health check failed, attempting reconnect")
                        asyncio.create_task(self._reconnect_server(server_name, config))

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health check error for '{server_name}': {e}")

        task = asyncio.create_task(health_check_loop())
        self._health_check_tasks[server_name] = task

    async def _reconnect_server(self, server_name: str, config: MCPServerConfig) -> None:
        """Reconnect a server after disconnect.
        
        Args:
            server_name: Name of server
            config: Server configuration
        """
        if server_name in self._reconnect_tasks:
            return  # Already reconnecting

        async def reconnect_loop():
            max_retries = 3
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    logger.info(f"Reconnecting to '{server_name}' (attempt {attempt + 1}/{max_retries})")
                    await self.start_server(server_name)
                    logger.info(f"Successfully reconnected to '{server_name}'")
                    return
                except Exception as e:
                    logger.warning(f"Reconnect attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))

            logger.error(f"Failed to reconnect to '{server_name}' after {max_retries} attempts")

        task = asyncio.create_task(reconnect_loop())
        self._reconnect_tasks[server_name] = task

    async def health_check(self, server_name: str | None = None) -> MCPServerHealth | list[MCPServerHealth]:
        """Get health status for server(s).
        
        Args:
            server_name: Optional specific server name
            
        Returns:
            Health status for server or all servers
        """
        if server_name:
            return self._health_status.get(server_name, MCPServerHealth(
                server_name=server_name,
                healthy=False,
                error="Server not found",
            ))

        return list(self._health_status.values())

    async def validate_tool_permission(
        self,
        tool_name: str,
        required_permission: str | None = None,
    ) -> bool:
        """Validate tool permission.
        
        Args:
            tool_name: Name of tool
            required_permission: Optional required permission
            
        Returns:
            True if tool is permitted
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise MCPToolNotFoundError(tool_name)

        # If tool has no permissions, it's allowed
        if not tool.permissions:
            return True

        # If no specific permission required, allow tools with any permissions
        if not required_permission:
            return True

        return required_permission in tool.permissions


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


# For backwards compatibility
MCPServerManager = MCPServerManager
get_mcp_manager = get_mcp_manager
