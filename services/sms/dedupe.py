"""In-memory MessageSid set so a Twilio retry does not send twice."""

from __future__ import annotations

import threading

_SEEN: set[str] = set()
_LOCK = threading.Lock()


def already_handled(message_sid: str | None) -> bool:
    """True when this process already accepted a send for this sid."""
    if not message_sid:
        return False
    with _LOCK:
        return message_sid in _SEEN


def remember_message_sid(message_sid: str | None) -> None:
    """Keep a sid after the Messages API call succeeds."""
    if not message_sid:
        return
    with _LOCK:
        _SEEN.add(message_sid)


def forget_message_sid(message_sid: str | None) -> None:
    """Drop a sid when the send fails, so Twilio's retry can try again."""
    if not message_sid:
        return
    with _LOCK:
        _SEEN.discard(message_sid)


def clear_seen_message_sids() -> None:
    """Test helper. A process restart clears the set the same way."""
    with _LOCK:
        _SEEN.clear()
