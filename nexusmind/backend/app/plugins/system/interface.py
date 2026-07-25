"""Plugin interface and base class."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from app.plugins.system.schemas import PluginExport, PluginHealth, PluginManifest


class PluginInterface(ABC):
    """Base interface for all plugins."""

    def __init__(self, manifest: PluginManifest):
        """Initialize plugin.
        
        Args:
            manifest: Plugin manifest
        """
        self.manifest = manifest
        self._exported: PluginExport | None = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin. Called on first load."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin. Called on unload."""
        pass

    @abstractmethod
    async def health_check(self) -> PluginHealth:
        """Check plugin health.
        
        Returns:
            PluginHealth status
        """
        pass

    def get_export(self) -> PluginExport:
        """Get plugin exports.
        
        Returns:
            PluginExport with tools, agents, etc.
        """
        if self._exported is None:
            self._exported = self._create_export()
        return self._exported

    def _create_export(self) -> PluginExport:
        """Create plugin export. Override in subclass."""
        return PluginExport()

    async def reload(self) -> None:
        """Reload the plugin."""
        await self.shutdown()
        await self.initialize()

    def get_metadata(self) -> dict[str, Any]:
        """Get plugin metadata.
        
        Returns:
            Metadata dict
        """
        return {
            "id": self.manifest.metadata.id,
            "name": self.manifest.metadata.name,
            "version": self.manifest.metadata.version,
            "type": self.manifest.metadata.plugin_type.value,
        }


class ToolPluginInterface(PluginInterface):
    """Interface for tool plugins."""

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """Get plugin tools.
        
        Returns:
            List of tool definitions
        """
        pass


class AgentPluginInterface(PluginInterface):
    """Interface for agent plugins."""

    @abstractmethod
    def get_agents(self) -> list[dict[str, Any]]:
        """Get plugin agents.
        
        Returns:
            List of agent definitions
        """
        pass


class WorkflowPluginInterface(PluginInterface):
    """Interface for workflow plugins."""

    @abstractmethod
    def get_workflows(self) -> list[dict[str, Any]]:
        """Get plugin workflows.
        
        Returns:
            List of workflow definitions
        """
        pass


class APIPluginInterface(PluginInterface):
    """Interface for API plugins."""

    @abstractmethod
    def get_api_routes(self) -> list[dict[str, Any]]:
        """Get plugin API routes.
        
        Returns:
            List of API route definitions
        """
        pass


class UIPluginInterface(PluginInterface):
    """Interface for UI panel plugins."""

    @abstractmethod
    def get_ui_panels(self) -> list[dict[str, Any]]:
        """Get plugin UI panels.
        
        Returns:
            List of UI panel definitions
        """
        pass


# Plugin decorator for registration
def plugin(name: str, version: str, plugin_type: str):
    """Decorator to register a plugin class.
    
    Args:
        name: Plugin name
        version: Plugin version
        plugin_type: Plugin type
    
    Usage:
        @plugin("my-plugin", "1.0.0", "tool")
        class MyPlugin(ToolPluginInterface):
            ...
    """
    def decorator(cls):
        cls._plugin_name = name
        cls._plugin_version = version
        cls._plugin_type = plugin_type
        return cls
    return decorator
