"""A plain-text email gets one English placeholder through Mail Send."""

import base64

import httpx
from fastapi.testclient import TestClient

from app.main import app
from core.config import settings
from services.email.quota import clear_quota
from services.email.replies import UNKNOWN_REPLY, reply_for
from services.email.intent import GET_PIN

client = TestClient(app)

_USER = "inbound"
_PASSWORD = "phase-three-secret"
_TEXT = "pin-9876 café"
_SUBJECT = "Hello there"


def _auth() -> str:
    token = base64.b64encode(f"{_USER}:{_PASSWORD}".encode()).decode()
    return f"Basic {token}"


def _configure(monkeypatch, cap: int = 20) -> None:
    monkeypatch.setattr(settings, "SENDGRID_INBOUND_USER", _USER)
    monkeypatch.setattr(settings, "SENDGRID_INBOUND_PASSWORD", _PASSWORD)
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "test-key")
    monkeypatch.setattr(settings, "EMAIL_DAILY_SEND_CAP", cap)
    clear_quota()


def _payload(**overrides: str) -> dict[str, str]:
    data = {
        "from": "Sender Name <sender@example.com>",
        "to": "Echo <echo@internationalivr.xyz>",
        "subject": _SUBJECT,
        "text": _TEXT,
        "html": "<p>html-only-should-not-be-the-body</p>",
        "envelope": '{"to":["echo@internationalivr.xyz"],"from":"sender@example.com"}',
    }
    data.update(overrides)
    return data


def _capture(monkeypatch) -> list[dict]:
    calls: list[dict] = []

    def fake_post(url, *, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return httpx.Response(202, request=httpx.Request("POST", url))

    monkeypatch.setattr("services.email.outbound.httpx.post", fake_post)
    return calls


def test_pin_gets_the_placeholder(monkeypatch, caplog):
    _configure(monkeypatch)
    calls = _capture(monkeypatch)
    with caplog.at_level("INFO"):
        response = client.post(
            "/email/incoming",
            headers={"authorization": _auth()},
            data=_payload(),
        )
    assert response.status_code == 200
    assert len(calls) == 1
    message = calls[0]["json"]
    pin_line = reply_for(GET_PIN)
    assert message["from"] == {"email": "echo@internationalivr.xyz"}
    assert message["personalizations"] == [{"to": [{"email": "sender@example.com"}]}]
    assert message["subject"] == "Re: Hello there"
    assert message["content"] == [{"type": "text/plain", "value": pin_line}]
    assert "9876" not in pin_line
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0]["url"] == "https://api.sendgrid.com/v3/mail/send"
    assert '"event": "email_reply"' in caplog.text
    assert '"from": "echo@internationalivr.xyz"' in caplog.text
    assert '"to": "sender@example.com"' in caplog.text
    assert '"intent": "get_pin"' in caplog.text
    assert '"score":' in caplog.text
    assert _TEXT not in caplog.text
    assert _SUBJECT not in caplog.text


def test_two_actions_get_the_unknown_line(monkeypatch, caplog):
    inbound = "block and balance"
    _configure(monkeypatch)
    calls = _capture(monkeypatch)
    with caplog.at_level("INFO"):
        response = client.post(
            "/email/incoming",
            headers={"authorization": _auth()},
            data=_payload(text=inbound),
        )
    assert response.status_code == 200
    assert calls[0]["json"]["content"] == [{"type": "text/plain", "value": UNKNOWN_REPLY}]
    assert '"intent": "none"' in caplog.text
    assert inbound not in caplog.text


def test_french_reply_logs_french_and_sends_the_unknown_line(monkeypatch, caplog):
    french = "Bonjour, je voudrais connaitre le solde de ma carte."
    _configure(monkeypatch)
    calls = _capture(monkeypatch)
    with caplog.at_level("INFO"):
        response = client.post(
            "/email/incoming",
            headers={"authorization": _auth()},
            data=_payload(text=french),
        )
    assert response.status_code == 200
    assert calls[0]["json"]["content"] == [{"type": "text/plain", "value": UNKNOWN_REPLY}]
    assert '"language": "fr"' in caplog.text
    assert '"language": "en"' not in caplog.text
    assert '"intent": "none"' in caplog.text
    assert french not in caplog.text


def test_empty_text_does_not_send(monkeypatch):
    _configure(monkeypatch)
    calls = _capture(monkeypatch)
    response = client.post(
        "/email/incoming",
        headers={"authorization": _auth()},
        data=_payload(text="  "),
    )
    assert response.status_code == 200
    assert calls == []


def test_daily_cap_skips_the_second_send(monkeypatch, caplog):
    _configure(monkeypatch, cap=1)
    calls = _capture(monkeypatch)
    headers = {"authorization": _auth()}
    first = client.post(
        "/email/incoming",
        headers=headers,
        data=_payload(headers="Message-ID: <one@mail.example>\n"),
    )
    with caplog.at_level("INFO"):
        second = client.post(
            "/email/incoming",
            headers=headers,
            data=_payload(headers="Message-ID: <two@mail.example>\n"),
        )
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(calls) == 1
    assert "email_cap_reached" in caplog.text


def test_failed_send_returns_500_and_releases_the_cap(monkeypatch):
    _configure(monkeypatch, cap=1)

    def fail_post(url, *, headers, json, timeout):
        return httpx.Response(401, request=httpx.Request("POST", url))

    monkeypatch.setattr("services.email.outbound.httpx.post", fail_post)
    headers = {"authorization": _auth()}
    failed = client.post("/email/incoming", headers=headers, data=_payload())
    assert failed.status_code == 500

    calls = _capture(monkeypatch)
    retried = client.post("/email/incoming", headers=headers, data=_payload())
    assert retried.status_code == 200
    assert len(calls) == 1
