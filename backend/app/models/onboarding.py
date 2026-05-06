import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class OnboardingStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class OnboardingSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "onboarding_sessions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    # agent_id é preenchido quando a sessão de onboarding cria o agente
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[OnboardingStatus] = mapped_column(
        Enum(OnboardingStatus, name="onboardingstatus"),
        default=OnboardingStatus.in_progress,
        nullable=False,
    )
    # Array de mensagens: [{role: "user"|"assistant", content: "..."}]
    messages: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    # Dados extraídos ao final: {system_prompt, qualification_schema, objection_responses}
    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Modelo usado no onboarder (Claude Haiku 4.5 by default)
    llm_model: Mapped[str] = mapped_column(
        String(100), default="claude-haiku-4-5-20251001", nullable=False
    )
