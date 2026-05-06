import enum
import uuid

from sqlalchemy import Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentStatus(str, enum.Enum):
    draft = "draft"
    training = "training"
    active = "active"
    paused = "paused"


class Agent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agentstatus"),
        default=AgentStatus.draft,
        nullable=False,
        index=True,
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Schema de qualificação: {fields: [{name, type, question, required}]}
    qualification_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="pt-BR", nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    # Incrementado a cada edição do prompt (rastreabilidade)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class AgentVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_versions"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    qualification_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    change_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
