"""Public URL and Twilio signature check for the SMS webhook."""

from __future__ import annotations

from fastapi import Request
from twilio.request_validator import RequestValidator

from core.config import settings


def public_webhook_url(request: Request) -> str:
    """Absolute URL Twilio signed, including the ngrok host forwarded to us."""
    host = request.headers.get("host", "localhost:8000")
    forwarded = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    if forwarded in ("http", "https"):
        scheme = forwarded
    elif "ngrok" in host or request.url.scheme == "https":
        scheme = "https"
    else:
        scheme = request.url.scheme or "http"
    url = f"{scheme}://{host}{request.url.path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    return url


def form_params(form) -> dict[str, str]:
    """Form fields as strings. The last value wins when a key is repeated."""
    params: dict[str, str] = {}
    for key, value in form.multi_items():
        params[str(key)] = value if isinstance(value, str) else str(value)
    return params


def signature_is_valid(url: str, params: dict[str, str], signature: str) -> bool:
    """True when the header matches Twilio's signature for this URL and form."""
    if not signature or not settings.TWILIO_AUTH_TOKEN:
        return False
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return bool(validator.validate(url, params, signature))
