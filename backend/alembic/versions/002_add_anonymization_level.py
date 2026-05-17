"""add anonymization_level

Revision ID: 002_add_anonymization_level
Revises: 001_create_analysis_sessions
Create Date: 2026-02-03 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_anonymization_level"
down_revision = "001_create_analysis_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analysis_sessions",
        sa.Column("anonymization_level", sa.String(length=16), nullable=False, server_default="full"),
    )


def downgrade() -> None:
    op.drop_column("analysis_sessions", "anonymization_level")
