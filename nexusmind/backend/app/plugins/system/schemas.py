"""Plugin system schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Types of plugins."""

    TOOL = "tool"
    AGENT = "agent"
    WORKFLOW = "workflow"
    API = "api"
    UI_PANEL = "ui_panel"
    INTEGRATION = "integration"


class PluginStatus(str, Enum):
    """Plugin status."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class Permission(str, Enum):
    """Plugin permissions."""

    # File system
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    EXECUTE_CODE = "execute_code"

    # Network
    NETWORK_ACCESS = "network_access"
    WEB_SEARCH = "web_search"

    # System
    EXECUTE_COMMANDS = "execute_commands"
    ACCESS_SECRETS = "access_secrets"

    # Data
    ACCESS_MEMORY = "access_memory"
    ACCESS_SESSIONS = "access_sessions"

    # Plugins
    MANAGE_PLUGINS = "manage_plugins"


class Version(BaseModel):
    """Plugin version."""

    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version

    @classmethod
    def parse(cls, version: str) -> "Version":
        """Parse version string, handling npm-style prefixes."""
        # Remove npm-style version prefixes
        version = version.lstrip("^~>=")
        version = version.lstrip("v")

        parts = version.split("-")
        nums = parts[0].split(".")
        return cls(
            major=int(nums[0]) if len(nums) > 0 else 0,
            minor=int(nums[1]) if len(nums) > 1 else 0,
            patch=int(nums[2]) if len(nums) > 2 else 0,
            prerelease=parts[1] if len(parts) > 1 else None,
        )

    def is_compatible(self, required: "Version") -> bool:
        """Check if this version satisfies a requirement.
        
        Returns True if self >= required (same major version).
        """
        if self.major != required.major:
            return False
        if self.minor != required.minor:
            return self.minor > required.minor
        return self.patch >= required.patch


class Dependency(BaseModel):
    """Plugin dependency."""

    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Version requirement")
    optional: bool = Field(False, description="Is optional")

    def check_version(self, installed_version: Version | None) -> bool:
        """Check if dependency is satisfied."""
        if installed_version is None:
            return self.optional

        required = Version.parse(self.version)
        return installed_version.is_compatible(required)


class PluginMetadata(BaseModel):
    """Plugin metadata."""

    id: str = Field(..., description="Unique plugin ID")
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field("", description="Plugin description")
    author: str = Field("", description="Plugin author")
    license: str = Field("MIT", description="License")
    homepage: str = Field("", description="Homepage URL")
    repository: str = Field("", description="Repository URL")
    plugin_type: PluginType = Field(..., description="Plugin type")
    permissions: list[Permission] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    min_app_version: str = Field("0.1.0", description="Minimum app version")
    tags: list[str] = Field(default_factory=list)
    icon: str = Field("", description="Icon URL or emoji")


class PluginManifest(BaseModel):
    """Plugin manifest (plugin.json)."""

    manifest_version: str = "1.0"
    metadata: PluginMetadata


class PluginConfig(BaseModel):
    """Plugin runtime configuration."""

    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0


class PluginInfo(BaseModel):
    """Full plugin information."""

    manifest: PluginManifest
    status: PluginStatus = PluginStatus.INSTALLED
    config: PluginConfig = Field(default_factory=PluginConfig)
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None
    health_check: str | None = None


class PluginExport(BaseModel):
    """Exports from a plugin."""

    tools: list[dict[str, Any]] = Field(default_factory=list)
    agents: list[dict[str, Any]] = Field(default_factory=list)
    workflows: list[dict[str, Any]] = Field(default_factory=list)
    api_routes: list[dict[str, Any]] = Field(default_factory=list)
    ui_panels: list[dict[str, Any]] = Field(default_factory=list)


class PluginHealth(BaseModel):
    """Plugin health status."""

    healthy: bool = True
    message: str = "OK"
    latency_ms: float | None = None


class MarketplaceListing(BaseModel):
    """Plugin marketplace listing."""

    metadata: PluginMetadata
    downloads: int = 0
    rating: float = 0.0
    reviews: int = 0
    verified: bool = False
    featured: bool = False
    categories: list[str] = Field(default_factory=list)


class PluginInstallRequest(BaseModel):
    """Request to install a plugin."""

    source: str = Field(..., description="Source: local, url, marketplace")
    version: str | None = None
    force: bool = False


class PluginUpdateRequest(BaseModel):
    """Request to update a plugin."""

    target_version: str | None = None
    force: bool = False
