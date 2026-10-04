"""Tests for WebSockets message text helpers."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The malformed JSON test proves the input fails the standard decoder.
import logging  # The filter test builds a log record.

import pytest  # The malformed JSON test checks the decoder refusal.

from src.mist.realtime.websocket_streams.live.runners.text.messages import (
    MessageShaper,
)  # Test channel message shaping.
from src.mist.realtime.websocket_streams.live.runners.text.packets import PacketSummary  # Test packet summary shaping.
from src.mist.realtime.websocket_streams.live.runners.text.redaction import (
    ShellAddressFilter,
)  # Test address redaction.


class TestMessageText:
    """Verify channel, packet, and shell text helpers."""

    def test_channel_message_decodes_nested_data(self) -> None:
        """Decode a JSON string in the data field."""
        kind, content, source = MessageShaper().channel_message(
            {"channel": "/sites/site/stats", "data": '{"mac":"aa"}'}
        )  # Shape one channel event.
        assert kind == "json"  # Channel mappings render as JSON.
        assert content["data"] == {"mac": "aa"}  # The nested JSON string is decoded.
        assert source == "/sites/site/stats"  # The runner keeps the path private.

    def test_plain_channel_message_becomes_text(self) -> None:
        """Return plain text for non-mapping channel messages."""
        kind, content, source = MessageShaper().channel_message("hello")  # Shape one plain SDK message.
        assert kind == "text"  # Plain values render as text.
        assert content == "hello"  # The content is preserved.
        assert source is None  # Plain messages have no channel path.

    def test_bad_nested_data_stays_text(self) -> None:
        """Keep invalid nested JSON as text."""
        kind, content, _source = MessageShaper().channel_message({"data": "not json"})  # Shape invalid nested data.
        assert kind == "json"  # Mappings still render as JSON.
        assert content["data"] == "not json"  # Invalid JSON text stays unchanged.

    def test_cut_json_data_stays_text(self) -> None:
        """Keep a cut JSON object as text, and do not fail."""
        cut_json = '{"mac": "aa"'  # A JSON object without its end, as a cut frame can arrive.
        with pytest.raises(json.JSONDecodeError):  # Prove that the input is malformed JSON.
            json.loads(cut_json)  # The standard decoder refuses the cut object.
        kind, content, _source = MessageShaper().channel_message({"data": cut_json})  # Shape the malformed data.
        assert kind == "json"  # Mappings still render as JSON.
        assert content["data"] == cut_json  # The shaper keeps the malformed text unchanged.

    def test_empty_body_stays_empty(self) -> None:
        """Keep an empty channel body empty."""
        kind, content, _source = MessageShaper().channel_message(dict(data=""))  # Shape an empty body.
        assert kind == "json"  # Mappings still render as JSON.
        assert content["data"] == ""  # The empty body stays an empty string.

    def test_shaper_keeps_no_terminal_cleaner(self) -> None:
        """Prove that the shaper no longer removes terminal control codes (issue #3671)."""
        assert not hasattr(MessageShaper(), "clean_shell_text")  # xterm.js needs each raw control byte.

    def test_packet_summary_uses_dash_for_missing_fields(self) -> None:
        """Use dashes when packet fields are absent."""
        summary = PacketSummary.summarize(
            {"src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", "proto": "udp"}
        )  # Build one summary.
        assert summary == "- 1.1.1.1 -> 2.2.2.2 udp -"  # Missing time and length become dashes.

    def test_shell_address_filter_redacts_wss_address(self) -> None:
        """Redact WebSocket addresses from log records."""
        record = logging.LogRecord(
            "mistapi", logging.INFO, __file__, 1, "open wss://secret.example/path", (), None
        )  # Build one log record.
        assert ShellAddressFilter().filter(record) is True  # The filter keeps the record.
        assert record.getMessage() == "open wss://[redacted]"  # The address is redacted.
