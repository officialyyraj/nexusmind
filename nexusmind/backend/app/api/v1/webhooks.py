"""Webhooks API endpoints."""

from typing import Any

from fastapi import APIRouter

from app.dependencies import AuthenticatedUser

router = APIRouter()


@router.post("/")
async def create_webhook(
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Create a webhook."""
    webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
    return {"id": webhook_id, "url": data.get("url", ""), "enabled": True}


@router.get("/")
async def list_webhooks(
    user: AuthenticatedUser,
) -> list[dict[str, Any]]:
    """List all webhooks for the authenticated user."""
    return []


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Get webhook details."""
    return {"id": webhook_id, "enabled": True}


@router.patch("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    data: dict[str, Any],
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Update webhook."""
    return {"id": webhook_id, "updated": True}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    user: AuthenticatedUser,
) -> dict[str, Any]:
    """Delete webhook."""
    return {"id": webhook_id, "deleted": True}
