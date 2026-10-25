# FEAT-01 — Email echo on a SendGrid hostname

| | |
|---|---|
| **Feature ID** | FEAT-01 |
| **Name** | SendGrid inbound mail, then an exact plain-text echo |
| **Branch** | `feat/email-echo` |
| **Status** | Phases 1–6 implemented. |
| **Target** | A plain-text email to `echo@inbox.<your-domain>` is answered with that same plain text |

Voice stays on [FEAT-04](../../ivr/features/FEAT-04.md). SMS stays on [FEAT-02](../../sms/features/FEAT-02.md). The account and hostname decision is [ADR-001](../adr/ADR-001.md). The webhook password check is [ADR-002](../adr/ADR-002.md). The plain-text echo is [ADR-003](../adr/ADR-003.md). Language detection is [ADR-004](../adr/ADR-004.md). Retry dedupe is [ADR-005](../adr/ADR-005.md).

---

## User experience

When this feature is finished, any sender can email `echo@inbox.<your-domain>` and receive the same plain-text body from that address. The subject of the reply is `Re:` plus the original subject. HTML and attachments are ignored. An empty plain-text part gets no reply. Language detection runs on every non-empty body and is written to the log. It does not change the reply.

A plain-text email to the inbound address is answered with that same text. The reply comes from the address that received the mail.

### Try this (Phase 6)

