"""
Manual check: an allowlisted text gets one English placeholder. The Twilio
client is replaced, so this script does not send an SMS.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\sms\\manual\\manual_verify_sms_intent.py
"""

from __future__ import annotations

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
from services.sms.dedupe import clear_seen_message_sids  # noqa: E402
from services.sms.intent import BLOCK_CARD, GET_PIN  # noqa: E402
from services.sms.replies import UNKNOWN_REPLY, reply_for  # noqa: E402

_HOST = "example.ngrok-free.app"
_URL = f"https://{_HOST}/sms/incoming"
_SENDER = "+15550001111"
_TWILIO = "+15550002222"

_CASES = (
    ("pin", "pin", reply_for(GET_PIN)),
    ("two_actions", "block and balance", reply_for(BLOCK_CARD)),
    ("unrelated", "what time is it", UNKNOWN_REPLY),
)


def main() -> int:
    clear_seen_message_sids()
    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        sent.append((from_, to, body))

    sms_api.send_sms = fake_send
    sms_api.is_caller_allowed = lambda number: number == _SENDER

    client = TestClient(app)
    print("SMS intent verification (manual, no live send)")
    print(f"  from_number = {_SENDER!r}")

    failed: list[str] = []
    for name, body, expected in _CASES:
        before = len(sent)
        data = {
            "MessageSid": f"SMintent-{name}",
            "From": _SENDER,
            "To": _TWILIO,
            "Body": body,
        }
        signature = RequestValidator(settings.TWILIO_AUTH_TOKEN).compute_signature(_URL, data)
        response = client.post(
            "/sms/incoming",
            headers={
                "host": _HOST,
                "x-forwarded-proto": "https",
                "x-twilio-signature": signature,
            },
            data=data,
        )
        delivered = sent[before:]
        ok = (
            response.status_code == 200
            and "<Message" not in response.text
            and body not in response.text
            and delivered == [(_TWILIO, _SENDER, expected)]
        )
        if not ok:
            failed.append(name)
        print(f"  {name} = {'PASS' if ok else 'FAIL'}")
        print(f"    inbound = {body!r}")
        print(f"    reply = {delivered[0][2]!r}" if delivered else "    reply = (none)")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline SMS intent checks passed.")
    print("A live text of pin from the allowlisted handset should receive the PIN placeholder once.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
