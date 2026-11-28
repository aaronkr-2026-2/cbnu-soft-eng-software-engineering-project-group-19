"""Bind passkey credentials and challenges to the browser site origin."""

import os

from alembic import op
import sqlalchemy as sa
from dotenv import load_dotenv

revision = "2a5b7d9c1e31"
down_revision = "c5d92a6f1340"
branch_labels = None
depends_on = None


def upgrade() -> None:
    load_dotenv()
    legacy_rp_id = os.getenv("WEBAUTHN_RP_ID", "localhost")
    op.add_column("passkey_credentials", sa.Column("rp_id", sa.String(length=253), nullable=True))
    op.create_index("ix_passkey_credentials_rp_id", "passkey_credentials", ["rp_id"])
    op.execute(
        sa.text("UPDATE passkey_credentials SET rp_id = :rp_id WHERE rp_id IS NULL").bindparams(
            rp_id=legacy_rp_id
        )
    )
    op.add_column("passkey_challenges", sa.Column("rp_id", sa.String(length=253), nullable=True))
    op.add_column("passkey_challenges", sa.Column("origin", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("passkey_challenges", "origin")
    op.drop_column("passkey_challenges", "rp_id")
    op.drop_index("ix_passkey_credentials_rp_id", table_name="passkey_credentials")
    op.drop_column("passkey_credentials", "rp_id")
