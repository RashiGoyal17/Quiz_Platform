"""
Regression tests for the MissingGreenlet bug.

Root cause: SQLAlchemy marks columns with onupdate=func.now() as expired
after flush(). Accessing them synchronously (via model_validate) inside an
async context raises MissingGreenlet. Fix: session.refresh(entity) after
every flush() that returns a mutated entity.

These tests verify that refresh() is always called on the returned entity
so that expired server-computed attributes (updated_at) are reloaded before
the object leaves the service layer.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.models.question_bank import QuestionBank
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.services.quiz_service import QuizService


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_quiz(**kwargs) -> MagicMock:
    q = MagicMock(spec=Quiz)
    q.id = uuid.uuid4()
    q.creator_id = uuid.uuid4()
    q.title = kwargs.get("title", "Test Quiz")
    q.is_published = kwargs.get("is_published", False)
    q.duration_minutes = kwargs.get("duration_minutes", 60)
    return q


def _mock_bank(**kwargs) -> MagicMock:
    b = MagicMock(spec=QuestionBank)
    b.id = uuid.uuid4()
    b.name = kwargs.get("name", "Test Bank")
    b.description = kwargs.get("description", None)
    return b


def _svc(session: AsyncMock | None = None) -> QuizService:
    return QuizService(session or AsyncMock())


_ORG_ID = uuid.uuid4()


# ── update_quiz ───────────────────────────────────────────────────────────────

class TestUpdateQuiz:
    async def test_refresh_is_called_after_flush(self):
        """session.refresh(quiz) must follow flush() so updated_at is not expired."""
        session = AsyncMock()
        svc = _svc(session)
        mock_quiz = _mock_quiz()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=mock_quiz)

        await svc.update_quiz(mock_quiz.id, _ORG_ID, {"title": "New Title"})

        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once_with(mock_quiz)

    async def test_refresh_called_before_return(self):
        """refresh() must precede the return so the caller always gets fresh data."""
        session = AsyncMock()
        call_order: list[str] = []
        session.flush.side_effect = lambda: call_order.append("flush")
        session.refresh.side_effect = lambda _: call_order.append("refresh")

        svc = _svc(session)
        mock_quiz = _mock_quiz()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=mock_quiz)

        result = await svc.update_quiz(mock_quiz.id, _ORG_ID, {"title": "X"})

        assert call_order == ["flush", "refresh"], "refresh must come after flush"
        assert result is mock_quiz

    async def test_field_values_applied_before_refresh(self):
        session = AsyncMock()
        svc = _svc(session)
        mock_quiz = _mock_quiz()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=mock_quiz)

        await svc.update_quiz(mock_quiz.id, _ORG_ID, {"title": "Updated", "duration_minutes": 90})

        assert mock_quiz.title == "Updated"
        assert mock_quiz.duration_minutes == 90

    async def test_unknown_id_raises_lookup_error(self):
        svc = _svc()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.update_quiz(uuid.uuid4(), _ORG_ID, {"title": "X"})

    async def test_no_refresh_on_not_found(self):
        """refresh must NOT be called when the quiz does not exist."""
        session = AsyncMock()
        svc = _svc(session)
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError):
            await svc.update_quiz(uuid.uuid4(), _ORG_ID, {})

        session.refresh.assert_not_awaited()


# ── publish_quiz ──────────────────────────────────────────────────────────────

class TestPublishQuiz:
    async def test_refresh_is_called_after_flush(self):
        session = AsyncMock()
        svc = _svc(session)
        mock_quiz = _mock_quiz()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=mock_quiz)
        svc.quiz_repo.get_quiz_questions_ordered = AsyncMock(
            return_value=[MagicMock(spec=QuizQuestion)]
        )

        await svc.publish_quiz(mock_quiz.id, _ORG_ID, uuid.uuid4())

        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once_with(mock_quiz)

    async def test_is_published_set_to_true(self):
        session = AsyncMock()
        svc = _svc(session)
        mock_quiz = _mock_quiz(is_published=False)
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=mock_quiz)
        svc.quiz_repo.get_quiz_questions_ordered = AsyncMock(
            return_value=[MagicMock(spec=QuizQuestion)]
        )

        await svc.publish_quiz(mock_quiz.id, _ORG_ID, uuid.uuid4())

        assert mock_quiz.is_published is True

    async def test_no_questions_raises_and_skips_refresh(self):
        session = AsyncMock()
        svc = _svc(session)
        mock_quiz = _mock_quiz()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=mock_quiz)
        svc.quiz_repo.get_quiz_questions_ordered = AsyncMock(return_value=[])

        with pytest.raises(ValueError, match="no questions"):
            await svc.publish_quiz(mock_quiz.id, _ORG_ID, uuid.uuid4())

        session.flush.assert_not_awaited()
        session.refresh.assert_not_awaited()

    async def test_unknown_id_raises_lookup_error(self):
        svc = _svc()
        svc.quiz_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.publish_quiz(uuid.uuid4(), _ORG_ID, uuid.uuid4())


# ── update_question_bank ──────────────────────────────────────────────────────

class TestUpdateQuestionBank:
    async def test_refresh_is_called_after_flush(self):
        session = AsyncMock()
        svc = _svc(session)
        mock_bank = _mock_bank()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=mock_bank)

        await svc.update_question_bank(mock_bank.id, _ORG_ID, {"name": "New Name"})

        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once_with(mock_bank)

    async def test_refresh_called_before_return(self):
        session = AsyncMock()
        call_order: list[str] = []
        session.flush.side_effect = lambda: call_order.append("flush")
        session.refresh.side_effect = lambda _: call_order.append("refresh")

        svc = _svc(session)
        mock_bank = _mock_bank()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=mock_bank)

        result = await svc.update_question_bank(mock_bank.id, _ORG_ID, {"name": "X"})

        assert call_order == ["flush", "refresh"]
        assert result is mock_bank

    async def test_field_values_applied(self):
        session = AsyncMock()
        svc = _svc(session)
        mock_bank = _mock_bank()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=mock_bank)

        await svc.update_question_bank(mock_bank.id, _ORG_ID, {"name": "Updated Bank", "description": "New desc"}
        )

        assert mock_bank.name == "Updated Bank"
        assert mock_bank.description == "New desc"

    async def test_unknown_id_raises_lookup_error(self):
        svc = _svc()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Question bank not found"):
            await svc.update_question_bank(uuid.uuid4(), _ORG_ID, {"name": "X"})

    async def test_no_refresh_on_not_found(self):
        session = AsyncMock()
        svc = _svc(session)
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError):
            await svc.update_question_bank(uuid.uuid4(), _ORG_ID, {})

        session.refresh.assert_not_awaited()
