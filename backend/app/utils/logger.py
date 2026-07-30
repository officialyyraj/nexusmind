"""Logging configuration for NexusMind with structured logging support."""

import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from functools import lru_cache

from app.config import get_settings

# Context variables for request tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
workflow_id_var: ContextVar[str | None] = ContextVar("workflow_id", default=None)
agent_id_var: ContextVar[str | None] = ContextVar("agent_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class LogLevel(str, Enum):
    """Log level enumeration matching Python logging."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging with extended context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json

        # Use timezone-aware timestamp
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add all context variables
        request_id = request_id_var.get()
        session_id = session_id_var.get()
        workflow_id = workflow_id_var.get()
        agent_id = agent_id_var.get()
        user_id = user_id_var.get()

        if request_id:
            log_data["request_id"] = request_id
        if session_id:
            log_data["session_id"] = session_id
        if workflow_id:
            log_data["workflow_id"] = workflow_id
        if agent_id:
            log_data["agent_id"] = agent_id
        if user_id:
            log_data["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add resource info if available
        if hasattr(record, "resource"):
            log_data["resource"] = record.resource

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and context."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Add context suffix to message
        parts = [record.getMessage()]
        context_parts = []

        request_id = request_id_var.get()
        session_id = session_id_var.get()
        agent_id = agent_id_var.get()

        if request_id:
            context_parts.append(f"req={request_id[:8]}")
        if session_id:
            context_parts.append(f"sess={session_id[:8]}")
        if agent_id:
            context_parts.append(f"agent={agent_id[:8]}")

        if context_parts:
            parts.append(f"[{' '.join(context_parts)}]")

        record.msg = " ".join(parts)
        return super().format(record)


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.log_format == "json" and not settings.is_development:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


class StructuredLogger:
    """Logger with structured logging support."""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._name = name

    def _log(
        self,
        level: int,
        msg: str,
        session_id: str | None = None,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log with structured extra data."""
        extra = {"extra_data": kwargs}

        # Set context variables for the duration of this log call
        token = None
        if session_id:
            token = session_id_var.set(session_id)
        if workflow_id:
            workflow_id_var.set(workflow_id)
        if agent_id:
            agent_id_var.set(agent_id)
        if user_id:
            user_id_var.set(user_id)

        try:
            self._logger.log(level, msg, extra=extra)
        finally:
            # Reset context
            if token:
                session_id_var.reset(token)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(msg, extra={"extra_data": kwargs})


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter that adds context."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Process log message with extra context."""
        extra = kwargs.get("extra", {})

        # Add all context variables
        request_id = request_id_var.get()
        session_id = session_id_var.get()
        workflow_id = workflow_id_var.get()
        agent_id = agent_id_var.get()
        user_id = user_id_var.get()

        if request_id:
            extra["request_id"] = request_id
        if session_id:
            extra["session_id"] = session_id
        if workflow_id:
            extra["workflow_id"] = workflow_id
        if agent_id:
            extra["agent_id"] = agent_id
        if user_id:
            extra["user_id"] = user_id

        kwargs["extra"] = extra
        return msg, kwargs


@lru_cache
def get_logger_with_context(name: str) -> StructuredLogger:
    """Get a structured logger with context support."""
    return StructuredLogger(name)


def set_request_id(request_id: str | None) -> None:
    """Set the request ID for the current context."""
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get the current request ID."""
    return request_id_var.get()


def set_session_id(session_id: str | None) -> None:
    """Set the session ID for the current context."""
    session_id_var.set(session_id)


def get_session_id() -> str | None:
    """Get the current session ID."""
    return session_id_var.get()


def set_workflow_id(workflow_id: str | None) -> None:
    """Set the workflow ID for the current context."""
    workflow_id_var.set(workflow_id)


def get_workflow_id() -> str | None:
    """Get the current workflow ID."""
    return workflow_id_var.get()


def set_agent_id(agent_id: str | None) -> None:
    """Set the agent ID for the current context."""
    agent_id_var.set(agent_id)


def get_agent_id() -> str | None:
    """Get the current agent ID."""
    return agent_id_var.get()


def set_user_id(user_id: str | None) -> None:
    """Set the user ID for the current context."""
    user_id_var.set(user_id)


def get_user_id() -> str | None:
    """Get the current user ID."""
    return user_id_var.get()


def generate_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


class LogContext:
    """Context manager for setting log context variables."""

    def __init__(
        self,
        request_id: str | None = None,
        session_id: str | None = None,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        user_id: str | None = None,
    ):
        self._old_request_id = request_id_var.get()
        self._old_session_id = session_id_var.get()
        self._old_workflow_id = workflow_id_var.get()
        self._old_agent_id = agent_id_var.get()
        self._old_user_id = user_id_var.get()

        self._new_request_id = request_id
        self._new_session_id = session_id
        self._new_workflow_id = workflow_id
        self._new_agent_id = agent_id
        self._new_user_id = user_id

    def __enter__(self) -> "LogContext":
        if self._new_request_id:
            request_id_var.set(self._new_request_id)
        if self._new_session_id:
            session_id_var.set(self._new_session_id)
        if self._new_workflow_id:
            workflow_id_var.set(self._new_workflow_id)
        if self._new_agent_id:
            agent_id_var.set(self._new_agent_id)
        if self._new_user_id:
            user_id_var.set(self._new_user_id)
        return self

    def __exit__(self, *args: Any) -> None:
        request_id_var.set(self._old_request_id)
        session_id_var.set(self._old_session_id)
        workflow_id_var.set(self._old_workflow_id)
        agent_id_var.set(self._old_agent_id)
        user_id_var.set(self._old_user_id)
