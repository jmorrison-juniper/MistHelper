"""Unit tests for PromptNetworkDeviceUtils (src/device/prompt_utils.py).

Tests cover private helpers (pure logic) and API-calling public methods
(using unittest.mock.patch to isolate from real network calls):
_expand_index_range, _collect_selected_indices, _parse_port_indices,
_build_port_to_config_map, _filter_and_sort_ports, _build_port_stat_from_config,
_format_speed, _format_duplex, _handle_all_ports_selection, _find_device_by_mac,
_fetch_port_stats, _fetch_port_config, _build_port_table, _prompt_port_selection,
select_ap_mac, select_gateway_mac, select_switch_mac, select_ports_from_device.
"""

from __future__ import annotations  # Enable PEP 604 union types on Python 3.10+

from unittest.mock import MagicMock, patch  # Mock API session, injected callables, and mistapi module

from src.device.prompt_utils import PromptNetworkDeviceUtils  # Class under test

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_utils(expand_fn=None):  # Factory for instances with injectable mocks
    """Return a PromptNetworkDeviceUtils wired with minimal mocked dependencies."""
    session = MagicMock()  # Unused in pure-logic tests -- just satisfies the constructor
    safe_input = MagicMock(return_value="")  # Default: user presses Enter with no input
    if expand_fn is None:  # Default expander: return the key as a single-element list
        expand_fn = lambda key: [key]  # noqa: E731  -- simple identity for unit tests
    return PromptNetworkDeviceUtils(session, safe_input, expand_fn)  # Instantiate with mocks


# ---------------------------------------------------------------------------
# _expand_index_range
# ---------------------------------------------------------------------------


class TestExpandIndexRange:
    """Tests for _expand_index_range -- range token expansion."""

    def test_valid_range_all_in_map(self):  # Happy path: '1-3' with all indices present
        """Expanding '1-3' when 1, 2, 3 are all valid returns {1, 2, 3}."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port = {0: "ge-0", 1: "ge-1", 2: "ge-2", 3: "ge-3"}  # Four valid indices
        result = utils._expand_index_range("1-3", index_to_port)  # Expand range 1 through 3
        assert result == {1, 2, 3}  # All three indices should be returned

    def test_valid_range_partial_in_map(self, capsys):  # Warning path: some out of range
        """Out-of-range indices within a range are warned and skipped."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port = {0: "ge-0", 1: "ge-1"}  # Only indices 0 and 1 are valid
        result = utils._expand_index_range("0-3", index_to_port)  # Range includes invalid 2 and 3
        assert result == {0, 1}  # Only valid indices should be returned
        out = capsys.readouterr().out  # Capture printed warnings
        assert "out of range" in out  # Warning should be printed for invalid indices

    def test_malformed_range_too_many_parts(self):  # Edge case: '1-2-3'
        """A range token with more than one hyphen returns an empty set."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._expand_index_range("1-2-3", {0: "ge-0", 1: "ge-1", 2: "ge-2"})  # Ambiguous range
        assert result == set()  # Malformed range should produce no indices

    def test_single_element_range(self):  # Edge case: '2-2' is a valid single-element range
        """A start == end range returns a single-element set."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port = {2: "ge-2"}  # Only index 2 exists
        result = utils._expand_index_range("2-2", index_to_port)  # Degenerate range
        assert result == {2}  # Should still return the single index


# ---------------------------------------------------------------------------
# _collect_selected_indices
# ---------------------------------------------------------------------------


