# FEAT-02 - Placeholder SMS intents

| | |
|---|---|
| **Feature ID** | FEAT-02 |
| **Name** | One-shot English keyword intents on the Twilio number |
| **Branch** | `feat/sms-intent-recognition-stub` |
| **Status** | Phases 1–5 implemented. |
| **Target** | Replace the allowlisted echo with one English placeholder reply |

What a tester should see is [the SMS requirements](../../../requirements/sms_requirements.md). This note is the build log.

The signed webhook, allowlist, and `MessageSid` dedupe stay on [FEAT-01](FEAT-01.md). Voice stays on [FEAT-04](../../ivr/features/FEAT-04.md). Decisions for this feature are [ADR-005](../adr/ADR-005.md) through [ADR-007](../adr/ADR-007.md).

---

## Phases

Each phase has its own tests. Do not start the next phase until the current one is green.

### Phase 1 - English keyword match

- **Goal:** A text maps to one of the five actions, or to none, without Twilio.
- **Delivered:** `services/sms/intent.py`; [ADR-005](../adr/ADR-005.md). Whole-token English keywords. Two actions return the earlier token. The webhook is unchanged.
- **Tests:** `tests/sms/pytest/test_intent.py`.
- **Done when:** varied English sentences route; two actions return the earlier one; empty, unknown, and punctuation-only text return none.

### Phase 2 - SMS reply catalog

- **Goal:** Each action and the no-match case have one English line that the IVR catalog does not own.
- **Delivered:** `services/sms/replies.py`; [ADR-007](../adr/ADR-007.md). The five action lines and the no-match sentence are plain strings in that module. The webhook is unchanged.
- **Tests:** `tests/sms/pytest/test_replies.py`.
- **Done when:** the five lines differ, the PIN line has no digits, the no-match line is the sentence above, and [`core/language/phrases.json`](../../../core/language/phrases.json) is untouched.

### Phase 3 - Language detection

- **Goal:** The body is labeled with a language code before a reply is chosen.
- **Delivered:** `services/sms/language.py`; `py3langid` in [`requirements.txt`](../../../requirements.txt); [ADR-006](../adr/ADR-006.md). Blank text and a detector failure return `en`. The webhook is unchanged.
- **Tests:** `tests/sms/pytest/test_language.py`.
- **Done when:** a few obvious sentences each return a language code with no network call, in well under 4 seconds, and the webhook is still unchanged.

### Phase 4 - Replace the echo

- **Goal:** An allowlisted non-empty body gets the placeholder reply through the existing Messages API path in [`app/api/sms.py`](../../../app/api/sms.py).
- **Delivered:** `_reply_body` detects the language, matches the intent, and returns the SMS catalog line. The reply log is JSON with `language`, `score`, and `intent` (`none` when nothing matched) and does not record `Body`. Empty bodies, unknown numbers, bad signatures, and duplicate `MessageSid`s stay on the FEAT-01 paths.
- **Tests:** `tests/sms/pytest/test_echo_sms.py`, including a no-match case and a two-action case. Rejection and dedupe tests stay green.
- **Done when:** the mocked client is called once with the placeholder, `from_` equal to inbound `To`, and `to` equal to inbound `From`. The JSON log has the language code, the detector score, and the intent id, and not the body.

### Phase 5 - Manual check

- **Goal:** An offline script shows the reply a signed webhook would send, without calling Twilio.
- **Delivered:** `tests/sms/manual/manual_verify_sms_intent.py`. It posts three signed texts with the Messages API client replaced.
- **Tests:** `tests/sms/manual/manual_verify_sms_intent.py`.
- **Done when:** the script prints PASS for a PIN text, a two-action text, and an unrelated text. A live text of `pin` from the allowlisted handset receives the PIN placeholder once.

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-005](../adr/ADR-005.md) | English whole-word SMS intents, earliest action wins | Phase 1 |
| [ADR-006](../adr/ADR-006.md) | Detect the text language, reply in English | Phase 3 |
| [ADR-007](../adr/ADR-007.md) | SMS-owned English placeholders replace the echo | Phases 2 and 4 |
