from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.quiz_repository import QuizRepository
from app.schemas.analytics import (
    AdminDashboardResponse,
    AttemptHistoryItem,
    QuestionAnalyticsItem,
    QuizAnalyticsResponse,
    QuizAntiCheatAnalytics,
    QuizQuestionAnalyticsResponse,
    RecentActivityItem,
    StudentAnalyticsResponse,
    StudentHistoryResponse,
)

MIN_ATTEMPTS_FOR_RANKING: int = 10

_TWO_PLACES = Decimal("0.01")


def _pct(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0.00")
    return Decimal(str(numerator / denominator * 100)).quantize(_TWO_PLACES)


def _build_question_item(row, rank: int | None, insufficient_data: bool) -> QuestionAnalyticsItem:
    total = int(row["total_seen"])
    correct = int(row["correct_count"])
    incorrect = int(row["incorrect_count"])
    answered = int(row["answered_count"])
    unanswered = total - answered

    def pct(n: int) -> Decimal | None:
        if total == 0:
            return None
        return Decimal(str(n / total * 100)).quantize(_TWO_PLACES)

    return QuestionAnalyticsItem(
        question_id=row["question_id"],
        question_text_snapshot=row["question_text_snapshot"],
        total_seen=total,
        answered_count=answered,
        correct_count=correct,
        incorrect_count=incorrect,
        unanswered_count=unanswered,
        correct_pct=pct(correct),
        incorrect_pct=pct(incorrect),
        unanswered_pct=pct(unanswered),
        difficulty_rank=rank,
        insufficient_data=insufficient_data,
    )


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.analytics_repo = AnalyticsRepository(session)
        self.quiz_repo = QuizRepository(session)

    # ── Student ────────────────────────────────────────────────────────────────

    async def get_student_analytics(self, student_id: UUID) -> StudentAnalyticsResponse:
        row = await self.analytics_repo.get_student_stats(student_id)

        avg_score = row["average_score"]
        best_score = row["best_score"]

        # Percentages require knowing total possible marks — not tracked on attempts.
        # We store raw score; percentage is score/max_score*100, but max_score differs
        # per quiz. For a cross-quiz summary we express avg/best as a ratio of
        # score-to-score only (same unit). Percentage fields are None at summary level
        # because there is no single max_score denominator across quizzes.
        # Per-quiz percentages are available on the quiz analytics endpoint.
        avg_pct: Decimal | None = None
        best_pct: Decimal | None = None

        return StudentAnalyticsResponse(
            student_id=student_id,
            total_attempts=int(row["total_attempts"]),
            submitted_count=int(row["submitted_count"]),
            timed_out_count=int(row["timed_out_count"]),
            abandoned_count=int(row["abandoned_count"]),
            in_progress_count=int(row["in_progress_count"]),
            average_score=Decimal(str(avg_score)).quantize(_TWO_PLACES) if avg_score is not None else None,
            best_score=Decimal(str(best_score)).quantize(_TWO_PLACES) if best_score is not None else None,
            average_percentage=avg_pct,
            best_percentage=best_pct,
        )

    async def get_student_history(
        self,
        student_id: UUID,
        limit: int = 20,
        offset: int = 0,
        quiz_id: UUID | None = None,
    ) -> StudentHistoryResponse:
        rows, total = await self.analytics_repo.get_student_history(
            student_id, limit, offset, quiz_id
        )
        items = [
            AttemptHistoryItem(
                attempt_id=row["attempt_id"],
                quiz_id=row["quiz_id"],
                quiz_title=row["quiz_title"],
                attempt_number=int(row["attempt_number"]),
                status=row["status"].value if hasattr(row["status"], "value") else str(row["status"]),
                score=Decimal(str(row["score"])).quantize(_TWO_PLACES) if row["score"] is not None else None,
                started_at=row["started_at"],
                submitted_at=row["submitted_at"],
            )
            for row in rows
        ]
        return StudentHistoryResponse(items=items, total=total, limit=limit, offset=offset)

    # ── Quiz ──────────────────────────────────────────────────────────────────

    async def get_quiz_analytics(self, quiz_id: UUID, organization_id: UUID) -> QuizAnalyticsResponse:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")

        stats = await self.analytics_repo.get_quiz_stats(quiz_id, organization_id)
        anti_cheat = await self.analytics_repo.get_quiz_anti_cheat_stats(quiz_id, organization_id)
        most_common = await self.analytics_repo.get_quiz_most_common_event(quiz_id, organization_id)

        submitted = int(stats["submitted_count"])
        timed_out = int(stats["timed_out_count"])
        abandoned = int(stats["abandoned_count"])
        finished = submitted + timed_out + abandoned

        avg_score = stats["average_score"]
        avg_ts = anti_cheat["avg_tab_switches"]

        return QuizAnalyticsResponse(
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            total_attempts=int(stats["total_attempts"]),
            in_progress_count=int(stats["in_progress_count"]),
            submitted_count=submitted,
            timed_out_count=timed_out,
            abandoned_count=abandoned,
            completion_rate=_pct(submitted + timed_out, finished),
            abandonment_rate=_pct(abandoned, finished),
            timeout_rate=_pct(timed_out, finished),
            average_score=Decimal(str(avg_score)).quantize(_TWO_PLACES) if avg_score is not None else None,
            anti_cheat=QuizAntiCheatAnalytics(
                total_tab_switches=int(anti_cheat["total_tab_switches"]),
                average_tab_switches_per_attempt=(
                    Decimal(str(avg_ts)).quantize(_TWO_PLACES) if avg_ts is not None else None
                ),
                attempts_with_proctoring_events=int(anti_cheat["attempts_with_proctoring_events"]),
                most_common_proctoring_event=most_common,
            ),
        )

    async def get_quiz_question_analytics(
        self, quiz_id: UUID, organization_id: UUID
    ) -> QuizQuestionAnalyticsResponse:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")

        rows = await self.analytics_repo.get_quiz_question_stats(quiz_id, organization_id)

        rankable = [r for r in rows if int(r["total_seen"]) >= MIN_ATTEMPTS_FOR_RANKING]
        insufficient = [r for r in rows if int(r["total_seen"]) < MIN_ATTEMPTS_FOR_RANKING]

        # Sort rankable ascending by correct ratio: lowest = hardest = rank 1
        rankable_sorted = sorted(
            rankable,
            key=lambda r: int(r["correct_count"]) / int(r["total_seen"]),
        )

        items: list[QuestionAnalyticsItem] = []
        for rank, row in enumerate(rankable_sorted, start=1):
            items.append(_build_question_item(row, rank=rank, insufficient_data=False))
        for row in insufficient:
            items.append(_build_question_item(row, rank=None, insufficient_data=True))

        # total_finalized_attempts = distinct finalized attempts covering these questions
        finalized = len({r["question_id"] for r in rows})  # proxy: unique questions seen
        # More accurate: count the attempts that fed these rows via a separate query,
        # but that would need another round-trip. Use the max total_seen as the upper
        # bound — sufficient for display purposes.
        total_finalized = max((int(r["total_seen"]) for r in rows), default=0)

        return QuizQuestionAnalyticsResponse(
            quiz_id=quiz.id,
            total_finalized_attempts=total_finalized,
            min_attempts_for_ranking=MIN_ATTEMPTS_FOR_RANKING,
            questions=items,
        )

    # ── Admin ──────────────────────────────────────────────────────────────────

    async def get_admin_dashboard(self, organization_id: UUID) -> AdminDashboardResponse:
        org = await self.analytics_repo.get_org_stats(organization_id)
        total_events = await self.analytics_repo.get_org_total_proctoring_events(organization_id)
        recent_rows = await self.analytics_repo.get_recent_activity(organization_id, limit=10)

        avg_ts = org["avg_tab_switches"]

        recent = [
            RecentActivityItem(
                attempt_id=row["attempt_id"],
                student_id=row["student_id"],
                student_username=row["student_username"],
                quiz_id=row["quiz_id"],
                quiz_title=row["quiz_title"],
                status=row["status"].value if hasattr(row["status"], "value") else str(row["status"]),
                score=Decimal(str(row["score"])).quantize(_TWO_PLACES) if row["score"] is not None else None,
                started_at=row["started_at"],
                submitted_at=row["submitted_at"],
            )
            for row in recent_rows
        ]

        return AdminDashboardResponse(
            total_users=int(org["total_users"]),
            total_students=int(org["total_students"]),
            total_admins=int(org["total_admins"]),
            active_users=int(org["active_users"]),
            total_quizzes=int(org["total_quizzes"]),
            published_quizzes=int(org["published_quizzes"]),
            total_attempts=int(org["total_attempts"]),
            in_progress_attempts=int(org["in_progress_attempts"]),
            submitted_attempts=int(org["submitted_attempts"]),
            timed_out_attempts=int(org["timed_out_attempts"]),
            abandoned_attempts=int(org["abandoned_attempts"]),
            total_tab_switches=int(org["total_tab_switches"]),
            average_tab_switches_per_attempt=(
                Decimal(str(avg_ts)).quantize(_TWO_PLACES) if avg_ts is not None else None
            ),
            total_proctoring_events=total_events,
            recent_attempts=recent,
        )
