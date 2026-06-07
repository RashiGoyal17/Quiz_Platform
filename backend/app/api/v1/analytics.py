import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_student
from app.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AdminDashboardResponse,
    QuizAnalyticsResponse,
    QuizQuestionAnalyticsResponse,
    StudentAnalyticsResponse,
    StudentHistoryResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _svc(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


def _handle(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ── Student endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=StudentAnalyticsResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get personal analytics",
    description=(
        "Returns aggregate statistics for the authenticated student: "
        "total attempts, score averages, and status breakdown. "
        "average_percentage and best_percentage are null at the summary level "
        "because each quiz has a different total possible score."
    ),
)
async def get_student_analytics(
    svc: AnalyticsService = Depends(_svc),
    student: User = Depends(require_student),
) -> StudentAnalyticsResponse:
    return await svc.get_student_analytics(student.id)


@router.get(
    "/me/history",
    response_model=StudentHistoryResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get attempt history",
    description=(
        "Paginated list of all attempts for the authenticated student, "
        "ordered by most recent first. Optionally filter by quiz_id."
    ),
)
async def get_student_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    quiz_id: uuid.UUID | None = Query(default=None),
    svc: AnalyticsService = Depends(_svc),
    student: User = Depends(require_student),
) -> StudentHistoryResponse:
    return await svc.get_student_history(
        student_id=student.id,
        limit=limit,
        offset=offset,
        quiz_id=quiz_id,
    )


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizAnalyticsResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get quiz analytics (admin)",
    description=(
        "Returns aggregate attempt statistics for a single quiz: "
        "status breakdown, completion/abandonment/timeout rates, "
        "average score, and anti-cheat metrics. Admin only."
    ),
)
async def get_quiz_analytics(
    quiz_id: uuid.UUID,
    svc: AnalyticsService = Depends(_svc),
    _: User = Depends(require_admin),
) -> QuizAnalyticsResponse:
    try:
        return await svc.get_quiz_analytics(quiz_id)
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.get(
    "/quizzes/{quiz_id}/questions",
    response_model=QuizQuestionAnalyticsResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get per-question analytics for a quiz (admin)",
    description=(
        "Returns correct/incorrect/unanswered percentages and difficulty ranking "
        "for each question in the quiz, computed over SUBMITTED and TIMED_OUT attempts only. "
        "Questions with fewer than min_attempts_for_ranking finalized attempts are flagged "
        "with insufficient_data=true and difficulty_rank=null. Admin only."
    ),
)
async def get_quiz_question_analytics(
    quiz_id: uuid.UUID,
    svc: AnalyticsService = Depends(_svc),
    _: User = Depends(require_admin),
) -> QuizQuestionAnalyticsResponse:
    try:
        return await svc.get_quiz_question_analytics(quiz_id)
    except (LookupError, ValueError) as exc:
        _handle(exc)


@router.get(
    "/admin/dashboard",
    response_model=AdminDashboardResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get admin dashboard metrics",
    description=(
        "Platform-wide snapshot: user counts, quiz counts, attempt status breakdown, "
        "anti-cheat totals, and the 10 most recent attempts with student and quiz names. "
        "Admin only."
    ),
)
async def get_admin_dashboard(
    svc: AnalyticsService = Depends(_svc),
    _: User = Depends(require_admin),
) -> AdminDashboardResponse:
    return await svc.get_admin_dashboard()
