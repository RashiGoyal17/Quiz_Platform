"""
Tests for app.utils.password — bcrypt hash and verify.
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.utils.password import hash_password, verify_password


class TestHashPassword:
    def test_valid_password_produces_bcrypt_hash(self):
        hashed = hash_password("StrongPass123!")
        # bcrypt hashes always start with $2b$
        assert hashed.startswith("$2b$")

    def test_hash_is_never_plain_text(self):
        password = "StrongPass123!"
        assert hash_password(password) != password

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses a random salt on every call
        pw = "StrongPass123!"
        assert hash_password(pw) != hash_password(pw)


class TestVerifyPassword:
    def test_correct_password_verifies(self):
        password = "StrongPass123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_incorrect_password_rejected(self):
        hashed = hash_password("StrongPass123!")
        assert verify_password("WrongPass123!", hashed) is False

    def test_empty_string_rejected(self):
        hashed = hash_password("StrongPass123!")
        assert verify_password("", hashed) is False

    def test_case_sensitive(self):
        hashed = hash_password("StrongPass123!")
        assert verify_password("strongpass123!", hashed) is False


class TestPasswordSchemaValidation:
    """Test that the Pydantic schema enforces password rules before the service is called."""

    def _valid_payload(self, **overrides):
        return {
            "name": "Admin User",
            "email": "admin@test.com",
            "password": "StrongPass123!",
            "role": "admin",
            **overrides,
        }

    def test_valid_password_accepted(self):
        req = RegisterRequest(**self._valid_payload())
        assert req.password == "StrongPass123!"

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**self._valid_payload(password="Sh0rt!"))
        errors = exc_info.value.errors()
        assert any("password" in str(e["loc"]) for e in errors)

    def test_password_missing_uppercase_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**self._valid_payload(password="weakpass123!"))
        assert any("uppercase" in str(exc_info.value))

    def test_password_missing_digit_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**self._valid_payload(password="StrongPass!!"))
        assert any("digit" in str(exc_info.value))

    def test_password_missing_special_char_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**self._valid_payload(password="StrongPass123"))
        assert any("special" in str(exc_info.value))
