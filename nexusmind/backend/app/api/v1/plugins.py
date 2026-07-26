"""Plugins API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.dependencies import AuthenticatedUser
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
)
from app.api.v1.schemas import (
    PluginResponse,
    PluginDetailResponse,
    PluginInstallRequest,
    PluginUpdateRequest,
)

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


def get_manager() -> PluginManager:
    """Get plugin manager."""
    return get_plugin_manager()


def get_mp() -> MarketplaceClient:
    """Get marketplace client."""
    return get_marketplace()


def plugin_to_response(plugin: PluginInfo) -> PluginDetailResponse:
    """Convert PluginInfo to API response."""
    return PluginDetailResponse(
        name=plugin.manifest.metadata.name,
        version=plugin.manifest.metadata.version,
        status=plugin.status.value,
        description=plugin.manifest.metadata.description,
        plugin_type=plugin.manifest.metadata.plugin_type.value,
        manifest={
            "id": plugin.manifest.metadata.id,
            "name": plugin.manifest.metadata.name,
            "version": plugin.manifest.metadata.version,
            "description": plugin.manifest.metadata.description,
            "author": plugin.manifest.metadata.author,
            "license": plugin.manifest.metadata.license,
            "homepage": plugin.manifest.metadata.homepage,
            "repository": plugin.manifest.metadata.repository,
            "plugin_type": plugin.manifest.metadata.plugin_type.value,
            "permissions": [p.value for p in plugin.manifest.metadata.permissions],
            "dependencies": [{"name": d.name, "version": d.version} for d in plugin.manifest.metadata.dependencies],
            "tags": plugin.manifest.metadata.tags,
        },
        installed_at=plugin.installed_at,
        error=plugin.error,
    )


@router.get("/", response_model=list[PluginResponse])
async def list_plugins(
    user: AuthenticatedUser,
    enabled_only: bool = False,
    plugin_type: str | None = None,
) -> list[PluginResponse]:
    """List all plugins."""
    manager = get_manager()

    plugins = manager.get_all_plugins()

    if enabled_only:
        plugins = [p for p in plugins if p.status == PluginStatus.ENABLED]

    if plugin_type:
        try:
            pt = PluginType(plugin_type.lower())
            plugins = [p for p in plugins if p.manifest.metadata.plugin_type == pt]
        except ValueError:
            pass

    return [
        PluginResponse(
            name=p.manifest.metadata.name,
            version=p.manifest.metadata.version,
            status=p.status.value,
            description=p.manifest.metadata.description,
            plugin_type=p.manifest.metadata.plugin_type.value,
        )
        for p in plugins
    ]


@router.get("/{plugin_id}", response_model=PluginDetailResponse)
async def get_plugin(
    plugin_id: str,
    user: AuthenticatedUser,
) -> PluginDetailResponse:
    """Get plugin details."""
    manager = get_manager()
    plugin = manager.get_plugin(plugin_id)

    if not plugin:
        # Try to find by name
        for p in manager.get_all_plugins():
            if p.manifest.metadata.name == plugin_id:
                plugin = p
                break

    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin not found: {plugin_id}",
        )

    return plugin_to_response(plugin)


@router.patch("/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: str,
    data: PluginUpdateRequest,
    user: AuthenticatedUser,
) -> PluginResponse:
    """Update plugin configuration."""
    manager = get_manager()
    plugin = manager.get_plugin(plugin_id)

    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin not found: {plugin_id}",
        )

    if data.enabled is not None:
        if data.enabled:
            try:
                await manager.enable_plugin(plugin_id)
            except (PluginError, DependencyError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
        else:
            try:
                await manager.disable_plugin(plugin_id)
            except PluginError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

    if data.settings is not None:
        plugin.config.settings = data.settings

    return PluginResponse(
        name=plugin.manifest.metadata.name,
        version=plugin.manifest.metadata.version,
        status=plugin.status.value,
        description=plugin.manifest.metadata.description,
        plugin_type=plugin.manifest.metadata.plugin_type.value,
    )


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_plugin(
    plugin_id: str,
    user: AuthenticatedUser,
) -> None:
    """Uninstall plugin."""
    manager = get_manager()

    try:
        await manager.uninstall_plugin(plugin_id)
    except (PluginError, DependencyError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{plugin_id}/enable", response_model=PluginResponse)
async def enable_plugin(
    plugin_id: str,
    user: AuthenticatedUser,
) -> PluginResponse:
    """Enable plugin."""
    manager = get_manager()

    try:
        plugin = await manager.enable_plugin(plugin_id)
        return PluginResponse(
            name=plugin.manifest.metadata.name,
            version=plugin.manifest.metadata.version,
            status=plugin.status.value,
            description=plugin.manifest.metadata.description,
            plugin_type=plugin.manifest.metadata.plugin_type.value,
        )
    except (PluginError, DependencyError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{plugin_id}/disable", response_model=PluginResponse)
async def disable_plugin(
    plugin_id: str,
    user: AuthenticatedUser,
) -> PluginResponse:
    """Disable plugin."""
    manager = get_manager()

    try:
        plugin = await manager.disable_plugin(plugin_id)
        return PluginResponse(
            name=plugin.manifest.metadata.name,
            version=plugin.manifest.metadata.version,
            status=plugin.status.value,
            description=plugin.manifest.metadata.description,
            plugin_type=plugin.manifest.metadata.plugin_type.value,
        )
    except PluginError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{plugin_id}/reload", response_model=PluginResponse)
async def reload_plugin(
    plugin_id: str,
    user: AuthenticatedUser,
) -> PluginResponse:
    """Reload plugin."""
    manager = get_manager()

    try:
        plugin = await manager.reload_plugin(plugin_id)
        return PluginResponse(
            name=plugin.manifest.metadata.name,
            version=plugin.manifest.metadata.version,
            status=plugin.status.value,
            description=plugin.manifest.metadata.description,
            plugin_type=plugin.manifest.metadata.plugin_type.value,
        )
    except PluginError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{plugin_id}/health")
async def check_health(
    plugin_id: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Check plugin health."""
    manager = get_manager()
    plugin = manager.get_plugin(plugin_id)

    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin not found: {plugin_id}",
        )

    instance = manager._instances.get(plugin_id)
    if not instance:
        return {"healthy": False, "message": "No instance"}

    try:
        health = await instance.health_check()
        return {
            "healthy": health.healthy,
            "message": health.message,
            "latency_ms": health.latency_ms,
        }
    except Exception as e:
        return {"healthy": False, "message": str(e)}


