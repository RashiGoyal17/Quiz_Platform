import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_student
from app.database import get_db
from app.models.user import User
from app.schemas.quiz import (
    AddQuestionToQuiz,
    QuizAvailableResponse,
    QuizCreate,
    QuizQuestionResponse,
    QuizResponse,
    QuizUpdate,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


def _svc(db: AsyncSession = Depends(get_db)) -> QuizService:
    return QuizService(db)


def _handle(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ── Quiz CRUD ─────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a quiz",
)
async def create_quiz(
    body: QuizCreate,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> QuizResponse:
    quiz = await svc.create_quiz(
        creator_id=admin.id,
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
        start_time=body.start_time,
        end_time=body.end_time,
        shuffle_questions=body.shuffle_questions,
        shuffle_options=body.shuffle_options,
        max_attempts=body.max_attempts,
        proctoring_enabled=body.proctoring_enabled,
        max_tab_switches=body.max_tab_switches,
    )
    return QuizResponse.model_validate(quiz)


@router.get(
    "",
    response_model=list[QuizResponse],
    summary="List all quizzes",
)
async def list_quizzes(
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> list[QuizResponse]:
    quizzes = await svc.list_quizzes()
    return [QuizResponse.model_validate(q) for q in quizzes]


# ── Student browsing ──────────────────────────────────────────────────────────

@router.get(
    "/available",
    response_model=list[QuizAvailableResponse],
    summary="List quizzes available to the current student",
    description=(
        "Returns published quizzes whose time window currently contains `now` "
        "(start_time <= now <= end_time, with null bounds treated as unrestricted). "
        "Expired or not-yet-open quizzes are excluded. Admin-only fields "
        "(creator_id, is_published, shuffle settings, max_tab_switches, timestamps) "
        "are not exposed."
    ),
    responses={
        200: {
            "description": "Quizzes the student may currently start or resume",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "title": "Midterm Geography",
                            "description": "Covers chapters 1-5 of the textbook",
                            "duration_minutes": 60,
                            "start_time": "2026-06-10T09:00:00Z",
                            "end_time": "2026-06-10T11:00:00Z",
                            "max_attempts": 1,
                            "proctoring_enabled": True,
                        }
                    ]
                }
            },
        }
    },
)
async def list_available_quizzes(
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_student),
) -> list[QuizAvailableResponse]:
    quizzes = await svc.list_available_quizzes_for_student()
    return [QuizAvailableResponse.model_validate(q) for q in quizzes]


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
    summary="Get a quiz by ID",
)
async def get_quiz(
    quiz_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> QuizResponse:
    try:
        quiz = await svc.get_quiz(quiz_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return QuizResponse.model_validate(quiz)


@router.put(
    "/{quiz_id}",
    response_model=QuizResponse,
    summary="Update quiz metadata",
)
async def update_quiz(
    quiz_id: uuid.UUID,
    body: QuizUpdate,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> QuizResponse:
    updates = body.model_dump(exclude_unset=True)
    try:
        quiz = await svc.update_quiz(quiz_id, updates)
    except (LookupError, ValueError) as e:
        _handle(e)
    return QuizResponse.model_validate(quiz)


# ── Publish / Unpublish ───────────────────────────────────────────────────────

@router.post(
    "/{quiz_id}/publish",
    response_model=QuizResponse,
    summary="Publish a quiz (requires at least one question assigned)",
)
async def publish_quiz(
    quiz_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> QuizResponse:
    try:
        quiz = await svc.publish_quiz(quiz_id, admin.id)
    except (LookupError, ValueError) as e:
        _handle(e)
    return QuizResponse.model_validate(quiz)


@router.post(
    "/{quiz_id}/unpublish",
    response_model=QuizResponse,
    summary="Unpublish a quiz",
)
async def unpublish_quiz(
    quiz_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> QuizResponse:
    try:
        quiz = await svc.unpublish_quiz(quiz_id, admin.id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return QuizResponse.model_validate(quiz)


# ── Quiz Questions ────────────────────────────────────────────────────────────

@router.post(
    "/{quiz_id}/questions",
    response_model=QuizQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a question to a quiz",
)
async def add_question_to_quiz(
    quiz_id: uuid.UUID,
    body: AddQuestionToQuiz,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> QuizQuestionResponse:
    try:
        qq = await svc.add_question_to_quiz(
            quiz_id=quiz_id,
            question_id=body.question_id,
            position=body.position,
            marks_override=body.marks_override,
            requester_id=admin.id,
        )
    except (LookupError, ValueError) as e:
        _handle(e)
    return QuizQuestionResponse.model_validate(qq)


@router.delete(
    "/{quiz_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a question from a quiz",
)
async def remove_question_from_quiz(
    quiz_id: uuid.UUID,
    question_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    admin: User = Depends(require_admin),
) -> None:
    try:
        await svc.remove_question_from_quiz(quiz_id, question_id, admin.id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{quiz_id}/questions",
    response_model=list[QuizQuestionResponse],
    summary="List questions assigned to a quiz (ordered by position)",
)
async def list_quiz_questions(
    quiz_id: uuid.UUID,
    svc: QuizService = Depends(_svc),
    _: User = Depends(require_admin),
) -> list[QuizQuestionResponse]:
    try:
        rows = await svc.list_quiz_questions(quiz_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [QuizQuestionResponse.model_validate(r) for r in rows]
