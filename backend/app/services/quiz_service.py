import csv
import io
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError
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
from app.schemas.quiz import BulkImportResponse, BulkImportRowError, QuestionCreate

MAX_IMPORT_ROWS = 500

_CORRECT_LETTER_MAP = {"A": 0, "B": 1, "C": 2, "D": 3}


def _parse_csv_rows(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for raw in reader:
        correct_letter = (raw.get("correct_option") or "").strip().upper()
        correct_index = _CORRECT_LETTER_MAP.get(correct_letter, -1)
        options = [
            {"text": (raw.get(f"option_{k}") or "").strip(), "is_correct": i == correct_index}
            for i, k in enumerate(["a", "b", "c", "d"])
        ]
        rows.append({
            "text": (raw.get("text") or "").strip(),
            "explanation": (raw.get("explanation") or "").strip() or None,
            "marks": (raw.get("marks") or "").strip(),
            "negative_marks": (raw.get("negative_marks") or "0").strip() or "0",
            "options": options,
        })
    return rows


def _parse_json_rows(content: bytes) -> list[dict]:
    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array")
    return data


# Phase 9B note: every method below that touches a question bank, question,
# or quiz takes an `organization_id` (the requesting admin's organization) and
# resolves resources through organization-scoped repository lookups. A
# resource that exists but belongs to another organization is treated
# identically to one that does not exist — `LookupError` (-> 404), never a
# separate "forbidden" path — per Phase 9B "Tenant Boundary Rules" #3.


class QuizService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.quiz_repo = QuizRepository(session)
        self.question_repo = QuestionRepository(session)
        self.bank_repo = QuestionBankRepository(session)
        self.option_repo = QuestionOptionRepository(session)

    # ── Question Banks ─────────────────────────────────────────────────────

    async def create_question_bank(
        self,
        creator_id: UUID,
        organization_id: UUID,
        name: str,
        description: str | None = None,
    ) -> QuestionBank:
        bank = QuestionBank(
            name=name,
            description=description,
            creator_id=creator_id,
            organization_id=organization_id,
        )
        return await self.bank_repo.create(bank)

    async def list_question_banks(self, organization_id: UUID) -> list[QuestionBank]:
        return await self.bank_repo.get_by_organization(organization_id)

    async def get_question_bank(self, bank_id: UUID, organization_id: UUID) -> QuestionBank:
        bank = await self.bank_repo.get_by_id_scoped(bank_id, organization_id)
        if bank is None:
            raise LookupError("Question bank not found")
        return bank

    async def update_question_bank(
        self, bank_id: UUID, organization_id: UUID, updates: dict
    ) -> QuestionBank:
        bank = await self.bank_repo.get_by_id_scoped(bank_id, organization_id)
        if bank is None:
            raise LookupError("Question bank not found")
        for field, value in updates.items():
            setattr(bank, field, value)
        await self.session.flush()
        await self.session.refresh(bank)
        return bank

    async def delete_question_bank(self, bank_id: UUID, organization_id: UUID) -> None:
        bank = await self.bank_repo.get_by_id_scoped(bank_id, organization_id)
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
        organization_id: UUID,
        text: str,
        marks: int,
        options: list,
        requester_id: UUID | None = None,
        negative_marks: Decimal = Decimal("0.00"),
        explanation: str | None = None,
    ) -> Question:
        bank = await self.bank_repo.get_by_id_scoped(bank_id, organization_id)
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

    async def list_questions_in_bank(self, bank_id: UUID, organization_id: UUID) -> list[Question]:
        bank = await self.bank_repo.get_by_id_scoped(bank_id, organization_id)
        if bank is None:
            raise LookupError("Question bank not found")
        return await self.question_repo.get_by_bank_with_options(bank_id)

    async def get_question(self, question_id: UUID, organization_id: UUID) -> Question:
        question = await self.question_repo.get_with_options_scoped(question_id, organization_id)
        if question is None:
            raise LookupError("Question not found")
        return question

    async def update_question(
        self,
        question_id: UUID,
        organization_id: UUID,
        updates: dict,
        options: list | None = None,
    ) -> Question:
        question = await self.question_repo.get_with_options_scoped(question_id, organization_id)
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

    async def delete_question(self, question_id: UUID, organization_id: UUID) -> None:
        question = await self.question_repo.get_with_options_scoped(question_id, organization_id)
        if question is None:
            raise LookupError("Question not found")
        try:
            await self.question_repo.delete(question)
        except IntegrityError:
            raise ValueError(
                "Cannot delete question: it is assigned to one or more quizzes. "
                "Remove it from all quizzes first."
            )

    async def bulk_import_questions(
        self,
        bank_id: UUID,
        organization_id: UUID,
        file_content: bytes,
        fmt: str,
    ) -> BulkImportResponse:
        bank = await self.bank_repo.get_by_id_scoped(bank_id, organization_id)
        if bank is None:
            raise LookupError("Question bank not found")

        if fmt == "csv":
            rows = _parse_csv_rows(file_content)
        else:
            rows = _parse_json_rows(file_content)

        if len(rows) > MAX_IMPORT_ROWS:
            raise ValueError(f"Import exceeds maximum of {MAX_IMPORT_ROWS} rows")

        errors: list[BulkImportRowError] = []
        imported = 0
        failed_rows = 0

        for i, raw in enumerate(rows):
            row_num = i + 1
            try:
                validated = QuestionCreate.model_validate(raw)
            except ValidationError as exc:
                failed_rows += 1
                for e in exc.errors():
                    loc = e.get("loc", ())
                    field = str(loc[0]) if loc else None
                    errors.append(BulkImportRowError(row=row_num, field=field, message=e["msg"]))
                continue

            await self.create_question(
                bank_id=bank_id,
                organization_id=organization_id,
                text=validated.text,
                marks=validated.marks,
                negative_marks=validated.negative_marks,
                explanation=validated.explanation,
                options=validated.options,
            )
            imported += 1

        return BulkImportResponse(imported=imported, failed=failed_rows, errors=errors)

    # ── Quizzes ────────────────────────────────────────────────────────────

    async def create_quiz(self, creator_id: UUID, organization_id: UUID, title: str, **kwargs) -> Quiz:
        quiz = Quiz(
            creator_id=creator_id,
            organization_id=organization_id,
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

    async def list_quizzes(self, organization_id: UUID) -> list[Quiz]:
        return await self.quiz_repo.get_by_organization(organization_id)

    async def list_available_quizzes_for_student(self) -> list[Quiz]:
        # Students are global (Phase 9B "Tenant Boundary Rules" #7) — they may
        # discover and attempt published quizzes from any organization.
        return await self.quiz_repo.get_available_for_student(datetime.now(timezone.utc))

    async def get_quiz(self, quiz_id: UUID, organization_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        return quiz

    async def update_quiz(self, quiz_id: UUID, organization_id: UUID, updates: dict) -> Quiz:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        for field, value in updates.items():
            setattr(quiz, field, value)
        await self.session.flush()
        await self.session.refresh(quiz)
        return quiz

    # ── Publish / Unpublish ────────────────────────────────────────────────

    async def publish_quiz(self, quiz_id: UUID, organization_id: UUID, requester_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        assigned = await self.quiz_repo.get_quiz_questions_ordered(quiz_id)
        if not assigned:
            raise ValueError("Cannot publish a quiz with no questions assigned")
        quiz.is_published = True
        await self.session.flush()
        await self.session.refresh(quiz)
        return quiz

    async def unpublish_quiz(self, quiz_id: UUID, organization_id: UUID, requester_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
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
        organization_id: UUID,
        question_id: UUID,
        position: int,
        requester_id: UUID,
        marks_override: Decimal | None = None,
    ) -> QuizQuestion:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")

        # A quiz may only reference questions whose bank belongs to the same
        # organization — cross-tenant references are never created
        # (Phase 9B "Tenant Boundary Rules" #5).
        question = await self.question_repo.get_with_options_scoped(question_id, organization_id)
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
        self, quiz_id: UUID, organization_id: UUID, question_id: UUID, requester_id: UUID
    ) -> None:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        await self.quiz_repo.remove_question(quiz_id, question_id)

    async def list_quiz_questions(self, quiz_id: UUID, organization_id: UUID) -> list[QuizQuestion]:
        quiz = await self.quiz_repo.get_by_id_scoped(quiz_id, organization_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        return await self.quiz_repo.get_quiz_questions_with_details(quiz_id)
