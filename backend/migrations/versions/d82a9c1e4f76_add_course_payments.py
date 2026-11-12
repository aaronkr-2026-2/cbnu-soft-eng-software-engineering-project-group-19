"""Add paid course pricing and verified checkout records."""

from alembic import op
import sqlalchemy as sa


revision = "d82a9c1e4f76"
down_revision = "ab42e7e1c90d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("price_uzs", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("courses", "price_uzs", server_default=None)
    op.create_table(
        "course_payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("amount_uzs", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("external_id", sa.String(length=36), nullable=False),
        sa.Column("provider_token", sa.String(length=100), nullable=False),
        sa.Column("checkout_url", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_course_payments_external_id"),
    )
    op.create_index("ix_course_payments_user_id", "course_payments", ["user_id"])
    op.create_index("ix_course_payments_course_id", "course_payments", ["course_id"])


def downgrade() -> None:
    op.drop_index("ix_course_payments_course_id", table_name="course_payments")
    op.drop_index("ix_course_payments_user_id", table_name="course_payments")
    op.drop_table("course_payments")
    op.drop_column("courses", "price_uzs")
