"""Add ordered supplemental materials to lessons."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c7d4e2a910bf"
down_revision = "a3c71d8e5f42"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("resource_type", sa.String(length=16), nullable=False),
        sa.Column("resource_key", sa.String(length=80), nullable=False),
        sa.Column("resource_mime_type", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_key"),
    )
    op.create_index("ix_lesson_materials_lesson_id", "lesson_materials", ["lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_lesson_materials_lesson_id", table_name="lesson_materials")
    op.drop_table("lesson_materials")
