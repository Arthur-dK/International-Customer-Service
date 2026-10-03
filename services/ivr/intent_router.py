"""Whole-word placeholder intents for five card actions.

The turn engine uses this router after language selection. Goodbye stays on
``map_placeholder_intent``, and only when no action keyword matched.
"""

from __future__ import annotations

import re
import unicodedata

GET_BALANCE = "get_balance"
GET_PIN = "get_pin"
GET_CARD_STATEMENT = "get_card_statement"
BLOCK_CARD = "block_card"
UNBLOCK_CARD = "unblock_card"

def _tokens(text: str) -> tuple[str, ...]:
    """Casefold, drop accents and Hebrew/Arabic vowel marks, then split on words."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    cleaned = re.sub(r"[^\w\s]", " ", without_marks, flags=re.UNICODE)
    return tuple(cleaned.split())


# Accents are stripped at load, so relevé and débloquer match releve and debloquer.
_RAW_KEYWORDS: dict[str, tuple[tuple[str, str], ...]] = {
    "en": (
        ("balance", GET_BALANCE),
        ("pin", GET_PIN),
        ("statement", GET_CARD_STATEMENT),
        ("block", BLOCK_CARD),
        ("unblock", UNBLOCK_CARD),
    ),
    "fr": (
        ("solde", GET_BALANCE),
        ("pin", GET_PIN),
        ("relevé", GET_CARD_STATEMENT),
        ("bloquer", BLOCK_CARD),
        ("débloquer", UNBLOCK_CARD),
    ),
    "he": (
        ("יתרה", GET_BALANCE),
        ("פין", GET_PIN),
        ("דוח", GET_CARD_STATEMENT),
        ("חסום", BLOCK_CARD),
        ("שחרור", UNBLOCK_CARD),
    ),
    "ar": (
        ("رصيد", GET_BALANCE),
        ("pin", GET_PIN),
        ("كشف", GET_CARD_STATEMENT),
        ("حظر", BLOCK_CARD),
        ("تنشيط", UNBLOCK_CARD),
    ),
    "sw": (
        ("salio", GET_BALANCE),
        ("pin", GET_PIN),
        ("taarifa", GET_CARD_STATEMENT),
        ("zuia", BLOCK_CARD),
        ("fungua", UNBLOCK_CARD),
    ),
}

_KEYWORDS: dict[str, tuple[tuple[tuple[str, ...], str], ...]] = {
    language: tuple((_tokens(phrase), intent) for phrase, intent in rows)
    for language, rows in _RAW_KEYWORDS.items()
}


def matched_intents(transcript: str, language: str) -> frozenset[str]:
    """Action ids whose keywords appear as whole tokens in the selected language."""
    language_code = (language or "en").lower().replace("_", "-").split("-", 1)[0]
    table = _KEYWORDS.get(language_code)
    if not table:
        return frozenset()
    tokens = _tokens(transcript)
    if not tokens:
        return frozenset()
    found: set[str] = set()
    for keyword, intent in table:
        width = len(keyword)
        for start in range(len(tokens) - width + 1):
            if tokens[start : start + width] == keyword:
                found.add(intent)
                break
    return frozenset(found)


def route_intent(transcript: str, language: str) -> str | None:
    """Return one action id, or None when the utterance is empty, unknown, or mixed.

    Only the selected language's keywords count. A keyword hits only as a whole
    token, or as a run of whole tokens. Two different actions in one utterance
    do not match.
    """
    found = matched_intents(transcript, language)
    if len(found) == 1:
        return next(iter(found))
    return None
