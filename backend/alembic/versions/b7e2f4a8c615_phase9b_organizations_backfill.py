"""phase9b_organizations_backfill

Phase 9B step 2/3 (backfill): assign every existing admin to the
"Default Organization" seeded in the previous migration, then propagate
that organization down through question banks, quizzes, and attempts via
their existing ownership chains (creator -> org, quiz -> org).

Students are intentionally left with `organization_id = NULL` — they
remain global users (see Phase 9B design: "Tenant Boundary Rules" #7).

Revision ID: b7e2f4a8c615
Revises: d4a7c1e9f263
Create Date: 2026-06-07 10:05:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "b7e2f4a8c615"
down_revision: Union[str, None] = "d4a7c1e9f263"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        text(
            "UPDATE users SET organization_id = :org_id "
            "WHERE role = 'ADMIN' AND organization_id IS NULL"
        ),
        {"org_id": DEFAULT_ORG_ID},
    )

    conn.execute(
        text(
            "UPDATE question_banks AS qb "
            "SET organization_id = COALESCE(u.organization_id, :org_id) "
            "FROM users AS u "
            "WHERE qb.creator_id = u.id AND qb.organization_id IS NULL"
        ),
        {"org_id": DEFAULT_ORG_ID},
    )
    # Defensive fallback for any bank whose creator row is missing/orphaned.
    conn.execute(
        text(
            "UPDATE question_banks SET organization_id = :org_id WHERE organization_id IS NULL"
        ),
        {"org_id": DEFAULT_ORG_ID},
    )

    conn.execute(
        text(
            "UPDATE quizzes AS q "
            "SET organization_id = COALESCE(u.organization_id, :org_id) "
            "FROM users AS u "
            "WHERE q.creator_id = u.id AND q.organization_id IS NULL"
        ),
        {"org_id": DEFAULT_ORG_ID},
    )
    conn.execute(
        text("UPDATE quizzes SET organization_id = :org_id WHERE organization_id IS NULL"),
        {"org_id": DEFAULT_ORG_ID},
    )

    conn.execute(
        text(
            "UPDATE attempts AS a "
            "SET organization_id = COALESCE(qz.organization_id, :org_id) "
            "FROM quizzes AS qz "
            "WHERE a.quiz_id = qz.id AND a.organization_id IS NULL"
        ),
        {"org_id": DEFAULT_ORG_ID},
    )
    conn.execute(
        text("UPDATE attempts SET organization_id = :org_id WHERE organization_id IS NULL"),
        {"org_id": DEFAULT_ORG_ID},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("UPDATE attempts SET organization_id = NULL"))
    conn.execute(text("UPDATE quizzes SET organization_id = NULL"))
    conn.execute(text("UPDATE question_banks SET organization_id = NULL"))
    conn.execute(
        text("UPDATE users SET organization_id = NULL WHERE organization_id = :org_id"),
        {"org_id": DEFAULT_ORG_ID},
    )
