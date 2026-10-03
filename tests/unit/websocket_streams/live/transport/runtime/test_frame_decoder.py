"""Tests for live transport frame decoding."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # One test proves that a cut frame is malformed JSON.

import pytest  # The malformed JSON proof uses the standard exception helper.

from src.websocket_streams.live.transport.runtime.frame_decoder import FrameDecoder, SubscribeError


class TestFrameDecoder:
    """Verify outer and nested frame decoding."""

    def test_event_removes_nul_from_binary_json(self) -> None:
        """Remove NUL bytes before JSON decoding."""
        frame = b'\x00{"event": "data", "channel": "c", "data": "{}"}\x00'  # Binary frames can contain NUL bytes.
        expected = {"event": "data", "channel": "c", "data": "{}"}  # The decoded event stays unchanged.
        assert FrameDecoder.event(frame) == expected  # NUL bytes must not break JSON decoding.

    @pytest.mark.parametrize("frame", ["plain text", '{"event": "data", "data": '])
    def test_event_wraps_non_json_text(self, frame: str) -> None:
        """Wrap complete and cut non-JSON text as raw data."""
        if frame.startswith("{"):  # Prove that the cut object is invalid JSON.
            with pytest.raises(json.JSONDecodeError):  # The standard parser must reject the cut frame.
                json.loads(frame)  # Parse the incomplete JSON text.
        assert FrameDecoder.event(frame) == {"raw": frame}  # Preserve the prior SDK fallback shape.

    def test_event_empty_body_returns_raw_empty_text(self) -> None:
        """Preserve an empty frame body through the raw-data fallback."""
        assert FrameDecoder.event(b"") == {"raw": ""}  # Keep the empty-body result explicit for callers.

    def test_data_payload_decodes_json_text(self) -> None:
        """Decode JSON text inside a data event."""
        event = {"event": "data", "data": '{"session": "one", "raw": "show \\u2603"}'}  # Keep Unicode escaped.
        assert FrameDecoder.data_payload(event) == {"session": "one", "raw": "show \u2603"}  # Decode inner JSON.

    @pytest.mark.parametrize("payload", ["{broken", "", {"value": 1}])
    def test_data_payload_preserves_non_json_values(self, payload: object) -> None:
        """Preserve malformed, empty, and already decoded values."""
        assert FrameDecoder.data_payload({"data": payload}) == payload  # Keep the original edge value.

    def test_subscribe_error_keeps_fields(self) -> None:
        """Store the failed channel and detail."""
        error = SubscribeError("/channel", "timeout")  # Build one subscription timeout.
        assert (error.channel, error.detail) == ("/channel", "timeout")  # Preserve the public error fields.
