"""Tests for browser automation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.tools.browser.schemas import (
    BrowserConfig,
    BrowserSession,
    BrowserState,
    BrowserType,
    ClickOptions,
    ConsoleEntry,
    FillOptions,
    JavaScriptResult,
    LoginCredentials,
    PageContent,
    PageInfo,
    ScreenshotOptions,
)


class TestBrowserSchemas:
    """Test browser schemas."""

    def test_browser_config_defaults(self):
        """Test BrowserConfig defaults."""
        config = BrowserConfig()
        assert config.browser_type == BrowserType.CHROMIUM
        assert config.headless is True
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert config.timeout == 30000

    def test_browser_config_custom(self):
        """Test BrowserConfig with custom values."""
        config = BrowserConfig(
            browser_type=BrowserType.FIREFOX,
            headless=False,
            viewport_width=1280,
            viewport_height=720,
            user_agent="Custom Agent",
        )
        assert config.browser_type == BrowserType.FIREFOX
        assert config.headless is False
        assert config.viewport_width == 1280
        assert config.user_agent == "Custom Agent"

    def test_browser_session(self):
        """Test BrowserSession."""
        from datetime import datetime
        session = BrowserSession(
            session_id="test-123",
            browser_type=BrowserType.CHROMIUM,
            state=BrowserState.RUNNING,
            created_at=datetime.utcnow(),
        )
        assert session.session_id == "test-123"
        assert session.state == BrowserState.RUNNING

    def test_page_info(self):
        """Test PageInfo."""
        info = PageInfo(
            page_id="page-1",
            url="https://example.com",
            title="Example",
            viewport_size={"width": 1920, "height": 1080},
        )
        assert info.url == "https://example.com"
        assert info.loaded is True

    def test_click_options(self):
        """Test ClickOptions."""
        options = ClickOptions(
            button="right",
            click_count=2,
            delay=100,
        )
        assert options.button == "right"
        assert options.click_count == 2

    def test_fill_options(self):
        """Test FillOptions."""
        options = FillOptions(delay=50, force=True)
        assert options.delay == 50
        assert options.force is True

    def test_login_credentials(self):
        """Test LoginCredentials."""
        creds = LoginCredentials(
            username="user@example.com",
            password="secret",
            login_url="https://example.com/login",
        )
        assert creds.username == "user@example.com"
        assert creds.username_selector is None

    def test_screenshot_options(self):
        """Test ScreenshotOptions."""
        opts = ScreenshotOptions(full_page=True, type="jpeg", quality=90)
        assert opts.full_page is True
        assert opts.type == "jpeg"
        assert opts.quality == 90

    def test_console_entry(self):
        """Test ConsoleEntry."""
        from datetime import datetime
        entry = ConsoleEntry(
            type="error",
            text="Something went wrong",
            location={"url": "https://example.com", "line": "10"},
            timestamp=datetime.utcnow(),
        )
        assert entry.type == "error"
        assert "wrong" in entry.text

    def test_javascript_result(self):
        """Test JavaScriptResult."""
        result = JavaScriptResult(result={"key": "value"})
        assert result.result["key"] == "value"
        assert result.error is None

        error_result = JavaScriptResult(result=None, error="Syntax error")
        assert error_result.error == "Syntax error"

    def test_page_content(self):
        """Test PageContent."""
        content = PageContent(
            url="https://example.com",
            title="Example",
            html="<html><body>Hello</body></html>",
            text="Hello",
            elements_count=5,
            images_count=2,
            links_count=3,
            scripts_count=1,
        )
        assert content.url == "https://example.com"
        assert content.elements_count == 5
        assert content.images_count == 2


class TestBrowserState:
    """Test browser state enum."""

    def test_state_values(self):
        """Test state enum values."""
        assert BrowserState.IDLE.value == "idle"
        assert BrowserState.LAUNCHING.value == "launching"
        assert BrowserState.RUNNING.value == "running"
        assert BrowserState.CLOSED.value == "closed"


class TestBrowserType:
    """Test browser type enum."""

    def test_type_values(self):
        """Test type enum values."""
        assert BrowserType.CHROMIUM.value == "chromium"
        assert BrowserType.FIREFOX.value == "firefox"
        assert BrowserType.WEBKIT.value == "webkit"


class TestBrowserTool:
    """Test BrowserTool functionality."""

    def test_tool_import(self):
        """Test that BrowserTool can be imported."""
        from app.tools.browser import BrowserTool, get_browser_tool
        assert BrowserTool is not None
        assert get_browser_tool is not None

    def test_tool_creation(self):
        """Test BrowserTool creation."""
        from app.tools.browser import BrowserTool
        tool = BrowserTool(download_path="/tmp/test")
        assert tool._sessions == {}
        assert tool._download_path == "/tmp/test"

    def test_get_browser_tool_singleton(self):
        """Test singleton pattern."""
        from app.tools.browser import get_browser_tool
        
        tool1 = get_browser_tool()
        tool2 = get_browser_tool()
        assert tool1 is tool2


class TestBrowserIntegration:
    """Integration tests for browser tool (requires Playwright)."""

    @pytest.mark.asyncio
    async def test_launch_browser(self):
        """Test launching a browser."""
        from app.tools.browser import BrowserTool, BrowserConfig, BrowserState
        
        tool = BrowserTool()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            assert session.session_id is not None
            assert session.state == BrowserState.RUNNING
            assert len(tool._sessions) == 1
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_open_page(self):
        """Test opening a page."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            page_info = await tool.open_page(session.session_id, "https://example.com")
            assert page_info.url == "https://example.com"
            assert page_info.title is not None
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_screenshot(self):
        """Test taking a screenshot."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            await tool.open_page(session.session_id, "https://example.com")
            
            result = await tool.screenshot(session.session_id)
            assert result.success is True
            assert "image" in result.data
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_extract_content(self):
        """Test extracting page content."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            await tool.open_page(session.session_id, "https://example.com")
            
            content = await tool.extract_content(session.session_id)
            assert content.url == "https://example.com"
            assert content.html is not None
            assert content.text is not None
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_javascript_execution(self):
        """Test JavaScript execution."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            await tool.open_page(session.session_id, "https://example.com")
            
            result = await tool.execute_javascript(session.session_id, "document.title")
            assert result.error is None
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing a session."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        await tool.start()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            assert len(tool._sessions) == 1
            
            result = await tool.close_session(session.session_id)
            assert result is True
            assert len(tool._sessions) == 0
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_console_logs(self):
        """Test collecting console logs."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        try:
            session = await tool.launch_browser(BrowserConfig(headless=True))
            await tool.open_page(session.session_id, "https://example.com")
            
            # Execute JS that logs to console
            await tool.execute_javascript(session.session_id, "console.log('test message')")
            
            # Give a moment for logs to be collected
            import asyncio
            await asyncio.sleep(0.1)
            
            logs = await tool.get_console_logs(session.session_id)
            assert isinstance(logs, list)
        finally:
            await tool.stop()

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """Test listing sessions."""
        from app.tools.browser import BrowserTool, BrowserConfig
        
        tool = BrowserTool()
        try:
            session1 = await tool.launch_browser(BrowserConfig(headless=True))
            session2 = await tool.launch_browser(BrowserConfig(headless=True))
            
            sessions = tool.list_sessions()
            assert len(sessions) == 2
        finally:
            await tool.stop()
