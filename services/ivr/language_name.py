"""Match a spoken language name ("English", "Nederlands") to an ISO code.

The selection prompt asks for the language name. A single short word is too
brief for acoustic language ID, which labels these clips as unrelated languages.
"""

from __future__ import annotations

import logging

import numpy as np

from core.language.countries import load_language_names
from services.ivr.audio import TWILIO_SAMPLE_RATE, pcm16_rms, resample_pcm16

logger = logging.getLogger(__name__)

# Endonyms and common names that are not the English label in language_names.json.
_SPOKEN_ALIASES: dict[str, str] = {
    "english": "en",
    "engels": "en",
    "dutch": "nl",
    "nederlands": "nl",
    "french": "fr",
    "francais": "fr",
    "français": "fr",
    "german": "de",
    "deutsch": "de",
    "spanish": "es",
    "espanol": "es",
    "español": "es",
    "polish": "pl",
    "polski": "pl",
    "punjabi": "pa",
    "urdu": "ur",
    "bengali": "bn",
    "bangla": "bn",
    "portuguese": "pt",
    "portugues": "pt",
    "português": "pt",
    "italian": "it",
    "italiano": "it",
    "arabic": "ar",
    "hindi": "hi",
    "chinese": "zh",
    "mandarin": "zh",
    "russian": "ru",
    "turkish": "tr",
    "turkce": "tr",
    "türkçe": "tr",
    "ukrainian": "uk",
}

_DUTCH_TOKENS = frozenset({"ned", "nederland", "nederlands", "dutch"})


def utterance_is_too_short(
    voiced_ms: float,
    min_utterance_ms: float,
    speech_end_ms: float,
) -> bool:
    """True for coughs. The configured minimum includes VAD's trailing silence."""
    if min_utterance_ms <= 0:
        return False
    min_voiced_ms = max(200.0, min_utterance_ms - speech_end_ms - 150.0)
    return voiced_ms < min_voiced_ms


def _edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for index, char in enumerate(left, start=1):
        current = [index]
        for other_index, other in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[other_index] + 1,
                    previous[other_index - 1] + (char != other),
                )
            )
        previous = current
    return previous[-1]


def _language_labels() -> dict[str, str]:
    labels = dict(_SPOKEN_ALIASES)
    for code, name in load_language_names().items():
        key = "".join(ch for ch in name.lower() if ch.isalpha())
        if key:
            labels.setdefault(key, code)
    return labels


def spoken_name_to_language(text: str) -> str | None:
    """Map a transcript to one ISO 639-1 code.

    Accented speech often misspells the language name ("nedlands" for
    Nederlands). Several different language names in one transcript is the
    recognizer repeating its hint list, not a choice.
    """
    tokens = [
        "".join(ch for ch in part.lower() if ch.isalpha())
        for part in text.replace(".", " ").split()
    ]
    tokens = [token for token in tokens if token]
    if not tokens:
        return None
    labels = _language_labels()
    found: list[str] = []
    for token in tokens:
        exact = labels.get(token)
        if exact:
            found.append(exact)
            continue
        if token in _DUTCH_TOKENS or token.startswith("neder"):
            found.append("nl")
            continue
        if len(token) < 6:
            continue
        best_code: str | None = None
        best_distance = 3
        for label, code in labels.items():
            if len(label) < 6 or abs(len(label) - len(token)) > 3:
                continue
            distance = _edit_distance(token, label)
            if distance < best_distance:
                best_distance = distance
                best_code = code
        if best_code is not None and best_distance <= 2:
            found.append(best_code)
    unique = list(dict.fromkeys(found))
    if len(unique) == 1:
        return unique[0]
    return None


def _trim_low_energy(pcm16: bytes, threshold: float = 250.0) -> bytes:
    frame_bytes = int(TWILIO_SAMPLE_RATE * 0.02) * 2
    frames = [pcm16[offset : offset + frame_bytes] for offset in range(0, len(pcm16), frame_bytes)]
    loud = [index for index, frame in enumerate(frames) if pcm16_rms(frame) >= threshold]
    if not loud:
        return pcm16
    return b"".join(frames[loud[0] : loud[-1] + 1])


def recognize_spoken_language_name(pcm16: bytes) -> str | None:
    """Transcribe a short language name. None when the transcript is not a language."""
    if not pcm16:
        return None
    from services.ivr.whisper_stt import _load_model

    trimmed = _trim_low_energy(pcm16)
    heard = ""
    try:
        audio = resample_pcm16(trimmed, TWILIO_SAMPLE_RATE, 16000)
        waveform = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        model = _load_model("tiny")
        options = {
            "language": None,
            "vad_filter": False,
            "beam_size": 5,
            "condition_on_previous_text": False,
            "hotwords": "English Nederlands Dutch Polish Urdu Punjabi Bengali",
        }
        try:
            segments, _info = model.transcribe(waveform, **options)
        except TypeError:
            options.pop("hotwords", None)
            segments, _info = model.transcribe(waveform, **options)
        heard = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception:
        logger.exception("Spoken language-name transcription failed")
    code = spoken_name_to_language(heard)
    logger.info("language_name heard=%r language=%s", heard, code)
    return code
