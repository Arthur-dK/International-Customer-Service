"""Phase 1: POST /sms/incoming accepts a Twilio signature and sends no SMS."""

from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from app.api import sms as sms_api
from app.main import app
from core.config import settings

client = TestClient(app)

_TOKEN = "test_auth_token"
_HOST = "example.ngrok-free.app"
_URL = f"https://{_HOST}/sms/incoming"
_BODY = "pin-9876 café"


def _sign(url: str, data: dict[str, str], token: str = _TOKEN) -> str:
    return RequestValidator(token).compute_signature(url, data)


def _no_send(monkeypatch) -> None:
    async def fake_send(*, from_: str, to: str, body: str) -> None:
        return None

    monkeypatch.setattr(sms_api, "send_sms", fake_send)


def _post(data: dict[str, str], signature: str | None, url: str = _URL):
    headers = {"host": _HOST, "x-forwarded-proto": "https"}
    if signature is not None:
        headers["x-twilio-signature"] = signature
    return client.post("/sms/incoming", headers=headers, data=data)


def test_missing_signature_is_forbidden(monkeypatch, caplog):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    data = {"From": "+15550001111", "To": "+15550002222", "Body": _BODY, "MessageSid": "SM1"}
    with caplog.at_level("INFO"):
        response = _post(data, signature=None)
    assert response.status_code == 403
    assert "<Message" not in response.text
    assert _BODY not in caplog.text


def test_bad_signature_is_forbidden(monkeypatch, caplog):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    data = {"From": "+15550001111", "To": "+15550002222", "Body": _BODY, "MessageSid": "SM2"}
    with caplog.at_level("INFO"):
        response = _post(data, signature="not-a-signature")
    assert response.status_code == 403
    assert _BODY not in caplog.text


def test_valid_signature_returns_empty_twiml_and_no_message(monkeypatch, caplog):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    _no_send(monkeypatch)
    data = {
        "MessageSid": "SM3",
        "From": "+15550001111",
        "To": "+15550002222",
        "Body": _BODY,
        "NumMedia": "0",
    }
    with caplog.at_level("INFO"):
        response = _post(data, signature=_sign(_URL, data))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/xml")
    assert "<Response" in response.text
    assert "<Message" not in response.text
    assert "from=+15550001111" in caplog.text
    assert "to=+15550002222" in caplog.text
    assert "message_sid=SM3" in caplog.text
    assert "signature=valid" in caplog.text
    assert _BODY not in caplog.text


def test_signature_must_use_the_forwarded_https_url(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    data = {"From": "+15550001111", "To": "+15550002222", "Body": "hi", "MessageSid": "SM4"}
    http_url = f"http://{_HOST}/sms/incoming"
    response = _post(data, signature=_sign(http_url, data))
    assert response.status_code == 403


def test_query_string_is_part_of_the_signed_url(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TOKEN)
    _no_send(monkeypatch)
    data = {"From": "+15550001111", "To": "+15550002222", "Body": "hi", "MessageSid": "SM5"}
    signed = f"{_URL}?attempt=1"
    headers = {
        "host": _HOST,
        "x-forwarded-proto": "https",
        "x-twilio-signature": _sign(signed, data),
    }
    response = client.post("/sms/incoming?attempt=1", headers=headers, data=data)
    assert response.status_code == 200
    assert "<Message" not in response.text
