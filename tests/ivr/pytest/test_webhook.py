from fastapi.testclient import TestClient

from app.main import app
from core.telephony.allowlist import load_allowed_numbers

client = TestClient(app)

_IL = "+972501234567"
_GB = "+442071838750"
_FR = "+33142685300"
_DE = "+493012345678"
_KE = "+254712345678"
_SA = "+966501234567"


def _allow(monkeypatch, *numbers: str) -> None:
    monkeypatch.setattr(
        "core.telephony.allowlist.load_allowed_numbers",
        lambda path=None: frozenset(numbers),
    )


def test_allowlisted_caller_opens_media_stream(monkeypatch):
    _allow(monkeypatch, _IL)
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _IL},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<Stream url=" in response.text
    assert "<Connect>" in response.text
    assert "<Hangup" not in response.text
    assert 'name="from" value="+972501234567"' in response.text
    assert 'name="country_code" value="IL"' in response.text


def test_allowlisted_gb_caller_gets_gb_country_param(monkeypatch):
    _allow(monkeypatch, _GB)
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _GB},
    )
    assert response.status_code == 200
    assert "<Stream url=" in response.text
    assert 'name="country_code" value="GB"' in response.text
    assert 'name="from" value="+442071838750"' in response.text


def test_default_allowlist_file_is_empty():
    assert load_allowed_numbers() == frozenset()


def test_unknown_number_is_rejected_before_the_stream():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _IL},
    )
    assert response.status_code == 200
    assert "<Stream" not in response.text
    assert "<Connect>" not in response.text
    assert '<Pause length="1"></Pause>' in response.text
    assert '<Redirect method="POST">http://localhost:8000/voice/hangup</Redirect>' in response.text
    assert "<Hangup" not in response.text
    assert 'language="he-IL"' in response.text
    assert "המספר הזה אינו מזוהה." in response.text


def test_missing_caller_is_rejected_in_english():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={},
    )
    assert response.status_code == 200
    assert "<Stream" not in response.text
    assert 'language="en-US"' in response.text
    assert "This number is not recognised." in response.text
    assert "/voice/hangup</Redirect>" in response.text


def test_anonymous_caller_is_rejected_in_english():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": "anonymous"},
    )
    assert response.status_code == 200
    assert "<Stream" not in response.text
    assert 'language="en-US"' in response.text
    assert "This number is not recognised." in response.text
    assert "/voice/hangup</Redirect>" in response.text


def test_hangup_document_contains_only_hangup():
    response = client.post("/voice/hangup")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/xml")
    assert "<Hangup></Hangup>" in response.text
    assert "<Say" not in response.text
    assert "<Stream" not in response.text


def test_rejection_redirect_uses_forwarded_https_host():
    response = client.post(
        "/voice/incoming",
        headers={"host": "example.ngrok-free.app", "x-forwarded-proto": "https"},
        data={"From": "anonymous"},
    )
    assert (
        '<Redirect method="POST">https://example.ngrok-free.app/voice/hangup</Redirect>'
        in response.text
    )


def test_french_number_is_rejected_in_french():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _FR},
    )
    assert "<Stream" not in response.text
    assert 'language="fr-FR"' in response.text
    assert "Ce numéro n'est pas reconnu." in response.text


def test_arabic_number_is_rejected_in_arabic():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _SA},
    )
    assert "<Stream" not in response.text
    assert 'language="ar-XA"' in response.text
    assert "هذا الرقم غير معروف." in response.text


def test_allowlisted_number_matches_after_surrounding_spaces(monkeypatch):
    _allow(monkeypatch, _GB)
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": f"  {_GB}  "},
    )
    assert "<Stream url=" in response.text
    assert 'name="from" value="+442071838750"' in response.text


def test_swahili_country_rejection_falls_back_to_english():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _KE},
    )
    assert "<Stream" not in response.text
    assert 'language="en-US"' in response.text
    assert "This number is not recognised." in response.text
    assert "Nambari" not in response.text


def test_unsupported_prompt_language_falls_back_to_english():
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": _DE},
    )
    assert "<Stream" not in response.text
    assert 'language="en-US"' in response.text
    assert "This number is not recognised." in response.text
