"""Webhooks API endpoints."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_webhook(data: dict[str, Any]) -> dict[str, Any]:
    """Create a webhook."""
    return {"id": "wh_placeholder", "url": "", "enabled": True}


@router.get("/")
async def list_webhooks() -> list[dict[str, Any]]:
    """List all webhooks."""
    return []


@router.get("/{webhook_id}")
async def get_webhook(webhook_id: str) -> dict[str, Any]:
    """Get webhook details."""
    return {"id": webhook_id, "enabled": True}


@router.patch("/{webhook_id}")
async def update_webhook(
    webhook_id: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Update webhook."""
    return {"id": webhook_id, "updated": True}


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str) -> dict[str, Any]:
    """Delete webhook."""
    return {"id": webhook_id, "deleted": True}
