"""
Kullanıcı başına basit kayan pencere (sliding window) rate limiting.

Her /api/ask çağrısı 4+ LLM isteği tetikliyor; kotasız bırakılırsa tek bir
kullanıcı maliyeti patlatabilir. Bu modül dakika ve gün bazlı iki pencere uygular.

SINIR: Sayaçlar süreç içinde (in-process) tutulur. Tek instance için yeterlidir;
birden fazla worker/instance ile deploy edilirse her sürecin kendi sayacı olur.
Dağıtık kota için Redis veya Firestore tabanlı bir sayaç gerekir (Faz 7).
"""

import logging
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status

from backend.auth import get_current_user

logger = logging.getLogger(__name__)

MINUTE = 60
DAY = 24 * 60 * 60

# 0 veya negatif değer ilgili limiti kapatır.
LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))
LIMIT_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", "200"))

# Bu süre boyunca hiç istek göndermeyen kullanıcıların kaydı temizlenir.
_IDLE_EVICTION_SECONDS = DAY

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()
_last_sweep = 0.0


def _sweep(now: float) -> None:
    """Uzun süredir sessiz kullanıcıları sözlükten düşür (bellek sızıntısı önleme)."""
    global _last_sweep
    if now - _last_sweep < MINUTE:
        return
    _last_sweep = now
    stale = [uid for uid, hits in _hits.items() if not hits or now - hits[-1] > _IDLE_EVICTION_SECONDS]
    for uid in stale:
        _hits.pop(uid, None)


def check_rate_limit(uid: str) -> None:
    """Kullanıcı için bir istek kaydeder. Limit aşıldıysa HTTP 429 fırlatır."""
    if LIMIT_PER_MIN <= 0 and LIMIT_PER_DAY <= 0:
        return

    now = time.monotonic()
    window = max(MINUTE if LIMIT_PER_MIN > 0 else 0, DAY if LIMIT_PER_DAY > 0 else 0)

    with _lock:
        _sweep(now)
        hits = _hits[uid]

        # Pencere dışında kalan kayıtları at
        while hits and now - hits[0] > window:
            hits.popleft()

        if LIMIT_PER_DAY > 0 and len(hits) >= LIMIT_PER_DAY:
            retry_after = int(DAY - (now - hits[0])) + 1
            logger.warning("Rate limit (gün) aşıldı: uid=%s", uid)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Günlük sorgu limitiniz doldu ({LIMIT_PER_DAY}). Yarın tekrar deneyin.",
                headers={"Retry-After": str(retry_after)},
            )

        if LIMIT_PER_MIN > 0:
            recent = sum(1 for t in hits if now - t <= MINUTE)
            if recent >= LIMIT_PER_MIN:
                oldest_recent = next(t for t in hits if now - t <= MINUTE)
                retry_after = int(MINUTE - (now - oldest_recent)) + 1
                logger.warning("Rate limit (dakika) aşıldı: uid=%s", uid)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Dakikada en fazla {LIMIT_PER_MIN} sorgu yapabilirsiniz. "
                           f"{retry_after} saniye sonra tekrar deneyin.",
                    headers={"Retry-After": str(retry_after)},
                )

        hits.append(now)


def reset() -> None:
    """Test amaçlı — tüm sayaçları sıfırlar."""
    with _lock:
        _hits.clear()


async def enforce_rate_limit(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Kimlik doğrulaması + kota kontrolü yapan FastAPI dependency'si.
    Pahalı uçlarda `get_current_user` yerine bu kullanılır.
    """
    uid = current_user.get("uid") or "anonymous"
    check_rate_limit(uid)
    return current_user
