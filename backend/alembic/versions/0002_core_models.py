"""core models: users, tasks, agent_runs, artifacts (tenant_id + index on every table)

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _id():
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _tenant_id():
    return sa.Column(
        "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False
    )


def _created_at():
    return sa.Column(
        "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")
    )


def upgrade():
    op.create_table(
        "users",
        _id(),
        _tenant_id(),
        sa.Column("email", sa.Text, nullable=False, unique=True),
        sa.Column("cognito_sub", sa.Text, nullable=False, unique=True),
        _created_at(),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    op.create_table(
        "tasks",
        _id(),
        _tenant_id(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        _created_at(),
    )
    op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"])

    op.create_table(
        "agent_runs",
        _id(),
        _tenant_id(),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="queued"),
        sa.Column("step", sa.Text, nullable=True),
        sa.Column("output_key", sa.Text, nullable=True),
        _created_at(),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index("ix_agent_runs_tenant_id", "agent_runs", ["tenant_id"])

    op.create_table(
        "artifacts",
        _id(),
        _tenant_id(),
        sa.Column(
            "run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id"), nullable=False
        ),
        sa.Column("s3_key", sa.Text, nullable=False),
        _created_at(),
    )
    op.create_index("ix_artifacts_tenant_id", "artifacts", ["tenant_id"])


def downgrade():
    for table in ("artifacts", "agent_runs", "tasks", "users"):
        op.drop_table(table)
