"""Offline language id for one SMS body.

The code is detected before a reply is chosen. It does not select the
keywords or the reply language. Blank text and detector failures are English.
"""

from __future__ import annotations

import py3langid


def detect_language(text: str) -> tuple[str, float]:
    """Return an ISO 639-1 code and a confidence score. Blank text and a detector failure return ``en``."""
    if not text or not text.strip():
        return "en", 0.0
    try:
        language, _score = py3langid.classify(text)
    except Exception:
        return "en", 0.0
    code = (language or "en").lower().replace("_", "-").split("-", 1)[0]
    if not code.isalpha():
        return "en", 0.0
    return code, _score
