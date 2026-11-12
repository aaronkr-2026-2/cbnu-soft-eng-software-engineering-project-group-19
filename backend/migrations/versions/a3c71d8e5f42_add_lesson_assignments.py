"""Add lesson assignments and learner submissions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a3c71d8e5f42"
down_revision = "f8a42c19d763"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("max_score", sa.Integer(), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id"),
    )
    op.create_table(
        "assignment_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="submitted", nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["lesson_assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", "user_id", name="uq_assignment_submission_user"),
    )
    op.create_index("ix_assignment_submissions_assignment_id", "assignment_submissions", ["assignment_id"])
    op.create_index("ix_assignment_submissions_user_id", "assignment_submissions", ["user_id"])
    op.create_table(
        "assignment_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["lesson_assignments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", "language", name="uq_assignment_translation_language"),
    )
    op.create_index("ix_assignment_translations_assignment_id", "assignment_translations", ["assignment_id"])


def downgrade() -> None:
    op.drop_index("ix_assignment_translations_assignment_id", table_name="assignment_translations")
    op.drop_table("assignment_translations")
    op.drop_index("ix_assignment_submissions_user_id", table_name="assignment_submissions")
    op.drop_index("ix_assignment_submissions_assignment_id", table_name="assignment_submissions")
    op.drop_table("assignment_submissions")
    op.drop_table("lesson_assignments")
