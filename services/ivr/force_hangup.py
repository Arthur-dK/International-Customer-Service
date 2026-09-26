"""End a rejected call from Twilio's API if TwiML <Hangup> leaves it open."""

from __future__ import annotations

import asyncio
import logging

import httpx

from core.config import settings
from services.ivr.twiml import REJECTION_HANGUP_PAUSE_S

logger = logging.getLogger(__name__)

# Keep strong references. asyncio only holds tasks weakly, so an unstored
# task can be garbage-collected before the hangup request is sent.
_PENDING_HANGUPS: set[asyncio.Task[None]] = set()

# Phone TTS is slower than conversational speech. This keeps the API hangup
# from cutting off the last word; TwiML still pauses exactly one second.
_SECONDS_PER_WORD = 0.6
_MINIMUM_SPEECH_S = 2.5


def rejection_hangup_delay_s(spoken_text: str) -> float:
    """Seconds from the webhook response until one second after the line."""
    words = max(1, len(spoken_text.split()))
    spoken_s = max(_MINIMUM_SPEECH_S, words * _SECONDS_PER_WORD)
    return spoken_s + REJECTION_HANGUP_PAUSE_S


def schedule_rejection_hangup(call_sid: str | None, spoken_text: str) -> None:
    """Ask Twilio to complete the call after the rejection line and a one-second pause."""
    if not call_sid or not _live_twilio_credentials():
        logger.info("rejection_force_hangup skipped call_sid=%s", call_sid or "missing")
        return
    delay_s = rejection_hangup_delay_s(spoken_text)
    task = asyncio.create_task(_complete_call_after(call_sid, delay_s))
    _PENDING_HANGUPS.add(task)
    task.add_done_callback(_PENDING_HANGUPS.discard)


def _live_twilio_credentials() -> bool:
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    return sid not in ("", "mock_sid") and token not in ("", "mock_token")


async def _complete_call_after(call_sid: str, delay_s: float) -> None:
    try:
        await asyncio.sleep(delay_s)
        await complete_call(call_sid)
    except Exception:
        logger.exception("rejection force hangup failed call_sid=%s", call_sid)


async def complete_call(call_sid: str) -> int:
    """Set the live call to completed. Returns the Twilio HTTP status."""
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls/{call_sid}.json"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            data={"Status": "completed"},
            auth=(sid, token),
            timeout=10.0,
        )
    logger.info(
        "rejection_force_hangup call_sid=%s http=%s",
        call_sid,
        response.status_code,
    )
    return response.status_code
