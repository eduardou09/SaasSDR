import enum
import uuid

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]

    VECTOR_TYPE = Vector(1536)
except ImportError:
    # Fallback para quando pgvector não está instalado (ex: build de CI sem a extension)
    from sqlalchemy import JSON

    VECTOR_TYPE = JSON  # type: ignore[assignment]


class KnowledgeItemType(str, enum.Enum):
    pdf = "pdf"
    text = "text"
    faq = "faq"
    objection = "objection"


class KnowledgeBaseItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_base_items"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    type: Mapped[KnowledgeItemType] = mapped_column(
        Enum(KnowledgeItemType, name="knowledgeitemtype"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Embedding gerado via OpenAI text-embedding-3-small (1536 dims)
    # Usado para busca semântica (RAG) — nullable enquanto o worker processa
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR_TYPE, nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
