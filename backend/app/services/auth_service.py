import hashlib
from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.enums import UserRole
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserInfo
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.password import hash_password, verify_password


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _build_token_response(user: User, access_token: str, refresh_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserInfo(
            id=user.id,
            email=user.email,
            name=user.full_name,
            role=user.role.value,
        ),
    )


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)

    async def register(
        self, name: str, email: str, password: str, role: UserRole
    ) -> TokenResponse:
        # Phase 9B: admin accounts must belong to an organization (Tenant
        # Boundary Rule #8), and organization/admin provisioning remains an
        # internal operational process until a future Organization
        # Invitations / Platform Admin phase exists. Public self-service
        # registration is therefore student-only.
        if role != UserRole.STUDENT:
            raise ValueError("Self-service registration is only available for students")

        if await self.user_repo.email_exists(email):
            raise ValueError("Email already registered")

        username = await self._unique_username(email)

        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            full_name=name,
            role=role,
        )
        user = await self.user_repo.create(user)

        return await self._issue_token_pair(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is disabled")

        return await self._issue_token_pair(user)

    async def refresh_tokens(self, raw_refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(raw_refresh_token)
        except JWTError:
            raise ValueError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        token_hash = _hash_token(raw_refresh_token)
        stored = await self.token_repo.get_by_token_hash(token_hash)

        if stored is None or stored.revoked:
            raise ValueError("Refresh token not found or already revoked")

        if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired")

        await self.token_repo.revoke(stored)

        user = await self.user_repo.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise ValueError("User not found or disabled")

        return await self._issue_token_pair(user)

    async def logout(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_token(raw_refresh_token)
        except JWTError:
            raise ValueError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        token_hash = _hash_token(raw_refresh_token)
        stored = await self.token_repo.get_by_token_hash(token_hash)

        if stored is None or stored.revoked:
            raise ValueError("Refresh token not found or already revoked")

        await self.token_repo.revoke(stored)

    async def change_password(
        self, user_id, current_password: str, new_password: str
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        await self.session.flush()

    # ── internals ──────────────────────────────────────────────────────────

    async def _issue_token_pair(self, user: User) -> TokenResponse:
        access_token = create_access_token(user.id, user.role.value, user.organization_id)
        raw_refresh = create_refresh_token(user.id)

        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.token_repo.create(refresh_token_obj)

        return _build_token_response(user, access_token, raw_refresh)

    async def _unique_username(self, email: str) -> str:
        base = email.split("@")[0].lower()
        base = "".join(c if c.isalnum() or c == "_" else "_" for c in base)
        username = base
        suffix = 1
        while await self.user_repo.username_exists(username):
            username = f"{base}{suffix}"
            suffix += 1
        return username
