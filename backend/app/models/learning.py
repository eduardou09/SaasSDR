import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class LearningItemType(str, enum.Enum):
    objection = "objection"
    edge_case = "edge_case"
    complaint = "complaint"
    success_pattern = "success_pattern"


class LearningItemStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"


class SupervisorRunStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"


class LearningInboxItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "learning_inbox"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    type: Mapped[LearningItemType] = mapped_column(
        Enum(LearningItemType, name="learningitemtype"), nullable=False
    )
    detected_text: Mapped[str] = mapped_column(Text, nullable=False)
    agent_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_improvement: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LearningItemStatus] = mapped_column(
        Enum(LearningItemStatus, name="learningitemstatus"),
        default=LearningItemStatus.pending,
        nullable=False,
        index=True,
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupervisorRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supervisor_runs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    conversations_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Insights gerados pelo Claude Sonnet: {patterns: [], failures: [], successes: []}
    findings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    proposed_prompt_changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SupervisorRunStatus] = mapped_column(
        Enum(SupervisorRunStatus, name="supervisorrunstatus"),
        default=SupervisorRunStatus.pending_review,
        nullable=False,
        index=True,
    )
    # Custo do Claude Sonnet nessa run (pago pelo Convo)
    llm_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)


class UsageRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "usage_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    # Mês de referência: primeiro dia do mês (ex: 2025-01-01)
    period_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversations_started: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads_qualified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
