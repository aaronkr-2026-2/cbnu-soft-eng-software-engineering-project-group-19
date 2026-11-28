"""Add optional explanations to lesson quiz questions."""

from alembic import op
import sqlalchemy as sa


revision = "44d092c36e7f"
down_revision = "c7d4e2a910bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quiz_questions", sa.Column("explanation", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("quiz_questions", "explanation")
