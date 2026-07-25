"""Plugin marketplace architecture."""

import hashlib
import json
import re
from datetime import datetime
from typing import Any

import httpx

from app.plugins.system.schemas import MarketplaceListing, PluginManifest, PluginMetadata


class MarketplaceError(Exception):
    """Marketplace error."""
    pass


class MarketplaceClient:
    """Client for plugin marketplace."""

    def __init__(
        self,
        marketplace_url: str = "https://marketplace.example.com",
        api_key: str | None = None,
    ):
        """Initialize marketplace client.
        
        Args:
            marketplace_url: Marketplace URL
            api_key: API key for authenticated requests
        """
        self._url = marketplace_url.rstrip("/")
        self._api_key = api_key
        self._cache: dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def search(
        self,
        query: str | None = None,
        plugin_type: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[MarketplaceListing]:
        """Search marketplace.
        
        Args:
            query: Search query
            plugin_type: Filter by type
            tags: Filter by tags
            limit: Max results
            
        Returns:
            List of marketplace listings
        """
        params = {"limit": limit}
        if query:
            params["q"] = query
        if plugin_type:
            params["type"] = plugin_type
        if tags:
            params["tags"] = ",".join(tags)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._url}/api/v1/plugins/search",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            return [MarketplaceListing(**item) for item in data.get("results", [])]

    async def get_listing(self, plugin_id: str) -> MarketplaceListing:
        """Get a plugin listing.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            MarketplaceListing
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._url}/api/v1/plugins/{plugin_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return MarketplaceListing(**response.json())

    async def get_version(self, plugin_id: str, version: str) -> dict[str, Any]:
        """Get specific plugin version.
        
        Args:
            plugin_id: Plugin ID
            version: Version string
            
        Returns:
            Version info with download URL
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._url}/api/v1/plugins/{plugin_id}/versions/{version}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def download_plugin(
        self,
        plugin_id: str,
        version: str | None = None,
        target_dir: str | None = None,
    ) -> dict[str, Any]:
        """Download a plugin.
        
        Args:
            plugin_id: Plugin ID
            version: Specific version (latest if None)
            target_dir: Target directory
            
        Returns:
            Download info with manifest
        """
        version_info = await self.get_version(plugin_id, version or "latest")

        # Download plugin package
        download_url = version_info.get("download_url")
        if not download_url:
            raise MarketplaceError("No download URL available")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(download_url)
            response.raise_for_status()

            # Parse plugin package
            import tarfile
            import io

            with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
                # Extract to target directory
                manifest_data = None

                for member in tar.getmembers():
                    if member.name == "plugin.json":
                        manifest_data = json.loads(tar.extractfile(member).read())
                        break

                if not manifest_data:
                    raise MarketplaceError("Invalid plugin package: missing plugin.json")

                return {
                    "manifest": PluginManifest(**manifest_data),
                    "version": version_info,
                    "directory": target_dir,
                }

    async def verify_plugin(self, plugin_id: str) -> dict[str, Any]:
        """Verify a plugin's integrity.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Verification result
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._url}/api/v1/plugins/{plugin_id}/verify",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def submit_plugin(self, manifest: PluginManifest) -> dict[str, Any]:
        """Submit a plugin to the marketplace.
        
        Args:
            manifest: Plugin manifest
            
        Returns:
            Submission result
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._url}/api/v1/plugins/submit",
                json=manifest.model_dump(),
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_featured(self) -> list[MarketplaceListing]:
        """Get featured plugins.
        
        Returns:
            List of featured plugins
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._url}/api/v1/plugins/featured",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            return [MarketplaceListing(**item) for item in data.get("results", [])]

    async def get_categories(self) -> list[dict[str, Any]]:
        """Get marketplace categories.
        
        Returns:
            List of categories
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._url}/api/v1/categories",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()


class LocalMarketplace:
    """Local file-based marketplace for development."""

    def __init__(self, directory: str = "/tmp/marketplace"):
        """Initialize local marketplace.
        
        Args:
            directory: Directory containing plugins
        """
        from pathlib import Path
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def add_plugin(
        self,
        manifest: PluginManifest,
        files: dict[str, str] | None = None,
    ) -> None:
        """Add a plugin to local marketplace.
        
        Args:
            manifest: Plugin manifest
            files: Additional files to add
        """
        plugin_dir = self._directory / manifest.metadata.id
        plugin_dir.mkdir(exist_ok=True)

        # Save manifest
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)

        # Save additional files
        if files:
            for filename, content in files.items():
                filepath = plugin_dir / filename
                filepath.parent.mkdir(exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(content)

    def get_plugin_ids(self) -> list[str]:
        """Get all plugin IDs.
        
        Returns:
            List of plugin IDs
        """
        return [d.name for d in self._directory.iterdir() if d.is_dir()]

    def get_manifest(self, plugin_id: str) -> PluginManifest | None:
        """Get plugin manifest.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            PluginManifest or None
        """
        manifest_path = self._directory / plugin_id / "plugin.json"

        if not manifest_path.exists():
            return None

        with open(manifest_path) as f:
            return PluginManifest(**json.load(f))

    def get_file(self, plugin_id: str, filename: str) -> str | None:
        """Get plugin file content.
        
        Args:
            plugin_id: Plugin ID
            filename: File name
            
        Returns:
            File content or None
        """
        file_path = self._directory / plugin_id / filename

        if not file_path.exists():
            return None

        with open(file_path) as f:
            return f.read()

    def list_all(self) -> list[MarketplaceListing]:
        """List all plugins in marketplace.
        
        Returns:
            List of marketplace listings
        """
        listings = []

        for plugin_id in self.get_plugin_ids():
            manifest = self.get_manifest(plugin_id)
            if manifest:
                listings.append(MarketplaceListing(
                    metadata=manifest.metadata,
                    downloads=0,
                    rating=0.0,
                    verified=True,  # Local = verified
                ))

        return listings


# Global marketplace client
_marketplace: MarketplaceClient | None = None
_local_marketplace: LocalMarketplace | None = None


def get_marketplace() -> MarketplaceClient:
    """Get the global marketplace client.
    
    Returns:
        MarketplaceClient instance
    """
    global _marketplace
    if _marketplace is None:
        _marketplace = MarketplaceClient()
    return _marketplace


def get_local_marketplace() -> LocalMarketplace:
    """Get the local marketplace.
    
    Returns:
        LocalMarketplace instance
    """
    global _local_marketplace
    if _local_marketplace is None:
        _local_marketplace = LocalMarketplace()
    return _local_marketplace


def set_marketplace(marketplace: MarketplaceClient) -> None:
    """Set the global marketplace client.
    
    Args:
        marketplace: MarketplaceClient instance
    """
    global _marketplace
    _marketplace = marketplace
