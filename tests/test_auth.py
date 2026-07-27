"""
Auth middleware testleri.
"""

import os
import pytest
from backend.auth import verify_firebase_token


def test_dev_mode_returns_mock_user():
    """Dev mode'da herhangi bir token kabul edilmeli."""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["FIREBASE_PRIVATE_KEY"] = ""

    # Reset state for fresh test
    import backend.auth
    backend.auth._firebase_initialized = False
    backend.auth._is_dev_mode = False

    result = verify_firebase_token("any-token")
    assert result["uid"] == "dev-user"
    assert result["email"] == "dev@localhost"


def test_production_mode_requires_key():
    """Production'da FIREBASE_PRIVATE_KEY yoksa RuntimeError fırlatmalı."""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["FIREBASE_PRIVATE_KEY"] = ""

    import backend.auth
    backend.auth._firebase_initialized = False
    backend.auth._is_dev_mode = False

    with pytest.raises(RuntimeError, match="FIREBASE_PRIVATE_KEY is required"):
        verify_firebase_token("any-token")

    # Reset for other tests
    os.environ["ENVIRONMENT"] = "development"
    backend.auth._firebase_initialized = False
    backend.auth._is_dev_mode = False
