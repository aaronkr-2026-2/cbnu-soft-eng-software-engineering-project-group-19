"""Allow learners to remove courses from their active learning list."""

import sqlalchemy as sa
from alembic import op

revision = "31cce79aa285"
down_revision = "92f3ab46c18d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "enrollments",
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("enrollments", "is_hidden")
