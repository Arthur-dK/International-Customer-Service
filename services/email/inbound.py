"""Fields taken from one SendGrid Inbound Parse post."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_MESSAGE_ID = re.compile(r"(?im)^message-id:\s*(\S+)")


@dataclass(frozen=True)
class InboundEmail:
    """Sender, recipient, subject, and plain-text body. HTML is ignored."""

    sender: str
    recipient: str
    subject: str
    text: str
    message_id: str

    @property
    def text_present(self) -> bool:
        return bool(self.text.strip())


def form_params(form) -> dict[str, str]:
    """String fields only. File uploads are left unread."""
    params: dict[str, str] = {}
    for key, value in form.multi_items():
        if isinstance(value, str):
            params[str(key)] = value
    return params


def parse_inbound(params: dict[str, str]) -> InboundEmail:
    """Prefer the SMTP envelope. Fall back to the bare address in the headers."""
    envelope_from, envelope_to = _envelope(params.get("envelope", ""))
    sender = envelope_from or _bare_address(params.get("from", ""))
    recipient = envelope_to or _bare_address(params.get("to", ""))
    return InboundEmail(
        sender=sender,
        recipient=recipient,
        subject=params.get("subject", ""),
        text=params.get("text", ""),
        message_id=message_id_from_headers(params.get("headers", "")),
    )


def message_id_from_headers(headers: str) -> str:
    """The first Message-ID value, or an empty string when the headers omit it."""
    match = _MESSAGE_ID.search(headers or "")
    if not match:
        return ""
    return match.group(1).strip()


def _envelope(raw: str) -> tuple[str, str]:
    if not raw.strip():
        return "", ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    sender = payload.get("from")
    recipients = payload.get("to")
    recipient = ""
    if isinstance(recipients, list) and recipients:
        first = recipients[0]
        if isinstance(first, str):
            recipient = _bare_address(first)
    if not isinstance(sender, str):
        sender = ""
    return _bare_address(sender), recipient


def _bare_address(value: str) -> str:
    text = value.strip()
    if "<" in text and text.endswith(">"):
        text = text.rsplit("<", 1)[1][:-1].strip()
    return text
