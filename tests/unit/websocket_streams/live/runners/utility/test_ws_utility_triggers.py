"""Tests for the WebSocket utility trigger table."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import pytest  # The tests check contract refusals.

from src.mist.realtime.websocket_streams.catalog.model import Safety  # Tests filter shell catalog entries.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
    UtilityCatalog,
)  # Build real definitions.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Unknown keys raise this error.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Tests build checked start requests.
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.table import (
    UtilityTriggerTable,
)  # The table under test.


class TestUtilityTriggerTable:
    """Verify utility trigger request building."""

    SITE_ID = "11111111-2222-3333-4444-555555555555"  # Use a stable checked site identifier.
    DEVICE_ID = "00000000-0000-0000-1000-aabbccddeeff"  # Use a stable checked device identifier.
    ORG_ID = "99999999-8888-7777-6666-555555555555"  # Use a stable checked organization identifier.

    def test_keys_cover_non_shell_catalog_entries(self) -> None:
        """Return one trigger key for each non-shell catalog utility."""
        catalog_keys = tuple(
            entry.key for entry in UtilityCatalog().entries() if entry.safety is not Safety.SHELL
        )  # Shell uses a separate trigger helper.
        table = UtilityTriggerTable()  # Build the trigger table.
        assert table.keys() == catalog_keys  # The trigger table follows catalog order.

    def test_request_for_command_capture_screen_and_shell(self) -> None:
        """Build representative command, capture, screen, and shell requests."""
        table = UtilityTriggerTable()  # Build the trigger table.
        ping = table.request_for(self._request("ap.ping", {"host": "8.8.8.8"}))  # Build one command trigger.
        assert ping.path == f"/api/v1/sites/{self.SITE_ID}/devices/{self.DEVICE_ID}/ping"  # Command path matches SDK.
        assert ping.body == {"host": "8.8.8.8"}  # Command body matches SDK.
        assert ping.listen.channel_path == f"/sites/{self.SITE_ID}/devices/{self.DEVICE_ID}/cmd"  # Subscribe path.
        capture = table.request_for(
            self._request("ssr.remotePcap", {"port_ids": ["ge-0/0/1"], "tcpdump_expression": "icmp"})
        )  # Build one capture trigger.
        assert capture.body == {
            "duration": 60,
            "max_pkt_len": 512,
            "num_packets": 1024,
            "tcpdump_expression": "icmp",
            "gateways": {"aabbccddeeff": {"ports": {"ge-0/0/1": {}}}},
            "type": "gateway",
            "format": "stream",
            "raw": False,
        }  # SSR capture body matches SDK defaults.
        assert capture.listen.timing.total_seconds == 70.0  # Capture total time adds ten seconds.
        screen = table.request_for(self._request("ex.topCommand", {}))  # Build one screen trigger.
        assert screen.body is None  # The SDK top command sends no body.
        assert screen.listen.channel == "url"  # Screen commands listen through the returned URL.
        shell = table.shell_request(self.SITE_ID, self.DEVICE_ID)  # Build the shell trigger.
        assert shell.path == f"/api/v1/sites/{self.SITE_ID}/devices/{self.DEVICE_ID}/shell"  # Shell path matches SDK.
        assert shell.listen.channel_path == ""  # Shell sessions do not subscribe to a stream channel.

    def test_timing_uses_sdk_quiet_floor(self) -> None:
        """Keep SDK quiet values and enforce a five second floor."""
        table = UtilityTriggerTable()  # Build the trigger table.
        arp = table.request_for(self._request("ex.retrieveArpTable", {}))  # Build one short-quiet command.
        leases = table.request_for(
            self._request("ex.retrieveDhcpLeases", {"network": "corp"})
        )  # Build one long command.
        assert arp.listen.timing.first_output_seconds == 30.0  # First output timeout is fixed.
        assert arp.listen.timing.quiet_seconds == 5.0  # A one second SDK quiet value becomes five.
        assert arp.listen.timing.total_seconds == 60.0  # Commands use the SDK total limit.
        assert leases.listen.timing.quiet_seconds == 15.0  # A long SDK quiet value is preserved.

    def test_unknown_key_raises_bad_request(self) -> None:
        """Refuse a key that is not in the trigger table."""
        table = UtilityTriggerTable()  # Build the trigger table.
        with pytest.raises(StreamRequestError) as caught:  # Unknown keys use a contract error.
            table.request_for(self._request("ex.createShellSession", {}))  # Shell uses shell_request instead.
        assert caught.value.code == "bad_request"  # The requested refusal code is used.

    def _request(self, key: str, parameters: dict[str, object]) -> StartRequest:
        """Build a checked start request for one catalog key.

        Args:
            key: The utility catalog key.
            parameters: The checked parameters.

        Returns:
            A checked start request.
        """
        definition = UtilityCatalog().get(key)  # Read the real catalog definition.
        if definition is None:  # Test setup must use a real key.
            raise RuntimeError(f"Missing catalog entry {key}")  # Fail the test with evidence.
        targets = {
            "org_id": (self.ORG_ID,),
            "site_id": (self.SITE_ID,),
            "device_id": (self.DEVICE_ID,),
            "mxedge_id": (self.DEVICE_ID,),
        }  # Provide every target that table paths can need.
        return StartRequest("utility", definition, targets, parameters, "Utility")  # Return a checked request.
