"""Yes or no for block and unblock.

Only the selected language's words count. A word matches as a whole token.
Silence is not an answer. Two answers in one utterance are not an answer.
"""

from __future__ import annotations

import re
import unicodedata

YES = "yes"
NO = "no"

_RAW: dict[str, tuple[tuple[str, str], ...]] = {
    "en": (("yes", YES), ("no", NO)),
    "fr": (("oui", YES), ("non", NO)),
    "he": (("ken", YES), ("כן", YES), ("lo", NO), ("לא", NO)),
    "ar": (("naam", YES), ("نعم", YES), ("la", NO), ("لا", NO)),
    "sw": (("ndiyo", YES), ("hapana", NO)),
}


def _tokens(text: str) -> tuple[str, ...]:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    cleaned = re.sub(r"[^\w\s]", " ", without_marks, flags=re.UNICODE)
    return tuple(cleaned.split())


_WORDS: dict[str, tuple[tuple[tuple[str, ...], str], ...]] = {
    language: tuple((_tokens(word), answer) for word, answer in pairs)
    for language, pairs in _RAW.items()
}


def route_confirm(transcript: str, language: str) -> str | None:
    """Return ``yes``, ``no``, or nothing when the utterance is not one answer."""
    language_code = (language or "en").lower().replace("_", "-").split("-", 1)[0]
    table = _WORDS.get(language_code)
    if not table:
        return None
    tokens = _tokens(transcript)
    if not tokens:
        return None
    found: set[str] = set()
    for word, answer in table:
        width = len(word)
        for start in range(len(tokens) - width + 1):
            if tokens[start : start + width] == word:
                found.add(answer)
                break
    if len(found) == 1:
        return next(iter(found))
    return None
