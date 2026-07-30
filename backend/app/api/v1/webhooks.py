"""Webhooks API endpoints."""

import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select, desc

from app.dependencies import AuthenticatedUser, DbSession
from app.db.webhook import Webhook, WebhookDelivery
from app.api.v1.schemas import (
    WebhookResponse,
    WebhookDetailResponse,
    WebhookCreateRequest,
    WebhookUpdateRequest,
    WebhookDeliveryResponse,
    WebhookRotateSecretResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def get_webhook_or_404(
    webhook_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> Webhook:
    """Get webhook by ID or raise 404."""
    try:
        webhook_uuid = uuid.UUID(webhook_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook ID format",
        )
    
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_uuid)
    )
    webhook = result.scalar_one_or_none()
    
    if webhook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Ownership verification
    if webhook.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this webhook",
        )
    
    return webhook


@router.post("/", response_model=WebhookDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreateRequest,
    user: AuthenticatedUser,
    db: DbSession,
) -> WebhookDetailResponse:
    """Create a new webhook."""
    # Generate secret if not provided
    secret = data.webhook_secret or Webhook.generate_secret()
    
    webhook = Webhook(
        user_id=user.id,
        name=data.url.split("?")[0],  # Use URL path as default name
        url=data.url,
        source=data.source,
        event_key_expr=data.event_key_expr,
        signature_header=data.signature_header,
        is_enabled=True,
    )
    webhook.set_secret(secret)
    
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    
    return WebhookDetailResponse(
        id=str(webhook.id),
        url=webhook.url,
        enabled=webhook.is_enabled,
        created_at=webhook.created_at,
        source=webhook.source,
        event_key_expr=webhook.event_key_expr,
        signature_header=webhook.signature_header,
        last_triggered=webhook.last_triggered,
        delivery_count=webhook.delivery_count,
    )


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(
    user: AuthenticatedUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[WebhookResponse]:
    """List all webhooks for the authenticated user."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.user_id == user.id)
        .order_by(desc(Webhook.created_at))
        .offset(offset)
        .limit(limit)
    )
    webhooks = result.scalars().all()
    
    return [
        WebhookResponse(
            id=str(w.id),
            url=w.url,
            enabled=w.is_enabled,
            created_at=w.created_at,
        )
        for w in webhooks
    ]


@router.get("/{webhook_id}", response_model=WebhookDetailResponse)
async def get_webhook(
    webhook_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> WebhookDetailResponse:
    """Get webhook details."""
    webhook = await get_webhook_or_404(webhook_id, user, db)
    
    return WebhookDetailResponse(
        id=str(webhook.id),
        url=webhook.url,
        enabled=webhook.is_enabled,
        created_at=webhook.created_at,
        source=webhook.source,
        event_key_expr=webhook.event_key_expr,
        signature_header=webhook.signature_header,
        last_triggered=webhook.last_triggered,
        delivery_count=webhook.delivery_count,
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    data: WebhookUpdateRequest,
    user: AuthenticatedUser,
    db: DbSession,
) -> WebhookResponse:
    """Update webhook."""
    webhook = await get_webhook_or_404(webhook_id, user, db)
    
    if data.url is not None:
        webhook.url = data.url
    if data.enabled is not None:
        webhook.is_enabled = data.enabled
    if data.event_key_expr is not None:
        webhook.event_key_expr = data.event_key_expr
    
    await db.flush()
    await db.refresh(webhook)
    
    return WebhookResponse(
        id=str(webhook.id),
        url=webhook.url,
        enabled=webhook.is_enabled,
        created_at=webhook.created_at,
    )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> None:
    """Delete webhook."""
    webhook = await get_webhook_or_404(webhook_id, user, db)
    
    await db.delete(webhook)
    await db.flush()


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_deliveries(
    webhook_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[WebhookDeliveryResponse]:
    """List webhook delivery history."""
    webhook = await get_webhook_or_404(webhook_id, user, db)
    
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook.id)
        .order_by(desc(WebhookDelivery.created_at))
        .offset(offset)
        .limit(limit)
    )
    deliveries = result.scalars().all()
    
    return [
        WebhookDeliveryResponse(
            id=str(d.id),
            webhook_id=str(d.webhook_id),
            status="success" if d.response_status and d.response_status < 400 else "failed",
            payload=d.payload,
            response_status=d.response_status,
            response_body=d.response_body,
            error=d.error,
            delivered_at=d.delivered_at,
        )
        for d in deliveries
    ]


@router.post("/{webhook_id}/rotate-secret", response_model=WebhookRotateSecretResponse)
async def rotate_secret(
    webhook_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> WebhookRotateSecretResponse:
    """Rotate webhook secret."""
    webhook = await get_webhook_or_404(webhook_id, user, db)
    
    new_secret = Webhook.generate_secret()
    webhook.set_secret(new_secret)
    
    await db.flush()
    
    return WebhookRotateSecretResponse(
        id=str(webhook.id),
        new_secret=new_secret,
        rotated_at=datetime.utcnow(),
    )


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Send a test webhook delivery."""
    webhook = await get_webhook_or_404(webhook_id, user, db)
    
    test_payload = {
        "event": "test",
        "webhook_id": str(webhook.id),
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"message": "This is a test webhook delivery"},
    }
    
    # Queue delivery in background
    async def deliver():
        await _deliver_webhook(webhook, "test", test_payload, db)
    
    background_tasks.add_task(deliver)
    
    return {
        "id": str(webhook.id),
        "status": "queued",
        "message": "Test delivery queued",
    }


async def _deliver_webhook(
    webhook: Webhook,
    event_type: str,
    payload: dict[str, Any],
    db: DbSession,
) -> WebhookDelivery:
    """Deliver a webhook payload."""
    start_time = datetime.utcnow()
    
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload=payload,
    )
    db.add(delivery)
    
    try:
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "NexusMind-Webhook/1.0",
            "X-Webhook-ID": str(webhook.id),
            "X-Event-Type": event_type,
        }
        
        # Add signature if configured
        if webhook.signature_header and webhook.secret_hash:
            body = json.dumps(payload)
            signature = hmac.new(
                webhook.secret_hash.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers[webhook.signature_header] = f"sha256={signature}"
        
        # Add custom headers
        if webhook.headers:
            headers.update(webhook.headers)
        
        # Send request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers,
            )
        
        # Update delivery record
        delivery.response_status = response.status_code
        delivery.response_body = response.text[:1000] if response.text else None
        delivery.delivered_at = datetime.utcnow()
        delivery.duration_ms = int(
            (delivery.delivered_at - start_time).total_seconds() * 1000
        )
        
        # Update webhook stats
        webhook.delivery_count += 1
        webhook.last_triggered = datetime.utcnow()
        
    except Exception as e:
        delivery.error = str(e)
        delivery.delivered_at = datetime.utcnow()
        delivery.duration_ms = int(
            (delivery.delivered_at - start_time).total_seconds() * 1000
        )
        
        # Update failure count
        webhook.failure_count += 1
        webhook.last_triggered = datetime.utcnow()
    
    await db.flush()
    return delivery


@router.post("/deliver", include_in_schema=False)
async def trigger_webhook(
    webhook_id: str,
    event_type: str,
    payload: dict[str, Any],
    db: DbSession,
) -> dict[str, Any]:
    """Internal endpoint to trigger webhook delivery.
    
    This is called by internal services to trigger webhooks.
    """
    try:
        webhook_uuid = uuid.UUID(webhook_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook ID format",
        )
    
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_uuid)
    )
    webhook = result.scalar_one_or_none()
    
    if webhook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    if not webhook.is_enabled:
        return {"status": "skipped", "message": "Webhook is disabled"}
    
    delivery = await _deliver_webhook(webhook, event_type, payload, db)
    
    return {
        "delivery_id": str(delivery.id),
        "status": "success" if not delivery.error else "failed",
        "response_status": delivery.response_status,
        "error": delivery.error,
    }
