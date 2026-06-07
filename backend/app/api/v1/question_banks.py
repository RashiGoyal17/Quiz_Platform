import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.quiz import (
    QuestionBankCreate,
    QuestionBankResponse,
    QuestionBankUpdate,
    QuestionCreate,
    QuestionResponse,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/question-banks", tags=["question-banks"])


def _svc(db: AsyncSession = Depends(get_db)) -> QuizService:
    return QuizService(db)


def _handle(exc: Exception, not_found_msg: str | None = None) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ── Question Bank CRUD ────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=QuestionBankResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question bank",
)
async def create_question_bank(
    body: QuestionBankCreate,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> QuestionBankResponse:
    bank = await svc.create_question_bank(
        creator_id=admin.id,
        name=body.name,
        description=body.description,
    )
    return QuestionBankResponse.model_validate(bank)


@router.get(
    "",
    response_model=list[QuestionBankResponse],
    summary="List all question banks",
)
async def list_question_banks(
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> list[QuestionBankResponse]:
    banks = await svc.list_question_banks()
    return [QuestionBankResponse.model_validate(b) for b in banks]


@router.get(
    "/{bank_id}",
    response_model=QuestionBankResponse,
    summary="Get a question bank by ID",
)
async def get_question_bank(
    bank_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> QuestionBankResponse:
    try:
        bank = await svc.get_question_bank(bank_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return QuestionBankResponse.model_validate(bank)


@router.put(
    "/{bank_id}",
    response_model=QuestionBankResponse,
    summary="Update a question bank",
)
async def update_question_bank(
    bank_id: uuid.UUID,
    body: QuestionBankUpdate,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> QuestionBankResponse:
    updates = body.model_dump(exclude_unset=True)
    try:
        bank = await svc.update_question_bank(bank_id, updates)
    except (LookupError, ValueError) as e:
        _handle(e)
    return QuestionBankResponse.model_validate(bank)


@router.delete(
    "/{bank_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question bank",
)
async def delete_question_bank(
    bank_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> None:
    try:
        await svc.delete_question_bank(bank_id)
    except (LookupError, ValueError) as e:
        _handle(e)


# ── Questions scoped to a bank ────────────────────────────────────────────────

@router.post(
    "/{bank_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a question bank",
)
async def create_question(
    bank_id: uuid.UUID,
    body: QuestionCreate,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> QuestionResponse:
    try:
        question = await svc.create_question(
            bank_id=bank_id,
            text=body.text,
            marks=body.marks,
            negative_marks=body.negative_marks,
            explanation=body.explanation,
            options=body.options,
            requester_id=admin.id,
        )
    except (LookupError, ValueError) as e:
        _handle(e)
    return QuestionResponse.model_validate(question)


@router.get(
    "/{bank_id}/questions",
    response_model=list[QuestionResponse],
    summary="List all questions in a question bank",
)
async def list_questions(
    bank_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> list[QuestionResponse]:
    try:
        questions = await svc.list_questions_in_bank(bank_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [QuestionResponse.model_validate(q) for q in questions]