class TestCollectSelectedIndices:
    """Tests for _collect_selected_indices -- comma-and-range parser."""

    def _default_map(self):  # Shared index map for most tests
        """Return a standard 5-entry index-to-port mapping."""
        return {0: "ge-0", 1: "ge-1", 2: "ge-2", 3: "ge-3", 4: "ge-4"}  # Ports 0..4

    def test_single_valid_index(self):  # "0" -> {0}
        """A single valid numeric index returns a one-element set."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("0", self._default_map())  # Parse single index
        assert result == {0}  # Should return the index

    def test_multiple_comma_separated(self):  # "0,2,4" -> {0, 2, 4}
        """Comma-separated valid indices return all of them as a set."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("0,2,4", self._default_map())  # Parse three indices
        assert result == {0, 2, 4}  # All three should be returned

    def test_range_input(self):  # "1-3" -> {1, 2, 3}
        """A range notation input returns the expanded indices."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("1-3", self._default_map())  # Parse range
        assert result == {1, 2, 3}  # Range 1 through 3

    def test_mixed_single_and_range(self):  # "0,2-4" -> {0, 2, 3, 4}
        """Mixed single index and range in one input returns the union."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("0,2-4", self._default_map())  # Mixed format
        assert result == {0, 2, 3, 4}  # Union of single and range

    def test_non_numeric_returns_none(self, capsys):  # "abc" -> None
        """Non-numeric input triggers ValueError and returns None."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("abc", self._default_map())  # Parse garbage
        assert result is None  # Parse failure should return None
        out = capsys.readouterr().out  # Check error message was printed
        assert "Invalid input" in out  # Error message should be printed

    def test_out_of_range_single(self, capsys):  # "99" with map 0..4 -> {}
        """An out-of-range single index is skipped and returns an empty set."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("99", self._default_map())  # Out-of-range index
        assert result == set()  # No valid indices -- empty set (not None)
        out = capsys.readouterr().out  # Warning should be printed
        assert "out of range" in out  # Warning message should appear

    def test_deduplication(self):  # "0,0,0" -> {0}
        """Duplicate indices are deduplicated in the returned set."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._collect_selected_indices("0,0,0", self._default_map())  # Repeated index
        assert result == {0}  # Should only appear once


# ---------------------------------------------------------------------------
# _parse_port_indices
# ---------------------------------------------------------------------------


class TestParsePortIndices:
    """Tests for _parse_port_indices -- top-level dispatcher with 6-port limit."""

    def _map_5(self):  # Helper: 5-port map
        """Return a 5-entry index-to-port mapping and matching available_ports list."""
        index_to_port = {i: f"ge-0/0/{i}" for i in range(5)}  # ge-0/0/0 through ge-0/0/4
        available_ports = [(f"ge-0/0/{i}", {"up": True}) for i in range(5)]  # Matching list
        return index_to_port, available_ports  # Both structures for use in tests

    def test_single_index_returns_list(self):  # "0" -> ["ge-0/0/0"]
        """Single valid index returns a one-element list."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port, available_ports = self._map_5()  # Get test structures
        result = utils._parse_port_indices("0", index_to_port, False, available_ports)  # Parse "0"
        assert result == ["ge-0/0/0"]  # First port by index

    def test_too_many_ports_returns_none(self, capsys):  # 7 ports exceeds API limit
        """Selecting more than 6 ports returns None and prints an error."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port = {i: f"ge-0/0/{i}" for i in range(10)}  # 10-port map
        available_ports = [(f"ge-0/0/{i}", {"up": True}) for i in range(10)]  # 10 ports
        result = utils._parse_port_indices("0-6", index_to_port, False, available_ports)  # 7 ports
        assert result is None  # Should reject -- exceeds 6-port API limit
        out = capsys.readouterr().out  # Check error message
        assert "maximum is 6 ports" in out  # Error message should mention the limit

    def test_return_available_flag(self):  # When return_available=True, return tuple
        """With return_available=True the result is (selected_ports, available_ports)."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port, available_ports = self._map_5()  # Get test structures
        result = utils._parse_port_indices("0", index_to_port, True, available_ports)  # With flag
        assert isinstance(result, tuple)  # Should be a tuple
        assert result[0] == ["ge-0/0/0"]  # First element: selected ports
        assert result[1] == available_ports  # Second element: full available list

    def test_invalid_input_returns_none(self, capsys):  # "xyz" -> None
        """Non-parseable input returns None."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port, available_ports = self._map_5()  # Get test structures
        result = utils._parse_port_indices("xyz", index_to_port, False, available_ports)  # Invalid
        assert result is None  # Parse error should return None

    def test_no_valid_indices_returns_none(self, capsys):  # All out of range
        """Input that maps to no valid indices returns None."""
        utils = _make_utils()  # Create instance with default mocks
        index_to_port, available_ports = self._map_5()  # Get test structures
        result = utils._parse_port_indices("99", index_to_port, False, available_ports)  # Out-of-range
        assert result is None  # Nothing selected


# ---------------------------------------------------------------------------
# _build_port_to_config_map
# ---------------------------------------------------------------------------


class TestBuildPortToConfigMap:
    """Tests for _build_port_to_config_map -- range-key expansion."""

    def test_identity_single_port(self):  # Non-range key maps to itself
        """A non-range key is passed through the expander as-is."""
        utils = _make_utils(expand_fn=lambda key: [key])  # Identity expander
        port_config = {"ge-0/0/0": {"speed": "1G"}}  # Single port config
        result = utils._build_port_to_config_map(port_config)  # Build map
        assert result == {"ge-0/0/0": {"speed": "1G"}}  # Should map the single port

    def test_range_key_expands_to_multiple(self):  # Range key maps to many
        """A range key is expanded to all individual ports by the expander."""
        expanded = ["ge-0/0/0", "ge-0/0/1", "ge-0/0/2"]  # Simulate range expansion
        utils = _make_utils(expand_fn=lambda key: expanded)  # Always expand to 3 ports
        port_config = {"ge-0/0/0-2": {"speed": "1G"}}  # Range key config
        result = utils._build_port_to_config_map(port_config)  # Build map
        assert len(result) == 3  # All 3 ports should be in the map
        assert result["ge-0/0/1"] == {"speed": "1G"}  # Each port gets the same config dict

    def test_empty_config_returns_empty_map(self):  # No config -> empty map
        """An empty port_config returns an empty dict."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._build_port_to_config_map({})  # Empty input
        assert result == {}  # Should produce empty map


# ---------------------------------------------------------------------------
# _filter_and_sort_ports
# ---------------------------------------------------------------------------


class TestFilterAndSortPorts:
    """Tests for _filter_and_sort_ports -- exclusion and natural sort."""

    def test_management_ports_excluded(self):  # fxp/em/me ports stripped
        """Management interface prefixes are excluded from results."""
        utils = _make_utils()  # Create instance with default mocks
        port_stat = {
            "ge-0/0/0": {"up": True},  # Should be included
            "fxp0": {"up": True},  # Management -- must be excluded
            "em0": {"up": True},  # Management -- must be excluded
        }
        result = utils._filter_and_sort_ports(port_stat)  # Filter and sort
        names = [name for name, _ in result]  # Extract just the port names
        assert "fxp0" not in names  # Management port excluded
        assert "em0" not in names  # Management port excluded
        assert "ge-0/0/0" in names  # User port included

    def test_down_ports_excluded(self):  # DOWN ports stripped
        """Ports with up=False are excluded."""
        utils = _make_utils()  # Create instance with default mocks
        port_stat = {
            "ge-0/0/0": {"up": True},  # UP -- include
            "ge-0/0/1": {"up": False},  # DOWN -- exclude
        }
        result = utils._filter_and_sort_ports(port_stat)  # Filter and sort
        names = [name for name, _ in result]  # Extract port names
        assert "ge-0/0/1" not in names  # DOWN port excluded
        assert "ge-0/0/0" in names  # UP port included

    def test_natural_sort_order(self):  # ge-0/0/10 after ge-0/0/9
        """Ports are sorted in natural (human) order, not lexicographic order."""
        utils = _make_utils()  # Create instance with default mocks
        port_stat = {
            "ge-0/0/10": {"up": True},  # Lexicographic: comes before ge-0/0/9
            "ge-0/0/9": {"up": True},  # Natural sort: comes before ge-0/0/10
            "ge-0/0/1": {"up": True},  # Natural sort: comes first
        }
        result = utils._filter_and_sort_ports(port_stat)  # Filter and sort
        names = [name for name, _ in result]  # Extract sorted names
        assert names == ["ge-0/0/1", "ge-0/0/9", "ge-0/0/10"]  # Natural sort order


