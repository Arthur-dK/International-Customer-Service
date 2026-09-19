# Code files

What each application, data, and test file in this repository does. SMS and email routers exist as placeholders; the implemented path is multi-lingual IVR over Twilio Voice plus a media-stream WebSocket.

Related design notes live under `docs/adr/` and `docs/features/`. This page is a file map, not an architecture decision record.

---

## Application entry and HTTP API

| File | What it does |
|------|----------------|
| `app/main.py` | Creates the FastAPI app, attaches health/IVR/SMS/email routers, and on startup warms TTS, phrase audio, and language ID without blocking `/health`. |
| `app/deps.py` | Shared constructors for TTS, streaming STT/TTS, phrase cache, VAD config, and SpeechBrain (or fallback) language ID. |
| `app/api/__init__.py` | Empty package marker for API routers. |
| `app/api/health.py` | `GET /health` — liveness JSON used by Render and local checks. |
| `app/api/ivr.py` | Twilio `POST /voice/incoming` (TwiML that opens a media stream) and `WebSocket /media-stream` (inbound μ-law, DTMF, language selection, then placeholder task turns). |
| `app/api/sms.py` | Empty `/sms` router for the future multi-lingual SMS channel. |
| `app/api/email.py` | Empty `/email` router for the future translator / classifier / auto-reply channel. |

---

## Core (config, language, unused packages)

| File | What it does |
|------|----------------|
| `core/config.py` | Pydantic settings from `.env`: Twilio mocks, Ollama defaults, IVR TTS/LID/STT/VAD/timeout flags. |
| `core/ai/__init__.py` | Empty package reserved for shared LLM / embedding helpers. |
| `core/telephony/__init__.py` | Empty package reserved for telephony helpers outside IVR services. |
| `core/language/__init__.py` | Re-exports country/locale helpers used by the voice webhook and language selector. |
| `core/language/countries.py` | Parses caller numbers (E.164), maps country → language shortlist, builds DTMF menus, and loads prompt/name JSON. |
| `core/language/phrases.py` | Phrase-id catalog (`main_menu`, `placeholder_balance`, …) with language fallback and warmup language list. |
| `core/language/country_languages.json` | ISO country code → ordered language codes for the IVR selection menu. |
| `core/language/language_names.json` | ISO language code → English display name (used in DTMF menus). |
| `core/language/prompts.json` | Spoken “please say your language” line per language. |
| `core/language/phrases.json` | Canned IVR lines (English and French today) plus `warmup_languages`. |

---

## IVR services

| File | What it does |
|------|----------------|
| `services/cards/__init__.py` | Empty package reserved for live card APIs (balance, PIN, block). Placeholder phrases do not call this. |
| `services/ivr/twiml.py` | Builds `<Connect><Stream>` TwiML with optional `from` and `country_code` parameters. |
| `services/ivr/audio.py` | 8 kHz μ-law ↔ PCM conversion, RMS, silence/tone generation, 20 ms framing, WAV export, resampling for LID. |
| `services/ivr/vad.py` | Energy VAD: sustained RMS → `speech_start`, hangover silence → `speech_end` with buffered PCM. |
| `services/ivr/tts_lang.py` | Normalizes ISO language tags, aliases (e.g. `cmn` → `zh`), and Piper voice path maps. |
| `services/ivr/tts.py` | Batch TTS: tone stub, Windows SAPI, optional Piper, caching, language-matched routing, prompt warmup. |
| `services/ivr/edge_tts.py` | Microsoft Edge neural TTS for Linux/Render; MP3 → μ-law. Used when SAPI/Piper are not available. |
| `services/ivr/lid.py` | Spoken language ID: SpeechBrain VoxLingua107, remapping lookalikes to major languages, or a fixed-language stub. |
| `services/ivr/language_selection.py` | Call-start state machine: country-aware prompt, listen, LID, DTMF menu, barge-in; runs entirely on media-stream queues. |
| `services/ivr/metrics.py` | Dataclass of language-selection metrics for logs and tests. |
| `services/ivr/selection_store.py` | Process-local last `LanguageSelectionResult` for pytest / fake-Twilio harnesses. |
| `services/ivr/phrase_cache.py` | In-memory (and optional disk) μ-law buffers keyed by phrase id + language; hot path never synthesizes. |
| `services/ivr/streaming_tts.py` | Streams μ-law frames; wraps batch TTS or plays ready catalog audio; first chunk stops the TTFB clock. |
| `services/ivr/streaming_stt.py` | STT protocol plus scripted stub (CI) and factory (`scripted` vs `sapi`). |
| `services/ivr/sapi_stt.py` | Windows SAPI grammar STT: buffers until `speech_end`, recognizes balance/PIN/block/goodbye. |
| `services/ivr/placeholder_intents.py` | Keyword map from transcript → canned phrase id; grammar word lists for SAPI. |
| `services/ivr/turn_engine.py` | After language is known: play menu, listen, map intent, play canned reply, hang up on goodbye. |
| `services/ivr/turn_store.py` | Process-local last placeholder `TurnResult` list for harnesses. |
| `services/ivr/ttfb.py` | Time-to-first-audio-byte harness (speech_end → first outbound μ-law); 500 ms canned SLO. |

