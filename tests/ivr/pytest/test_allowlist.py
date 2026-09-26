import json

from core.telephony.allowlist import is_caller_allowed, load_allowed_numbers
from core.telephony.rejection import not_recognised_say


def test_load_allowed_numbers_strips_surrounding_spaces(tmp_path):
    path = tmp_path / "allowed_callers.json"
    path.write_text(
        json.dumps({"numbers": ["  +972501234567  ", "", "   "]}),
        encoding="utf-8",
    )
    assert load_allowed_numbers(path) == frozenset({"+972501234567"})


def test_is_caller_allowed_is_exact_after_trim():
    allowed = ["  +442071838750  "]
    assert is_caller_allowed("+442071838750", allowed)
    assert is_caller_allowed("  +442071838750", allowed)
    assert not is_caller_allowed("+44 207 183 8750", allowed)
    assert not is_caller_allowed("+972501234567", allowed)


def test_missing_and_blank_callers_are_not_allowed():
    allowed = ["+442071838750"]
    assert not is_caller_allowed(None, allowed)
    assert not is_caller_allowed("", allowed)
    assert not is_caller_allowed("   ", allowed)
    assert not is_caller_allowed("anonymous", allowed)


def test_empty_allowlist_rejects_every_number():
    assert not is_caller_allowed("+442071838750", [])


def test_not_recognised_say_uses_twilio_languages():
    assert not_recognised_say("fr") == ("fr-FR", "Ce numéro n'est pas reconnu.")
    assert not_recognised_say("he")[0] == "he-IL"
    assert not_recognised_say("ar")[0] == "ar-XA"
    assert not_recognised_say("en")[0] == "en-US"


def test_not_recognised_say_falls_back_when_twilio_cannot_speak_the_language():
    english = not_recognised_say("en")
    assert not_recognised_say("sw") == english
    assert not_recognised_say("de") == english
    assert not_recognised_say(None) == english
