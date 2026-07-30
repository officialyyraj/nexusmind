"""Monitoring API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_maker
from app.monitoring.metrics import get_metrics_service
from app.monitoring.health import get_health_service

router = APIRouter()


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in async_session_maker():
        yield session


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns OK if the application is running.
    """
    return {
        "status": "healthy",
        "service": "NexusMind",
    }


@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Detailed health check with component status.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - ChromaDB connectivity
    - Ollama connectivity
    - MCP servers
    - Docker
    - Browser service
    """
    health_service = get_health_service()
    return await health_service.check_all(db)


@router.get("/health/live")
async def liveness_probe() -> dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns OK if the application is alive.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the application is ready to serve traffic.
    """
    health_service = get_health_service()

    # Check critical services
    db_health = await health_service.check_database(db)
    redis_health = await health_service.check_redis()

    if db_health.status.value == "healthy" and redis_health.status.value == "healthy":
        return {"status": "ready"}
    else:
        return {
            "status": "not_ready",
            "checks": {
                "database": db_health.status.value,
                "redis": redis_health.status.value,
            },
        }


@router.get("/metrics")
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    """
    metrics_service = get_metrics_service()
    content, content_type = metrics_service.get_metrics()
    return Response(content=content, media_type=content_type)


@router.get("/metrics/json")
async def metrics_json() -> dict[str, Any]:
    """
    JSON metrics endpoint for debugging.
    
    Returns metrics as a dictionary.
    """
    metrics_service = get_metrics_service()
    # Return basic stats as JSON
    return {
        "active_sessions": 0,
        "active_agents": 0,
        "websocket_connections": 0,
    }
