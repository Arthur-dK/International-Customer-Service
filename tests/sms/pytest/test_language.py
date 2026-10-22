import socket
import time

from services.language import detect_language

_ENGLISH = "Please tell me the balance on my card today."
_FRENCH = "Bonjour, je voudrais connaitre le solde de ma carte."
_HEBREW = "שלום, אני רוצה לבדוק את היתרה של הכרטיס."


def test_obvious_sentences_are_labeled_quickly():
    started = time.perf_counter()
    assert detect_language(_ENGLISH)[0] == "en"
    assert detect_language(_FRENCH)[0] == "fr"
    assert detect_language(_HEBREW)[0] == "he"
    assert time.perf_counter() - started < 4


def test_blank_text_is_english():
    assert detect_language("")[0] == "en"
    assert detect_language("   ")[0] == "en"


def test_detector_failure_is_english(monkeypatch):
    def fail(text: str):
        raise RuntimeError("detector down")

    monkeypatch.setattr("services.language.py3langid.classify", fail)
    assert detect_language(_ENGLISH)[0] == "en"


def test_detection_does_not_open_a_network_connection(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("detect_language opened a network connection")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    assert detect_language(_FRENCH)[0] == "fr"
