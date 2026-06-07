from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.attempt_question import AttemptQuestion
from app.models.enums import AttemptStatus, ProctoringEventType, UserRole
from app.models.proctoring_event import ProctoringEvent
from app.models.quiz import Quiz
from app.models.user import User


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Student ───────────────────────────────────────────────────────────────

    async def get_student_stats(self, student_id: UUID):
        result = await self.session.execute(
            select(
                func.count(Attempt.id).label("total_attempts"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.SUBMITTED
                ).label("submitted_count"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.TIMED_OUT
                ).label("timed_out_count"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.ABANDONED
                ).label("abandoned_count"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.IN_PROGRESS
                ).label("in_progress_count"),
                func.avg(Attempt.score).filter(
                    Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT])
                ).label("average_score"),
                func.max(Attempt.score).filter(
                    Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT])
                ).label("best_score"),
            ).where(Attempt.student_id == student_id)
        )
        return result.mappings().one()

    async def get_student_history(
        self,
        student_id: UUID,
        limit: int = 20,
        offset: int = 0,
        quiz_id: UUID | None = None,
    ) -> tuple[list, int]:
        base_where = [Attempt.student_id == student_id]
        if quiz_id is not None:
            base_where.append(Attempt.quiz_id == quiz_id)

        data_q = (
            select(
                Attempt.id.label("attempt_id"),
                Attempt.quiz_id,
                Quiz.title.label("quiz_title"),
                Attempt.attempt_number,
                Attempt.status,
                Attempt.score,
                Attempt.started_at,
                Attempt.submitted_at,
            )
            .join(Quiz, Quiz.id == Attempt.quiz_id)
            .where(*base_where)
            .order_by(Attempt.started_at.desc())
            .limit(limit)
            .offset(offset)
        )

        count_q = select(func.count(Attempt.id)).where(*base_where)

        rows_result = await self.session.execute(data_q)
        count_result = await self.session.execute(count_q)

        return list(rows_result.mappings().all()), count_result.scalar_one()

    # ── Quiz ──────────────────────────────────────────────────────────────────

    async def get_quiz_stats(self, quiz_id: UUID, organization_id: UUID):
        result = await self.session.execute(
            select(
                func.count(Attempt.id).label("total_attempts"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.IN_PROGRESS
                ).label("in_progress_count"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.SUBMITTED
                ).label("submitted_count"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.TIMED_OUT
                ).label("timed_out_count"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.ABANDONED
                ).label("abandoned_count"),
                func.avg(Attempt.score).filter(
                    Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT])
                ).label("average_score"),
            ).where(Attempt.quiz_id == quiz_id, Attempt.organization_id == organization_id)
        )
        return result.mappings().one()

    async def get_quiz_anti_cheat_stats(self, quiz_id: UUID, organization_id: UUID) -> dict:
        ts_result = await self.session.execute(
            select(
                func.coalesce(func.sum(Attempt.tab_switch_count), 0).label("total_tab_switches"),
                func.avg(Attempt.tab_switch_count).label("avg_tab_switches"),
            ).where(Attempt.quiz_id == quiz_id, Attempt.organization_id == organization_id)
        )
        ts_row = ts_result.mappings().one()

        pe_result = await self.session.execute(
            select(
                func.count(func.distinct(ProctoringEvent.attempt_id)).label("attempts_with_events")
            )
            .select_from(ProctoringEvent)
            .join(Attempt, Attempt.id == ProctoringEvent.attempt_id)
            .where(Attempt.quiz_id == quiz_id, Attempt.organization_id == organization_id)
        )
        pe_row = pe_result.mappings().one()

        return {
            "total_tab_switches": ts_row["total_tab_switches"],
            "avg_tab_switches": ts_row["avg_tab_switches"],
            "attempts_with_proctoring_events": pe_row["attempts_with_events"],
        }

    async def get_quiz_most_common_event(self, quiz_id: UUID, organization_id: UUID) -> str | None:
        result = await self.session.execute(
            select(ProctoringEvent.event_type)
            .join(Attempt, Attempt.id == ProctoringEvent.attempt_id)
            .where(Attempt.quiz_id == quiz_id, Attempt.organization_id == organization_id)
            .group_by(ProctoringEvent.event_type)
            .order_by(func.count(ProctoringEvent.id).desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        # row is a ProctoringEventType enum; return its string value
        return row.value if isinstance(row, ProctoringEventType) else str(row)

    async def get_quiz_question_stats(self, quiz_id: UUID, organization_id: UUID) -> list:
        result = await self.session.execute(
            select(
                AttemptQuestion.question_id,
                func.max(AttemptQuestion.question_text_snapshot).label(
                    "question_text_snapshot"
                ),
                func.count(AttemptQuestion.id).label("total_seen"),
                func.count(AttemptAnswer.id).filter(
                    AttemptAnswer.selected_option_id.isnot(None)
                ).label("answered_count"),
                func.count(AttemptAnswer.id).filter(
                    AttemptAnswer.is_correct.is_(True)
                ).label("correct_count"),
                func.count(AttemptAnswer.id).filter(
                    AttemptAnswer.is_correct.is_(False)
                ).label("incorrect_count"),
            )
            .select_from(AttemptQuestion)
            .join(Attempt, Attempt.id == AttemptQuestion.attempt_id)
            .outerjoin(AttemptAnswer, AttemptAnswer.attempt_question_id == AttemptQuestion.id)
            .where(
                Attempt.quiz_id == quiz_id,
                Attempt.organization_id == organization_id,
                Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT]),
            )
            .group_by(AttemptQuestion.question_id)
        )
        return list(result.mappings().all())

    # ── Admin (organization-scoped) ───────────────────────────────────────────
    #
    # These queries back the admin dashboard. Per Phase 9B "Tenant Boundary
    # Rules" #10, they are scoped to the requesting admin's organization —
    # there is no platform-wide ("all organizations") aggregate exposed to
    # regular admins. Students are global (no organization_id), so "students
    # belonging to" an organization is defined as "students who have attempted
    # at least one of that organization's quizzes."

    async def get_org_stats(self, organization_id: UUID):
        admin_result = await self.session.execute(
            select(
                func.count(User.id).label("total_admins"),
                func.count(User.id).filter(User.is_active.is_(True)).label("active_admins"),
            ).where(User.role == UserRole.ADMIN, User.organization_id == organization_id)
        )
        admin_row = admin_result.mappings().one()

        student_result = await self.session.execute(
            select(
                func.count(func.distinct(Attempt.student_id)).label("total_students"),
                func.count(func.distinct(Attempt.student_id)).filter(
                    User.is_active.is_(True)
                ).label("active_students"),
            )
            .select_from(Attempt)
            .join(User, User.id == Attempt.student_id)
            .where(Attempt.organization_id == organization_id)
        )
        student_row = student_result.mappings().one()

        quiz_result = await self.session.execute(
            select(
                func.count(Quiz.id).label("total_quizzes"),
                func.count(Quiz.id).filter(Quiz.is_published.is_(True)).label("published_quizzes"),
            ).where(Quiz.organization_id == organization_id)
        )
        quiz_row = quiz_result.mappings().one()

        attempt_result = await self.session.execute(
            select(
                func.count(Attempt.id).label("total_attempts"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.IN_PROGRESS
                ).label("in_progress_attempts"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.SUBMITTED
                ).label("submitted_attempts"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.TIMED_OUT
                ).label("timed_out_attempts"),
                func.count(Attempt.id).filter(
                    Attempt.status == AttemptStatus.ABANDONED
                ).label("abandoned_attempts"),
                func.coalesce(func.sum(Attempt.tab_switch_count), 0).label("total_tab_switches"),
                func.avg(Attempt.tab_switch_count).label("avg_tab_switches"),
            ).where(Attempt.organization_id == organization_id)
        )
        attempt_row = attempt_result.mappings().one()

        total_admins = admin_row["total_admins"]
        total_students = student_row["total_students"]
        active_admins = admin_row["active_admins"]
        active_students = student_row["active_students"]

        return {
            "total_users": total_admins + total_students,
            "total_students": total_students,
            "total_admins": total_admins,
            "active_users": active_admins + active_students,
            "total_quizzes": quiz_row["total_quizzes"],
            "published_quizzes": quiz_row["published_quizzes"],
            "total_attempts": attempt_row["total_attempts"],
            "in_progress_attempts": attempt_row["in_progress_attempts"],
            "submitted_attempts": attempt_row["submitted_attempts"],
            "timed_out_attempts": attempt_row["timed_out_attempts"],
            "abandoned_attempts": attempt_row["abandoned_attempts"],
            "total_tab_switches": attempt_row["total_tab_switches"],
            "avg_tab_switches": attempt_row["avg_tab_switches"],
        }

    async def get_org_total_proctoring_events(self, organization_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(ProctoringEvent.id))
            .select_from(ProctoringEvent)
            .join(Attempt, Attempt.id == ProctoringEvent.attempt_id)
            .where(Attempt.organization_id == organization_id)
        )
        return result.scalar_one()

    async def get_recent_activity(self, organization_id: UUID, limit: int = 10) -> list:
        result = await self.session.execute(
            select(
                Attempt.id.label("attempt_id"),
                Attempt.status,
                Attempt.score,
                Attempt.started_at,
                Attempt.submitted_at,
                User.id.label("student_id"),
                User.username.label("student_username"),
                Quiz.id.label("quiz_id"),
                Quiz.title.label("quiz_title"),
            )
            .join(User, User.id == Attempt.student_id)
            .join(Quiz, Quiz.id == Attempt.quiz_id)
            .where(Attempt.organization_id == organization_id)
            .order_by(Attempt.started_at.desc())
            .limit(limit)
        )
        return list(result.mappings().all())
