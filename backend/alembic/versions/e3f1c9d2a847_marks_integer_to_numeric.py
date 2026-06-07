"""marks_integer_to_numeric

Migrate questions.marks and attempt_questions.marks from INTEGER to NUMERIC(5,2)
to be consistent with the rest of the scoring pipeline (marks_override, marks_awarded,
negative_marks, score — all NUMERIC). This eliminates the int() truncation that caused
fractional marks_override values to be silently zeroed during attempt snapshotting.

Revision ID: e3f1c9d2a847
Revises: a4f8b2d3e901
Create Date: 2026-06-06 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3f1c9d2a847"
down_revision: Union[str, None] = "a4f8b2d3e901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # INTEGER → NUMERIC(5,2) is lossless: every integer n becomes n.00 exactly.
    # PostgreSQL performs this cast implicitly; the USING clause makes it explicit.
    op.alter_column(
        "questions",
        "marks",
        type_=sa.Numeric(precision=5, scale=2),
        postgresql_using="marks::numeric(5,2)",
        nullable=False,
    )
    op.alter_column(
        "attempt_questions",
        "marks",
        type_=sa.Numeric(precision=5, scale=2),
        postgresql_using="marks::numeric(5,2)",
        nullable=False,
    )


def downgrade() -> None:
    # NUMERIC → INTEGER truncates fractional values (e.g. 0.50 → 0, 1.50 → 1).
    # This downgrade is lossy if any non-integer marks exist in the database.
    op.alter_column(
        "attempt_questions",
        "marks",
        type_=sa.Integer(),
        postgresql_using="marks::integer",
        nullable=False,
    )
    op.alter_column(
        "questions",
        "marks",
        type_=sa.Integer(),
        postgresql_using="marks::integer",
        nullable=False,
    )
