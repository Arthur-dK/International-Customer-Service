"""Process-local count of echo sends for the current UTC day."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from core.config import settings

_LOCK = threading.Lock()
_DAY = ""
_COUNT = 0


def try_reserve() -> bool:
    """True when this send still fits under EMAIL_DAILY_SEND_CAP."""
    global _DAY, _COUNT
    today = datetime.now(timezone.utc).date().isoformat()
    with _LOCK:
        if _DAY != today:
            _DAY = today
            _COUNT = 0
        if _COUNT >= settings.EMAIL_DAILY_SEND_CAP:
            return False
        _COUNT += 1
        return True


def release() -> None:
    """Give a reservation back when the Mail Send call fails."""
    global _COUNT
    with _LOCK:
        if _COUNT > 0:
            _COUNT -= 1


def clear_quota() -> None:
    """Test helper. A process restart clears the count the same way."""
    global _DAY, _COUNT
    with _LOCK:
        _DAY = ""
        _COUNT = 0
