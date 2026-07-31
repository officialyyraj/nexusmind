"""Main FastAPI application for NexusMind."""

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.agents import router as agents_router
from app.api.v1.memory import router as memory_router
from app.api.v1.plugins import router as plugins_router
from app.api.v1.mcp import router as mcp_router
from app.api.v1.sandbox import router as sandbox_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.executions import router as executions_router
from app.api.v1.providers import router as providers_router
from app.auth.routes import router as auth_router
from app.api.ws import router as ws_router
from app.tools.browser.api import router as browser_router
from app.monitoring.routes import router as monitoring_router
from app.security.middleware import setup_security_middleware
from app.security.routes import router as security_router
from app.config import get_settings
from app.utils.logger import get_logger, set_request_id, setup_logging, generate_request_id
from app.monitoring.metrics import get_metrics_service
from app.monitoring.telemetry import get_telemetry_service

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Initialize telemetry
telemetry = get_telemetry_service()

# Global flag for startup status
_startup_complete = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _startup_complete
    settings = get_settings()
    
    # Run deployment gate validation in production
    if settings.is_production:
        from app.security.deployment_gate import run_deployment_gate, StartupError
        try:
            report = run_deployment_gate(settings, raise_on_failure=True)
            logger.info("Deployment gate passed")
            for check in report.checks:
                if check.passed:
                    logger.debug(f"  ✓ {check.name}")
                else:
                    logger.warning(f"  ✗ {check.name}: {check.message}")
        except StartupError as e:
            logger.critical("Deployment gate FAILED:")
            for failure in e.report.critical_failures:
                logger.critical(f"  🔴 CRITICAL - {failure.name}: {failure.message}")
                if failure.hint:
                    logger.critical(f"    → {failure.hint}")
            for failure in e.report.high_failures:
                logger.critical(f"  🟠 HIGH - {failure.name}: {failure.message}")
            raise
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Run zero-touch initialization if not already done
    if not _startup_complete:
        try:
            from app.startup import initialize_all, StartupError as InitError
            results = await initialize_all()
            _startup_complete = True
            logger.info("Zero-touch initialization completed successfully")
            for item in results.get("initialized", []):
                logger.info(f"  - {item}: OK")
        except InitError as e:
            logger.error(f"Initialization failed: {e}")
            if e.service:
                logger.error(f"  Service: {e.service}")
            if e.hint:
                logger.error(f"  Hint: {e.hint}")
            raise
        except Exception as e:
            logger.error(f"Unexpected initialization error: {e}")
            raise

    # Initialize MCP servers and sync tools to registry
    try:
        from app.mcp import get_mcp_manager

        manager = get_mcp_manager()

        # Try to load config from default location
        config_path = Path("./config/mcp.yaml")
        if not config_path.exists():
            config_path = Path("/app/config/mcp.yaml")

        if config_path.exists():
            config = await manager.load_config(config_path)
            await manager.initialize(config)
            await manager.start_all()
            logger.info(f"MCP initialized with {len(config.servers)} servers")
        else:
            await manager.initialize()
            logger.info("MCP initialized without servers (no config found)")

        # Sync MCP tools to Tool Registry for agent access
        try:
            from app.tools.mcp_integration import get_mcp_integrator
            integrator = get_mcp_integrator()
            stats = await integrator.sync_tools()
            logger.info(f"MCP tools synced: {stats.get('registered', 0)} registered, {stats.get('unregistered', 0)} removed")
        except Exception as e:
            logger.warning(f"MCP tool sync failed: {e}")

    except Exception as e:
        logger.warning(f"MCP initialization failed: {e}")

    # Initialize tools registry
    try:
        from app.dependencies import get_sandbox_manager, get_docker_sandbox_tool
        from app.tools.registry import get_tool_registry
        from app.tools.registration import register_tools
        
        settings = get_settings()
        sandbox_manager = get_sandbox_manager(settings)
        docker_sandbox_tool = get_docker_sandbox_tool(sandbox_manager)
        
        register_tools(docker_sandbox_tool)

        registry = get_tool_registry()
        tools = registry.list_tools(include_mcp=True)
        logger.info(f"Tool Registry initialized with {len(tools)} tools")
    except Exception as e:
        logger.warning(f"Tool Registry initialization failed: {e}")

    yield

    # Shutdown MCP servers
    try:
        from app.mcp import get_mcp_manager

        manager = get_mcp_manager()
        await manager.shutdown()
        logger.info("MCP shutdown complete")
    except Exception as e:
        logger.warning(f"MCP shutdown failed: {e}")

    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous Multi-Agent AI Platform",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Setup security middleware (must be added after CORS but before routes)
    setup_security_middleware(app)

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any) -> Any:
        """Add request ID to each request for tracing."""
        request_id = request.headers.get("X-Request-ID", generate_request_id())
        set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Add timing middleware
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next: Any) -> Any:
        """Add timing header to response."""
        import time

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Record metrics
        metrics = get_metrics_service()
        metrics.record_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=process_time,
        )

        return response

    # Add metrics middleware for error tracking
    @app.middleware("http")
    async def track_errors(request: Request, call_next: Any) -> Any:
        """Track errors in metrics."""
        try:
            return await call_next(request)
        except Exception as e:
            metrics = get_metrics_service()
            metrics.record_error(
                error_type=type(e).__name__,
                endpoint=request.url.path,
            )
            raise

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routers
    settings = get_settings()
    api_prefix = settings.api_prefix
    app.include_router(auth_router, prefix=f"{api_prefix}/auth")
    app.include_router(security_router, prefix=f"{api_prefix}/security")
    app.include_router(sessions_router, prefix=api_prefix)  # Router has /sessions prefix
    app.include_router(agents_router, prefix=api_prefix)     # Router has /agents prefix
    app.include_router(sandbox_router, prefix=api_prefix)    # Router has /sandbox prefix
    app.include_router(memory_router, prefix=api_prefix)     # Router has /memory prefix
    app.include_router(plugins_router, prefix=api_prefix)    # Router has /plugins prefix
    app.include_router(webhooks_router, prefix=api_prefix)    # Router has /webhooks prefix
    app.include_router(mcp_router, prefix=f"{api_prefix}/mcp")  # Router has no internal prefix
    app.include_router(executions_router)
    app.include_router(providers_router)  # BYOK provider management
    app.include_router(browser_router)

    # Include WebSocket router (no prefix - uses /ws path)
    app.include_router(ws_router)

    # Include monitoring routes (no prefix for /health, /metrics)
    app.include_router(monitoring_router)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root() -> dict[str, Any]:
        """Root endpoint with service info."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs" if settings.is_development else "disabled",
        }

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
            headers=exc.headers if hasattr(exc, "headers") else None,
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle ValueError exceptions."""
        logger.error(f"ValueError: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": str(exc),
                "status_code": 400,
            },
        )

    @app.exception_handler(TypeError)
    async def type_error_handler(
        request: Request, exc: TypeError
    ) -> JSONResponse:
        """Handle TypeError exceptions."""
        logger.error(f"TypeError: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": str(exc),
                "status_code": 400,
            },
        )

    @app.exception_handler(ConnectionError)
    async def connection_error_handler(
        request: Request, exc: ConnectionError
    ) -> JSONResponse:
        """Handle connection errors."""
        logger.error(f"ConnectionError: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service temporarily unavailable",
                "status_code": 503,
            },
        )

    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(
        request: Request, exc: TimeoutError
    ) -> JSONResponse:
        """Handle timeout errors."""
        logger.error(f"TimeoutError: {exc}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": "Request timed out",
                "status_code": 504,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "status_code": 500,
            },
        )


# Create the app instance
app = create_app()

# Debug: print registered routes
if __name__ == "__main__":
    from app.security.deployment_gate import run_deployment_gate, StartupError
    from app.config import get_settings
    
    settings = get_settings()
    
    # Run deployment gate validation
    # In debug mode (__main__), show validation but don't block
    # In production, it blocks automatically
    strict_mode = os.environ.get("NEXUSMIND_STRICT_STARTUP", "").lower() in ("true", "1", "yes")
    
    try:
        report = run_deployment_gate(settings, raise_on_failure=strict_mode)
        print(report.format_report())
        if not report.all_passed:
            print("\n⚠️  WARNING: Some checks failed. Application may not work correctly.")
            if strict_mode:
                exit(1)
    except StartupError as e:
        print(e)
        if strict_mode or settings.is_production:
            print("\n❌ STARTUP BLOCKED: Fix validation failures before deployment.")
            exit(1)
