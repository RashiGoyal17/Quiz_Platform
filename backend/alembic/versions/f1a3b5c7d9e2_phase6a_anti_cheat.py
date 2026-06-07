"""phase6a_anti_cheat

Add max_tab_switches to quizzes for tab-switch limit enforcement.
Nullable integer — None means no limit.

Revision ID: f1a3b5c7d9e2
Revises: e3f1c9d2a847
Create Date: 2026-06-06 19:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a3b5c7d9e2"
down_revision: Union[str, None] = "e3f1c9d2a847"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("quizzes", sa.Column("max_tab_switches", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("quizzes", "max_tab_switches")
