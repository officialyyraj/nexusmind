"""MCP exceptions for error handling."""


class MCPError(Exception):
    """Base exception for MCP-related errors."""

    def __init__(self, message: str, code: int | None = None):
        self.message = message
        self.code = code or -32603  # Internal error
        super().__init__(self.message)


class MCPConnectionError(MCPError):
    """Raised when connection to MCP server fails."""

    def __init__(self, message: str, server_name: str | None = None):
        self.server_name = server_name
        super().__init__(f"Connection failed to server '{server_name}': {message}" if server_name else message, code=-32000)


class MCPTimeoutError(MCPError):
    """Raised when MCP operation times out."""

    def __init__(self, message: str, timeout: float | None = None):
        self.timeout = timeout
        timeout_str = f" (timeout: {timeout}s)" if timeout else ""
        super().__init__(f"Operation timed out{timeout_str}: {message}", code=-32001)


class MCPToolNotFoundError(MCPError):
    """Raised when MCP tool is not found."""

    def __init__(self, tool_name: str, server_name: str | None = None):
        self.tool_name = tool_name
        self.server_name = server_name
        msg = f"Tool '{tool_name}' not found"
        if server_name:
            msg += f" on server '{server_name}'"
        super().__init__(msg, code=-32601)


class MCPToolExecutionError(MCPError):
    """Raised when MCP tool execution fails."""

    def __init__(self, tool_name: str, message: str, server_name: str | None = None):
        self.tool_name = tool_name
        self.server_name = server_name
        msg = f"Tool '{tool_name}' execution failed: {message}"
        if server_name:
            msg = f"[{server_name}] {msg}"
        super().__init__(msg, code=-32002)


class MCPServerError(MCPError):
    """Raised when MCP server returns an error."""

    def __init__(self, message: str, server_name: str | None = None, code: int | None = None):
        self.server_name = server_name
        msg = f"Server error: {message}"
        if server_name:
            msg = f"[{server_name}] {msg}"
        super().__init__(msg, code=code or -32003)


class MCPProtocolError(MCPError):
    """Raised when MCP protocol violation is detected."""

    def __init__(self, message: str):
        super().__init__(f"Protocol error: {message}", code=-32004)


class MCPTransportError(MCPError):
    """Raised when MCP transport fails."""

    def __init__(self, message: str, transport: str | None = None):
        self.transport = transport
        msg = "Transport error"
        if transport:
            msg += f" ({transport})"
        msg += f": {message}"
        super().__init__(msg, code=-32005)


class MCPInvalidConfigError(MCPError):
    """Raised when MCP configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(f"Invalid configuration: {message}", code=-32006)


class MCPPermissionError(MCPError):
    """Raised when MCP operation is not permitted."""

    def __init__(self, tool_name: str, permission: str):
        self.tool_name = tool_name
        self.permission = permission
        super().__init__(
            f"Permission denied for tool '{tool_name}': requires '{permission}' permission",
            code=-32007,
        )


class MCPHealthCheckError(MCPError):
    """Raised when MCP health check fails."""

    def __init__(self, server_name: str, message: str):
        self.server_name = server_name
        super().__init__(f"Health check failed for '{server_name}': {message}", code=-32008)
