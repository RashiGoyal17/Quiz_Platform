"""proctoring_event_index

Add composite index on proctoring_events(attempt_id, event_type) to support
efficient per-type filtering in admin audit queries.

Revision ID: a9c4e6f8b0d1
Revises: f1a3b5c7d9e2
Create Date: 2026-06-06 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a9c4e6f8b0d1"
down_revision: Union[str, None] = "f1a3b5c7d9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_proctoring_events_attempt_type",
        "proctoring_events",
        ["attempt_id", "event_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_proctoring_events_attempt_type", table_name="proctoring_events")
