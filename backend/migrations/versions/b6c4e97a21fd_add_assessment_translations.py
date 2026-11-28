"""Cache localized quiz and final exam content."""

from alembic import op
import sqlalchemy as sa


revision = "b6c4e97a21fd"
down_revision = "a47d1c86e502"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lesson_translations", sa.Column("quiz_content", sa.JSON(), nullable=True))
    op.add_column("course_translations", sa.Column("final_exam_content", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("course_translations", "final_exam_content")
    op.drop_column("lesson_translations", "quiz_content")
