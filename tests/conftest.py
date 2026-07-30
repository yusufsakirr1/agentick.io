"""
Shared test fixtures.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Dev mode: Firebase auth bypass
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("FIREBASE_PRIVATE_KEY", "")

# Rate limit testleri kendi limitlerini kurar; diğer testler etkilenmesin
os.environ.setdefault("RATE_LIMIT_PER_MIN", "0")
os.environ.setdefault("RATE_LIMIT_PER_DAY", "0")

from backend.main import app  # noqa: E402
from backend import rate_limit  # noqa: E402


@pytest.fixture
def client():
    """FastAPI test client with auth bypass header."""
    c = TestClient(app)
    c.headers["Authorization"] = "Bearer dev-token"
    return c


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Her testten sonra auth ve rate limit durumunu sıfırla."""
    yield
    import backend.auth
    backend.auth._firebase_initialized = False
    backend.auth._is_dev_mode = False
    rate_limit.reset()
