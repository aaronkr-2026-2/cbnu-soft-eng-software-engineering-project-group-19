"""expand certificate verification code length

Revision ID: c1a4b9e72d30
Revises: 9f84d2c16a30
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c1a4b9e72d30"
down_revision: Union[str, Sequence[str], None] = "9f84d2c16a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("course_certificates", "certificate_code", type_=sa.String(length=40), existing_type=sa.String(length=32), nullable=False)


def downgrade() -> None:
    op.alter_column("course_certificates", "certificate_code", type_=sa.String(length=32), existing_type=sa.String(length=40), nullable=False)