@router.get("/{plugin_id}/exports")
async def get_exports(
    plugin_id: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Get plugin exports."""
    manager = get_manager()

    exports = manager.get_exports(plugin_id)
    if not exports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin not found or has no exports: {plugin_id}",
        )

    return {
        "tools": exports.tools,
        "agents": exports.agents,
        "workflows": exports.workflows,
        "api_routes": exports.api_routes,
        "ui_panels": exports.ui_panels,
    }


@router.get("/marketplace/search")
async def search_marketplace(
    user: AuthenticatedUser,
    query: str | None = None,
    plugin_type: str | None = None,
    tags: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search marketplace."""
    marketplace = get_mp()

    tag_list = tags.split(",") if tags else None

    try:
        results = await marketplace.search(
            query=query,
            plugin_type=plugin_type,
            tags=tag_list,
            limit=limit,
        )
        return [
            {
                "id": r.metadata.id,
                "name": r.metadata.name,
                "version": r.metadata.version,
                "description": r.metadata.description,
                "author": r.metadata.author,
                "downloads": r.downloads,
                "rating": r.rating,
                "verified": r.verified,
                "featured": r.featured,
                "categories": r.categories,
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/marketplace/install/{plugin_id}")
async def install_from_marketplace(
    plugin_id: str,
    user: AuthenticatedUser,
    version: str | None = None,
) -> dict[str, Any]:
    """Install plugin from marketplace."""
    marketplace = get_mp()
    manager = get_manager()

    try:
        result = await marketplace.download_plugin(plugin_id, version)
        await manager.load_from_directory(result["directory"])

        return {
            "status": "installed",
            "plugin_id": plugin_id,
            "version": result["version"].get("version"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
