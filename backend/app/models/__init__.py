"""
Importa todos os models para que o Alembic autogenerate detecte as tabelas.
A ordem de importação não importa para autogenerate, mas importa para o app.
"""

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.tenant import Tenant, TenantMember, TenantPlan, TenantStatus
from app.models.user import User
from app.models.credentials import LLMCredentials, LLMProvider, WhatsAppCredentials, WhatsAppStatus
from app.models.agent import Agent, AgentStatus, AgentVersion
from app.models.agent_log import AgentEventLog
from app.models.contact import Contact, LeadStatus
from app.models.conversation import Conversation, ConversationOutcome, ConversationStatus, QualityLabel
from app.models.message import Message, MessageDirection, MessageSenderType
from app.models.knowledge import KnowledgeBaseItem, KnowledgeItemType
from app.models.onboarding import OnboardingSession, OnboardingStatus
from app.models.learning import (
    LearningInboxItem,
    LearningItemStatus,
    LearningItemType,
    SupervisorRun,
    SupervisorRunStatus,
    UsageRecord,
)
from app.models.webhook import WebhookEvent

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "Tenant",
    "TenantMember",
    "TenantPlan",
    "TenantStatus",
    "User",
    "LLMCredentials",
    "LLMProvider",
    "WhatsAppCredentials",
    "WhatsAppStatus",
    "Agent",
    "AgentStatus",
    "AgentVersion",
    "AgentEventLog",
    "Contact",
    "LeadStatus",
    "Conversation",
    "ConversationOutcome",
    "ConversationStatus",
    "QualityLabel",
    "Message",
    "MessageDirection",
    "MessageSenderType",
    "KnowledgeBaseItem",
    "KnowledgeItemType",
    "OnboardingSession",
    "OnboardingStatus",
    "LearningInboxItem",
    "LearningItemStatus",
    "LearningItemType",
    "SupervisorRun",
    "SupervisorRunStatus",
    "UsageRecord",
    "WebhookEvent",
]
