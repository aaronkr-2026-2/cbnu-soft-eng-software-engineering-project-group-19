"""Add course banner art, external videos, and tracked viewing time."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c5d92a6f1340"
down_revision = "b6c4e97a21fd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("banner_key", sa.String(length=80), nullable=True))
    op.add_column("lessons", sa.Column("external_video_url", sa.String(length=500), nullable=True))
    op.create_table(
        "video_watch_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watched_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("last_position_seconds", sa.Float(), nullable=False),
        sa.Column("last_reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_video_watch_user_lesson"),
    )
    op.create_index("ix_video_watch_progress_user_id", "video_watch_progress", ["user_id"])
    op.create_index("ix_video_watch_progress_lesson_id", "video_watch_progress", ["lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_video_watch_progress_lesson_id", table_name="video_watch_progress")
    op.drop_index("ix_video_watch_progress_user_id", table_name="video_watch_progress")
    op.drop_table("video_watch_progress")
    op.drop_column("lessons", "external_video_url")
    op.drop_column("courses", "banner_key")
