# Later

Work to do after the current phase. This list is a reminder, not a decision record.

## A recognizer that is both fast and accurate

Left for later. On this PC, local Whisper `tiny` is the only model quick enough for an IVR: about half a second after the caller stops. It is also weak at hearing what was said, including short words such as PIN. Whisper `small` heard those words more reliably and took about three seconds, which is too slow to leave on the call. Faster decode settings on `small` only moved a test sentence from 3.3 seconds to 3.0 seconds. There is a gap between the recognizer this IVR needs and the one that can run here. This phase keeps `tiny`.

When this is picked up, the replacement should still transcribe the whole sentence. Intent matching stays in the router. [ADR-014](adr/ADR-014.md) already leaves a swap behind `StreamingSpeechToText`. Deepgram is the paid phone engine named there. Send each finished utterance to that engine, do not write the audio to disk, and keep language selection and the intent router as they are. It needs an API key. Audio for the utterance leaves this machine for the length of that request. Phone noise, accents, and French, Hebrew, Arabic, and Swahili will keep missing turns until that exists.

## Language selection for every language

Left for later. Accurate selection across the full catalog, including accents and languages the caller says in their own wording, is a large task. Do not spend more time on it until the important work in the current phase is done.

What is in place now is enough to continue. A caller can say the English name of a catalog language, or one of a few native names such as Nederlands, Français, and Deutsch. A misspelling has to stay within two letters of a known name. Live calls have only confirmed English and Dutch, including an accented Dutch sentence heard as "Netherlands." If the name is not recognized, the acoustic model only accepts a language on that caller's menu, or a major language when it is confident. Short phone clips were often labeled as an unrelated language. The transcriber is hinted toward English, Dutch, Polish, Urdu, Punjabi, and Bengali, which helps that menu and makes other names less likely. Keypad selection still follows the menu for the caller's number.