# ---------------------------------------------------------------------------
# _build_port_stat_from_config
# ---------------------------------------------------------------------------


class TestBuildPortStatFromConfig:
    """Tests for _build_port_stat_from_config -- offline device fallback."""

    def test_empty_config_returns_none(self, capsys):  # No config -- nothing to show
        """An empty port_config returns None (nothing to display)."""

        def expand(key):  # Expander that returns empty list for empty config
            """Return empty list for any port range key."""
            return []  # No ports from empty config

        utils = _make_utils(expand_fn=expand)  # Instance with minimal expander
        result = utils._build_port_stat_from_config({}, "dev1", "switch", "SW-1")  # Empty config
        assert result is None  # Should return None -- nothing to show

    def test_normal_config_builds_stat(self):  # Config -> synthetic stat
        """A populated port_config produces a synthetic port_stat dict."""
        expanded_ports = ["ge-0/0/0"]  # Single port from range expansion

        def expand(key):  # Expander that always returns one port
            """Always expand to the single test port."""
            return expanded_ports  # Fixed expansion for test

        utils = _make_utils(expand_fn=expand)  # Instance with controlled expander
        port_config = {"ge-0/0/0": {"usage": "access", "speed": "1G", "duplex": "full"}}  # Normal config
        result = utils._build_port_stat_from_config(port_config, "dev1", "switch", "SW-1")  # Build stat
        assert result is not None  # Should produce a stat dict
        assert "ge-0/0/0" in result  # Port should be present
        assert result["ge-0/0/0"]["up"] is True  # 'access' usage means port is UP
        assert result["ge-0/0/0"]["_fallback"] is True  # Fallback flag must be set

    def test_disabled_usage_marks_port_down(self):  # disabled -> not up
        """A port with usage='disabled' is marked as not up in the synthetic stat."""

        def expand(key):  # Expander returning one port
            """Always expand to the test port."""
            return ["ge-0/0/0"]  # Fixed expansion

        utils = _make_utils(expand_fn=expand)  # Instance with controlled expander
        port_config = {"ge-0/0/0": {"usage": "disabled"}}  # Disabled usage profile
        result = utils._build_port_stat_from_config(port_config, "dev1", "switch", "SW-1")  # Build
        assert result is not None  # Should produce a stat dict
        assert result["ge-0/0/0"]["up"] is False  # 'disabled' usage means port is DOWN

    def test_exception_in_config_parsing_returns_none(self, capsys):  # lines 550-554 path
        """Returns None when port_config is None, triggering the except Exception handler."""
        utils = _make_utils()  # Create instance -- default expand_fn not needed here
        result = utils._build_port_stat_from_config(None, "dev1", "switch", "SW-1")  # None -> AttributeError
        assert result is None  # Exception swallowed -- returns None
        out = capsys.readouterr().out  # Capture output
        assert "No port information" in out  # User-facing error message should be printed


# ---------------------------------------------------------------------------
# _format_speed (static)
# ---------------------------------------------------------------------------


class TestFormatSpeed:
    """Tests for the _format_speed static method."""

    def test_gigabit_string(self):  # '1G' -> '1000 Mbps'
        """'1G' is converted to '1000 Mbps'."""
        assert PromptNetworkDeviceUtils._format_speed("1G") == "1000 Mbps"  # 1 Gbps

    def test_ten_gigabit_string(self):  # '10G' -> '10000 Mbps'
        """'10G' is converted to '10000 Mbps'."""
        assert PromptNetworkDeviceUtils._format_speed("10G") == "10000 Mbps"  # 10 Gbps

    def test_auto_string(self):  # 'auto' -> 'Auto'
        """'auto' returns 'Auto'."""
        assert PromptNetworkDeviceUtils._format_speed("auto") == "Auto"  # Auto-negotiated

    def test_numeric_mbps(self):  # 1000 (int) -> '1000 Mbps'
        """A positive integer is formatted as '<N> Mbps'."""
        assert PromptNetworkDeviceUtils._format_speed(1000) == "1000 Mbps"  # Numeric Mbps

    def test_unknown_returns_na(self):  # 0 or None -> 'N/A'
        """Zero or unknown values return 'N/A'."""
        assert PromptNetworkDeviceUtils._format_speed(0) == "N/A"  # Zero speed

    def test_invalid_g_suffix_falls_back_to_raw(self):  # '1.5G' -> int('1.5') raises ValueError
        """A 'G'-suffixed string with non-integer prefix falls back to the raw value."""
        result = PromptNetworkDeviceUtils._format_speed("1.5G")  # '1.5' is not int-parseable
        assert result == "1.5G"  # ValueError caught -- raw value returned as-is


# ---------------------------------------------------------------------------
# _format_duplex (static)
# ---------------------------------------------------------------------------


class TestFormatDuplex:
    """Tests for the _format_duplex static method."""

    def test_full_string(self):  # 'full' -> 'Full'
        """'full' string returns 'Full'."""
        assert PromptNetworkDeviceUtils._format_duplex("full", False) == "Full"  # Explicit full

    def test_half_string(self):  # 'half' -> 'Half'
        """'half' string returns 'Half'."""
        assert PromptNetworkDeviceUtils._format_duplex("half", True) == "Half"  # Explicit half

    def test_auto_string(self):  # 'auto' -> 'Auto'
        """'auto' string returns 'Auto'."""
        assert PromptNetworkDeviceUtils._format_duplex("auto", False) == "Auto"  # Auto-negotiated

    def test_empty_string_bool_fallback_full(self):  # empty + True -> 'Full'
        """Empty string falls back to full_duplex_flag=True -> 'Full'."""
        assert PromptNetworkDeviceUtils._format_duplex("", True) == "Full"  # Bool flag True

    def test_empty_string_bool_fallback_half(self):  # empty + False -> 'Half'
        """Empty string falls back to full_duplex_flag=False -> 'Half'."""
        assert PromptNetworkDeviceUtils._format_duplex("", False) == "Half"  # Bool flag False