---

## Automated tests (`pytest`)

| File | What it does |
|------|----------------|
| `tests/test_main.py` | Asserts `/health` returns 200 and `healthy`. |
| `tests/ivr/__init__.py` | Package marker for IVR tests. |
| `tests/sms/__init__.py` | Empty package for future SMS tests. |
| `tests/email/__init__.py` | Empty package for future email tests. |
| `tests/ivr/pytest/conftest.py` | Puts the repo root on `sys.path` and sets short, stub-friendly IVR env vars before imports. |
| `tests/ivr/pytest/test_audio.py` | μ-law duration, energy, round-trip, 20 ms chunks, WAV write. |
| `tests/ivr/pytest/test_vad.py` | Noise ignore, speech start/end, reset, Twilio-sized frames. |
| `tests/ivr/pytest/test_twiml.py` | Stream URL, caller parameters, XML escaping. |
| `tests/ivr/pytest/test_webhook.py` | Incoming-call webhook TwiML includes stream and country when the number is known. |
| `tests/ivr/pytest/test_websocket.py` | WebSocket connect plus a minimal Twilio connected/start/media handshake. |
| `tests/ivr/pytest/test_countries.py` | Phone → country, language shortlists, prompts, DTMF digit mapping. |
| `tests/ivr/pytest/test_tts.py` | Tone/SAPI/cached TTS contracts and prompt warmup. |
| `tests/ivr/pytest/test_tts_routing.py` | Voice language must match the call language (no English-accented French). |
| `tests/ivr/pytest/test_edge_tts.py` | Edge voice table covers English/French and not arbitrary codes (no network). |
| `tests/ivr/pytest/test_lid.py` | Fixed LID, VoxLingua label remap, SpeechBrain load/fallback, optional real-model sample. |
| `tests/ivr/pytest/test_language_selection.py` | Selector state machine with fake TTS/LID/queues (speech, silence, DTMF, barge-in). |
| `tests/ivr/pytest/test_phrase_cache.py` | Catalog lookup and ready μ-law without TTS on the hot path. |
| `tests/ivr/pytest/test_streaming_stt.py` | Scripted STT after VAD `speech_end`; script parsing. |
| `tests/ivr/pytest/test_streaming_tts.py` | Chunk streaming, TTFB on first chunk, cancel, ready-phrase playback. |
| `tests/ivr/pytest/test_sapi_stt.py` | Grammar STT wiring (injected recognizer; no live Windows dictation required). |
| `tests/ivr/pytest/test_turn_engine.py` | Placeholder listen→reply cycles and median canned TTFB budget. |
| `tests/ivr/pytest/test_ttfb.py` | Fake-clock TTFB harness: budgets, median SLO, ignore extra marks. |
| `tests/ivr/pytest/test_media_stream_language.py` | Real FastAPI WebSocket + fake Twilio messages for language selection. |
| `tests/ivr/pytest/test_media_stream_turns.py` | Same harness through a placeholder task turn after language selection. |

---

## Manual IVR scripts

Runnable from the repo root (not collected as the default pytest suite). They exercise live Windows/Render-shaped stacks or a fake Twilio client.

| File | What it does |
|------|----------------|
| `tests/ivr/manual/__init__.py` | Package marker. |
| `tests/ivr/manual/fake_twilio_stream.py` | Builds Twilio-like WebSocket JSON (`connected`, `start`, `media`, `dtmf`, `stop`). |
| `tests/ivr/manual/manual_verify_media_stream.py` | Fake Twilio client against the real app (language selection and optional placeholder mode). |
| `tests/ivr/manual/manual_verify_webhook.py` | Live HTTP check of `POST /voice/incoming`. |
| `tests/ivr/manual/manual_verify_audio.py` | Playable WAV / μ-law sanity for local speakers. |
| `tests/ivr/manual/manual_verify_vad.py` | Energy VAD on generated or recorded audio. |
| `tests/ivr/manual/manual_verify_tts.py` | Speaks sample prompts through the configured TTS backend. |
| `tests/ivr/manual/manual_verify_lid.py` | Loads Fixed or SpeechBrain LID and scores fixture/English audio. |
| `tests/ivr/manual/manual_verify_language_selection.py` | End-to-end language selection without placing a Twilio call. |
| `tests/ivr/manual/manual_verify_smoke.py` | Readiness checklist for live-call profiles (phases 7–10); does not place a call. |

---

## Call flow (where files sit)

1. Twilio hits `app/api/ivr.py` → `core/language/countries.py` → `services/ivr/twiml.py`.
2. Media stream: inbound μ-law (`services/ivr/audio.py`, `vad.py`) → `language_selection.py` + `lid.py` + `tts.py` / `edge_tts.py`.
3. Then `turn_engine.py` uses `streaming_stt.py` (or `sapi_stt.py`), `placeholder_intents.py`, `phrase_cache.py`, and `streaming_tts.py`, with `ttfb.py` measuring reply start.
