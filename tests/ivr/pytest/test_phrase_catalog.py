"""Phase 3: one shared reply per action, and the PIN line speaks no PIN."""

from __future__ import annotations

import re

from core.language.phrases import (
    PLACEHOLDER_BALANCE,
    PLACEHOLDER_BLOCKED,
    PLACEHOLDER_PIN,
    PLACEHOLDER_STATEMENT,
    PLACEHOLDER_UNBLOCKED,
    load_phrase_catalog,
)

_ACTIONS = (
    PLACEHOLDER_BALANCE,
    PLACEHOLDER_PIN,
    PLACEHOLDER_STATEMENT,
    PLACEHOLDER_BLOCKED,
    PLACEHOLDER_UNBLOCKED,
)
_LANGUAGES = ("en", "fr", "he", "ar", "sw")

# A run of these would speak a PIN ("one two three four"). A lone "un" in
# "un exemple" is the French article, so a single hit is allowed.
_NUMBER_WORDS = {
    "en": {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero"},
    "fr": {"un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "zero"},
    "he": {"אחת", "אחד", "שתיים", "שניים", "שלוש", "ארבע", "חמש", "שש", "שבע", "שמונה", "תשע", "אפס"},
    "ar": {"واحد", "اثنان", "ثلاثة", "أربعة", "اربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "صفر"},
    "sw": {"moja", "mbili", "tatu", "nne", "tano", "sita", "saba", "nane", "tisa", "sifuri"},
}


def _tokens(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.casefold(), flags=re.UNICODE).split()


def _has_number_word_run(tokens: list[str], words: set[str]) -> bool:
    run = 0
    for token in tokens:
        if token in words:
            run += 1
            if run >= 2:
                return True
        else:
            run = 0
    return False


def test_each_action_has_one_line_in_each_language():
    catalog = load_phrase_catalog()
    for phrase_id in _ACTIONS:
        texts = [catalog.text(phrase_id, language, strict=True) for language in _LANGUAGES]
        assert len(set(texts)) == len(_LANGUAGES)


def test_pin_line_does_not_speak_a_pin():
    catalog = load_phrase_catalog()
    for language in _LANGUAGES:
        text = catalog.text(PLACEHOLDER_PIN, language, strict=True)
        assert not re.search(r"\d", text)
        assert not _has_number_word_run(_tokens(text), _NUMBER_WORDS[language])


def test_same_balance_line_for_every_caller():
    catalog = load_phrase_catalog()
    english = catalog.text(PLACEHOLDER_BALANCE, "en", strict=True)
    assert english == "Your available balance is one hundred dollars. This is a placeholder."
    assert "one two three four" not in catalog.text(PLACEHOLDER_PIN, "en", strict=True)
