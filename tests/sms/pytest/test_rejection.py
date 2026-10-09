"""Phase 3: unknown numbers get the translated not-recognised SMS."""

from app.api import sms as sms_api
from core.config import settings
from tests.sms.pytest.test_signature import _TOKEN, _URL, _post, _sign

_TWILIO = "+15550002222"
_FRENCH = "Ce numéro n'est pas reconnu."
_ENGLISH = "This number is not recognised."
_HEBREW = "המספר הזה אינו מזוהה."
_ARABIC = "هذا الرقم غير معروف."


def _allow_nobody(monkeypatch) -> None:
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    monkeypatch.setattr(
        "core.telephony.allowlist.load_allowed_numbers",
        lambda path=None: frozenset(),
    )


def _capture(monkeypatch):
    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        sent.append((from_, to, body))

    monkeypatch.setattr(sms_api, "send_sms", fake_send)
    return sent


def _signed_post(data: dict[str, str]):
    return _post(data, signature=_sign(_URL, data))


def test_unknown_french_number_gets_the_french_line(monkeypatch, caplog):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    inbound = "solde s'il vous plaît"
    data = {"MessageSid": "SM20", "From": "+33142685300", "To": _TWILIO, "Body": inbound}
    with caplog.at_level("INFO"):
        response = _signed_post(data)
    assert response.status_code == 200
    assert "<Message" not in response.text
    assert sent == [(_TWILIO, "+33142685300", _FRENCH)]
    assert inbound not in sent[0][2]
    assert inbound not in caplog.text
    assert "sms_reject message_sid=SM20" in caplog.text


def test_unknown_empty_body_sends_nothing(monkeypatch):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM21", "From": "+33142685300", "To": _TWILIO, "Body": ""}
    response = _signed_post(data)
    assert response.status_code == 200
    assert sent == []


def test_missing_body_sends_nothing(monkeypatch):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM22", "From": "+33142685300", "To": _TWILIO}
    response = _signed_post(data)
    assert response.status_code == 200
    assert sent == []


def test_spaces_from_an_unknown_number_are_rejected(monkeypatch):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM23", "From": "+442071838750", "To": _TWILIO, "Body": "  "}
    response = _signed_post(data)
    assert response.status_code == 200
    assert sent == [(_TWILIO, "+442071838750", _ENGLISH)]


def test_picture_without_a_caption_sends_nothing(monkeypatch):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    data = {
        "MessageSid": "SM24",
        "From": "+33142685300",
        "To": _TWILIO,
        "Body": "",
        "NumMedia": "1",
    }
    response = _signed_post(data)
    assert response.status_code == 200
    assert sent == []


def test_picture_caption_from_an_unknown_number_is_rejected(monkeypatch):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    data = {
        "MessageSid": "SM25",
        "From": "+966501234567",
        "To": _TWILIO,
        "Body": "photo",
        "NumMedia": "1",
    }
    response = _signed_post(data)
    assert response.status_code == 200
    assert sent == [(_TWILIO, "+966501234567", _ARABIC)]
    assert "photo" not in sent[0][2]


def test_hebrew_and_swahili_use_the_voice_lines(monkeypatch):
    _allow_nobody(monkeypatch)
    sent = _capture(monkeypatch)
    hebrew = {"MessageSid": "SM26", "From": "+972501234567", "To": _TWILIO, "Body": "יתרה"}
    kenya = {"MessageSid": "SM27", "From": "+254712345678", "To": _TWILIO, "Body": "salio"}
    assert _signed_post(hebrew).status_code == 200
    assert _signed_post(kenya).status_code == 200
    assert sent == [
        (_TWILIO, "+972501234567", _HEBREW),
        (_TWILIO, "+254712345678", _ENGLISH),
    ]
