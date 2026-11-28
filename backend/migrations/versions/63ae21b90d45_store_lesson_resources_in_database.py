"""Store uploaded lesson resources in the database."""

from alembic import op
import sqlalchemy as sa


revision = "63ae21b90d45"
down_revision = "44d092c36e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_resource_files",
        sa.Column("key", sa.String(length=80), primary_key=True),
        sa.Column("size", sa.Integer(), nullable=False),
    )
    op.create_table(
        "lesson_resource_chunks",
        sa.Column(
            "file_key",
            sa.String(length=80),
            sa.ForeignKey("lesson_resource_files.key", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("data", sa.LargeBinary(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("lesson_resource_chunks")
    op.drop_table("lesson_resource_files")
