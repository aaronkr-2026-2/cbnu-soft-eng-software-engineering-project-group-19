"""Separate learner and author accounts."""

from alembic import op
import sqlalchemy as sa

revision = "f09ab32c18de"
down_revision = "ce8d912f4a30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("account_type", sa.String(length=16), nullable=False, server_default="learner"),
    )
    op.execute(
        "UPDATE users SET account_type = 'author' "
        "WHERE id IN (SELECT DISTINCT owner_id FROM courses)"
    )
    op.alter_column("users", "account_type", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "account_type")
