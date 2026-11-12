"""Add generated lesson banners and cached per-language translations."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e8b3c0a1912f"
down_revision = "d82a9c1e4f76"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("banner_key", sa.String(length=80), nullable=True))
    op.create_table(
        "lesson_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", "language", name="uq_lesson_translation_language"),
    )
    op.create_index("ix_lesson_translations_lesson_id", "lesson_translations", ["lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_lesson_translations_lesson_id", table_name="lesson_translations")
    op.drop_table("lesson_translations")
    op.drop_column("lessons", "banner_key")
