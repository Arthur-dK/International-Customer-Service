"""Caller audio stays in memory. Static prompt caches may stay."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from core.language.phrases import PLACEHOLDER_PIN
from services.ivr.audio import generate_silence_mulaw, generate_tone_mulaw
from services.ivr.phrase_cache import PhraseAudioCache
from services.ivr.streaming_stt import ScriptedStreamingSpeechToText
from services.ivr.tts import ToneTextToSpeech
from services.ivr.turn_engine import PlaceholderTurnEngine

_REPO = Path(__file__).resolve().parents[3]
_SKIP_DIRS = {".git", "venv", ".venv", "huggingface"}
_PIN_LEAKS = ("1234", "one two three four", "un deux trois quatre")

client = TestClient(app)


def _audio_files(root: Path) -> set[Path]:
    found: set[Path] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in _SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith((".wav", ".mp3")):
                found.add(Path(dirpath) / name)
    return found


def _utterance() -> bytes:
    return generate_tone_mulaw(400, amplitude=0.45) + generate_silence_mulaw(400)


@pytest.mark.asyncio
async def test_pin_turn_logs_the_transcript_but_not_a_pin(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    before = _audio_files(_REPO)
    tts = ToneTextToSpeech()
    cache = PhraseAudioCache(tts, cache_dir=tmp_path)
    await cache.warmup(languages=("en",))
    engine = PlaceholderTurnEngine(
        language="en",
        cache=cache,
        stt=ScriptedStreamingSpeechToText(finals=["PIN please"]),
    )
    await engine.start()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    result = await engine.handle_utterance(_utterance(), outbound)
    logged = "\n".join(record.getMessage() for record in caplog.records).casefold()

    assert result is not None
    assert result.phrase_id == PLACEHOLDER_PIN
    assert "pin please" in logged
    for leak in _PIN_LEAKS:
        assert leak not in logged
    assert _audio_files(_REPO) == before
    assert list(tmp_path.rglob("*.wav")) == []
    assert list(tmp_path.rglob("*.mp3")) == []
    assert list(tmp_path.rglob("*.mulaw"))


def test_incoming_call_log_keeps_the_full_number(caplog):
    caplog.set_level(logging.INFO)
    number = "+33142685300"
    response = client.post(
        "/voice/incoming",
        headers={"host": "localhost:8000"},
        data={"From": number},
    )
    logged = "\n".join(record.getMessage() for record in caplog.records).casefold()
    assert response.status_code == 200
    assert number in logged
    for leak in _PIN_LEAKS:
        assert leak not in logged


def test_sapi_recognition_does_not_leave_a_wav(monkeypatch):
    if not sys.platform.startswith("win"):
        from services.ivr.sapi_stt import sapi_grammar_recognize

        assert sapi_grammar_recognize(b"\xff\xff", "en") == ""
        return

    created: list[Path] = []
    real_temp = tempfile.TemporaryDirectory

    def tracking(*args, **kwargs):
        directory = real_temp(*args, **kwargs)
        created.append(Path(directory.name))
        return directory

    monkeypatch.setattr(tempfile, "TemporaryDirectory", tracking)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args, returncode=0, stdout="balance\n", stderr=""),
    )
    from services.ivr.sapi_stt import sapi_grammar_recognize

    heard = sapi_grammar_recognize(_utterance(), "en")
    assert heard == "balance"
    assert created
    assert all(not path.exists() for path in created)
