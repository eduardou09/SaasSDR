import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class WebhookEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "webhook_events"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: "zapi", "clerk"
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # ID externo para deduplicação
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    # Payload completo do webhook (para debug e replay)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Erro caso o processamento tenha falhado
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
