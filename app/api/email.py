"""SendGrid Inbound Parse webhook. A valid password may send one English placeholder."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response

from services.email.auth import basic_auth_is_valid
from services.email.dedupe import already_handled, delivery_key, forget_message, remember_message
from services.email.inbound import form_params, parse_inbound
from services.email.intent import match_intent
from services.email.outbound import reply_subject, send_email
from services.email.quota import release, try_reserve
from services.email.replies import reply_for
from services.language import detect_language

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/incoming")
async def email_incoming(request: Request):
    """
    SendGrid Inbound Parse.
    A missing or wrong basic-auth password is HTTP 403.
    A valid post with plain text sends one English placeholder, from the inbound recipient.
    An empty body, a missing address, or a full daily cap returns 200 and sends nothing.
    A repeated message does not send again. A failed send returns 500 and can be retried.
    The language code, the score, and the intent id are logged. The plain-text body and the subject are not logged.
    """
    form = await request.form()
    params = form_params(form)
    incoming = parse_inbound(params)
    valid = basic_auth_is_valid(request.headers.get("authorization"))
    logger.info(
        "email_incoming from=%s to=%s text_present=%s auth=%s",
        incoming.sender,
        incoming.recipient,
        "yes" if incoming.text_present else "no",
        "valid" if valid else "invalid",
    )
    if not valid:
        return Response(status_code=403)
    if not incoming.text_present or not incoming.sender or not incoming.recipient:
        return Response(status_code=200)
    message_key = delivery_key(
        incoming.message_id, incoming.sender, incoming.recipient, incoming.text
    )
    if already_handled(message_key):
        logger.info("email_duplicate message_id=%s", message_key)
        return Response(status_code=200)
    language, score = detect_language(incoming.text)
    intent = match_intent(incoming.text)
    if not try_reserve():
        logger.info("email_cap_reached to=%s", incoming.recipient)
        return Response(status_code=200)
    try:
        await send_email(
            from_email=incoming.recipient,
            to_email=incoming.sender,
            subject=reply_subject(incoming.subject),
            body=reply_for(intent),
        )
    except Exception as exc:
        release()
        forget_message(message_key)
        logger.error("email_send_failed error=%s", type(exc).__name__)
        return Response(status_code=500)
    remember_message(message_key)
    logger.info(
        json.dumps(
            {
                "event": "email_reply",
                "from": incoming.recipient,
                "to": incoming.sender,
                "language": language,
                "score": score,
                "intent": intent or "none",
            }
        )
    )
    return Response(status_code=200)
