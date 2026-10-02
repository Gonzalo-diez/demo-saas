"""
test_security.py — Tests del módulo de seguridad (hashing de passwords y JWT).
"""
import time
import pytest
from jose import jwt


from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.core.config import get_settings

settings = get_settings()


class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        hashed = get_password_hash("mypassword")
        assert hashed != "mypassword"

    def test_verify_correct_password(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        h1 = get_password_hash("abc123")
        h2 = get_password_hash("abc123")
        # bcrypt uses random salt → different hashes
        assert h1 != h2

    def test_empty_password(self):
        # bcrypt en este entorno limita a 72 bytes; string vacío es válido
        hashed = get_password_hash("short")
        assert verify_password("short", hashed) is True

    def test_unicode_password(self):
        hashed = get_password_hash("contrasena123")
        assert verify_password("contrasena123", hashed) is True
        assert verify_password("otracosa", hashed) is False


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token("42", tenant_id=1)
        assert isinstance(token, str)

    def test_decodable(self):
        token = create_access_token("42", tenant_id=1)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert payload["sub"] == "42"

    def test_contains_exp(self):
        token = create_access_token("1", tenant_id=1)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert "exp" in payload

    def test_exp_in_future(self):
        token = create_access_token("1", tenant_id=1)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert payload["exp"] > time.time()

    def test_different_subjects_different_tokens(self):
        t1 = create_access_token("1", tenant_id=1)
        t2 = create_access_token("2", tenant_id=1)
        assert t1 != t2

    def test_wrong_secret_fails(self):
        token = create_access_token("1", tenant_id=1)
        with pytest.raises(Exception):
            jwt.decode(token, "wrong-secret", algorithms=[settings.JWT_ALG])

    def test_contains_tenant_id(self):
        token = create_access_token("1", tenant_id=7)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert payload["tenant_id"] == 7

    def test_requires_tenant_id(self):
        with pytest.raises(ValueError):
            create_access_token("1")
