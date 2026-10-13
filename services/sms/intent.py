"""English whole-word placeholder intents for one SMS.

Five card actions, matched the same way as the IVR English keywords.
Two actions in one text return the one that appears first. Nothing is stored.
"""

from __future__ import annotations

import re
import unicodedata

GET_BALANCE = "get_balance"
GET_PIN = "get_pin"
GET_CARD_STATEMENT = "get_card_statement"
BLOCK_CARD = "block_card"
UNBLOCK_CARD = "unblock_card"

_RAW_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("balance", GET_BALANCE),
    ("pin", GET_PIN),
    ("statement", GET_CARD_STATEMENT),
    ("block", BLOCK_CARD),
    ("unblock", UNBLOCK_CARD),
)


def _tokens(text: str) -> tuple[str, ...]:
    """Casefold, drop accents, then split on words."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    cleaned = re.sub(r"[^\w\s]", " ", without_marks, flags=re.UNICODE)
    return tuple(cleaned.split())


_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = tuple(
    (_tokens(phrase), intent) for phrase, intent in _RAW_KEYWORDS
)


def match_intent(text: str) -> str | None:
    """Return one action id, or None when the text is empty or has no keyword.

    A keyword hits only as a whole token. ``unblock`` is not ``block``.
    When two different actions appear, the one with the earlier token wins.
    """
    tokens = _tokens(text or "")
    if not tokens:
        return None
    earliest: tuple[int, str] | None = None
    for keyword, intent in _KEYWORDS:
        width = len(keyword)
        for start in range(len(tokens) - width + 1):
            if tokens[start : start + width] != keyword:
                continue
            if earliest is None or start < earliest[0]:
                earliest = (start, intent)
            break
    if earliest is None:
        return None
    return earliest[1]
