"""In-memory message keys so a SendGrid retry does not send twice."""

from __future__ import annotations

import hashlib
import threading

_SEEN: set[str] = set()
_LOCK = threading.Lock()


def delivery_key(message_id: str, sender: str, recipient: str, text: str) -> str:
    """The Message-ID when the headers have one, otherwise a hash of from, to, and text."""
    if message_id:
        return message_id
    raw = f"{sender}\n{recipient}\n{text}".encode()
    return hashlib.sha256(raw).hexdigest()


def already_handled(message_key: str) -> bool:
    """True when this process already accepted a send for this key."""
    if not message_key:
        return False
    with _LOCK:
        return message_key in _SEEN


def remember_message(message_key: str) -> None:
    """Keep a key after the Mail Send call succeeds."""
    if not message_key:
        return
    with _LOCK:
        _SEEN.add(message_key)


def forget_message(message_key: str) -> None:
    """Drop a key when the send fails, so SendGrid's retry can try again."""
    if not message_key:
        return
    with _LOCK:
        _SEEN.discard(message_key)


def clear_seen_messages() -> None:
    """Test helper. A process restart clears the set the same way."""
    with _LOCK:
        _SEEN.clear()
