"""Stdio transport for MCP server communication."""

import asyncio
import json
import os
import subprocess
from typing import Any, AsyncGenerator

from app.mcp.exceptions import MCPConnectionError, MCPTransportError
from app.mcp.transports.base import BaseTransport


class StdioTransport(BaseTransport):
    """Transport implementation using stdio for MCP server communication."""

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ):
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.cwd = cwd
        self._process: subprocess.Popen | None = None
        self._stdin_writer: asyncio.StreamWriter | None = None
        self._stdout_reader: asyncio.StreamReader | None = None
        self._stderr_reader: asyncio.StreamReader | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()
        self._connected = False
        self._response_futures: dict[int, asyncio.Future] = {}

    async def connect(self) -> None:
        """Start the MCP server process and establish stdio communication."""
        if self._connected:
            return

        try:
            # Prepare environment
            env = {**os.environ, **self.env}

            # Start process
            self._process = subprocess.Popen(
                [self.command, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self.cwd,
            )

            # Create async streams
            loop = asyncio.get_event_loop()

            # Stdout reader for responses
            self._stdout_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self._stdout_reader)
            await loop.connect_read_pipe(lambda: protocol, self._process.stdout)

            # Stdin writer
            transport, _ = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin, self._process.stdin
            )
            self._stdin_writer = asyncio.StreamWriter(transport, protocol, self._stdout_reader, loop)

            # Start stderr reader for error logging
            self._stderr_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self._stderr_reader)
            await loop.connect_read_pipe(lambda: protocol, self._process.stderr)

            # Start background task to read responses
            asyncio.create_task(self._read_loop())

            self._connected = True

        except FileNotFoundError as e:
            raise MCPConnectionError(f"Command not found: {self.command}") from e
        except Exception as e:
            raise MCPTransportError(f"Failed to start server: {e}", transport="stdio") from e

    async def _read_loop(self) -> None:
        """Background task to read responses from stdout."""
        try:
            while True:
                if self._stdout_reader is None:
                    break
                line = await self._stdout_reader.readline()
                if not line:
                    break

                try:
                    response = json.loads(line.decode())
                except json.JSONDecodeError:
                    continue

                # Handle responses
                if "id" in response and response["id"] in self._response_futures:
                    future = self._response_futures.pop(response["id"])
                    if "error" in response:
                        future.set_result(response)
                    else:
                        future.set_result(response)
                elif "error" in response:
                    # Log error notifications
                    pass

        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def disconnect(self) -> None:
        """Stop the MCP server process."""
        if not self._connected:
            return

        self._connected = False

        # Cancel pending futures
        for future in self._response_futures.values():
            if not future.done():
                future.cancel()
        self._response_futures.clear()

        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

        self._stdin_writer = None
        self._stdout_reader = None
        self._stderr_reader = None

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for response."""
        if not self._connected:
            raise MCPTransportError("Not connected", transport="stdio")

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

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._response_futures[request_id] = future

        try:
            # Send request
            data = json.dumps(request) + "\n"
            if self._stdin_writer:
                self._stdin_writer.write(data.encode())
                await self._stdin_writer.drain()

            # Wait for response
            response = await asyncio.wait_for(future, timeout=60.0)

            if "error" in response:
                raise MCPTransportError(
                    f"Server error: {response['error']}",
                    transport="stdio",
                )

            return response.get("result", {})

        except asyncio.TimeoutError:
            self._response_futures.pop(request_id, None)
            raise
        finally:
            self._response_futures.pop(request_id, None)

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._connected:
            raise MCPTransportError("Not connected", transport="stdio")

        request = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            request["params"] = params

        data = json.dumps(request) + "\n"
        if self._stdin_writer:
            self._stdin_writer.write(data.encode())
            await self._stdin_writer.drain()

    async def stream_responses(self) -> AsyncGenerator[dict[str, Any], None]:
        """Stream responses from the server (stdio is request-response only)."""
        # Stdio is not a streaming transport, but we can yield pending responses
        while self._connected:
            await asyncio.sleep(0.1)

    def is_connected(self) -> bool:
        """Check if transport is connected."""
        if not self._connected:
            return False
        if self._process and self._process.poll() is not None:
            self._connected = False
            return False
        return True

    async def health_check(self) -> bool:
        """Perform health check by attempting to ping the server."""
        if not self.is_connected():
            return False
        try:
            await self.send_notification("ping")
            return True
        except Exception:
            return False
