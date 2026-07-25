"""REST API endpoints for plugin system."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.plugins.system.manager import (
    PluginManager,
    get_plugin_manager,
    DependencyError,
    PluginError,
)
from app.plugins.system.schemas import (
    PluginExport,
    PluginHealth,
    PluginInfo,
    PluginManifest,
    PluginStatus,
    PluginType,
)
from app.plugins.system.marketplace import (
    MarketplaceClient,
    get_marketplace,
    get_local_marketplace,
    MarketplaceListing,
)

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


def get_manager() -> PluginManager:
    """Get plugin manager."""
    return get_plugin_manager()


def get_mp() -> MarketplaceClient:
    """Get marketplace client."""
    return get_marketplace()


# Plugin Management

@router.get("/", response_model=list[PluginInfo])
async def list_plugins(
    enabled_only: bool = False,
    plugin_type: PluginType | None = None,
) -> list[PluginInfo]:
    """List all plugins.
    
    Args:
        enabled_only: Only return enabled plugins
        plugin_type: Filter by type
        
    Returns:
        List of plugins
    """
    manager = get_manager()

    plugins = manager.get_all_plugins()

    if enabled_only:
        plugins = [p for p in plugins if p.status == PluginStatus.ENABLED]

    if plugin_type:
        plugins = [p for p in plugins if p.manifest.metadata.plugin_type == plugin_type]

    return plugins


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str) -> PluginInfo:
    """Get plugin info.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Plugin info
    """
    manager = get_manager()
    plugin = manager.get_plugin(plugin_id)

    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return plugin


@router.post("/{plugin_id}/load")
async def load_plugin(plugin_id: str) -> PluginInfo:
    """Load a plugin.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Updated plugin info
    """
    manager = get_manager()

    try:
        return await manager.load_plugin(plugin_id)
    except PluginError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/unload")
async def unload_plugin(plugin_id: str) -> dict[str, Any]:
    """Unload a plugin.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Success status
    """
    manager = get_manager()

    try:
        await manager.unload_plugin(plugin_id)
        return {"status": "unloaded"}
    except PluginError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str) -> PluginInfo:
    """Enable a plugin.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Updated plugin info
    """
    manager = get_manager()

    try:
        return await manager.enable_plugin(plugin_id)
    except (PluginError, DependencyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str) -> PluginInfo:
    """Disable a plugin.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Updated plugin info
    """
    manager = get_manager()

    try:
        return await manager.disable_plugin(plugin_id)
    except PluginError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/reload")
async def reload_plugin(plugin_id: str) -> PluginInfo:
    """Hot reload a plugin.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Updated plugin info
    """
    manager = get_manager()

    try:
        return await manager.reload_plugin(plugin_id)
    except PluginError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{plugin_id}")
async def uninstall_plugin(plugin_id: str) -> dict[str, Any]:
    """Uninstall a plugin.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Success status
    """
    manager = get_manager()

    try:
        await manager.uninstall_plugin(plugin_id)
        return {"status": "uninstalled"}
    except (PluginError, DependencyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health & Exports

@router.get("/{plugin_id}/health", response_model=PluginHealth)
async def health_check(plugin_id: str) -> PluginHealth:
    """Check plugin health.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Plugin health status
    """
    manager = get_manager()
    plugin = manager.get_plugin(plugin_id)

    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    instance = manager._instances.get(plugin_id)
    if not instance:
        return PluginHealth(healthy=False, message="No instance")

    try:
        return await instance.health_check()
    except Exception as e:
        return PluginHealth(healthy=False, message=str(e))


@router.get("/{plugin_id}/exports", response_model=PluginExport)
async def get_exports(plugin_id: str) -> PluginExport:
    """Get plugin exports.
    
    Args:
        plugin_id: Plugin ID
        
    Returns:
        Plugin exports
    """
    manager = get_manager()

    exports = manager.get_exports(plugin_id)
    if not exports:
        raise HTTPException(status_code=404, detail="Plugin not found or no exports")

    return exports


@router.get("/exports/all", response_model=PluginExport)
async def get_all_exports() -> PluginExport:
    """Get all plugin exports combined.
    
    Returns:
        Combined exports
    """
    manager = get_manager()
    return manager.get_all_exports()


@router.get("/health/all")
async def health_check_all() -> dict[str, PluginHealth]:
    """Check health of all plugins.
    
    Returns:
        Health status for all plugins
    """
    manager = get_manager()
    return await manager.health_check_all()


# Marketplace

@router.get("/marketplace/search")
async def search_marketplace(
    query: str | None = None,
    plugin_type: str | None = None,
    tags: str | None = None,
    limit: int = 20,
) -> list[MarketplaceListing]:
    """Search marketplace.
    
    Args:
        query: Search query
        plugin_type: Filter by type
        tags: Comma-separated tags
        limit: Max results
        
    Returns:
        Search results
    """
    marketplace = get_mp()

    tag_list = tags.split(",") if tags else None

    try:
        return await marketplace.search(
            query=query,
            plugin_type=plugin_type,
            tags=tag_list,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/featured")
async def get_featured() -> list[MarketplaceListing]:
    """Get featured plugins.
    
    Returns:
        Featured plugins
    """
    marketplace = get_mp()

    try:
        return await marketplace.get_featured()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/install/{plugin_id}")
async def install_from_marketplace(
    plugin_id: str,
    version: str | None = None,
) -> dict[str, Any]:
    """Install plugin from marketplace.
    
    Args:
        plugin_id: Plugin ID
        version: Specific version
        
    Returns:
        Installation result
    """
    marketplace = get_mp()
    manager = get_manager()

    try:
        # Download plugin
        result = await marketplace.download_plugin(plugin_id, version)

        # Load plugin
        await manager.load_from_directory(result["directory"])

        return {
            "status": "installed",
            "plugin_id": plugin_id,
            "version": result["version"].get("version"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Local Marketplace (Development)

@router.get("/local/list")
async def list_local_plugins() -> list[MarketplaceListing]:
    """List plugins in local marketplace.
    
    Returns:
        Local plugins
    """
    local = get_local_marketplace()
    return local.list_all()


# Registration

@router.post("/register")
async def register_plugin(manifest: dict[str, Any]) -> dict[str, Any]:
    """Register a plugin with manifest.
    
    Args:
        manifest: Plugin manifest
        
    Returns:
        Registration result
    """
    manager = get_manager()

    try:
        plugin_manifest = PluginManifest(**manifest)
        plugin_id = plugin_manifest.metadata.id

        manager.register_plugin(plugin_manifest, None)

        return {"status": "registered", "plugin_id": plugin_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
