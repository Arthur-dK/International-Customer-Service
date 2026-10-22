"""
Manual check: one French plain-text post is echoed once, the log has a
language code and a score, and a second post of the same Message-ID does
not send again. The HTTP call is replaced, so this script does not send
an email.

Usage (from repo root):
  .\\venv\\Scripts\\python.exe tests\\email\\manual\\manual_verify_email_reply.py
"""

from __future__ import annotations

import base64
import json
import logging
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
from services.email.quota import clear_quota  # noqa: E402

_TEXT = "Bonjour, je voudrais connaitre le solde de ma carte."
_MESSAGE_ID = "<phase-6@mail.example>"
_DATA = {
    "from": "sender@example.com",
    "to": "echo@internationalivr.xyz",
    "subject": "Hello",
    "text": _TEXT,
    "headers": f"Message-ID: {_MESSAGE_ID}\n",
    "envelope": '{"to":["echo@internationalivr.xyz"],"from":"sender@example.com"}',
}


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())


def main() -> int:
    user = settings.SENDGRID_INBOUND_USER
    password = settings.SENDGRID_INBOUND_PASSWORD
    print("Email reply verification (manual, no live send)")
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

    capture = _Capture()
    logger = logging.getLogger("app.api.email")
    logger.addHandler(capture)
    logger.setLevel(logging.INFO)

    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    client = TestClient(app)
    headers = {"authorization": f"Basic {token}"}
    first = client.post("/email/incoming", headers=headers, data=_DATA)
    second = client.post("/email/incoming", headers=headers, data=_DATA)
    logger.removeHandler(capture)

    reply = next((json.loads(line) for line in capture.lines if '"email_reply"' in line), {})
    content = (calls[0].get("content") if calls else [{}])[0].get("value") if calls else None
    log_text = "\n".join(capture.lines)
    print(f"  status first = {first.status_code}")
    print(f"  status second = {second.status_code}")
    print(f"  sends = {len(calls)}")
    print(f"  language = {reply.get('language')!r}")
    print(f"  score = {reply.get('score')!r}")

    checks = {
        "first_200": first.status_code == 200,
        "second_200": second.status_code == 200,
        "one_send": len(calls) == 1,
        "exact_text": content == _TEXT,
        "language_fr": reply.get("language") == "fr",
        "score_is_number": isinstance(reply.get("score"), (int, float)),
        "body_not_in_log": _TEXT not in log_text,
        "duplicate_logged": f"email_duplicate message_id={_MESSAGE_ID}" in log_text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  check[{name}] = {'PASS' if ok else 'FAIL'}")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("All offline email reply checks passed.")
    print("No email was sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
