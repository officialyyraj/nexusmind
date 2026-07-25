"""Health check service for NexusMind."""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status for a single component."""

    def __init__(
        self,
        name: str,
        status: HealthStatus,
        latency_ms: float | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.name = name
        self.status = status
        self.latency_ms = latency_ms
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "details": self.details,
        }


class HealthService:
    """Service for checking system health."""

    def __init__(self):
        self._settings = get_settings()

    async def check_database(self, session: AsyncSession) -> ComponentHealth:
        """Check database connectivity."""
        import time

        start = time.perf_counter()
        try:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                message="Database connection successful",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=f"Database connection failed: {str(e)}",
            )

    async def check_redis(self) -> ComponentHealth:
        """Check Redis connectivity."""
        import time

        start = time.perf_counter()
        try:
            redis = await aioredis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await redis.ping()
            latency = (time.perf_counter() - start) * 1000
            await redis.aclose()
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                message="Redis connection successful",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=f"Redis connection failed: {str(e)}",
            )

    async def check_chromadb(self) -> ComponentHealth:
        """Check ChromaDB connectivity."""
        import time

        start = time.perf_counter()
        try:
            import chromadb
            client = chromadb.Client()
            client.heartbeat()
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="chromadb",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                message="ChromaDB connection successful",
            )
        except ImportError:
            return ComponentHealth(
                name="chromadb",
                status=HealthStatus.DEGRADED,
                latency_ms=None,
                message="ChromaDB not installed",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="chromadb",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=f"ChromaDB connection failed: {str(e)}",
            )

    async def check_ollama(self) -> ComponentHealth:
        """Check Ollama connectivity."""
        import time

        start = time.perf_counter()
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._settings.ollama_base_url}/api/tags",
                    timeout=5.0,
                )
                latency = (time.perf_counter() - start) * 1000

                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return ComponentHealth(
                        name="ollama",
                        status=HealthStatus.HEALTHY,
                        latency_ms=round(latency, 2),
                        message=f"Ollama connected ({len(models)} models available)",
                        details={"models": [m.get("name") for m in models[:5]]},
                    )
                else:
                    return ComponentHealth(
                        name="ollama",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=round(latency, 2),
                        message=f"Ollama returned status {response.status_code}",
                    )
        except ImportError:
            return ComponentHealth(
                name="ollama",
                status=HealthStatus.DEGRADED,
                latency_ms=None,
                message="httpx not installed",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="ollama",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=f"Ollama connection failed: {str(e)}",
            )

    async def check_mcp_servers(self) -> ComponentHealth:
        """Check MCP server connectivity."""
        try:
            from app.mcp import get_mcp_manager

            manager = get_mcp_manager()
            servers = manager.list_servers()

            healthy_count = sum(1 for s in servers if s.get("status") == "running")
            total_count = len(servers)

            if healthy_count == total_count:
                return ComponentHealth(
                    name="mcp_servers",
                    status=HealthStatus.HEALTHY,
                    message=f"All {total_count} MCP servers healthy",
                    details={"servers": servers},
                )
            elif healthy_count > 0:
                return ComponentHealth(
                    name="mcp_servers",
                    status=HealthStatus.DEGRADED,
                    message=f"{healthy_count}/{total_count} MCP servers healthy",
                    details={"servers": servers},
                )
            else:
                return ComponentHealth(
                    name="mcp_servers",
                    status=HealthStatus.UNHEALTHY,
                    message="No MCP servers healthy",
                    details={"servers": servers},
                )
        except ImportError:
            return ComponentHealth(
                name="mcp_servers",
                status=HealthStatus.DEGRADED,
                message="MCP module not available",
            )
        except Exception as e:
            return ComponentHealth(
                name="mcp_servers",
                status=HealthStatus.UNHEALTHY,
                message=f"MCP check failed: {str(e)}",
            )

    async def check_docker(self) -> ComponentHealth:
        """Check Docker connectivity."""
        try:
            import docker
            client = docker.from_env()
            info = client.info()
            containers = client.containers.list()

            return ComponentHealth(
                name="docker",
                status=HealthStatus.HEALTHY,
                message=f"Docker connected ({len(containers)} containers)",
                details={
                    "version": info.get("ServerVersion"),
                    "containers_running": len(containers),
                },
            )
        except ImportError:
            return ComponentHealth(
                name="docker",
                status=HealthStatus.DEGRADED,
                message="Docker SDK not installed",
            )
        except Exception as e:
            return ComponentHealth(
                name="docker",
                status=HealthStatus.UNHEALTHY,
                message=f"Docker connection failed: {str(e)}",
            )

    async def check_browser_service(self) -> ComponentHealth:
        """Check browser automation service."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                await browser.close()

            return ComponentHealth(
                name="browser_service",
                status=HealthStatus.HEALTHY,
                message="Browser service available",
            )
        except ImportError:
            return ComponentHealth(
                name="browser_service",
                status=HealthStatus.DEGRADED,
                message="Playwright not installed",
            )
        except Exception as e:
            return ComponentHealth(
                name="browser_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Browser service failed: {str(e)}",
            )

    async def check_all(
        self,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Check all system components."""
        checks = []

        # Run all checks in parallel
        tasks = []

        if session:
            tasks.append(self.check_database(session))
        tasks.append(self.check_redis())
        tasks.append(self.check_chromadb())
        tasks.append(self.check_ollama())
        tasks.append(self.check_mcp_servers())
        tasks.append(self.check_docker())
        tasks.append(self.check_browser_service())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle failed checks
                check_names = ["database", "redis", "chromadb", "ollama", "mcp_servers", "docker", "browser_service"]
                name = check_names[i] if i < len(check_names) else f"unknown_{i}"
                checks.append(ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(result)}",
                ))
            else:
                checks.append(result)

        # Determine overall status
        statuses = [c.status for c in checks]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        return {
            "status": overall.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "components": [c.to_dict() for c in checks],
        }


# Global health service instance
_health_service: HealthService | None = None


def get_health_service() -> HealthService:
    """Get the global health service instance."""
    global _health_service
    if _health_service is None:
        _health_service = HealthService()
    return _health_service