# ---------------------------------------------------------------------------
# _handle_all_ports_selection
# ---------------------------------------------------------------------------


class TestHandleAllPortsSelection:
    """Tests for _handle_all_ports_selection -- all-ports sentinel handling."""

    def _make_ports(self, count: int):  # Helper: make a list of N port tuples
        """Return a list of N (port_name, port_info) tuples."""
        return [(f"ge-0/0/{i}", {"up": True}) for i in range(count)]  # N ports

    def test_within_limit_returns_empty_list(self):  # <= 6 ports -> []
        """Selecting all ports within the 6-port limit returns an empty list sentinel."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._handle_all_ports_selection(self._make_ports(4), False)  # 4 ports, no return_available
        assert result == []  # Empty list is the 'all ports' sentinel

    def test_exceeds_limit_returns_none(self, capsys):  # > 6 ports -> None
        """Selecting all ports when > 6 available returns None."""
        utils = _make_utils()  # Create instance with default mocks
        result = utils._handle_all_ports_selection(self._make_ports(7), False)  # 7 ports -- over limit
        assert result is None  # Should reject -- exceeds 6-port API limit
        out = capsys.readouterr().out  # Check error message
        assert "API maximum" in out or "6 port" in out  # Error message should reference limit

    def test_return_available_flag(self):  # return_available=True -> ([], ports)
        """With return_available=True returns a tuple ([], available_ports)."""
        utils = _make_utils()  # Create instance with default mocks
        ports = self._make_ports(3)  # 3 ports -- within limit
        result = utils._handle_all_ports_selection(ports, True)  # With flag
        assert isinstance(result, tuple)  # Should return a tuple
        assert result[0] == []  # Sentinel empty list
        assert result[1] == ports  # Full available port list


# ---------------------------------------------------------------------------
# Helpers shared by API-mock test classes
# ---------------------------------------------------------------------------


def _mock_list_response(data: list) -> MagicMock:  # Build a minimal API response mock
    """Return a MagicMock whose .data attribute holds the given list."""
    response = MagicMock()  # Fake mistapi response object
    response.data = data  # Set .data so callers can do response.data as normal
    return response  # Caller uses this as the return_value of listSiteDevices


def _make_ap(index: int = 0) -> dict:  # Build a minimal AP dict for test data
    """Return a minimal AP device dict with predictable test values."""
    return {  # Minimal fields that select_ap_mac / select_gateway_mac / select_switch_mac inspect
        "name": f"AP-{index}",  # Human-readable name
        "mac": f"aa:bb:cc:dd:ee:{index:02x}",  # Unique MAC per index
        "model": "AP43",  # Hardware model
        "status": "connected",  # Online status
    }


def _make_switch(index: int = 0) -> dict:  # Build a minimal switch dict
    """Return a minimal switch device dict with predictable test values."""
    return {  # Minimal fields needed by select_switch_mac
        "name": f"SW-{index}",  # Human-readable name
        "mac": f"11:22:33:44:55:{index:02x}",  # Unique MAC per index
        "model": "EX2300-24P",  # Hardware model
        "status": "connected",  # Online status
    }


# ---------------------------------------------------------------------------
# _find_device_by_mac
# ---------------------------------------------------------------------------


class TestFindDeviceByMac:
    """Tests for _find_device_by_mac -- normalised MAC matching."""

    def test_match_with_colons(self):  # Happy path: colon-formatted MAC in device list
        """Device with colon-formatted MAC matches normalised target."""
        utils = _make_utils()  # Create instance with mocked session
        devices = [{"name": "SW1", "mac": "aa:bb:cc:dd:ee:ff", "id": "dev-1"}]  # One device
        result = utils._find_device_by_mac(devices, "aabbccddeeff", "aa:bb:cc:dd:ee:ff")  # Normalised target
        assert result == devices[0]  # Should return the matching dict

    def test_match_without_colons(self):  # Device MAC stored without colons
        """Device with colon-less MAC still matches normalised target."""
        utils = _make_utils()  # Create instance with mocked session
        devices = [{"name": "SW1", "mac": "aabbccddeeff", "id": "dev-1"}]  # No colons in stored MAC
        result = utils._find_device_by_mac(devices, "aabbccddeeff", "aabbccddeeff")  # Target without colons
        assert result == devices[0]  # Should still match after normalisation

    def test_no_match_returns_none(self):  # Target not in device list
        """Returns None when no device MAC matches the normalised target."""
        utils = _make_utils()  # Create instance with mocked session
        devices = [{"name": "SW1", "mac": "aa:bb:cc:dd:ee:ff", "id": "dev-1"}]  # Different MAC
        result = utils._find_device_by_mac(devices, "112233445566", "11:22:33:44:55:66")  # Unrelated MAC
        assert result is None  # Not found -- should return None

    def test_empty_device_list_returns_none(self):  # Empty inventory
        """Returns None when the device list is empty."""
        utils = _make_utils()  # Create instance with mocked session
        result = utils._find_device_by_mac([], "aabbccddeeff", "aa:bb:cc:dd:ee:ff")  # Empty list
        assert result is None  # Nothing to match


# ---------------------------------------------------------------------------
# select_ap_mac
# ---------------------------------------------------------------------------


class TestSelectApMac:
    """Tests for select_ap_mac -- AP selection with mocked Mist API."""

    def test_empty_ap_list_returns_none(self, capsys):  # No APs at site
        """Returns None and prints a warning when no APs are returned."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([])  # Empty
            result = utils.select_ap_mac("site-1")  # Invoke with a fake site ID
        assert result is None  # No APs available -- return None
        out = capsys.readouterr().out  # Capture printed output
        assert "No APs" in out  # User should see a helpful message

    def test_all_input_returns_sentinel(self):  # User types 'all'
        """Returns 'ALL_APS' sentinel when user enters 'all'."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="all")  # Simulate user typing 'all'
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_ap(0)]  # One AP in the list
            )
            result = utils.select_ap_mac("site-1")  # Invoke
        assert result == "ALL_APS"  # Sentinel for multi-AP mode

    def test_valid_index_returns_mac(self):  # User picks index 0
        """Returns the AP MAC when user enters a valid numeric index."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="0")  # User selects first AP
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_ap(0)]  # One AP: mac = 'aa:bb:cc:dd:ee:00'
            )
            result = utils.select_ap_mac("site-1")  # Invoke
        assert result == "aa:bb:cc:dd:ee:00"  # Index 0 maps to the first AP's MAC

    def test_invalid_index_returns_none(self, capsys):  # User enters out-of-range index
        """Returns None when user enters a numeric index that is out of range."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="99")  # Index 99 -- beyond list length
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_ap(0)]  # Only one AP (index 0 is valid)
            )
            result = utils.select_ap_mac("site-1")  # Invoke
        assert result is None  # Invalid index -- return None
        out = capsys.readouterr().out  # Capture printed output
        assert "Invalid" in out  # User should see an error message

    def test_non_digit_input_returns_none(self, capsys):  # User enters non-numeric text
        """Returns None when user enters a non-numeric string that is not 'all'."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="abc")  # Non-numeric, non-'all' input
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_ap(0)]  # One AP available
            )
            result = utils.select_ap_mac("site-1")  # Invoke
        assert result is None  # Bad input -- return None
        out = capsys.readouterr().out  # Capture printed output
        assert "valid" in out  # User should see a helpful error

    def test_api_exception_returns_none(self, capsys):  # API call raises
        """Returns None and prints an error when the Mist API raises an exception."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("timeout")  # API fails
            result = utils.select_ap_mac("site-1")  # Invoke
        assert result is None  # Exception handled gracefully -- return None
        out = capsys.readouterr().out  # Capture printed output
        assert "Error" in out  # User should see an error message


# ---------------------------------------------------------------------------
# select_gateway_mac
# ---------------------------------------------------------------------------


class TestSelectGatewayMac:
    """Tests for select_gateway_mac -- gateway selection with mocked Mist API."""

    def test_empty_list_returns_none(self, capsys):  # No gateways at site
        """Returns None when no gateways are returned from the API."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([])  # Empty
            result = utils.select_gateway_mac("site-1")  # Invoke
        assert result is None  # No gateways -- return None
        out = capsys.readouterr().out  # Capture output
        assert "No gateways" in out  # Warning should be shown

    def test_valid_index_returns_mac(self):  # User picks index 0
        """Returns the gateway MAC when user enters a valid index."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="0")  # User selects index 0
        gw = {"name": "GW-1", "mac": "de:ad:be:ef:00:01", "model": "SRX300", "status": "connected"}  # One gateway
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([gw])  # One GW
            result = utils.select_gateway_mac("site-1")  # Invoke
        assert result == "de:ad:be:ef:00:01"  # Should return gateway MAC

    def test_invalid_index_returns_none(self, capsys):  # Out-of-range
        """Returns None when user enters an out-of-range index."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="5")  # No index 5 in a 1-item list
        gw = {"name": "GW-1", "mac": "de:ad:be:ef:00:01", "model": "SRX300", "status": "connected"}  # One GW
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([gw])  # One GW
            result = utils.select_gateway_mac("site-1")  # Invoke
        assert result is None  # Bad index -- return None

    def test_api_exception_returns_none(self, capsys):  # API raises
        """Returns None when the Mist API raises an exception."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("down")  # API fails
            result = utils.select_gateway_mac("site-1")  # Invoke
        assert result is None  # Exception handled -- return None

    def test_non_digit_input_returns_none(self, capsys):  # Non-numeric input
        """Returns None when user enters a non-numeric string."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="xyz")  # Non-numeric input
        gw = {"name": "GW-1", "mac": "de:ad:be:ef:00:01", "model": "SRX300", "status": "connected"}  # One GW
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([gw])  # One GW
            result = utils.select_gateway_mac("site-1")  # Invoke
        assert result is None  # Non-digit input not accepted


