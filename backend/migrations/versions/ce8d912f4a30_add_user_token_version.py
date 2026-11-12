"""Add a version counter to revoke access tokens after password changes."""

from alembic import op
import sqlalchemy as sa

revision = "ce8d912f4a30"
down_revision = "b82a601cf4d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("users", "token_version", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "token_version")
