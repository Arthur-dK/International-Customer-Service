# FEAT-05 — SMS echo on the Twilio number

| | |
|---|---|
| **Feature ID** | FEAT-05 |
| **Name** | Signed SMS webhook, then an exact echo |
| **Branch** | `feat/sms-twilio-setup` |
| **Status** | Phases 1–4 implemented. |
| **Target** | A text to the existing Twilio number is answered with the same characters, after the sender is allowlisted |

Voice stays on [FEAT-04](FEAT-04.md). Decisions for this feature are [ADR-027](../adr/ADR-027.md) through [ADR-030](../adr/ADR-030.md).

---

## User experience

When this feature is finished, a person texts the same Twilio number used for calls. If their number is on the voice allowlist and the text has characters, they receive those same characters. If their number is not on the list, they receive the same “not recognised” line the phone call would speak, in that country’s language when a translation exists. A text with no characters gets no reply. Pictures are ignored.

A text from a number on the voice allowlist comes back as the same characters. Any other number with characters gets the not-recognised line for that country’s language: French, Hebrew, or Arabic when that is the prompt language, and English otherwise. An empty text gets no reply. A picture with no caption gets no reply.

A repeated delivery of the same Twilio message does not send a second text. If the Messages API call fails, that message is forgotten and a later delivery can send.

### Try this (Phase 4)

- Pytest, from the repo root: `.\venv\Scripts\python.exe -m pytest tests/sms/pytest -q`
- Offline dedupe check (no SMS is sent): `.\venv\Scripts\python.exe tests\sms\manual\manual_verify_sms_dedupe.py`
- It prints PASS when two posts with the same `MessageSid` would send once.
- Live: text the Twilio number once from the allowlisted handset. One reply comes back. Twilio’s own retry of that same inbound message does not add a second reply.

---

## Phases

Each phase has its own tests. Do not start the next phase until the current one is green.

### Phase 1 — Signed acknowledgement

- **Goal:** Twilio can POST to `/sms/incoming`. A valid signature gets HTTP 200 and an empty `<Response/>`. A missing or invalid signature gets HTTP 403. No SMS is sent.
- **Delivered:** `services/sms/signature.py`; `POST /sms/incoming` in [`app/api/sms.py`](../../../app/api/sms.py); the `twilio` package; [ADR-029](../adr/ADR-029.md). Logs may include `From`, `To`, and `MessageSid`, and must not include `Body`.
- **Tests:** `tests/sms/pytest/test_signature.py`. Manual: `tests/sms/manual/manual_verify_sms_webhook.py`.
- **Done when:** a signature over `https://<host>/sms/incoming` plus the form fields returns empty TwiML; the same fields signed as `http://` are rejected; the body string is absent from the log and from the response.

### Phase 2 — Exact echo

- **Goal:** An allowlisted sender with a non-empty body receives that body back through the Messages API. The webhook still returns empty TwiML so Twilio does not send a second copy.
- **Delivered:** `services/sms/outbound.py`; the echo call in [`app/api/sms.py`](../../../app/api/sms.py); [ADR-027](../adr/ADR-027.md). A failed Messages API call returns HTTP 500. The body is not logged.
- **Tests:** `tests/sms/pytest/test_echo.py`. Manual: `tests/sms/manual/manual_verify_sms_echo.py`.
- **Done when:** the mocked client is called once with that exact body, `from_` equal to the inbound `To`, and `to` equal to the inbound `From`.

### Phase 3 — Rejection and silence

- **Goal:** A non-empty body from any other number gets one translated “not recognised” SMS. An empty body sends nothing. Pictures are ignored.
- **Delivered:** `_reply_body` in [`app/api/sms.py`](../../../app/api/sms.py), using `not_recognised_say` and the voice allowlist; [ADR-028](../adr/ADR-028.md).
- **Tests:** `tests/sms/pytest/test_rejection.py`. Manual: `tests/sms/manual/manual_verify_sms_rejection.py`.
- **Done when:** an unknown French number gets “Ce numéro n'est pas reconnu.” and not the inbound body; `Body` of `""` does not call the client; a body of spaces still follows the allowlist.

### Phase 4 — Retry dedupe

- **Goal:** A second POST with the same `MessageSid` does not send again. A failed Messages API call returns HTTP 500 and forgets that sid so Twilio can retry.
- **Delivered:** `services/sms/dedupe.py`; the sid check in [`app/api/sms.py`](../../../app/api/sms.py); [ADR-030](../adr/ADR-030.md).
- **Tests:** `tests/sms/pytest/test_dedupe.py`. Manual: `tests/sms/manual/manual_verify_sms_dedupe.py`.
- **Done when:** two valid posts of one sid call the client once; a failed create returns 500, and a later post of that sid can send.

---

## Console steps for a live Phase 1 check

The number already used for voice must have SMS enabled. Leave “A call comes in” on `/voice/incoming`.

1. Run the app: `.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Expose HTTPS (ngrok or the existing tunnel) to port 8000.
3. Twilio Console → the phone number → Messaging → “A message comes in” → Webhook, HTTP POST, `https://<public-host>/sms/incoming`.
4. `TWILIO_AUTH_TOKEN` in `.env` must be that account’s auth token. The signature check uses it.
5. Text the number from the allowlisted handset. The phone should receive the same characters. Text it from a handset that is not on the list. That phone should receive the not-recognised line and not the original text.
6. From another terminal, POST the same public URL with no signature header. The status is 403.

```powershell
curl.exe -X POST "https://<public-host>/sms/incoming" -d "From=+15550001111&To=+15550002222&Body=hi&MessageSid=SMcurl"
```

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-027](../adr/ADR-027.md) | Echo SMS through the Messages API | Phase 2 |
| [ADR-028](../adr/ADR-028.md) | Same allowlist, translated rejection, empty body stays silent | Phase 3 |
| [ADR-029](../adr/ADR-029.md) | Reject unsigned SMS webhook posts | Phase 1 |
| [ADR-030](../adr/ADR-030.md) | Remember MessageSid in memory | Phase 4 |
