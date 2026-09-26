"""Spoken rejection for a calling number that is not on the allowlist.

Twilio ``<Say>`` can speak English, French, Hebrew, and Arabic. It has no
Swahili voice, so a Swahili country prompt falls back to the English line.
"""

from __future__ import annotations

# Prompt language -> (Twilio Say language, spoken line).
_SAY_LINES: dict[str, tuple[str, str]] = {
    "en": ("en-US", "This number is not recognised."),
    "fr": ("fr-FR", "Ce numéro n'est pas reconnu."),
    "he": ("he-IL", "המספר הזה אינו מזוהה."),
    "ar": ("ar-XA", "هذا الرقم غير معروف."),
}

_ENGLISH = _SAY_LINES["en"]


def not_recognised_say(prompt_language: str | None) -> tuple[str, str]:
    """Return ``(twilio_language, text)`` for the not-recognised line.

    Languages Twilio ``<Say>`` cannot speak, including Swahili, use English.
    """
    code = (prompt_language or "en").lower().replace("_", "-").split("-", 1)[0]
    return _SAY_LINES.get(code, _ENGLISH)
