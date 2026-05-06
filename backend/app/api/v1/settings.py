"""Endpoints de configuração — LLM e WhatsApp credentials."""

import secrets
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.crypto import decrypt, encrypt, mask
from app.core.db import TenantDB
from app.config import settings
from app.models.credentials import LLMCredentials, WhatsAppCredentials, WhatsAppStatus
from app.schemas.settings import (
    LLMSettingsCreate,
    LLMSettingsResponse,
    WebhookSyncResponse,
    WhatsAppSettingsCreate,
    WhatsAppSettingsResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _build_webhook_url(tenant_id: uuid.UUID, secret: str) -> str:
    return f"{settings.api_public_base_url}/api/v1/webhooks/zapi/{tenant_id}/{secret}"


def _validate_webhook_url(url: str) -> None:
    if "localhost" in url or "127.0.0.1" in url:
        raise HTTPException(
            status_code=400,
            detail=(
                "Webhook URL está local. Defina API_PUBLIC_BASE_URL com domínio público HTTPS "
                "para a Z-API conseguir entregar eventos."
            ),
        )
    if not url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail="Webhook URL precisa ser HTTPS para a Z-API.",
        )

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


@router.get("/llm", response_model=list[LLMSettingsResponse])
async def list_llm(request: Request, db: TenantDB) -> list[LLMSettingsResponse]:
    creds = (
        await db.execute(
            select(LLMCredentials).where(LLMCredentials.tenant_id == request.state.tenant_id)
        )
    ).scalars().all()
    return [
        LLMSettingsResponse(
            id=c.id,
            provider=c.provider,
            api_key_masked=mask(decrypt(c.api_key_encrypted)),
            default_model=c.default_model,
            is_active=c.is_active,
            updated_at=c.updated_at,
        )
        for c in creds
    ]


@router.post("/llm", response_model=LLMSettingsResponse, status_code=201)
async def upsert_llm(
    body: LLMSettingsCreate, request: Request, db: TenantDB
) -> LLMSettingsResponse:
    tid = request.state.tenant_id
    existing = (
        await db.execute(
            select(LLMCredentials).where(
                LLMCredentials.tenant_id == tid,
                LLMCredentials.provider == body.provider,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.api_key_encrypted = encrypt(body.api_key)
        existing.default_model = body.default_model
        existing.is_active = True
        await db.flush()
        await db.refresh(existing)
        c = existing
    else:
        c = LLMCredentials(
            tenant_id=tid,
            provider=body.provider,
            api_key_encrypted=encrypt(body.api_key),
            default_model=body.default_model,
        )
        db.add(c)
        await db.flush()
        await db.refresh(c)

    return LLMSettingsResponse(
        id=c.id,
        provider=c.provider,
        api_key_masked=mask(decrypt(c.api_key_encrypted)),
        default_model=c.default_model,
        is_active=c.is_active,
        updated_at=c.updated_at,
    )


@router.delete("/llm/{cred_id}", status_code=204)
async def delete_llm(cred_id: uuid.UUID, request: Request, db: TenantDB) -> None:
    c = (
        await db.execute(
            select(LLMCredentials).where(
                LLMCredentials.id == cred_id,
                LLMCredentials.tenant_id == request.state.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Credencial não encontrada")
    await db.delete(c)


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------


@router.get("/whatsapp", response_model=Optional[WhatsAppSettingsResponse])
async def get_whatsapp(
    request: Request, db: TenantDB
) -> Optional[WhatsAppSettingsResponse]:
    creds = (
        await db.execute(
            select(WhatsAppCredentials).where(
                WhatsAppCredentials.tenant_id == request.state.tenant_id
            )
        )
    ).scalar_one_or_none()
    if not creds:
        return None
    return WhatsAppSettingsResponse(
        id=creds.id,
        instance_id=creds.instance_id,
        instance_token=creds.instance_token,
        has_client_token=bool(creds.client_token_encrypted),
        phone_number=creds.phone_number,
        status=creds.status,
        webhook_url=_build_webhook_url(request.state.tenant_id, creds.webhook_secret),
        updated_at=creds.updated_at,
    )


@router.post("/whatsapp", response_model=WhatsAppSettingsResponse, status_code=201)
async def upsert_whatsapp(
    body: WhatsAppSettingsCreate, request: Request, db: TenantDB
) -> WhatsAppSettingsResponse:
    tid = request.state.tenant_id
    existing = (
        await db.execute(
            select(WhatsAppCredentials).where(WhatsAppCredentials.tenant_id == tid)
        )
    ).scalar_one_or_none()

    if existing:
        existing.instance_id = body.instance_id
        if body.instance_token.strip():
            existing.instance_token = body.instance_token
        if body.client_token.strip():
            existing.client_token_encrypted = encrypt(body.client_token)
        # MVP: ao salvar credenciais válidas, marca como conectado.
        # Em sprint de integração Z-API, substituir por validação ativa via endpoint de status.
        existing.status = WhatsAppStatus.connected
        if body.phone_number is not None:
            existing.phone_number = body.phone_number
        await db.flush()
        await db.refresh(existing)
        return WhatsAppSettingsResponse(
            id=existing.id,
            instance_id=existing.instance_id,
            instance_token=existing.instance_token,
            has_client_token=bool(existing.client_token_encrypted),
            phone_number=existing.phone_number,
            status=existing.status,
            webhook_url=_build_webhook_url(request.state.tenant_id, existing.webhook_secret),
            updated_at=existing.updated_at,
        )

    c = WhatsAppCredentials(
        tenant_id=tid,
        instance_id=body.instance_id,
        instance_token=body.instance_token,
        client_token_encrypted=encrypt(body.client_token),
        phone_number=body.phone_number,
        status=WhatsAppStatus.connected,
        webhook_secret=secrets.token_hex(32),
    )
    db.add(c)
    await db.flush()
    await db.refresh(c)
    return WhatsAppSettingsResponse(
        id=c.id,
        instance_id=c.instance_id,
        instance_token=c.instance_token,
        has_client_token=bool(c.client_token_encrypted),
        phone_number=c.phone_number,
        status=c.status,
        webhook_url=_build_webhook_url(request.state.tenant_id, c.webhook_secret),
        updated_at=c.updated_at,
    )


@router.post("/whatsapp/sync-webhook", response_model=WebhookSyncResponse)
async def sync_whatsapp_webhook(
    request: Request, db: TenantDB
) -> WebhookSyncResponse:
    creds = (
        await db.execute(
            select(WhatsAppCredentials).where(
                WhatsAppCredentials.tenant_id == request.state.tenant_id
            )
        )
    ).scalar_one_or_none()
    if not creds:
        raise HTTPException(status_code=404, detail="Credencial de WhatsApp não encontrada")

    webhook_url = _build_webhook_url(request.state.tenant_id, creds.webhook_secret)
    _validate_webhook_url(webhook_url)
    client_token = decrypt(creds.client_token_encrypted)

    zapi_url = (
        f"{settings.zapi_base_url}/instances/{creds.instance_id}/token/"
        f"{creds.instance_token}/update-every-webhooks"
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.put(
                zapi_url,
                headers={
                    "Client-Token": client_token,
                    "Content-Type": "application/json",
                },
                json={"value": webhook_url, "notifySentByMe": True},
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede com Z-API: {e}") from e

    if res.status_code >= 400:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao sincronizar webhook na Z-API: {res.text}",
        )

    return WebhookSyncResponse(
        success=True,
        detail="Webhook sincronizado com sucesso na Z-API.",
    )
