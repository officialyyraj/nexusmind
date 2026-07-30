"""Hostile Verification Tests - Testing failure scenarios and recovery.

These tests verify graceful handling of:
- Missing tools
- Tool timeouts
- Browser failures
- Sandbox failures
- Memory unavailable
- MCP unavailable
- Permission denied
- Multiple tool chains
"""

import asyncio
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.execution_engine import (
    AgentToolInvoker,
    ToolCall,
    ToolCallStatus,
    ToolExecutionContext,
    ToolResult,
    ToolType,
    get_tool_invoker,
)
from app.agents.reasoning_loop import (
    ReasoningLoop,
    ReasoningTrace,
    LoopState,
    ToolSelector,
)
from app.tools.registry import BaseTool, ToolHealth, ToolRegistry


# ==================== Missing Tool Tests ====================

class TestMissingTool:
    """Tests for missing tool handling."""
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker with empty registry."""
        registry = ToolRegistry()
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_missing_native_tool(self, invoker, context):
        """Test graceful handling of missing native tool."""
        tool_call = ToolCall.create(
            tool_name="nonexistent_tool",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "not found" in result.error.lower()
        assert not result.is_success()
    
    @pytest.mark.asyncio
    async def test_missing_function_tool(self, invoker, context):
        """Test graceful handling of missing function tool."""
        tool_call = ToolCall.create(
            tool_name="nonexistent_function",
            tool_type=ToolType.FUNCTION,
            arguments={},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_missing_mcp_tool(self, invoker, context):
        """Test graceful handling of missing MCP tool."""
        tool_call = ToolCall.create(
            tool_name="nonexistent_mcp_tool",
            tool_type=ToolType.MCP,
            arguments={},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED


# ==================== Tool Timeout Tests ====================

class TestToolTimeout:
    """Tests for tool timeout handling."""
    
    class SlowTool(BaseTool):
        """A tool that takes a long time."""
        
        def __init__(self):
            super().__init__("slow_tool", "A slow tool")
        
        async def execute(self, **kwargs) -> dict:
            await asyncio.sleep(100)  # Very slow
            return {"result": "done"}
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker."""
        registry = ToolRegistry()
        registry.register(SlowTool())
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_tool_timeout(self, invoker, context):
        """Test timeout handling for slow tools."""
        tool_call = ToolCall.create(
            tool_name="slow_tool",
            tool_type=ToolType.NATIVE,
            arguments={},
            timeout=0.5,  # Very short timeout
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.TIMEOUT
        assert "timed out" in result.error.lower()


# ==================== Tool Exception Tests ====================

class TestToolException:
    """Tests for tool exception handling."""
    
    class FailingTool(BaseTool):
        """A tool that raises exceptions."""
        
        def __init__(self):
            super().__init__("failing_tool", "A failing tool")
        
        async def execute(self, **kwargs) -> dict:
            raise ValueError("Intentional test error")
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker."""
        registry = ToolRegistry()
        registry.register(FailingTool())
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_tool_exception_handling(self, invoker, context):
        """Test exception handling in tool execution."""
        tool_call = ToolCall.create(
            tool_name="failing_tool",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "ValueError" in result.error
        assert "Intentional test error" in result.error


# ==================== Unhealthy Tool Tests ====================

class TestUnhealthyTool:
    """Tests for unhealthy tool handling."""
    
    class UnhealthyTool(BaseTool):
        """A tool that reports unhealthy status."""
        
        def __init__(self):
            super().__init__("unhealthy_tool", "An unhealthy tool")
            self._health = ToolHealth.UNHEALTHY
        
        async def execute(self, **kwargs) -> dict:
            return {"result": "done"}
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker."""
        registry = ToolRegistry()
        registry.register(UnhealthyTool())
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_unhealthy_tool(self, invoker, context):
        """Test handling of unhealthy tools."""
        tool_call = ToolCall.create(
            tool_name="unhealthy_tool",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "unhealthy" in result.error.lower()


# ==================== Permission Denied Tests ====================

class TestPermissionDenied:
    """Tests for permission denial handling."""
    
    class RestrictedTool(BaseTool):
        """A tool with restricted access."""
        
        def __init__(self):
            super().__init__("restricted_tool", "A restricted tool")
        
        async def execute(self, **kwargs) -> dict:
            return {"result": "done"}
        
        async def can_execute(self, **kwargs) -> bool:
            return False  # Always denied
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker."""
        registry = ToolRegistry()
        registry.register(RestrictedTool())
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_permission_denied(self, invoker, context):
        """Test handling of permission denied."""
        tool_call = ToolCall.create(
            tool_name="restricted_tool",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "cannot execute" in result.error.lower()


# ==================== Multiple Tool Chain Tests ====================

class TestMultipleToolChain:
    """Tests for chained tool execution."""
    
    class ChainTool(BaseTool):
        """A tool that chains to another."""
        
        def __init__(self, name: str, chain_to: str | None = None):
            super().__init__(name, f"Tool that chains to {chain_to or 'none'}")
            self.chain_to = chain_to
            self.call_count = 0
        
        async def execute(self, **kwargs) -> dict:
            self.call_count += 1
            return {
                "tool": self.name,
                "call_count": self.call_count,
                "chain_to": self.chain_to,
            }
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker with chain tools."""
        registry = ToolRegistry()
        registry.register(ChainTool("tool_a"))
        registry.register(ChainTool("tool_b", "tool_a"))
        registry.register(ChainTool("tool_c", "tool_b"))
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            max_total_tools=100,
        )
    
    @pytest.mark.asyncio
    async def test_tool_chain_execution(self, invoker, context):
        """Test successful execution of tool chain."""
        # Execute first tool
        call1 = ToolCall.create(
            tool_name="tool_a",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        result1 = await invoker.invoke(call1, context)
        
        # Execute second tool (depends on first)
        call2 = ToolCall.create(
            tool_name="tool_b",
            tool_type=ToolType.NATIVE,
            arguments={"depends_on": result1.result},
        )
        result2 = await invoker.invoke(call2, context)
        
        # Execute third tool
        call3 = ToolCall.create(
            tool_name="tool_c",
            tool_type=ToolType.NATIVE,
            arguments={"depends_on": result2.result},
        )
        result3 = await invoker.invoke(call3, context)
        
        assert result1.is_success()
        assert result2.is_success()
        assert result3.is_success()
        assert context.tool_count == 3
    
    @pytest.mark.asyncio
    async def test_chain_with_failure(self, invoker, context):
        """Test chain continues even after failure."""
        # Execute first tool
        call1 = ToolCall.create(
            tool_name="tool_a",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        result1 = await invoker.invoke(call1, context)
        
        # Execute missing tool (failure)
        call2 = ToolCall.create(
            tool_name="nonexistent",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        result2 = await invoker.invoke(call2, context)
        
        # Continue chain with tool_c
        call3 = ToolCall.create(
            tool_name="tool_c",
            tool_type=ToolType.NATIVE,
            arguments={"recovered_from": "failure"},
        )
        result3 = await invoker.invoke(call3, context)
        
        assert result1.is_success()
        assert not result2.is_success()
        assert result3.is_success()


# ==================== Max Tools Limit Tests ====================

class TestMaxToolsLimit:
    """Tests for maximum tools per execution limit."""
    
    class SimpleTool(BaseTool):
        """A simple tool."""
        
        def __init__(self, name: str):
            super().__init__(name, "A simple tool")
        
        async def execute(self, **kwargs) -> dict:
            return {"result": f"from {self.name}"}
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker."""
        registry = ToolRegistry()
        registry.register(SimpleTool("simple_tool"))
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.mark.asyncio
    async def test_max_tools_limit(self, invoker):
        """Test that max tools limit is enforced."""
        context = ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            max_total_tools=3,  # Low limit
        )
        
        # Execute 3 tools (should succeed)
        for i in range(3):
            call = ToolCall.create(
                tool_name="simple_tool",
                tool_type=ToolType.NATIVE,
                arguments={"iteration": i},
            )
            result = await invoker.invoke(call, context)
            assert result.is_success()
        
        # Fourth tool should fail (exceeded limit)
        call = ToolCall.create(
            tool_name="simple_tool",
            tool_type=ToolType.NATIVE,
            arguments={"iteration": 3},
        )
        result = await invoker.invoke(call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "exceeded maximum" in result.error.lower()


# ==================== Sandbox Failure Tests ====================

class TestSandboxFailure:
    """Tests for sandbox failure handling."""
    
    class MockFailingSandboxTool(BaseTool):
        """A mock sandbox tool that fails."""
        
        def __init__(self):
            super().__init__("sandbox", "Sandbox tool")
        
        async def execute(self, **kwargs) -> dict:
            action = kwargs.get("action")
            if action == "allocate":
                return {"success": False, "error": "Sandbox pool exhausted"}
            elif action == "execute":
                return {"success": False, "error": "Execution failed"}
            return {"success": False, "error": "Unknown action"}
    
    @pytest.fixture
    def invoker(self):
        """Create tool invoker."""
        registry = ToolRegistry()
        registry.register(MockFailingSandboxTool())
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_sandbox_allocation_failure(self, invoker, context):
        """Test handling of sandbox allocation failure."""
        tool_call = ToolCall.create(
            tool_name="sandbox",
            tool_type=ToolType.NATIVE,
            arguments={"action": "allocate"},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.SUCCESS  # Tool itself succeeded
        # But the result contains the failure
        assert result.result.get("success") == False
        assert "exhausted" in result.result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_sandbox_execution_failure(self, invoker, context):
        """Test handling of sandbox execution failure."""
        tool_call = ToolCall.create(
            tool_name="sandbox",
            tool_type=ToolType.NATIVE,
            arguments={"action": "execute", "code": "print('hello')"},
        )
        
        result = await invoker.invoke(tool_call, context)
        
        assert result.result.get("success") == False
        assert "failed" in result.result.get("error", "").lower()


# ==================== Memory Unavailable Tests ====================

class TestMemoryUnavailable:
    """Tests for memory service unavailability."""
    
    @pytest.mark.asyncio
    async def test_reasoning_loop_memory_failure(self):
        """Test reasoning loop handles memory failure gracefully."""
        # Create mock memory service that fails
        mock_memory = MagicMock()
        mock_memory.semantic_search = AsyncMock(side_effect=Exception("Memory unavailable"))
        mock_memory.store_conversation = AsyncMock(side_effect=Exception("Memory unavailable"))
        
        loop = ReasoningLoop(
            max_iterations=1,
            memory_service=mock_memory,
        )
        
        # Execute should still work even if memory fails
        trace = await loop.execute(
            task="Test task",
            agent_type=MagicMock(value="test"),
            session_id=str(uuid.uuid4()),
        )
        
        # Trace should exist even with memory failure
        assert trace is not None


# ==================== MCP Unavailable Tests ====================

class TestMCPUnavailable:
    """Tests for MCP service unavailability."""
    
    @pytest.fixture
    def invoker_with_mock_mcp(self):
        """Create tool invoker with mock MCP registry."""
        from app.mcp.registry import MCPRegistry
        
        mock_mcp = MagicMock(spec=MCPRegistry)
        mock_mcp.invoke_tool = AsyncMock(side_effect=Exception("MCP server unavailable"))
        mock_mcp.get_tool = MagicMock(return_value=None)
        
        registry = ToolRegistry()
        return AgentToolInvoker(
            tool_registry=registry,
            mcp_registry=mock_mcp,
        )
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_mcp_unavailable(self, invoker_with_mock_mcp, context):
        """Test handling of MCP unavailability."""
        tool_call = ToolCall.create(
            tool_name="mcp_tool",
            tool_type=ToolType.MCP,
            arguments={},
        )
        
        result = await invoker_with_mock_mcp.invoke(tool_call, context)
        
        assert result.status == ToolCallStatus.FAILED
        assert "MCP" in result.error or "unavailable" in result.error.lower()


# ==================== Browser Failure Tests ====================

class TestBrowserFailure:
    """Tests for browser tool failure handling."""
    
    @pytest.fixture
    def invoker_with_mock_browser(self):
        """Create tool invoker with mock browser tool."""
        class MockFailingBrowserTool(BaseTool):
            def __init__(self):
                super().__init__("browser", "Browser tool")
            
            async def execute(self, **kwargs) -> dict:
                action = kwargs.get("action")
                if action == "launch":
                    return {"success": False, "error": "Playwright not available"}
                return {"success": False, "error": f"Unknown action: {action}"}
        
        registry = ToolRegistry()
        registry.register(MockFailingBrowserTool())
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_browser_launch_failure(self, invoker_with_mock_browser, context):
        """Test handling of browser launch failure."""
        tool_call = ToolCall.create(
            tool_name="browser",
            tool_type=ToolType.NATIVE,
            arguments={"action": "launch"},
        )
        
        result = await invoker_with_mock_browser.invoke(tool_call, context)
        
        assert result.result.get("success") == False
        assert "playwright" in result.result.get("error", "").lower()


# ==================== Recovery Verification ====================

class TestRecoveryVerification:
    """Tests verifying recovery capabilities."""
    
    @pytest.fixture
    def recovery_invoker(self):
        """Create tool invoker for recovery tests."""
        registry = ToolRegistry()
        
        class RecoverableTool(BaseTool):
            def __init__(self, fail_count: int = 2):
                super().__init__("recoverable", "A recoverable tool")
                self.fail_count = fail_count
                self.calls = 0
            
            async def execute(self, **kwargs) -> dict:
                self.calls += 1
                if self.calls <= self.fail_count:
                    raise Exception(f"Transient failure {self.calls}")
                return {"result": "success after recovery", "attempts": self.calls}
        
        registry.register(RecoverableTool(fail_count=2))
        return AgentToolInvoker(tool_registry=registry)
    
    @pytest.fixture
    def context(self):
        """Create execution context."""
        return ToolExecutionContext(
            agent_type="test",
            session_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            max_total_tools=10,
        )
    
    @pytest.mark.asyncio
    async def test_execution_trace_after_failure(self, recovery_invoker, context):
        """Test that execution trace captures failures."""
        tool_call = ToolCall.create(
            tool_name="recoverable",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        
        # Execute and capture result
        result = await recovery_invoker.invoke(tool_call, context)
        
        # Verify trace
        trace = recovery_invoker.get_execution_trace(context.execution_id)
        
        assert trace["total_calls"] == 1
        assert len(trace["results"]) == 1
        assert trace["results"][0]["status"] == result.status.value
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, recovery_invoker, context):
        """Test graceful degradation when tools fail."""
        # Execute with a tool that will fail
        tool_call = ToolCall.create(
            tool_name="nonexistent",
            tool_type=ToolType.NATIVE,
            arguments={},
        )
        
        result = await recovery_invoker.invoke(tool_call, context)
        
        # Should return a structured error, not crash
        assert result is not None
        assert result.status == ToolCallStatus.FAILED
        assert result.error is not None
        # Context should still be usable
        assert context.tool_count == 1
