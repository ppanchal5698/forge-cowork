"""agent_runs.execution_arn — link a run to its Step Functions execution

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agent_runs", sa.Column("execution_arn", sa.Text, nullable=True))


def downgrade():
    op.drop_column("agent_runs", "execution_arn")
