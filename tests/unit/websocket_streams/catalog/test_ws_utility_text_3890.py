"""Tests for the DHCP release and MAC table purpose text.

Why:
    Issue #3890. The audit for issue #3862 found that the DHCP release forms
    did not name the valid SDK target sets or the state change. The MAC table
    form did not say that its filters are optional. These tests keep the text
    aligned with the installed SDK and prove that the safety stays unchanged.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import inspect  # Read the installed SDK docstrings.

import pytest  # Parametrize the three DHCP families.

from src.mist.realtime.websocket_streams.catalog.model import Safety  # Safety classes of the utilities.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
    UtilityCatalog,
)  # Read the installed SDK catalog.
from src.mist.realtime.websocket_streams.catalog.utility_text import UtilityText  # The class under test.

STATE_CHANGE = "This changes client state, so each client must ask for a new address."  # Required effect text.
EX_TARGETS = "Network and MAC addresses, Network and Port, or Port only."  # The three EX target sets.
# The five SRX and SSR target sets.
SRX_TARGETS = "Network only, Network and MAC addresses, Network and Port, Port only, or Port and MAC addresses."
DHCP_FIELDS = ("macs", "network", "node", "port_id")  # Fields before this change.
MAC_TABLE_FIELDS = ("mac_address", "port_id", "vlan_id")  # Fields before this change.


@pytest.fixture(scope="module")
def catalog() -> UtilityCatalog:
    """Return one catalog built from the installed SDK."""
    return UtilityCatalog()  # Discovery reads the installed mistapi package.


def sdk_sets(family: str) -> list[str]:
    """Return the valid target sets that the installed SDK docstring lists for one family."""
    import mistapi.device_utils as device_utils  # Read the installed SDK facade.

    doc = inspect.getdoc(getattr(device_utils, family).releaseDhcpLeases) or ""  # Read the SDK docstring.
    marker = "valid combinations for EX are:" if family == "ex" else "valid combinations for SRX / SSR are:"  # Header.
    section = doc.split(marker, 1)[1].split("\n\n", 1)[0]  # Keep the bullet list under the header.
    return [line.lstrip("- ").strip() for line in section.splitlines() if line.startswith("-")]  # One set per bullet.


class TestDhcpReleaseText:
    """Verify the DHCP release purpose text for each family."""

    @pytest.mark.parametrize(
        ("family", "device", "targets"),
        [
            ("ex", "an EX switch", EX_TARGETS),
            ("srx", "an SRX device", SRX_TARGETS),
            ("ssr", "an SSR device", SRX_TARGETS),
        ],
    )
    def test_text_names_the_device_effect_and_targets(
        self, catalog: UtilityCatalog, family: str, device: str, targets: str
    ) -> None:
        """Each family text names the device, the state change, and its own target sets."""
        expected = f"Release DHCP leases on {device}. {STATE_CHANGE} Use one of these target sets: {targets}"  # Text.
        assert catalog.get(f"{family}.releaseDhcpLeases").description == expected  # The full text matches.

    def test_ex_text_omits_the_targets_that_ex_rejects(self, catalog: UtilityCatalog) -> None:
        """The EX text never offers the SRX-only target sets."""
        text = catalog.get("ex.releaseDhcpLeases").description  # Read the EX text.
        assert "Network only" not in text  # The SDK rejects a network-only target on EX.
        assert "Port and MAC addresses" not in text  # The SDK rejects a port and MAC target on EX.

    def test_ex_sets_match_the_sdk_docstring(self) -> None:
        """The EX text follows the target sets in the installed SDK docstring."""
        assert sdk_sets("ex") == ["network + macs", "network + port_id", "port_id"]  # Three EX sets in the SDK.

    @pytest.mark.parametrize("family", ["srx", "ssr"])
    def test_srx_and_ssr_sets_match_the_sdk_docstring(self, family: str) -> None:
        """The SRX and SSR text follows the target sets in the installed SDK docstring."""
        expected = ["network", "network + macs", "network + port_id", "port_id", "port_id + macs"]  # SDK sets.
        assert sdk_sets(family) == expected  # The SDK still lists the five sets that the text names.

    @pytest.mark.parametrize("family", ["ex", "srx", "ssr"])
    def test_safety_and_fields_stay_unchanged(self, catalog: UtilityCatalog, family: str) -> None:
        """The text change keeps the change safety class and the SDK fields."""
        entry = catalog.get(f"{family}.releaseDhcpLeases")  # Read one DHCP entry.
        assert entry.safety is Safety.CHANGE  # The release still needs the change lock.
        assert tuple(field.name for field in entry.fields) == DHCP_FIELDS  # The fields stay unchanged.


class TestMacTableText:
    """Verify the MAC table purpose text."""

    def test_text_explains_the_optional_filters(self, catalog: UtilityCatalog) -> None:
        """The MAC table text states the full table and the optional MAC address filter."""
        expected = (
            "Get the MAC table from the switch. All filters are optional. Leave them empty to get the full table."
            " Type a MAC address, a port, or a VLAN ID to show fewer entries."
        )  # The required guidance.
        assert catalog.get("ex.retrieveMacTable").description == expected  # The full text matches.

    def test_safety_and_fields_stay_unchanged(self, catalog: UtilityCatalog) -> None:
        """The text change keeps the read safety class and the SDK fields."""
        entry = catalog.get("ex.retrieveMacTable")  # Read the MAC table entry.
        assert entry.safety is Safety.READ  # The MAC table stays a read utility.
        assert tuple(field.name for field in entry.fields) == MAC_TABLE_FIELDS  # The fields stay unchanged.

    def test_filters_are_optional_in_the_sdk(self) -> None:
        """The installed SDK gives each filter an empty default."""
        import mistapi.device_utils as device_utils  # Read the installed SDK facade.

        parameters = inspect.signature(device_utils.ex.retrieveMacTable).parameters  # Read the SDK signature.
        defaults = [parameters[name].default for name in ("mac_address", "port_id", "vlan_id")]  # Filter defaults.
        assert defaults == [None, None, None]  # Each filter is optional in the SDK.


class TestSentenceFallback:
    """Verify that other utilities keep their text."""

    def test_name_only_call_keeps_the_generic_dhcp_sentence(self) -> None:
        """A call without a utility key keeps the generic DHCP sentence."""
        expected = "Release DHCP leases on the device. Each client must then ask for a new address."  # Old text.
        assert UtilityText.sentence("releaseDhcpLeases", Safety.CHANGE) == expected  # The fallback stays.

    def test_unknown_key_keeps_the_generic_read_sentence(self) -> None:
        """An unknown utility key uses the shared read rule."""
        text = UtilityText.sentence("retrieveMacTable", Safety.READ, "future.retrieveMacTable")  # Unknown family.
        assert text == "Get the MAC table from the device."  # The shared rule still applies.

    def test_capture_text_stays_unchanged(self, catalog: UtilityCatalog) -> None:
        """A capture utility keeps the shared capture sentence."""
        expected = "Capture packets for 60 seconds and show each packet record."  # The shared capture text.
        assert catalog.get("ex.remotePcap").description == expected  # The capture text stays.
