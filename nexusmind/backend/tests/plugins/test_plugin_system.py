"""Tests for plugin system."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from app.plugins.system.schemas import (
    Dependency,
    MarketplaceListing,
    Permission,
    PluginConfig,
    PluginExport,
    PluginHealth,
    PluginInfo,
    PluginManifest,
    PluginMetadata,
    PluginStatus,
    PluginType,
    Version,
)
from app.plugins.system.manager import (
    DependencyError,
    PermissionError,
    PluginError,
    PluginManager,
    VersionError,
    get_plugin_manager,
)
from app.plugins.system.interface import (
    PluginInterface,
    ToolPluginInterface,
    plugin,
)
from app.plugins.system.marketplace import LocalMarketplace


class TestSchemas:
    """Test plugin schemas."""

    def test_version_parse(self):
        """Test version parsing."""
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_version_parse_prerelease(self):
        """Test version parsing with prerelease."""
        v = Version.parse("1.0.0-beta.1")
        assert v.major == 1
        assert v.prerelease == "beta.1"

    def test_version_parse_v_prefix(self):
        """Test version parsing with v prefix."""
        v = Version.parse("v2.0.0")
        assert v.major == 2

    def test_version_str(self):
        """Test version string representation."""
        v = Version(major=1, minor=2, patch=3)
        assert str(v) == "1.2.3"

    def test_version_is_compatible(self):
        """Test version compatibility (v1 >= v2)."""
        # v1 = 1.2.0, v2 = 1.3.0
        # v1 >= v2? No (1.2.0 < 1.3.0)
        v1 = Version.parse("1.2.0")
        v2 = Version.parse("1.3.0")
        assert not v1.is_compatible(v2)  # 1.2.0 < 1.3.0
        
        # v1 = 1.3.0, v2 = 1.2.0
        # v1 >= v2? Yes
        v3 = Version.parse("1.3.0")
        v4 = Version.parse("1.2.0")
        assert v3.is_compatible(v4)  # 1.3.0 >= 1.2.0
        
        # Same version
        assert v1.is_compatible(Version.parse("1.2.0"))  # 1.2.0 >= 1.2.0

    def test_version_not_compatible_major(self):
        """Test version incompatibility (different major)."""
        v1 = Version.parse("1.0.0")
        v2 = Version.parse("2.0.0")
        assert not v1.is_compatible(v2)

    def test_dependency_check_version(self):
        """Test dependency version checking."""
        dep = Dependency(name="test", version="^1.0.0")
        
        # Installed 1.0.0 >= required 1.0.0? Yes
        assert dep.check_version(Version.parse("1.0.0")) is True
        # Installed 1.5.0 >= required 1.0.0? Yes
        assert dep.check_version(Version.parse("1.5.0")) is True
        # Installed 2.0.0 >= required 1.0.0? No (different major)

    def test_dependency_optional(self):
        """Test optional dependency."""
        dep = Dependency(name="test", version="^1.0.0", optional=True)
        
        assert dep.check_version(None) is True

    def test_plugin_metadata(self):
        """Test plugin metadata."""
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
            permissions=[Permission.READ_FILES],
        )
        
        assert metadata.id == "test-plugin"
        assert Permission.READ_FILES in metadata.permissions

    def test_plugin_manifest(self):
        """Test plugin manifest."""
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        
        manifest = PluginManifest(metadata=metadata)
        
        assert manifest.metadata.id == "test-plugin"
        assert manifest.metadata.version == "1.0.0"

    def test_plugin_info_defaults(self):
        """Test plugin info defaults."""
        metadata = PluginMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        
        manifest = PluginManifest(metadata=metadata)
        info = PluginInfo(manifest=manifest)
        
        assert info.status == PluginStatus.INSTALLED
        assert info.config.enabled is True

    def test_plugin_export(self):
        """Test plugin export."""
        export = PluginExport(
            tools=[{"name": "my_tool", "description": "A tool"}],
            agents=[{"name": "my_agent", "type": "coder"}],
        )
        
        assert len(export.tools) == 1
        assert len(export.agents) == 1

    def test_plugin_health(self):
        """Test plugin health."""
        health = PluginHealth(healthy=True, latency_ms=100.0)
        
        assert health.healthy is True
        assert health.latency_ms == 100.0

    def test_permission_values(self):
        """Test permission enum values."""
        assert Permission.READ_FILES.value == "read_files"
        assert Permission.WRITE_FILES.value == "write_files"
        assert Permission.NETWORK_ACCESS.value == "network_access"


class TestPluginManager:
    """Test plugin manager."""

    def test_manager_creation(self):
        """Test plugin manager creation."""
        manager = PluginManager(plugins_dir="/tmp/test_plugins")
        assert manager is not None
        assert len(manager.get_all_plugins()) == 0

    def test_register_plugin(self):
        """Test plugin registration."""
        manager = PluginManager()
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        mock_instance = MagicMock(spec=PluginInterface)
        manager.register_plugin(manifest, mock_instance)
        
        plugin = manager.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.manifest.metadata.id == "test-plugin"

    def test_unregister_plugin(self):
        """Test plugin unregistration."""
        manager = PluginManager()
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        manager.register_plugin(manifest, None)
        assert manager.get_plugin("test-plugin") is not None
        
        manager.unregister_plugin("test-plugin")
        assert manager.get_plugin("test-plugin") is None

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins."""
        manager = PluginManager()
        
        metadata1 = PluginMetadata(
            id="test1", name="Test1", version="1.0.0", plugin_type=PluginType.TOOL
        )
        metadata2 = PluginMetadata(
            id="test2", name="Test2", version="1.0.0", plugin_type=PluginType.TOOL
        )
        
        p1 = PluginInfo(manifest=PluginManifest(metadata=metadata1), status=PluginStatus.ENABLED)
        p2 = PluginInfo(manifest=PluginManifest(metadata=metadata2), status=PluginStatus.DISABLED)
        
        manager._plugins["test1"] = p1
        manager._plugins["test2"] = p2
        
        enabled = manager.get_enabled_plugins()
        assert len(enabled) == 1
        assert enabled[0].manifest.metadata.id == "test1"

    def test_get_plugins_by_type(self):
        """Test getting plugins by type."""
        manager = PluginManager()
        
        metadata1 = PluginMetadata(
            id="tool1", name="Tool1", version="1.0.0", plugin_type=PluginType.TOOL
        )
        metadata2 = PluginMetadata(
            id="agent1", name="Agent1", version="1.0.0", plugin_type=PluginType.AGENT
        )
        
        p1 = PluginInfo(manifest=PluginManifest(metadata=metadata1))
        p2 = PluginInfo(manifest=PluginManifest(metadata=metadata2))
        
        manager._plugins["tool1"] = p1
        manager._plugins["agent1"] = p2
        
        tools = manager.get_plugins_by_type(PluginType.TOOL)
        assert len(tools) == 1
        
        agents = manager.get_plugins_by_type(PluginType.AGENT)
        assert len(agents) == 1

    def test_check_permission(self):
        """Test permission checking."""
        manager = PluginManager(permissions_enabled=True)
        manager.set_active_permissions({Permission.READ_FILES})
        
        assert manager.check_permission(Permission.READ_FILES) is True
        assert manager.check_permission(Permission.WRITE_FILES) is False

    def test_check_permission_disabled(self):
        """Test permission checking when disabled."""
        manager = PluginManager(permissions_enabled=False)
        
        assert manager.check_permission(Permission.WRITE_FILES) is True

    @pytest.mark.asyncio
    async def test_load_plugin(self):
        """Test loading a plugin."""
        manager = PluginManager()
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        mock_instance = MagicMock(spec=PluginInterface)
        mock_instance.initialize = AsyncMock()
        mock_instance.health_check = AsyncMock(
            return_value=PluginHealth(healthy=True)
        )
        
        manager.register_plugin(manifest, mock_instance)
        
        await manager.load_plugin("test-plugin")
        
        plugin = manager.get_plugin("test-plugin")
        assert plugin.status == PluginStatus.ENABLED
        mock_instance.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_dependency_error(self):
        """Test dependency error."""
        manager = PluginManager()
        
        # Plugin with unsatisfied dependency
        metadata = PluginMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
            dependencies=[
                Dependency(name="missing-plugin", version="^1.0.0", optional=False)
            ],
        )
        manifest = PluginManifest(metadata=metadata)
        
        manager.register_plugin(manifest, None)
        
        with pytest.raises(DependencyError):
            await manager._check_dependencies("test")

    @pytest.mark.asyncio
    async def test_unload_plugin(self):
        """Test unloading a plugin."""
        manager = PluginManager()
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        mock_instance = MagicMock(spec=PluginInterface)
        mock_instance.shutdown = AsyncMock()
        mock_instance.health_check = AsyncMock(
            return_value=PluginHealth(healthy=True)
        )
        
        manager.register_plugin(manifest, mock_instance)
        manager._plugins["test-plugin"].status = PluginStatus.ENABLED
        
        await manager.unload_plugin("test-plugin")
        
        plugin = manager.get_plugin("test-plugin")
        assert plugin.status == PluginStatus.DISABLED
        mock_instance.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_plugin(self):
        """Test reloading a plugin."""
        manager = PluginManager()
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        mock_instance = MagicMock(spec=PluginInterface)
        mock_instance.initialize = AsyncMock()
        mock_instance.shutdown = AsyncMock()
        mock_instance.health_check = AsyncMock(
            return_value=PluginHealth(healthy=True)
        )
        
        manager.register_plugin(manifest, mock_instance)
        manager._plugins["test-plugin"].status = PluginStatus.ENABLED
        
        await manager.reload_plugin("test-plugin")
        
        plugin = manager.get_plugin("test-plugin")
        assert plugin.status == PluginStatus.ENABLED
        mock_instance.shutdown.assert_called_once()
        mock_instance.initialize.assert_called_once()


