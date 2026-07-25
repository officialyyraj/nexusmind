"""Security middleware for FastAPI."""

import uuid
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' ws: wss: https:",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Strict-Transport-Security (HTTPS only)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), document-domain=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), midi=(), "
            "payment=(), usb=()"
        )

        # X-XSS-Protection (legacy, but kept for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for basic rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self._requests_per_minute = requests_per_minute
        self._requests: dict[str, list[float]] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Apply rate limiting."""
        # Get client identifier
        client_ip = self._get_client_ip(request)

        # Clean old requests
        self._clean_old_requests(client_ip)

        # Check rate limit
        if len(self._requests.get(client_ip, [])) >= self._requests_per_minute:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self._requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Record request
        import time
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        self._requests[client_ip].append(time.time())

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._requests_per_minute - len(self._requests.get(client_ip, []))
        response.headers["X-RateLimit-Limit"] = str(self._requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _clean_old_requests(self, client_ip: str) -> None:
        """Remove requests older than 1 minute."""
        import time
        now = time.time()
        if client_ip in self._requests:
            self._requests[client_ip] = [
                t for t in self._requests[client_ip]
                if now - t < 60
            ]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID for tracing."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Add request ID to request and response."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add to request state for access in handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class CORSMiddleware:
    """Custom CORS middleware with stricter settings."""

    def __init__(
        self,
        app,
        allowed_origins: list[str],
        allowed_methods: list[str] | None = None,
        allowed_headers: list[str] | None = None,
        allow_credentials: bool = True,
        max_age: int = 600,
    ):
        self._app = app
        self._allowed_origins = allowed_origins
        self._allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self._allowed_headers = allowed_headers or [
            "Accept",
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-Request-ID",
            "X-CSRF-Token",
        ]
        self._allow_credentials = allow_credentials
        self._max_age = max_age

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Handle CORS for the request."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        # Get origin from request
        origin = None
        for key, value in scope.get("headers", []):
            if key == b"origin":
                origin = value.decode()
                break

        # Check if origin is allowed
        if origin and origin in self._allowed_origins:
            # Handle preflight
            if scope.get("method") == "OPTIONS":
                await self._send_preflight_response(scope, receive, send, origin)
                return

            # Add CORS headers to response
            async def send_wrapper(message: dict) -> None:
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.extend([
                        (b"Access-Control-Allow-Origin", origin.encode()),
                        (b"Access-Control-Allow-Methods", ",".join(self._allowed_methods).encode()),
                        (b"Access-Control-Allow-Headers", ",".join(self._allowed_headers).encode()),
                        (b"Access-Control-Max-Age", str(self._max_age).encode()),
                    ])
                    if self._allow_credentials:
                        headers.append((b"Access-Control-Allow-Credentials", b"true"))
                    message["headers"] = headers
                await send(message)

            await self._app(scope, receive, send_wrapper)
        else:
            await self._app(scope, receive, send)

    async def _send_preflight_response(
        self,
        scope: dict,
        receive: Callable,
        send: Callable,
        origin: str,
    ) -> None:
        """Send preflight response."""
        await send({
            "type": "http.response.start",
            "status": 204,
            "headers": [
                (b"Access-Control-Allow-Origin", origin.encode()),
                (b"Access-Control-Allow-Methods", ",".join(self._allowed_methods).encode()),
                (b"Access-Control-Allow-Headers", ",".join(self._allowed_headers).encode()),
                (b"Access-Control-Max-Age", str(self._max_age).encode()),
                (b"Access-Control-Allow-Credentials", b"true") if self._allow_credentials else (b"", b""),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })


def setup_security_middleware(app: FastAPI) -> None:
    """Setup all security middleware for the application."""
    settings = get_settings()

    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    # Add request ID middleware
    app.add_middleware(RequestIDMiddleware)

    logger.info("Security middleware configured")