# ---------------------------------------------------------------------------
# select_switch_mac
# ---------------------------------------------------------------------------


class TestSelectSwitchMac:
    """Tests for select_switch_mac -- switch selection with mocked Mist API."""

    def test_empty_list_returns_none(self, capsys):  # No switches at site
        """Returns None when no switches are returned from the API."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([])  # Empty
            result = utils.select_switch_mac("site-1")  # Invoke
        assert result is None  # No switches -- return None
        out = capsys.readouterr().out  # Capture output
        assert "No switches" in out  # Warning should be shown

    def test_valid_index_returns_mac(self):  # User picks index 0
        """Returns the switch MAC when user enters a valid index."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="0")  # User selects index 0
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_switch(0)]  # One switch
            )
            result = utils.select_switch_mac("site-1")  # Invoke
        assert result == "11:22:33:44:55:00"  # Index 0 maps to first switch MAC

    def test_invalid_index_returns_none(self, capsys):  # Out-of-range
        """Returns None when user enters an out-of-range index."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="10")  # Index 10 -- out of range
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_switch(0)]  # Only one switch (index 0 valid)
            )
            result = utils.select_switch_mac("site-1")  # Invoke
        assert result is None  # Invalid index -- return None

    def test_api_exception_returns_none(self, capsys):  # API raises
        """Returns None when the Mist API raises an exception."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("timeout")  # API fails
            result = utils.select_switch_mac("site-1")  # Invoke
        assert result is None  # Exception handled -- return None

    def test_non_digit_input_returns_none(self, capsys):  # Non-numeric input
        """Returns None when user enters a non-numeric string."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="??")  # Non-numeric input
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [_make_switch(0)]  # One switch available
            )
            result = utils.select_switch_mac("site-1")  # Invoke
        assert result is None  # Non-digit not accepted


# ---------------------------------------------------------------------------
# _fetch_port_stats
# ---------------------------------------------------------------------------


class TestFetchPortStats:
    """Tests for _fetch_port_stats -- per-port status retrieval."""

    def test_switch_happy_path_builds_dict(self):  # Switch/gateway path via searchSiteSwOrGwPorts
        """Switch path returns a dict keyed by port_id from searchSiteSwOrGwPorts."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            search_response = MagicMock()  # Fake search response
            search_response.data = {  # Simulate API returning two port entries
                "results": [
                    {"port_id": "ge-0/0/0", "up": True, "speed": 1000},  # First port
                    {"port_id": "ge-0/0/1", "up": False, "speed": 0},  # Second port
                ]
            }
            mock_mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts.return_value = search_response  # Wire up mock
            result = utils._fetch_port_stats("site-1", "dev-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert "ge-0/0/0" in result  # First port should be in the result dict
        assert "ge-0/0/1" in result  # Second port should be in the result dict

    def test_switch_api_exception_returns_empty(self):  # API raises during switch path
        """Returns empty dict when searchSiteSwOrGwPorts raises an exception."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts.side_effect = RuntimeError("err")  # API fails
            result = utils._fetch_port_stats("site-1", "dev-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert result == {}  # Exception swallowed -- return empty dict

    def test_ap_happy_path_uses_port_stat(self):  # AP path via getSiteDeviceStats
        """AP path returns port_stat dict embedded in device stats response."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            stats_response = MagicMock()  # Fake device stats response
            stats_response.data = {  # AP stats embed port info under 'port_stat'
                "port_stat": {"eth0": {"up": True, "speed": 1000}}  # One Ethernet port
            }
            mock_mistapi.api.v1.sites.stats.getSiteDeviceStats.return_value = stats_response  # Wire up mock
            result = utils._fetch_port_stats("site-1", "dev-1", "aa:bb:cc:dd:ee:ff", "ap")  # Invoke AP path
        assert "eth0" in result  # AP port should be present in result

    def test_ap_no_port_stat_returns_empty(self):  # AP stats with no port_stat key
        """Returns empty dict when AP stats response has no 'port_stat' key."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            stats_response = MagicMock()  # Fake device stats response
            stats_response.data = {}  # No 'port_stat' key in the response
            mock_mistapi.api.v1.sites.stats.getSiteDeviceStats.return_value = stats_response  # Wire up mock
            result = utils._fetch_port_stats("site-1", "dev-1", "aa:bb:cc:dd:ee:ff", "ap")  # Invoke AP path
        assert result == {}  # No port data -- return empty dict

    def test_gateway_path_uses_same_endpoint_as_switch(self):  # Gateway uses switch endpoint
        """Gateway device_type uses the same searchSiteSwOrGwPorts endpoint as switch."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            search_response = MagicMock()  # Fake search response
            search_response.data = {"results": [{"port_id": "ge-0/0/0", "up": True}]}  # One port
            mock_mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts.return_value = search_response  # Wire up mock
            utils._fetch_port_stats("site-1", "dev-1", "de:ad:be:ef:00:01", "gateway")  # Invoke gateway path
        mock_mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts.assert_called_once()  # Same endpoint as switch

    def test_switch_results_missing_port_id_returns_empty(self, capsys):  # line 439 path
        """Returns empty dict and logs a warning when results lack a 'port_id' key."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            search_response = MagicMock()  # Fake search response
            search_response.data = {"results": [{"name": "port1"}]}  # Result with no port_id key
            mock_mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts.return_value = search_response  # Wire up
            result = utils._fetch_port_stats("site-1", "dev-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert result == {}  # No valid port_id entries -- return empty dict


# ---------------------------------------------------------------------------
# _fetch_port_config
# ---------------------------------------------------------------------------


class TestFetchPortConfig:
    """Tests for _fetch_port_config -- device config retrieval."""

    def test_happy_path_returns_port_config(self):  # Normal case
        """Returns the port_config section from the device config response."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            device_response = MagicMock()  # Fake device config response
            device_response.data = {  # Minimal device config with port_config section
                "port_config": {"ge-0/0/0-5": {"usage": "default"}}  # Port range config
            }
            mock_mistapi.api.v1.sites.devices.getSiteDevice.return_value = device_response  # Wire up mock
            result = utils._fetch_port_config("site-1", "dev-1")  # Invoke
        assert "ge-0/0/0-5" in result  # Port range key should be in result

    def test_exception_returns_empty_dict(self):  # API raises
        """Returns empty dict when the device config API raises an exception."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.getSiteDevice.side_effect = RuntimeError("timeout")  # API fails
            result = utils._fetch_port_config("site-1", "dev-1")  # Invoke
        assert result == {}  # Exception swallowed -- return empty dict

    def test_missing_port_config_key_returns_empty(self):  # Device config without port_config
        """Returns empty dict when the device config response has no 'port_config' key."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            device_response = MagicMock()  # Fake response without port_config
            device_response.data = {"name": "SW-1"}  # No port_config key present
            mock_mistapi.api.v1.sites.devices.getSiteDevice.return_value = device_response  # Wire up mock
            result = utils._fetch_port_config("site-1", "dev-1")  # Invoke
        assert result == {}  # No port_config -- return empty dict


# ---------------------------------------------------------------------------
# _build_port_table
# ---------------------------------------------------------------------------


class TestBuildPortTable:
    """Tests for _build_port_table -- PrettyTable rendering of port status."""

    def _make_port_info(self, name: str, speed=1000) -> tuple:  # Helper: build one (name, info) tuple
        """Return a (port_name, port_info) tuple with common test values."""
        return (  # Tuple matching available_ports list format
            name,  # Port name string
            {  # Minimal port info dict with all fields _build_port_table reads
                "up": True,  # Port is UP
                "speed": speed,  # Raw speed value
                "duplex": "full",  # Duplex mode string
                "full_duplex": True,  # Boolean fallback flag
                "_fallback": False,  # Not using config fallback stats
            },
        )

    def test_returns_prettytable_with_correct_fields(self):  # Happy path
        """Returns a PrettyTable with the expected 7 column headers."""
        from prettytable import PrettyTable  # Import for isinstance check

        utils = _make_utils()  # Create instance with mocked session
        ports = [self._make_port_info("ge-0/0/0"), self._make_port_info("ge-0/0/1")]  # Two ports
        table = utils._build_port_table(ports, {})  # No port_to_config needed
        assert isinstance(table, PrettyTable)  # Should return a PrettyTable instance
        assert "Port Name" in table.field_names  # Column header must be present
        assert "Speed" in table.field_names  # Speed column must be present
        assert "Duplex" in table.field_names  # Duplex column must be present

    def test_long_description_is_truncated(self):  # Description > 30 chars should be cut
        """Descriptions longer than 30 characters are truncated with '...'."""
        utils = _make_utils()  # Create instance with mocked session
        ports = [self._make_port_info("ge-0/0/0")]  # One port
        port_to_config = {  # Port config with a very long description
            "ge-0/0/0": {
                "port_profile": "uplink",  # Profile name
                "description": "A" * 40,  # 40-char description -- exceeds the 30-char limit
            }
        }
        table = utils._build_port_table(ports, port_to_config)  # Build table with long description
        table_str = str(table)  # Convert to string for text inspection
        assert "AAA..." in table_str  # Truncated form should appear in the table string

    def test_empty_description_shows_dash(self):  # No description configured
        """Empty description is replaced with a dash in the table output."""
        utils = _make_utils()  # Create instance with mocked session
        ports = [self._make_port_info("ge-0/0/0")]  # One port
        port_to_config = {  # Port config with empty description
            "ge-0/0/0": {"port_profile": "access", "description": ""}  # No description
        }
        table = utils._build_port_table(ports, port_to_config)  # Build table
        table_str = str(table)  # Convert to string for text inspection
        assert "| -" in table_str or " - " in table_str  # Dash placeholder should appear


# ---------------------------------------------------------------------------
# _prompt_port_selection
# ---------------------------------------------------------------------------


class TestPromptPortSelection:
    """Tests for _prompt_port_selection -- interactive port selection with mocks."""

    def _make_up_ports(self, count: int = 3) -> list:  # Helper: build UP-port tuples
        """Return a list of N (port_name, port_info) tuples with _fallback=False."""
        return [  # Each port is UP with minimal required info for _build_port_table
            (
                f"ge-0/0/{i}",  # Port name like 'ge-0/0/0'
                {"up": True, "speed": 1000, "duplex": "full", "full_duplex": True, "_fallback": False},
            )
            for i in range(count)  # N ports total
        ]

    def test_cancel_returns_none(self, capsys):  # User types 'c'
        """Returns None when user enters 'c' to cancel."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="c")  # Simulate cancel input
        ports = self._make_up_ports(3)  # Three UP ports
        result = utils._prompt_port_selection(ports, {}, "aa:bb:cc:dd:ee:ff", "SW1", "switch", False)  # Invoke
        assert result is None  # 'c' means cancel -- return None
        out = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in out  # User should see a cancellation message

    def test_empty_input_within_limit_returns_sentinel(self):  # Empty = all ports (3 <= 6)
        """Empty input returns the [] sentinel when available ports <= 6."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="")  # User presses Enter with no input
        ports = self._make_up_ports(3)  # Three ports -- within the 6-port API limit
        result = utils._prompt_port_selection(ports, {}, "aa:bb:cc:dd:ee:ff", "SW1", "switch", False)  # Invoke
        assert result == []  # Empty list is the 'all ports' sentinel

    def test_valid_index_returns_port_name(self):  # User picks index 1
        """Returns a list with the port name when user enters a valid single index."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="1")  # User selects index 1
        ports = self._make_up_ports(3)  # Three ports: ge-0/0/0, ge-0/0/1, ge-0/0/2
        result = utils._prompt_port_selection(ports, {}, "aa:bb:cc:dd:ee:ff", "SW1", "switch", False)  # Invoke
        assert result == ["ge-0/0/1"]  # Index 1 maps to ge-0/0/1

    def test_fallback_notice_displayed(self, capsys):  # _fallback=True triggers NOTE
        """Displays a NOTE about configured values when any port uses fallback stats."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="c")  # Cancel immediately after display
        fallback_ports = [  # Ports flagged as coming from config (not live stats)
            ("ge-0/0/0", {"up": True, "speed": 1000, "duplex": "full", "full_duplex": True, "_fallback": True})
        ]
        utils._prompt_port_selection(  # Invoke -- cancel is fine, we just check output
            fallback_ports, {}, "aa:bb:cc:dd:ee:ff", "SW1", "switch", False
        )
        out = capsys.readouterr().out  # Capture printed output
        assert "NOTE" in out  # Fallback notice must be printed when _fallback=True

    def test_return_available_true_wraps_result(self):  # return_available=True
        """With return_available=True, wraps single-port result in (ports, available) tuple."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="0")  # User selects index 0
        ports = self._make_up_ports(2)  # Two ports
        result = utils._prompt_port_selection(  # Invoke with return_available flag
            ports, {}, "aa:bb:cc:dd:ee:ff", "SW1", "switch", True  # return_available=True
        )
        assert isinstance(result, tuple)  # Should wrap result in a tuple
        assert result[0] == ["ge-0/0/0"]  # First element is the selected port list
        assert result[1] == ports  # Second element is the full available list

    def test_more_than_six_ports_shows_limit_exceeded(self, capsys):  # line 636 -- else branch
        """Prints a limit-exceeded warning when available port count exceeds 6."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="c")  # Cancel immediately after display
        ports = self._make_up_ports(7)  # Seven ports -- exceeds the 6-port capture limit
        utils._prompt_port_selection(  # Invoke -- user cancels after seeing the table
            ports, {}, "aa:bb:cc:dd:ee:ff", "SW1", "switch", False
        )
        out = capsys.readouterr().out  # Capture printed output
        assert "exceeds 6" in out or "NOT AVAILABLE" in out  # Limit-exceeded warning shown


# ---------------------------------------------------------------------------
# select_ports_from_device (integration of private helpers)
# ---------------------------------------------------------------------------


class TestSelectPortsFromDevice:
    """Tests for select_ports_from_device -- full orchestration with mocked API."""

    def _device_dict(self) -> dict:  # Minimal device dict for the mock
        """Return a minimal device dict with the fields select_ports_from_device reads."""
        return {  # Only fields that the method actually inspects
            "name": "SW-1",  # Human-readable name for display messages
            "mac": "aa:bb:cc:dd:ee:ff",  # MAC that matches the search target
            "id": "device-uuid-1",  # Mist UUID needed for subsequent API calls
        }

    def test_device_not_found_returns_none(self, capsys):  # listSiteDevices returns no matching device
        """Returns None when no device in the site matches the provided MAC."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response([])  # No devices
            result = utils.select_ports_from_device("site-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert result is None  # Device not found -- return None
        out = capsys.readouterr().out  # Capture output
        assert "Could not find" in out  # User should see a helpful message

    def test_api_exception_returns_none(self, capsys):  # listSiteDevices raises
        """Returns None when the initial listSiteDevices API call raises an exception."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate from real API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("timeout")  # API fails
            result = utils.select_ports_from_device("site-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert result is None  # Exception handled -- return None
        out = capsys.readouterr().out  # Capture output
        assert "Error" in out  # User should see an error message

    def test_no_ports_after_filtering_returns_none(self, capsys):  # All ports filtered out
        """Returns None when _filter_and_sort_ports returns an empty list."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [self._device_dict()]  # Device found
            )
            with patch.object(utils, "_fetch_port_stats", return_value={"ge-0/0/0": {"up": False}}):  # Ports found
                with patch.object(utils, "_fetch_port_config", return_value={}):  # Empty config
                    with patch.object(utils, "_build_port_to_config_map", return_value={}):  # Empty map
                        with patch.object(utils, "_filter_and_sort_ports", return_value=[]):  # All filtered
                            result = utils.select_ports_from_device("site-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert result is None  # No available ports -- return None

    def test_successful_flow_calls_prompt(self):  # Happy path end-to-end
        """Returns the prompt result when all helpers succeed."""
        utils = _make_utils()  # Create instance with mocked session
        utils._safe_input = MagicMock(return_value="0")  # User selects first port
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [self._device_dict()]  # Device found in inventory
            )
            port_stat = {"ge-0/0/0": {"up": True, "speed": 1000, "duplex": "full", "full_duplex": True}}
            with patch.object(utils, "_fetch_port_stats", return_value=port_stat):  # Stats available
                with patch.object(utils, "_fetch_port_config", return_value={}):  # No config
                    with patch.object(utils, "_build_port_to_config_map", return_value={}):  # No map
                        result = utils.select_ports_from_device(  # Invoke -- user picks index 0
                            "site-1", "aa:bb:cc:dd:ee:ff", "switch"
                        )
        assert result == ["ge-0/0/0"]  # User selected the only UP port at index 0

    def test_empty_port_stats_with_none_fallback_returns_none(self):  # lines 362 path
        """Returns None when stats are empty AND _build_port_stat_from_config returns None."""
        utils = _make_utils()  # Create instance with mocked session
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [self._device_dict()]  # Device found
            )
            with patch.object(utils, "_fetch_port_stats", return_value={}):  # Empty stats
                with patch.object(utils, "_fetch_port_config", return_value={}):  # Empty config
                    with patch.object(utils, "_build_port_to_config_map", return_value={}):  # Empty map
                        with patch.object(utils, "_build_port_stat_from_config", return_value=None):  # Fallback fails
                            result = utils.select_ports_from_device("site-1", "aa:bb:cc:dd:ee:ff", "switch")  # Invoke
        assert result is None  # Both stats and fallback failed -- return None

    def test_empty_port_stats_with_valid_fallback_uses_fallback(self, capsys):  # lines 363-367 path
        """Uses fallback port_stat when live stats are empty but config fallback succeeds."""
        utils = _make_utils()  # Create instance with mocked session
        fallback_stat = {"ge-0/0/0": {"up": True, "speed": 1000, "_fallback": True}}  # Config-derived stats
        with patch("src.device.prompt_utils.mistapi") as mock_mistapi:  # Isolate API
            mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = _mock_list_response(
                [self._device_dict()]  # Device found
            )
            with patch.object(utils, "_fetch_port_stats", return_value={}):  # Empty live stats
                with patch.object(utils, "_fetch_port_config", return_value={}):  # Empty config
                    with patch.object(utils, "_build_port_to_config_map", return_value={}):  # Empty map
                        with patch.object(  # Non-None fallback stat from config
                            utils, "_build_port_stat_from_config", return_value=fallback_stat
                        ):
                            utils._safe_input = MagicMock(return_value="c")  # User cancels at prompt
                            result = utils.select_ports_from_device(  # Invoke -- stats absent but fallback works
                                "site-1", "aa:bb:cc:dd:ee:ff", "switch"
                            )
        assert result is None  # User cancelled -- but fallback path was exercised (lines 363-367)
