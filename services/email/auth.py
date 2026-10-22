"""HTTP basic auth for the SendGrid Inbound Parse webhook."""

from __future__ import annotations

import base64
import secrets

from core.config import settings


def basic_auth_is_valid(header: str | None) -> bool:
    """True when the header matches the inbound user and password in settings.

    An empty configured user or password never matches. The password may contain
    a colon; only the first colon separates the user from the password.
    """
    expected_user = settings.SENDGRID_INBOUND_USER
    expected_password = settings.SENDGRID_INBOUND_PASSWORD
    if not expected_user or not expected_password or not header:
        return False
    scheme, _, encoded = header.strip().partition(" ")
    if scheme.lower() != "basic" or not encoded:
        return False
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    user, separator, password = decoded.partition(":")
    if not separator:
        return False
    return secrets.compare_digest(user, expected_user) and secrets.compare_digest(
        password, expected_password
    )
