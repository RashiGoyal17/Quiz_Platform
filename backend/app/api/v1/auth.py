from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin, require_student
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "<jwt>",
                        "refresh_token": "<jwt>",
                        "token_type": "bearer",
                        "user": {
                            "id": "uuid",
                            "email": "jane@example.com",
                            "name": "Jane Doe",
                            "role": "student",
                        },
                    }
                }
            },
        },
        409: {"description": "Email already registered"},
        422: {"description": "Validation error (weak password, bad email, etc.)"},
    },
)
async def register(
    body: RegisterRequest,
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    try:
        return await svc.register(
            name=body.name,
            email=body.email,
            password=body.password,
            role=body.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    body: LoginRequest,
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    try:
        return await svc.login(email=body.email, password=body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new token pair",
    responses={
        200: {"description": "New token pair issued"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh(
    body: RefreshRequest,
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    try:
        return await svc.refresh_tokens(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token (logout)",
    responses={
        204: {"description": "Logged out successfully"},
        401: {"description": "Invalid refresh token"},
    },
)
async def logout(
    body: LogoutRequest,
    svc: AuthService = Depends(_get_auth_service),
) -> None:
    try:
        await svc.logout(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


# ── Verification routes ────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserInfo,
    summary="Get current authenticated user",
)
async def me(current_user: User = Depends(get_current_user)) -> UserInfo:
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name,
        role=current_user.role.value,
    )


@router.get(
    "/admin-test",
    summary="ADMIN-only test endpoint",
    responses={403: {"description": "Forbidden — not an admin"}},
)
async def admin_test(current_user: User = Depends(require_admin)) -> dict:
    return {"message": "Admin access confirmed", "user": current_user.email}


@router.get(
    "/student-test",
    summary="STUDENT-only test endpoint",
    responses={403: {"description": "Forbidden — not a student"}},
)
async def student_test(current_user: User = Depends(require_student)) -> dict:
    return {"message": "Student access confirmed", "user": current_user.email}
