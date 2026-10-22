"""Keep email tests off the live Mail Send API."""

import httpx
import pytest

from core.config import settings
from services.email.dedupe import clear_seen_messages
from services.email.quota import clear_quota


@pytest.fixture(autouse=True)
def _clear_email_quota():
    clear_quota()
    clear_seen_messages()
    yield
    clear_quota()
    clear_seen_messages()


@pytest.fixture(autouse=True)
def _no_live_mail(monkeypatch):
    """A test that needs a specific response replaces this stub."""

    def fake_post(url, *, headers, json, timeout):
        return httpx.Response(202, request=httpx.Request("POST", url))

    monkeypatch.setattr("services.email.outbound.httpx.post", fake_post)
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "test-key")
