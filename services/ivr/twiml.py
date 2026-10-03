"""TwiML builders for Twilio Voice responses."""


def build_media_stream_connect_twiml(
    ws_url: str,
    *,
    caller_from: str | None = None,
    country_code: str | None = None,
) -> str:
    """Return TwiML that opens a bi-directional Media Stream with caller metadata."""
    parameters: list[str] = []
    if caller_from:
        parameters.append(
            f'            <Parameter name="from" value="{_xml_escape(caller_from)}" />'
        )
    if country_code:
        parameters.append(
            f'            <Parameter name="country_code" value="{_xml_escape(country_code)}" />'
        )

    parameter_block = ("\n" + "\n".join(parameters) + "\n") if parameters else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{_xml_escape(ws_url)}">{parameter_block}        </Stream>
    </Connect>
</Response>"""


# Silence after the rejection line, then Twilio hangs up.
REJECTION_HANGUP_PAUSE_S = 1


def build_not_recognised_twiml(*, text: str, say_language: str, hangup_url: str) -> str:
    """Speak the rejection, wait one second, then fetch a hangup document.

    ``<Hangup>`` in the first webhook response does not end this call: Twilio
    fetches that document while the call is still ringing. A later document
    whose only verb is ``<Hangup>`` runs after the call has been answered.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{_xml_escape(say_language)}">{_xml_escape(text)}</Say>
    <Pause length="{REJECTION_HANGUP_PAUSE_S}"></Pause>
    <Redirect method="POST">{_xml_escape(hangup_url)}</Redirect>
</Response>"""


def build_hangup_twiml() -> str:
    """Return a document that only hangs up."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Hangup></Hangup>
</Response>"""


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
