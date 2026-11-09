"""Add modules and optional lesson grouping to courses."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f8a42c19d763"
down_revision = "d3e9c701f4a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_course_modules_course_id", "course_modules", ["course_id"])
    op.create_table(
        "course_module_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["course_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", "language", name="uq_course_module_translation_language"),
    )
    op.create_index("ix_course_module_translations_module_id", "course_module_translations", ["module_id"])
    op.add_column("lessons", sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])
    op.create_foreign_key(
        "fk_lessons_module_id_course_modules",
        "lessons",
        "course_modules",
        ["module_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_index("ix_lessons_module_id", table_name="lessons")
    op.drop_constraint("fk_lessons_module_id_course_modules", "lessons", type_="foreignkey")
    op.drop_column("lessons", "module_id")
    op.drop_index("ix_course_module_translations_module_id", table_name="course_module_translations")
    op.drop_table("course_module_translations")
    op.drop_index("ix_course_modules_course_id", table_name="course_modules")
    op.drop_table("course_modules")
