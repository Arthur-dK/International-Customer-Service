"""Send one SMS through Twilio's Messages API."""

from __future__ import annotations

import asyncio

from twilio.rest import Client

from core.config import settings


def create_message(*, from_: str, to: str, body: str) -> None:
    """Place the Messages API call. ``from_`` is this Twilio number."""
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(from_=from_, to=to, body=body)


async def send_sms(*, from_: str, to: str, body: str) -> None:
    """Run the synchronous Twilio client off the FastAPI event loop."""
    await asyncio.to_thread(create_message, from_=from_, to=to, body=body)
