# Model Context Protocol (MCP) Integration

The MCP integration provides a standardized way to connect AI agents with external tools and services through the Model Context Protocol.

## Architecture

```
app/mcp/
├── __init__.py           # Module exports
├── schemas.py            # Pydantic models
├── registry.py           # Dynamic tool registry
├── client.py            # MCP client (stdio/HTTP)
└── server_manager.py    # Server lifecycle management
```

## Concepts

### MCP Server
An MCP server is a process that provides tools through the MCP protocol. Servers can use different transports:

- **stdio**: Server runs as a subprocess, communicates via stdin/stdout
- **HTTP**: Server exposes HTTP endpoint, communicates via JSON-RPC
- **SSE**: Server uses Server-Sent Events for streaming responses

### MCP Tool
A tool is a callable function exposed by an MCP server. Tools have:
- **Name**: Unique identifier
- **Description**: Human-readable description
- **Parameters**: JSON Schema defining input
- **Server**: Which server provides this tool

### MCP Registry
Central registry that tracks all available tools from all servers. Provides:
- Dynamic registration/unregistration
- Tool lookup by name
- Tool invocation with timeout
- Server-scoped tool queries

## Features

- **Multi-transport support**: stdio, HTTP, SSE
- **Auto-discovery**: Automatically discover tools when server starts
- **Dynamic registration**: Register/unregister tools at runtime
- **Tool invocation**: Invoke tools with arguments and timeout
- **Server management**: Start/stop/restart servers
- **YAML configuration**: Configure servers via config file

## Configuration

Create `mcp.yaml` in your config directory:

```yaml
enabled: true
default_timeout: 30
auto_discover: true

servers:
  # Filesystem server via stdio
  - name: filesystem
    transport: stdio
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
    env:
      HOME: /home/user
    enabled: true

  # GitHub server via HTTP
  - name: github
    transport: http
    url: https://api.github.com/mcp
    headers:
      Authorization: "Bearer ${GITHUB_TOKEN}"
    enabled: true
```

## Usage

### Initialize MCP Manager

```python
from app.mcp import get_mcp_manager

manager = get_mcp_manager()

# Load configuration
config = await manager.load_config("config/mcp.yaml")
await manager.configure(config)
```

### Start Servers

```python
# Start specific server
info = await manager.start_server("filesystem")

# Start all enabled servers
servers = await manager.start_all()
```

### List Available Tools

```python
# All tools
tools = manager.get_registered_tools()

# Tools by server
tools = manager.get_tools_by_server("filesystem")

# Tools for specific agent
tools = manager.get_tools_for_agent("coder")
```

### Invoke Tool

```python
from app.mcp import MCPToolInvocation

result = await manager.invoke_tool(
    MCPToolInvocation(
        tool_name="filesystem__list_directory",
        arguments={"path": "/workspace"},
        timeout=30,
    )
)

if result.success:
    print(result.result)
else:
    print(f"Error: {result.error}")
```

### Direct Registry Access

```python
from app.mcp import get_mcp_registry

registry = get_mcp_registry()

# Register a custom tool
tool = MCPTool(
    name="custom_tool",
    description="Custom tool",
    server_name="custom",
    input_schema={...},
    parameters=[],
)

async def handler(**kwargs):
    return {"result": "ok"}

await registry.register_tool(tool, handler)

# Invoke
result = await registry.invoke_tool(
    MCPToolInvocation(tool_name="custom_tool", arguments={})
)
```

## API Reference

### MCPServerManager

```python
class MCPServerManager:
    async def load_config(path: str | Path) -> MCPConfig
    async def configure(config: MCPConfig) -> None
    async def start_server(name: str) -> MCPServerInfo
    async def stop_server(name: str) -> bool
    async def start_all() -> list[MCPServerInfo]
    async def stop_all() -> None
    async def restart_server(name: str) -> MCPServerInfo
    async def invoke_tool(invocation: MCPToolInvocation) -> MCPToolInvocationResult
    def get_registered_tools() -> list[MCPTool]
    def list_servers() -> list[MCPServerInfo]
```

### MCPRegistry

```python
class MCPRegistry:
    async def register_tool(tool: MCPTool, handler: Callable) -> None
    async def unregister_tool(name: str) -> bool
    async def unregister_server_tools(server: str) -> list[str]
    async def invoke_tool(invocation: MCPToolInvocation) -> MCPToolInvocationResult
    def get_tool(name: str) -> MCPTool | None
    def list_tools() -> list[MCPTool]
    def get_tools_by_server(server: str) -> list[MCPTool]
```

### MCPClient

```python
class MCPClient:
    async def start() -> None
    async def stop() -> None
    async def list_tools() -> list[MCPTool]
    async def call_tool(name: str, args: dict) -> CallToolResult
```

## Schemas

### MCPServerConfig
```python
name: str                    # Server name
transport: TransportType     # stdio, http, sse
command: str | None         # For stdio transport
args: list[str]             # Command arguments
env: dict[str, str]         # Environment variables
url: str | None             # For HTTP transport
headers: dict[str, str]     # HTTP headers
enabled: bool               # Enable/disable server
```

### MCPTool
```python
name: str                   # Tool name
description: str            # Tool description
server_name: str            # Server providing this tool
input_schema: dict          # JSON Schema
parameters: list[MCPToolParameter]  # Parameter definitions
```

### MCPToolInvocation
```python
tool_name: str              # Name of tool to invoke
arguments: dict             # Tool arguments
timeout: int                # Timeout in seconds (default: 30)
```

## Testing

```bash
pytest tests/mcp/test_mcp.py -v
```

All 24 MCP tests pass:
- Schema validation
- Tool registration/unregistration
- Tool invocation with success and error cases
- Timeout handling
- Server management

## Integration with Tool Registry

The MCP registry integrates with the existing tool registry:

```python
# Tools can be accessed via both interfaces
from app.tools import get_tool_registry

# Get MCP tools
mcp_tools = get_mcp_registry().list_tools()

# Or via unified tool registry
tool_registry = get_tool_registry()
mcp_tools = tool_registry.get_tools_by_source("mcp")
```

## Best Practices

1. **Server isolation**: Each MCP server runs independently
2. **Timeout handling**: Always set appropriate timeouts
3. **Error handling**: Check result.success before accessing result.data
4. **Resource cleanup**: Stop servers when done
5. **Configuration**: Use YAML for production deployments
