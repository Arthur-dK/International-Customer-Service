"""Phase 4: one MessageSid sends once. A failed send can be retried."""

from app.api import sms as sms_api
from core.config import settings
from tests.sms.pytest.test_signature import _TOKEN, _URL, _post, _sign

_SENDER = "+15550001111"
_TWILIO = "+15550002222"
_BODY = "same text"


def _allow(monkeypatch) -> None:
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    monkeypatch.setattr(
        "core.telephony.allowlist.load_allowed_numbers",
        lambda path=None: frozenset({_SENDER}),
    )


def _capture(monkeypatch):
    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        sent.append((from_, to, body))

    monkeypatch.setattr(sms_api, "send_sms", fake_send)
    return sent


def test_second_post_of_the_same_sid_does_not_send(monkeypatch, caplog):
    _allow(monkeypatch)
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM40", "From": _SENDER, "To": _TWILIO, "Body": _BODY}
    signature = _sign(_URL, data)
    with caplog.at_level("INFO"):
        first = _post(data, signature=signature)
        second = _post(data, signature=signature)
    assert first.status_code == 200
    assert second.status_code == 200
    assert "<Message" not in second.text
    assert sent == [(_TWILIO, _SENDER, _BODY)]
    assert "sms_duplicate message_sid=SM40" in caplog.text
    assert _BODY not in caplog.text


def test_failed_send_is_forgotten_and_a_retry_can_send(monkeypatch, caplog):
    _allow(monkeypatch)
    calls = {"n": 0}

    async def fail_once(*, from_: str, to: str, body: str) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError(body)

    monkeypatch.setattr(sms_api, "send_sms", fail_once)
    data = {"MessageSid": "SM41", "From": _SENDER, "To": _TWILIO, "Body": _BODY}
    signature = _sign(_URL, data)
    with caplog.at_level("ERROR"):
        failed = _post(data, signature=signature)
        retried = _post(data, signature=signature)
    assert failed.status_code == 500
    assert retried.status_code == 200
    assert calls["n"] == 2
    assert "sms_send_failed message_sid=SM41 error=RuntimeError" in caplog.text
    assert _BODY not in caplog.text


def test_duplicate_rejection_sends_once(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    monkeypatch.setattr(
        "core.telephony.allowlist.load_allowed_numbers",
        lambda path=None: frozenset(),
    )
    sent = _capture(monkeypatch)
    data = {"MessageSid": "SM42", "From": "+33142685300", "To": _TWILIO, "Body": "bonjour"}
    signature = _sign(_URL, data)
    assert _post(data, signature=signature).status_code == 200
    assert _post(data, signature=signature).status_code == 200
    assert len(sent) == 1
    assert sent[0][2] == "Ce numéro n'est pas reconnu."
