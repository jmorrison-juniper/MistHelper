"""Wave 6 P2 coverage for ``src.gateway.overrides.override_classifier.OverrideClassifier``.

The classifier is a pure module with zero runtime dependencies -- no mocks
required. Tests import the real class and exercise every branch of the
missing coverage set (21 stmts across ``classify``, ``_field_matches_port``,
``_value_is_override``, ``_port_has_override``, ``build_port_entry``,
``_format_config_type``, ``_port_detail_columns``, ``_assemble_entry``).
"""

from __future__ import annotations  # WHY: PEP 604 unions in test annotations.

from typing import Any  # Broad typing for CSV row / device_info payloads.

from src.gateway.overrides.override_classifier import OverrideClassifier  # Real class under test.


class TestClassify:
    """Cover the public ``classify`` entry point."""

    def test_returns_only_overridden_ports(self) -> None:
        """Only ports whose fields carry override values appear in the result."""
        # WHY: exercises the True/False branches of _port_has_override via classify.
        row: dict[str, Any] = {
            "port_config_ge-0/0/0_ip_config_ip": "10.0.0.1",  # ge-0/0/0 has override
            "port_config_ge-0/0/1_ip_config_ip": "",  # ge-0/0/1 blank -> not override
        }
        result = OverrideClassifier.classify(row, ["ge-0/0/0", "ge-0/0/1"])  # Classify both.
        assert result == ["ge-0/0/0"]  # Only the port with a real value survives.

    def test_empty_target_ports_returns_empty(self) -> None:
        """When there are no ports to classify, the accumulator stays empty."""
        # WHY: baseline for the for-loop no-iterations branch.
        assert OverrideClassifier.classify({"anything": "x"}, []) == []  # No ports -> empty list.

    def test_no_overrides_returns_empty(self) -> None:
        """All-empty override fields yield an empty result."""
        # WHY: exercises _port_has_override False branch across the loop.
        row = {"port_config_ge-0/0/0_ip_config_ip": ""}  # Blank value.
        assert OverrideClassifier.classify(row, ["ge-0/0/0"]) == []  # No overrides detected.


class TestFieldMatchesPort:
    """Cover both separator variants of ``_field_matches_port``."""

    def test_underscore_separator_matches(self) -> None:
        """``port_config_<port>_`` variant qualifies."""
        # WHY: covers the underscore branch of the OR predicate.
        assert OverrideClassifier._field_matches_port("port_config_ge-0/0/0_ip", "ge-0/0/0") is True

    def test_dot_separator_matches(self) -> None:
        """``port_config_<port>.`` variant qualifies."""
        # WHY: covers the dot branch of the OR predicate.
        assert OverrideClassifier._field_matches_port("port_config_ge-0/0/0.ip", "ge-0/0/0") is True

    def test_unrelated_field_does_not_match(self) -> None:
        """Unrelated column names are rejected."""
        # WHY: covers the False fall-through when neither prefix matches.
        assert OverrideClassifier._field_matches_port("other_field", "ge-0/0/0") is False


class TestValueIsOverride:
    """Cover the normalization branches of ``_value_is_override``."""

    def test_blank_string_is_not_override(self) -> None:
        """Empty string normalizes to ``""`` -> not an override."""
        # WHY: covers the blank True->False mapping.
        assert OverrideClassifier._value_is_override("") is False  # Blank -> not override.

    def test_none_string_is_not_override(self) -> None:
        """Literal 'none' string normalizes to filtered set."""
        # WHY: covers the "none" tombstone rejection.
        assert OverrideClassifier._value_is_override("None") is False  # Case-insensitive "none".

    def test_null_string_is_not_override(self) -> None:
        """Literal 'null' string normalizes to filtered set."""
        # WHY: covers the "null" tombstone rejection.
        assert OverrideClassifier._value_is_override("NULL") is False  # Case-insensitive "null".

    def test_none_value_is_not_override(self) -> None:
        """Python None normalizes via ``value or ""`` to blank."""
        # WHY: covers the (value or "") guard.
        assert OverrideClassifier._value_is_override(None) is False  # None -> blank.

    def test_real_value_is_override(self) -> None:
        """Any non-blank/non-tombstone value counts as an override."""
        # WHY: covers the True path.
        assert OverrideClassifier._value_is_override("10.0.0.1") is True  # Real IP is override.


class TestPortHasOverride:
    """Cover the branching paths inside ``_port_has_override``."""

    def test_vpn_paths_field_is_ignored(self) -> None:
        """Fields containing ``_vpn_paths_`` never count as overrides."""
        # WHY: covers the VPN-path skip continue branch.
        row = {"port_config_ge-0/0/0_vpn_paths_uuid": "some-value"}  # VPN path field.
        assert OverrideClassifier._port_has_override(row, "ge-0/0/0") is False  # Ignored.

    def test_other_port_field_is_ignored(self) -> None:
        """Fields owned by a different port are skipped."""
        # WHY: covers the _field_matches_port False continue branch.
        row = {"port_config_ge-0/0/1_ip": "10.0.0.1"}  # Different port.
        assert OverrideClassifier._port_has_override(row, "ge-0/0/0") is False  # Skipped.

    def test_meaningful_value_returns_true(self) -> None:
        """A meaningful port-owned value returns True immediately."""
        # WHY: covers the True return path.
        row = {"port_config_ge-0/0/0.ip": "10.0.0.1"}  # Dot-variant with real value.
        assert OverrideClassifier._port_has_override(row, "ge-0/0/0") is True  # Detected.

    def test_no_matches_returns_false(self) -> None:
        """Exhaustion returns False."""
        # WHY: covers the fall-off end-of-loop False return.
        assert OverrideClassifier._port_has_override({}, "ge-0/0/0") is False  # Empty row.


