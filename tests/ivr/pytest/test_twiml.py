from services.ivr.twiml import (
    build_hangup_twiml,
    build_media_stream_connect_twiml,
    build_not_recognised_twiml,
)


def test_build_media_stream_connect_twiml_includes_stream_url():
    twiml = build_media_stream_connect_twiml("wss://example.com/media-stream")
    assert "<Stream url=" in twiml
    assert "wss://example.com/media-stream" in twiml
    assert "<Connect>" in twiml
    assert "Connecting to Customer Support" not in twiml


def test_build_media_stream_connect_twiml_includes_caller_parameters():
    twiml = build_media_stream_connect_twiml(
        "wss://example.com/media-stream",
        caller_from="+972501234567",
        country_code="IL",
    )
    assert 'name="from" value="+972501234567"' in twiml
    assert 'name="country_code" value="IL"' in twiml


def test_build_not_recognised_twiml_says_then_redirects_without_a_stream():
    twiml = build_not_recognised_twiml(
        text="This number is not recognised.",
        say_language="en-US",
        hangup_url="https://example.com/voice/hangup",
    )
    assert "<Say language=\"en-US\">This number is not recognised.</Say>" in twiml
    say_at = twiml.index("<Say ")
    pause_at = twiml.index('<Pause length="1"></Pause>')
    redirect_at = twiml.index('<Redirect method="POST">https://example.com/voice/hangup</Redirect>')
    assert say_at < pause_at < redirect_at
    assert "<Hangup" not in twiml
    assert "<Connect>" not in twiml
    assert "<Stream" not in twiml


def test_build_hangup_twiml_is_only_hangup():
    twiml = build_hangup_twiml()
    assert "<Hangup></Hangup>" in twiml
    assert "<Say" not in twiml
    assert "<Connect>" not in twiml


def test_build_media_stream_connect_twiml_escapes_xml_special_chars():
    twiml = build_media_stream_connect_twiml(
        'wss://example.com/media-stream?a="b"',
        caller_from='+1"<>&',
    )
    assert "&quot;" in twiml
    assert "&lt;" in twiml
    assert "&amp;" in twiml
