import pytest

from core.config import settings
from services.ivr.force_hangup import (
    complete_call,
    rejection_hangup_delay_s,
    schedule_rejection_hangup,
)
from services.ivr.twiml import REJECTION_HANGUP_PAUSE_S


def test_rejection_hangup_delay_includes_one_second_after_speech():
    delay = rejection_hangup_delay_s("This number is not recognised.")
    assert delay >= REJECTION_HANGUP_PAUSE_S + 2.5
    assert delay == pytest.approx(5 * 0.6 + REJECTION_HANGUP_PAUSE_S)


def test_schedule_rejection_hangup_skips_mock_credentials(monkeypatch):
    created: list[object] = []
    monkeypatch.setattr(
        "services.ivr.force_hangup.asyncio.create_task",
        lambda coro: created.append(coro) or coro.close(),
    )
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "mock_sid")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "mock_token")
    schedule_rejection_hangup("CA123", "This number is not recognised.")
    assert created == []


@pytest.mark.asyncio
async def test_complete_call_posts_completed_status(monkeypatch):
    posted: dict[str, object] = {}

    class _Response:
        status_code = 200

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, data, auth, timeout):
            posted["url"] = url
            posted["data"] = data
            posted["auth"] = auth
            posted["timeout"] = timeout
            return _Response()

    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setattr("services.ivr.force_hangup.httpx.AsyncClient", _Client)

    status = await complete_call("CA123")
    assert status == 200
    assert posted["data"] == {"Status": "completed"}
    assert posted["auth"] == ("AC_test", "token")
    assert str(posted["url"]).endswith("/Accounts/AC_test/Calls/CA123.json")
