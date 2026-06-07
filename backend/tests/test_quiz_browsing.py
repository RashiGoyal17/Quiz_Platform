"""
Unit tests for Phase 8A: GET /quizzes/available (student quiz browsing).

Tests cover:
  - QuizService.list_available_quizzes_for_student delegates to the repository
    with the current UTC time and returns its result untouched
  - QuizRepository.get_available_for_student builds a query that filters on
    is_published and the optional start_time/end_time window
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.quiz import Quiz
from app.repositories.quiz_repository import QuizRepository
from app.services.quiz_service import QuizService

pytestmark = pytest.mark.asyncio

_NOW = datetime.now(timezone.utc)


def _svc(session: AsyncMock | None = None) -> QuizService:
    return QuizService(session or AsyncMock())


def _mock_quiz(**kwargs) -> MagicMock:
    q = MagicMock(spec=Quiz)
    q.id = kwargs.get("id", uuid.uuid4())
    q.title = kwargs.get("title", "Test Quiz")
    q.description = kwargs.get("description", None)
    q.duration_minutes = kwargs.get("duration_minutes", 60)
    q.start_time = kwargs.get("start_time", None)
    q.end_time = kwargs.get("end_time", None)
    q.max_attempts = kwargs.get("max_attempts", 1)
    q.proctoring_enabled = kwargs.get("proctoring_enabled", False)
    return q


# ── QuizService.list_available_quizzes_for_student ───────────────────────────

class TestListAvailableQuizzesForStudent:
    async def test_delegates_to_repository_with_current_utc_time(self):
        svc = _svc()
        svc.quiz_repo.get_available_for_student = AsyncMock(return_value=[])

        before = datetime.now(timezone.utc)
        await svc.list_available_quizzes_for_student()
        after = datetime.now(timezone.utc)

        svc.quiz_repo.get_available_for_student.assert_awaited_once()
        (passed_now,), _ = svc.quiz_repo.get_available_for_student.call_args
        assert passed_now.tzinfo is not None
        assert before <= passed_now <= after

    async def test_returns_repository_result_unchanged(self):
        svc = _svc()
        quizzes = [_mock_quiz(), _mock_quiz()]
        svc.quiz_repo.get_available_for_student = AsyncMock(return_value=quizzes)

        result = await svc.list_available_quizzes_for_student()

        assert result == quizzes


# ── QuizRepository.get_available_for_student ─────────────────────────────────

class TestGetAvailableForStudentQuery:
    """The query must require is_published and treat null start/end as unbounded."""

    async def test_executes_query_and_returns_scalars(self):
        session = AsyncMock()
        scalars_result = MagicMock()
        scalars_result.all.return_value = [_mock_quiz()]
        execute_result = MagicMock()
        execute_result.scalars.return_value = scalars_result
        session.execute = AsyncMock(return_value=execute_result)

        repo = QuizRepository(session)
        result = await repo.get_available_for_student(_NOW)

        session.execute.assert_awaited_once()
        assert len(result) == 1

    async def test_compiled_query_filters_on_publish_and_time_window(self):
        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=execute_result)

        repo = QuizRepository(session)
        await repo.get_available_for_student(_NOW)

        statement = session.execute.call_args[0][0]
        compiled = str(statement.compile(compile_kwargs={"literal_binds": False}))

        assert "is_published" in compiled
        assert "start_time" in compiled
        assert "end_time" in compiled
        # null-safe bounds: nulls must not exclude a quiz from either side
        assert compiled.count("IS NULL") == 2
