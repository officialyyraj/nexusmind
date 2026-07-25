"""Browser automation tool using Playwright."""

import asyncio
import base64
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.tools.browser.schemas import (
    BrowserAction,
    BrowserConfig,
    BrowserResult,
    BrowserSession,
    BrowserState,
    BrowserType,
    ClickOptions,
    ConsoleEntry,
    DownloadInfo,
    FillOptions,
    JavaScriptResult,
    LoginCredentials,
    PageContent,
    PageInfo,
    ScreenshotOptions,
)


class BrowserTool:
    """Browser automation tool with Playwright."""

    def __init__(self, download_path: str | None = None):
        self._playwright = None
        self._sessions: dict[str, dict] = {}
        self._download_path = download_path or "/tmp/downloads"
        self._lock = asyncio.Lock()

        # Create download directory
        Path(self._download_path).mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start Playwright."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()

    async def stop(self) -> None:
        """Stop Playwright and close all sessions."""
        async with self._lock:
            for session_id in list(self._sessions.keys()):
                await self.close_session(session_id)

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

    async def launch_browser(
        self,
        config: BrowserConfig | None = None,
    ) -> BrowserSession:
        """Launch a new browser session.
        
        Args:
            config: Browser configuration
            
        Returns:
            Browser session info
        """
        await self.start()
        config = config or BrowserConfig()

        session_id = str(uuid.uuid4())

        # Launch browser
        browser_type = config.browser_type.value
        browser = await getattr(self._playwright, browser_type).launch(
            headless=config.headless,
            proxy=config.proxy,
        )

        # Create context
        context = await browser.new_context(
            viewport={"width": config.viewport_width, "height": config.viewport_height},
            user_agent=config.user_agent,
            ignore_https_errors=config.ignore_https_errors,
        )

        # Track session
        self._sessions[session_id] = {
            "browser": browser,
            "context": context,
            "page": None,
            "config": config,
            "state": BrowserState.RUNNING,
            "created_at": datetime.utcnow(),
            "console_logs": [],
            "downloads": [],
        }

        return BrowserSession(
            session_id=session_id,
            browser_type=config.browser_type,
            state=BrowserState.RUNNING,
            created_at=datetime.utcnow(),
        )

    async def close_session(self, session_id: str) -> bool:
        """Close a browser session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session was closed
        """
        async with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]

            if session["page"]:
                await session["page"].close()

            await session["context"].close()
            await session["browser"].close()

            del self._sessions[session_id]
            return True

    async def open_page(self, session_id: str, url: str) -> PageInfo:
        """Open a new page in the browser.
        
        Args:
            session_id: Session ID
            url: URL to open
            
        Returns:
            Page info
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Close existing page
        if session["page"]:
            await session["page"].close()

        # Create new page
        page = await session["context"].new_page()

        # Listen to console
        page.on("console", lambda msg: self._handle_console(session_id, msg))

        # Listen to downloads
        page.on("download", lambda download: self._handle_download(session_id, download))

        # Navigate
        await page.goto(url, timeout=session["config"].timeout)

        session["page"] = page

        return PageInfo(
            page_id=str(uuid.uuid4()),
            url=page.url,
            title=await page.title(),
            viewport_size={"width": session["config"].viewport_width, "height": session["config"].viewport_height},
            loaded=True,
        )

    def _get_session(self, session_id: str) -> dict | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def _handle_console(self, session_id: str, msg) -> None:
        """Handle browser console message."""
        if session_id in self._sessions:
            self._sessions[session_id]["console_logs"].append({
                "type": msg.type,
                "text": msg.text,
                "location": {"url": msg.location.get("url", ""), "line": str(msg.location.get("lineNumber", 0))},
                "timestamp": datetime.utcnow().isoformat(),
            })

    async def _handle_download(self, session_id: str, download) -> None:
        """Handle download."""
        if session_id in self._sessions:
            path = await download.path()
            self._sessions[session_id]["downloads"].append({
                "url": download.url,
                "suggested_filename": download.suggested_filename,
                "path": str(path),
            })

    async def click(
        self,
        session_id: str,
        selector: str,
        options: ClickOptions | None = None,
    ) -> BrowserResult:
        """Click an element.
        
        Args:
            session_id: Session ID
            selector: Element selector
            options: Click options
            
        Returns:
            Action result
        """
        options = options or ClickOptions()
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return BrowserResult(success=False, session_id=session_id, action="click", error="No active page")

        try:
            await session["page"].click(
                selector,
                button=options.button,
                click_count=options.click_count,
                delay=options.delay,
                position=(options.position_x, options.position_y) if options.position_x else None,
            )
            return BrowserResult(success=True, session_id=session_id, action="click", data={"selector": selector})
        except Exception as e:
            return BrowserResult(success=False, session_id=session_id, action="click", error=str(e))

    async def fill(
        self,
        session_id: str,
        selector: str,
        value: str,
        options: FillOptions | None = None,
    ) -> BrowserResult:
        """Fill an input field.
        
        Args:
            session_id: Session ID
            selector: Element selector
            value: Value to fill
            options: Fill options
            
        Returns:
            Action result
        """
        options = options or FillOptions()
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return BrowserResult(success=False, session_id=session_id, action="fill", error="No active page")

        try:
            await session["page"].fill(selector, value, delay=options.delay, force=options.force)
            return BrowserResult(success=True, session_id=session_id, action="fill", data={"selector": selector, "value": value})
        except Exception as e:
            return BrowserResult(success=False, session_id=session_id, action="fill", error=str(e))

    async def login(
        self,
        session_id: str,
        credentials: LoginCredentials,
    ) -> BrowserResult:
        """Perform login on a page.
        
        Args:
            session_id: Session ID
            credentials: Login credentials
            
        Returns:
            Action result
        """
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return BrowserResult(success=False, session_id=session_id, action="login", error="No active page")

        try:
            page = session["page"]

            # Navigate to login page if needed
            if credentials.login_url:
                await page.goto(credentials.login_url)

            # Default selectors
            username_selector = credentials.username_selector or 'input[name="username"], input[type="email"], input[id="email"]'
            password_selector = credentials.password_selector or 'input[name="password"], input[type="password"]'
            submit_selector = credentials.submit_selector or 'button[type="submit"], input[type="submit"]'

            # Fill credentials
            await page.fill(username_selector, credentials.username)
            await page.fill(password_selector, credentials.password)

            # Submit
            await page.click(submit_selector)

            return BrowserResult(
                success=True,
                session_id=session_id,
                action="login",
                data={"username": credentials.username, "logged_in": True},
            )
        except Exception as e:
            return BrowserResult(success=False, session_id=session_id, action="login", error=str(e))

    async def screenshot(
        self,
        session_id: str,
        options: ScreenshotOptions | None = None,
    ) -> BrowserResult:
        """Take a screenshot.
        
        Args:
            session_id: Session ID
            options: Screenshot options
            
        Returns:
            Action result with base64 image
        """
        options = options or ScreenshotOptions()
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return BrowserResult(success=False, session_id=session_id, action="screenshot", error="No active page")

        try:
            page = session["page"]

            # Take screenshot
            image_bytes = await page.screenshot(
                full_page=options.full_page,
                path=options.path,
                type=options.type,
                quality=options.quality,
            )

            # Encode to base64
            image_base64 = base64.b64encode(image_bytes).decode()

            return BrowserResult(
                success=True,
                session_id=session_id,
                action="screenshot",
                data={"image": image_base64, "format": options.type},
            )
        except Exception as e:
            return BrowserResult(success=False, session_id=session_id, action="screenshot", error=str(e))

    async def download_file(
        self,
        session_id: str,
        url: str,
        filename: str | None = None,
    ) -> BrowserResult:
        """Trigger a file download.
        
        Args:
            session_id: Session ID
            url: File URL
            filename: Optional filename
            
        Returns:
            Action result with download info
        """
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return BrowserResult(success=False, session_id=session_id, action="download", error="No active page")

        try:
            # Navigate to trigger download or use page context
            async with session["page"].expect_download() as download_info:
                await session["page"].evaluate(f"window.open('{url}', '_blank')")

            download = await download_info.value
            path = await download.path()

            # Move to download directory
            dest_path = Path(self._download_path) / (filename or download.suggested_filename)
            if path:
                Path(path).rename(dest_path)

            return BrowserResult(
                success=True,
                session_id=session_id,
                action="download",
                data={"path": str(dest_path), "filename": filename or download.suggested_filename},
            )
        except Exception as e:
            return BrowserResult(success=False, session_id=session_id, action="download", error=str(e))

    async def upload_file(
        self,
        session_id: str,
        selector: str,
        file_path: str,
    ) -> BrowserResult:
        """Upload a file to an input element.
        
        Args:
            session_id: Session ID
            selector: File input selector
            file_path: Path to file
            
        Returns:
            Action result
        """
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return BrowserResult(success=False, session_id=session_id, action="upload", error="No active page")

        try:
            await session["page"].set_input_files(selector, file_path)
            return BrowserResult(
                success=True,
                session_id=session_id,
                action="upload",
                data={"selector": selector, "file_path": file_path},
            )
        except Exception as e:
            return BrowserResult(success=False, session_id=session_id, action="upload", error=str(e))

    async def execute_javascript(
        self,
        session_id: str,
        script: str,
    ) -> JavaScriptResult:
        """Execute JavaScript in the page.
        
        Args:
            session_id: Session ID
            script: JavaScript code
            
        Returns:
            Execution result
        """
        session = self._get_session(session_id)
        if not session or not session["page"]:
            return JavaScriptResult(result=None, error="No active page")

        try:
            result = await session["page"].evaluate(script)
            return JavaScriptResult(result=result)
        except Exception as e:
            return JavaScriptResult(result=None, error=str(e))

    async def extract_content(
        self,
        session_id: str,
        selector: str | None = None,
    ) -> PageContent:
        """Extract page content.
        
        Args:
            session_id: Session ID
            selector: Optional element selector
            
        Returns:
            Extracted content
        """
        session = self._get_session(session_id)
        if not session or not session["page"]:
            raise ValueError(f"No active page for session: {session_id}")

        page = session["page"]

        if selector:
            # Extract from specific element
            element = await page.query_selector(selector)
            if not element:
                raise ValueError(f"Element not found: {selector}")

            html = await element.inner_html()
            text = await element.inner_text()
            elements_count = len(await element.query_selector_all("*"))
        else:
            # Extract entire page
            html = await page.content()
            text = await page.inner_text("body")
            elements_count = len(await page.query_selector_all("*"))

        # Count elements
        images_count = len(await page.query_selector_all("img"))
        links_count = len(await page.query_selector_all("a"))
        scripts_count = len(await page.query_selector_all("script"))

        return PageContent(
            url=page.url,
            title=await page.title(),
            html=html,
            text=text,
            elements_count=elements_count,
            images_count=images_count,
            links_count=links_count,
            scripts_count=scripts_count,
        )

    async def get_console_logs(self, session_id: str) -> list[ConsoleEntry]:
        """Get browser console logs.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of console entries
        """
        if session_id not in self._sessions:
            return []

        logs = self._sessions[session_id]["console_logs"]
        return [
            ConsoleEntry(
                type=log["type"],
                text=log["text"],
                location=log["location"],
                timestamp=datetime.fromisoformat(log["timestamp"]),
            )
            for log in logs
        ]

    async def clear_console_logs(self, session_id: str) -> None:
        """Clear console logs for a session.
        
        Args:
            session_id: Session ID
        """
        if session_id in self._sessions:
            self._sessions[session_id]["console_logs"] = []

    def get_session_info(self, session_id: str) -> BrowserSession | None:
        """Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session info or None
        """
        session = self._get_session(session_id)
        if not session:
            return None

        return BrowserSession(
            session_id=session_id,
            browser_type=session["config"].browser_type,
            state=session["state"],
            created_at=session["created_at"],
            url=session["page"].url if session["page"] else None,
        )

    def list_sessions(self) -> list[BrowserSession]:
        """List all active sessions.
        
        Returns:
            List of sessions
        """
        return [
            self.get_session_info(session_id)
            for session_id in self._sessions
        ]


# Global instance
_browser_tool: BrowserTool | None = None


def get_browser_tool() -> BrowserTool:
    """Get the global browser tool instance.
    
    Returns:
        BrowserTool instance
    """
    global _browser_tool
    if _browser_tool is None:
        _browser_tool = BrowserTool()
    return _browser_tool
