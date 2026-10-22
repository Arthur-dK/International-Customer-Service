"""
Manual check: POST /email/incoming rejects a bad password and returns 200
when the password matches. No email is sent.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\email\\manual\\manual_verify_email_webhook.py
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from core.config import settings  # noqa: E402

_DATA = {
    "from": "sender@example.com",
    "to": "echo@inbox.example.com",
    "subject": "manual",
    "text": "phase-2-manual",
    "envelope": '{"to":["echo@inbox.example.com"],"from":"sender@example.com"}',
}


def _header(user: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"authorization": f"Basic {token}"}


def main() -> int:
    user = settings.SENDGRID_INBOUND_USER
    password = settings.SENDGRID_INBOUND_PASSWORD
    print("Email webhook basic-auth verification (manual)")
    if not user or not password:
        print("FAILED: set SENDGRID_INBOUND_USER and SENDGRID_INBOUND_PASSWORD in .env")
        return 1

    client = TestClient(app)
    missing = client.post("/email/incoming", data=_DATA)
    wrong = client.post(
        "/email/incoming",
        headers=_header(user, "not-the-password"),
        data=_DATA,
    )
    valid = client.post("/email/incoming", headers=_header(user, password), data=_DATA)

    print(f"  status missing password = {missing.status_code}")
    print(f"  status wrong password   = {wrong.status_code}")
    print(f"  status valid password   = {valid.status_code}")

    checks = {
        "missing_is_403": missing.status_code == 403,
        "wrong_is_403": wrong.status_code == 403,
        "valid_is_200": valid.status_code == 200,
        "empty_body": valid.text == "",
        "text_not_in_response": "phase-2-manual" not in valid.text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")

    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1

    print("All offline email webhook checks passed.")
    print("No email was sent. A live reply is a later phase.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
