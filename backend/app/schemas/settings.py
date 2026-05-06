"""Schemas Pydantic para configurações de LLM e WhatsApp."""

import uuid
from datetime import datetime

from app.models.credentials import LLMProvider, WhatsAppStatus
from app.schemas.common import APIModel


class LLMSettingsCreate(APIModel):
    provider: LLMProvider
    api_key: str
    default_model: str


class LLMSettingsResponse(APIModel):
    id: uuid.UUID
    provider: LLMProvider
    api_key_masked: str
    default_model: str
    is_active: bool
    updated_at: datetime


class WhatsAppSettingsCreate(APIModel):
    instance_id: str
    instance_token: str
    client_token: str
    phone_number: str | None = None


class WhatsAppSettingsResponse(APIModel):
    id: uuid.UUID
    instance_id: str
    instance_token: str
    has_client_token: bool
    phone_number: str | None = None
    status: WhatsAppStatus
    webhook_url: str
    updated_at: datetime


class WebhookSyncResponse(APIModel):
    success: bool
    detail: str
