"""phase9b_organizations_contract

Phase 9B step 3/3 (contract): tighten `organization_id` to NOT NULL on
`question_banks`, `quizzes`, and `attempts` now that the backfill migration
has populated every row, and add the composite anti-cheat/audit index used
by admin attempt filtering and analytics.

`users.organization_id` is intentionally left nullable at the database
level — students remain global users and never receive an organization
(see Phase 9B design: "Tenant Boundary Rules" #7 and #8). Admins are
guaranteed a non-null organization by the internal provisioning process,
not by a DB constraint, to keep the column uniformly nullable for both
roles.

Revision ID: 9c1d6b3a7f02
Revises: b7e2f4a8c615
Create Date: 2026-06-07 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9c1d6b3a7f02"
down_revision: Union[str, None] = "b7e2f4a8c615"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("question_banks", "organization_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("quizzes", "organization_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("attempts", "organization_id", existing_type=sa.UUID(), nullable=False)

    op.create_index(
        "ix_attempts_organization_id_status",
        "attempts",
        ["organization_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attempts_organization_id_status", table_name="attempts")

    op.alter_column("attempts", "organization_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("quizzes", "organization_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("question_banks", "organization_id", existing_type=sa.UUID(), nullable=True)
