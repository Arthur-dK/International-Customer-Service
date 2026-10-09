"""
Manual check: an allowlisted non-empty body is handed to the Messages API
once, and the webhook still returns empty TwiML. The Twilio client is replaced
so this script does not send an SMS.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\sms\\manual\\manual_verify_sms_echo.py
  .\\venv\\Scripts\\python.exe tests\\sms\\manual\\manual_verify_sms_echo.py --from-number +15550001111
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from twilio.request_validator import RequestValidator  # noqa: E402

from app.api import sms as sms_api  # noqa: E402
from app.main import app  # noqa: E402
from core.config import settings  # noqa: E402
from core.telephony.allowlist import load_allowed_numbers  # noqa: E402

_HOST = "example.ngrok-free.app"
_URL = f"https://{_HOST}/sms/incoming"
_TWILIO = "+15550002222"
_BODY = "phase-2-manual"


async def _capture(*, from_: str, to: str, body: str, sent: list) -> None:
    sent.append((from_, to, body))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the SMS echo without sending.")
    parser.add_argument("--from-number", default="")
    args = parser.parse_args()
    allowed = load_allowed_numbers()
    sender = args.from_number.strip() or (sorted(allowed)[0] if allowed else "")

    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        await _capture(from_=from_, to=to, body=body, sent=sent)

    sms_api.send_sms = fake_send

    data = {"MessageSid": "SMecho", "From": sender, "To": _TWILIO, "Body": _BODY}
    signature = RequestValidator(settings.TWILIO_AUTH_TOKEN).compute_signature(_URL, data)
    client = TestClient(app)
    response = client.post(
        "/sms/incoming",
        headers={
            "host": _HOST,
            "x-forwarded-proto": "https",
            "x-twilio-signature": signature,
        },
        data=data,
    )

    print("SMS echo verification (manual, no live send)")
    print(f"  from_number = {sender!r}")
    print(f"  on_allowlist = {sender in allowed}")
    print(f"  status = {response.status_code}")
    print("  twiml:")
    print(response.text)
    print(f"  sent = {sent!r}")

    on_list = sender in allowed
    checks = {
        "has_sender": bool(sender),
        "http_200": response.status_code == 200,
        "empty_response": "<Response" in response.text,
        "no_message_verb": "<Message" not in response.text,
        "body_not_in_twiml": _BODY not in response.text,
        "echoed_once": sent == [(_TWILIO, sender, _BODY)] if on_list else sent == [],
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline SMS echo checks passed.")
    if on_list:
        print("A live text from this number should come back as the same characters.")
    else:
        print("This number is not allowlisted, so a live text still gets no reply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
