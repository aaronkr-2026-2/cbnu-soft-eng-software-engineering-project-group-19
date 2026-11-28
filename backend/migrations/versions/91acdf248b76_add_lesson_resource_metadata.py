"""Add media metadata to course lessons."""

from alembic import op
import sqlalchemy as sa

revision = "91acdf248b76"
down_revision = "f09ab32c18de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("resource_type", sa.String(length=16), nullable=False, server_default="text"),
    )
    op.add_column("lessons", sa.Column("resource_key", sa.String(length=80), nullable=True))
    op.add_column("lessons", sa.Column("resource_mime_type", sa.String(length=100), nullable=True))
    op.alter_column("lessons", "resource_type", server_default=None)


def downgrade() -> None:
    op.drop_column("lessons", "resource_mime_type")
    op.drop_column("lessons", "resource_key")
    op.drop_column("lessons", "resource_type")