class TestLocalMarketplace:
    """Test local marketplace."""

    def test_marketplace_creation(self):
        """Test local marketplace creation."""
        marketplace = LocalMarketplace("/tmp/test_marketplace")
        assert marketplace is not None

    def test_add_plugin(self):
        """Test adding a plugin to marketplace."""
        marketplace = LocalMarketplace("/tmp/test_marketplace2")
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        marketplace.add_plugin(manifest, {"README.md": "# Test"})
        
        ids = marketplace.get_plugin_ids()
        assert "test-plugin" in ids

    def test_get_manifest(self):
        """Test getting plugin manifest."""
        marketplace = LocalMarketplace("/tmp/test_marketplace3")
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        marketplace.add_plugin(manifest)
        
        retrieved = marketplace.get_manifest("test-plugin")
        assert retrieved is not None
        assert retrieved.metadata.id == "test-plugin"

    def test_get_file(self):
        """Test getting plugin file."""
        marketplace = LocalMarketplace("/tmp/test_marketplace4")
        
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        marketplace.add_plugin(manifest, {"README.md": "# Test Plugin"})
        
        content = marketplace.get_file("test-plugin", "README.md")
        assert content == "# Test Plugin"

    def test_list_all(self):
        """Test listing all plugins."""
        marketplace = LocalMarketplace("/tmp/test_marketplace5")
        
        metadata = PluginMetadata(
            id="plugin1",
            name="Plugin 1",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        marketplace.add_plugin(manifest)
        
        listings = marketplace.list_all()
        assert len(listings) >= 1
        assert any(l.metadata.id == "plugin1" for l in listings)


class TestPluginInterface:
    """Test plugin interface."""

    def test_plugin_decorator(self):
        """Test plugin decorator."""
        @plugin("my-plugin", "1.0.0", "tool")
        class MyPlugin(ToolPluginInterface):
            pass
        
        assert hasattr(MyPlugin, "_plugin_name")
        assert MyPlugin._plugin_name == "my-plugin"
        assert MyPlugin._plugin_version == "1.0.0"
        assert MyPlugin._plugin_type == "tool"

    def test_get_metadata(self):
        """Test getting plugin metadata."""
        metadata = PluginMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
        )
        manifest = PluginManifest(metadata=metadata)
        
        class MockPlugin(PluginInterface):
            async def initialize(self): pass
            async def shutdown(self): pass
            async def health_check(self): 
                return PluginHealth()
        
        plugin = MockPlugin(manifest)
        meta = plugin.get_metadata()
        
        assert meta["id"] == "test"
        assert meta["name"] == "Test"


class TestAPI:
    """Test API endpoints."""

    def test_api_router_import(self):
        """Test that API router can be imported."""
        from app.plugins.system.api import router
        assert router is not None
