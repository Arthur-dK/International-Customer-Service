"""Twilio SMS webhook. A valid signature may echo an allowlisted text."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response

from core.language import resolve_caller_locale
from core.telephony.allowlist import is_caller_allowed
from core.telephony.rejection import not_recognised_say
from services.sms.dedupe import already_handled, forget_message_sid, remember_message_sid
from services.sms.outbound import send_sms
from services.sms.signature import form_params, public_webhook_url, signature_is_valid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sms", tags=["sms"])

# Empty on purpose. A <Message> verb would make Twilio send a second text.
EMPTY_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


@router.post("/incoming")
async def sms_incoming(request: Request):
    """
    Twilio Messaging webhook.
    A bad signature is HTTP 403. A valid one returns empty TwiML.
    An allowlisted sender with a non-empty body is echoed through the Messages API.
    Any other non-empty body gets the translated not-recognised line. An empty body sends nothing.
    A repeated MessageSid does not send again. A failed send is forgotten so Twilio can retry.
    """
    form = await request.form()
    params = form_params(form)
    signature = request.headers.get("x-twilio-signature", "")
    url = public_webhook_url(request)
    valid = signature_is_valid(url, params, signature)
    logger.info(
        "sms_incoming from=%s to=%s message_sid=%s signature=%s",
        params.get("From"),
        params.get("To"),
        params.get("MessageSid"),
        "valid" if valid else "invalid",
    )
    if not valid:
        return Response(status_code=403)

    message_sid = params.get("MessageSid")
    if already_handled(message_sid):
        logger.info("sms_duplicate message_sid=%s", message_sid)
        return Response(content=EMPTY_TWIML, media_type="text/xml")

    body = params.get("Body", "")
    sender = params.get("From")
    twilio_number = params.get("To")
    reply = _reply_body(sender, body)
    if reply is not None and sender and twilio_number:
        try:
            await send_sms(from_=twilio_number, to=sender, body=reply)
        except Exception as exc:
            forget_message_sid(message_sid)
            logger.error(
                "sms_send_failed message_sid=%s error=%s",
                message_sid,
                type(exc).__name__,
            )
            return Response(status_code=500)
        remember_message_sid(message_sid)
        logger.info(
            "sms_%s message_sid=%s",
            "echo" if is_caller_allowed(sender) else "reject",
            message_sid,
        )

    return Response(content=EMPTY_TWIML, media_type="text/xml")


def _reply_body(sender: str | None, body: str) -> str | None:
    """Echo, the not-recognised line, or nothing. Pictures are not part of this."""
    if not body or not sender:
        return None
    if is_caller_allowed(sender):
        return body
    _language, text = not_recognised_say(resolve_caller_locale(sender).prompt_language)
    return text
