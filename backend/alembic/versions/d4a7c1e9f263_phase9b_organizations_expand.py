"""phase9b_organizations_expand

Phase 9B step 1/3 (expand): introduce the `organizations` table, seed a
"Default Organization" that absorbs all pre-existing tenant-owned data, and
add nullable `organization_id` foreign keys to `users`, `question_banks`,
`quizzes`, and `attempts`. The columns are added nullable here; they are
backfilled in the next migration and tightened to NOT NULL (where required)
in the migration after that — this expand/backfill/contract sequence avoids
locking large tables or requiring a maintenance window.

Revision ID: d4a7c1e9f263
Revises: c2d5f7a1b3e8
Create Date: 2026-06-07 10:00:00.000000

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4a7c1e9f263"
down_revision: Union[str, None] = "c2d5f7a1b3e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_ORG_NAME = "Default Organization"
DEFAULT_ORG_SLUG = "default"


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)

    organizations = sa.table(
        "organizations",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        organizations,
        [
            {
                "id": DEFAULT_ORG_ID,
                "name": DEFAULT_ORG_NAME,
                "slug": DEFAULT_ORG_SLUG,
                "is_active": True,
            }
        ],
    )

    op.add_column("users", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False)
    op.create_foreign_key(
        "fk_users_organization_id_organizations",
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column("question_banks", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_question_banks_organization_id"), "question_banks", ["organization_id"], unique=False
    )
    op.create_foreign_key(
        "fk_question_banks_organization_id_organizations",
        "question_banks",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column("quizzes", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_quizzes_organization_id"), "quizzes", ["organization_id"], unique=False)
    op.create_foreign_key(
        "fk_quizzes_organization_id_organizations",
        "quizzes",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column("attempts", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_attempts_organization_id_organizations",
        "attempts",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_attempts_organization_id_organizations", "attempts", type_="foreignkey")
    op.drop_column("attempts", "organization_id")

    op.drop_constraint("fk_quizzes_organization_id_organizations", "quizzes", type_="foreignkey")
    op.drop_index(op.f("ix_quizzes_organization_id"), table_name="quizzes")
    op.drop_column("quizzes", "organization_id")

    op.drop_constraint(
        "fk_question_banks_organization_id_organizations", "question_banks", type_="foreignkey"
    )
    op.drop_index(op.f("ix_question_banks_organization_id"), table_name="question_banks")
    op.drop_column("question_banks", "organization_id")

    op.drop_constraint("fk_users_organization_id_organizations", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_column("users", "organization_id")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")
