"""Initial schema — todas as tabelas do Convo

Revision ID: 0001
Revises:
Create Date: 2026-05-04

Notas:
- Habilita pgvector para embeddings na knowledge base
- RLS em todas as tabelas com tenant_id (exceto tenants e users, usados no auth middleware)
- O usuário do banco em produção deve ter BYPASSRLS para que as migrations funcionem
- current_setting('app.current_tenant_id', true) usa missing_ok=true: retorna NULL
  se não setado → RLS bloqueia tudo (fail-safe)
- create_type=False em todos os sa.Enum: os tipos são gerenciados explicitamente
  pelos op.execute("CREATE TYPE ...") no início do upgrade()
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_ISOLATED_TABLES = [
    "tenant_members",
    "llm_credentials",
    "whatsapp_credentials",
    "agents",
    "agent_versions",
    "knowledge_base_items",
    "onboarding_sessions",
    "contacts",
    "conversations",
    "messages",
    "learning_inbox",
    "supervisor_runs",
    "webhook_events",
    "usage_records",
]


def _enum(*values: str, name: str) -> postgresql.ENUM:
    """
    Retorna um postgresql.ENUM com create_type=False.
    Os tipos são criados explicitamente pelos op.execute("CREATE TYPE ...") acima,
    então precisamos dizer ao SQLAlchemy para não tentar criá-los de novo.
    """
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # Extensions
    # -------------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # -------------------------------------------------------------------------
    # Enum types — criados explicitamente para controle total no downgrade
    # -------------------------------------------------------------------------
    op.execute("CREATE TYPE tenantplan AS ENUM ('trial', 'starter', 'growth', 'scale')")
    op.execute("CREATE TYPE tenantstatus AS ENUM ('active', 'suspended', 'cancelled')")
    op.execute("CREATE TYPE memberrole AS ENUM ('owner', 'admin', 'operator')")
    op.execute("CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic', 'google')")
    op.execute("CREATE TYPE whatsappstatus AS ENUM ('connected', 'disconnected', 'qr_pending')")
    op.execute("CREATE TYPE agentstatus AS ENUM ('draft', 'training', 'active', 'paused')")
    op.execute("CREATE TYPE leadstatus AS ENUM ('new', 'in_qualification', 'qualified', 'scheduled', 'won', 'lost')")
    op.execute("CREATE TYPE conversationstatus AS ENUM ('bot_active', 'human_active', 'paused', 'closed')")
    op.execute("CREATE TYPE conversationoutcome AS ENUM ('qualified', 'lost', 'no_response', 'handed_off')")
    op.execute("CREATE TYPE qualitylabel AS ENUM ('good', 'bad', 'neutral')")
    op.execute("CREATE TYPE messagedirection AS ENUM ('inbound', 'outbound')")
    op.execute("CREATE TYPE messagesendertype AS ENUM ('contact', 'agent', 'human')")
    op.execute("CREATE TYPE knowledgeitemtype AS ENUM ('pdf', 'text', 'faq', 'objection')")
    op.execute("CREATE TYPE onboardingstatus AS ENUM ('in_progress', 'completed', 'abandoned')")
    op.execute("CREATE TYPE learningitemtype AS ENUM ('objection', 'edge_case', 'complaint', 'success_pattern')")
    op.execute("CREATE TYPE learningitemstatus AS ENUM ('pending', 'approved', 'rejected', 'applied')")
    op.execute("CREATE TYPE supervisorrunstatus AS ENUM ('pending_review', 'approved', 'rejected', 'applied')")

    # -------------------------------------------------------------------------
    # tenants
    # -------------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("clerk_org_id", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("plan", _enum("trial", "starter", "growth", "scale", name="tenantplan"), nullable=False, server_default="trial"),
        sa.Column("status", _enum("active", "suspended", "cancelled", name="tenantstatus"), nullable=False, server_default="active"),
        sa.Column("trial_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_tenants_clerk_org_id", "tenants", ["clerk_org_id"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # -------------------------------------------------------------------------
    # users
    # -------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("clerk_user_id", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"])

    # -------------------------------------------------------------------------
    # tenant_members
    # -------------------------------------------------------------------------
    op.create_table(
        "tenant_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", _enum("owner", "admin", "operator", name="memberrole"), nullable=False, server_default="operator"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_members_tenant_user"),
    )
    op.create_index("ix_tenant_members_tenant_id", "tenant_members", ["tenant_id"])
    op.create_index("ix_tenant_members_user_id", "tenant_members", ["user_id"])

    # -------------------------------------------------------------------------
    # llm_credentials
    # -------------------------------------------------------------------------
    op.create_table(
        "llm_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", _enum("openai", "anthropic", "google", name="llmprovider"), nullable=False),
        sa.Column("api_key_encrypted", sa.String(1024), nullable=False),
        sa.Column("default_model", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_llm_credentials_tenant_id", "llm_credentials", ["tenant_id"])

    # -------------------------------------------------------------------------
    # whatsapp_credentials
    # -------------------------------------------------------------------------
    op.create_table(
        "whatsapp_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instance_id", sa.String(255), nullable=False),
        sa.Column("instance_token", sa.String(512), nullable=False),
        sa.Column("client_token_encrypted", sa.String(1024), nullable=False),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("status", _enum("connected", "disconnected", "qr_pending", name="whatsappstatus"), nullable=False, server_default="disconnected"),
        sa.Column("webhook_secret", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_whatsapp_credentials_tenant_id", "whatsapp_credentials", ["tenant_id"])

    # -------------------------------------------------------------------------
    # agents
    # -------------------------------------------------------------------------
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", _enum("draft", "training", "active", "paused", name="agentstatus"), nullable=False, server_default="draft"),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("qualification_schema", postgresql.JSONB, nullable=True),
        sa.Column("tone", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="pt-BR"),
        sa.Column("llm_provider", sa.String(50), nullable=True),
        sa.Column("llm_model", sa.String(255), nullable=True),
        sa.Column("temperature", sa.Float, nullable=False, server_default="0.7"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_agents_tenant_id", "agents", ["tenant_id"])
    op.create_index("ix_agents_status", "agents", ["status"])

    # -------------------------------------------------------------------------
    # agent_versions
    # -------------------------------------------------------------------------
    op.create_table(
        "agent_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("qualification_schema", postgresql.JSONB, nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])
    op.create_index("ix_agent_versions_tenant_id", "agent_versions", ["tenant_id"])

    # -------------------------------------------------------------------------
    # knowledge_base_items (com pgvector)
    # -------------------------------------------------------------------------
    op.create_table(
        "knowledge_base_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", _enum("pdf", "text", "faq", "objection", name="knowledgeitemtype"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_filename", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    # Adiciona coluna vector separadamente (tipo não suportado nativamente pelo sa.Column)
    op.execute("ALTER TABLE knowledge_base_items ADD COLUMN embedding vector(1536)")
    op.execute(
        "CREATE INDEX ix_knowledge_base_items_embedding "
        "ON knowledge_base_items USING hnsw (embedding vector_cosine_ops)"
    )
    op.create_index("ix_knowledge_base_items_agent_id", "knowledge_base_items", ["agent_id"])
    op.create_index("ix_knowledge_base_items_tenant_id", "knowledge_base_items", ["tenant_id"])

    # -------------------------------------------------------------------------
    # onboarding_sessions
    # -------------------------------------------------------------------------
    op.create_table(
        "onboarding_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", _enum("in_progress", "completed", "abandoned", name="onboardingstatus"), nullable=False, server_default="in_progress"),
        sa.Column("messages", postgresql.JSONB, nullable=True, server_default="[]"),
        sa.Column("extracted_data", postgresql.JSONB, nullable=True),
        sa.Column("llm_model", sa.String(100), nullable=False, server_default="claude-haiku-4-5-20251001"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_onboarding_sessions_tenant_id", "onboarding_sessions", ["tenant_id"])

    # -------------------------------------------------------------------------
    # contacts
    # -------------------------------------------------------------------------
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("lead_status", _enum("new", "in_qualification", "qualified", "scheduled", "won", "lost", name="leadstatus"), nullable=False, server_default="new"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("qualification_data", postgresql.JSONB, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "phone", name="uq_contacts_tenant_phone"),
    )
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_lead_status", "contacts", ["lead_status"])
    op.create_index("ix_contacts_last_message_at", "contacts", ["last_message_at"])

    # -------------------------------------------------------------------------
    # conversations
    # -------------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", _enum("bot_active", "human_active", "paused", "closed", name="conversationstatus"), nullable=False, server_default="bot_active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_messages", sa.Integer, nullable=False, server_default="0"),
        sa.Column("outcome", _enum("qualified", "lost", "no_response", "handed_off", name="conversationoutcome"), nullable=True),
        sa.Column("quality_label", _enum("good", "bad", "neutral", name="qualitylabel"), nullable=True),
        sa.Column("channel", sa.String(50), nullable=False, server_default="whatsapp"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"])
    op.create_index("ix_conversations_contact_id", "conversations", ["contact_id"])
    op.create_index("ix_conversations_status", "conversations", ["status"])
    op.create_index("ix_conversations_started_at", "conversations", ["started_at"])
    op.create_index("ix_conversations_quality_label", "conversations", ["quality_label"])

    # -------------------------------------------------------------------------
    # messages
    # -------------------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_message_id", sa.String(255), nullable=True),
        sa.Column("direction", _enum("inbound", "outbound", name="messagedirection"), nullable=False),
        sa.Column("sender_type", _enum("contact", "agent", "human", name="messagesendertype"), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("media_url", sa.String(1024), nullable=True),
        sa.Column("media_type", sa.String(100), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("llm_input_tokens", sa.Integer, nullable=True),
        sa.Column("llm_output_tokens", sa.Integer, nullable=True),
        sa.Column("llm_cost_usd", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "external_message_id", name="uq_messages_tenant_external"),
    )
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sent_at", "messages", ["sent_at"])
    op.create_index("ix_messages_direction", "messages", ["direction"])

    # -------------------------------------------------------------------------
    # learning_inbox
    # -------------------------------------------------------------------------
    op.create_table(
        "learning_inbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", _enum("objection", "edge_case", "complaint", "success_pattern", name="learningitemtype"), nullable=False),
        sa.Column("detected_text", sa.Text, nullable=False),
        sa.Column("agent_response", sa.Text, nullable=True),
        sa.Column("suggested_improvement", sa.Text, nullable=True),
        sa.Column("status", _enum("pending", "approved", "rejected", "applied", name="learningitemstatus"), nullable=False, server_default="pending"),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_learning_inbox_tenant_id", "learning_inbox", ["tenant_id"])
    op.create_index("ix_learning_inbox_agent_id", "learning_inbox", ["agent_id"])
    op.create_index("ix_learning_inbox_status", "learning_inbox", ["status"])

    # -------------------------------------------------------------------------
    # supervisor_runs
    # -------------------------------------------------------------------------
    op.create_table(
        "supervisor_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("conversations_analyzed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("findings", postgresql.JSONB, nullable=True),
        sa.Column("proposed_prompt_changes", sa.Text, nullable=True),
        sa.Column("status", _enum("pending_review", "approved", "rejected", "applied", name="supervisorrunstatus"), nullable=False, server_default="pending_review"),
        sa.Column("llm_cost_usd", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_supervisor_runs_tenant_id", "supervisor_runs", ["tenant_id"])
    op.create_index("ix_supervisor_runs_agent_id", "supervisor_runs", ["agent_id"])
    op.create_index("ix_supervisor_runs_status", "supervisor_runs", ["status"])

    # -------------------------------------------------------------------------
    # webhook_events
    # -------------------------------------------------------------------------
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_webhook_events_tenant_id", "webhook_events", ["tenant_id"])
    op.create_index("ix_webhook_events_event_type", "webhook_events", ["event_type"])
    op.create_index("ix_webhook_events_external_id", "webhook_events", ["external_id"])

    # -------------------------------------------------------------------------
    # usage_records
    # -------------------------------------------------------------------------
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_month", sa.Date, nullable=False),
        sa.Column("messages_sent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("messages_received", sa.Integer, nullable=False, server_default="0"),
        sa.Column("conversations_started", sa.Integer, nullable=False, server_default="0"),
        sa.Column("leads_qualified", sa.Integer, nullable=False, server_default="0"),
        sa.Column("llm_cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "period_month", name="uq_usage_records_tenant_month"),
    )
    op.create_index("ix_usage_records_tenant_id", "usage_records", ["tenant_id"])
    op.create_index("ix_usage_records_period_month", "usage_records", ["period_month"])

    # -------------------------------------------------------------------------
    # RLS
    # -------------------------------------------------------------------------
    for table in TENANT_ISOLATED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        """)

    # -------------------------------------------------------------------------
    # Trigger de updated_at automático
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    for table in ["tenants", "users"] + TENANT_ISOLATED_TABLES:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)


def downgrade() -> None:
    tables_to_drop = [
        "usage_records", "webhook_events", "supervisor_runs", "learning_inbox",
        "messages", "conversations", "contacts", "onboarding_sessions",
        "knowledge_base_items", "agent_versions", "agents",
        "whatsapp_credentials", "llm_credentials", "tenant_members", "users", "tenants",
    ]
    for table in tables_to_drop:
        op.drop_table(table)

    for enum_name in [
        "supervisorrunstatus", "learningitemstatus", "learningitemtype",
        "onboardingstatus", "knowledgeitemtype", "messagesendertype",
        "messagedirection", "qualitylabel", "conversationoutcome",
        "conversationstatus", "leadstatus", "agentstatus", "whatsappstatus",
        "llmprovider", "memberrole", "tenantstatus", "tenantplan",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
