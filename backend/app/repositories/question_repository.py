from uuid import UUID

from sqlalchemy import select

from app.models.question import Question
from app.models.question_bank import QuestionBank
from app.models.question_option import QuestionOption
from app.repositories.base_repository import BaseRepository


class QuestionBankRepository(BaseRepository[QuestionBank]):
    model = QuestionBank

    async def get_by_creator(self, creator_id: UUID) -> list[QuestionBank]:
        result = await self.session.execute(
            select(QuestionBank).where(QuestionBank.creator_id == creator_id)
        )
        return list(result.scalars().all())

    async def get_by_organization(self, organization_id: UUID) -> list[QuestionBank]:
        result = await self.session.execute(
            select(QuestionBank).where(QuestionBank.organization_id == organization_id)
        )
        return list(result.scalars().all())

    async def get_by_id_scoped(self, bank_id: UUID, organization_id: UUID) -> QuestionBank | None:
        result = await self.session.execute(
            select(QuestionBank).where(
                QuestionBank.id == bank_id,
                QuestionBank.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()


class QuestionRepository(BaseRepository[Question]):
    model = Question

    async def get_by_bank(self, question_bank_id: UUID) -> list[Question]:
        result = await self.session.execute(
            select(Question).where(Question.question_bank_id == question_bank_id)
        )
        return list(result.scalars().all())

    async def get_with_options(self, question_id: UUID) -> Question | None:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        return result.scalar_one_or_none()

    async def get_with_options_scoped(
        self, question_id: UUID, organization_id: UUID
    ) -> Question | None:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(Question)
            .join(QuestionBank, QuestionBank.id == Question.question_bank_id)
            .where(
                Question.id == question_id,
                QuestionBank.organization_id == organization_id,
            )
            .options(selectinload(Question.options))
        )
        return result.scalar_one_or_none()

    async def get_by_bank_with_options(self, question_bank_id: UUID) -> list[Question]:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(Question)
            .where(Question.question_bank_id == question_bank_id)
            .options(selectinload(Question.options))
            .order_by(Question.created_at)
        )
        return list(result.scalars().all())


class QuestionOptionRepository(BaseRepository[QuestionOption]):
    model = QuestionOption

    async def get_by_question(self, question_id: UUID) -> list[QuestionOption]:
        result = await self.session.execute(
            select(QuestionOption)
            .where(QuestionOption.question_id == question_id)
            .order_by(QuestionOption.position)
        )
        return list(result.scalars().all())
