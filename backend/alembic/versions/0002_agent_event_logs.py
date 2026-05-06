"""Add agent_event_logs table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_event_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_agent_event_logs_tenant_id", "agent_event_logs", ["tenant_id"])
    op.create_index("ix_agent_event_logs_agent_id", "agent_event_logs", ["agent_id"])
    op.create_index("ix_agent_event_logs_event_type", "agent_event_logs", ["event_type"])
    op.create_index("ix_agent_event_logs_created_at", "agent_event_logs", ["created_at"])

    op.execute("ALTER TABLE agent_event_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agent_event_logs FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON agent_event_logs
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_agent_event_logs_updated_at
        BEFORE UPDATE ON agent_event_logs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """
    )


def downgrade() -> None:
    op.drop_table("agent_event_logs")
