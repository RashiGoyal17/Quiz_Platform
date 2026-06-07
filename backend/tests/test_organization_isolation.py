"""
Phase 9B — cross-organization isolation coverage.

These tests verify the Tenant Boundary Rules at the service layer: an admin
from organization A must never be able to read, modify, or reference a
resource (quiz, question bank, question, attempt, analytics) that belongs to
organization B.

The repository's `get_by_id_scoped`/`get_with_options_scoped` methods filter
by `organization_id` at the SQL level — a cross-tenant lookup returns `None`,
exactly as if the row did not exist. We simulate that here by mocking those
repo methods to return `None` for a foreign `organization_id`, and assert the
service raises `LookupError` (which the API layer turns into a 404 — Tenant
Boundary Rule #3: cross-tenant access looks identical to non-existence, never
a 403).
"""
import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.attempt_service import AttemptService
from app.services.quiz_service import QuizService

pytestmark = pytest.mark.asyncio

_ORG_A = uuid.uuid4()
_ORG_B = uuid.uuid4()


def _quiz_svc(session: AsyncMock | None = None) -> QuizService:
    return QuizService(session or AsyncMock())


def _attempt_svc(session: AsyncMock | None = None) -> AttemptService:
    return AttemptService(session or AsyncMock())


# A resource that exists, but belongs to org B — org A's admin must see it as
# absent. We model this by having the scoped repo lookup return None whenever
# it's queried with org A's id (mirrors the real `WHERE organization_id = :id`
# filter excluding a foreign-org row).
def _not_in_this_org() -> AsyncMock:
    return AsyncMock(return_value=None)


class TestQuizCrossTenantIsolation:
    async def test_get_quiz_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.quiz_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.get_quiz(uuid.uuid4(), _ORG_A)

    async def test_update_quiz_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.quiz_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.update_quiz(uuid.uuid4(), _ORG_A, {"title": "Hijacked"})

    async def test_publish_quiz_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.quiz_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.publish_quiz(uuid.uuid4(), _ORG_A, uuid.uuid4())

    async def test_unpublish_quiz_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.quiz_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.unpublish_quiz(uuid.uuid4(), _ORG_A, uuid.uuid4())

    async def test_list_quiz_questions_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.quiz_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.list_quiz_questions(uuid.uuid4(), _ORG_A)

    async def test_remove_question_from_other_org_quiz_raises_lookup_error(self):
        session = AsyncMock()
        svc = _quiz_svc(session)
        svc.quiz_repo.get_by_id_scoped = _not_in_this_org()
        svc.quiz_repo.remove_question = AsyncMock()

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.remove_question_from_quiz(uuid.uuid4(), _ORG_A, uuid.uuid4(), uuid.uuid4())

        svc.quiz_repo.remove_question.assert_not_awaited()


class TestQuestionBankCrossTenantIsolation:
    async def test_get_question_bank_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.bank_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Question bank not found"):
            await svc.get_question_bank(uuid.uuid4(), _ORG_A)

    async def test_update_question_bank_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.bank_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Question bank not found"):
            await svc.update_question_bank(uuid.uuid4(), _ORG_A, {"name": "Hijacked"})

    async def test_delete_question_bank_from_other_org_raises_lookup_error(self):
        session = AsyncMock()
        svc = _quiz_svc(session)
        svc.bank_repo.get_by_id_scoped = _not_in_this_org()
        svc.bank_repo.delete = AsyncMock()

        with pytest.raises(LookupError, match="Question bank not found"):
            await svc.delete_question_bank(uuid.uuid4(), _ORG_A)

        svc.bank_repo.delete.assert_not_awaited()

    async def test_create_question_in_other_org_bank_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.bank_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Question bank not found"):
            await svc.create_question(
                bank_id=uuid.uuid4(),
                organization_id=_ORG_A,
                text="2+2=?",
                marks=1,
                options=[],
            )


