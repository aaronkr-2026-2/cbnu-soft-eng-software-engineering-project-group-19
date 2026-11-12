"""add course reviews

Revision ID: 7d63a8b90c41
Revises: c1a4b9e72d30
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7d63a8b90c41"
down_revision: Union[str, Sequence[str], None] = "c1a4b9e72d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "course_id", name="uq_course_reviews_user_course"),
    )
    op.create_index(op.f("ix_course_reviews_course_id"), "course_reviews", ["course_id"], unique=False)
    op.create_index(op.f("ix_course_reviews_user_id"), "course_reviews", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_course_reviews_user_id"), table_name="course_reviews")
    op.drop_index(op.f("ix_course_reviews_course_id"), table_name="course_reviews")
    op.drop_table("course_reviews")
