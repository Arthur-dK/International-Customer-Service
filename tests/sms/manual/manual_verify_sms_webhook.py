"""
Manual check: POST /sms/incoming rejects a bad signature and returns empty
TwiML when the signature matches. No SMS is sent.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\sms\\manual\\manual_verify_sms_webhook.py
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

_HOST = "example.ngrok-free.app"
_URL = f"https://{_HOST}/sms/incoming"
_DATA = {
    "MessageSid": "SMmanual",
    "From": "+15550001111",
    "To": "+15550002222",
    "Body": "phase-1-manual",
}


def main() -> int:
    async def fake_send(*, from_: str, to: str, body: str) -> None:
        return None

    sms_api.send_sms = fake_send
    token = settings.TWILIO_AUTH_TOKEN
    signature = RequestValidator(token).compute_signature(_URL, _DATA)
    client = TestClient(app)
    headers = {"host": _HOST, "x-forwarded-proto": "https"}

    missing = client.post("/sms/incoming", headers=headers, data=_DATA)
    signed = client.post(
        "/sms/incoming",
        headers={**headers, "x-twilio-signature": signature},
        data=_DATA,
    )
    forged = client.post(
        "/sms/incoming",
        headers={**headers, "x-twilio-signature": "forged"},
        data=_DATA,
    )

    print("SMS webhook signature verification (manual)")
    print(f"  status missing signature = {missing.status_code}")
    print(f"  status forged signature  = {forged.status_code}")
    print(f"  status valid signature   = {signed.status_code}")
    print("  twiml:")
    print(signed.text)

    checks = {
        "missing_is_403": missing.status_code == 403,
        "forged_is_403": forged.status_code == 403,
        "valid_is_200": signed.status_code == 200,
        "empty_response": "<Response" in signed.text,
        "no_message_verb": "<Message" not in signed.text,
        "body_not_in_twiml": "phase-1-manual" not in signed.text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline SMS signature checks passed.")
    print("This phase does not send an SMS. A live text should get no reply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
