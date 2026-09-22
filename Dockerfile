# Production image: Python 3.12 + CPU Torch + SpeechBrain LID (VoxLingua107).
# Target: a VPS (Hetzner or similar) via docker compose — not a RAM-capped PaaS.
FROM python:3.12.8-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HF_HOME=/app/.cache/huggingface \
    IVR_USE_SPEECHBRAIN_LID=true \
    IVR_LID_FORCE_LANGUAGE= \
    TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ivr-lid.txt requirements-linux.txt ./
RUN pip install --no-cache-dir -r requirements-linux.txt

COPY . .
RUN PYTHONPATH=. python -c "from services.ivr.lid import SpeechBrainLanguageIdentifier, build_default_lid; lid = SpeechBrainLanguageIdentifier(); print('lid_backend', type(build_default_lid()).__name__)"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
