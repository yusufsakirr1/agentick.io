"""
Firebase Auth middleware for FastAPI.

Verifies Firebase ID tokens from the Authorization header.
"""

import os

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_security = HTTPBearer()

_firebase_initialized = False


def _ensure_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return

    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
    if not private_key:
        # Dev mode: skip Firebase init, auth will use a mock
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
    _firebase_initialized = True


def verify_firebase_token(token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    _ensure_firebase()

    # Dev mode: Firebase not configured — accept any token
    if not firebase_admin._apps:
        return {"uid": "dev-user", "email": "dev@localhost"}

    try:
        return firebase_auth.verify_id_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_security),
) -> dict:
    """FastAPI dependency that extracts and verifies the Firebase token."""
    return verify_firebase_token(creds.credentials)