class TestFormatConfigType:
    """Cover all three branches of ``_format_config_type``."""

    def test_dhcp_returns_upper(self) -> None:
        """Canonical dhcp -> DHCP."""
        # WHY: covers the explicit dhcp branch.
        assert OverrideClassifier._format_config_type("dhcp") == "DHCP"  # Canonical DHCP.

    def test_static_returns_upper(self) -> None:
        """Canonical static -> STATIC."""
        # WHY: covers the explicit static branch.
        assert OverrideClassifier._format_config_type("static") == "STATIC"  # Canonical STATIC.

    def test_other_value_uppercased(self) -> None:
        """Non-canonical non-empty value is uppercased."""
        # WHY: covers the final ternary True branch.
        assert OverrideClassifier._format_config_type("pppoe") == "PPPOE"  # Uppercased.

    def test_empty_returns_unknown(self) -> None:
        """Empty value returns 'UNKNOWN'."""
        # WHY: covers the final ternary False branch.
        assert OverrideClassifier._format_config_type("") == "UNKNOWN"  # Fallback label.


class TestBuildPortEntry:
    """Cover ``build_port_entry`` and its downstream assemblers."""

    def _device_info(self) -> dict[str, Any]:
        """Minimal device_info stub with every required key present."""
        # WHY: shared fixture keeps test bodies tight.
        return {
            "device_name": "gw01",  # Reporting key.
            "site_name": "Site-A",  # Human label.
            "template_name": "tmpl-1",  # Template label.
            "device_id": "dev-uuid",  # Optional but exercised.
            "site_id": "site-uuid",  # Required.
            "template_id": "tmpl-uuid",  # Required.
        }

    def test_full_entry_with_dhcp_up_enabled(self) -> None:
        """A fully populated DHCP/up/enabled port yields the expected CSV row."""
        # WHY: exercises the DHCP path, port-up True branch, and disabled=False -> enabled path.
        port_config = {
            "ip_config": {"type": "dhcp", "gateway": "10.0.0.1", "ip": "10.0.0.2", "netmask": "255.255.255.0"},
            "description": "primary WAN",
            "disabled": False,  # -> admin enabled.
            "usage": "wan",
        }
        interface_stat = {"up": True}  # -> port_status "up".
        entry = OverrideClassifier.build_port_entry(self._device_info(), "ge-0/0/0", port_config, interface_stat)
        assert entry["port_config_type"] == "DHCP"  # Formatted display label.
        assert entry["port_status"] == "up"  # Live status.
        assert entry["port_admin_status"] == "enabled"  # Configured admin state.
        assert entry["port_gateway_ip"] == "10.0.0.1"  # IP config surface.
        assert entry["overridden_from_template"] == "Yes"  # Constant flag.
        assert entry["device_id"] == "dev-uuid"  # Device UUID passthrough.
        assert entry["gateway_device_name"] == "gw01"  # Reporting key.

    def test_static_disabled_port_down(self) -> None:
        """Static/disabled/down port exercises the alternate branches."""
        # WHY: covers static config type, admin=disabled, and up=False path.
        port_config = {"ip_config": {"type": "static"}, "disabled": True}  # Bare-minimum config.
        interface_stat = {"up": False}  # Down.
        entry = OverrideClassifier.build_port_entry(self._device_info(), "ge-0/0/1", port_config, {})  # Empty stat.
        # WHY: empty interface_stat is falsy -> the ternary picks "down" via the truthiness guard.
        assert entry["port_status"] == "down"  # Down branch.
        assert entry["port_admin_status"] == "disabled"  # Disabled=True -> disabled.
        entry2 = OverrideClassifier.build_port_entry(self._device_info(), "ge-0/0/1", port_config, interface_stat)
        assert entry2["port_config_type"] == "STATIC"  # Static branch.
        assert entry2["port_status"] == "down"  # up=False branch of the boolean.

    def test_missing_optional_device_id_defaults_to_empty(self) -> None:
        """When ``device_id`` is missing, the entry uses ``''`` per legacy expectation."""
        # WHY: covers the .get("device_id", "") default branch inside _assemble_entry.
        device_info = self._device_info()  # Baseline fixture.
        del device_info["device_id"]  # Drop optional key.
        entry = OverrideClassifier.build_port_entry(device_info, "ge-0/0/0", {"ip_config": {}}, {})  # Empty config.
        assert entry["device_id"] == ""  # Default kicks in.
        assert entry["port_config_type"] == "UNKNOWN"  # Empty ip_config type -> UNKNOWN.
