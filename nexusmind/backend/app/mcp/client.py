"""MCP client for connecting to MCP servers."""

import asyncio
import json
import subprocess
from typing import Any, AsyncIterator

import httpx

from app.mcp.schemas import (
    CallToolResult,
    ListToolsResult,
    MCPTool,
    MCPToolParameter,
    ServerStatus,
    TransportType,
)


class MCPClient:
    """Client for MCP server communication."""

    def __init__(
        self,
        name: str,
        transport: TransportType,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        url: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.name = name
        self.transport = transport
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.url = url
        self.headers = headers or {}
        
        self._process: subprocess.Popen | None = None
        self._stdin_writer: asyncio.StreamWriter | None = None
        self._stdout_reader: asyncio.StreamReader | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()
        self._status = ServerStatus.STOPPED

    @property
    def status(self) -> ServerStatus:
        """Get server status."""
        return self._status

    async def start(self) -> None:
        """Start the MCP server."""
        if self._status == ServerStatus.RUNNING:
            return

        self._status = ServerStatus.STARTING

        if self.transport == TransportType.STDIO:
            await self._start_stdio()
        elif self.transport == TransportType.HTTP:
            await self._start_http()
        elif self.transport == TransportType.SSE:
            await self._start_sse()

        # Send initialize request
        await self._send_initialize()
        
        self._status = ServerStatus.RUNNING

    async def _start_stdio(self) -> None:
        """Start server with stdio transport."""
        env = {**subprocess.os.environ, **self.env}
        
        self._process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        
        # Create async streams
        loop = asyncio.get_event_loop()
        self._stdin_writer = asyncio.StreamWriter(
            self._process.stdin,
            protocol=None,
            loop=loop,
        )
        self._stdout_reader = asyncio.StreamReader()
        loop.add_reader(
            self._process.stdout.fileno(),
            lambda: self._stdout_reader.feed_data,
        )

    async def _start_http(self) -> None:
        """Start server with HTTP transport."""
        if not self.url:
            raise ValueError("URL required for HTTP transport")
        
        self._http_client = httpx.AsyncClient(
            base_url=self.url,
            headers=self.headers,
            timeout=60.0,
        )

    async def _start_sse(self) -> None:
        """Start server with SSE transport."""
        if not self.url:
            raise ValueError("URL required for SSE transport")
        
        self._http_client = httpx.AsyncClient(
            base_url=self.url,
            headers=self.headers,
            timeout=60.0,
        )

    async def _send_initialize(self) -> dict[str, Any]:
        """Send initialize request to server."""
        return await self._send_request(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "nexusmind",
                    "version": "1.0.0",
                },
            },
        )

    async def _send_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send JSON-RPC request.
        
        Args:
            method: RPC method name
            params: Method parameters
            
        Returns:
            Response result
        """
        async with self._lock:
            self._request_id += 1
            request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        if self.transport == TransportType.STDIO:
            return await self._send_stdio_request(request)
        else:
            return await self._send_http_request(request)

    async def _send_stdio_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send request via stdio."""
        if not self._stdin_writer:
            raise RuntimeError("Server not started")
        
        # Write request
        data = json.dumps(request) + "\n"
        self._stdin_writer.write(data.encode())
        await self._stdin_writer.drain()
        
        # Read response
        line = await self._stdout_reader.readline()
        response = json.loads(line.decode())
        
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        
        return response.get("result", {})

    async def _send_http_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send request via HTTP."""
        if not self._http_client:
            raise RuntimeError("Server not started")
        
        response = await self._http_client.post(
            "/mcp",
            json=request,
        )
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        
        return data.get("result", {})

    async def list_tools(self) -> list[MCPTool]:
        """List available tools from server.
        
        Returns:
            List of tools
        """
        result = await self._send_request("tools/list")
        
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
            ))
        
        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> CallToolResult:
        """Call a tool on the server.
        
        Args:
            tool_name: Name of tool
            arguments: Tool arguments
            
        Returns:
            Tool call result
        """
        result = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )
        
        return CallToolResult(
            content=result.get("content", []),
            is_error=result.get("isError", False),
        )

    async def stop(self) -> None:
        """Stop the MCP server."""
        if self._status == ServerStatus.STOPPED:
            return

        if self.transport == TransportType.STDIO:
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                self._process = None
                self._stdin_writer = None
                self._stdout_reader = None
        else:
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None

        self._status = ServerStatus.STOPPED

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
