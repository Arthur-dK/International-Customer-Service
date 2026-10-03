# FEAT-04 — Placeholder intent router

| | |
|---|---|
| **Feature ID** | FEAT-04 |
| **Name** | Keyword placeholder intents, caller-ID gate, in-memory audio |
| **Branch** | `feat/stub-intent-router` |
| **Status** | Phases 1–6 implemented. |
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

- **Goal:** The task dialogue runs after language selection on the existing media stream. No new speech engine.
- **Delivered:** `PlaceholderTurnEngine.run_on_queues` in [`app/api/ivr.py`](../../../app/api/ivr.py) on the same inbound, outbound, and keypad queues; [ADR-025](../adr/ADR-025.md).
- **Tests:** `tests/ivr/pytest/test_media_stream_turns.py`.
- **Done when:** a fake Twilio stream selects a language, then plays a canned reply, a block confirm followed by yes, and the task keypad after silence. The scripted recognizer is the only one used in that test.

### Phase 6 — Privacy assertions

- **Goal:** Caller audio stays in memory. A turn does not leave a `.wav` or `.mp3`, and logs do not contain a PIN as digits.
- **Delivered:** [ADR-026](../adr/ADR-026.md). Temporary speech files were already deleted when synthesis or recognition finished. The new tests lock that in.
- **Tests:** `tests/ivr/pytest/test_privacy.py`.
- **Done when:** a PIN turn logs the transcript and not `1234` or "one two three four"; the repo gains no `.wav` or `.mp3`; the `incoming_call` log still contains the full number; a Windows recognition temporary directory is gone after the call.

---

## Errors on live calls

What went wrong while this phase was called, and what we concluded.

1. **The rejection message played, then the line stayed silent.** `<Hangup>` in the first webhook does not end the call, because that webhook still sees the call as ringing. The document now says the line, pauses one second, and redirects to a second document whose only verb is `<Hangup>`. Completing the call through Twilio's REST API does nothing while the account credentials are placeholders.
2. **Every sentence was answered with "I did not catch that."** `IVR_STT_BACKEND=whisper` was set before a Whisper recognizer existed, so the live path was the scripted recognizer. That ignores the audio and returns an empty transcript.
3. **A fixed phrase list still missed phone speech.** Windows speech grammar only accepts exact phrases. Open dictation on the same audio returned a single letter, or an unrelated sentence such as "Collide, do you want bells, please?" A closed list is not the recognizer. The caller can say any sentence. Whisper writes it down, and the router looks for one action word.
4. **The task menu was treated as the caller's answer.** Burst playback returns before the caller has heard the line, and the phone echo of that line was transcribed. Inbound audio is now ignored for the length of the line that is playing.
5. **The first PIN request played the balance line.** Whisper was given a hint sentence that starts "Can I check the balance, PIN…", and it copied "balance" into the transcript ("Can I check the balance, PIN?"). The older keyword map then returned the first word it found. The hint sentence was removed. Two actions in one sentence now ask the caller to repeat. The older map is only used for goodbye.
6. **Language selection seemed not to hear anything, then it worked.** Speech during the language prompt is discarded. On this PC that prompt is 3.6 seconds. A clip under 0.8 seconds is also rejected. After the prompt finished, "I would like English please" (1.5 seconds) was accepted as English. No selection rule was changed for that call.
7. **About four seconds of silence after the caller stopped talking.** That was Whisper `small` transcribing (3.9 seconds, then 3.8 seconds). The six-second silence timer, which opens the language keypad, did not run. Faster decode settings only moved a test sentence from 3.3 seconds to 3.0 seconds. `small` cannot be made quick enough on this PC, so the live model is `tiny` again. `tiny` is fast and still a weak phone recognizer. A better one is left for later: [later.md](../later.md).
8. **The first balance request failed and the second worked.** The first transcript was "Collide, do you want bells, please?" and did not match. The second was "Can I check the balance please?" and played the balance line. Audio from before the caller started speaking had been included. The recognizer is now fed only after speech starts. A hint sentence was also removed, because it was copied into a later PIN transcript (item 5).
9. **"Block my card" was heard as "block my cop" and still blocked the card.** The match is the whole word `block`. A wrong word next to it does not cancel the action.
10. **A changed catalog line kept playing the old recording.** Phrase audio is stored as `.cache/ivr-phrases/{phrase id}.{language}.mulaw`. The file name does not include the text. After a line changes, that file has to be deleted or the phone keeps the old audio. This happened to the English PIN line.
11. **`test_default_allowlist_file_is_empty` failed.** The live test number is committed in `allowed_callers.json`, which [ADR-020](../adr/ADR-020.md) allows. An empty list is still tested with a temporary file. The webhook test checks that each committed entry is an exact E.164 string.
12. **Pytest printed four warnings.** SpeechBrain was setting an old Torch switch at import. That switch is skipped before import, and on this CPU it does not change language detection. Starlette's test client wanted `httpx2`, which is installed beside the app's existing `httpx`. The Windows speech test was using a retired event-loop policy. It now starts a selector loop directly. Call behavior did not change.

---

## Decisions recorded outside the ADRs

The ADRs above are the decision record. These are the smaller choices and facts that do not have their own ADR.

- Spanish was replaced with French, so one non-English language can be heard on this PC. The five languages are English, French, Hebrew, Arabic, and Swahili.
- The task menu is: "You can check your balance, check your PIN, hear your statement, block your card, or unblock your card." Goodbye is not on that menu.
- The balance line may still say a placeholder amount ("one hundred dollars"). Only the PIN line is forbidden from digits and spelled-out numbers ([ADR-023](../adr/ADR-023.md)).
- The recognizer is not given audio until speech has started, so silence and the tail of a prompt are not the transcript.
- Hearing French, Hebrew, Arabic, or Swahili with a real voice on this PC, without paying for a host, is not part of this phase. See [later.md](../later.md).

---

## ADR correlation

| ADR | Title | Role |
|-----|--------|------|
| [ADR-020](../adr/ADR-020.md) | Allowlist gate before language selection | Phase 1 |
| [ADR-021](../adr/ADR-021.md) | Whole-word keyword intents | Phase 2 |
| [ADR-022](../adr/ADR-022.md) | Hear language selection; add languages without a rewrite | This phase stays callable end to end |
| [ADR-023](../adr/ADR-023.md) | One canned line per action, and the PIN is not spoken | Phase 3 |
| [ADR-024](../adr/ADR-024.md) | Confirm block and unblock, then a keypad after silence | Phase 4 |
| [ADR-025](../adr/ADR-025.md) | Task dialogue stays on the existing media stream | Phase 5 |
| [ADR-026](../adr/ADR-026.md) | Caller audio stays in memory | Phase 6 |
