"""
Manual check: a password-checked email gets one English placeholder. The
Mail Send call is replaced, so this script does not send an email.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\email\\manual\\manual_verify_email_intent.py
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from core.config import settings  # noqa: E402
from services.email import outbound  # noqa: E402
from services.email.dedupe import clear_seen_messages  # noqa: E402
from services.email.intent import GET_PIN  # noqa: E402
from services.email.quota import clear_quota  # noqa: E402
from services.email.replies import UNKNOWN_REPLY, reply_for  # noqa: E402

_RECIPIENT = "intent@internationalivr.xyz"
_SENDER = "sender@example.com"

_CASES = (
    ("pin", "pin", reply_for(GET_PIN)),
    ("two_actions", "block and balance", UNKNOWN_REPLY),
    ("unrelated", "what time is it", UNKNOWN_REPLY),
)


def _payload(name: str, text: str) -> dict[str, str]:
    return {
        "from": _SENDER,
        "to": _RECIPIENT,
        "subject": "Hello",
        "text": text,
        "headers": f"Message-ID: <phase-4-{name}@mail.example>\n",
        "envelope": f'{{"to":["{_RECIPIENT}"],"from":"{_SENDER}"}}',
    }


def main() -> int:
    user = settings.SENDGRID_INBOUND_USER
    password = settings.SENDGRID_INBOUND_PASSWORD
    print("Email intent verification (manual, no live send)")
    if not user or not password:
        print("FAILED: set SENDGRID_INBOUND_USER and SENDGRID_INBOUND_PASSWORD in .env")
        return 1

    calls: list[dict] = []

    def fake_post(url, *, headers, json, timeout):
        calls.append(json)
        return httpx.Response(202, request=httpx.Request("POST", url))

    outbound.httpx.post = fake_post
    settings.SENDGRID_API_KEY = settings.SENDGRID_API_KEY or "manual-test-key"
    clear_quota()
    clear_seen_messages()

    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    client = TestClient(app)
    headers = {"authorization": f"Basic {token}"}

    failed: list[str] = []
    for name, text, expected in _CASES:
        before = len(calls)
        response = client.post("/email/incoming", headers=headers, data=_payload(name, text))
        delivered = calls[before:]
        content = None
        if delivered:
            content = (delivered[0].get("content") or [{}])[0].get("value")
        ok = (
            response.status_code == 200
            and text not in response.text
            and len(delivered) == 1
            and delivered[0].get("from") == {"email": _RECIPIENT}
            and delivered[0].get("personalizations") == [{"to": [{"email": _SENDER}]}]
            and delivered[0].get("subject") == "Re: Hello"
            and content == expected
        )
        if not ok:
            failed.append(name)
        print(f"  {name} = {'PASS' if ok else 'FAIL'}")
        print(f"    inbound = {text!r}")
        print(f"    reply = {content!r}")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline email intent checks passed.")
    print("A live email of pin to the inbound address should receive the PIN placeholder once.")
    print("No email was sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
