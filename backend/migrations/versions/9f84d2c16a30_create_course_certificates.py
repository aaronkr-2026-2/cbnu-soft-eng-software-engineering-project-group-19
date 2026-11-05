"""create course certificates

Revision ID: 9f84d2c16a30
Revises: 4d738aa921c1
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f84d2c16a30"
down_revision: Union[str, Sequence[str], None] = "4d738aa921c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_certificates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("course_title", sa.String(length=200), nullable=False),
        sa.Column("certificate_code", sa.String(length=40), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("certificate_code"),
        sa.UniqueConstraint("user_id", "course_id", name="uq_course_certificates_user_course"),
    )
    op.create_index(op.f("ix_course_certificates_course_id"), "course_certificates", ["course_id"], unique=False)
    op.create_index(op.f("ix_course_certificates_user_id"), "course_certificates", ["user_id"], unique=False)
    op.create_index(op.f("ix_course_certificates_certificate_code"), "course_certificates", ["certificate_code"], unique=True)
    op.create_table(
        "final_exam_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("score_percent", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_final_exam_attempts_course_id"), "final_exam_attempts", ["course_id"], unique=False)
    op.create_index(op.f("ix_final_exam_attempts_user_id"), "final_exam_attempts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_final_exam_attempts_user_id"), table_name="final_exam_attempts")
    op.drop_index(op.f("ix_final_exam_attempts_course_id"), table_name="final_exam_attempts")
    op.drop_table("final_exam_attempts")
    op.drop_index(op.f("ix_course_certificates_certificate_code"), table_name="course_certificates")
    op.drop_index(op.f("ix_course_certificates_user_id"), table_name="course_certificates")
    op.drop_index(op.f("ix_course_certificates_course_id"), table_name="course_certificates")
    op.drop_table("course_certificates")
