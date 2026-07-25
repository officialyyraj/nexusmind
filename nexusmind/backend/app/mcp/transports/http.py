"""HTTP transport for MCP server communication."""

import asyncio
import json
from typing import Any, AsyncGenerator

import httpx

from app.mcp.exceptions import MCPConnectionError, MCPTransportError
from app.mcp.transports.base import BaseTransport


class HTTPTransport(BaseTransport):
    """Transport implementation using HTTP for MCP server communication."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 60.0,
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._connected = False
        self._request_id = 0
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish HTTP connection to the MCP server."""
        if self._connected:
            return

        try:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                headers=self.headers,
                timeout=self.timeout,
            )
            self._connected = True
        except Exception as e:
            raise MCPConnectionError(f"Failed to connect to {self.url}: {e}") from e

    async def disconnect(self) -> None:
        """Close HTTP connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request over HTTP."""
        if not self._connected or not self._client:
            raise MCPTransportError("Not connected", transport="http")

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

        try:
            response = await self._client.post(
                "/mcp",
                json=request,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise MCPTransportError(
                    f"Server error: {data['error']}",
                    transport="http",
                )

            return data.get("result", {})

        except httpx.TimeoutException as e:
            raise MCPTransportError(f"Request timed out: {e}", transport="http") from e
        except httpx.HTTPStatusError as e:
            raise MCPTransportError(f"HTTP error: {e.response.status_code}", transport="http") from e
        except Exception as e:
            raise MCPTransportError(f"Request failed: {e}", transport="http") from e

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a JSON-RPC notification over HTTP."""
        if not self._connected or not self._client:
            raise MCPTransportError("Not connected", transport="http")

        request = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            request["params"] = params

        try:
            await self._client.post(
                "/mcp",
                json=request,
                timeout=5.0,
            )
        except Exception:
            # Notifications should not raise errors
            pass

    async def stream_responses(self) -> AsyncGenerator[dict[str, Any], None]:
        """Stream responses using HTTP SSE if supported."""
        if not self._connected or not self._client:
            raise MCPTransportError("Not connected", transport="http")

        try:
            async with self._client.stream("GET", "/mcp/stream") as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPStatusError:
            # Server doesn't support streaming, yield nothing
            return

    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected and self._client is not None

    async def health_check(self) -> bool:
        """Perform health check by sending a ping."""
        if not self.is_connected():
            return False
        try:
            await self.send_notification("ping")
            return True
        except Exception:
            return False
