# Later

Work to do after the current phase. This list is a reminder, not a decision record.

## A recognizer that is both fast and accurate

Left for later. On this PC, local Whisper `tiny` is the only model quick enough for an IVR: about half a second after the caller stops. It is also weak at hearing what was said, including short words such as PIN. Whisper `small` heard those words more reliably and took about three seconds, which is too slow to leave on the call. Faster decode settings on `small` only moved a test sentence from 3.3 seconds to 3.0 seconds. There is a gap between the recognizer this IVR needs and the one that can run here. This phase keeps `tiny`.

When this is picked up, the replacement should still transcribe the whole sentence. Intent matching stays in the router. [ADR-014](adr/ADR-014.md) already leaves a swap behind `StreamingSpeechToText`. Deepgram is the paid phone engine named there. Send each finished utterance to that engine, do not write the audio to disk, and keep language selection and the intent router as they are. It needs an API key. Audio for the utterance leaves this machine for the length of that request. Phone noise, accents, and French, Hebrew, Arabic, and Swahili will keep missing turns until that exists.

## Voices for French, Hebrew, Arabic, and Swahili on this PC

Not in this phase. [ADR-018](adr/ADR-018.md) and [ADR-022](adr/ADR-022.md) already say that a language with no matching voice plays the English line, not an English voice reading the other language. This PC's Windows voices are English only. A free online read-aloud path can speak some of the other languages and was not turned on. Hebrew and Swahili are not in that voice map. Do not test those languages by having the English voice read their text.
