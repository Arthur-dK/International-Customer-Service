"""Send one plain-text reply through the SendGrid Mail Send API."""

from __future__ import annotations

import asyncio

import httpx

from core.config import settings

_MAIL_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


def reply_subject(subject: str) -> str:
    """Subject of the echo. The body stays the inbound plain text."""
    text = subject.strip()
    if not text:
        return "Re:"
    return f"Re: {text}"


def mail_payload(*, from_email: str, to_email: str, subject: str, body: str) -> dict:
    """JSON body for one Mail Send call."""
    return {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }


def create_message(*, from_email: str, to_email: str, subject: str, body: str) -> None:
    """Place the Mail Send call. ``from_email`` is the address that received the mail."""
    api_key = settings.SENDGRID_API_KEY
    if not api_key:
        raise RuntimeError("SendGrid API key is empty")
    response = httpx.post(
        _MAIL_SEND_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json=mail_payload(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            body=body,
        ),
        timeout=20.0,
    )
    response.raise_for_status()


async def send_email(*, from_email: str, to_email: str, subject: str, body: str) -> None:
    """Run the SendGrid call off the FastAPI event loop."""
    await asyncio.to_thread(
        create_message,
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
    )
