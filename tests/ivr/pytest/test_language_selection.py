"""State-machine tests for language selection (fake TTS/LID/queues only)."""

from __future__ import annotations

import asyncio

import pytest

from services.ivr.audio import chunk_mulaw, generate_silence_mulaw, generate_tone_mulaw
from services.ivr.language_selection import LanguageSelector
from services.ivr.lid import FixedLanguageIdentifier, LanguageIdResult
from services.ivr.tts import ToneTextToSpeech
from services.ivr.vad import VadConfig


async def _wait_for_outbound(outbound: asyncio.Queue[str], min_chunks: int = 1, timeout: float = 2.0) -> None:
    async def _poll():
        while outbound.qsize() < min_chunks:
            await asyncio.sleep(0.01)

    await asyncio.wait_for(_poll(), timeout=timeout)


async def _clear_outbound(outbound: asyncio.Queue[str]) -> None:
    while not outbound.empty():
        outbound.get_nowait()


async def _feed_speech(inbound: asyncio.Queue[bytes], duration_ms: int = 300) -> None:
    tone = generate_tone_mulaw(duration_ms=20, amplitude=0.6)
    frames = max(1, duration_ms // 20)
    for _ in range(frames):
        await inbound.put(tone)
    for chunk in chunk_mulaw(generate_silence_mulaw(500), chunk_ms=20):
        await inbound.put(chunk)


def _selector(lid_language: str = "he", silence_timeout_s: float = 0.3) -> LanguageSelector:
    return LanguageSelector(
        tts=ToneTextToSpeech(ms_per_char=5, min_ms=40, max_ms=80),
        lid=FixedLanguageIdentifier(language=lid_language, confidence=0.9),
        silence_timeout_s=silence_timeout_s,
        min_lid_confidence=0.1,
        min_utterance_ms=0.0,
        vad_config=VadConfig(rms_threshold=500, speech_start_ms=40, speech_end_ms=60),
        outbound_chunk_ms=20,
        playback_realtime=False,
        max_dtmf_rounds=3,
    )


class _SequenceLid:
    def __init__(self, languages: list[str]) -> None:
        self._languages = languages
        self._index = 0
        self.backend = "sequence"

    async def identify(self, pcm16_audio: bytes, sample_rate: int = 8000) -> LanguageIdResult:
        lang = self._languages[min(self._index, len(self._languages) - 1)]
        self._index += 1
        return LanguageIdResult(
            language=lang,
            confidence=0.9,
            latency_ms=1.0,
            backend=self.backend,
        )


@pytest.mark.asyncio
async def test_speech_selects_language_for_known_country():
    selector = _selector(lid_language="he")
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await asyncio.sleep(0.2)  # wait out burst-prompt hold
        await _feed_speech(inbound)

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+972501234567",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.language == "he"
    assert result.method == "speech"
    assert result.metrics.country_known is True
    assert result.metrics.prompt_language == "he"
    assert result.metrics.lid_language == "he"
    assert result.metrics.tts_calls >= 1
    assert result.metrics.outcome == "selected"
    assert result.metrics.total_selection_ms is not None


@pytest.mark.asyncio
async def test_silence_then_dtmf_selects_language():
    selector = _selector(lid_language="en", silence_timeout_s=0.25)
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await _clear_outbound(outbound)
        await asyncio.sleep(0.35)
        await _wait_for_outbound(outbound)  # DTMF menu
        await dtmf.put("2")

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+972501234567",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.method == "dtmf"
    assert result.language == "ar"  # IL: he, ar, en, ru
    assert result.metrics.dtmf_fallback_entered is True
    assert result.metrics.dtmf_digit == "2"
    assert result.metrics.silence_timeouts >= 1


@pytest.mark.asyncio
async def test_speech_barge_in_during_dtmf_fallback():
    selector = _selector(lid_language="en", silence_timeout_s=0.25)
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await _clear_outbound(outbound)
        await asyncio.sleep(0.35)
        await _wait_for_outbound(outbound)
        await _feed_speech(inbound)

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+972501234567",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.method == "speech_barge_in"
    assert result.language == "en"
    assert result.metrics.barge_in_during_dtmf is True
    assert result.metrics.dtmf_fallback_entered is True


@pytest.mark.asyncio
async def test_unknown_country_reprompts_in_english_before_dtmf():
    selector = _selector(lid_language="fr", silence_timeout_s=0.25)
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await _clear_outbound(outbound)
        await asyncio.sleep(0.35)
        await _wait_for_outbound(outbound)
        await _clear_outbound(outbound)
        await asyncio.sleep(0.35)
        await _wait_for_outbound(outbound)
        await dtmf.put("1")

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number=None,
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.metrics.country_known is False
    assert result.metrics.english_reprompts == 2
    assert result.metrics.silence_timeouts >= 2
    assert result.method == "dtmf"
    assert result.language == "en"


@pytest.mark.asyncio
async def test_dtmf_during_initial_listen_selects_without_menu():
    selector = _selector(lid_language="he", silence_timeout_s=1.0)
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await asyncio.sleep(0.05)
        await dtmf.put("1")

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+972501234567",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.method == "dtmf"
    assert result.language == "he"
    assert result.metrics.dtmf_fallback_entered is False
    assert result.metrics.dtmf_digit == "1"


def test_lid_language_acceptable_rejects_junk_and_allows_menu_english():
    from services.ivr.language_selection import lid_language_acceptable

    gb = ("en", "pl", "pa", "ur", "bn")
    assert lid_language_acceptable("en", 0.37, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert lid_language_acceptable("fr", 0.82, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert not lid_language_acceptable("fr", 0.44, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert not lid_language_acceptable("kk", 0.9, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert not lid_language_acceptable("sl", 0.7, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert not lid_language_acceptable("ht", 0.85, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert not lid_language_acceptable("ja", 0.44, gb, min_confidence=0.15, off_menu_min_confidence=0.5)
    assert lid_language_acceptable("pa", 0.2, gb, min_confidence=0.15, off_menu_min_confidence=0.5)


@pytest.mark.asyncio
async def test_off_menu_junk_lid_is_rejected_then_dtmf_works():
    selector = _selector(lid_language="kk", silence_timeout_s=1.0)
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await _clear_outbound(outbound)
        await asyncio.sleep(0.2)
        await _feed_speech(inbound)
        await asyncio.sleep(1.0)
        await _wait_for_outbound(outbound)
        await dtmf.put("1")

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+442071838750",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.method == "dtmf"
    assert result.language == "en"
    assert result.metrics.lid_language == "kk"
    assert result.metrics.speech_utterances >= 1


@pytest.mark.asyncio
async def test_rejected_lid_then_real_speech_still_selects():
    selector = LanguageSelector(
        tts=ToneTextToSpeech(ms_per_char=5, min_ms=40, max_ms=80),
        lid=_SequenceLid(["kk", "en"]),
        silence_timeout_s=1.0,
        min_lid_confidence=0.1,
        min_utterance_ms=0.0,
        vad_config=VadConfig(rms_threshold=500, speech_start_ms=40, speech_end_ms=60),
        outbound_chunk_ms=20,
        playback_realtime=False,
        max_dtmf_rounds=3,
    )
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await asyncio.sleep(0.2)
        await _feed_speech(inbound)
        await asyncio.sleep(0.15)
        await _feed_speech(inbound)

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+442071838750",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.method == "speech"
    assert result.language == "en"
    assert result.metrics.speech_utterances >= 2
    assert result.metrics.dtmf_fallback_entered is False


@pytest.mark.asyncio
async def test_speech_during_prompt_hold_does_not_select():
    selector = LanguageSelector(
        tts=ToneTextToSpeech(ms_per_char=20, min_ms=400, max_ms=500),
        lid=FixedLanguageIdentifier(language="kk", confidence=0.99),
        silence_timeout_s=0.25,
        min_lid_confidence=0.1,
        min_utterance_ms=0.0,
        vad_config=VadConfig(rms_threshold=500, speech_start_ms=40, speech_end_ms=60),
        outbound_chunk_ms=20,
        playback_realtime=False,
        max_dtmf_rounds=3,
    )
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await _feed_speech(inbound)
        await asyncio.sleep(0.55)
        await _wait_for_outbound(outbound)
        await dtmf.put("1")

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+442071838750",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is not None
    assert result.method == "dtmf"
    assert result.language == "en"
    assert result.metrics.speech_utterances == 0


@pytest.mark.asyncio
async def test_three_invalid_dtmf_digits_abandon():
    selector = _selector(lid_language="en", silence_timeout_s=0.2)
    inbound: asyncio.Queue[bytes] = asyncio.Queue()
    outbound: asyncio.Queue[str] = asyncio.Queue()
    dtmf: asyncio.Queue[str] = asyncio.Queue()

    async def feed():
        await _wait_for_outbound(outbound)
        await _clear_outbound(outbound)
        await asyncio.sleep(0.3)
        for _ in range(3):
            await _wait_for_outbound(outbound)
            await _clear_outbound(outbound)
            await dtmf.put("0")
            await asyncio.sleep(0.05)

    feeder = asyncio.create_task(feed())
    result = await selector.run(
        phone_number="+442071838750",
        inbound_audio=inbound,
        outbound_audio=outbound,
        dtmf_digits=dtmf,
    )
    await feeder

    assert result is None
