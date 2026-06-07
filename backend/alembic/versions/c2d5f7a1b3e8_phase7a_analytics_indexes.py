"""phase7a_analytics_indexes

Add indexes on attempts.status and users.role to support
efficient filtering in analytics aggregate queries.

Revision ID: c2d5f7a1b3e8
Revises: a9c4e6f8b0d1
Create Date: 2026-06-06 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c2d5f7a1b3e8"
down_revision: Union[str, None] = "a9c4e6f8b0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_attempts_status", "attempts", ["status"])
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_attempts_status", table_name="attempts")
    op.drop_index("ix_users_role", table_name="users")
