"""
Shared test fixtures.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Dev mode: Firebase auth bypass
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("FIREBASE_PRIVATE_KEY", "")

from backend.main import app


@pytest.fixture
def client():
    """FastAPI test client with auth bypass header."""
    c = TestClient(app)
    c.headers["Authorization"] = "Bearer dev-token"
    return c
