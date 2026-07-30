"""OpenTelemetry instrumentation for NexusMind."""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Generator

from app.config import get_settings


class TelemetryService:
    """Service for OpenTelemetry tracing and metrics."""

    def __init__(self):
        self._tracer = None
        self._initialized = False
        self._spans = []

    def initialize(self) -> None:
        """Initialize OpenTelemetry instrumentation."""
        if self._initialized:
            return

        settings = get_settings()

        # Try to import OpenTelemetry
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import (
                BatchSpanProcessor,
                ConsoleSpanExporter,
            )
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.semconv.resource import ResourceAttributes

            # Create resource with service info
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: settings.app_name,
                ResourceAttributes.SERVICE_VERSION: settings.app_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.environment,
            })

            # Create tracer provider
            provider = TracerProvider(resource=resource)

            # Add console exporter for development
            if settings.is_development:
                console_processor = BatchSpanProcessor(ConsoleSpanExporter())
                provider.add_span_processor(console_processor)

            # Set the global tracer provider
            trace.set_tracer_provider(provider)

            # Get tracer
            self._tracer = trace.get_tracer(settings.app_name)
            self._initialized = True

        except ImportError:
            # OpenTelemetry not installed, use no-op implementation
            self._tracer = NoOpTracer()
            self._initialized = True

    def get_tracer(self):
        """Get the OpenTelemetry tracer."""
        if not self._initialized:
            self.initialize()
        return self._tracer

    @contextmanager
    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[Any, None, None]:
        """Create a span context."""
        tracer = self.get_tracer()
        with tracer.start_as_current_span(name, attributes=attributes) as span:
            try:
                yield span
            except Exception as e:
                if hasattr(span, 'record_exception'):
                    span.record_exception(e)
                raise

    def trace_function(self, name: str | None = None, attributes: dict[str, Any] | None = None):
        """Decorator to trace a function."""
        def decorator(func):
            span_name = name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self.span(span_name, attributes):
                    return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.span(span_name, attributes):
                    return func(*args, **kwargs)

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator

    def record_api_latency(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
    ) -> None:
        """Record API latency metric."""
        # This would be exported to the metrics service
        pass

    def record_agent_execution(
        self,
        agent_type: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record agent execution metric."""
        span = self.get_tracer().start_span("agent.execution")
        span.set_attribute("agent.type", agent_type)
        span.set_attribute("agent.duration_ms", duration_ms)
        span.set_attribute("agent.success", success)
        span.end()

    def record_tool_execution(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record tool execution metric."""
        span = self.get_tracer().start_span("tool.execution")
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("tool.duration_ms", duration_ms)
        span.set_attribute("tool.success", success)
        span.end()

    def record_database_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record database operation metric."""
        span = self.get_tracer().start_span("db.operation")
        span.set_attribute("db.operation", operation)
        span.set_attribute("db.duration_ms", duration_ms)
        span.set_attribute("db.success", success)
        span.end()

    def record_websocket_message(
        self,
        direction: str,
        message_size: int,
    ) -> None:
        """Record WebSocket message metric."""
        span = self.get_tracer().start_span("websocket.message")
        span.set_attribute("ws.direction", direction)
        span.set_attribute("ws.message_size", message_size)
        span.end()

    def record_mcp_invocation(
        self,
        server: str,
        tool: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record MCP invocation metric."""
        span = self.get_tracer().start_span("mcp.invocation")
        span.set_attribute("mcp.server", server)
        span.set_attribute("mcp.tool", tool)
        span.set_attribute("mcp.duration_ms", duration_ms)
        span.set_attribute("mcp.success", success)
        span.end()

    def record_browser_action(
        self,
        action_type: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record browser automation action metric."""
        span = self.get_tracer().start_span("browser.action")
        span.set_attribute("browser.action_type", action_type)
        span.set_attribute("browser.duration_ms", duration_ms)
        span.set_attribute("browser.success", success)
        span.end()


class NoOpSpan:
    """No-op span implementation."""

    def __init__(self):
        self._attributes = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def record_exception(self, exception: Exception) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class NoOpTracer:
    """No-op tracer implementation."""

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> NoOpSpan:
        return NoOpSpan()

    def start_as_current_span(self, name: str, attributes: dict[str, Any] | None = None):
        return NoOpSpan()

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None):
        yield NoOpSpan()


# Global telemetry service instance
_telemetry_service: TelemetryService | None = None


def get_telemetry_service() -> TelemetryService:
    """Get the global telemetry service instance."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service
