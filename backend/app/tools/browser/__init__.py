"""Browser automation tool module."""

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
from app.tools.browser.tool import BrowserTool, get_browser_tool

__all__ = [
    "BrowserTool",
    "get_browser_tool",
    "BrowserConfig",
    "BrowserSession",
    "BrowserState",
    "BrowserType",
    "BrowserAction",
    "BrowserResult",
    "PageInfo",
    "PageContent",
    "ClickOptions",
    "FillOptions",
    "LoginCredentials",
    "ScreenshotOptions",
    "JavaScriptResult",
    "ConsoleEntry",
    "DownloadInfo",
]
