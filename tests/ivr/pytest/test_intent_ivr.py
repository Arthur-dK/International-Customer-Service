import pytest

from services.ivr.intent_router import (
    BLOCK_CARD,
    GET_BALANCE,
    GET_CARD_STATEMENT,
    GET_PIN,
    UNBLOCK_CARD,
    route_intent,
)

_CASES = (
    ("en", "what is my balance", GET_BALANCE),
    ("en", "I'd like the balance, please.", GET_BALANCE),
    ("en", "can I get my PIN", GET_PIN),
    ("en", "send the statement", GET_CARD_STATEMENT),
    ("en", "please block the card", BLOCK_CARD),
    ("en", "please unblock the card", UNBLOCK_CARD),
    ("fr", "quel est mon solde", GET_BALANCE),
    ("fr", "je voudrais le solde de la carte", GET_BALANCE),
    ("fr", "mon code pin", GET_PIN),
    ("fr", "le relevé du compte", GET_CARD_STATEMENT),
    ("fr", "le releve du compte", GET_CARD_STATEMENT),
    ("fr", "je veux bloquer la carte", BLOCK_CARD),
    ("fr", "je veux débloquer la carte", UNBLOCK_CARD),
    ("fr", "je veux debloquer la carte", UNBLOCK_CARD),
    ("he", "מה יתרה שלי", GET_BALANCE),
    ("he", "בבקשה ה יתרה", GET_BALANCE),
    ("he", "תן לי את פין", GET_PIN),
    ("he", "אני רוצה דוח", GET_CARD_STATEMENT),
    ("he", "בבקשה חסום את הכרטיס", BLOCK_CARD),
    ("he", "צריך שחרור לכרטיס", UNBLOCK_CARD),
    ("ar", "أريد رصيد البطاقة", GET_BALANCE),
    ("ar", "ما هو رصيد الحساب", GET_BALANCE),
    ("ar", "أعطني pin", GET_PIN),
    ("ar", "أرسل كشف الحساب", GET_CARD_STATEMENT),
    ("ar", "أريد حظر البطاقة", BLOCK_CARD),
    ("ar", "أريد تنشيط البطاقة", UNBLOCK_CARD),
    ("sw", "nataka salio yangu", GET_BALANCE),
    ("sw", "naomba salio tafadhali", GET_BALANCE),
    ("sw", "nataka pin", GET_PIN),
    ("sw", "naomba taarifa ya kadi", GET_CARD_STATEMENT),
    ("sw", "tafadhali zuia kadi", BLOCK_CARD),
    ("sw", "tafadhali fungua kadi", UNBLOCK_CARD),
)


@pytest.mark.parametrize(("language", "transcript", "intent"), _CASES)
def test_varied_phrasing_routes_when_the_keyword_is_a_whole_word(language, transcript, intent):
    assert route_intent(transcript, language) == intent


def test_unblock_does_not_match_block():
    assert route_intent("please unblock the card", "en") == UNBLOCK_CARD
    assert route_intent("je veux débloquer", "fr") == UNBLOCK_CARD
    assert route_intent("block", "en") == BLOCK_CARD


def test_two_actions_in_one_utterance_do_not_match():
    assert route_intent("block and balance", "en") is None
    assert route_intent("solde et pin", "fr") is None
    assert route_intent("zuia na salio", "sw") is None


def test_unknown_goodbye_and_blank_do_not_match():
    assert route_intent("how much is left on the card", "en") is None
    assert route_intent("goodbye", "en") is None
    assert route_intent("au revoir", "fr") is None
    assert route_intent("   ", "en") is None
    assert route_intent("", "he") is None


def test_keywords_from_another_language_do_not_match():
    assert route_intent("what is my balance", "fr") is None
    assert route_intent("quel est mon solde", "en") is None
    assert route_intent("nataka salio", "ar") is None


def test_language_tag_uses_the_primary_subtag():
    assert route_intent("my balance", "en-US") == GET_BALANCE
    assert route_intent("mon solde", "fr_FR") == GET_BALANCE
