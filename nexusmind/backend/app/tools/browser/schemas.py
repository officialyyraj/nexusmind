"""Browser automation schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BrowserType(str, Enum):
    """Supported browser types."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserState(str, Enum):
    """Browser session state."""

    IDLE = "idle"
    LAUNCHING = "launching"
    RUNNING = "running"
    CLOSED = "closed"


class BrowserConfig(BaseModel):
    """Browser configuration."""

    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str | None = None
    proxy: str | None = None
    timeout: int = 30000  # milliseconds
    ignore_https_errors: bool = False


class BrowserSession(BaseModel):
    """Browser session info."""

    session_id: str
    browser_type: BrowserType
    state: BrowserState
    created_at: datetime
    pages_opened: int = 0
    url: str | None = None


class PageInfo(BaseModel):
    """Information about a page."""

    page_id: str
    url: str
    title: str
    viewport_size: dict[str, int]
    loaded: bool = True


class ClickOptions(BaseModel):
    """Options for click action."""

    button: str = "left"
    click_count: int = 1
    delay: int = 0
    position_x: int | None = None
    position_y: int | None = None


class FillOptions(BaseModel):
    """Options for fill action."""

    delay: int = 0
    force: bool = False


class LoginCredentials(BaseModel):
    """Login credentials for form submission."""

    username: str
    password: str
    username_selector: str | None = None
    password_selector: str | None = None
    submit_selector: str | None = None
    login_url: str | None = None


class ScreenshotOptions(BaseModel):
    """Options for screenshot."""

    full_page: bool = False
    path: str | None = None
    type: str = "png"  # png, jpeg
    quality: int | None = None


class JavaScriptResult(BaseModel):
    """Result of JavaScript execution."""

    result: Any
    error: str | None = None


class ConsoleEntry(BaseModel):
    """Browser console log entry."""

    type: str  # log, info, warning, error
    text: str
    location: dict[str, str]
    timestamp: datetime


class DownloadInfo(BaseModel):
    """Download information."""

    url: str
    suggested_filename: str | None
    mime_type: str | None
    total_bytes: int | None


class PageContent(BaseModel):
    """Extracted page content."""

    url: str
    title: str
    html: str | None
    text: str
    elements_count: int
    images_count: int
    links_count: int
    scripts_count: int


class BrowserAction(BaseModel):
    """Browser action request."""

    session_id: str
    action: str  # navigate, click, fill, screenshot, etc.
    selector: str | None = None
    value: Any = None
    options: dict[str, Any] = Field(default_factory=dict)


class BrowserResult(BaseModel):
    """Browser action result."""

    success: bool
    session_id: str
    action: str
    data: Any = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
