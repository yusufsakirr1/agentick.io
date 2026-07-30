"""
Firebase Auth middleware for FastAPI.

Verifies Firebase ID tokens from the Authorization header.

Güvenlik modeli (fail-safe):
  - ENVIRONMENT tanımlı değilse "production" varsayılır — yani kimlik doğrulama
    bypass'ı ASLA kazara açılmaz. Dev bypass için ENVIRONMENT açıkça
    development/dev/local/test olmalıdır.
  - Production'da FIREBASE_PRIVATE_KEY zorunludur; yoksa uygulama başlarken
    (init_auth) RuntimeError ile durur — istek anında 500 vermez.
"""

import logging
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

logger = logging.getLogger(__name__)

_security = HTTPBearer()

# Dev bypass'ın açılabileceği ortam adları — bunun dışındaki her değer
# (ve tanımsızlık) production gibi davranır.
DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}

_firebase_initialized = False
_is_dev_mode = False


def _ensure_firebase():
    global _firebase_initialized, _is_dev_mode
    if _firebase_initialized:
        return

    environment = os.getenv("ENVIRONMENT", "production").strip().lower()
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").strip()
    is_dev_env = environment in DEV_ENVIRONMENTS

    if not private_key:
        if not is_dev_env:
            raise RuntimeError(
                "FIREBASE_PRIVATE_KEY is required in production. "
                "Set ENVIRONMENT=development for dev mode bypass."
            )
        # Dev mode: skip Firebase init, auth will use a mock
        logger.warning(
            "Firebase Auth: DEV MODE (ENVIRONMENT=%s) — tüm token'lar kabul ediliyor. "
            "Bu ayarla production'a deploy ETMEYİN.",
            environment,
        )
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
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    _is_dev_mode = False
    _firebase_initialized = True
    logger.info("Firebase Auth: production mode — token doğrulama aktif.")


def init_auth() -> None:
    """
    Uygulama başlarken çağrılır. Yanlış yapılandırma varsa burada patlar,
    her istekte 500 dönmek yerine servis hiç ayağa kalkmaz.
    """
    _ensure_firebase()


def is_dev_mode() -> bool:
    _ensure_firebase()
    return _is_dev_mode


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
