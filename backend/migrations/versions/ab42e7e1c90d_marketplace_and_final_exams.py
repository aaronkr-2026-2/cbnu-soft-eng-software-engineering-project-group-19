"""Add marketplace subjects, author-managed final exams, and certificate grades."""

from alembic import op
import sqlalchemy as sa


revision = "ab42e7e1c90d"
down_revision = "91acdf248b76"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("category", sa.String(length=100), nullable=False, server_default="General"))
    op.alter_column("courses", "category", server_default=None)
    op.add_column("course_certificates", sa.Column("score_percent", sa.Float(), nullable=False, server_default="0"))
    op.add_column("course_certificates", sa.Column("achievement_level", sa.String(length=20), nullable=False, server_default="bronze"))
    op.execute(
        "UPDATE course_certificates AS cert SET score_percent = attempts.score_percent "
        "FROM (SELECT course_id, user_id, MAX(score_percent) AS score_percent "
        "FROM final_exam_attempts WHERE passed = TRUE GROUP BY course_id, user_id) AS attempts "
        "WHERE cert.course_id = attempts.course_id AND cert.user_id = attempts.user_id"
    )
    op.execute(
        "UPDATE course_certificates SET achievement_level = CASE "
        "WHEN score_percent >= 90 THEN 'gold' WHEN score_percent >= 80 THEN 'silver' ELSE 'bronze' END"
    )
    op.create_table(
        "course_final_exams",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("passing_score", sa.Integer(), nullable=False, server_default="70"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id"),
    )
    op.create_table(
        "course_final_exam_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("choices", sa.JSON(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["course_final_exams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "position", name="uq_final_exam_questions_position"),
    )
    op.create_index("ix_course_final_exam_questions_exam_id", "course_final_exam_questions", ["exam_id"])


def downgrade() -> None:
    op.drop_index("ix_course_final_exam_questions_exam_id", table_name="course_final_exam_questions")
    op.drop_table("course_final_exam_questions")
    op.drop_table("course_final_exams")
    op.drop_column("course_certificates", "achievement_level")
    op.drop_column("course_certificates", "score_percent")
    op.drop_column("courses", "category")
