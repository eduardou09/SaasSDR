import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class LLMProvider(str, enum.Enum):
    openai = "openai"
    anthropic = "anthropic"
    google = "google"


class WhatsAppStatus(str, enum.Enum):
    connected = "connected"
    disconnected = "disconnected"
    qr_pending = "qr_pending"


class LLMCredentials(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "llm_credentials"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    provider: Mapped[LLMProvider] = mapped_column(
        Enum(LLMProvider, name="llmprovider"), nullable=False
    )
    # Chave criptografada com Fernet — nunca exposta em logs ou respostas de API
    api_key_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)
    default_model: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WhatsAppCredentials(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "whatsapp_credentials"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    instance_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # instance_token é public — não precisa de criptografia
    instance_token: Mapped[str] = mapped_column(String(512), nullable=False)
    # client_token é sensível — criptografado
    client_token_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[WhatsAppStatus] = mapped_column(
        Enum(WhatsAppStatus, name="whatsappstatus"),
        default=WhatsAppStatus.disconnected,
        nullable=False,
    )
    # Secret único por tenant para validar webhooks Z-API
    webhook_secret: Mapped[str] = mapped_column(String(128), nullable=False)
