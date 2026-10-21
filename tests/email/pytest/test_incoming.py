"""Phase 2: POST /email/incoming accepts basic auth and sends no mail."""

import base64

from fastapi.testclient import TestClient

from app.main import app
from core.config import settings

client = TestClient(app)

_USER = "inbound"
_PASSWORD = "phase-two-secret"
_TEXT = "pin-9876 café"
_SUBJECT = "subject-should-stay-out-of-the-log"


def _auth(user: str = _USER, password: str = _PASSWORD) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def _configure(monkeypatch, user: str = _USER, password: str = _PASSWORD) -> None:
    monkeypatch.setattr(settings, "SENDGRID_INBOUND_USER", user)
    monkeypatch.setattr(settings, "SENDGRID_INBOUND_PASSWORD", password)


def _payload() -> dict[str, str]:
    return {
        "from": "Sender Name <sender@example.com>",
        "to": "Echo <echo@inbox.example.com>",
        "subject": _SUBJECT,
        "text": _TEXT,
        "html": "<p>html-should-stay-out-of-the-log</p>",
        "envelope": '{"to":["echo@inbox.example.com"],"from":"sender@example.com"}',
    }


def test_missing_password_is_forbidden(monkeypatch, caplog):
    _configure(monkeypatch)
    with caplog.at_level("INFO"):
        response = client.post("/email/incoming", data=_payload())
    assert response.status_code == 403
    assert response.text == ""
    assert _TEXT not in caplog.text
    assert _SUBJECT not in caplog.text
    assert "auth=invalid" in caplog.text


def test_bad_password_is_forbidden(monkeypatch, caplog):
    _configure(monkeypatch)
    with caplog.at_level("INFO"):
        response = client.post(
            "/email/incoming",
            headers={"authorization": _auth(password="wrong")},
            data=_payload(),
        )
    assert response.status_code == 403
    assert _TEXT not in caplog.text
    assert "auth=invalid" in caplog.text


def test_empty_configured_password_is_forbidden(monkeypatch):
    _configure(monkeypatch, user="", password="")
    response = client.post(
        "/email/incoming",
        headers={"authorization": _auth(user="", password="")},
        data=_payload(),
    )
    assert response.status_code == 403


def test_valid_password_returns_200_and_logs_addresses(monkeypatch, caplog):
    _configure(monkeypatch)
    with caplog.at_level("INFO"):
        response = client.post(
            "/email/incoming",
            headers={"authorization": _auth()},
            data=_payload(),
        )
    assert response.status_code == 200
    assert response.text == ""
    assert "from=sender@example.com" in caplog.text
    assert "to=echo@inbox.example.com" in caplog.text
    assert "text_present=yes" in caplog.text
    assert "auth=valid" in caplog.text
    assert _TEXT not in caplog.text
    assert _SUBJECT not in caplog.text
    assert "html-should-stay-out-of-the-log" not in caplog.text


def test_password_may_contain_a_colon(monkeypatch):
    _configure(monkeypatch, password="a:b")
    response = client.post(
        "/email/incoming",
        headers={"authorization": _auth(password="a:b")},
        data={"text": "hi", "from": "a@b.c", "to": "c@d.e"},
    )
    assert response.status_code == 200


def test_attachment_is_not_logged(monkeypatch, caplog):
    _configure(monkeypatch)
    secret = "attachment-bytes-stay-out"
    with caplog.at_level("INFO"):
        response = client.post(
            "/email/incoming",
            headers={"authorization": _auth()},
            data={"from": "a@b.c", "to": "c@d.e", "text": ""},
            files={"attachment1": ("note.txt", secret.encode(), "text/plain")},
        )
    assert response.status_code == 200
    assert "text_present=no" in caplog.text
    assert secret not in caplog.text
