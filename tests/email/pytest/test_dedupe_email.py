"""Phase 5: one Message-ID sends once. A failed send can be retried."""

import base64

import httpx
from fastapi.testclient import TestClient

from app.main import app
from core.config import settings
from services.email.quota import clear_quota

client = TestClient(app)

_USER = "inbound"
_PASSWORD = "phase-five-secret"
_TEXT = "same plain text"


def _auth() -> str:
    token = base64.b64encode(f"{_USER}:{_PASSWORD}".encode()).decode()
    return f"Basic {token}"


def _configure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "SENDGRID_INBOUND_USER", _USER)
    monkeypatch.setattr(settings, "SENDGRID_INBOUND_PASSWORD", _PASSWORD)
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "test-key")
    clear_quota()


def _payload(message_id: str | None) -> dict[str, str]:
    data = {
        "from": "sender@example.com",
        "to": "echo@internationalivr.xyz",
        "subject": "Hello",
        "text": _TEXT,
        "envelope": '{"to":["echo@internationalivr.xyz"],"from":"sender@example.com"}',
    }
    if message_id is not None:
        data["headers"] = f"Message-ID: {message_id}\nFrom: sender@example.com\n"
    return data


def _capture(monkeypatch) -> list[dict]:
    calls: list[dict] = []

    def fake_post(url, *, headers, json, timeout):
        calls.append(json)
        return httpx.Response(202, request=httpx.Request("POST", url))

    monkeypatch.setattr("services.email.outbound.httpx.post", fake_post)
    return calls


def test_second_post_of_the_same_message_id_does_not_send(monkeypatch, caplog):
    _configure(monkeypatch)
    calls = _capture(monkeypatch)
    headers = {"authorization": _auth()}
    data = _payload("<same@mail.example>")
    with caplog.at_level("INFO"):
        first = client.post("/email/incoming", headers=headers, data=data)
        second = client.post("/email/incoming", headers=headers, data=data)
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(calls) == 1
    assert calls[0]["content"] == [{"type": "text/plain", "value": _TEXT}]
    assert "email_duplicate message_id=<same@mail.example>" in caplog.text
    assert _TEXT not in caplog.text


def test_missing_message_id_uses_the_same_text_once(monkeypatch):
    _configure(monkeypatch)
    calls = _capture(monkeypatch)
    headers = {"authorization": _auth()}
    data = _payload(None)
    assert client.post("/email/incoming", headers=headers, data=data).status_code == 200
    assert client.post("/email/incoming", headers=headers, data=data).status_code == 200
    assert len(calls) == 1


def test_failed_send_is_forgotten_and_a_retry_can_send(monkeypatch, caplog):
    _configure(monkeypatch)
    calls = {"n": 0}

    def fail_once(url, *, headers, json, timeout):
        calls["n"] += 1
        status = 401 if calls["n"] == 1 else 202
        return httpx.Response(status, request=httpx.Request("POST", url))

    monkeypatch.setattr("services.email.outbound.httpx.post", fail_once)
    headers = {"authorization": _auth()}
    data = _payload("<retry@mail.example>")
    with caplog.at_level("ERROR"):
        failed = client.post("/email/incoming", headers=headers, data=data)
        retried = client.post("/email/incoming", headers=headers, data=data)
    assert failed.status_code == 500
    assert retried.status_code == 200
    assert calls["n"] == 2
    assert "email_send_failed error=HTTPStatusError" in caplog.text
    assert _TEXT not in caplog.text
