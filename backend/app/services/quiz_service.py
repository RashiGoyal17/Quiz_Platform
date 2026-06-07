from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.question_bank import QuestionBank
from app.models.question_option import QuestionOption
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.repositories.question_repository import (
    QuestionBankRepository,
    QuestionOptionRepository,
    QuestionRepository,
)
from app.repositories.quiz_repository import QuizRepository


class QuizService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.quiz_repo = QuizRepository(session)
        self.question_repo = QuestionRepository(session)
        self.bank_repo = QuestionBankRepository(session)
        self.option_repo = QuestionOptionRepository(session)

    # ── Question Banks ─────────────────────────────────────────────────────

    async def create_question_bank(
        self, creator_id: UUID, name: str, description: str | None = None
    ) -> QuestionBank:
        bank = QuestionBank(name=name, description=description, creator_id=creator_id)
        return await self.bank_repo.create(bank)

    async def list_question_banks(self) -> list[QuestionBank]:
        return list(await self.bank_repo.get_all(limit=1000))

    async def get_question_bank(self, bank_id: UUID) -> QuestionBank:
        bank = await self.bank_repo.get_by_id(bank_id)
        if bank is None:
            raise LookupError("Question bank not found")
        return bank

    async def update_question_bank(self, bank_id: UUID, updates: dict) -> QuestionBank:
        bank = await self.bank_repo.get_by_id(bank_id)
        if bank is None:
            raise LookupError("Question bank not found")
        for field, value in updates.items():
            setattr(bank, field, value)
        await self.session.flush()
        await self.session.refresh(bank)
        return bank

    async def delete_question_bank(self, bank_id: UUID) -> None:
        bank = await self.bank_repo.get_by_id(bank_id)
        if bank is None:
            raise LookupError("Question bank not found")
        try:
            await self.bank_repo.delete(bank)
        except IntegrityError:
            raise ValueError(
                "Cannot delete bank: questions are assigned to quizzes. "
                "Remove them from all quizzes first."
            )

    # ── Questions ──────────────────────────────────────────────────────────

    async def create_question(
        self,
        bank_id: UUID,
        text: str,
        marks: int,
        options: list,
        requester_id: UUID | None = None,
        negative_marks: Decimal = Decimal("0.00"),
        explanation: str | None = None,
    ) -> Question:
        bank = await self.bank_repo.get_by_id(bank_id)
        if bank is None:
            raise LookupError("Question bank not found")

        question = Question(
            question_bank_id=bank_id,
            text=text,
            explanation=explanation,
            marks=marks,
            negative_marks=negative_marks,
        )
        question = await self.question_repo.create(question)

        for i, opt in enumerate(options):
            self.session.add(
                QuestionOption(
                    question_id=question.id,
                    text=opt.text,
                    is_correct=opt.is_correct,
                    position=i,
                )
            )
        await self.session.flush()

        return await self.question_repo.get_with_options(question.id)  # type: ignore[return-value]

    async def list_questions_in_bank(self, bank_id: UUID) -> list[Question]:
        bank = await self.bank_repo.get_by_id(bank_id)
        if bank is None:
            raise LookupError("Question bank not found")
        return await self.question_repo.get_by_bank_with_options(bank_id)

    async def get_question(self, question_id: UUID) -> Question:
        question = await self.question_repo.get_with_options(question_id)
        if question is None:
            raise LookupError("Question not found")
        return question

    async def update_question(
        self, question_id: UUID, updates: dict, options: list | None = None
    ) -> Question:
        question = await self.question_repo.get_with_options(question_id)
        if question is None:
            raise LookupError("Question not found")

        for field, value in updates.items():
            setattr(question, field, value)

        if options is not None:
            for opt in list(question.options):
                await self.session.delete(opt)
            await self.session.flush()
            for i, opt_data in enumerate(options):
                self.session.add(
                    QuestionOption(
                        question_id=question.id,
                        text=opt_data.text,
                        is_correct=opt_data.is_correct,
                        position=i,
                    )
                )

        await self.session.flush()
        return await self.question_repo.get_with_options(question_id)  # type: ignore[return-value]

    async def delete_question(self, question_id: UUID) -> None:
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            raise LookupError("Question not found")
        try:
            await self.question_repo.delete(question)
        except IntegrityError:
            raise ValueError(
                "Cannot delete question: it is assigned to one or more quizzes. "
                "Remove it from all quizzes first."
            )

    # ── Quizzes ────────────────────────────────────────────────────────────

    async def create_quiz(self, creator_id: UUID, title: str, **kwargs) -> Quiz:
        quiz = Quiz(
            creator_id=creator_id,
            title=title,
            duration_minutes=kwargs.get("duration_minutes", 60),
            description=kwargs.get("description"),
            start_time=kwargs.get("start_time"),
            end_time=kwargs.get("end_time"),
            shuffle_questions=kwargs.get("shuffle_questions", False),
            shuffle_options=kwargs.get("shuffle_options", False),
            max_attempts=kwargs.get("max_attempts", 1),
            proctoring_enabled=kwargs.get("proctoring_enabled", False),
            max_tab_switches=kwargs.get("max_tab_switches"),
        )
        return await self.quiz_repo.create(quiz)

    async def list_quizzes(self) -> list[Quiz]:
        return list(await self.quiz_repo.get_all(limit=1000))

    async def list_available_quizzes_for_student(self) -> list[Quiz]:
        return await self.quiz_repo.get_available_for_student(datetime.now(timezone.utc))

    async def get_quiz(self, quiz_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        return quiz

    async def update_quiz(self, quiz_id: UUID, updates: dict) -> Quiz:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        for field, value in updates.items():
            setattr(quiz, field, value)
        await self.session.flush()
        await self.session.refresh(quiz)
        return quiz

    # ── Publish / Unpublish ────────────────────────────────────────────────

    async def publish_quiz(self, quiz_id: UUID, requester_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        assigned = await self.quiz_repo.get_quiz_questions_ordered(quiz_id)
        if not assigned:
            raise ValueError("Cannot publish a quiz with no questions assigned")
        quiz.is_published = True
        await self.session.flush()
        await self.session.refresh(quiz)
        return quiz

    async def unpublish_quiz(self, quiz_id: UUID, requester_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        quiz.is_published = False
        await self.session.flush()
        await self.session.refresh(quiz)
        return quiz

    # ── Quiz Questions ─────────────────────────────────────────────────────

    async def add_question_to_quiz(
        self,
        quiz_id: UUID,
        question_id: UUID,
        position: int,
        requester_id: UUID,
        marks_override: Decimal | None = None,
    ) -> QuizQuestion:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")

        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            raise LookupError("Question not found")

        existing = await self.quiz_repo.get_quiz_questions_ordered(quiz_id)
        if any(q.question_id == question_id for q in existing):
            raise ValueError("Question is already assigned to this quiz")

        qq = QuizQuestion(
            quiz_id=quiz_id,
            question_id=question_id,
            position=position,
            marks_override=marks_override,
        )
        await self.quiz_repo.add_question(qq)

        rows = await self.quiz_repo.get_quiz_questions_with_details(quiz_id)
        return next(r for r in rows if r.question_id == question_id)

    async def remove_question_from_quiz(
        self, quiz_id: UUID, question_id: UUID, requester_id: UUID
    ) -> None:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        await self.quiz_repo.remove_question(quiz_id, question_id)

    async def list_quiz_questions(self, quiz_id: UUID) -> list[QuizQuestion]:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        return await self.quiz_repo.get_quiz_questions_with_details(quiz_id)
