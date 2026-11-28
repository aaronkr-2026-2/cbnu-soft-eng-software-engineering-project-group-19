"""Add optional learner profile fields."""

from alembic import op
import sqlalchemy as sa

revision = "a4f31c8d0b72"
down_revision = "7d63a8b90c41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "bio")
    op.drop_column("users", "age")
