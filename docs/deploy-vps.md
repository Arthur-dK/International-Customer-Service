# Deploy on a VPS (Hetzner)

**Status: later — do not provision a server yet.** The Docker/Caddy layout is in the repo so public Twilio calling can be stood up when needed. Until then, run the app locally. A billed VPS is not required for software-engineering work.

---

Run this FastAPI app on a **small always-on Linux VM** with Docker. Twilio Voice needs public **HTTPS** and a **long-lived WebSocket** (`/media-stream`). A VPS is the right fit now and later: you can add RAM when SMS, email, and intent models land, without paying PaaS memory premiums.

**Recommended starter:** [Hetzner Cloud](https://www.hetzner.com/cloud) **CX23** (2 vCPU, **4 GB RAM**, ~€5–7/month in Falkenstein/Helsinki). SpeechBrain LID wants about 2 GB; 4 GB leaves headroom. When the stack grows, **resize the same server** (CX33 = 8 GB, and so on) instead of switching hosts.

Do **not** use Vercel, Netlify, Cloudflare Workers, or AWS Lambda for this process.

---

## What you need before you start

1. A Hetzner account and a billed project.
2. A **domain name** you control (A record must point at the VPS). Let's Encrypt will not issue a cert for a bare IP.
3. A Twilio account and a voice number.
4. This repo on GitHub (or another git remote you can clone on the server).

---

## 1. Create the server

1. Hetzner Cloud → **Add server**.
2. Location: closest to you / your callers (EU users: Falkenstein or Helsinki).
3. Image: **Ubuntu 24.04**.
4. Type: **CX23** (4 GB).
5. Networking: enable **IPv4**.
6. SSH key: add your public key.
7. Create the server. Copy the **public IPv4**.

---

## 2. Point DNS at the server

At your DNS host, create:

| Type | Name | Value |
|------|------|--------|
| A | `ivr` (or `@` / `api`) | the VPS IPv4 |

Wait until `ping your-host.example.com` reaches that IP (often a few minutes).

---

## 3. Prepare the VPS

SSH in:

```bash
ssh root@YOUR_SERVER_IP
```

Install Docker Engine (Ubuntu):

```bash
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

Clone the app (use your repo URL):

```bash
mkdir -p /opt
cd /opt
git clone https://github.com/YOUR_ORG/Customer-Service-AI-System.git app
cd /opt/app
```

Open ports 22, 80, and 443 in the Hetzner firewall (or `ufw allow 80,443,22/tcp`).

---

## 4. Environment file

On the server:

```bash
cp .env.example .env
nano .env
```

Set at least:

```env
DOMAIN=ivr.example.com
ACME_EMAIL=you@example.com

TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx

DEBUG=false
IVR_USE_SPEECHBRAIN_LID=true
IVR_LID_FORCE_LANGUAGE=
IVR_STT_BACKEND=scripted
IVR_STT_SCRIPT=balance,goodbye
IVR_PLAYBACK_REALTIME=false
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
```

`DOMAIN` must match the DNS name from step 2. `ACME_EMAIL` is for Let's Encrypt expiry mail.

Leave `IVR_LID_FORCE_LANGUAGE` empty. Linux has no Windows SAPI STT; `scripted` is expected until a Linux STT backend exists.

---

## 5. Build and start

First build downloads Torch and the VoxLingua107 weights. Allow several minutes and a few GB of disk.

```bash
cd /opt/app
docker compose up -d --build
docker compose logs -f app
```

Pass when logs show:

- `lid_backend SpeechBrainLanguageIdentifier` during image build
- `IVR LID warmed class=SpeechBrainLanguageIdentifier`
- `GET /health` is reachable: `curl -s https://ivr.example.com/health`

Caddy obtains a TLS certificate automatically. If HTTPS fails, DNS is wrong or ports 80/443 are blocked.

---

## 6. Point Twilio at the VPS

1. Twilio Console → your Voice number → **A call comes in**.
2. Webhook: `https://ivr.example.com/voice/incoming` — HTTP **POST**.
3. Save. The media stream URL is derived from that host (`wss://…/media-stream`).

Call the number. Trial accounts may ask you to press a key first.

**Phone checks**

1. Logs: SpeechBrain, not `FixedLanguageIdentifier`.
2. Speak **French**, pause → `language_selected language=fr`.
3. Speak **English**, pause → `language=en`.
4. After the menu, scripted STT still plays `balance` then `goodbye` on each pause unless you change `IVR_STT_SCRIPT`.

---

## Day-to-day

```bash
cd /opt/app
git pull
docker compose up -d --build
docker compose logs -f --tail=100
docker compose ps
```

Hugging Face and TTS caches live in the `model-cache` volume (they survive rebuilds).

---

## When the app gets heavier

| Growth | What to do |
|--------|------------|
| OOM / LID crashes | Hetzner → server → **Resize** to CX33 (8 GB) or larger; `docker compose up -d` again |
| Intent models, extra voices, email stack | Same VM, more RAM; keep compose — add services later |
| Need a GPU later | New GPU CX or a second box; keep Caddy on this host as the public edge |

You do not need to migrate off Hetzner for SMS/email; those are more HTTP webhooks on the same process (or extra compose services).

---

## If SpeechBrain fails to load

Build did not install Torch, or the model download failed. Rebuild with `docker compose build --no-cache app` and confirm disk is not full (`df -h`). Temporary fallback (English-only LID):

```env
IVR_USE_SPEECHBRAIN_LID=false
IVR_LID_FORCE_LANGUAGE=en
```

Callers can still use the **DTMF** language menu.
