"""
Tests for AuthService — register and login flows.
Uses AsyncMock to avoid a real database connection.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import AuthService


def _make_mock_user(
    role: UserRole = UserRole.STUDENT,
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "jane@example.com"
    user.full_name = "Jane Doe"
    user.role = role          # actual UserRole enum; .value works naturally
    user.is_active = is_active
    user.hashed_password = None  # set per-test when needed
    return user


def _make_service(session: AsyncMock) -> AuthService:
    return AuthService(session)


class TestRegister:
    async def test_register_duplicate_email_raises(self):
        session = AsyncMock()
        svc = _make_service(session)
        svc.user_repo.email_exists = AsyncMock(return_value=True)

        with pytest.raises(ValueError, match="Email already registered"):
            await svc.register(
                name="Admin User",
                email="admin@test.com",
                password="StrongPass123!",
                role=UserRole.ADMIN,
            )

    async def test_register_success_returns_token_response(self):
        session = AsyncMock()
        svc = _make_service(session)

        mock_user = _make_mock_user(role=UserRole.STUDENT)
        svc.user_repo.email_exists = AsyncMock(return_value=False)
        svc.user_repo.username_exists = AsyncMock(return_value=False)
        svc.user_repo.create = AsyncMock(return_value=mock_user)
        svc.token_repo.create = AsyncMock(return_value=MagicMock())

        result = await svc.register(
            name="Jane Doe",
            email="jane@example.com",
            password="StrongPass123!",
            role=UserRole.STUDENT,
        )

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        assert result.user.email == mock_user.email

    async def test_register_username_collision_uses_suffix(self):
        session = AsyncMock()
        svc = _make_service(session)

        mock_user = _make_mock_user()
        svc.user_repo.email_exists = AsyncMock(return_value=False)
        # first two username checks collide, third is free
        svc.user_repo.username_exists = AsyncMock(side_effect=[True, True, False])
        svc.user_repo.create = AsyncMock(return_value=mock_user)
        svc.token_repo.create = AsyncMock(return_value=MagicMock())

        await svc.register(
            name="Jane Doe",
            email="jane@example.com",
            password="StrongPass123!",
            role=UserRole.STUDENT,
        )

        # Should have tried username 3 times (base, base+1, base+2)
        assert svc.user_repo.username_exists.call_count == 3


class TestLogin:
    async def test_login_valid_credentials_returns_token_response(self):
        from app.utils.password import hash_password

        session = AsyncMock()
        svc = _make_service(session)

        password = "StrongPass123!"
        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password(password)

        svc.user_repo.get_by_email = AsyncMock(return_value=mock_user)
        svc.token_repo.create = AsyncMock(return_value=MagicMock())

        result = await svc.login(email="jane@example.com", password=password)

        assert result.access_token
        assert result.refresh_token

    async def test_login_wrong_password_raises(self):
        from app.utils.password import hash_password

        session = AsyncMock()
        svc = _make_service(session)

        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password("StrongPass123!")

        svc.user_repo.get_by_email = AsyncMock(return_value=mock_user)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await svc.login(email="jane@example.com", password="WrongPass123!")

    async def test_login_unknown_email_raises(self):
        session = AsyncMock()
        svc = _make_service(session)
        svc.user_repo.get_by_email = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await svc.login(email="nobody@example.com", password="StrongPass123!")

    async def test_login_inactive_user_raises(self):
        from app.utils.password import hash_password

        session = AsyncMock()
        svc = _make_service(session)

        password = "StrongPass123!"
        mock_user = _make_mock_user(is_active=False)
        mock_user.hashed_password = hash_password(password)

        svc.user_repo.get_by_email = AsyncMock(return_value=mock_user)

        with pytest.raises(ValueError, match="Account is disabled"):
            await svc.login(email="jane@example.com", password=password)
