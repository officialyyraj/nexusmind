"""Tool registration for production tools.

This module registers all production tools with the Tool Registry.
"""
from functools import partial
from app.tools.registry import get_tool_registry, BaseTool, ToolHealth
from app.tools.browser.tool import BrowserTool
from app.tools.docker_sandbox_tool import DockerSandboxTool


class BrowserToolWrapper(BaseTool):
    """Wrapper for BrowserTool to conform to BaseTool interface."""

    def __init__(self):
        super().__init__(
            name="browser",
            description="Browser automation tool for web interactions",
        )
        self._browser = BrowserTool()
        self._health = ToolHealth.HEALTHY

    async def health(self) -> ToolHealth:
        """Check browser tool health."""
        try:
            return self._health
        except Exception:
            return ToolHealth.UNHEALTHY

    async def can_execute(self, **kwargs) -> bool:
        """Check if browser can execute."""
        return self._health == ToolHealth.HEALTHY

    async def execute(self, action: str, **kwargs) -> dict:
        """Execute browser action."""
        session_id = kwargs.get("session_id")
        if action == "launch":
            result = await self._browser.launch_browser()
            return {"success": True, "session_id": result.session_id}
        elif action == "open":
            result = await self._browser.open_page(session_id, kwargs.get("url", ""))
            return {"success": True, "url": result.url}
        elif action == "click":
            result = await self._browser.click(session_id, kwargs.get("selector", ""))
            return {"success": result.success, "error": result.error}
        elif action == "fill":
            result = await self._browser.fill(
                session_id,
                kwargs.get("selector", ""),
                kwargs.get("value", ""),
            )
            return {"success": result.success, "error": result.error}
        elif action == "screenshot":
            result = await self._browser.screenshot(session_id)
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
            }
        elif action == "close":
            result = await self._browser.close_session(session_id)
            return {"success": result}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def shutdown(self) -> None:
        """Shutdown browser tool."""
        await self._browser.stop()


def register_tools(docker_sandbox_tool: DockerSandboxTool) -> None:
    """Register all production tools with the Tool Registry."""
    registry = get_tool_registry()

    # Only register if not already registered
    if not registry.has_tool("browser"):
        browser_tool = BrowserToolWrapper()
        registry.register(browser_tool)

    if not registry.has_tool("docker_sandbox"):
        registry.register(docker_sandbox_tool)

    # Register function-based tools
    if not registry.get_function("execute_code"):
        registry.register_function(
            "execute_code",
            partial(_execute_code, docker_sandbox_tool),
            "Execute code in a sandboxed environment",
        )

    if not registry.get_function("web_search"):
        registry.register_function(
            "web_search",
            _web_search,
            "Search the web for information",
        )


async def _execute_code(docker_sandbox_tool: DockerSandboxTool, code: str, language: str = "python", timeout: int = 30) -> dict:
    """Execute code function wrapper."""
    result = await docker_sandbox_tool.execute(
        action="execute",
        code=code,
        language=language,
        timeout=timeout,
    )
    return result


async def _web_search(query: str, provider: str = "duckduckgo") -> dict:
    """Web search function wrapper."""
    try:
        from app.tools.web_search.service import get_search_service
        service = get_search_service()
        result = await service.search(query, provider=provider)
        return {
            "success": True,
            "results": [r.dict() for r in result.results] if hasattr(result, 'results') else [],
            "total": result.total if hasattr(result, 'total') else 0,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

