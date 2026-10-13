"""Twilio SMS webhook. A valid signature may answer an allowlisted text."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response

from core.language import resolve_caller_locale
from core.telephony.allowlist import is_caller_allowed
from core.telephony.rejection import not_recognised_say
from services.sms.dedupe import already_handled, forget_message_sid, remember_message_sid
from services.sms.intent import match_intent
from services.sms.language import detect_language
from services.sms.outbound import send_sms
from services.sms.replies import reply_for
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
    An allowlisted sender with a non-empty body gets one English placeholder.
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
    reply, language, score, intent = _reply_body(sender, body)
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
        if language is None:
            logger.info("sms_reject message_sid=%s", message_sid)
        else:
            logger.info(
                json.dumps(
                    {
                        "event": "sms_reply",
                        "message_sid": message_sid,
                        "language": language,
                        "score": None if score is None else float(score),
                        "intent": intent or "none",
                    }
                )
            )

    return Response(content=EMPTY_TWIML, media_type="text/xml")


def _reply_body(
    sender: str | None, body: str
) -> tuple[str | None, str | None, float | None, str | None]:
    """Placeholder, the not-recognised line, or nothing.

    An allowlisted non-empty body also returns the detected language, its
    score, and the intent id. Those three are None for a rejection or when
    nothing is sent. The body is not logged. Pictures are not part of this.
    """
    if not body or not sender:
        return None, None, None, None
    if is_caller_allowed(sender):
        intent = match_intent(body)
        language, score = detect_language(body)
        return reply_for(intent), language, score, intent
    _language, text = not_recognised_say(resolve_caller_locale(sender).prompt_language)
    return text, None, None, None
