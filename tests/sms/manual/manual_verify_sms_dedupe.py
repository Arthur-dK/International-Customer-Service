"""
Manual check: two signed posts with one MessageSid send once. The Twilio
client is replaced, so this script does not send an SMS.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\sms\\manual\\manual_verify_sms_dedupe.py
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
from core.telephony.allowlist import load_allowed_numbers  # noqa: E402
from services.sms.dedupe import clear_seen_message_sids  # noqa: E402

_HOST = "example.ngrok-free.app"
_URL = f"https://{_HOST}/sms/incoming"
_TWILIO = "+15550002222"
_BODY = "phase-4-manual"


def main() -> int:
    allowed = load_allowed_numbers()
    sender = sorted(allowed)[0] if allowed else ""
    clear_seen_message_sids()
    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        sent.append((from_, to, body))

    sms_api.send_sms = fake_send
    data = {"MessageSid": "SMdedupe", "From": sender, "To": _TWILIO, "Body": _BODY}
    signature = RequestValidator(settings.TWILIO_AUTH_TOKEN).compute_signature(_URL, data)
    client = TestClient(app)
    headers = {
        "host": _HOST,
        "x-forwarded-proto": "https",
        "x-twilio-signature": signature,
    }
    first = client.post("/sms/incoming", headers=headers, data=data)
    second = client.post("/sms/incoming", headers=headers, data=data)

    print("SMS retry dedupe verification (manual, no live send)")
    print(f"  from_number = {sender!r}")
    print(f"  first status = {first.status_code}")
    print(f"  second status = {second.status_code}")
    print(f"  sent_count = {len(sent)}")

    checks = {
        "has_sender": bool(sender),
        "sender_allowlisted": sender in allowed,
        "both_200": first.status_code == 200 and second.status_code == 200,
        "no_message_verb": "<Message" not in first.text and "<Message" not in second.text,
        "sent_once": sent == [(_TWILIO, sender, _BODY)],
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline SMS dedupe checks passed.")
    print("A Twilio retry of the same message should not produce a second text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
