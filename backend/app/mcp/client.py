"""MCP client for connecting to MCP servers."""

import asyncio
from typing import Any, AsyncGenerator

from app.mcp.exceptions import (
    MCPToolExecutionError,
    MCPConnectionError,
    MCPTimeoutError,
    MCPProtocolError,
)
from app.mcp.schemas import (
    CallToolResult,
    MCPTool,
    MCPToolParameter,
    ServerStatus,
    TransportType,
)
from app.mcp.transports.base import BaseTransport
from app.mcp.transports.stdio import StdioTransport
from app.mcp.transports.http import HTTPTransport


class MCPClient:
    """Client for MCP server communication with transport abstraction."""

    def __init__(
        self,
        name: str,
        transport: TransportType,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        self.name = name
        self.transport_type = transport
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self._transport: BaseTransport | None = None
        self._status = ServerStatus.STOPPED
        self._protocol_version: str | None = None
        self._capabilities: dict[str, Any] | None = None
        self._server_info: dict[str, str] | None = None
        self._cancellation_event: asyncio.Event | None = None

    @property
    def status(self) -> ServerStatus:
        """Get server status."""
        return self._status

    @property
    def protocol_version(self) -> str | None:
        """Get negotiated protocol version."""
        return self._protocol_version

    @property
    def capabilities(self) -> dict[str, Any] | None:
        """Get server capabilities."""
        return self._capabilities

    @property
    def server_info(self) -> dict[str, str] | None:
        """Get server info."""
        return self._server_info

    def _create_transport(self) -> BaseTransport:
        """Create the appropriate transport based on type."""
        if self.transport_type == TransportType.STDIO:
            if not self.command:
                raise MCPConnectionError("Command required for stdio transport", self.name)
            return StdioTransport(
                command=self.command,
                args=self.args,
                env=self.env,
            )
        elif self.transport_type == TransportType.HTTP:
            if not self.url:
                raise MCPConnectionError("URL required for HTTP transport", self.name)
            return HTTPTransport(
                url=self.url,
                headers=self.headers,
                timeout=self.timeout,
            )
        elif self.transport_type == TransportType.SSE:
            if not self.url:
                raise MCPConnectionError("URL required for SSE transport", self.name)
            return HTTPTransport(
                url=self.url,
                headers=self.headers,
                timeout=self.timeout,
            )
        else:
            raise MCPProtocolError(f"Unsupported transport type: {self.transport_type}")

    async def start(self) -> None:
        """Start the MCP server and establish connection."""
        if self._status == ServerStatus.RUNNING:
            return

        self._status = ServerStatus.STARTING
        self._cancellation_event = asyncio.Event()

        try:
            # Create and connect transport
            self._transport = self._create_transport()
            await self._transport.connect()

            # Send initialize request
            init_result = await self._send_initialize()

            self._protocol_version = init_result.get("protocolVersion", "2024-11-05")
            self._capabilities = init_result.get("capabilities", {})
            self._server_info = init_result.get("serverInfo", {})

            # Send initialized notification
            await self._transport.send_notification("notifications/initialized")

            self._status = ServerStatus.RUNNING

        except Exception:
            self._status = ServerStatus.ERROR
            if self._transport:
                await self._transport.disconnect()
                self._transport = None
            raise

    async def _send_initialize(self) -> dict[str, Any]:
        """Send initialize request to server."""
        return await self._transport.send_request(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {},
                },
                "clientInfo": {
                    "name": "nexusmind",
                    "version": "1.0.0",
                },
            },
        )

    async def list_tools(self) -> list[MCPTool]:
        """List available tools from server.
        
        Returns:
            List of tools
        """
        if self._status != ServerStatus.RUNNING:
            raise MCPConnectionError("Server not running", self.name)

        result = await self._transport.send_request("tools/list")

        # Parse tools
        tools = []
        for tool_data in result.get("tools", []):
            # Parse input schema
            input_schema = tool_data.get("inputSchema", {})
            parameters = []

            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])

            for param_name, param_info in properties.items():
                parameters.append(MCPToolParameter(
                    name=param_name,
                    type=param_info.get("type", "string"),
                    description=param_info.get("description"),
                    required=param_name in required,
                    default=param_info.get("default"),
                    enum=param_info.get("enum"),
                ))

            tools.append(MCPTool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                server_name=self.name,
                input_schema=input_schema,
                parameters=parameters,
                version=tool_data.get("version"),
                tags=tool_data.get("tags", []),
                permissions=tool_data.get("permissions", []),
                metadata=tool_data.get("metadata", {}),
            ))

        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: float | None = None,
    ) -> CallToolResult:
        """Call a tool on the server.
        
        Args:
            tool_name: Name of tool
            arguments: Tool arguments
            timeout: Optional timeout override
            
        Returns:
            Tool call result
        """
        if self._status != ServerStatus.RUNNING:
            raise MCPConnectionError("Server not running", self.name)

        # Check for cancellation
        if self._cancellation_event and self._cancellation_event.is_set():
            raise MCPToolExecutionError(tool_name, "Tool execution was cancelled", self.name)

        try:
            result = await asyncio.wait_for(
                self._transport.send_request(
                    "tools/call",
                    {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                ),
                timeout=timeout or self.timeout,
            )

            return CallToolResult(
                content=result.get("content", []),
                is_error=result.get("isError", False),
            )

        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"Tool '{tool_name}' timed out", timeout or self.timeout)
        except Exception as e:
            raise MCPToolExecutionError(tool_name, str(e), self.name)

    async def call_tool_streaming(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Call a tool with streaming responses.
        
        Args:
            tool_name: Name of tool
            arguments: Tool arguments
            
        Yields:
            Streaming response chunks
        """
        if self._status != ServerStatus.RUNNING:
            raise MCPConnectionError("Server not running", self.name)

        if self._cancellation_event and self._cancellation_event.is_set():
            raise MCPToolExecutionError(tool_name, "Tool execution was cancelled", self.name)

        # Start the tool call
        result = await self._transport.send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

        # Check if server supports streaming
        if self._capabilities and self._capabilities.get("streaming"):
            async for chunk in self._transport.stream_responses():
                yield chunk
        else:
            # Return result directly if streaming not supported
            yield result

    def cancel(self) -> None:
        """Cancel any ongoing operations."""
        if self._cancellation_event:
            self._cancellation_event.set()

    def reset_cancellation(self) -> None:
        """Reset the cancellation event for new operations."""
        if self._cancellation_event:
            self._cancellation_event.clear()

    async def stop(self) -> None:
        """Stop the MCP server."""
        if self._status == ServerStatus.STOPPED:
            return

        # Cancel any ongoing operations
        self.cancel()

        if self._transport:
            await self._transport.disconnect()
            self._transport = None

        self._status = ServerStatus.STOPPED
        self._protocol_version = None
        self._capabilities = None
        self._server_info = None
        self._cancellation_event = None

    async def health_check(self) -> bool:
        """Perform health check on the server."""
        if not self._transport or self._status != ServerStatus.RUNNING:
            return False
        return await self._transport.health_check()

    async def restart(self) -> None:
        """Restart the server."""
        await self.stop()
        await self.start()

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
