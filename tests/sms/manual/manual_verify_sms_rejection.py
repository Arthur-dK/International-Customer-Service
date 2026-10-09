"""
Manual check: a number that is not allowlisted gets the not-recognised SMS,
and an empty body sends nothing. The Twilio client is replaced, so this
script does not send an SMS.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\sms\\manual\\manual_verify_sms_rejection.py
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
from core.telephony.allowlist import is_caller_allowed  # noqa: E402

_HOST = "example.ngrok-free.app"
_URL = f"https://{_HOST}/sms/incoming"
_TWILIO = "+15550002222"
_FRENCH = "+33142685300"
_LINE = "Ce numéro n'est pas reconnu."


def main() -> int:
    sent: list[tuple[str, str, str]] = []

    async def fake_send(*, from_: str, to: str, body: str) -> None:
        sent.append((from_, to, body))

    sms_api.send_sms = fake_send
    client = TestClient(app)
    token = settings.TWILIO_AUTH_TOKEN

    def post(data: dict[str, str]):
        signature = RequestValidator(token).compute_signature(_URL, data)
        return client.post(
            "/sms/incoming",
            headers={
                "host": _HOST,
                "x-forwarded-proto": "https",
                "x-twilio-signature": signature,
            },
            data=data,
        )

    text = post(
        {"MessageSid": "SMreject", "From": _FRENCH, "To": _TWILIO, "Body": "bonjour"}
    )
    empty = post({"MessageSid": "SMempty", "From": _FRENCH, "To": _TWILIO, "Body": ""})

    print("SMS rejection verification (manual, no live send)")
    print(f"  french_allowed = {is_caller_allowed(_FRENCH)}")
    print(f"  text status = {text.status_code}")
    print(f"  empty status = {empty.status_code}")
    print(f"  sent = {sent!r}")

    checks = {
        "french_not_allowlisted": not is_caller_allowed(_FRENCH),
        "text_200": text.status_code == 200,
        "empty_200": empty.status_code == 200,
        "no_message_verb": "<Message" not in text.text,
        "french_line": sent == [(_TWILIO, _FRENCH, _LINE)],
        "inbound_not_sent": all(body != "bonjour" for _from, _to, body in sent),
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline SMS rejection checks passed.")
    print("A live text from a number that is not allowlisted should get that line, not an echo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
