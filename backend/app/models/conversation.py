import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConversationStatus(str, enum.Enum):
    bot_active = "bot_active"
    human_active = "human_active"
    paused = "paused"
    closed = "closed"


class ConversationOutcome(str, enum.Enum):
    qualified = "qualified"
    lost = "lost"
    no_response = "no_response"
    handed_off = "handed_off"


class QualityLabel(str, enum.Enum):
    good = "good"
    bad = "bad"
    neutral = "neutral"


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversationstatus"),
        default=ConversationStatus.bot_active,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outcome: Mapped[ConversationOutcome | None] = mapped_column(
        Enum(ConversationOutcome, name="conversationoutcome"), nullable=True
    )
    # Setado pelo worker de feedback implícito (sub-módulo 8.1)
    quality_label: Mapped[QualityLabel | None] = mapped_column(
        Enum(QualityLabel, name="qualitylabel"), nullable=True, index=True
    )
    # Canal (ex: whatsapp) — extensível para outros canais no futuro
    channel: Mapped[str] = mapped_column(String(50), default="whatsapp", nullable=False)
