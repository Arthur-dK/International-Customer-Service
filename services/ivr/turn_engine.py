"""Simulated IVR turns: speech_end → stub transcript → canned phrase audio.

Language is already known. Replies are catalog buffers, not live card data or an LLM.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from core.language.phrases import (
    CONFIRM_BLOCK,
    CONFIRM_KEYPAD,
    CONFIRM_UNBLOCK,
    DID_NOT_CATCH,
    GOODBYE,
    MAIN_MENU,
    PLACEHOLDER_BALANCE,
    PLACEHOLDER_BLOCKED,
    PLACEHOLDER_PIN,
    PLACEHOLDER_STATEMENT,
    PLACEHOLDER_UNBLOCKED,
    TASK_KEYPAD,
)
from services.ivr.audio import TWILIO_SAMPLE_RATE
from services.ivr.confirm import NO, YES, route_confirm
from services.ivr.intent_router import (
    BLOCK_CARD,
    GET_BALANCE,
    GET_CARD_STATEMENT,
    GET_PIN,
    UNBLOCK_CARD,
    matched_intents,
)
from services.ivr.language_selection import CLEAR_AUDIO_SENTINEL
from services.ivr.phrase_cache import PhraseAudioCache
from services.ivr.placeholder_intents import map_placeholder_intent
from services.ivr.streaming_stt import StreamingSpeechToText, Transcript, feed_until_speech_end
from services.ivr.streaming_tts import StreamingTextToSpeech, enqueue_tts_stream, stream_ready_phrase
from services.ivr.ttfb import ReplyKind, TtfbHarness
from services.ivr.vad import EnergyVad, VadConfig

logger = logging.getLogger(__name__)

_INTENT_PHRASES = {
    GET_BALANCE: PLACEHOLDER_BALANCE,
    GET_PIN: PLACEHOLDER_PIN,
    GET_CARD_STATEMENT: PLACEHOLDER_STATEMENT,
    BLOCK_CARD: PLACEHOLDER_BLOCKED,
    UNBLOCK_CARD: PLACEHOLDER_UNBLOCKED,
}
_CONFIRM_PHRASES = {
    BLOCK_CARD: CONFIRM_BLOCK,
    UNBLOCK_CARD: CONFIRM_UNBLOCK,
}
_TASK_DIGITS = {
    "1": GET_BALANCE,
    "2": GET_PIN,
    "3": GET_CARD_STATEMENT,
    "4": BLOCK_CARD,
    "5": UNBLOCK_CARD,
}
_CONFIRM_DIGITS = {"1": YES, "2": NO}
_CONFIRMED_ACTIONS = frozenset({BLOCK_CARD, UNBLOCK_CARD})


def _phrase_for_transcript(text: str, language: str) -> str:
    """Prefer the five-action router. Keep goodbye on the older keyword map.

    A transcript with two actions is not understood. It must not fall through
    to the older map, which returns the first keyword it sees.
    """
    found = matched_intents(text, language)
    if len(found) == 1:
        return _INTENT_PHRASES[next(iter(found))]
    if found:
        return DID_NOT_CATCH
    return map_placeholder_intent(text)


def _clear_playback(outbound: asyncio.Queue[str]) -> None:
    while not outbound.empty():
        try:
            outbound.get_nowait()
        except asyncio.QueueEmpty:
            break
    try:
        outbound.put_nowait(CLEAR_AUDIO_SENTINEL)
    except asyncio.QueueFull:
        pass


@dataclass(frozen=True)
class TurnResult:
    transcript: str
    phrase_id: str
    language: str
    chunks_sent: int
    ended: bool


@dataclass(frozen=True)
class _Heard:
    kind: str
    transcript: str = ""
    digit: str = ""


def _drain(queue: asyncio.Queue | None) -> None:
    if queue is None:
        return
    while not queue.empty():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break


class PlaceholderTurnEngine:
    """One listen→reply cycle after language selection (placeholder tasks only)."""

    def __init__(
        self,
        *,
        language: str,
        cache: PhraseAudioCache,
        stt: StreamingSpeechToText,
        ttfb: TtfbHarness | None = None,
        vad: EnergyVad | None = None,
        chunk_ms: int = 20,
        fallback_tts: StreamingTextToSpeech | None = None,
        silence_timeout_s: float = 6.0,
    ) -> None:
        self.language = language.lower()
        self.cache = cache
        self.stt = stt
        self.ttfb = ttfb if ttfb is not None else TtfbHarness()
        self.vad = vad or EnergyVad(VadConfig(rms_threshold=500, speech_start_ms=100, speech_end_ms=200))
        self.chunk_ms = chunk_ms
        self.fallback_tts = fallback_tts
        self.silence_timeout_s = silence_timeout_s
        self._confirm_intent: str | None = None
        self._confirm_unclear = 0

    async def start(self) -> None:
        await self.stt.start(language=self.language)

    def phrase_for_turn(self, text: str) -> str:
        """Next catalog line for a transcript, including block and unblock confirm."""
        if self._confirm_intent is not None:
            return self._apply_confirm(route_confirm(text, self.language))
        found = matched_intents(text, self.language)
        if len(found) == 1:
            return self._apply_intent(next(iter(found)))
        if found:
            return DID_NOT_CATCH
        return map_placeholder_intent(text)

    def phrase_for_digit(self, digit: str) -> str | None:
        """Keypad choice, or nothing when the key is not on the current menu."""
        if self._confirm_intent is not None:
            answer = _CONFIRM_DIGITS.get(digit)
            if answer is None:
                return None
            return self._apply_confirm(answer)
        intent = _TASK_DIGITS.get(digit)
        if intent is None:
            return None
        return self._apply_intent(intent)

    def keypad_for_silence(self) -> str:
        """Six seconds of silence opens the keypad. It does not spend the spoken retry."""
        if self._confirm_intent is not None:
            return CONFIRM_KEYPAD
        return TASK_KEYPAD

    def phrase_after_keypad_silence(self) -> str:
        """No key and no barge-in. Leave confirm without counting a spoken miss."""
        self._confirm_intent = None
        self._confirm_unclear = 0
        return MAIN_MENU

    def _apply_intent(self, intent: str) -> str:
        if intent in _CONFIRMED_ACTIONS:
            self._confirm_intent = intent
            self._confirm_unclear = 0
            return _CONFIRM_PHRASES[intent]
        self._confirm_intent = None
        self._confirm_unclear = 0
        return _INTENT_PHRASES[intent]

    def _apply_confirm(self, answer: str | None) -> str:
        if answer == YES and self._confirm_intent is not None:
            phrase_id = _INTENT_PHRASES[self._confirm_intent]
            self._confirm_intent = None
            self._confirm_unclear = 0
            return phrase_id
        if answer == NO:
            self._confirm_intent = None
            self._confirm_unclear = 0
            return MAIN_MENU
        self._confirm_unclear += 1
        if self._confirm_unclear >= 2 or self._confirm_intent is None:
            self._confirm_intent = None
            self._confirm_unclear = 0
            return MAIN_MENU
        return _CONFIRM_PHRASES[self._confirm_intent]

    async def _discard_playback_echo(
        self,
        inbound_audio: asyncio.Queue[bytes],
        stop_event: asyncio.Event,
        phrase_id: str,
    ) -> None:
        """Ignore the microphone while a prompt is still playing.

        Burst playback returns before the caller has heard the line. The phone
        echo of that line was being treated as their answer.
        """
        try:
            audio = self.cache.get_ready(phrase_id, self.language)
        except Exception:
            return
        deadline = time.perf_counter() + (len(audio) / float(TWILIO_SAMPLE_RATE))
        while time.perf_counter() < deadline and not stop_event.is_set():
            try:
                inbound_audio.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)
        while True:
            try:
                inbound_audio.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def play_phrase(
        self,
        phrase_id: str,
        outbound: asyncio.Queue[str],
        *,
        measure_ttfb: bool = False,
        cancel: asyncio.Event | None = None,
    ) -> int:
        """Enqueue a warmed catalog line. TTFB is only for post-speech_end replies."""
        return await enqueue_tts_stream(
            stream_ready_phrase(
                self.cache,
                phrase_id,
                self.language,
                chunk_ms=self.chunk_ms,
                cancel=cancel,
                fallback=self.fallback_tts,
            ),
            outbound,
            self.ttfb if measure_ttfb else None,
            reply_kind=ReplyKind.CANNED,
            cancel=cancel,
        )

    async def handle_utterance(
        self,
        mulaw: bytes,
        outbound: asyncio.Queue[str],
        *,
        cancel: asyncio.Event | None = None,
    ) -> TurnResult | None:
        """VAD speech_end → STT finish → canned phrase. Returns None if no utterance."""
        self.vad.reset()
        transcript = await feed_until_speech_end(
            mulaw,
            stt=self.stt,
            vad=self.vad,
            ttfb=self.ttfb,
            chunk_ms=self.chunk_ms,
        )
        if transcript is None:
            return None
        return await self._reply(transcript, outbound, cancel=cancel)

    async def handle_inbound_queue(
        self,
        inbound_audio: asyncio.Queue[bytes],
        outbound: asyncio.Queue[str],
        stop_event: asyncio.Event,
        *,
        cancel: asyncio.Event | None = None,
    ) -> TurnResult | None:
        """Read live Media Stream frames until VAD speech_end, then canned reply."""
        self.vad.reset()
        heard_speech = False
        while not stop_event.is_set():
            try:
                chunk = await asyncio.wait_for(inbound_audio.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            events = list(self.vad.process_mulaw(chunk))
            if any(event.kind == "speech_start" for event in events):
                await self.stt.start(language=self.language)
                heard_speech = True
            if heard_speech:
                await self.stt.feed_mulaw(chunk)
            for event in events:
                if event.kind == "speech_end":
                    self.ttfb.mark_speech_end()
                    transcript = await self.stt.finish()
                    if transcript is None:
                        return None
                    return await self._reply(transcript, outbound, cancel=cancel)
        return None

    async def run_on_queues(
        self,
        *,
        inbound_audio: asyncio.Queue[bytes],
        outbound_audio: asyncio.Queue[str],
        stop_event: asyncio.Event,
        dtmf_digits: asyncio.Queue[str] | None = None,
        play_menu: bool = True,
        max_turns: int = 8,
        on_turn: Callable[[list[TurnResult]], None] | None = None,
    ) -> list[TurnResult]:
        """Handoff after language selection: same inbound/outbound queues."""
        await self.start()
        _drain(dtmf_digits)
        if play_menu:
            await self.play_phrase(MAIN_MENU, outbound_audio, measure_ttfb=False)
            await self._discard_playback_echo(inbound_audio, stop_event, MAIN_MENU)
            await self.start()
        results: list[TurnResult] = []
        while len(results) < max_turns and not stop_event.is_set():
            heard = await self._listen_once(
                inbound_audio,
                dtmf_digits,
                stop_event,
                outbound_audio,
                timeout_s=self.silence_timeout_s,
            )
            if heard.kind == "stopped":
                break
            if heard.kind == "timeout":
                keypad_id = self.keypad_for_silence()
                played = await self._play_recorded(keypad_id, "", outbound_audio)
                results.append(played)
                if on_turn is not None:
                    on_turn(results)
                if len(results) >= max_turns:
                    break
                heard = await self._listen_for_keypad(
                    keypad_id,
                    inbound_audio,
                    dtmf_digits,
                    stop_event,
                    outbound_audio,
                )
                if heard.kind in ("stopped", "timeout"):
                    if heard.kind == "timeout":
                        phrase_id = self.phrase_after_keypad_silence()
                        played = await self._play_recorded(phrase_id, "", outbound_audio)
                        results.append(played)
                        if on_turn is not None:
                            on_turn(results)
                        if played.ended:
                            break
                        await self._discard_playback_echo(inbound_audio, stop_event, phrase_id)
                    continue
            phrase_id = (
                self.phrase_for_digit(heard.digit)
                if heard.kind == "dtmf"
                else self.phrase_for_turn(heard.transcript)
            )
            if phrase_id is None:
                continue
            played = await self._play_recorded(phrase_id, heard.transcript, outbound_audio)
            results.append(played)
            if on_turn is not None:
                on_turn(results)
            if played.ended:
                break
            await self._discard_playback_echo(inbound_audio, stop_event, phrase_id)
            await self.start()
        return results

    async def _listen_for_keypad(
        self,
        phrase_id: str,
        inbound_audio: asyncio.Queue[bytes],
        dtmf_digits: asyncio.Queue[str] | None,
        stop_event: asyncio.Event,
        outbound: asyncio.Queue[str],
    ) -> "_Heard":
        """Keep listening through keypad playback so speech can interrupt it."""
        try:
            audio = self.cache.get_ready(phrase_id, self.language)
            hold_s = len(audio) / float(TWILIO_SAMPLE_RATE)
        except Exception:
            hold_s = 0.0
        return await self._listen_once(
            inbound_audio,
            dtmf_digits,
            stop_event,
            outbound,
            timeout_s=hold_s + self.silence_timeout_s,
            flush_on_speech=True,
        )

    async def _listen_once(
        self,
        inbound_audio: asyncio.Queue[bytes],
        dtmf_digits: asyncio.Queue[str] | None,
        stop_event: asyncio.Event,
        outbound: asyncio.Queue[str],
        *,
        timeout_s: float,
        flush_on_speech: bool = False,
    ) -> "_Heard":
        self.vad.reset()
        heard_speech = False
        deadline = time.perf_counter() + timeout_s
        while not stop_event.is_set():
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return _Heard("timeout")
            tasks = [asyncio.create_task(inbound_audio.get(), name="audio")]
            if dtmf_digits is not None:
                tasks.append(asyncio.create_task(dtmf_digits.get(), name="dtmf"))
            done, pending = await asyncio.wait(
                tasks,
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if not done:
                return _Heard("timeout")
            finished = next(iter(done))
            if finished.get_name() == "dtmf":
                return _Heard("dtmf", digit=str(finished.result()))
            chunk = finished.result()
            events = list(self.vad.process_mulaw(chunk))
            if any(event.kind == "speech_start" for event in events):
                await self.stt.start(language=self.language)
                heard_speech = True
                if flush_on_speech:
                    _clear_playback(outbound)
                deadline = time.perf_counter() + max(self.silence_timeout_s, 3.0)
            if heard_speech:
                await self.stt.feed_mulaw(chunk)
            for event in events:
                if event.kind == "speech_end":
                    self.ttfb.mark_speech_end()
                    transcript = await self.stt.finish()
                    text = "" if transcript is None else transcript.text
                    return _Heard("speech", transcript=text)
        return _Heard("stopped")

    async def _play_recorded(
        self,
        phrase_id: str,
        transcript: str,
        outbound: asyncio.Queue[str],
    ) -> TurnResult:
        sent = await self.play_phrase(
            phrase_id,
            outbound,
            measure_ttfb=phrase_id not in (MAIN_MENU, TASK_KEYPAD, CONFIRM_KEYPAD),
        )
        logger.info(
            "placeholder_turn language=%s phrase=%s transcript=%r chunks=%s confirm=%s",
            self.language,
            phrase_id,
            transcript,
            sent,
            self._confirm_intent,
        )
        return TurnResult(
            transcript=transcript,
            phrase_id=phrase_id,
            language=self.language,
            chunks_sent=sent,
            ended=phrase_id == GOODBYE,
        )

    async def run_scripted_session(
        self,
        utterances: list[bytes],
        outbound: asyncio.Queue[str],
        *,
        play_menu: bool = True,
    ) -> list[TurnResult]:
        """Optional main menu, then one turn per inbound utterance until goodbye."""
        await self.start()
        if play_menu:
            await self.play_phrase(MAIN_MENU, outbound, measure_ttfb=False)
        results: list[TurnResult] = []
        for mulaw in utterances:
            result = await self.handle_utterance(mulaw, outbound)
            if result is None:
                continue
            results.append(result)
            if result.ended:
                break
        return results

    async def _reply(
        self,
        transcript: Transcript,
        outbound: asyncio.Queue[str],
        *,
        cancel: asyncio.Event | None,
    ) -> TurnResult:
        phrase_id = self.phrase_for_turn(transcript.text)
        sent = await self.play_phrase(
            phrase_id,
            outbound,
            measure_ttfb=True,
            cancel=cancel,
        )
        sample = self.ttfb.samples[-1] if self.ttfb.samples else None
        logger.info(
            "placeholder_turn language=%s phrase=%s transcript=%r chunks=%s ttfb_ms=%s within_budget=%s",
            self.language,
            phrase_id,
            transcript.text,
            sent,
            None if sample is None else round(sample.ttfb_ms, 1),
            None if sample is None else sample.within_budget,
        )
        return TurnResult(
            transcript=transcript.text,
            phrase_id=phrase_id,
            language=self.language,
            chunks_sent=sent,
            ended=phrase_id == GOODBYE,
        )
