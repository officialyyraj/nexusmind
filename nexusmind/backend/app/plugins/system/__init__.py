"""Plugin system module."""

from app.plugins.system.api import router as api_router
from app.plugins.system.interface import (
    AgentPluginInterface,
    APIPluginInterface,
    PluginInterface,
    ToolPluginInterface,
    UIPluginInterface,
    WorkflowPluginInterface,
    plugin,
)
from app.plugins.system.manager import (
    DependencyError,
    PermissionError,
    PluginError,
    PluginManager,
    VersionError,
    get_plugin_manager,
)
from app.plugins.system.marketplace import (
    LocalMarketplace,
    MarketplaceClient,
    MarketplaceError,
    get_local_marketplace,
    get_marketplace,
    set_marketplace,
)
from app.plugins.system.schemas import (
    Dependency,
    MarketplaceListing,
    Permission,
    PluginConfig,
    PluginExport,
    PluginHealth,
    PluginInfo,
    PluginManifest,
    PluginStatus,
    PluginType,
    PluginUpdateRequest,
    Version,
)

__all__ = [
    # API
    "api_router",
    # Interface
    "PluginInterface",
    "ToolPluginInterface",
    "AgentPluginInterface",
    "WorkflowPluginInterface",
    "APIPluginInterface",
    "UIPluginInterface",
    "plugin",
    # Manager
    "PluginManager",
    "get_plugin_manager",
    "PluginError",
    "DependencyError",
    "PermissionError",
    "VersionError",
    # Marketplace
    "MarketplaceClient",
    "LocalMarketplace",
    "get_marketplace",
    "get_local_marketplace",
    "set_marketplace",
    "MarketplaceError",
    # Schemas
    "PluginType",
    "PluginStatus",
    "Permission",
    "Version",
    "Dependency",
    "PluginManifest",
    "PluginMetadata",
    "PluginConfig",
    "PluginInfo",
    "PluginExport",
    "PluginHealth",
    "MarketplaceListing",
    "PluginUpdateRequest",
]