- Pytest, from the repo root: `.\venv\Scripts\python.exe -m pytest tests/email/pytest -q`
- Offline reply check (no email is sent): `.\venv\Scripts\python.exe tests\email\manual\manual_verify_email_reply.py`
- It prints PASS when one French plain-text post would be echoed once, the log has `fr` and a score, and a second post of that Message-ID would not send again.
- Live: follow [Live check](#live-check).

---

## Phases

Each later phase has its own tests. Do not start the next phase until the current one is green.

### Phase 1 — SendGrid and a domain

- **Goal:** A free trial account, one domain, an `inbox` hostname that points at SendGrid, and a Mail Send API key in `.env`. No application behavior.
- **Delivered:** this page and [ADR-001](../adr/ADR-001.md).
- **Tests:** none. The check is the console list.
- **Done when:** the clicks, the env names, and the mailbox hostname are written here, and the console list can be followed without buying anything except the domain.

### Phase 2 — Authenticated inbound webhook

- **Goal:** `POST /email/incoming` checks HTTP basic auth, returns 200, and sends no mail. A bad password returns 403.
- **Delivered:** `services/email/auth.py`, `services/email/inbound.py`, `POST /email/incoming` in [`app/api/email.py`](../../../app/api/email.py); [ADR-002](../adr/ADR-002.md). Logs may include the envelope sender, the envelope recipient, and whether plain text was present. They must not include the subject or the plain-text body.
- **Tests:** `tests/email/pytest/test_incoming.py`. Manual: `tests/email/manual/manual_verify_email_webhook.py`.
- **Done when:** the matching password returns 200 and an empty body; a missing or wrong password returns 403; the plain-text body is absent from the log and from the response.

### Phase 3 — Exact plain-text echo

- **Goal:** The parsed `text` field is sent back through the SendGrid Mail Send API. From is the address that received the mail. To is the sender. An empty `text` sends nothing. A daily cap stays under the trial quota.
- **Delivered:** `services/email/outbound.py`, `services/email/quota.py`, the send in [`app/api/email.py`](../../../app/api/email.py); [ADR-003](../adr/ADR-003.md). `EMAIL_DAILY_SEND_CAP` defaults to 20.
- **Tests:** `tests/email/pytest/test_echo_email.py`. Manual: `tests/email/manual/manual_verify_email_echo.py`.
- **Done when:** the mocked client is called once with that exact body, `from` equal to the inbound recipient, and `to` equal to the sender. An empty `text` does not call it.

### Phase 4 — Language detection on every email

- **Goal:** The same offline detector used for SMS runs on every non-empty plain-text body. The reply body stays that text. The log records the language code and the score.
- **Delivered:** `services/language.py`; SMS imports that function; the detect call in [`app/api/email.py`](../../../app/api/email.py); [ADR-004](../adr/ADR-004.md).
- **Tests:** `tests/email/pytest/test_echo_email.py` covers a French sentence. `tests/sms/pytest/test_language.py` still covers the shared function.
- **Done when:** the reply JSON log includes the language code and the score, and not the body. An obvious French sentence is not labeled English.

### Phase 5 — Retry dedupe

- **Goal:** A second POST with the same `Message-ID` does not send again. A failed send returns 500 and can be retried.
- **Delivered:** `services/email/dedupe.py`; the key check in [`app/api/email.py`](../../../app/api/email.py); [ADR-005](../adr/ADR-005.md). A missing Message-ID is hashed from the sender, the recipient, and the plain text.
- **Tests:** `tests/email/pytest/test_dedupe.py`.
- **Done when:** two posts of one Message-ID call Mail Send once. A failed send returns 500, and a later post of that message can send.

### Phase 6 — Manual check

- **Goal:** An offline script covers the echo without calling SendGrid. The live check is one real email whose reply body matches, with a language code in the log.
- **Delivered:** `tests/email/manual/manual_verify_email_reply.py` and the [Live check](#live-check) below.
- **Done when:** the offline script prints PASS, and the live steps can be followed with the app and the tunnel already running.

---

## Live check

The app and the HTTPS tunnel must already be running. Inbound Parse for `internationalivr.xyz` must post to `https://<user>:<password>@<public-host>/email/incoming`, with “POST the raw, full MIME message” left off. `.env` must contain `SENDGRID_API_KEY`, `SENDGRID_INBOUND_USER`, and `SENDGRID_INBOUND_PASSWORD`. Restart the app after any change to `.env`.

1. From the repo root: `.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Point the tunnel at port 8000. The host in the Inbound Parse URL must be the host that is running now.
3. Send one plain-text email to `echo@internationalivr.xyz`.
4. The reply body is that same text. The subject is `Re:` plus the original subject.
5. The app log has one `email_reply` line with a language code and a score. That line does not include the body.
6. SendGrid’s retry of that same message does not add a second reply. The log shows `email_duplicate` for that retry.

---

## Console steps for Phase 1

Twilio SendGrid’s current Email API trial is $0 for 60 days, about 100 sent emails per day, and it does not ask for a card. After 60 days, sending stops unless you upgrade. Leave every payment page blank. This phase does not send mail.

Replace `example.com` below with the domain you register. The mailbox hostname is `inbox.example.com`. The address you will email, in a later phase, is `echo@inbox.example.com`.

### 1. Open the trial

1. Sign up at [Twilio SendGrid](https://signup.sendgrid.com/). Choose the Email API trial.
2. Leave Marketing Campaigns unused.
3. Confirm the account email SendGrid sends you.
4. Stop on any page that asks for a card.

### 2. Register a domain

1. Register the cheapest domain whose DNS page lets you add MX and CNAME records yourself. A `.com` at the registrar’s cost is enough.
2. Skip a host that will not show those records.
3. Leave the domain’s existing mail records alone. The only new mail record in this phase is the `inbox` MX below.

### 3. Authenticate the root domain

SendGrid will not send a later reply until this domain is verified. Authenticate `example.com`, the root. Leave `inbox` for the MX record in the next step. Automated security on `inbox` itself would fight that MX record.

1. SendGrid console → **Settings** → **Sender Authentication**.
2. Under Domain Authentication, click **Get Started**.
3. Pick your DNS host, or **Other Host (Not Listed)**.
4. Set **Would you also like to brand the links for this domain?** to **No**.
5. Click **Next**. In **Domain You Send From**, type the root only: `example.com`.
6. Open **Advanced Settings**. Leave **Use automated security** checked. Leave custom return path, custom DKIM selector, and EU pinning unchecked.
7. Click **Next**. The Install DNS Records page lists CNAME records (SPF and DKIM) and a DMARC TXT record. Copy them exactly.
8. At your DNS host, add each record. If the host appends the domain for you, type only the left-hand label. SendGrid’s host `em1234.example.com` is entered as `em1234`, or the stored name becomes `em1234.example.com.example.com` and verification fails.
9. Return to SendGrid and click **Verify**. DNS can take up to 48 hours. The domain should show as verified before a live reply is expected. You can keep going through the rest of this list while you wait.

### 4. Point `inbox` at SendGrid

1. At the DNS host, add one MX record:

| Host | Type | Priority | Value |
|------|------|----------|--------|
| `inbox` | MX | 10 | `mx.sendgrid.net` |

2. If the host wants a trailing dot, use `mx.sendgrid.net.`. If it appends the domain, the host field is `inbox`, which it stores as `inbox.example.com`.
3. Leave the apex MX record unchanged.

### 5. Add the Inbound Parse host

The app does not accept this URL yet. Adding it now means Phase 2 only has to implement the route.

1. Invent a username and a long password. Characters `@`, `:`, `/`, `?`, and `#` in the password must be percent-encoded inside the URL.
2. SendGrid console → **Settings** → **Inbound Parse** → **Add Host & URL**.
3. Receiving domain: subdomain `inbox`, domain `example.com`. The host shown should be `inbox.example.com`.
4. Destination URL:

```text
https://<user>:<password>@<public-host>/email/incoming
```

`<public-host>` is the same HTTPS tunnel already used for SMS (ngrok or the existing tunnel), with no path before `/email/incoming`.

5. Leave **Check incoming emails for spam** unchecked.
6. Leave **POST the raw, full MIME message** unchecked. The webhook should receive the parsed `text` field.
7. Click **Add**.

The local part of the address can be any word except `abuse`, `postmaster`, and `unsubscribe`. Use `echo@inbox.example.com`.

### 6. Create a Mail Send API key

1. SendGrid console → **Settings** → **API Keys** → **Create API Key**.
2. Name it `email-echo`.
3. Choose **Restricted Access**.
4. Under Mail Send, set **Mail Send** to **Full Access**. Leave every other permission off.
5. Create the key and copy it. SendGrid shows it once.

### 7. Store the secrets

`.env` is gitignored. Add these three lines with your real values. The app does not read them until a later phase.

```text
SENDGRID_API_KEY=
SENDGRID_INBOUND_USER=
SENDGRID_INBOUND_PASSWORD=
```

`SENDGRID_INBOUND_USER` and `SENDGRID_INBOUND_PASSWORD` are the same pair embedded in the Inbound Parse URL. A later phase adds `EMAIL_DAILY_SEND_CAP` in the app. You can leave it unset now.

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-001](../adr/ADR-001.md) | Receive mail through SendGrid Inbound Parse | Phase 1 |
| [ADR-002](../adr/ADR-002.md) | Reject unauthenticated inbound email posts | Phase 2 |
| [ADR-003](../adr/ADR-003.md) | Echo the plain text through Mail Send | Phase 3 |
| [ADR-004](../adr/ADR-004.md) | Detect the email language, echo the same text | Phase 4 |
| [ADR-005](../adr/ADR-005.md) | Remember Message-ID in memory | Phase 5 |
