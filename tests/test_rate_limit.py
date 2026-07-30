"""
Rate limit testleri.
"""

import pytest
from fastapi import HTTPException

from backend import rate_limit


def test_within_limit_passes(monkeypatch):
    monkeypatch.setattr(rate_limit, "LIMIT_PER_MIN", 3)
    monkeypatch.setattr(rate_limit, "LIMIT_PER_DAY", 0)
    rate_limit.reset()

    for _ in range(3):
        rate_limit.check_rate_limit("user-a")


def test_minute_limit_returns_429(monkeypatch):
    monkeypatch.setattr(rate_limit, "LIMIT_PER_MIN", 2)
    monkeypatch.setattr(rate_limit, "LIMIT_PER_DAY", 0)
    rate_limit.reset()

    rate_limit.check_rate_limit("user-b")
    rate_limit.check_rate_limit("user-b")

    with pytest.raises(HTTPException) as exc:
        rate_limit.check_rate_limit("user-b")

    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_daily_limit_returns_429(monkeypatch):
    monkeypatch.setattr(rate_limit, "LIMIT_PER_MIN", 0)
    monkeypatch.setattr(rate_limit, "LIMIT_PER_DAY", 2)
    rate_limit.reset()

    rate_limit.check_rate_limit("user-c")
    rate_limit.check_rate_limit("user-c")

    with pytest.raises(HTTPException) as exc:
        rate_limit.check_rate_limit("user-c")

    assert exc.value.status_code == 429


def test_limits_are_per_user(monkeypatch):
    monkeypatch.setattr(rate_limit, "LIMIT_PER_MIN", 1)
    monkeypatch.setattr(rate_limit, "LIMIT_PER_DAY", 0)
    rate_limit.reset()

    rate_limit.check_rate_limit("user-d")
    # Farklı kullanıcı etkilenmemeli
    rate_limit.check_rate_limit("user-e")

    with pytest.raises(HTTPException):
        rate_limit.check_rate_limit("user-d")


def test_disabled_when_zero(monkeypatch):
    monkeypatch.setattr(rate_limit, "LIMIT_PER_MIN", 0)
    monkeypatch.setattr(rate_limit, "LIMIT_PER_DAY", 0)
    rate_limit.reset()

    for _ in range(50):
        rate_limit.check_rate_limit("user-f")
