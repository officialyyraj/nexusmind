"""Main FastAPI application for NexusMind."""

import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.agents import router as agents_router
from app.api.v1.memory import router as memory_router
from app.api.v1.plugins import router as plugins_router
from app.api.v1.sandbox import router as sandbox_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.webhooks import router as webhooks_router
from app.auth.routes import router as auth_router
from app.tools.browser.api import router as browser_router
from app.config import get_settings
from app.utils.logger import get_logger, set_request_id, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

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

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any) -> Any:
        """Add request ID to each request for tracing."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
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
        return response

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routers
    settings = get_settings()
    api_prefix = settings.api_prefix
    app.include_router(auth_router, prefix=f"{api_prefix}/auth")
    app.include_router(sessions_router, prefix=f"{api_prefix}/sessions")
    app.include_router(agents_router, prefix=f"{api_prefix}/agents")
    app.include_router(sandbox_router, prefix=f"{api_prefix}/sandbox")
    app.include_router(memory_router, prefix=f"{api_prefix}/memory")
    app.include_router(plugins_router, prefix=f"{api_prefix}/plugins")
    app.include_router(webhooks_router, prefix=f"{api_prefix}/webhooks")
    app.include_router(browser_router)

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
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", {"WS"})
            print(f"{methods}: {route.path}")
