"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1 import agents, executions, memory, mcp, plugins, sandbox, sessions, webhooks

api_router = APIRouter()

# Include all API routes
api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"],
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"],
)

api_router.include_router(
    sandbox.router,
    prefix="/sandbox",
    tags=["sandbox"],
)

api_router.include_router(
    memory.router,
    prefix="/memory",
    tags=["memory"],
)

api_router.include_router(
    plugins.router,
    prefix="/plugins",
    tags=["plugins"],
)

api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["webhooks"],
)

api_router.include_router(
    executions.router,
    prefix="/executions",
    tags=["executions"],
)

api_router.include_router(
    mcp.router,
    prefix="/mcp",
    tags=["mcp"],
)