class TestQuestionCrossTenantIsolation:
    async def test_get_question_from_other_org_raises_lookup_error(self):
        svc = _quiz_svc()
        svc.question_repo.get_with_options_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Question not found"):
            await svc.get_question(uuid.uuid4(), _ORG_A)


class TestAddQuestionToQuizCrossTenantReference:
    """Tenant Boundary Rule #5: a quiz may never reference a question whose
    bank belongs to a different organization — even if both the quiz and the
    question happen to be visible to the same caller through some other path.
    """

    async def test_question_from_other_org_cannot_be_attached_to_quiz(self):
        from unittest.mock import MagicMock

        from app.models.quiz import Quiz

        svc = _quiz_svc()
        quiz = MagicMock(spec=Quiz)
        quiz.id = uuid.uuid4()

        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=quiz)
        # The question exists, but its bank belongs to org B — the scoped
        # lookup (joined through QuestionBank.organization_id) excludes it.
        svc.question_repo.get_with_options_scoped = AsyncMock(return_value=None)
        svc.quiz_repo.add_question = AsyncMock()

        with pytest.raises(LookupError, match="Question not found"):
            await svc.add_question_to_quiz(
                quiz_id=quiz.id,
                organization_id=_ORG_A,
                question_id=uuid.uuid4(),
                position=0,
                requester_id=uuid.uuid4(),
            )

        svc.quiz_repo.add_question.assert_not_awaited()


class TestAttemptAuditCrossTenantIsolation:
    async def test_get_attempt_audit_from_other_org_raises_lookup_error(self):
        svc = _attempt_svc()
        svc.attempt_repo.get_by_id_scoped = _not_in_this_org()

        with pytest.raises(LookupError, match="Attempt not found"):
            await svc.get_attempt_audit(uuid.uuid4(), _ORG_A)

    async def test_get_attempt_audit_does_not_leak_logs_for_foreign_attempt(self):
        """Even the tab-switch/proctoring lookups must never run for a
        cross-tenant attempt — the LookupError must short-circuit first."""
        svc = _attempt_svc()
        svc.attempt_repo.get_by_id_scoped = _not_in_this_org()
        svc.tab_switch_log_repo.get_by_attempt = AsyncMock(return_value=[])
        svc.proctoring_event_repo.get_by_attempt = AsyncMock(return_value=[])

        with pytest.raises(LookupError):
            await svc.get_attempt_audit(uuid.uuid4(), _ORG_A)

        svc.tab_switch_log_repo.get_by_attempt.assert_not_awaited()
        svc.proctoring_event_repo.get_by_attempt.assert_not_awaited()


class TestScopedLookupsReceiveCallerOrganization:
    """Defense-in-depth: the service must always pass the *caller's*
    organization_id into the scoped repo lookup — never the resource's own
    (which the caller doesn't know yet) or a hardcoded/default value. This is
    what makes the repository-level filter an effective boundary."""

    async def test_get_quiz_passes_through_callers_org_id(self):
        svc = _quiz_svc()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=None)
        quiz_id = uuid.uuid4()

        with pytest.raises(LookupError):
            await svc.get_quiz(quiz_id, _ORG_B)

        svc.quiz_repo.get_by_id_scoped.assert_awaited_once_with(quiz_id, _ORG_B)

    async def test_get_question_bank_passes_through_callers_org_id(self):
        svc = _quiz_svc()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=None)
        bank_id = uuid.uuid4()

        with pytest.raises(LookupError):
            await svc.get_question_bank(bank_id, _ORG_B)

        svc.bank_repo.get_by_id_scoped.assert_awaited_once_with(bank_id, _ORG_B)

    async def test_get_attempt_audit_passes_through_callers_org_id(self):
        svc = _attempt_svc()
        svc.attempt_repo.get_by_id_scoped = AsyncMock(return_value=None)
        attempt_id = uuid.uuid4()

        with pytest.raises(LookupError):
            await svc.get_attempt_audit(attempt_id, _ORG_B)

        svc.attempt_repo.get_by_id_scoped.assert_awaited_once_with(attempt_id, _ORG_B)
