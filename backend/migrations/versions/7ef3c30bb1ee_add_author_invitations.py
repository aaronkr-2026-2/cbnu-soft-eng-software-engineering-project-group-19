"""Store email-bound, single-use author invitations."""

import sqlalchemy as sa
from alembic import op

revision = "7ef3c30bb1ee"
down_revision = "31cce79aa285"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "author_invitations",
        sa.Column("token_digest", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table("author_invitations")
