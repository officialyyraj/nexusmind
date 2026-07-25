"""Browser automation REST API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.tools.browser import (
    BrowserConfig,
    BrowserResult,
    BrowserSession,
    BrowserTool,
    BrowserType,
    ClickOptions,
    ConsoleEntry,
    FillOptions,
    get_browser_tool,
    JavaScriptResult,
    LoginCredentials,
    PageContent,
    PageInfo,
    ScreenshotOptions,
)

router = APIRouter(prefix="/api/v1/browser", tags=["browser"])


def get_tool() -> BrowserTool:
    """Get browser tool instance."""
    return get_browser_tool()


@router.post("/sessions", response_model=BrowserSession)
async def launch_browser(config: BrowserConfig | None = None) -> BrowserSession:
    """Launch a new browser session."""
    tool = get_tool()
    return await tool.launch_browser(config)


@router.get("/sessions")
async def list_sessions() -> list[BrowserSession]:
    """List all active browser sessions."""
    tool = get_tool()
    return tool.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> BrowserSession:
    """Get information about a session."""
    tool = get_tool()
    session = tool.get_session_info(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def close_session(session_id: str) -> dict[str, bool]:
    """Close a browser session."""
    tool = get_tool()
    result = await tool.close_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"closed": True}


@router.post("/sessions/{session_id}/pages", response_model=PageInfo)
async def open_page(session_id: str, url: str) -> PageInfo:
    """Open a new page in the browser."""
    tool = get_tool()
    return await tool.open_page(session_id, url)


@router.post("/sessions/{session_id}/click")
async def click_element(
    session_id: str,
    selector: str,
    options: ClickOptions | None = None,
) -> BrowserResult:
    """Click an element on the page."""
    tool = get_tool()
    return await tool.click(session_id, selector, options)


@router.post("/sessions/{session_id}/fill")
async def fill_element(
    session_id: str,
    selector: str,
    value: str,
    options: FillOptions | None = None,
) -> BrowserResult:
    """Fill an input field."""
    tool = get_tool()
    return await tool.fill(session_id, selector, value, options)


@router.post("/sessions/{session_id}/login")
async def login(session_id: str, credentials: LoginCredentials) -> BrowserResult:
    """Perform login on the page."""
    tool = get_tool()
    return await tool.login(session_id, credentials)


@router.post("/sessions/{session_id}/screenshot")
async def take_screenshot(
    session_id: str,
    options: ScreenshotOptions | None = None,
) -> BrowserResult:
    """Take a screenshot of the page."""
    tool = get_tool()
    return await tool.screenshot(session_id, options)


@router.post("/sessions/{session_id}/download")
async def download_file(
    session_id: str,
    url: str,
    filename: str | None = None,
) -> BrowserResult:
    """Trigger a file download."""
    tool = get_tool()
    return await tool.download_file(session_id, url, filename)


@router.post("/sessions/{session_id}/upload")
async def upload_file(
    session_id: str,
    selector: str,
    file_path: str,
) -> BrowserResult:
    """Upload a file to the page."""
    tool = get_tool()
    return await tool.upload_file(session_id, selector, file_path)


@router.post("/sessions/{session_id}/execute")
async def execute_javascript(
    session_id: str,
    script: str,
) -> JavaScriptResult:
    """Execute JavaScript on the page."""
    tool = get_tool()
    return await tool.execute_javascript(session_id, script)


@router.get("/sessions/{session_id}/content")
async def extract_content(
    session_id: str,
    selector: str | None = None,
) -> PageContent:
    """Extract content from the page."""
    tool = get_tool()
    return await tool.extract_content(session_id, selector)


@router.get("/sessions/{session_id}/console")
async def get_console_logs(session_id: str) -> list[ConsoleEntry]:
    """Get browser console logs."""
    tool = get_tool()
    return await tool.get_console_logs(session_id)


@router.delete("/sessions/{session_id}/console")
async def clear_console_logs(session_id: str) -> dict[str, bool]:
    """Clear browser console logs."""
    tool = get_tool()
    await tool.clear_console_logs(session_id)
    return {"cleared": True}


@router.post("/sessions/{session_id}/navigate")
async def navigate(
    session_id: str,
    url: str,
    wait_until: str = "load",
) -> BrowserResult:
    """Navigate to a URL."""
    tool = get_tool()
    try:
        page_info = await tool.open_page(session_id, url)
        return BrowserResult(
            success=True,
            session_id=session_id,
            action="navigate",
            data={"url": page_info.url, "title": page_info.title},
        )
    except Exception as e:
        return BrowserResult(
            success=False,
            session_id=session_id,
            action="navigate",
            error=str(e),
        )


@router.get("/sessions/{session_id}/html")
async def get_html(session_id: str) -> dict[str, str]:
    """Get the full HTML of the page."""
    tool = get_tool()
    content = await tool.extract_content(session_id)
    return {"html": content.html or ""}


@router.get("/sessions/{session_id}/screenshot")
async def get_screenshot_base64(
    session_id: str,
    full_page: bool = False,
) -> dict[str, str]:
    """Get screenshot as base64."""
    tool = get_tool()
    result = await tool.screenshot(session_id, ScreenshotOptions(full_page=full_page))
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return {"image": result.data["image"]}
