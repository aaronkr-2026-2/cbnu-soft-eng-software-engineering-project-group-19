"""Add cached translations for course catalog metadata."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f1a8c72d9e30"
down_revision = "e8b3c0a1912f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "language", name="uq_course_translation_language"),
    )
    op.create_index("ix_course_translations_course_id", "course_translations", ["course_id"])


def downgrade() -> None:
    op.drop_index("ix_course_translations_course_id", table_name="course_translations")
    op.drop_table("course_translations")
