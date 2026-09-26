# FEAT-04 — Placeholder intent router

| | |
|---|---|
| **Feature ID** | FEAT-04 |
| **Name** | Keyword placeholder intents, caller-ID gate, in-memory audio |
| **Branch** | `feat/stub-intent-router` |
| **Status** | Phase 1 implemented. Phases 2–6 not started. |
| **Target** | Route keyword requests to five canned card actions after an allowlisted caller picks a language |

Language selection remains [FEAT-02](FEAT-02.md). Templated turns and TTFB remain [FEAT-03](FEAT-03.md). Decisions for this feature start at [ADR-020](../adr/ADR-020.md).

---

## User experience

What the **caller** goes through:

1. They dial the Twilio number. If that number is missing, anonymous, or not on the allowlist, they hear that the number is not recognised, and the call ends. They never hear the language prompt.
2. An allowlisted caller goes through language selection ([FEAT-02](FEAT-02.md)), then a task menu for balance, PIN, statement, block, and unblock. Goodbye is not offered.
3. They speak a sentence that contains the action word, in English, French, Hebrew, Arabic, or Swahili. Two different actions in one sentence are not understood.
4. Balance, PIN, and statement play one canned line. The PIN line does not speak a PIN. Block and unblock ask for yes or no before the canned result.
5. Six seconds of silence opens a keypad menu. Speech can interrupt that menu.

What this feature **does not** do: call a live bank, record the call, or add a new speech-recognition engine for Hebrew, Arabic, or Swahili. Those languages are proven with transcripts until a later branch can hear them.

---

## Phases

Each phase has its own tests. Do not start the next phase until the current one is green.

### Phase 1 — Allowlist gate

- **Goal:** Unknown numbers are rejected on the Voice webhook, before language selection.
- **Delivered:** `core/telephony/allowed_callers.json`, `core/telephony/allowlist.py`, `core/telephony/rejection.py`; `<Say>`, a one-second pause, then `<Hangup>` in [`app/api/ivr.py`](../../../app/api/ivr.py); Twilio call completion in `services/ivr/force_hangup.py`; [ADR-020](../adr/ADR-020.md).
- **Tests:** `tests/ivr/pytest/test_allowlist.py`, `tests/ivr/pytest/test_webhook.py`.
- **Done when:** an allowlisted number still gets `<Connect><Stream>`; missing, anonymous, and unknown numbers get `<Say>` and `<Hangup>` and no stream URL.

### Phase 2 — Keyword router

Not started. Whole-word match for the five actions in English, French, Hebrew, Arabic, and Swahili. Two actions in one utterance are not understood.

### Phase 3 — Phrase catalog

Not started. Canned replies, including a PIN line with no digits or spelled-out numbers.

### Phase 4 — Confirm and keypad

Not started. Block and unblock ask for yes or no. Six seconds of silence opens the keypad, and speech can interrupt it.

### Phase 5 — Media stream

Not started. The dialogue runs after language selection on the existing turn path. No new speech engine.

### Phase 6 — Privacy assertions

Not started. Caller audio stays in memory. Tests forbid new `.wav` / `.mp3` files and PIN digit strings in logs. Static prompt caches may stay.

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-020](../adr/ADR-020.md) | Allowlist gate before language selection | Phase 1 |
