"""Yes and no words for block and unblock."""

from services.ivr.confirm import NO, YES, route_confirm


def test_confirm_words_for_each_language():
    assert route_confirm("yes please", "en") == YES
    assert route_confirm("no", "en") == NO
    assert route_confirm("oui", "fr") == YES
    assert route_confirm("non", "fr") == NO
    assert route_confirm("ken", "he") == YES
    assert route_confirm("כן", "he") == YES
    assert route_confirm("lo", "he") == NO
    assert route_confirm("לא", "he") == NO
    assert route_confirm("naam", "ar") == YES
    assert route_confirm("نعم", "ar") == YES
    assert route_confirm("la", "ar") == NO
    assert route_confirm("لا", "ar") == NO
    assert route_confirm("ndiyo", "sw") == YES
    assert route_confirm("hapana", "sw") == NO


def test_confirm_rejects_other_speech_and_silence():
    assert route_confirm("yesterday", "en") is None
    assert route_confirm("yes and no", "en") is None
    assert route_confirm("", "en") is None
    assert route_confirm("yes", "fr") is None
    assert route_confirm("oui", "en") is None
