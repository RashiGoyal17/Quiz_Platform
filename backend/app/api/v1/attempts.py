import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_student
from app.database import get_db
from app.models.user import User
from app.schemas.attempt import (
    AnswerResponse,
    AttemptResponse,
    AttemptResultResponse,
    ProctoringEventRequest,
    ProctoringEventResponse,
    SaveAnswerRequest,
    StartAttemptRequest,
    TabSwitchResponse,
)
from app.services.attempt_service import AttemptService

router = APIRouter(prefix="/attempts", tags=["attempts"])


def _svc(db: AsyncSession = Depends(get_db)) -> AttemptService:
    return AttemptService(db)


def _handle(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/start",
    response_model=AttemptResponse,
    status_code=status.HTTP_200_OK,
    summary="Start or resume a quiz attempt",
    description=(
        "Creates a new attempt for the authenticated student. "
        "If an IN_PROGRESS attempt already exists for this quiz, it is returned instead "
        "(resume). Validates published status, time window, and attempt limit."
    ),
)
async def start_attempt(
    body: StartAttemptRequest,
    request: Request,
    svc: AttemptService = Depends(_svc),
    student: User = Depends(require_student),
) -> AttemptResponse:
    ip = request.client.host if request.client else None
    try:
        return await svc.start_attempt(
            student_id=student.id,
            quiz_id=body.quiz_id,
            ip_address=ip,
        )
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.post(
    "/{attempt_id}/answers",
    response_model=AnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Save or update an answer",
    description=(
        "Upserts the student's answer for one question in an IN_PROGRESS attempt. "
        "Safe to call on every autosave tick. "
        "Pass selected_option_id=null to clear a previously saved answer."
    ),
)
async def save_answer(
    attempt_id: uuid.UUID,
    body: SaveAnswerRequest,
    svc: AttemptService = Depends(_svc),
    student: User = Depends(require_student),
) -> AnswerResponse:
    try:
        return await svc.save_answer(
            attempt_id=attempt_id,
            attempt_question_id=body.attempt_question_id,
            selected_option_id=body.selected_option_id,
            student_id=student.id,
        )
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.post(
    "/{attempt_id}/submit",
    response_model=AttemptResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a quiz attempt",
    description=(
        "Locks the attempt, grades all answers, and returns the full result. "
        "The attempt must be IN_PROGRESS and belong to the authenticated student."
    ),
)
async def submit_attempt(
    attempt_id: uuid.UUID,
    svc: AttemptService = Depends(_svc),
    student: User = Depends(require_student),
) -> AttemptResultResponse:
    try:
        return await svc.submit_attempt(
            attempt_id=attempt_id,
            student_id=student.id,
        )
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.get(
    "/{attempt_id}/result",
    response_model=AttemptResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get attempt result",
    description=(
        "Returns the graded result for a SUBMITTED, TIMED_OUT, or ABANDONED attempt. "
        "Students can only access their own attempts."
    ),
)
async def get_attempt_result(
    attempt_id: uuid.UUID,
    svc: AttemptService = Depends(_svc),
    student: User = Depends(require_student),
) -> AttemptResultResponse:
    try:
        return await svc.get_attempt_result(
            attempt_id=attempt_id,
            requester_id=student.id,
        )
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.post(
    "/{attempt_id}/tab-switch",
    response_model=TabSwitchResponse,
    status_code=status.HTTP_200_OK,
    summary="Log a tab switch event",
    description=(
        "Records a tab switch for an IN_PROGRESS attempt and increments the counter. "
        "If max_tab_switches is set and the count exceeds it, the attempt is marked "
        "ABANDONED. Also enforces timeout — raises 400 if the timer has expired."
    ),
)
async def log_tab_switch(
    attempt_id: uuid.UUID,
    svc: AttemptService = Depends(_svc),
    student: User = Depends(require_student),
) -> TabSwitchResponse:
    try:
        return await svc.log_tab_switch(
            attempt_id=attempt_id,
            student_id=student.id,
        )
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.post(
    "/{attempt_id}/proctoring-event",
    response_model=ProctoringEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a proctoring event",
    description=(
        "Records a browser-observable proctoring event for an IN_PROGRESS attempt. "
        "**Accepted types:** `window_blur`, `copy_paste`, `fullscreen_exit`. "
        "**Rejected types:** `tab_switch` (use /tab-switch instead), and all AI-detection "
        "types (`face_not_detected`, `multiple_faces`, `phone_detected`, `audio_detected`). "
        "Enforces attempt ownership, IN_PROGRESS status, and timeout. "
        "Events are immutable — each call creates a new row in the audit log."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "window_blur": {
                            "summary": "Window lost focus",
                            "value": {"event_type": "window_blur", "metadata": {"duration_ms": 1400}},
                        },
                        "copy_paste": {
                            "summary": "Copy-paste detected",
                            "value": {"event_type": "copy_paste", "metadata": {"element_type": "input", "content_length": 42}},
                        },
                        "fullscreen_exit": {
                            "summary": "Fullscreen exited",
                            "value": {"event_type": "fullscreen_exit", "metadata": None},
                        },
                    }
                }
            }
        }
    },
)
async def log_proctoring_event(
    attempt_id: uuid.UUID,
    body: ProctoringEventRequest,
    svc: AttemptService = Depends(_svc),
    student: User = Depends(require_student),
) -> ProctoringEventResponse:
    try:
        return await svc.log_proctoring_event(
            attempt_id=attempt_id,
            student_id=student.id,
            event_type=body.event_type,
            metadata=body.metadata,
        )
    except (LookupError, ValueError) as exc:
        _handle(exc)
