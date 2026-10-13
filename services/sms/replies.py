"""English placeholder replies for one SMS.

These lines are not read from the IVR phrase catalog. They contain no
real PIN, balance, or card status.
"""

from __future__ import annotations

from services.sms.intent import (
    BLOCK_CARD,
    GET_BALANCE,
    GET_CARD_STATEMENT,
    GET_PIN,
    UNBLOCK_CARD,
)

UNKNOWN_REPLY = (
    "I do not know what you are talking about, please limit your requests to 1 message."
)

_REPLIES: dict[str, str] = {
    GET_BALANCE: "I confirm you wish to check the balance. This is a placeholder.",
    GET_PIN: "I confirm you wish to check the PIN. This is a placeholder.",
    GET_CARD_STATEMENT: "I confirm you wish to check the statement. This is a placeholder.",
    BLOCK_CARD: "I confirm you wish to block the card. This is a placeholder.",
    UNBLOCK_CARD: "I confirm you wish to unblock the card. This is a placeholder.",
}


def reply_for(intent: str | None) -> str:
    """English line for one action id, or the no-match line when there is none."""
    if intent is None:
        return UNKNOWN_REPLY
    return _REPLIES[intent]
