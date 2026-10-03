"""Tests for the WebSocket utility message filter."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import pytest  # The tests check contract refusals.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Bad answers raise this error.
from src.websocket_streams.live.runners.utility.filters.message_filter import UtilityMessageFilter  # Filter class.


class TestUtilityMessageFilter:
    """Verify command and capture message filtering."""

    def test_command_filter_holds_and_returns_matching_raw_text(self) -> None:
        """Keep early command events and return matching raw text only."""
        filterer = UtilityMessageFilter("cmd")  # Build a command filter.
        assert filterer.offer({"session": "other", "raw": "drop"}) == []  # Early events wait until bind.
        assert filterer.offer({"event": "data", "data": {"session": "cmd-a", "raw": "first"}}) == []  # Hold match.
        held = filterer.bind({"session": "cmd-a"})  # Bind to the trigger answer.
        assert held == ["first"]  # The held match returns in arrival order.
        assert filterer.offer({"session": "cmd-a", "raw": "unicode \u2603"}) == ["unicode \u2603"]  # Unicode stays.
        assert filterer.offer({"session": "other", "raw": "drop"}) == []  # Another session is dropped.

    def test_capture_filter_returns_full_matching_payload(self) -> None:
        """Return the full capture payload for a matching capture id."""
        filterer = UtilityMessageFilter("site_pcaps")  # Build a site capture filter.
        payload = {"capture_id": "cap-a", "pcap_dict": {"src_ip": "1.1.1.1"}}  # Build one packet payload.
        assert filterer.offer(payload) == []  # Early packet waits until bind.
        held = filterer.bind({"id": "cap-a"})  # Bind to the capture answer.
        assert held == [payload]  # The whole payload is returned.
        assert filterer.offer({"capture_id": "cap-b", "pcap_dict": {}}) == []  # Another capture is dropped.

    def test_bad_shapes_missing_values_and_drops(self) -> None:
        """Handle malformed payloads, missing values, and early overflow."""
        filterer = UtilityMessageFilter("cmd")  # Build a command filter.
        for index in range(2001):  # Fill one more than the early payload limit.
            assert filterer.offer({"session": "cmd-a", "raw": str(index)}) == []  # Early events return nothing.
        assert filterer.dropped_count == 1  # The filter counts the overflowed payload.
        held = filterer.bind({"session": "cmd-a"})  # Bind after overflow.
        assert len(held) == 2000  # The filter kept the configured maximum.
        assert filterer.offer("not-a-dict") == []  # Non-dictionary payloads are dropped.
        assert filterer.offer({"session": "cmd-a"}) == []  # Missing raw text is dropped.
        missing = UtilityMessageFilter("cmd")  # Build another command filter.
        with pytest.raises(StreamRequestError) as caught:  # Missing session values are bad requests.
            missing.bind({"id": "cap-a"})  # Bind with the wrong answer key.
        assert caught.value.code == "bad_request"  # The requested refusal code is used.

    def test_bad_channel_raises_bad_request(self) -> None:
        """Refuse unsupported filter channels."""
        with pytest.raises(StreamRequestError) as caught:  # URL sessions do not use message filtering.
            UtilityMessageFilter("url")  # Try an unsupported channel.
        assert caught.value.code == "bad_request"  # The requested refusal code is used.
