"""
Firebase Auth middleware for FastAPI.

Verifies Firebase ID tokens from the Authorization header.
Dev mode: ENVIRONMENT != "production" ve FIREBASE_PRIVATE_KEY boşsa mock user döner.
Production mode: FIREBASE_PRIVATE_KEY zorunlu, yoksa başlatmada hata verir.
"""

import logging
import os

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_security = HTTPBearer()

_firebase_initialized = False
_is_dev_mode = False


def _ensure_firebase():
    global _firebase_initialized, _is_dev_mode
    if _firebase_initialized:
        return

    environment = os.getenv("ENVIRONMENT", "development").lower()
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")

    if not private_key:
        if environment == "production":
            raise RuntimeError(
                "FIREBASE_PRIVATE_KEY is required in production. "
                "Set ENVIRONMENT=development for dev mode bypass."
            )
        # Dev mode: skip Firebase init, auth will use a mock
        logger.warning("Firebase Auth: dev mode — tüm token'lar kabul ediliyor.")
        _is_dev_mode = True
        _firebase_initialized = True
        return

    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    firebase_admin.initialize_app(cred)
    _is_dev_mode = False
    _firebase_initialized = True
    logger.info("Firebase Auth: production mode — token doğrulama aktif.")


def verify_firebase_token(token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    _ensure_firebase()

    if _is_dev_mode:
        return {"uid": "dev-user", "email": "dev@localhost"}

    try:
        return firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_security),
) -> dict:
    """FastAPI dependency that extracts and verifies the Firebase token."""
    return verify_firebase_token(creds.credentials)
