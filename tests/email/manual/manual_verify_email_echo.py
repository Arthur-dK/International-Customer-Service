"""
Manual check: a plain-text post is handed to Mail Send once. The HTTP call is
replaced, so this script does not send an email.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\email\\manual\\manual_verify_email_echo.py
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
from services.email.quota import clear_quota  # noqa: E402

_TEXT = "phase-3-manual"
_DATA = {
    "from": "sender@example.com",
    "to": "echo@internationalivr.xyz",
    "subject": "Hello",
    "text": _TEXT,
    "envelope": '{"to":["echo@internationalivr.xyz"],"from":"sender@example.com"}',
}


def main() -> int:
    user = settings.SENDGRID_INBOUND_USER
    password = settings.SENDGRID_INBOUND_PASSWORD
    print("Email echo verification (manual, no live send)")
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

    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    response = TestClient(app).post(
        "/email/incoming",
        headers={"authorization": f"Basic {token}"},
        data=_DATA,
    )
    message = calls[0] if calls else {}
    content = (message.get("content") or [{}])[0].get("value")
    print(f"  status = {response.status_code}")
    print(f"  sends = {len(calls)}")
    print(f"  from = {message.get('from')!r}")
    print(f"  to = {message.get('personalizations')!r}")

    checks = {
        "http_200": response.status_code == 200,
        "one_send": len(calls) == 1,
        "from_recipient": message.get("from") == {"email": "echo@internationalivr.xyz"},
        "to_sender": message.get("personalizations") == [
            {"to": [{"email": "sender@example.com"}]}
        ],
        "exact_text": content == _TEXT,
        "text_not_in_response": _TEXT not in response.text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("All offline email echo checks passed.")
    print("No email was sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
