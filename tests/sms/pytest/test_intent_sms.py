import pytest

from services.sms.intent import (
    BLOCK_CARD,
    GET_BALANCE,
    GET_CARD_STATEMENT,
    GET_PIN,
    UNBLOCK_CARD,
    match_intent,
)

_CASES = (
    ("what is my balance", GET_BALANCE),
    ("I'd like the balance, please.", GET_BALANCE),
    ("can I get my PIN", GET_PIN),
    ("send the statement", GET_CARD_STATEMENT),
    ("please block the card", BLOCK_CARD),
    ("please unblock the card", UNBLOCK_CARD),
    ("block", BLOCK_CARD),
)


@pytest.mark.parametrize(("text", "intent"), _CASES)
def test_varied_phrasing_routes_when_the_keyword_is_a_whole_word(text, intent):
    assert match_intent(text) == intent


def test_unblock_does_not_match_block():
    assert match_intent("please unblock the card") == UNBLOCK_CARD
    assert match_intent("block") == BLOCK_CARD
    assert match_intent("blocking the card") is None


def test_two_actions_return_the_earlier_keyword():
    assert match_intent("block and balance") == BLOCK_CARD
    assert match_intent("balance and block") == GET_BALANCE
    assert match_intent("please unblock then block") == UNBLOCK_CARD
    assert match_intent("pin, then the statement") == GET_PIN


def test_unknown_blank_and_punctuation_do_not_match():
    assert match_intent("how much is left on the card") is None
    assert match_intent("goodbye") is None
    assert match_intent("   ") is None
    assert match_intent("") is None
    assert match_intent("???") is None
    assert match_intent("...") is None
