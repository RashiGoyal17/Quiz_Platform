import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_with_org
from app.database import get_db
from app.models.user import User
from app.schemas.quiz import QuestionResponse, QuestionUpdate
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/questions", tags=["questions"])


def _svc(db: AsyncSession = Depends(get_db)) -> QuizService:
    return QuizService(db)


def _handle(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Get a question by ID",
)
async def get_question(
    question_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin_with_org),
) -> QuestionResponse:
    try:
        question = await svc.get_question(question_id, admin.organization_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return QuestionResponse.model_validate(question)


@router.put(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Update a question (and optionally replace all options)",
)
async def update_question(
    question_id: uuid.UUID,
    body: QuestionUpdate,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin_with_org),
) -> QuestionResponse:
    options = body.options if "options" in body.model_fields_set else None
    updates = body.model_dump(exclude_unset=True, exclude={"options"})
    try:
        question = await svc.update_question(question_id, admin.organization_id, updates, options)
    except (LookupError, ValueError) as e:
        _handle(e)
    return QuestionResponse.model_validate(question)


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
)
async def delete_question(
    question_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin_with_org),
) -> None:
    try:
        await svc.delete_question(question_id, admin.organization_id)
    except (LookupError, ValueError) as e:
        _handle(e)
