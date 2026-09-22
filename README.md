# Multi-Lingual Support Engine

Automated customer support for card holders across **voice (IVR)**, **SMS**, and **email**. The primary customer is Yordex, a card-management fintech that serves global NGOs (for example Red Cross and World Food Programme) in 190+ countries. A small support team cannot cover every language and timezone with humans alone. This system extends self-service and assists agents so card holders get help in their language, around the clock, at lower cost.

The repository is organised as **two sequential workstreams**, not as three independent channel projects.

---

## Where I am

| | |
|---|---|
| **You are here** | **Software engineering** — build every channel end to end with a **placeholder** intent-recognition algorithm |
| **Not started** | **Data science** — research, test, and choose the real intent-recognition implementation for IVR, SMS, and email |
| **Public deploy** | **Deferred** — Hetzner/VPS is prepared in-repo but **not running**. No live host until there is a real need (current list price is not justified for local-only work). |
| **Rule** | Data science does **not** begin until the software engineering segment is complete |

```text
[======= SOFTWARE ENGINEERING (current) =======]  [---- data science (later) ----]
   IVR / SMS / email product + placeholder intents      model research per channel
```

Until the data science segment lands, “the caller/texter/sender wanted X” is answered by an explicit stub (today: keyword matching on IVR placeholder tasks). The rest of the stack must still be real: telephony, language, latency, templates, identity, and handoff.

---

## The two segments

### 1. Software engineering — everything except intent-model research

Product and platform work that must exist regardless of which intent model is chosen later:

- FastAPI service, webhooks, Twilio Media Streams, SMS and email adapters
- Language selection, speech/text language handling, TTS/STT plumbing, latency (TTFB)
- Phrase catalogs, menus, DTMF, barge-in, silence, human handoff
- Card/account lookup, security and privacy constraints, deploy and tests
- Channel behaviour for IVR, SMS, and email **with a swappable intent interface**

Detail for this segment lives under [`docs/software-engineering/`](docs/software-engineering/): feature notes ([FEAT-01](docs/software-engineering/features/FEAT-01.md), [FEAT-02](docs/software-engineering/features/FEAT-02.md), [FEAT-03](docs/software-engineering/features/FEAT-03.md)) and [ADRs](docs/software-engineering/adr/). File-by-file map: [`docs/code-files.md`](docs/code-files.md). Deploy: [`docs/deploy-vps.md`](docs/deploy-vps.md).

### 2. Data science — intent recognition only (all three channels)

A separate, high-complexity process: **research, experiment, evaluate, and choose** how the system maps language to a **fixed intent set**. That process is repeated (or jointly designed) for:

| Channel | What “intent” means here |
|---------|---------------------------|
| **IVR** | Spoken (or keypad) requests such as balance, PIN, block/unblock, statement, top-up, agent |
| **SMS** | Short texts whose meaning is **balance** or **PIN** (this phase), in many languages |
| **Email** | Ticket types for classification, then which types are safe to automate |

This is not “wire an LLM into the call.” It is model/data work: corpora, languages, latency vs accuracy, on-device vs API, and a documented choice that plugs into the software engineering interfaces. **No data-science folder or runbook yet** — that work starts after software engineering is done.

---

## Product goals

- **Multi-lingual support** — on the order of ~50 languages, not a small closed list.
- **24×7 self-service** — automate high-volume, well-scoped requests outside human office hours.
- **Lower support cost** — deflect routine card queries and speed email handling for agents.
- **Fixed action sets** — known intents / ticket types, not open-ended agentic chat.
- **Human in the loop** — ambiguity, language mismatch for live handoff, and non-automated email stay with people.

### Channels today vs this project

| Channel | Today | This project |
|--------|--------|----------------|
| **SMS** | Text `Balance` or `PIN` to company numbers (UK + US/Canada). 24×7, **English only**. | Multi-lingual SMS for the same two intents. |
| **IVR** | Call for balance, PIN, card/statement, block/unblock. 24×7, **English + Hebrew**. | Multi-lingual conversational IVR (~50 languages), keypad fallback. |
| **Email / human** | `support@yordex.com` or UK phone (8am–8pm UK, 7 days). **English only**. | Translate ↔ English, classify tickets, automate only safe types; the rest stays with humans. |

