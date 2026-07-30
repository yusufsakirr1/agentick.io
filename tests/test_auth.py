"""
Auth middleware testleri.
"""

import pytest

import backend.auth
from backend.auth import verify_firebase_token


def _reset_auth_state():
    backend.auth._firebase_initialized = False
    backend.auth._is_dev_mode = False


def test_dev_mode_returns_mock_user(monkeypatch):
    """Dev mode'da herhangi bir token kabul edilmeli."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "")
    _reset_auth_state()

    result = verify_firebase_token("any-token")
    assert result["uid"] == "dev-user"
    assert result["email"] == "dev@localhost"


def test_production_mode_requires_key(monkeypatch):
    """Production'da FIREBASE_PRIVATE_KEY yoksa RuntimeError fırlatmalı."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "")
    _reset_auth_state()

    with pytest.raises(RuntimeError, match="FIREBASE_PRIVATE_KEY is required"):
        verify_firebase_token("any-token")


def test_missing_environment_defaults_to_production(monkeypatch):
    """
    Fail-safe: ENVIRONMENT tanımlı değilse dev bypass AÇILMAMALI.
    Aksi halde deploy'da tek bir eksik env var API'yi tamamen açar.
    """
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "")
    _reset_auth_state()

    with pytest.raises(RuntimeError, match="FIREBASE_PRIVATE_KEY is required"):
        verify_firebase_token("any-token")


@pytest.mark.parametrize("env", ["staging", "prod", "canary", "PRODUCTION"])
def test_unknown_environment_is_treated_as_production(monkeypatch, env):
    """Bilinmeyen ortam adları dev bypass'ı açmamalı."""
    monkeypatch.setenv("ENVIRONMENT", env)
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "")
    _reset_auth_state()

    with pytest.raises(RuntimeError, match="FIREBASE_PRIVATE_KEY is required"):
        verify_firebase_token("any-token")


@pytest.mark.parametrize("env", ["development", "dev", "local", "test", "DEVELOPMENT"])
def test_known_dev_environments_bypass(monkeypatch, env):
    monkeypatch.setenv("ENVIRONMENT", env)
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "")
    _reset_auth_state()

    assert verify_firebase_token("any-token")["uid"] == "dev-user"
