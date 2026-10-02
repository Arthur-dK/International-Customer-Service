"""Fake Twilio stream: language selection then placeholder task turn."""

from __future__ import annotations

import asyncio
import time

from fastapi.testclient import TestClient

from app.main import app
from core.language.phrases import CONFIRM_BLOCK, PLACEHOLDER_BALANCE, PLACEHOLDER_BLOCKED, TASK_KEYPAD
from services.ivr.audio import chunk_mulaw, generate_silence_mulaw, generate_tone_mulaw
from services.ivr.lid import FixedLanguageIdentifier
from services.ivr.phrase_cache import PhraseAudioCache
from services.ivr.selection_store import clear_last_language_selection, get_last_language_selection
from services.ivr.streaming_stt import ScriptedStreamingSpeechToText
from services.ivr.streaming_tts import build_default_streaming_tts
from services.ivr.tts import ToneTextToSpeech
from services.ivr.turn_store import clear_last_turns, get_last_turns
from tests.ivr.manual.fake_twilio_stream import (
    STREAM_SID,
    connected_message,
    dtmf_message,
    media_message,
    parse_outbound,
    start_message,
    stop_message,
)
from tests.ivr.pytest.test_media_stream_language import _collect_outbound_media, _wait_for_selection


def _wait_for_phrase(phrase_id: str, timeout_s: float = 3.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        turns = get_last_turns()
        if any(turn.phrase_id == phrase_id for turn in turns):
            return turns
        time.sleep(0.05)
    return get_last_turns()


def _patch_stream(monkeypatch, tmp_path, *, finals: list[str], silence_s: float) -> None:
    tts = ToneTextToSpeech(ms_per_char=5, min_ms=40, max_ms=80)
    cache = PhraseAudioCache(tts, cache_dir=tmp_path)
    asyncio.run(cache.warmup(languages=("en",)))
    monkeypatch.setattr("app.api.ivr.get_tts", lambda: tts)
    monkeypatch.setattr("app.api.ivr.get_lid", lambda: FixedLanguageIdentifier(language="en", confidence=0.99))
    monkeypatch.setattr("app.api.ivr.get_phrase_cache", lambda: cache)
    monkeypatch.setattr("app.api.ivr.get_streaming_stt", lambda: ScriptedStreamingSpeechToText(finals=finals))
    monkeypatch.setattr("app.api.ivr.get_streaming_tts", lambda: build_default_streaming_tts(tts))
    monkeypatch.setattr("app.api.ivr.settings.IVR_SILENCE_TIMEOUT_S", silence_s)
    monkeypatch.setattr("app.api.ivr.settings.IVR_PLAYBACK_REALTIME", False)
    monkeypatch.setattr("app.api.ivr.settings.IVR_MIN_LID_CONFIDENCE", 0.1)
    monkeypatch.setattr("app.api.ivr.settings.IVR_MIN_LID_UTTERANCE_MS", 0.0)
    clear_last_language_selection()
    clear_last_turns()


def _select_english(websocket) -> None:
    prompt = _collect_outbound_media(websocket, min_frames=1, overall_timeout_s=2.0)
    assert any(message.get("event") == "media" for message in prompt)
    websocket.send_text(dtmf_message("1"))
    selected = _wait_for_selection(timeout_s=2.0)
    assert selected is not None
    assert selected.language == "en"
    menu = _collect_outbound_media(websocket, min_frames=1, overall_timeout_s=2.0)
    assert any(message.get("event") == "media" for message in menu)


def _send_utterance(websocket) -> None:
    tone = generate_tone_mulaw(duration_ms=20, amplitude=0.6)
    for _ in range(25):
        websocket.send_text(media_message(tone))
    for chunk in chunk_mulaw(generate_silence_mulaw(500), chunk_ms=20):
        websocket.send_text(media_message(chunk))


def test_media_stream_placeholder_turn_after_language_selection(tmp_path, monkeypatch):
    _patch_stream(monkeypatch, tmp_path, finals=["balance"], silence_s=1.5)

    client = TestClient(app)
    with client.websocket_connect("/media-stream") as websocket:
        websocket.send_text(connected_message())
        websocket.send_text(start_message(from_number="+442071838750"))
        _select_english(websocket)

        time.sleep(0.3)
        _send_utterance(websocket)
        turns = _wait_for_phrase(PLACEHOLDER_BALANCE, timeout_s=3.0)
        reply = _collect_outbound_media(websocket, min_frames=1, overall_timeout_s=2.0)
        websocket.send_text(stop_message())

    assert turns
    assert turns[0].phrase_id == PLACEHOLDER_BALANCE
    assert turns[0].language == "en"
    assert turns[0].chunks_sent >= 1
    assert any(message.get("event") == "media" for message in reply)
    assert all(
        message.get("streamSid") == STREAM_SID
        for message in reply
        if message.get("event") == "media"
    )


def test_media_stream_block_confirm_yes_uses_the_same_stream(tmp_path, monkeypatch):
    _patch_stream(monkeypatch, tmp_path, finals=["block my card"], silence_s=1.5)

    client = TestClient(app)
    with client.websocket_connect("/media-stream") as websocket:
        websocket.send_text(connected_message())
        websocket.send_text(start_message(from_number="+442071838750"))
        _select_english(websocket)

        time.sleep(0.3)
        _send_utterance(websocket)
        confirm = _wait_for_phrase(CONFIRM_BLOCK, timeout_s=3.0)
        assert [turn.phrase_id for turn in confirm] == [CONFIRM_BLOCK]

        websocket.send_text(dtmf_message("1"))
        done = _wait_for_phrase(PLACEHOLDER_BLOCKED, timeout_s=3.0)
        websocket.send_text(stop_message())

    assert [turn.phrase_id for turn in done] == [CONFIRM_BLOCK, PLACEHOLDER_BLOCKED]
    assert all(turn.language == "en" for turn in done)


def test_media_stream_silence_opens_task_keypad(tmp_path, monkeypatch):
    _patch_stream(monkeypatch, tmp_path, finals=[], silence_s=0.4)

    client = TestClient(app)
    with client.websocket_connect("/media-stream") as websocket:
        websocket.send_text(connected_message())
        websocket.send_text(start_message(from_number="+442071838750"))
        _select_english(websocket)
        turns = _wait_for_phrase(TASK_KEYPAD, timeout_s=2.0)
        websocket.send_text(stop_message())

    assert turns
    assert turns[0].phrase_id == TASK_KEYPAD
    assert turns[0].language == "en"
