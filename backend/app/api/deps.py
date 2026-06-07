from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.jwt import decode_token

__all__ = [
    "get_db",
    "get_current_user",
    "require_admin",
    "require_student",
    "require_admin_with_org",
]

_bearer = HTTPBearer()

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    if payload.get("type") != "access":
        raise _CREDENTIALS_EXCEPTION

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise _CREDENTIALS_EXCEPTION

    user = await UserRepository(db).get_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


async def require_admin_with_org(current_user: User = Depends(require_admin)) -> User:
    """
    Admin dependency that additionally guarantees `organization_id` is set.

    Per Phase 9B "Tenant Boundary Rules" #8, every admin must belong to an
    organization (enforced at creation, not via a DB constraint — students
    remain the deliberate global exception). Any admin route that scopes
    data by organization should depend on this rather than `require_admin`.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is not assigned to an organization",
        )
    return current_user