Human phone support remains for cases that need an agent. AI channels must hand off cleanly when automation is not enough.

---

## Software engineering — channel scope

Work **inside this segment** is still sequenced by impact (IVR first: many Red Cross–supported users prefer calling and may be illiterate), but that order is *delivery inside software engineering*, not a substitute for the data science segment.

1. **Multi-lingual IVR** (in progress on the current stack)
2. **Multi-lingual SMS** (PIN + Balance) — router stubbed
3. **Email translator** (inbound → English for agents; reply → card holder’s language)
4. **Email ticket pipeline** (structured types + confidence, human default)
5. **Automated email responses** for agreed-safe types only

Each of those uses **placeholder intent recognition** until data science replaces the stub.

### IVR

Call at any time and complete card self-service by voice or keypad, in a language appropriate to country and preference.

- Balance, PIN, card/statement-style prompts, block/unblock (with confirmation), top-up where product rules allow.
- Language selection from caller country, then speech LID or DTMF; barge-in; ~7s silence repeat; ~0.5s to start canned audio after the caller stops talking.
- Identity is the **calling number**. **Do not record or store calls.**
- Twilio Voice + bidirectional 8 kHz μ-law Media Streams. Implemented path: FEAT-01 (stream), FEAT-02 (language), FEAT-03 (templated turns + TTFB). Live card APIs are not wired yet.

### SMS

Text a Yordex number at any time for **PIN** or **balance** only, in the sender’s language.

- Tiny fixed intent set; short template replies; 24×7; same number-based identity as IVR.
- Out of scope → refuse and point to IVR or email. Not started in code beyond an empty `/sms` router.

### Email

Help agents with worldwide mail: understand non-English threads, triage, automate only the safest high-volume types.

- Translator, then classifier, then optional auto-reply per ticket type. Default is human handling.
- Identity is email/account references, not ANI. Not started in code beyond an empty `/email` router.

Shared principles for this segment: prefer **local open-source** tooling where it fits cost, latency, and security; reuse one stack across channels; keep an **intent port** so data science can swap the placeholder without rewriting telephony or email plumbing.

---

## Data science — what comes later

When software engineering is complete, this segment owns:

- Defining evaluation sets and languages per channel (noisy telephony vs short SMS vs long email).
- Comparing approaches (keywords, embeddings, constrained LLMs, classical classifiers, hybrids).
- Choosing **one implementation per channel** (or a justified shared model) with latency, cost, privacy, and accuracy recorded.
- Handing a production-ready intent module to the existing software interfaces — not a second product rewrite.

Until then, IVR placeholder mapping lives in `services/ivr/placeholder_intents.py` (keyword → canned phrase). That file is a stand-in, not the research outcome.

---

## Repository layout

```text
app/                              # FastAPI app + HTTP/WebSocket routers
services/ivr/                     # Voice pipeline (audio, LID, TTS/STT, placeholder intents)
services/cards/                   # Shared card operations (planned)
core/                             # Config, language tables, reserved AI/telephony packages
tests/                            # Channel-aligned tests (ivr/ implemented; sms/, email/ reserved)
docs/software-engineering/        # FEAT notes + ADRs for the current segment
docs/code-files.md                # What each code file does
docs/deploy-vps.md                # Hetzner/VPS runbook (deferred — not live)
deploy/Caddyfile                  # TLS reverse proxy for Twilio HTTPS/WSS
```

`app/main.py` stays thin. Channel behaviour lives under `app/api/` and `services/<channel>/`.

---

## Tech stack (software engineering, current)

| Layer | Choice |
|--------|--------|
| Backend | Python 3.12+, FastAPI, WebSockets, Pytest |
| Voice | Twilio Programmable Voice, 8 kHz μ-law Media Streams |
| Speech (now) | Energy VAD; SpeechBrain LID (or fixed stub); SAPI/Edge/Piper TTS; grammar or scripted STT |
| Intent (now) | **Placeholder** — not the data science deliverable |
| Intent (later) | Outcome of the data science segment |
| Messaging / mail | Twilio SMS and email adapters (planned) |
| Infra | Local for now. Later: Docker Compose on a VPS (Hetzner) + Caddy — [deploy-vps.md](docs/deploy-vps.md) (**deferred**) |

## Running tests

```bash
python -m pytest tests/ -v
```

Use the project virtualenv if present.
