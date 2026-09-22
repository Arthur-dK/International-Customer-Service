# FEAT-01 — Twilio Media Stream audio pipeline

| | |
|---|---|
| **Feature ID** | FEAT-01 |
| **Name** | Twilio Voice webhook and real-time μ-law Media Stream |
| **Branch** | `feat/ivr-twilio-websocket` |
| **Status** | Implemented |
| **Target** | High-level IVR setup and a real-time bidirectional audio pipeline |

This is the foundation feature: FastAPI hosts Twilio Voice, opens a Media Stream WebSocket, and moves 8 kHz μ-law audio on asyncio queues without blocking the event loop. Language selection is [FEAT-02](FEAT-02.md). Latency / canned turns are [FEAT-03](FEAT-03.md).

Architectural decisions: [ADR-001](../adr/ADR-001.md), [ADR-003](../adr/ADR-003.md).

---

## Objective

Hook Twilio call audio into this service so later IVR logic can run on the same stream.

**Scope and deliverables:**

- Core FastAPI `/media-stream` WebSocket endpoint.
- Parse incoming Twilio WebSocket payloads (`connected`, `start`, `media`, `dtmf`, `stop`) and keep a bidirectional 8 kHz μ-law stream.
- In-memory `asyncio.Queue` buffers for inbound and outbound audio so receive, send, and call logic can run concurrently without blocking the main event loop.
- Incoming Voice webhook returns TwiML that `<Connect>`s that stream (so a real call can attach).

---

## User experience

Every FEAT document should include a section like this: what the caller hears and does, and what the feature does **not** do.

What the **caller** goes through on this feature:

1. They dial the Twilio number. Twilio POSTs to `/voice/incoming`.
2. The call is connected to a live Media Stream (not a pre-recorded `<Play>` of the whole IVR). Audio can flow both ways as 8 kHz μ-law frames.
3. On this feature alone they do not yet get a language prompt or card tasks. The pipeline is ready so later features can speak and listen on the same socket.

What this feature **does not** do: choose a language, run LID/VAD as a product, play canned IVR menus, understand “balance” / PIN, or store the call.

---

## ADR correlation

| ADR | Title | Role |
|-----|-------|------|
| [ADR-001](../adr/ADR-001.md) | Webhook retrieval and IVR platform (FastAPI + asyncio WebSockets) | Hosting choice for this branch: FastAPI, native asyncio WebSockets, in-memory `asyncio.Queue` buffers for the real-time voice endpoint |
| [ADR-003](../adr/ADR-003.md) | Twilio 8 kHz μ-law as the IVR audio contract | Wire format on `/media-stream`: decode Twilio `media` payloads, send μ-law back, shared helpers in `services/ivr/audio.py` |

Later features reuse this socket and these queues ([ADR-002](../adr/ADR-002.md) language selector, [ADR-016](../adr/ADR-016.md) placeholder turns) but those decisions are not part of FEAT-01.

---

## Runtime call flow

1. Twilio Voice webhook `POST /voice/incoming` → TwiML `<Connect><Stream url="…/media-stream">` (`services/ivr/twiml.py`).
2. Twilio opens `WebSocket /media-stream` (`app/api/ivr.py`).
3. Events: `connected` → `start` (streamSid, custom `from` / country) → `media` (base64 μ-law → inbound queue) and optional `dtmf` → `stop`.
4. A send loop reads the outbound queue and writes Twilio `media` messages (same encoding).
5. Receive, send, and later IVR tasks are separate asyncio tasks; hangup/`stop` cancels them and closes the socket.

---

## Key code

| Area | Path |
|------|------|
| App + IVR router | `app/main.py` |
| Webhook + `/media-stream` | `app/api/ivr.py` |
| Stream TwiML | `services/ivr/twiml.py` |
| 8 kHz μ-law helpers | `services/ivr/audio.py` |
| Settings (Twilio / debug) | `core/config.py` |
| Pytest handshake | `tests/ivr/pytest/test_websocket.py` |
| Webhook TwiML | `tests/ivr/pytest/test_webhook.py`, `tests/ivr/pytest/test_twiml.py` |
| Audio contract | `tests/ivr/pytest/test_audio.py` |
| Manual webhook check | `tests/ivr/manual/manual_verify_webhook.py` |

---

## Testing / verification

Unit tests use pytest and FastAPI `TestClient.websocket_connect` to verify handshake and connection teardown (`tests/ivr/pytest/test_websocket.py`). Webhook tests check that incoming Voice TwiML points at the stream. Audio helpers are covered without a live Twilio account.

```powershell
.\venv\Scripts\python.exe -m pytest tests/ivr/pytest/test_websocket.py tests/ivr/pytest/test_webhook.py tests/ivr/pytest/test_twiml.py tests/ivr/pytest/test_audio.py -q
```
