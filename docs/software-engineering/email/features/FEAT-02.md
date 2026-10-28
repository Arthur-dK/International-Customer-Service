# FEAT-02 - Placeholder email intents

| | |
|---|---|
| **Feature ID** | FEAT-02 |
| **Name** | One-shot English keyword intents on the inbound mailbox |
| **Branch** | `feat/email-stub-intent-router` |
| **Status** | Phases 1–4 implemented. |
| **Target** | Replace the plain-text echo with one English placeholder reply |

What a tester should see is [the email requirements](../../../requirements/email_requirements.md). This note is the build log.

The password check, plain-text parsing, language log, Message-ID dedupe, and daily cap stay on [FEAT-01](FEAT-01.md). Voice stays on [FEAT-04](../../ivr/features/FEAT-04.md). SMS stays on [FEAT-02](../../sms/features/FEAT-02.md). The keyword decision is [ADR-006](../adr/ADR-006.md). The reply lines are [ADR-007](../adr/ADR-007.md).

---

## Phases

Each phase has its own tests. Do not start the next phase until the current one is green.

### Phase 1 - English keyword match

- **Goal:** A text maps to one of the five actions, or to none, without SendGrid.
- **Delivered:** `services/email/intent.py`; [ADR-006](../adr/ADR-006.md). Whole-token English keywords. Two actions return nothing. The webhook is unchanged.
- **Tests:** `tests/email/pytest/test_intent_email.py`.
- **Done when:** varied English sentences route; two actions return nothing; empty, unknown, and punctuation-only text return none.

### Phase 2 - Email reply catalog

- **Goal:** Each action and the no-match case have one English line that the IVR catalog and the SMS catalog do not own.
- **Delivered:** `services/email/replies.py`; [ADR-007](../adr/ADR-007.md). The five action lines and the no-match sentence are plain strings in that module. The webhook is unchanged.
- **Tests:** `tests/email/pytest/test_replies_email.py`.
- **Done when:** the five lines differ, the PIN line has no digits, the no-match line is the sentence above, and [`core/language/phrases.json`](../../../core/language/phrases.json) is untouched.

### Phase 3 - Remove the echo

- **Goal:** A non-empty plain-text body gets the placeholder reply through the existing Mail Send path in [`app/api/email.py`](../../../app/api/email.py).
- **Delivered:** body selection in [`app/api/email.py`](../../../app/api/email.py). The reply log is JSON with `language`, `score`, and `intent` (`none` when nothing matched) and does not record the body or the subject. Empty bodies, bad passwords, a full daily cap, and duplicate Message-IDs stay on the FEAT-01 paths.
- **Tests:** `tests/email/pytest/test_echo_email.py`, including a no-match case and a two-action case. Rejection, cap, and dedupe tests stay green.
- **Done when:** the mocked client is called once with the placeholder, `from` equal to the inbound recipient, and `to` equal to the sender. The JSON log has the language code, the detector score, and the intent id, and not the body.

### Phase 4 - Manual check

- **Goal:** An offline script shows the reply a password-checked post would send, without calling SendGrid.
- **Delivered:** `tests/email/manual/manual_verify_email_intent.py`. It posts three emails with the Mail Send client replaced.
- **Done when:** the script prints PASS for a PIN email, a two-action email, and an unrelated email. A live email of `pin` to the inbound address receives the PIN placeholder once.

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-006](../adr/ADR-006.md) | English whole-word email intents, two actions are no match | Phase 1 |
| [ADR-007](../adr/ADR-007.md) | Email-owned English placeholders replace the echo | Phases 2 and 3 |
