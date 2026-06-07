"""
Unit tests for AnalyticsService.

All tests are pure unit tests — no database, no HTTP client.
Repositories are replaced with AsyncMock/MagicMock at the service boundary.
Pattern mirrors test_proctoring_events.py.

Row fakes are plain dicts — the service uses row["key"] access throughout,
and dicts satisfy that contract without the MagicMock __getitem__ dunder trap.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import AttemptStatus
from app.schemas.analytics import (
    AdminDashboardResponse,
    QuizAnalyticsResponse,
    QuizQuestionAnalyticsResponse,
    StudentAnalyticsResponse,
    StudentHistoryResponse,
)
from app.services.analytics_service import MIN_ATTEMPTS_FOR_RANKING, AnalyticsService

pytestmark = pytest.mark.asyncio

_NOW = datetime.now(timezone.utc)


# ── helpers ───────────────────────────────────────────────────────────────────

def _svc() -> AnalyticsService:
    svc = AnalyticsService(AsyncMock())
    svc.analytics_repo = MagicMock()
    svc.quiz_repo = MagicMock()
    return svc


def _make_quiz(quiz_id: uuid.UUID | None = None, title: str = "Test Quiz") -> MagicMock:
    q = MagicMock()
    q.id = quiz_id or uuid.uuid4()
    q.title = title
    return q


def _stats_row(**kwargs) -> dict:
    return {
        "total_attempts": 0,
        "submitted_count": 0,
        "timed_out_count": 0,
        "abandoned_count": 0,
        "in_progress_count": 0,
        "average_score": None,
        "best_score": None,
        **kwargs,
    }


def _quiz_stats_row(**kwargs) -> dict:
    return {
        "total_attempts": 0,
        "in_progress_count": 0,
        "submitted_count": 0,
        "timed_out_count": 0,
        "abandoned_count": 0,
        "average_score": None,
        **kwargs,
    }


def _platform_row(**kwargs) -> dict:
    return {
        "total_users": 0,
        "total_students": 0,
        "total_admins": 0,
        "active_users": 0,
        "total_quizzes": 0,
        "published_quizzes": 0,
        "total_attempts": 0,
        "in_progress_attempts": 0,
        "submitted_attempts": 0,
        "timed_out_attempts": 0,
        "abandoned_attempts": 0,
        "total_tab_switches": 0,
        "avg_tab_switches": None,
        **kwargs,
    }


def _history_row(**kwargs) -> dict:
    return {
        "attempt_id": uuid.uuid4(),
        "quiz_id": uuid.uuid4(),
        "quiz_title": "A Quiz",
        "attempt_number": 1,
        "status": AttemptStatus.SUBMITTED,
        "score": None,
        "started_at": _NOW,
        "submitted_at": None,
        **kwargs,
    }


def _activity_row(**kwargs) -> dict:
    return {
        "attempt_id": uuid.uuid4(),
        "student_id": uuid.uuid4(),
        "student_username": "alice",
        "quiz_id": uuid.uuid4(),
        "quiz_title": "Quiz A",
        "status": AttemptStatus.SUBMITTED,
        "score": None,
        "started_at": _NOW,
        "submitted_at": None,
        **kwargs,
    }


def _question_row(**kwargs) -> dict:
    return {
        "question_id": uuid.uuid4(),
        "question_text_snapshot": "What is 2+2?",
        "total_seen": 20,
        "answered_count": 18,
        "correct_count": 12,
        "incorrect_count": 6,
        **kwargs,
    }


def _anti_cheat(**kwargs) -> dict:
    return {
        "total_tab_switches": 0,
        "avg_tab_switches": None,
        "attempts_with_proctoring_events": 0,
        **kwargs,
    }


# ── TestGetStudentAnalytics ───────────────────────────────────────────────────

class TestGetStudentAnalytics:

    async def test_returns_student_id_in_response(self):
        svc = _svc()
        student_id = uuid.uuid4()
        svc.analytics_repo.get_student_stats = AsyncMock(return_value=_stats_row())

        result = await svc.get_student_analytics(student_id)

        assert isinstance(result, StudentAnalyticsResponse)
        assert result.student_id == student_id

    async def test_total_attempts_from_repo(self):
        svc = _svc()
        svc.analytics_repo.get_student_stats = AsyncMock(
            return_value=_stats_row(total_attempts=7)
        )

        result = await svc.get_student_analytics(uuid.uuid4())

        assert result.total_attempts == 7

    async def test_all_status_counts_present(self):
        svc = _svc()
        svc.analytics_repo.get_student_stats = AsyncMock(
            return_value=_stats_row(
                submitted_count=3,
                timed_out_count=1,
                abandoned_count=2,
                in_progress_count=1,
            )
        )

        result = await svc.get_student_analytics(uuid.uuid4())

        assert result.submitted_count == 3
        assert result.timed_out_count == 1
        assert result.abandoned_count == 2
        assert result.in_progress_count == 1

    async def test_average_score_rounded_to_two_places(self):
        svc = _svc()
        svc.analytics_repo.get_student_stats = AsyncMock(
            return_value=_stats_row(average_score=72.333333)
        )

        result = await svc.get_student_analytics(uuid.uuid4())

        assert result.average_score == Decimal("72.33")

    async def test_average_score_none_when_no_finalized_attempts(self):
        svc = _svc()
        svc.analytics_repo.get_student_stats = AsyncMock(
            return_value=_stats_row(average_score=None)
        )

        result = await svc.get_student_analytics(uuid.uuid4())

        assert result.average_score is None

    async def test_best_score_rounded_to_two_places(self):
        svc = _svc()
        svc.analytics_repo.get_student_stats = AsyncMock(
            return_value=_stats_row(best_score=95.5)
        )

        result = await svc.get_student_analytics(uuid.uuid4())

        assert result.best_score == Decimal("95.50")

    async def test_best_score_none_when_no_finalized_attempts(self):
        svc = _svc()
        svc.analytics_repo.get_student_stats = AsyncMock(
            return_value=_stats_row(best_score=None)
        )

        result = await svc.get_student_analytics(uuid.uuid4())

        assert result.best_score is None

    async def test_repo_called_with_correct_student_id(self):
        svc = _svc()
        student_id = uuid.uuid4()
        svc.analytics_repo.get_student_stats = AsyncMock(return_value=_stats_row())

        await svc.get_student_analytics(student_id)

        svc.analytics_repo.get_student_stats.assert_awaited_once_with(student_id)


# ── TestGetStudentHistory ─────────────────────────────────────────────────────

class TestGetStudentHistory:

    async def test_empty_items_when_no_attempts(self):
        svc = _svc()
        svc.analytics_repo.get_student_history = AsyncMock(return_value=([], 0))

        result = await svc.get_student_history(uuid.uuid4())

        assert isinstance(result, StudentHistoryResponse)
        assert result.items == []
        assert result.total == 0

    async def test_items_include_quiz_title(self):
        svc = _svc()
        row = _history_row(quiz_title="Geo Quiz", score=Decimal("80.00"))
        svc.analytics_repo.get_student_history = AsyncMock(return_value=([row], 1))

        result = await svc.get_student_history(uuid.uuid4())

        assert result.items[0].quiz_title == "Geo Quiz"

    async def test_total_count_in_response(self):
        svc = _svc()
        svc.analytics_repo.get_student_history = AsyncMock(return_value=([], 42))

        result = await svc.get_student_history(uuid.uuid4())

        assert result.total == 42

    async def test_limit_and_offset_forwarded(self):
        svc = _svc()
        student_id = uuid.uuid4()
        svc.analytics_repo.get_student_history = AsyncMock(return_value=([], 0))

        await svc.get_student_history(student_id, limit=5, offset=10)

        svc.analytics_repo.get_student_history.assert_awaited_once_with(
            student_id, 5, 10, None
        )

    async def test_quiz_id_filter_forwarded_when_provided(self):
        svc = _svc()
        student_id = uuid.uuid4()
        quiz_id = uuid.uuid4()
        svc.analytics_repo.get_student_history = AsyncMock(return_value=([], 0))

        await svc.get_student_history(student_id, quiz_id=quiz_id)

        svc.analytics_repo.get_student_history.assert_awaited_once_with(
            student_id, 20, 0, quiz_id
        )

    async def test_limit_and_offset_in_response(self):
        svc = _svc()
        svc.analytics_repo.get_student_history = AsyncMock(return_value=([], 0))

        result = await svc.get_student_history(uuid.uuid4(), limit=15, offset=30)

        assert result.limit == 15
        assert result.offset == 30


# ── TestGetQuizAnalytics ──────────────────────────────────────────────────────

class TestGetQuizAnalytics:

    def _wire(self, svc, quiz, stats, ac, most_common=None):
        svc.quiz_repo.get_by_id = AsyncMock(return_value=quiz)
        svc.analytics_repo.get_quiz_stats = AsyncMock(return_value=stats)
        svc.analytics_repo.get_quiz_anti_cheat_stats = AsyncMock(return_value=ac)
        svc.analytics_repo.get_quiz_most_common_event = AsyncMock(return_value=most_common)

    async def test_quiz_not_found_raises_lookup_error(self):
        svc = _svc()
        svc.quiz_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.get_quiz_analytics(uuid.uuid4())

    async def test_quiz_title_in_response(self):
        svc = _svc()
        quiz = _make_quiz(title="History Final")
        self._wire(svc, quiz, _quiz_stats_row(), _anti_cheat())

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.quiz_title == "History Final"

    async def test_total_attempts_count(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(
            svc, quiz,
            _quiz_stats_row(total_attempts=10, submitted_count=7, timed_out_count=2, abandoned_count=1),
            _anti_cheat(),
        )

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.total_attempts == 10

    async def test_completion_rate_submitted_plus_timed_out_over_finished(self):
        svc = _svc()
        quiz = _make_quiz()
        # submitted=6, timed_out=2, abandoned=2 → finished=10 → (6+2)/10 * 100 = 80.00
        self._wire(
            svc, quiz,
            _quiz_stats_row(submitted_count=6, timed_out_count=2, abandoned_count=2),
            _anti_cheat(),
        )

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.completion_rate == Decimal("80.00")

    async def test_completion_rate_zero_when_no_finished_attempts(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, _quiz_stats_row(in_progress_count=3), _anti_cheat())

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.completion_rate == Decimal("0.00")

    async def test_abandonment_rate_correct(self):
        svc = _svc()
        quiz = _make_quiz()
        # abandoned=1, finished=4 → 25.00
        self._wire(
            svc, quiz,
            _quiz_stats_row(submitted_count=3, abandoned_count=1),
            _anti_cheat(),
        )

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.abandonment_rate == Decimal("25.00")

    async def test_timeout_rate_correct(self):
        svc = _svc()
        quiz = _make_quiz()
        # timed_out=2, finished=4 → 50.00
        self._wire(
            svc, quiz,
            _quiz_stats_row(submitted_count=2, timed_out_count=2),
            _anti_cheat(),
        )

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.timeout_rate == Decimal("50.00")

    async def test_average_score_none_when_no_finalized_attempts(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, _quiz_stats_row(average_score=None), _anti_cheat())

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.average_score is None

    async def test_anti_cheat_total_tab_switches(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, _quiz_stats_row(), _anti_cheat(total_tab_switches=14))

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.anti_cheat.total_tab_switches == 14

    async def test_anti_cheat_average_tab_switches_none_when_no_attempts(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, _quiz_stats_row(), _anti_cheat(avg_tab_switches=None))

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.anti_cheat.average_tab_switches_per_attempt is None

    async def test_anti_cheat_attempts_with_proctoring_events_count(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(
            svc, quiz,
            _quiz_stats_row(),
            _anti_cheat(attempts_with_proctoring_events=5),
        )

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.anti_cheat.attempts_with_proctoring_events == 5

    async def test_anti_cheat_most_common_event_none_when_no_events(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, _quiz_stats_row(), _anti_cheat(), most_common=None)

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.anti_cheat.most_common_proctoring_event is None

    async def test_anti_cheat_most_common_event_value(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, _quiz_stats_row(), _anti_cheat(), most_common="window_blur")

        result = await svc.get_quiz_analytics(quiz.id)

        assert result.anti_cheat.most_common_proctoring_event == "window_blur"


# ── TestGetQuizQuestionAnalytics ──────────────────────────────────────────────

class TestGetQuizQuestionAnalytics:

    def _wire(self, svc, quiz, rows):
        svc.quiz_repo.get_by_id = AsyncMock(return_value=quiz)
        svc.analytics_repo.get_quiz_question_stats = AsyncMock(return_value=rows)

    async def test_quiz_not_found_raises_lookup_error(self):
        svc = _svc()
        svc.quiz_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Quiz not found"):
            await svc.get_quiz_question_analytics(uuid.uuid4())

    async def test_empty_questions_list_when_no_finalized_attempts(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, [])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert isinstance(result, QuizQuestionAnalyticsResponse)
        assert result.questions == []

    async def test_correct_pct_computed(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(total_seen=20, correct_count=15, incorrect_count=5, answered_count=20)
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].correct_pct == Decimal("75.00")

    async def test_incorrect_pct_computed(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(total_seen=20, correct_count=15, incorrect_count=5, answered_count=20)
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].incorrect_pct == Decimal("25.00")

    async def test_unanswered_pct_computed(self):
        svc = _svc()
        quiz = _make_quiz()
        # total=20, answered=15 → unanswered=5 → 25%
        row = _question_row(total_seen=20, correct_count=12, incorrect_count=3, answered_count=15)
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].unanswered_pct == Decimal("25.00")

    async def test_pcts_none_when_total_seen_zero(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(total_seen=0, correct_count=0, incorrect_count=0, answered_count=0)
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        q = result.questions[0]
        assert q.correct_pct is None
        assert q.incorrect_pct is None
        assert q.unanswered_pct is None

    async def test_difficulty_rank_assigned_at_threshold(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(
            total_seen=MIN_ATTEMPTS_FOR_RANKING,
            correct_count=5,
            incorrect_count=5,
            answered_count=10,
        )
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].difficulty_rank == 1
        assert result.questions[0].insufficient_data is False

    async def test_difficulty_rank_null_below_threshold(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(
            total_seen=MIN_ATTEMPTS_FOR_RANKING - 1,
            correct_count=5,
            incorrect_count=4,
            answered_count=9,
        )
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].difficulty_rank is None

    async def test_insufficient_data_true_below_threshold(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(
            total_seen=MIN_ATTEMPTS_FOR_RANKING - 1,
            correct_count=4,
            incorrect_count=4,
            answered_count=8,
        )
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].insufficient_data is True

    async def test_insufficient_data_false_at_threshold(self):
        svc = _svc()
        quiz = _make_quiz()
        row = _question_row(
            total_seen=MIN_ATTEMPTS_FOR_RANKING,
            correct_count=5,
            incorrect_count=5,
            answered_count=10,
        )
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].insufficient_data is False

    async def test_rank_1_is_hardest_question(self):
        svc = _svc()
        quiz = _make_quiz()
        # Q1: 4/20 correct (20%) — hardest → rank 1
        # Q2: 16/20 correct (80%) — easiest → rank 2
        q1 = _question_row(total_seen=20, correct_count=4, incorrect_count=16, answered_count=20)
        q2 = _question_row(total_seen=20, correct_count=16, incorrect_count=4, answered_count=20)
        self._wire(svc, quiz, [q2, q1])  # deliberately reversed input order

        result = await svc.get_quiz_question_analytics(quiz.id)

        ranked = sorted(
            [q for q in result.questions if q.difficulty_rank is not None],
            key=lambda q: q.difficulty_rank,
        )
        assert ranked[0].correct_count == 4
        assert ranked[1].correct_count == 16

    async def test_insufficient_data_questions_appended_after_ranked(self):
        svc = _svc()
        quiz = _make_quiz()
        rankable = _question_row(
            total_seen=MIN_ATTEMPTS_FOR_RANKING,
            correct_count=5,
            incorrect_count=5,
            answered_count=10,
        )
        insufficient = _question_row(
            total_seen=2,
            correct_count=1,
            incorrect_count=1,
            answered_count=2,
        )
        self._wire(svc, quiz, [rankable, insufficient])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.questions[0].insufficient_data is False
        assert result.questions[0].difficulty_rank == 1
        assert result.questions[1].insufficient_data is True
        assert result.questions[1].difficulty_rank is None

    async def test_min_attempts_for_ranking_in_response(self):
        svc = _svc()
        quiz = _make_quiz()
        self._wire(svc, quiz, [])

        result = await svc.get_quiz_question_analytics(quiz.id)

        assert result.min_attempts_for_ranking == MIN_ATTEMPTS_FOR_RANKING

    async def test_pct_computed_even_when_insufficient_data(self):
        svc = _svc()
        quiz = _make_quiz()
        # total_seen=5 (< 10) but pcts should still be computed
        row = _question_row(total_seen=5, correct_count=3, incorrect_count=2, answered_count=5)
        self._wire(svc, quiz, [row])

        result = await svc.get_quiz_question_analytics(quiz.id)

        q = result.questions[0]
        assert q.insufficient_data is True
        assert q.correct_pct == Decimal("60.00")


# ── TestGetAdminDashboard ─────────────────────────────────────────────────────

class TestGetAdminDashboard:

    def _wire(self, svc, platform, total_events, recent):
        svc.analytics_repo.get_platform_stats = AsyncMock(return_value=platform)
        svc.analytics_repo.get_platform_total_proctoring_events = AsyncMock(
            return_value=total_events
        )
        svc.analytics_repo.get_recent_activity = AsyncMock(return_value=recent)

    async def test_total_users_from_platform_stats(self):
        svc = _svc()
        self._wire(svc, _platform_row(total_users=50), 0, [])

        result = await svc.get_admin_dashboard()

        assert isinstance(result, AdminDashboardResponse)
        assert result.total_users == 50

    async def test_student_and_admin_counts(self):
        svc = _svc()
        self._wire(svc, _platform_row(total_students=40, total_admins=10), 0, [])

        result = await svc.get_admin_dashboard()

        assert result.total_students == 40
        assert result.total_admins == 10

    async def test_quiz_counts(self):
        svc = _svc()
        self._wire(svc, _platform_row(total_quizzes=20, published_quizzes=15), 0, [])

        result = await svc.get_admin_dashboard()

        assert result.total_quizzes == 20
        assert result.published_quizzes == 15

    async def test_attempt_status_breakdown(self):
        svc = _svc()
        self._wire(
            svc,
            _platform_row(
                total_attempts=100,
                in_progress_attempts=10,
                submitted_attempts=60,
                timed_out_attempts=20,
                abandoned_attempts=10,
            ),
            0, [],
        )

        result = await svc.get_admin_dashboard()

        assert result.total_attempts == 100
        assert result.in_progress_attempts == 10
        assert result.submitted_attempts == 60
        assert result.timed_out_attempts == 20
        assert result.abandoned_attempts == 10

    async def test_total_tab_switches(self):
        svc = _svc()
        self._wire(svc, _platform_row(total_tab_switches=300), 0, [])

        result = await svc.get_admin_dashboard()

        assert result.total_tab_switches == 300

    async def test_average_tab_switches_none_when_no_attempts(self):
        svc = _svc()
        self._wire(svc, _platform_row(avg_tab_switches=None), 0, [])

        result = await svc.get_admin_dashboard()

        assert result.average_tab_switches_per_attempt is None

    async def test_average_tab_switches_rounded(self):
        svc = _svc()
        self._wire(svc, _platform_row(avg_tab_switches=2.666667), 0, [])

        result = await svc.get_admin_dashboard()

        assert result.average_tab_switches_per_attempt == Decimal("2.67")

    async def test_total_proctoring_events(self):
        svc = _svc()
        self._wire(svc, _platform_row(), 42, [])

        result = await svc.get_admin_dashboard()

        assert result.total_proctoring_events == 42

    async def test_recent_attempts_populated(self):
        svc = _svc()
        row = _activity_row(student_username="bob", quiz_title="Science Quiz")
        self._wire(svc, _platform_row(), 0, [row])

        result = await svc.get_admin_dashboard()

        assert len(result.recent_attempts) == 1
        assert result.recent_attempts[0].student_username == "bob"
        assert result.recent_attempts[0].quiz_title == "Science Quiz"

    async def test_recent_attempts_empty_when_none(self):
        svc = _svc()
        self._wire(svc, _platform_row(), 0, [])

        result = await svc.get_admin_dashboard()

        assert result.recent_attempts == []
