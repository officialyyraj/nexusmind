"""Input validation for all user inputs."""

import re
import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ValidationError(Exception):
    """Validation error with details."""

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


class InputValidator:
    """Comprehensive input validation service."""

    # Common patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # Dangerous patterns for injection detection
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]

    SCRIPT_INJECTION_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onload\s*=",
    ]

    def __init__(self):
        self._sql_pattern = re.compile("|".join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE)
        self._script_pattern = re.compile("|".join(self.SCRIPT_INJECTION_PATTERNS), re.IGNORECASE)

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        return bool(self.EMAIL_PATTERN.match(email))

    def validate_uuid(self, value: str) -> bool:
        """Validate UUID format."""
        if not value:
            return False
        return bool(self.UUID_PATTERN.match(value))

    def validate_alphanumeric(self, value: str) -> bool:
        """Validate alphanumeric string."""
        if not value:
            return False
        return bool(self.ALPHANUMERIC_PATTERN.match(value))

    def validate_length(
        self,
        value: str,
        min_length: int = 0,
        max_length: int = 10000,
    ) -> bool:
        """Validate string length."""
        if not value:
            return min_length == 0
        return min_length <= len(value) <= max_length

    def validate_safe_string(
        self,
        value: str,
        allow_whitespace: bool = True,
        allow_newlines: bool = False,
    ) -> bool:
        """Validate string is safe (no injection patterns)."""
        if not value:
            return True

        # Check for SQL injection
        if self._sql_pattern.search(value):
            return False

        # Check for script injection
        if self._script_pattern.search(value):
            return False

        # Check for null bytes
        if "\x00" in value:
            return False

        # Check whitespace settings
        if not allow_whitespace and any(c.isspace() for c in value):
            return False

        if not allow_newlines and ("\n" in value or "\r" in value):
            return False

        return True

    def sanitize_string(
        self,
        value: str,
        max_length: int = 10000,
        strip_html: bool = True,
    ) -> str:
        """Sanitize a string by removing dangerous content."""
        if not value:
            return ""

        # Truncate to max length
        if len(value) > max_length:
            value = value[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        if strip_html:
            # Basic HTML stripping
            value = re.sub(r"<[^>]*>", "", value)
            # Remove script-like content
            value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)
            value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)

        return value.strip()

    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        if not url:
            return False
        pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return bool(pattern.match(url))

    def validate_path(self, path: str, allowed_roots: list[str] | None = None) -> bool:
        """Validate file path is safe."""
        if not path:
            return False

        # Check for path traversal
        if ".." in path or path.startswith("/"):
            return False

        # Check for absolute paths on Windows
        if len(path) > 1 and path[1] == ":":
            return False

        if allowed_roots:
            # Verify path is within allowed roots
            normalized = path.replace("\\", "/")
            for root in allowed_roots:
                if normalized.startswith(root) or normalized.startswith("./" + root):
                    return True
            return False

        return True

    def validate_command(
        self,
        command: str,
        allowed_commands: list[str] | None = None,
    ) -> bool:
        """Validate terminal command."""
        if not command:
            return False

        # Basic safety checks
        dangerous_patterns = [
            r"rm\s+-rf\s+/",  # Dangerous rm
            r">\s*/dev/sda",  # Direct device write
            r"dd\s+.*of=/dev/",  # Direct device write
            r";\s*rm\s+",  # Command chaining with rm
            r"\|\s*rm\s+",  # Pipe to rm
            r"eval\s*\$",  # Eval of variable
            r"`.*`",  # Command substitution
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False

        # Check against allowed commands
        if allowed_commands:
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] not in allowed_commands:
                return False

        return True

    def validate_api_key_format(self, key: str) -> bool:
        """Validate API key format."""
        if not key:
            return False
        # Basic format check (at least 20 characters, alphanumeric with common separators)
        return len(key) >= 20 and bool(re.match(r"^[a-zA-Z0-9_\-]+$", key))

    def validate_json(self, data: Any) -> tuple[bool, str | None]:
        """Validate JSON data structure."""
        import json

        if isinstance(data, str):
            try:
                json.loads(data)
                return True, None
            except json.JSONDecodeError as e:
                return False, str(e)
        return True, None

    def validate_dict_schema(
        self,
        data: dict,
        required_fields: list[str],
        optional_fields: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """Validate dictionary has required fields."""
        if not isinstance(data, dict):
            return False, "Expected dict"

        # Check required fields
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        # Check for unknown fields
        if optional_fields is not None:
            allowed = set(required_fields + optional_fields)
            unknown = [k for k in data.keys() if k not in allowed]
            if unknown:
                return False, f"Unknown fields: {', '.join(unknown)}"

        return True, None

    def validate_mcp_input(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate MCP tool invocation input."""
        if not self.validate_alphanumeric(tool_name):
            return False, "Invalid tool name format"

        # Sanitize arguments
        sanitized = {}
        for key, value in arguments.items():
            if isinstance(value, str):
                if not self.validate_safe_string(value):
                    return False, f"Unsafe content in argument: {key}"
                sanitized[key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                # Recursively validate nested dicts
                valid, error = self._validate_nested_dict(value)
                if not valid:
                    return False, f"Unsafe content in nested argument: {key}.{error}"
                sanitized[key] = value
            else:
                sanitized[key] = value

        return True, None

    def _validate_nested_dict(self, data: dict) -> tuple[bool, str | None]:
        """Recursively validate nested dictionary."""
        for key, value in data.items():
            if isinstance(value, str):
                if not self.validate_safe_string(value):
                    return False, key
            elif isinstance(value, dict):
                valid, error = self._validate_nested_dict(value)
                if not valid:
                    return False, f"{key}.{error}"
        return True, None

    def validate_github_webhook(
        self,
        event: str,
        action: str | None = None,
    ) -> bool:
        """Validate GitHub webhook event."""
        valid_events = {
            "push", "pull_request", "issues", "issue_comment",
            "commit_comment", "create", "delete", "fork", "gollum",
            "label", "member", "membership", "milestone", "organization",
            "org_block", "page_build", "ping", "project_card", "project_column",
            "public", "pull_request_review", "pull_request_review_comment",
            "release", "repository", "status", "team", "team_add",
            "watch", "security_advisory",
        }

        if event not in valid_events:
            return False

        # Validate action if provided
        if action:
            if not self.validate_alphanumeric(action):
                return False

        return True


class PluginInputValidator:
    """Validator for plugin inputs."""

    def __init__(self, validator: InputValidator):
        self._validator = validator

    def validate_plugin_config(self, config: dict) -> tuple[bool, str | None]:
        """Validate plugin configuration."""
        required = ["name", "version"]
        valid, error = self._validator.validate_dict_schema(config, required)
        if not valid:
            return False, error

        # Validate name format
        if not self._validator.validate_alphanumeric(config["name"]):
            return False, "Invalid plugin name format"

        # Validate version format
        version_pattern = re.compile(r"^\d+\.\d+\.\d+$")
        if not version_pattern.match(config["version"]):
            return False, "Invalid version format (expected x.y.z)"

        return True, None

    def validate_plugin_permissions(self, permissions: list[str]) -> tuple[bool, str | None]:
        """Validate plugin permission requests."""
        valid_permissions = {
            "filesystem:read",
            "filesystem:write",
            "network:read",
            "network:write",
            "process:execute",
            "secrets:read",
            "secrets:write",
        }

        for perm in permissions:
            if perm not in valid_permissions:
                return False, f"Unknown permission: {perm}"

        return True, None


# Global validator instance
_input_validator: InputValidator | None = None


def get_input_validator() -> InputValidator:
    """Get input validator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator
