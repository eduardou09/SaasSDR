"""Webhooks públicos (Z-API)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.credentials import WhatsAppCredentials
from app.models.webhook import WebhookEvent

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/zapi/{tenant_id}/{secret}")
async def zapi_webhook(
    tenant_id: uuid.UUID,
    secret: str,
    request: Request,
) -> dict[str, str]:
    payload = await request.json()

    async with AsyncSessionLocal() as db:
        creds = (
            await db.execute(
                select(WhatsAppCredentials).where(
                    WhatsAppCredentials.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        if not creds:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        if creds.webhook_secret != secret:
            raise HTTPException(status_code=401, detail="Webhook secret inválido")

        event = WebhookEvent(
            tenant_id=tenant_id,
            provider="zapi",
            event_type=str(payload.get("type", "unknown")),
            external_id=str(payload.get("messageId", payload.get("id", ""))) or None,
            payload=payload,
            processed_at=datetime.now(UTC),
        )
        db.add(event)
        await db.commit()

    return {"status": "ok"}
