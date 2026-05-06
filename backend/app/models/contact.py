import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class LeadStatus(str, enum.Enum):
    new = "new"
    in_qualification = "in_qualification"
    qualified = "qualified"
    scheduled = "scheduled"
    won = "won"
    lost = "lost"


class Contact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contacts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lead_status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="leadstatus"),
        default=LeadStatus.new,
        nullable=False,
        index=True,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Dados de qualificação capturados pelo agente: {campo: valor}
    qualification_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    # Usuário responsável quando em handoff humano
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
