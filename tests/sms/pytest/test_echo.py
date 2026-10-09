"""Phase 2: an allowlisted non-empty body is echoed through the Messages API."""

from app.api import sms as sms_api
from core.config import settings
from tests.sms.pytest.test_signature import _TOKEN, _URL, _post, _sign

_SENDER = "+15550001111"
_TWILIO = "+15550002222"
_BODY = "pin-9876 café"


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


def test_allowlisted_body_is_echoed_once(monkeypatch, caplog):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM10", "From": _SENDER, "To": _TWILIO, "Body": _BODY}
    with caplog.at_level("INFO"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert "<Response" in response.text
    assert "<Message" not in response.text
    assert sent == [(_TWILIO, _SENDER, _BODY)]
    assert "sms_echo message_sid=SM10" in caplog.text
    assert _BODY not in caplog.text


def test_spaces_are_echoed_exactly(monkeypatch):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM11", "From": _SENDER, "To": _TWILIO, "Body": "  "}
    response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert sent == [(_TWILIO, _SENDER, "  ")]


def test_unknown_number_is_not_echoed(monkeypatch):
    _allow(monkeypatch, "+15559999999")
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM12", "From": _SENDER, "To": _TWILIO, "Body": _BODY}
    response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert "<Message" not in response.text
    assert sent == [(_TWILIO, _SENDER, "This number is not recognised.")]
    assert _BODY not in sent[0][2]


def test_empty_body_is_not_echoed(monkeypatch):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM13", "From": _SENDER, "To": _TWILIO, "Body": ""}
    response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert sent == []


def test_bad_signature_does_not_echo(monkeypatch):
    _allow(monkeypatch, _SENDER)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM14", "From": _SENDER, "To": _TWILIO, "Body": _BODY}
    response = _post(data, signature="forged")
    assert response.status_code == 403
    assert sent == []


def test_messages_api_failure_returns_500(monkeypatch, caplog):
    _allow(monkeypatch, _SENDER)

    async def fail(*, from_: str, to: str, body: str) -> None:
        raise RuntimeError(body)

    monkeypatch.setattr(sms_api, "send_sms", fail)
    data = {"MessageSid": "SM15", "From": _SENDER, "To": _TWILIO, "Body": _BODY}
    with caplog.at_level("ERROR"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 500
    assert "<Message" not in response.text
    assert "sms_send_failed message_sid=SM15 error=RuntimeError" in caplog.text
    assert _BODY not in caplog.text
