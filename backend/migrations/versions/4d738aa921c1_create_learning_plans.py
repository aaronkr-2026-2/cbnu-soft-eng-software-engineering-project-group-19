"""create personalized learning plans

Revision ID: 4d738aa921c1
Revises: 29ad41e7c2b1
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d738aa921c1"
down_revision: Union[str, Sequence[str], None] = "29ad41e7c2b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("weekly_study_days", sa.Integer(), nullable=False),
        sa.Column("session_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_weeks", sa.Integer(), nullable=False),
        sa.Column("plan_data", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_plans_course_id"), "learning_plans", ["course_id"], unique=False)
    op.create_index(op.f("ix_learning_plans_user_id"), "learning_plans", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_plans_user_id"), table_name="learning_plans")
    op.drop_index(op.f("ix_learning_plans_course_id"), table_name="learning_plans")
    op.drop_table("learning_plans")
