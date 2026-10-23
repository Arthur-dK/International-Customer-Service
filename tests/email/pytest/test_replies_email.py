"""Phase 2: each email action has its own English placeholder line."""

import ast
from pathlib import Path

import pytest

from services.email import replies
from services.email.intent import (
    BLOCK_CARD,
    GET_BALANCE,
    GET_CARD_STATEMENT,
    GET_PIN,
    UNBLOCK_CARD,
)
from services.email.replies import UNKNOWN_REPLY, reply_for

_ACTIONS = (GET_BALANCE, GET_PIN, GET_CARD_STATEMENT, BLOCK_CARD, UNBLOCK_CARD)
_PHRASES = Path("core/language/phrases.json")


def test_each_action_has_a_distinct_english_line():
    lines = [reply_for(intent) for intent in _ACTIONS]
    assert len(set(lines)) == len(_ACTIONS)
    assert all(line.endswith("This is a placeholder.") for line in lines)


def test_pin_line_has_no_digits():
    pin = reply_for(GET_PIN)
    assert pin == "I confirm you wish to check the PIN. This is a placeholder."
    assert not any(char.isdigit() for char in pin)


def test_no_match_uses_the_fixed_sentence():
    assert reply_for(None) == UNKNOWN_REPLY
    assert UNKNOWN_REPLY == "I didn't understand what you meant by that."


def test_replies_are_owned_by_the_email_module():
    source = Path(replies.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    imported = [name for name in modules if name != "__future__"]
    assert imported == ["services.email.intent"]
    catalog = _PHRASES.read_text(encoding="utf-8")
    for intent in _ACTIONS:
        assert reply_for(intent) not in catalog
    assert UNKNOWN_REPLY not in catalog


def test_unknown_action_id_is_rejected():
    with pytest.raises(KeyError):
        reply_for("goodbye")
