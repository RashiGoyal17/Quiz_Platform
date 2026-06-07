"""
Regression tests for marks scoring consistency.

Root cause of the original bug:
  QuizQuestion.marks_override is Numeric(5,2) — allows fractional values.
  AttemptQuestion.marks was Integer — cannot represent fractions.
  The snapshot code called int(qq.marks_override), which silently truncates:
      int(Decimal("0.50")) -> 0   (wrong: awarded 0 marks on correct answer)
      int(Decimal("1.50")) -> 1   (wrong: awarded 1 instead of 1.50)

Fix applied:
  - questions.marks and attempt_questions.marks migrated to Numeric(5,2).
  - Snapshot line changed to: effective_marks = qq.marks_override or q.marks
  - Grading line changed from Decimal(str(aq.marks)) to aq.marks (already Decimal).

Tests cover:
  - marks_override = 0.5  (was silently zeroed — the reported bug)
  - marks_override = 1.5  (was silently truncated to 1)
  - marks_override = 2    (whole number — baseline, must still work)
  - marks_override = None (fallback to question.marks)
  - Score floor: raw negative score stored as 0.00 in attempt.score
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.attempt_question import AttemptQuestion
from app.models.attempt_question_option import AttemptQuestionOption
from app.models.enums import AttemptStatus
from app.models.quiz import Quiz
from app.services.attempt_service import AttemptService


# ── helpers ───────────────────────────────────────────────────────────────────

def _svc(session: AsyncMock | None = None) -> AttemptService:
    return AttemptService(session or AsyncMock())


def _make_graded_question(
    marks: Decimal,
    negative_marks: Decimal,
    *,
    answered: bool = False,
    correct: bool = False,
) -> MagicMock:
    """
    Build a mock AttemptQuestion with one option and an optional answer.

    When answered=True, the answer's selected_option_id is wired to the
    single option so grading can find it. correct=True makes the option
    is_correct_snapshot=True.
    """
    opt = MagicMock(spec=AttemptQuestionOption)
    opt.id = uuid.uuid4()
    opt.is_correct_snapshot = correct

    aq = MagicMock(spec=AttemptQuestion)
    aq.marks = marks
    aq.negative_marks = negative_marks
    aq.options = [opt]

    if answered:
        ans = MagicMock(spec=AttemptAnswer)
        ans.selected_option_id = opt.id   # points to the only option
        ans.is_correct = None
        ans.marks_awarded = None
        aq.answer = ans
    else:
        aq.answer = None

    return aq


def _make_quiz(**overrides) -> MagicMock:
    quiz = MagicMock(spec=Quiz)
    quiz.id = uuid.uuid4()
    quiz.is_published = True
    quiz.start_time = None
    quiz.end_time = None
    quiz.max_attempts = 5
    quiz.duration_minutes = 60
    quiz.shuffle_questions = False
    quiz.shuffle_options = False
    for k, v in overrides.items():
        setattr(quiz, k, v)
    return quiz


def _make_attempt(quiz_id: uuid.UUID, student_id: uuid.UUID) -> MagicMock:
    a = MagicMock(spec=Attempt)
    a.id = uuid.uuid4()
    a.quiz_id = quiz_id
    a.student_id = student_id
    a.attempt_number = 1
    a.status = AttemptStatus.IN_PROGRESS
    a.started_at = datetime.now(timezone.utc)
    return a


def _make_quiz_question(
    marks_override: Decimal | None,
    question_marks: Decimal = Decimal("2"),
) -> MagicMock:
    """Build a QuizQuestion mock (used in start_attempt snapshot tests)."""
    opt = MagicMock()
    opt.id = uuid.uuid4()
    opt.text = "Option text"
    opt.is_correct = True
    opt.position = 0

    q = MagicMock()
    q.id = uuid.uuid4()
    q.text = "Question text"
    q.marks = question_marks
    q.negative_marks = Decimal("0.50")
    q.options = [opt]

    qq = MagicMock()
    qq.marks_override = marks_override
    qq.position = 0
    qq.question = q
    return qq


# ── _grade_attempt: grading arithmetic with Decimal marks ─────────────────────

class TestGradeAttemptDecimalMarks:
    """
    Test _grade_attempt directly with Decimal marks values.
    These are pure arithmetic tests — no DB, no snapshot logic.
    """

    async def test_marks_0_5_correct_awards_0_5(self):
        """marks=0.50, correct answer → awarded 0.50."""
        session = AsyncMock()
        svc = _svc(session)

        aq = _make_graded_question(
            marks=Decimal("0.50"),
            negative_marks=Decimal("0.25"),
            answered=True,
            correct=True,
        )
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[aq])

        score, correct, incorrect, unanswered = await svc._grade_attempt(uuid.uuid4())

        assert score == Decimal("0.50")
        assert correct == 1
        assert incorrect == 0
        assert unanswered == 0
        assert aq.answer.marks_awarded == Decimal("0.50")
        assert aq.answer.is_correct is True

    async def test_marks_0_5_wrong_deducts_negative_marks(self):
        """marks=0.50, negative_marks=0.25, wrong answer → deduct 0.25; floor score to 0."""
        session = AsyncMock()
        svc = _svc(session)

        aq = _make_graded_question(
            marks=Decimal("0.50"),
            negative_marks=Decimal("0.25"),
            answered=True,
            correct=False,   # wrong answer
        )
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[aq])

        score, correct, incorrect, unanswered = await svc._grade_attempt(uuid.uuid4())

        assert score == Decimal("0.00")   # raw -0.25, floored to 0
        assert incorrect == 1
        assert aq.answer.marks_awarded == Decimal("-0.25")
        assert aq.answer.is_correct is False

    async def test_marks_1_5_correct_awards_1_5(self):
        """marks=1.50 — previously truncated to 1 by int() cast. Must award 1.50."""
        session = AsyncMock()
        svc = _svc(session)

        aq = _make_graded_question(
            marks=Decimal("1.50"),
            negative_marks=Decimal("0.50"),
            answered=True,
            correct=True,
        )
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[aq])

        score, correct, incorrect, unanswered = await svc._grade_attempt(uuid.uuid4())

        assert score == Decimal("1.50")
        assert aq.answer.marks_awarded == Decimal("1.50")

    async def test_marks_2_whole_number_correct(self):
        """marks=2 (whole number) — baseline regression to ensure no breakage."""
        session = AsyncMock()
        svc = _svc(session)

        aq = _make_graded_question(
            marks=Decimal("2"),
            negative_marks=Decimal("0.50"),
            answered=True,
            correct=True,
        )
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[aq])

        score, correct, incorrect, unanswered = await svc._grade_attempt(uuid.uuid4())

        assert score == Decimal("2")
        assert aq.answer.marks_awarded == Decimal("2")

    async def test_unanswered_question_contributes_zero(self):
        """No answer → unanswered count incremented, score unaffected."""
        session = AsyncMock()
        svc = _svc(session)

        aq = _make_graded_question(
            marks=Decimal("1.50"),
            negative_marks=Decimal("0.50"),
            answered=False,
        )
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[aq])

        score, correct, incorrect, unanswered = await svc._grade_attempt(uuid.uuid4())

        assert score == Decimal("0.00")
        assert unanswered == 1
        assert correct == 0
        assert incorrect == 0

    async def test_score_floor_with_mixed_fractional_marks(self):
        """Two questions with fractional marks: one wrong, one unanswered → score floored to 0."""
        session = AsyncMock()
        svc = _svc(session)

        wrong_q = _make_graded_question(
            marks=Decimal("1.00"),
            negative_marks=Decimal("0.50"),
            answered=True,
            correct=False,
        )
        unanswered_q = _make_graded_question(
            marks=Decimal("0.50"),
            negative_marks=Decimal("0.25"),
            answered=False,
        )
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(
            return_value=[wrong_q, unanswered_q]
        )

        score, correct, incorrect, unanswered = await svc._grade_attempt(uuid.uuid4())

        assert score == Decimal("0.00")   # raw was -0.50, floored
        assert incorrect == 1
        assert unanswered == 1
        assert wrong_q.answer.marks_awarded == Decimal("-0.50")


# ── Snapshot: effective_marks wired correctly into AttemptQuestion ────────────

class TestSnapshotEffectiveMarks:
    """
    Verify that start_attempt stores the exact marks value into AttemptQuestion.
    These tests capture the AttemptQuestion object passed to session.add() and
    assert its .marks attribute — proving no int() truncation occurred.
    """

    async def _run_start_attempt(
        self,
        marks_override: Decimal | None,
        question_marks: Decimal = Decimal("2"),
    ) -> list[AttemptQuestion]:
        """
        Runs start_attempt with one quiz question and returns all AttemptQuestion
        objects that were added to the session.
        """
        session = AsyncMock()
        svc = _svc(session)

        quiz = _make_quiz()
        qq = _make_quiz_question(marks_override=marks_override, question_marks=question_marks)
        student_id = uuid.uuid4()
        mock_attempt = _make_attempt(quiz_id=quiz.id, student_id=student_id)

        svc.quiz_repo.get_by_id = AsyncMock(return_value=quiz)
        svc.attempt_repo.get_active_attempt = AsyncMock(return_value=None)
        svc.attempt_repo.count_student_quiz_attempts = AsyncMock(return_value=0)
        svc.attempt_repo.create = AsyncMock(return_value=mock_attempt)
        svc.quiz_repo.get_quiz_questions_with_details = AsyncMock(return_value=[qq])
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[])

        added: list = []
        session.add.side_effect = lambda obj: added.append(obj)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        await svc.start_attempt(student_id, quiz.id)

        return [obj for obj in added if isinstance(obj, AttemptQuestion)]

    async def test_marks_override_0_5_stored_without_truncation(self):
        """marks_override=0.50 must be stored as Decimal('0.50'), not 0."""
        snapshot_questions = await self._run_start_attempt(marks_override=Decimal("0.50"))

        assert len(snapshot_questions) == 1
        assert snapshot_questions[0].marks == Decimal("0.50"), (
            f"Got {snapshot_questions[0].marks!r}. "
            "int() truncation bug is still present — expected Decimal('0.50')."
        )

    async def test_marks_override_1_5_stored_without_truncation(self):
        """marks_override=1.50 must be stored as Decimal('1.50'), not 1."""
        snapshot_questions = await self._run_start_attempt(marks_override=Decimal("1.50"))

        assert len(snapshot_questions) == 1
        assert snapshot_questions[0].marks == Decimal("1.50"), (
            f"Got {snapshot_questions[0].marks!r}. Expected Decimal('1.50')."
        )

    async def test_marks_override_2_whole_number_preserved(self):
        """marks_override=2 (whole number) — must be stored exactly as Decimal('2')."""
        snapshot_questions = await self._run_start_attempt(marks_override=Decimal("2"))

        assert len(snapshot_questions) == 1
        assert snapshot_questions[0].marks == Decimal("2")

    async def test_marks_override_none_falls_back_to_question_marks(self):
        """No marks_override: AttemptQuestion.marks must equal the source question.marks."""
        snapshot_questions = await self._run_start_attempt(
            marks_override=None,
            question_marks=Decimal("3"),
        )

        assert len(snapshot_questions) == 1
        assert snapshot_questions[0].marks == Decimal("3")
