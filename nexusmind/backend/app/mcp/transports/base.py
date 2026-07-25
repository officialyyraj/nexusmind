"""Base transport interface for MCP communication."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator


class BaseTransport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the MCP server."""
        pass

    @abstractmethod
    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for response."""
        pass

    @abstractmethod
    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        pass

    @abstractmethod
    async def stream_responses(self) -> AsyncGenerator[dict[str, Any], None]:
        """Stream responses from the server (for streaming transports)."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform health check on the transport."""
        pass
