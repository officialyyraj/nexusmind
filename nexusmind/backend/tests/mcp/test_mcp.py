"""Tests for MCP integration."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.mcp.schemas import (
    MCPTool,
    MCPToolInvocation,
    MCPToolInvocationResult,
    MCPServerConfig,
    MCPServerInfo,
    MCPConfig,
    MCPToolParameter,
    TransportType,
    ServerStatus,
)
from app.mcp.registry import MCPRegistry


class TestMCPSchemas:
    """Test MCP schemas."""

    def test_mcp_tool_creation(self):
        """Test creating an MCP tool."""
        tool = MCPTool(
            name="search_files",
            description="Search for files in directory",
            server_name="filesystem",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pattern": {"type": "string"},
                },
                "required": ["path"],
            },
            parameters=[
                MCPToolParameter(
                    name="path",
                    type="string",
                    description="Directory path",
                    required=True,
                ),
            ],
        )
        
        assert tool.name == "search_files"
        assert tool.server_name == "filesystem"
        assert len(tool.parameters) == 1

    def test_mcp_tool_invocation(self):
        """Test creating a tool invocation."""
        invocation = MCPToolInvocation(
            tool_name="search_files",
            arguments={"path": "/tmp", "pattern": "*.py"},
            timeout=30,
        )
        
        assert invocation.tool_name == "search_files"
        assert invocation.arguments["path"] == "/tmp"
        assert invocation.timeout == 30

    def test_mcp_tool_invocation_result(self):
        """Test tool invocation result."""
        result = MCPToolInvocationResult(
            success=True,
            tool_name="search_files",
            result={"files": ["a.py", "b.py"]},
            execution_time=0.5,
            server_name="filesystem",
        )
        
        assert result.success is True
        assert result.result["files"] == ["a.py", "b.py"]

    def test_mcp_server_config(self):
        """Test server config."""
        config = MCPServerConfig(
            name="filesystem",
            transport=TransportType.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            env={"HOME": "/home/user"},
        )
        
        assert config.name == "filesystem"
        assert config.transport == TransportType.STDIO
        assert "npx" in config.command

    def test_mcp_server_config_http(self):
        """Test HTTP server config."""
        config = MCPServerConfig(
            name="github",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"},
        )
        
        assert config.transport == TransportType.HTTP
        assert config.url == "https://api.example.com/mcp"

    def test_mcp_config_defaults(self):
        """Test MCP config defaults."""
        config = MCPConfig()
        
        assert config.enabled is True
        assert config.default_timeout == 30
        assert config.auto_discover is True
        assert len(config.servers) == 0

    def test_server_status_values(self):
        """Test server status enum."""
        assert ServerStatus.STOPPED.value == "stopped"
        assert ServerStatus.STARTING.value == "starting"
        assert ServerStatus.RUNNING.value == "running"
        assert ServerStatus.ERROR.value == "error"


class TestMCPRegistry:
    """Test MCP registry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for testing."""
        return MCPRegistry()

    @pytest.mark.asyncio
    async def test_register_tool(self, registry):
        """Test registering a tool."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {"result": "ok"}
        
        await registry.register_tool(tool, handler)
        
        assert registry.has_tool("test_tool")
        assert registry.count_tools() == 1

    @pytest.mark.asyncio
    async def test_unregister_tool(self, registry):
        """Test unregistering a tool."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {}
        
        await registry.register_tool(tool, handler)
        result = await registry.unregister_tool("test_tool")
        
        assert result is True
        assert not registry.has_tool("test_tool")

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_tool(self, registry):
        """Test unregistering non-existent tool."""
        result = await registry.unregister_tool("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_tool(self, registry):
        """Test getting a tool."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {}
        
        await registry.register_tool(tool, handler)
        
        retrieved = registry.get_tool("test_tool")
        assert retrieved is not None
        assert retrieved.name == "test_tool"

    @pytest.mark.asyncio
    async def test_invoke_tool(self, registry):
        """Test invoking a tool."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {"output": "hello"}
        
        await registry.register_tool(tool, handler)
        
        invocation = MCPToolInvocation(
            tool_name="test_tool",
            arguments={},
        )
        
        result = await registry.invoke_tool(invocation)
        
        assert result.success is True
        assert result.result["output"] == "hello"

    @pytest.mark.asyncio
    async def test_invoke_nonexistent_tool(self, registry):
        """Test invoking non-existent tool."""
        invocation = MCPToolInvocation(
            tool_name="nonexistent",
            arguments={},
        )
        
        result = await registry.invoke_tool(invocation)
        
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_list_tools(self, registry):
        """Test listing all tools."""
        tool1 = MCPTool(
            name="tool1",
            description="Tool 1",
            server_name="server1",
            input_schema={},
            parameters=[],
        )
        tool2 = MCPTool(
            name="tool2",
            description="Tool 2",
            server_name="server1",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {}
        
        await registry.register_tool(tool1, handler)
        await registry.register_tool(tool2, handler)
        
        tools = registry.list_tools()
        assert len(tools) == 2

    @pytest.mark.asyncio
    async def test_get_tools_by_server(self, registry):
        """Test getting tools by server."""
        tool1 = MCPTool(
            name="tool1",
            description="Tool 1",
            server_name="server1",
            input_schema={},
            parameters=[],
        )
        tool2 = MCPTool(
            name="tool2",
            description="Tool 2",
            server_name="server2",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {}
        
        await registry.register_tool(tool1, handler)
        await registry.register_tool(tool2, handler)
        
        tools = registry.get_tools_by_server("server1")
        assert len(tools) == 1
        assert tools[0].name == "tool1"

    @pytest.mark.asyncio
    async def test_unregister_server_tools(self, registry):
        """Test unregistering all tools from a server."""
        tool1 = MCPTool(
            name="tool1",
            description="Tool 1",
            server_name="server1",
            input_schema={},
            parameters=[],
        )
        tool2 = MCPTool(
            name="tool2",
            description="Tool 2",
            server_name="server1",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {}
        
        await registry.register_tool(tool1, handler)
        await registry.register_tool(tool2, handler)
        
        removed = await registry.unregister_server_tools("server1")
        
        assert len(removed) == 2
        assert registry.count_tools() == 0

    @pytest.mark.asyncio
    async def test_tool_timeout(self, registry):
        """Test tool invocation timeout."""
        tool = MCPTool(
            name="slow_tool",
            description="Slow tool",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def slow_handler(**kwargs):
            await asyncio.sleep(10)
            return {}
        
        await registry.register_tool(tool, slow_handler)
        
        invocation = MCPToolInvocation(
            tool_name="slow_tool",
            arguments={},
            timeout=1,
        )
        
        result = await registry.invoke_tool(invocation)
        
        assert result.success is False
        assert "timed out" in result.error

    @pytest.mark.asyncio
    async def test_tool_error(self, registry):
        """Test tool invocation error."""
        tool = MCPTool(
            name="error_tool",
            description="Error tool",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def error_handler(**kwargs):
            raise ValueError("Something went wrong")
        
        await registry.register_tool(tool, error_handler)
        
        invocation = MCPToolInvocation(
            tool_name="error_tool",
            arguments={},
        )
        
        result = await registry.invoke_tool(invocation)
        
        assert result.success is False
        assert "Something went wrong" in result.error


class TestMCPServerManager:
    """Test MCP server manager."""

    @pytest.mark.asyncio
    async def test_configure_servers(self):
        """Test configuring servers."""
        from app.mcp.server_manager import MCPServerManager
        
        manager = MCPServerManager()
        
        config = MCPConfig(
            servers=[
                MCPServerConfig(
                    name="test_server",
                    transport=TransportType.STDIO,
                    command="echo",
                    args=["hello"],
                ),
            ],
        )
        
        await manager.configure(config)
        
        assert len(manager._configs) == 1
        assert "test_server" in manager._configs

    @pytest.mark.asyncio
    async def test_list_servers(self):
        """Test listing servers."""
        from app.mcp.server_manager import MCPServerManager
        
        manager = MCPServerManager()
        
        # Manually add server info
        manager._server_info["server1"] = MCPServerInfo(
            name="server1",
            status=ServerStatus.RUNNING,
            transport=TransportType.STDIO,
            tools_count=5,
        )
        
        servers = manager.list_servers()
        
        assert len(servers) == 1
        assert servers[0].name == "server1"

    @pytest.mark.asyncio
    async def test_get_registered_tools(self):
        """Test getting registered tools."""
        from app.mcp.server_manager import MCPServerManager
        
        manager = MCPServerManager()
        
        # Register a tool directly
        tool = MCPTool(
            name="test_tool",
            description="Test",
            server_name="test_server",
            input_schema={},
            parameters=[],
        )
        
        async def handler(**kwargs):
            return {}
        
        await manager.registry.register_tool(tool, handler)
        
        tools = manager.get_registered_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "test_tool"


class TestMCPIntegration:
    """Integration tests for MCP."""

    def test_get_mcp_registry_singleton(self):
        """Test singleton pattern for registry."""
        from app.mcp.registry import get_mcp_registry
        
        registry1 = get_mcp_registry()
        registry2 = get_mcp_registry()
        
        assert registry1 is registry2

    def test_get_mcp_manager_singleton(self):
        """Test singleton pattern for manager."""
        from app.mcp.server_manager import get_mcp_manager
        
        manager1 = get_mcp_manager()
        manager2 = get_mcp_manager()
        
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_registry_integration(self):
        """Test full registry workflow."""
        from app.mcp.registry import MCPRegistry
        
        registry = MCPRegistry()
        
        # Register multiple tools
        for i in range(3):
            tool = MCPTool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                server_name="test_server",
                input_schema={},
                parameters=[],
            )
            
            async def handler(**kwargs):
                return {"index": i}
            
            await registry.register_tool(tool, handler)
        
        assert registry.count_tools() == 3
        assert len(registry.get_servers()) == 1
        
        # Invoke each tool
        for i in range(3):
            result = await registry.invoke_tool(
                MCPToolInvocation(tool_name=f"tool_{i}", arguments={})
            )
            assert result.success is True
            assert result.result["index"] == i
        
        # Cleanup
        await registry.unregister_server_tools("test_server")
        assert registry.count_tools() == 0
