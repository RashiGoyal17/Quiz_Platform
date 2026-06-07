from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select

from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.repositories.base_repository import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    model = Quiz

    async def get_by_creator(self, creator_id: UUID) -> list[Quiz]:
        result = await self.session.execute(
            select(Quiz).where(Quiz.creator_id == creator_id)
        )
        return list(result.scalars().all())

    async def get_published(self, limit: int = 100, offset: int = 0) -> list[Quiz]:
        result = await self.session.execute(
            select(Quiz).where(Quiz.is_published.is_(True)).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_available_for_student(self, now: datetime) -> list[Quiz]:
        """Published quizzes whose optional time window contains `now`."""
        result = await self.session.execute(
            select(Quiz).where(
                Quiz.is_published.is_(True),
                or_(Quiz.start_time.is_(None), Quiz.start_time <= now),
                or_(Quiz.end_time.is_(None), Quiz.end_time >= now),
            )
        )
        return list(result.scalars().all())

    async def add_question(self, quiz_question: QuizQuestion) -> QuizQuestion:
        self.session.add(quiz_question)
        await self.session.flush()
        return quiz_question

    async def remove_question(self, quiz_id: UUID, question_id: UUID) -> None:
        result = await self.session.execute(
            select(QuizQuestion).where(
                QuizQuestion.quiz_id == quiz_id,
                QuizQuestion.question_id == question_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            await self.session.delete(row)
            await self.session.flush()

    async def get_quiz_questions_ordered(self, quiz_id: UUID) -> list[QuizQuestion]:
        result = await self.session.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.position)
        )
        return list(result.scalars().all())

    async def get_quiz_questions_with_details(self, quiz_id: UUID) -> list[QuizQuestion]:
        from sqlalchemy.orm import selectinload
        from app.models.question import Question
        result = await self.session.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .options(
                selectinload(QuizQuestion.question).selectinload(Question.options)
            )
            .order_by(QuizQuestion.position)
        )
        return list(result.scalars().all())
