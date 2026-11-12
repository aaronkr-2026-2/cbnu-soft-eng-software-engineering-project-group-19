"""Track viewing progress for every video in an embedded YouTube playlist."""

from alembic import op
import sqlalchemy as sa

revision = "d3e9c701f4a2"
down_revision = "2a5b7d9c1e31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "video_watch_progress",
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "video_watch_progress",
        sa.Column("item_progress", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("video_watch_progress", "item_progress")
    op.drop_column("video_watch_progress", "item_count")
