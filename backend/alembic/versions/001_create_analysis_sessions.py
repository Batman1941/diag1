"""create analysis_sessions

Revision ID: 001_create_analysis_sessions
Revises: 
Create Date: 2026-02-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_create_analysis_sessions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.Enum("created", "processing", "completed", "deleted", "failed", name="sessionstatus"), nullable=False),
        sa.Column("consent_terms", sa.Boolean(), nullable=False),
        sa.Column("consent_health_data", sa.Boolean(), nullable=False),
        sa.Column("consent_ai", sa.Boolean(), nullable=False),
        sa.Column("report_markdown", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("client_id", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("analysis_sessions")
    op.execute("DROP TYPE sessionstatus")
