"""Keep MessageSid memory from leaking between SMS tests."""

import pytest

from services.sms.dedupe import clear_seen_message_sids


@pytest.fixture(autouse=True)
def _clear_seen_message_sids():
    clear_seen_message_sids()
    yield
    clear_seen_message_sids()
