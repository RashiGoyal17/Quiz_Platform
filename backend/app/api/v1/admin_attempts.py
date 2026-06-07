import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_with_org
from app.database import get_db
from app.models.enums import AttemptStatus
from app.models.user import User
from app.schemas.attempt import AttemptAdminResponse, AttemptAuditResponse
from app.services.attempt_service import AttemptService

router = APIRouter(prefix="/admin/attempts", tags=["admin-attempts"])


def _svc(db: AsyncSession = Depends(get_db)) -> AttemptService:
    return AttemptService(db)


@router.get(
    "",
    response_model=list[AttemptAdminResponse],
    summary="List attempts (admin)",
    description=(
        "Paginated list of all attempts. Filterable by quiz, student, and status. "
        "Admin only."
    ),
)
async def list_attempts(
    quiz_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    attempt_status: AttemptStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    svc: AttemptService = Depends(_svc),
    admin: User = Depends(require_admin_with_org),
) -> list[AttemptAdminResponse]:
    attempts = await svc.list_attempts_admin(
        organization_id=admin.organization_id,
        quiz_id=quiz_id,
        student_id=student_id,
        status=attempt_status,
        limit=limit,
        offset=offset,
    )
    return [AttemptAdminResponse.model_validate(a) for a in attempts]


@router.get(
    "/{attempt_id}/audit",
    response_model=AttemptAuditResponse,
    summary="Get attempt audit trail (admin)",
    description=(
        "Returns full attempt metadata and a chronological tab switch log. "
        "Admin only."
    ),
)
async def get_attempt_audit(
    attempt_id: uuid.UUID,
    svc: AttemptService = Depends(_svc),
    admin: User = Depends(require_admin_with_org),
) -> AttemptAuditResponse:
    try:
        return await svc.get_attempt_audit(attempt_id, admin.organization_id)
    except LookupError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
