# FEAT-04 — Placeholder intent router

| | |
|---|---|
| **Feature ID** | FEAT-04 |
| **Name** | Keyword placeholder intents, caller-ID gate, in-memory audio |
| **Branch** | `feat/stub-intent-router` |
| **Status** | Phases 1–4 implemented. Phases 5–6 not started. |
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

- **Goal:** A transcript in the selected language maps to one of the five actions, or to no match.
- **Delivered:** `services/ivr/intent_router.py`; [ADR-021](../adr/ADR-021.md). After language selection, the turn engine uses `route_intent`. The older mapper is only for goodbye. A sentence with two actions asks the caller to repeat.
- **Tests:** `tests/ivr/pytest/test_intent_router.py`.
- **Done when:** varied sentences in English, French, Hebrew, Arabic, and Swahili route when they contain that language's keyword as a whole word; unblock does not match block; two actions do not match.

### Phase 3 — Phrase catalog

- **Goal:** Each action plays one canned line, in the selected language, and the PIN line does not speak a PIN.
- **Delivered:** `core/language/phrases.json` lines for balance, PIN, statement, block, and unblock in English, French, Hebrew, Arabic, and Swahili; [ADR-023](../adr/ADR-023.md). The English PIN line is "Your PIN will not be spoken on this call. This is a placeholder."
- **Tests:** `tests/ivr/pytest/test_phrase_catalog.py`.
- **Done when:** every action has a distinct line in each of the five languages; the PIN line has no digits and no run of spelled-out numbers.

### Phase 4 — Confirm and keypad

- **Goal:** Block and unblock ask for yes or no. Six seconds of silence opens a keypad, and speech can interrupt it.
- **Delivered:** `services/ivr/confirm.py`; confirm and keypad lines in `core/language/phrases.json`; the turn engine listens for speech, a key, or silence; [ADR-024](../adr/ADR-024.md).
- **Tests:** `tests/ivr/pytest/test_confirm.py`, `tests/ivr/pytest/test_turn_engine.py`.
- **Done when:** yes plays the result line; no, or a second unclear answer, plays the task menu; silence opens the keypad and does not spend the spoken retry. Keys are 1 balance, 2 PIN, 3 statement, 4 block, 5 unblock, and on confirm 1 yes, 2 no.

### Phase 5 — Media stream

Not started. The dialogue runs after language selection on the existing turn path. No new speech engine.

### Phase 6 — Privacy assertions

Not started. Caller audio stays in memory. Tests forbid new `.wav` / `.mp3` files and PIN digit strings in logs. Static prompt caches may stay.

---

## Errors on live calls

What went wrong while this phase was called, and what we concluded.

1. **The rejection message played, then the line stayed silent.** `<Hangup>` in the first webhook does not end the call, because that webhook still sees the call as ringing. The document now says the line, pauses one second, and redirects to a second document whose only verb is `<Hangup>`. Completing the call through Twilio's REST API does nothing while the account credentials are placeholders.
2. **Every sentence was answered with "I did not catch that."** `IVR_STT_BACKEND=whisper` was set before a Whisper recognizer existed, so the live path was the scripted recognizer. That ignores the audio and returns an empty transcript.
3. **A fixed phrase list still missed phone speech.** Windows speech grammar only accepts exact phrases. Open dictation on the same audio returned a single letter, or an unrelated sentence such as "Collide, do you want bells, please?" A closed list is not the recognizer. The caller can say any sentence. Whisper writes it down, and the router looks for one action word.
4. **The task menu was treated as the caller's answer.** Burst playback returns before the caller has heard the line, and the phone echo of that line was transcribed. Inbound audio is now ignored for the length of the line that is playing.
5. **The first PIN request played the balance line.** Whisper was given a hint sentence that starts "Can I check the balance, PIN…", and it copied "balance" into the transcript ("Can I check the balance, PIN?"). The older keyword map then returned the first word it found. The hint sentence was removed. Two actions in one sentence now ask the caller to repeat. The older map is only used for goodbye.
6. **Language selection seemed not to hear anything, then it worked.** Speech during the language prompt is discarded. On this PC that prompt is 3.6 seconds. A clip under 0.8 seconds is also rejected. After the prompt finished, "I would like English please" (1.5 seconds) was accepted as English. No selection rule was changed for that call.
7. **About four seconds of silence after the caller stopped talking.** That was Whisper `small` transcribing (3.9 seconds, then 3.8 seconds). The six-second silence timer, which opens the language keypad, did not run. `small` cannot be made quick enough on this PC, so the live model is `tiny` again. `tiny` is fast and still a weak phone recognizer. A better one is left for later: [later.md](../later.md).

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-020](../adr/ADR-020.md) | Allowlist gate before language selection | Phase 1 |
| [ADR-021](../adr/ADR-021.md) | Whole-word keyword intents | Phase 2 |
| [ADR-022](../adr/ADR-022.md) | Hear language selection; add languages without a rewrite | This phase stays callable end to end |
| [ADR-023](../adr/ADR-023.md) | One canned line per action, and the PIN is not spoken | Phase 3 |
| [ADR-024](../adr/ADR-024.md) | Confirm block and unblock, then a keypad after silence | Phase 4 |
