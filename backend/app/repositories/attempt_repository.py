from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.attempt_question import AttemptQuestion
from app.models.attempt_question_option import AttemptQuestionOption
from app.models.enums import AttemptStatus
from app.models.proctoring_event import ProctoringEvent
from app.models.tab_switch_log import TabSwitchLog
from app.repositories.base_repository import BaseRepository


class AttemptRepository(BaseRepository[Attempt]):
    model = Attempt

    async def get_by_student(self, student_id: UUID) -> list[Attempt]:
        result = await self.session.execute(
            select(Attempt).where(Attempt.student_id == student_id)
        )
        return list(result.scalars().all())

    async def get_by_quiz(self, quiz_id: UUID) -> list[Attempt]:
        result = await self.session.execute(
            select(Attempt).where(Attempt.quiz_id == quiz_id)
        )
        return list(result.scalars().all())

    async def get_student_quiz_attempts(self, student_id: UUID, quiz_id: UUID) -> list[Attempt]:
        result = await self.session.execute(
            select(Attempt)
            .where(Attempt.student_id == student_id, Attempt.quiz_id == quiz_id)
            .order_by(Attempt.attempt_number)
        )
        return list(result.scalars().all())

    async def count_student_quiz_attempts(self, student_id: UUID, quiz_id: UUID) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(Attempt.id)).where(
                Attempt.student_id == student_id,
                Attempt.quiz_id == quiz_id,
            )
        )
        return result.scalar_one()

    async def get_active_attempt(self, student_id: UUID, quiz_id: UUID) -> Attempt | None:
        result = await self.session.execute(
            select(Attempt).where(
                Attempt.student_id == student_id,
                Attempt.quiz_id == quiz_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_filtered(
        self,
        organization_id: UUID,
        quiz_id: UUID | None = None,
        student_id: UUID | None = None,
        status: AttemptStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Attempt]:
        q = select(Attempt).where(Attempt.organization_id == organization_id)
        if quiz_id is not None:
            q = q.where(Attempt.quiz_id == quiz_id)
        if student_id is not None:
            q = q.where(Attempt.student_id == student_id)
        if status is not None:
            q = q.where(Attempt.status == status)
        q = q.order_by(Attempt.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id_scoped(self, attempt_id: UUID, organization_id: UUID) -> Attempt | None:
        result = await self.session.execute(
            select(Attempt).where(
                Attempt.id == attempt_id,
                Attempt.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()


class AttemptQuestionRepository(BaseRepository[AttemptQuestion]):
    model = AttemptQuestion

    async def get_by_attempt(self, attempt_id: UUID) -> list[AttemptQuestion]:
        result = await self.session.execute(
            select(AttemptQuestion)
            .where(AttemptQuestion.attempt_id == attempt_id)
            .order_by(AttemptQuestion.position)
        )
        return list(result.scalars().all())

    async def get_with_options(self, attempt_question_id: UUID) -> AttemptQuestion | None:
        result = await self.session.execute(
            select(AttemptQuestion)
            .where(AttemptQuestion.id == attempt_question_id)
            .options(selectinload(AttemptQuestion.options))
        )
        return result.scalar_one_or_none()

    async def get_by_attempt_with_details(self, attempt_id: UUID) -> list[AttemptQuestion]:
        """Load questions with snapshotted options and student answer — used for grading and results."""
        result = await self.session.execute(
            select(AttemptQuestion)
            .where(AttemptQuestion.attempt_id == attempt_id)
            .options(
                selectinload(AttemptQuestion.options),
                selectinload(AttemptQuestion.answer),
            )
            .order_by(AttemptQuestion.position)
        )
        return list(result.scalars().all())


class TabSwitchLogRepository(BaseRepository[TabSwitchLog]):
    model = TabSwitchLog

    async def get_by_attempt(self, attempt_id: UUID) -> list[TabSwitchLog]:
        result = await self.session.execute(
            select(TabSwitchLog)
            .where(TabSwitchLog.attempt_id == attempt_id)
            .order_by(TabSwitchLog.switched_at)
        )
        return list(result.scalars().all())


class ProctoringEventRepository(BaseRepository[ProctoringEvent]):
    model = ProctoringEvent

    async def get_by_attempt(self, attempt_id: UUID) -> list[ProctoringEvent]:
        """Return all proctoring events for an attempt ordered chronologically."""
        result = await self.session.execute(
            select(ProctoringEvent)
            .where(ProctoringEvent.attempt_id == attempt_id)
            .order_by(ProctoringEvent.occurred_at)
        )
        return list(result.scalars().all())


class AttemptAnswerRepository(BaseRepository[AttemptAnswer]):
    model = AttemptAnswer

    async def get_by_attempt_question(self, attempt_question_id: UUID) -> AttemptAnswer | None:
        result = await self.session.execute(
            select(AttemptAnswer).where(
                AttemptAnswer.attempt_question_id == attempt_question_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_attempt(self, attempt_id: UUID) -> list[AttemptAnswer]:
        result = await self.session.execute(
            select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id)
        )
        return list(result.scalars().all())
