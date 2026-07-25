"""Plugin manager with hot loading, dependencies, and permissions."""

import asyncio
import importlib
import importlib.util
import json
import os
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Callable

import yaml

from app.plugins.system.interface import PluginInterface
from app.plugins.system.schemas import (
    Dependency,
    Permission,
    PluginConfig,
    PluginExport,
    PluginHealth,
    PluginInfo,
    PluginManifest,
    PluginStatus,
    PluginType,
    Version,
)


class PluginError(Exception):
    """Plugin error."""
    pass


class DependencyError(PluginError):
    """Dependency error."""
    pass


class PermissionError(PluginError):
    """Permission denied error."""
    pass


class VersionError(PluginError):
    """Version incompatibility error."""
    pass


class PluginManager:
    """Manager for plugins with hot loading and dependency management."""

    def __init__(
        self,
        plugins_dir: str = "/tmp/plugins",
        permissions_enabled: bool = True,
    ):
        """Initialize plugin manager.
        
        Args:
            plugins_dir: Directory to load plugins from
            permissions_enabled: Whether to enforce permissions
        """
        self._plugins_dir = Path(plugins_dir)
        self._plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self._plugins: dict[str, PluginInfo] = {}
        self._instances: dict[str, PluginInterface] = {}
        self._permissions_enabled = permissions_enabled
        self._file_watchers: dict[str, Any] = {}
        self._hooks: dict[str, list[Callable]] = {
            "before_load": [],
            "after_load": [],
            "before_unload": [],
            "after_unload": [],
            "before_enable": [],
            "after_enable": [],
            "before_disable": [],
            "after_disable": [],
        }
        
        # Active permissions for current context
        self._active_permissions: set[Permission] = set()

    def add_hook(self, event: str, callback: Callable) -> None:
        """Add a hook callback.
        
        Args:
            event: Event name
            callback: Callback function
        """
        if event in self._hooks:
            self._hooks[event].append(callback)

    async def _run_hooks(self, event: str, plugin_id: str | None = None) -> None:
        """Run hook callbacks.
        
        Args:
            event: Event name
            plugin_id: Plugin ID if applicable
        """
        for callback in self._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin_id)
                else:
                    callback(plugin_id)
            except Exception as e:
                print(f"Hook error for {event}: {e}")

    def set_active_permissions(self, permissions: set[Permission]) -> None:
        """Set active permissions for current context.
        
        Args:
            permissions: Set of active permissions
        """
        self._active_permissions = permissions

    def check_permission(self, permission: Permission) -> bool:
        """Check if a permission is granted.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if granted
        """
        if not self._permissions_enabled:
            return True
        return permission in self._active_permissions

    def check_plugin_permissions(
        self,
        plugin_id: str,
        required_permissions: list[Permission],
    ) -> bool:
        """Check if plugin has required permissions.
        
        Args:
            plugin_id: Plugin ID
            required_permissions: Required permissions
            
        Returns:
            True if all granted
        """
        if not self._permissions_enabled:
            return True
        
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        # Check if plugin's permissions are granted
        for perm in plugin.manifest.metadata.permissions:
            if perm in required_permissions and perm not in self._active_permissions:
                return False
        
        return True

    def register_plugin(
        self,
        manifest: PluginManifest,
        instance: PluginInterface,
    ) -> None:
        """Register a plugin.
        
        Args:
            manifest: Plugin manifest
            instance: Plugin instance
        """
        plugin_id = manifest.metadata.id
        
        plugin_info = PluginInfo(
            manifest=manifest,
            status=PluginStatus.INSTALLED,
        )
        
        self._plugins[plugin_id] = plugin_info
        self._instances[plugin_id] = instance

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin.
        
        Args:
            plugin_id: Plugin ID
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
        if plugin_id in self._instances:
            del self._instances[plugin_id]

    async def load_plugin(self, plugin_id: str) -> PluginInfo:
        """Load a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginInfo
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise PluginError(f"Plugin not registered: {plugin_id}")
        
        if plugin.status in [PluginStatus.ENABLED]:
            return plugin
        
        await self._run_hooks("before_load", plugin_id)
        
        try:
            # Check dependencies
            await self._check_dependencies(plugin_id)
            
            # Initialize plugin
            instance = self._instances.get(plugin_id)
            if instance:
                await instance.initialize()
            
            plugin.status = PluginStatus.ENABLED
            plugin.updated_at = plugin.updated_at
            
            await self._run_hooks("after_load", plugin_id)
            
            return plugin
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error = str(e)
            raise

    async def unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin.
        
        Args:
            plugin_id: Plugin ID
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return
        
        await self._run_hooks("before_unload", plugin_id)
        
        try:
            instance = self._instances.get(plugin_id)
            if instance:
                await instance.shutdown()
            
            plugin.status = PluginStatus.DISABLED
            
            await self._run_hooks("after_unload", plugin_id)
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error = str(e)
            raise

    async def enable_plugin(self, plugin_id: str) -> PluginInfo:
        """Enable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginInfo
        """
        await self._run_hooks("before_enable", plugin_id)
        
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise PluginError(f"Plugin not registered: {plugin_id}")
        
        await self.load_plugin(plugin_id)
        plugin.config.enabled = True
        
        await self._run_hooks("after_enable", plugin_id)
        
        return plugin

    async def disable_plugin(self, plugin_id: str) -> PluginInfo:
        """Disable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginInfo
        """
        await self._run_hooks("before_disable", plugin_id)
        
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise PluginError(f"Plugin not registered: {plugin_id}")
        
        await self.unload_plugin(plugin_id)
        plugin.config.enabled = False
        
        await self._run_hooks("after_disable", plugin_id)
        
        return plugin

    async def reload_plugin(self, plugin_id: str) -> PluginInfo:
        """Hot reload a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginInfo
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise PluginError(f"Plugin not registered: {plugin_id}")
        
        plugin.status = PluginStatus.UPDATING
        
        try:
            # Shutdown
            instance = self._instances.get(plugin_id)
            if instance:
                await instance.shutdown()
            
            # Re-initialize
            if instance:
                await instance.initialize()
            
            plugin.status = PluginStatus.ENABLED
            plugin.updated_at = plugin.updated_at
            
            return plugin
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error = str(e)
            raise

    async def _check_dependencies(self, plugin_id: str) -> None:
        """Check plugin dependencies.
        
        Args:
            plugin_id: Plugin ID
            
        Raises:
            DependencyError: If dependencies not met
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return
        
        for dep in plugin.manifest.metadata.dependencies:
            dep_plugin = self._plugins.get(dep.name)
            
            if dep_plugin is None:
                if not dep.optional:
                    raise DependencyError(f"Missing dependency: {dep.name}")
                continue
            
            installed_version = Version.parse(dep_plugin.manifest.metadata.version)
            if not dep.check_version(installed_version):
                raise DependencyError(
                    f"Version mismatch for {dep.name}: "
                    f"required {dep.version}, got {installed_version}"
                )
            
            if dep_plugin.status != PluginStatus.ENABLED:
                if not dep.optional:
                    raise DependencyError(f"Dependency not enabled: {dep.name}")

    def get_plugin(self, plugin_id: str) -> PluginInfo | None:
        """Get plugin info.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginInfo or None
        """
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> list[PluginInfo]:
        """Get all plugins.
        
        Returns:
            List of PluginInfo
        """
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> list[PluginInfo]:
        """Get enabled plugins.
        
        Returns:
            List of enabled PluginInfo
        """
        return [
            p for p in self._plugins.values()
            if p.status == PluginStatus.ENABLED
        ]

    def get_plugins_by_type(self, plugin_type: PluginType) -> list[PluginInfo]:
        """Get plugins by type.
        
        Args:
            plugin_type: Plugin type
            
        Returns:
            List of PluginInfo
        """
        return [
            p for p in self._plugins.values()
            if p.manifest.metadata.plugin_type == plugin_type
        ]

    async def health_check_all(self) -> dict[str, PluginHealth]:
        """Check health of all plugins.
        
        Returns:
            Dict of plugin_id to PluginHealth
        """
        results = {}
        
        for plugin_id, plugin in self._plugins.items():
            if plugin.status != PluginStatus.ENABLED:
                continue
            
            try:
                instance = self._instances.get(plugin_id)
                if instance:
                    start = time.time()
                    health = await instance.health_check()
                    health.latency_ms = (time.time() - start) * 1000
                    results[plugin_id] = health
                else:
                    results[plugin_id] = PluginHealth(healthy=False, message="No instance")
            except Exception as e:
                results[plugin_id] = PluginHealth(
                    healthy=False,
                    message=str(e),
                )
        
        return results

    def get_exports(self, plugin_id: str) -> PluginExport | None:
        """Get plugin exports.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginExport or None
        """
        instance = self._instances.get(plugin_id)
        if instance:
            return instance.get_export()
        return None

    def get_all_exports(self) -> PluginExport:
        """Get all plugin exports combined.
        
        Returns:
            Combined PluginExport
        """
        combined = PluginExport()
        
        for plugin_id, plugin in self._plugins.items():
            if plugin.status != PluginStatus.ENABLED:
                continue
            
            exports = self.get_exports(plugin_id)
            if exports:
                combined.tools.extend(exports.tools)
                combined.agents.extend(exports.agents)
                combined.workflows.extend(exports.workflows)
                combined.api_routes.extend(exports.api_routes)
                combined.ui_panels.extend(exports.ui_panels)
        
        return combined

    async def load_from_directory(self, plugin_dir: Path) -> PluginInfo | None:
        """Load a plugin from a directory.
        
        Args:
            plugin_dir: Plugin directory containing plugin.json
            
        Returns:
            PluginInfo or None
        """
        manifest_path = plugin_dir / "plugin.json"
        
        if not manifest_path.exists():
            return None
        
        with open(manifest_path) as f:
            data = json.load(f)
        
        manifest = PluginManifest(**data)
        plugin_id = manifest.metadata.id
        
        # Check if already loaded
        if plugin_id in self._plugins:
            return self._plugins[plugin_id]
        
        # Load plugin module
        module_path = plugin_dir / "plugin.py"
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id}",
                module_path,
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"plugin_{plugin_id}"] = module
                spec.loader.exec_module(module)
                
                # Find plugin class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, PluginInterface)
                        and attr != PluginInterface
                    ):
                        instance = attr(manifest)
                        self.register_plugin(manifest, instance)
                        break
        else:
            # Just register without instance
            self.register_plugin(manifest, None)
        
        return self._plugins.get(plugin_id)

    async def load_all_plugins(self) -> list[PluginInfo]:
        """Load all plugins from plugins directory.
        
        Returns:
            List of loaded PluginInfo
        """
        loaded = []
        
        for item in self._plugins_dir.iterdir():
            if item.is_dir():
                plugin = await self.load_from_directory(item)
                if plugin:
                    loaded.append(plugin)
        
        return loaded

    async def uninstall_plugin(self, plugin_id: str) -> None:
        """Uninstall a plugin.
        
        Args:
            plugin_id: Plugin ID
        """
        if plugin_id not in self._plugins:
            return
        
        # Check for dependents
        for other_id, other in self._plugins.items():
            if other_id == plugin_id:
                continue
            for dep in other.manifest.metadata.dependencies:
                if dep.name == plugin_id and not dep.optional:
                    raise DependencyError(
                        f"Cannot uninstall {plugin_id}: required by {other_id}"
                    )
        
        await self.unload_plugin(plugin_id)
        self.unregister_plugin(plugin_id)
        
        # Remove files
        plugin_dir = self._plugins_dir / plugin_id
        if plugin_dir.exists():
            import shutil
            shutil.rmtree(plugin_dir)


# Global manager
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager.
    
    Returns:
        PluginManager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
