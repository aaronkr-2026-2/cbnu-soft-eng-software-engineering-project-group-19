"""Add localized course categories."""

from alembic import op
import sqlalchemy as sa


revision = "a47d1c86e502"
down_revision = "f1a8c72d9e30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("course_translations", sa.Column("category", sa.String(length=100), nullable=False, server_default=""))
    op.alter_column("course_translations", "category", server_default=None)


def downgrade() -> None:
    op.drop_column("course_translations", "category")
