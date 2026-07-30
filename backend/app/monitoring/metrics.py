"""Prometheus metrics for NexusMind."""

import time
from contextlib import contextmanager
from typing import Generator
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

from app.config import get_settings


class MetricsService:
    """Service for collecting and exposing Prometheus metrics."""

    def __init__(self, registry: CollectorRegistry = REGISTRY):
        self._registry = registry

        # Application info
        self.app_info = Info(
            "nexusmind_app",
            "NexusMind application information",
            registry=registry,
        )

        # Request metrics
        self.requests_total = Counter(
            "nexusmind_requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"],
            registry=registry,
        )

        self.request_duration = Histogram(
            "nexusmind_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=registry,
        )

        # Error metrics
        self.errors_total = Counter(
            "nexusmind_errors_total",
            "Total number of errors",
            ["type", "endpoint"],
            registry=registry,
        )

        # Session metrics
        self.active_sessions = Gauge(
            "nexusmind_active_sessions",
            "Number of active sessions",
            registry=registry,
        )

        self.sessions_total = Counter(
            "nexusmind_sessions_total",
            "Total number of sessions created",
            registry=registry,
        )

        # Agent metrics
        self.active_agents = Gauge(
            "nexusmind_active_agents",
            "Number of active agents",
            registry=registry,
        )

        self.agents_executed_total = Counter(
            "nexusmind_agents_executed_total",
            "Total number of agents executed",
            ["agent_type", "status"],
            registry=registry,
        )

        self.agent_execution_duration = Histogram(
            "nexusmind_agent_execution_duration_seconds",
            "Agent execution duration in seconds",
            ["agent_type"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=registry,
        )

        # Tool execution metrics
        self.tool_executions_total = Counter(
            "nexusmind_tool_executions_total",
            "Total number of tool executions",
            ["tool_name", "status"],
            registry=registry,
        )

        self.tool_execution_duration = Histogram(
            "nexusmind_tool_execution_duration_seconds",
            "Tool execution duration in seconds",
            ["tool_name"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
            registry=registry,
        )

        # Database metrics
        self.db_queries_total = Counter(
            "nexusmind_db_queries_total",
            "Total number of database queries",
            ["operation", "status"],
            registry=registry,
        )

        self.db_query_duration = Histogram(
            "nexusmind_db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=registry,
        )

        # WebSocket metrics
        self.websocket_connections = Gauge(
            "nexusmind_websocket_connections",
            "Number of active WebSocket connections",
            registry=registry,
        )

        self.websocket_messages_total = Counter(
            "nexusmind_websocket_messages_total",
            "Total number of WebSocket messages",
            ["direction"],
            registry=registry,
        )

        # MCP metrics
        self.mcp_tool_invocations_total = Counter(
            "nexusmind_mcp_tool_invocations_total",
            "Total number of MCP tool invocations",
            ["server", "tool", "status"],
            registry=registry,
        )

        self.mcp_latency = Histogram(
            "nexusmind_mcp_latency_seconds",
            "MCP tool invocation latency in seconds",
            ["server", "tool"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=registry,
        )

        # Browser automation metrics
        self.browser_actions_total = Counter(
            "nexusmind_browser_actions_total",
            "Total number of browser actions",
            ["action_type", "status"],
            registry=registry,
        )

        self.browser_action_duration = Histogram(
            "nexusmind_browser_action_duration_seconds",
            "Browser action duration in seconds",
            ["action_type"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=registry,
        )

        # Docker metrics
        self.docker_containers = Gauge(
            "nexusmind_docker_containers",
            "Number of active Docker containers",
            ["status"],
            registry=registry,
        )

        # Resource metrics
        self.memory_usage_bytes = Gauge(
            "nexusmind_memory_usage_bytes",
            "Memory usage in bytes",
            ["type"],
            registry=registry,
        )

        self.cpu_usage_percent = Gauge(
            "nexusmind_cpu_usage_percent",
            "CPU usage percentage",
            registry=registry,
        )

        # Token usage
        self.tokens_used = Counter(
            "nexusmind_tokens_used_total",
            "Total number of tokens used",
            ["model", "type"],
            registry=registry,
        )

    def set_app_info(self, name: str, version: str, environment: str) -> None:
        """Set application information."""
        self.app_info.info({
            "name": name,
            "version": version,
            "environment": environment,
        })

    @contextmanager
    def track_request(self, method: str, endpoint: str) -> Generator[None, None, None]:
        """Context manager to track request duration."""
        start_time = time.perf_counter()
        status = "500"
        try:
            yield
            status = "200"
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start_time
            self.requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
            self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_request(self, method: str, endpoint: str, status: int, duration: float) -> None:
        """Record a request metric."""
        self.requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_error(self, error_type: str, endpoint: str) -> None:
        """Record an error metric."""
        self.errors_total.labels(type=error_type, endpoint=endpoint).inc()

    def track_agent_execution(self, agent_type: str):
        """Decorator to track agent execution."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status = "success"
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception:
                    status = "error"
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    self.agents_executed_total.labels(agent_type=agent_type, status=status).inc()
                    self.agent_execution_duration.labels(agent_type=agent_type).observe(duration)
            return wrapper
        return decorator

    def track_tool_execution(self, tool_name: str):
        """Decorator to track tool execution."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status = "success"
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception:
                    status = "error"
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    self.tool_executions_total.labels(tool_name=tool_name, status=status).inc()
                    self.tool_execution_duration.labels(tool_name=tool_name).observe(duration)
            return wrapper
        return decorator

    def track_db_query(self, operation: str):
        """Decorator to track database query duration."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status = "success"
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception:
                    status = "error"
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    self.db_queries_total.labels(operation=operation, status=status).inc()
                    self.db_query_duration.labels(operation=operation).observe(duration)
            return wrapper
        return decorator

    def record_mcp_invocation(
        self,
        server: str,
        tool: str,
        status: str,
        duration: float,
    ) -> None:
        """Record an MCP tool invocation."""
        self.mcp_tool_invocations_total.labels(
            server=server, tool=tool, status=status
        ).inc()
        self.mcp_latency.labels(server=server, tool=tool).observe(duration)

    def record_tokens(self, model: str, token_type: str, count: int) -> None:
        """Record token usage."""
        self.tokens_used.labels(model=model, type=token_type).inc(count)

    def set_active_sessions(self, count: int) -> None:
        """Set the number of active sessions."""
        self.active_sessions.set(count)

    def set_active_agents(self, count: int) -> None:
        """Set the number of active agents."""
        self.active_agents.set(count)

    def set_websocket_connections(self, count: int) -> None:
        """Set the number of WebSocket connections."""
        self.websocket_connections.set(count)

    def set_docker_containers(self, status: str, count: int) -> None:
        """Set the number of Docker containers by status."""
        self.docker_containers.labels(status=status).set(count)

    def get_metrics(self) -> tuple[bytes, str]:
        """Get the current metrics in Prometheus format."""
        return generate_latest(self._registry), CONTENT_TYPE_LATEST


# Global metrics service instance
_metrics_service: MetricsService | None = None


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
        settings = get_settings()
        _metrics_service.set_app_info(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )
    return _metrics_service
