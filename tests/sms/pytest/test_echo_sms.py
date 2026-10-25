"""Allowlisted texts get one English placeholder through the Messages API."""

import json

from app.api import sms as sms_api
from core.config import settings
from services.language import detect_language
from services.sms.replies import UNKNOWN_REPLY, reply_for
from services.sms.intent import BLOCK_CARD, GET_PIN
from tests.sms.pytest.test_signature import _TOKEN, _URL, _post, _sign

_SENDER = "+15550001111"
_TWILIO = "+15550002222"
_PIN = "pin"
_PIN_LINE = reply_for(GET_PIN)


def _allow(monkeypatch, *numbers: str) -> None:
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    monkeypatch.setattr(
        "core.telephony.allowlist.load_allowed_numbers",
        lambda path=None: frozenset(numbers),
    )


def _capture(monkeypatch):
    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        sent.append((from_, to, body))

    monkeypatch.setattr(sms_api, "send_sms", fake_send)
    return sent


def test_allowlisted_pin_gets_the_placeholder(monkeypatch, caplog):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM10", "From": _SENDER, "To": _TWILIO, "Body": _PIN}
    with caplog.at_level("INFO"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert "<Response" in response.text
    assert "<Message" not in response.text
    language, score = detect_language(_PIN)
    assert sent == [(_TWILIO, _SENDER, _PIN_LINE)]
    assert json.dumps(
        {
            "event": "sms_reply",
            "message_sid": "SM10",
            "language": language,
            "score": float(score),
            "intent": "get_pin",
        }
    ) in caplog.text
    assert _PIN_LINE not in caplog.text


def test_two_actions_use_the_earlier_keyword(monkeypatch, caplog):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    inbound = "block and balance"
    data = {"MessageSid": "SM16", "From": _SENDER, "To": _TWILIO, "Body": inbound}
    with caplog.at_level("INFO"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert sent == [(_TWILIO, _SENDER, reply_for(BLOCK_CARD))]
    assert '"intent": "block_card"' in caplog.text
    assert '"score":' in caplog.text
    assert inbound not in caplog.text


def test_no_match_gets_the_unknown_line(monkeypatch, caplog):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    inbound = "what time is it"
    data = {"MessageSid": "SM17", "From": _SENDER, "To": _TWILIO, "Body": inbound}
    with caplog.at_level("INFO"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert sent == [(_TWILIO, _SENDER, UNKNOWN_REPLY)]
    assert '"intent": "none"' in caplog.text
    assert '"score":' in caplog.text
    assert inbound not in caplog.text


def test_spaces_get_the_unknown_line(monkeypatch):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM11", "From": _SENDER, "To": _TWILIO, "Body": "  "}
    response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert sent == [(_TWILIO, _SENDER, UNKNOWN_REPLY)]


def test_unknown_number_is_not_answered_with_the_body(monkeypatch):
    _allow(monkeypatch, "+15559999999")
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM12", "From": _SENDER, "To": _TWILIO, "Body": _PIN}
    response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert "<Message" not in response.text
    assert sent == [(_TWILIO, _SENDER, "This number is not recognised.")]
    assert _PIN not in sent[0][2]


def test_empty_body_is_not_sent(monkeypatch):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM13", "From": _SENDER, "To": _TWILIO, "Body": ""}
    response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert sent == []


def test_bad_signature_does_not_send(monkeypatch):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM14", "From": _SENDER, "To": _TWILIO, "Body": _PIN}
    response = _post(data, signature="forged")
    assert response.status_code == 403
    assert sent == []


def test_messages_api_failure_returns_500(monkeypatch, caplog):
    _allow(monkeypatch, _SENDER)
    inbound = "please block the card"

    async def fail(*, from_: str, to: str, body: str) -> None:
        raise RuntimeError("send failed")

    monkeypatch.setattr(sms_api, "send_sms", fail)
    data = {"MessageSid": "SM15", "From": _SENDER, "To": _TWILIO, "Body": inbound}
    with caplog.at_level("ERROR"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 500
    assert "<Message" not in response.text
    assert "sms_send_failed message_sid=SM15 error=RuntimeError" in caplog.text
    assert inbound not in caplog.text
