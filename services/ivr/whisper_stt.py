"""Local free-speech transcription for a finished utterance.

Whisper writes down the whole sentence. Intent matching stays in the router,
which looks for one action word inside that sentence.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time

import numpy as np

from services.ivr.audio import TWILIO_SAMPLE_RATE, mulaw_to_pcm16, resample_pcm16
from services.ivr.streaming_stt import Transcript
from services.ivr.tts_lang import normalize_language

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_NAME = ""
_MODEL_LOCK = threading.Lock()


def _load_model(model_name: str):
    global _MODEL, _MODEL_NAME
    with _MODEL_LOCK:
        if _MODEL is None or _MODEL_NAME != model_name:
            from faster_whisper import WhisperModel

            _MODEL = WhisperModel(model_name, device="cpu", compute_type="int8")
            _MODEL_NAME = model_name
        return _MODEL


class WhisperStreamingSpeechToText:
    """Free-form STT: one local Whisper pass when VAD closes the utterance."""

    def __init__(self, model_name: str = "tiny") -> None:
        self._model_name = (model_name or "tiny").strip() or "tiny"
        self._language = "en"
        self._buffer = bytearray()
        self._bytes_fed = 0

    @property
    def bytes_fed(self) -> int:
        return self._bytes_fed

    def supports_language(self, language: str) -> bool:
        return True

    def warm_model(self) -> None:
        _load_model(self._model_name)

    async def start(self, *, language: str) -> None:
        self._language = normalize_language(language) or "en"
        self._buffer.clear()
        self._bytes_fed = 0

    async def feed_mulaw(self, chunk: bytes) -> list[Transcript]:
        self._buffer.extend(chunk)
        self._bytes_fed += len(chunk)
        return []

    async def finish(self) -> Transcript | None:
        mulaw = bytes(self._buffer)
        self._buffer.clear()
        started = time.perf_counter()
        text = await asyncio.to_thread(self._transcribe, mulaw)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        cleaned = (text or "").strip()
        logger.info(
            "whisper_stt language=%s chars=%s stt_ms=%.1f text=%r",
            self._language,
            len(cleaned),
            elapsed_ms,
            cleaned,
        )
        return Transcript(text=cleaned, is_final=True, language=self._language)

    async def aclose(self) -> None:
        self._buffer.clear()

    def _transcribe(self, mulaw: bytes) -> str:
        if not mulaw:
            return ""
        pcm = resample_pcm16(mulaw_to_pcm16(mulaw), TWILIO_SAMPLE_RATE, 16000)
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        model = _load_model(self._model_name)
        segments, _info = model.transcribe(
            audio,
            language=self._language,
            vad_filter=False,
            beam_size=5,
            condition_on_previous_text=False,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()
