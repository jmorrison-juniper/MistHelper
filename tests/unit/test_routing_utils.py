"""Tests for RoutingUtils (Issue #207).

Covers pure parsing helpers, display methods, orchestrator flows,
device selection/guidance, WebSocket interaction, error handling,
and SSR/SRX dedicated API paths.

Uses identity-checked teardown to avoid cross-test sys.modules contamination.
"""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

# --- Module-level mistapi mock (identity-checked teardown) ---
_had_mistapi = "mistapi" in sys.modules
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock


from src.network.routing_utils import RoutingUtils


def setup_module() -> None:
    """Re-assert our mock in sys.modules before tests run."""
    sys.modules["mistapi"] = _our_mock


def teardown_module() -> None:
    """Restore sys.modules only if our mock is still installed."""
    if sys.modules.get("mistapi") is not _our_mock:
        return
    if _had_mistapi:
        sys.modules["mistapi"] = _saved_mistapi  # type: ignore[assignment]
    else:
        sys.modules.pop("mistapi", None)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture()
def mock_deps() -> dict[str, MagicMock]:
    """Return dict of constructor dependencies as mocks."""
    return {
        "apisession": MagicMock(),
        "select_site_fn": MagicMock(return_value="site-1"),
        "select_device_fn": MagicMock(return_value="dev-1"),
        "safe_input_fn": MagicMock(return_value=""),
        "websocket_manager_factory": MagicMock(),
        "is_debug_mode_fn": MagicMock(return_value=False),
    }


@pytest.fixture()
def ru(mock_deps: dict[str, MagicMock]) -> RoutingUtils:
    """Return a RoutingUtils instance with mocked deps."""
    return RoutingUtils(**mock_deps)


# ===================================================================
# INIT
# ===================================================================


class TestInit:
    """Constructor stores all injected dependencies."""

    def test_stores_apisession(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        assert ru.apisession is mock_deps["apisession"]

    def test_stores_select_site_fn(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        assert ru.select_site_fn is mock_deps["select_site_fn"]

    def test_stores_select_device_fn(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        assert ru.select_device_fn is mock_deps["select_device_fn"]

    def test_stores_safe_input_fn(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        assert ru.safe_input_fn is mock_deps["safe_input_fn"]

    def test_stores_websocket_factory(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        assert ru.websocket_manager_factory is mock_deps["websocket_manager_factory"]

    def test_stores_is_debug_mode_fn(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        assert ru.is_debug_mode_fn is mock_deps["is_debug_mode_fn"]


# ===================================================================
# PARSING: _parse_forwarding_table
# ===================================================================


class TestParseForwardingTable:
    """Parse raw forwarding table output into structured entries."""

    def test_empty_input(self, ru: RoutingUtils) -> None:
        assert ru._parse_forwarding_table("") == []

    def test_json_list(self, ru: RoutingUtils) -> None:
        data = [
            {"prefix": "10.0.0.0/8", "nextHop": "10.0.0.1", "interface": "eth0", "service": "internet"},
        ]
        result = ru._parse_forwarding_table(json.dumps(data))
        assert len(result) == 1
        assert result[0]["destination"] == "10.0.0.0/8"
        assert result[0]["next_hop"] == "10.0.0.1"
        assert result[0]["interface"] == "eth0"
        assert result[0]["service"] == "internet"

    def test_json_dict_with_list_values(self, ru: RoutingUtils) -> None:
        data = {"routes": [{"destination": "192.168.0.0/16", "next_hop": "gw1", "dev": "ge-0/0/0"}]}
        result = ru._parse_forwarding_table(json.dumps(data))
        assert len(result) == 1
        assert result[0]["destination"] == "192.168.0.0/16"
        assert result[0]["interface"] == "ge-0/0/0"

    def test_plain_text_lines(self, ru: RoutingUtils) -> None:
        raw = "10.0.0.0/8 10.0.0.1 eth0 svc\n172.16.0.0/12 172.16.0.1 eth1 corp"
        result = ru._parse_forwarding_table(raw)
        assert len(result) == 2
        assert result[0]["destination"] == "10.0.0.0/8"
        assert result[1]["next_hop"] == "172.16.0.1"

    def test_skips_comments_and_dividers(self, ru: RoutingUtils) -> None:
        raw = "# header\n---\n10.0.0.0/8 gw1"
        result = ru._parse_forwarding_table(raw)
        assert len(result) == 1

    def test_invalid_json_falls_through_to_text(self, ru: RoutingUtils) -> None:
        raw = "{invalid json\n10.0.0.0/8 gw1 eth0"
        result = ru._parse_forwarding_table(raw)
        assert len(result) == 2  # Both lines parsed as text

    def test_json_dict_without_list_values(self, ru: RoutingUtils) -> None:
        data = {"status": "ok", "count": 0}
        result = ru._parse_forwarding_table(json.dumps(data))
        assert result == []


# ===================================================================
# PARSING: _parse_routing_table
# ===================================================================


class TestParseRoutingTable:
    """Parse routing table output supporting multiple formats."""

    def test_empty_input(self, ru: RoutingUtils) -> None:
        assert ru._parse_routing_table("") == []

    def test_json_list(self, ru: RoutingUtils) -> None:
        data = [{"prefix": "10.0.0.0/8", "nextHop": "10.0.0.1", "protocol": "BGP"}]
        result = ru._parse_routing_table(json.dumps(data))
        assert len(result) == 1
        assert result[0]["destination"] == "10.0.0.0/8"
        assert result[0]["protocol"] == "BGP"

    def test_json_dict_with_list_values(self, ru: RoutingUtils) -> None:
        data = {"inet.0": [{"prefix": "192.168.1.0/24", "gateway": "10.0.0.1"}]}
        result = ru._parse_routing_table(json.dumps(data))
        assert len(result) == 1
        assert result[0]["next_hop"] == "10.0.0.1"

    def test_standard_route_line_via(self, ru: RoutingUtils) -> None:
        raw = "10.0.0.0/8 via 10.0.0.1 dev eth0 proto bgp"
        result = ru._parse_routing_table(raw)
        assert len(result) == 1
        assert result[0]["next_hop"] == "10.0.0.1"
        assert result[0]["interface"] == "eth0"

    def test_protocol_route_line(self, ru: RoutingUtils) -> None:
        raw = "BGP 10.0.0.0/8 10.0.0.1 ge-0/0/0"
        result = ru._parse_routing_table(raw)
        assert len(result) == 1
        assert result[0]["protocol"] == "BGP"

    def test_tabular_route_line(self, ru: RoutingUtils) -> None:
        raw = "10.0.0.0/8 10.0.0.1 eth0 static 100"
        result = ru._parse_routing_table(raw)
        assert len(result) == 1

    def test_juniper_inet0_format(self, ru: RoutingUtils) -> None:
        raw = "inet.0: 5 destinations\n" ">* 10.0.0.0/8 [BGP/170] via 10.0.0.1\n" "   ge-0/0/0.0\n"
        result = ru._parse_routing_table(raw)
        assert len(result) >= 1
        assert result[0]["destination"] == "10.0.0.0/8"

    def test_skips_comment_and_divider_lines(self, ru: RoutingUtils) -> None:
        raw = "# comment\n---\n10.0.0.0/8 via 10.0.0.1"
        result = ru._parse_routing_table(raw)
        assert len(result) == 1


# ===================================================================
# PARSING: _parse_standard_route_line
# ===================================================================


class TestParseStandardRouteLine:
    """Parse route lines with via/dev/proto keywords."""

    def test_active_selected_flags(self, ru: RoutingUtils) -> None:
        result = ru._parse_standard_route_line(">* 10.0.0.0/8 via 10.0.0.1 dev eth0 proto bgp")
        assert result is not None
        assert result["active"] is True
        assert result["selected"] is True
        assert result["next_hop"] == "10.0.0.1"
        assert result["interface"] == "eth0"
        assert result["protocol"] == "bgp"

    def test_no_flags(self, ru: RoutingUtils) -> None:
        result = ru._parse_standard_route_line("10.0.0.0/8 via 10.0.0.1")
        assert result is not None
        assert result["active"] is False
        assert result["selected"] is False


# ===================================================================
# PARSING: _parse_protocol_route_line
# ===================================================================


class TestParseProtocolRouteLine:
    """Parse route lines with BGP/OSPF/static indicators."""

    def test_bgp_line(self, ru: RoutingUtils) -> None:
        result = ru._parse_protocol_route_line("BGP 10.0.0.0/8 10.0.0.1 ge-0/0/0")
        assert result is not None
        assert result["protocol"] == "BGP"
        assert result["destination"] == "10.0.0.0/8"
        assert result["next_hop"] == "10.0.0.1"
        assert result["interface"] == "ge-0/0/0"

    def test_empty_parts(self, ru: RoutingUtils) -> None:
        result = ru._parse_protocol_route_line("")
        assert result is None

    def test_no_destination(self, ru: RoutingUtils) -> None:
        result = ru._parse_protocol_route_line("BGP")
        assert result is None

    def test_active_selected_flags(self, ru: RoutingUtils) -> None:
        result = ru._parse_protocol_route_line(">* BGP 10.0.0.0/8")
        assert result is not None
        assert result["active"] is True
        assert result["selected"] is True


# ===================================================================
# PARSING: _parse_tabular_route_line
# ===================================================================


class TestParseTabularRouteLine:
    """Parse space-separated tabular route lines."""

    def test_basic_tabular(self, ru: RoutingUtils) -> None:
        result = ru._parse_tabular_route_line("10.0.0.0/8 10.0.0.1 eth0 bgp 100")
        assert result is not None
        assert result["destination"] == "10.0.0.0/8"
        assert result["next_hop"] == "10.0.0.1"
        assert result["admin_distance"] == "100"

    def test_too_few_parts(self, ru: RoutingUtils) -> None:
        result = ru._parse_tabular_route_line("single")
        assert result is None

    def test_active_flag(self, ru: RoutingUtils) -> None:
        result = ru._parse_tabular_route_line("> 10.0.0.0/8 gw1")
        assert result is not None
        assert result["active"] is True


# ===================================================================
# PARSING: _normalize_json_route_entry
# ===================================================================


class TestNormalizeJsonRouteEntry:
    """Normalize JSON dict into standard route entry format."""

    def test_standard_keys(self, ru: RoutingUtils) -> None:
        item = {"prefix": "10.0.0.0/8", "nextHop": "gw1", "interface": "eth0", "protocol": "BGP"}
        result = ru._normalize_json_route_entry(item)
        assert result["destination"] == "10.0.0.0/8"
        assert result["next_hop"] == "gw1"
        assert result["interface"] == "eth0"
        assert result["protocol"] == "BGP"

    def test_alternate_keys(self, ru: RoutingUtils) -> None:
        item = {"route": "192.168.0.0/16", "gateway": "gw2", "iface": "lo0", "type": "static"}
        result = ru._normalize_json_route_entry(item)
        assert result["destination"] == "192.168.0.0/16"
        assert result["next_hop"] == "gw2"
        assert result["interface"] == "lo0"
        assert result["protocol"] == "static"


# ===================================================================
# PARSING: _parse_juniper_routing
# ===================================================================


class TestParseJuniperRouting:
    """Parse Juniper inet.0/inet6.0 multi-line routing format."""

    def test_inet0_with_via(self, ru: RoutingUtils) -> None:
        raw = (
            "inet.0: 3 destinations\n"
            ">* 10.0.0.0/8 [BGP/170] via 10.0.0.1\n"
            "   ge-0/0/0.0\n"
            "   192.168.1.0/24 [Static/5] via 192.168.1.1\n"
        )
        result = ru._parse_juniper_routing(raw)
        assert len(result) == 2
        assert result[0]["protocol"] == "BGP"
        assert result[0]["admin_distance"] == "170"
        assert result[0]["active"] is True
        assert result[0]["table"] == "inet.0"

    def test_local_next_hop(self, ru: RoutingUtils) -> None:
        raw = "inet.0: 1 destinations\n* 127.0.0.1/32 [Local/0]\n  Local\n"
        result = ru._parse_juniper_routing(raw)
        assert len(result) == 1
        assert result[0]["next_hop"] == "Local"


# ===================================================================
# PARSING: _parse_ssr_routing
# ===================================================================


class TestParseSsrRouting:
    """Parse SSR/SRX routing table JSON from dedicated API."""

    def test_success_response(self, ru: RoutingUtils) -> None:
        data = {
            "status": "SUCCESS",
            "message": "bgp routes",
            "columns": ["prefix", "nextHops"],
            "rows": [
                {
                    "prefix": "10.0.0.0/8",
                    "nextHops": "10.0.0.1",
                    "metric": 100,
                    "vrfName": "default",
                    "name": "route1",
                    "weight": 0,
                    "path": "65001 65002",
                    "localPreference": 100,
                    "selectionReason": "best",
                    "status": "active",
                }
            ],
        }
        result = ru._parse_ssr_routing(json.dumps(data))
        assert len(result) == 1
        assert result[0]["destination"] == "10.0.0.0/8"
        assert result[0]["protocol"] == "BGP"
        assert result[0]["as_path"] == "65001 65002"

    def test_failed_status(self, ru: RoutingUtils) -> None:
        data = {"status": "FAILED", "message": "error"}
        result = ru._parse_ssr_routing(json.dumps(data))
        assert result == []

    def test_empty_rows(self, ru: RoutingUtils) -> None:
        data = {"status": "SUCCESS", "columns": ["prefix"], "rows": []}
        result = ru._parse_ssr_routing(json.dumps(data))
        assert result == []

    def test_invalid_json(self, ru: RoutingUtils) -> None:
        result = ru._parse_ssr_routing("{bad json")
        assert result == []


# ===================================================================
# DISPLAY: _display_forwarding_summary
# ===================================================================


class TestDisplayForwardingSummary:
    """Display summary of forwarding table entries."""

    def test_empty_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_summary([])
        assert "No forwarding table entries found" in capsys.readouterr().out

    def test_with_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "interface": "eth0",
                "service": "internet",
                "table": "main",
                "type": "",
            },
            {
                "destination": "172.16.0.0/12",
                "next_hop": "gw2",
                "interface": "eth1",
                "service": "internet",
                "table": "main",
                "type": "",
            },
        ]
        ru._display_forwarding_summary(entries)
        output = capsys.readouterr().out
        assert "Total forwarding entries: 2" in output
        assert "Top services:" in output


# ===================================================================
# DISPLAY: _display_prefix_table_impl
# ===================================================================


class TestDisplayPrefixTableImpl:
    """Display forwarding entries via PrettyTable."""

    def test_empty_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_prefix_table_impl([])
        assert capsys.readouterr().out == ""

    def test_with_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "interface": "eth0",
                "service": "svc",
                "table": "t",
                "type": "x",
            }
        ]
        ru._display_prefix_table_impl(entries)
        output = capsys.readouterr().out
        assert "10.0.0.0/8" in output


# ===================================================================
# DISPLAY: _display_routing_summary
# ===================================================================


class TestDisplayRoutingSummary:
    """Display summary of routing table entries."""

    def test_empty_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_routing_summary([])
        assert "No routing table entries found" in capsys.readouterr().out

    def test_empty_with_query_params(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_routing_summary([], {"protocol": "bgp"})
        output = capsys.readouterr().out
        assert "protocol: bgp" in output

    def test_with_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "interface": "eth0",
                "protocol": "BGP",
                "table": "inet.0",
                "active": True,
                "admin_distance": "170",
            },
        ]
        ru._display_routing_summary(entries)
        output = capsys.readouterr().out
        assert "Total routing table entries: 1" in output
        assert "BGP" in output


# ===================================================================
# DISPLAY: _display_routing_details
# ===================================================================


class TestDisplayRoutingDetails:
    """Display detailed routing table."""

    def test_empty_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_routing_details([])
        assert capsys.readouterr().out == ""

    def test_with_active_selected(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "interface": "eth0",
                "protocol": "BGP",
                "active": True,
                "selected": True,
                "admin_distance": "170",
            },
        ]
        ru._display_routing_details(entries)
        output = capsys.readouterr().out
        assert "Status Legend" in output
        assert "10.0.0.0/8" in output


# ===================================================================
# DISPLAY: _display_ssr_routing
# ===================================================================


class TestDisplaySsrRouting:
    """Display SSR/SRX routing table."""

    def test_empty_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_ssr_routing([])
        assert "No routing table entries found" in capsys.readouterr().out

    def test_with_entries(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "10.0.0.1",
                "protocol": "BGP",
                "name": "route1",
                "status": "active",
                "selection_reason": "best",
                "weight": "0",
                "metric": "100",
                "local_preference": "100",
                "as_path": "65001",
                "vrf": "default",
            }
        ]
        ru._display_ssr_routing(entries)
        output = capsys.readouterr().out
        assert "Total routing table entries: 1" in output
        assert "BGP" in output


# ===================================================================
# DISPLAY: _display_forwarding_device_guidance
# ===================================================================


class TestDisplayForwardingDeviceGuidance:
    """Display device type guidance for forwarding table."""

    def test_none_device_info(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_device_guidance(None)
        assert capsys.readouterr().out == ""

    def test_ssr_gateway(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_device_guidance({"type": "gateway", "model": "SSR-1200"})
        assert "SSR gateway detected" in capsys.readouterr().out

    def test_generic_gateway(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_device_guidance({"type": "gateway", "model": "SRX-300"})
        assert "Gateway device detected" in capsys.readouterr().out

    def test_switch_warning(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_device_guidance({"type": "switch", "model": "EX4300"})
        assert "Switch device" in capsys.readouterr().out

    def test_ap_warning(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_device_guidance({"type": "ap", "model": "AP45"})
        assert "Access Point" in capsys.readouterr().out


# ===================================================================
# DISPLAY: _display_routing_device_guidance
# ===================================================================


class TestDisplayRoutingDeviceGuidance:
    """Display device guidance for routing table. Returns bool."""

    def test_none_device_info(self, ru: RoutingUtils) -> None:
        assert ru._display_routing_device_guidance(None) is True

    def test_ex_switch(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = ru._display_routing_device_guidance({"type": "switch", "model": "EX4300"})
        assert result is True
        assert "EX switch" in capsys.readouterr().out

    def test_qfx_switch(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = ru._display_routing_device_guidance({"type": "switch", "model": "QFX5100"})
        assert result is True
        assert "QFX switch" in capsys.readouterr().out

    def test_non_switch_user_cancels(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        result = ru._display_routing_device_guidance({"type": "gateway", "model": "SSR-1200"})
        assert result is False

    def test_non_switch_user_continues(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "y"
        result = ru._display_routing_device_guidance({"type": "gateway", "model": "SSR-1200"})
        assert result is True


# ===================================================================
# DISPLAY: _verify_ssr_compatibility
# ===================================================================


class TestVerifySsrCompatibility:
    """Verify device is SSR/SRX compatible."""

    def test_none_device_info(self, ru: RoutingUtils) -> None:
        assert ru._verify_ssr_compatibility(None) is True

    def test_ssr_gateway(self, ru: RoutingUtils) -> None:
        assert ru._verify_ssr_compatibility({"type": "gateway", "model": "SSR-1200"}) is True

    def test_srx_gateway(self, ru: RoutingUtils) -> None:
        assert ru._verify_ssr_compatibility({"type": "gateway", "model": "SRX-300"}) is True

    def test_generic_gateway_user_cancels(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        assert ru._verify_ssr_compatibility({"type": "gateway", "model": "Other"}) is False

    def test_generic_gateway_user_continues(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "y"
        assert ru._verify_ssr_compatibility({"type": "gateway", "model": "Other"}) is True

    def test_non_gateway_user_cancels(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        assert ru._verify_ssr_compatibility({"type": "switch", "model": "EX4300"}) is False


# ===================================================================
# HELPER: _setup_debug_mode
# ===================================================================


class TestSetupDebugMode:
    """Configure logging for debug mode."""

    def test_debug_enabled(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._setup_debug_mode(True)
        assert "[DEBUG] DEBUG MODE ENABLED" in capsys.readouterr().out

    def test_debug_disabled(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._setup_debug_mode(False)
        assert capsys.readouterr().out == ""


# ===================================================================
# HELPER: _get_device_info
# ===================================================================


class TestGetDeviceInfo:
    """Retrieve device info via API."""

    def test_device_found(self, ru: RoutingUtils) -> None:
        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "SSR"}]
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            result = ru._get_device_info("site-1", "dev-1", "all", False)
        assert result is not None
        assert result["model"] == "SSR"

    def test_device_not_found(self, ru: RoutingUtils) -> None:
        resp = MagicMock()
        resp.data = [{"id": "other-dev", "type": "switch"}]
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            result = ru._get_device_info("site-1", "dev-1", "all", False)
        assert result is None

    def test_api_error(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("timeout")
            result = ru._get_device_info("site-1", "dev-1", "all", False)
        assert result is None
        assert "Proceeding with standard command" in capsys.readouterr().out


# ===================================================================
# HELPER: _connect_websocket
# ===================================================================


class TestConnectWebsocket:
    """Establish WebSocket connection and subscribe."""

    def test_successful_connection(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        with patch("src.network.routing_utils.time"):
            result = ru._connect_websocket("site-1", "dev-1", False)
        assert result is ws_mgr

    def test_connect_fails(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = False
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        result = ru._connect_websocket("site-1", "dev-1", False)
        assert result is None
        assert "Failed to establish" in capsys.readouterr().out

    def test_subscribe_fails(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = False
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        result = ru._connect_websocket("site-1", "dev-1", False)
        assert result is None
        ws_mgr.disconnect.assert_called_once()


# ===================================================================
# HELPER: _get_forwarding_table_params
# ===================================================================


class TestGetForwardingTableParams:
    """Get user input for forwarding table parameters."""

    def test_default_params(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        result = ru._get_forwarding_table_params()
        assert result["prefix"] == "0.0.0.0/0"

    def test_custom_prefix(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].side_effect = ["10.0.0.0/8", "svc1", "vrf1", "node0"]
        result = ru._get_forwarding_table_params()
        assert result["prefix"] == "10.0.0.0/8"
        assert result["service_name"] == "svc1"
        assert result["vrf"] == "vrf1"
        assert result["node"] == "node0"


# ===================================================================
# HELPER: _get_routing_table_params
# ===================================================================


class TestGetRoutingTableParams:
    """Get user input for routing table parameters."""

    def test_default_params(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        result = ru._get_routing_table_params()
        assert result["protocol"] == "any"

    def test_bgp_with_neighbor(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].side_effect = [
            "10.0.0.0/8",  # prefix
            "bgp",  # protocol
            "vrf1",  # vrf
            "10.0.0.1",  # neighbor
            "received",  # direction
            "",  # node
        ]
        result = ru._get_routing_table_params()
        assert result["prefix"] == "10.0.0.0/8"
        assert result["protocol"] == "bgp"
        assert result["neighbor"] == "10.0.0.1"
        assert result["route"] == "received"


# ===================================================================
# HELPER: _get_ssr_route_params
# ===================================================================


class TestGetSsrRouteParams:
    """Get user input for SSR/SRX route parameters."""

    def test_default_params(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        result = ru._get_ssr_route_params()
        assert "protocol" not in result

    def test_full_params(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].side_effect = [
            "bgp",  # protocol
            "10.0.0.0/8",  # prefix
            "default",  # vrf
            "10.0.0.1",  # neighbor
            "received",  # direction
            "node0",  # node
            "5",  # interval
            "60",  # duration
        ]
        result = ru._get_ssr_route_params()
        assert result["protocol"] == "bgp"
        assert result["prefix"] == "10.0.0.0/8"
        assert result["interval"] == 5
        assert result["duration"] == 60


# ===================================================================
# HELPER: _execute_forwarding_table_command
# ===================================================================


class TestExecuteForwardingTableCommand:
    """Execute forwarding table command via REST API."""

    def test_success(self, ru: RoutingUtils) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session": "sess-abc-123"}
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_forwarding_table_command("site-1", "dev-1", {"prefix": "0.0.0.0/0"}, False)
        assert result == "sess-abc-123"

    def test_http_error(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_forwarding_table_command("site-1", "dev-1", {}, False)
        assert result is None
        assert "Failed to issue" in capsys.readouterr().out

    def test_no_host(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru.apisession.host = None
        with patch.dict("os.environ", {}, clear=True):
            result = ru._execute_forwarding_table_command("site-1", "dev-1", {}, False)
        assert result is None

    def test_no_session_id_in_response(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_forwarding_table_command("site-1", "dev-1", {}, False)
        assert result is None


# ===================================================================
# HELPER: _execute_routing_table_command
# ===================================================================


class TestExecuteRoutingTableCommand:
    """Execute routing table command via REST API."""

    def test_success(self, ru: RoutingUtils) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session": "sess-def-456"}
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_routing_table_command("site-1", "dev-1", {"protocol": "any"}, False)
        assert result == "sess-def-456"

    def test_http_error(self, ru: RoutingUtils) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_routing_table_command("site-1", "dev-1", {}, False)
        assert result is None


# ===================================================================
# HELPER: _execute_ssr_route_command
# ===================================================================


class TestExecuteSsrRouteCommand:
    """Execute SSR/SRX routing API call."""

    def test_success(self, ru: RoutingUtils) -> None:
        resp = MagicMock()
        resp.data = {"session": "ssr-sess-789"}
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.showSiteSsrAndSrxRoutes.return_value = resp
            result = ru._execute_ssr_route_command("site-1", "dev-1", {"protocol": "bgp"}, False)
        assert result == "ssr-sess-789"

    def test_no_session_in_response(self, ru: RoutingUtils) -> None:
        resp = MagicMock()
        resp.data = {"status": "ok"}
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.showSiteSsrAndSrxRoutes.return_value = resp
            result = ru._execute_ssr_route_command("site-1", "dev-1", {}, False)
        assert result is None

    def test_api_exception(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.showSiteSsrAndSrxRoutes.side_effect = RuntimeError("fail")
            result = ru._execute_ssr_route_command("site-1", "dev-1", {}, False)
        assert result is None
        assert "Error calling SSR/SRX" in capsys.readouterr().out

    def test_no_data_attr(self, ru: RoutingUtils) -> None:
        resp = MagicMock(spec=[])
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.showSiteSsrAndSrxRoutes.return_value = resp
            result = ru._execute_ssr_route_command("site-1", "dev-1", {}, False)
        assert result is None


# ===================================================================
# HELPER: _handle_routing_error & _cleanup_websocket
# ===================================================================


class TestErrorHandling:
    """Error handling and WebSocket cleanup."""

    def test_handle_routing_error(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._handle_routing_error("forwarding table", RuntimeError("test"), False)
        output = capsys.readouterr().out
        assert "forwarding table operation failed" in output

    def test_handle_routing_error_debug(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._handle_routing_error("routing", ValueError("bad"), True)
        output = capsys.readouterr().out
        assert "[DEBUG] Exception details" in output

    def test_cleanup_websocket_none(self, ru: RoutingUtils) -> None:
        ru._cleanup_websocket(None, False)  # should not raise

    def test_cleanup_websocket(self, ru: RoutingUtils) -> None:
        ws_mgr = MagicMock()
        ru._cleanup_websocket(ws_mgr, False)
        ws_mgr.disconnect.assert_called_once()

    def test_cleanup_websocket_error(self, ru: RoutingUtils) -> None:
        ws_mgr = MagicMock()
        ws_mgr.disconnect.side_effect = RuntimeError("cleanup fail")
        ru._cleanup_websocket(ws_mgr, False)  # should not raise


# ===================================================================
# ORCHESTRATORS: execute_* entry points
# ===================================================================


class TestExecuteShowForwardingTable:
    """Execute forwarding table end-to-end."""

    def test_no_site_selected(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].return_value = None
        ru.execute_show_forwarding_table()
        assert "No site selected" in capsys.readouterr().out

    def test_no_device_selected(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_device_fn"].return_value = None
        with patch("src.network.routing_utils.mistapi"):
            ru.execute_show_forwarding_table()
        assert "No gateway device selected" in capsys.readouterr().out

    def test_exception_handled(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].side_effect = RuntimeError("boom")
        ru.execute_show_forwarding_table()
        output = capsys.readouterr().out
        assert "operation failed" in output


class TestExecuteShowRoutingTable:
    """Execute routing table end-to-end."""

    def test_no_site_selected(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].return_value = None
        ru.execute_show_routing_table()
        assert "No site selected" in capsys.readouterr().out

    def test_no_device_selected(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_device_fn"].return_value = None
        with patch("src.network.routing_utils.mistapi"):
            ru.execute_show_routing_table()
        assert "No device selected" in capsys.readouterr().out

    def test_keyboard_interrupt(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].side_effect = KeyboardInterrupt()
        ru.execute_show_routing_table()
        assert "interrupted by user" in capsys.readouterr().out


class TestExecuteShowSsrRoutes:
    """Execute SSR/SRX routes end-to-end."""

    def test_no_site_selected(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].return_value = None
        ru.execute_show_ssr_routes()
        assert "No site selected" in capsys.readouterr().out

    def test_no_device_selected(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_device_fn"].return_value = None
        with patch("src.network.routing_utils.mistapi"):
            ru.execute_show_ssr_routes()
        assert "No device selected" in capsys.readouterr().out

    def test_keyboard_interrupt(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].side_effect = KeyboardInterrupt()
        ru.execute_show_ssr_routes()
        assert "interrupted by user" in capsys.readouterr().out

    def test_exception_handled(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_deps["select_site_fn"].side_effect = RuntimeError("fail")
        ru.execute_show_ssr_routes()
        assert "operation failed" in capsys.readouterr().out


# ===================================================================
# PROCESS RESULTS helpers
# ===================================================================


class TestProcessForwardingTableResults:
    """Process forwarding table WebSocket results."""

    def test_with_result(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1"}]),
            "session": "sess-1",
        }
        ru._process_forwarding_table_results(ws_mgr, "sess-1", "dev-1", None, False)
        output = capsys.readouterr().out
        assert "FORWARDING TABLE RESULTS" in output

    def test_timeout(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = None
        ru._process_forwarding_table_results(ws_mgr, "sess-1", "dev-1", None, False)
        output = capsys.readouterr().out
        assert "Timeout" in output


class TestProcessRoutingTableResults:
    """Process routing table WebSocket results."""

    def test_with_result(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1", "protocol": "BGP"}]),
            "session": "sess-1",
        }
        ru._process_routing_table_results(ws_mgr, "sess-1", "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "ROUTING TABLE RESULTS" in output

    def test_timeout(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = None
        ru._process_routing_table_results(ws_mgr, "sess-1", "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "Timeout" in output


class TestProcessSsrRouteResults:
    """Process SSR/SRX WebSocket results."""

    def test_with_result(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {
            "raw": json.dumps({"status": "SUCCESS", "columns": ["prefix"], "rows": [{"prefix": "10.0.0.0/8"}]}),
            "session": "sess-1",
        }
        ru._process_ssr_route_results(ws_mgr, "sess-1", "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "SSR/SRX ROUTING TABLE RESULTS" in output

    def test_timeout(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = None
        ru._process_ssr_route_results(ws_mgr, "sess-1", "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "Timeout" in output


# ===================================================================
# DISPLAY OUTPUT helpers
# ===================================================================


class TestDisplayForwardingTableOutput:
    """Display formatted forwarding table results."""

    def test_with_raw_output(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {"raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1"}]), "session": "s"}
        ru._display_forwarding_table_output(result, "dev-1", None, False)
        output = capsys.readouterr().out
        assert "10.0.0.0/8" in output

    def test_no_data(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {"session": "s"}
        ru._display_forwarding_table_output(result, "dev-1", None, False)
        output = capsys.readouterr().out
        assert "No forwarding table data" in output

    def test_with_output_field(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": "",
            "Output": json.dumps([{"prefix": "172.16.0.0/12"}]),
            "session": "s",
        }
        ru._display_forwarding_table_output(result, "dev-1", None, False)
        output = capsys.readouterr().out
        assert "ADDITIONAL OUTPUT" in output


class TestDisplayForwardingTableTimeout:
    """Display timeout message with troubleshooting."""

    def test_no_device_info(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_table_timeout(None)
        output = capsys.readouterr().out
        assert "Timeout" in output

    def test_gateway_device(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_table_timeout({"type": "gateway", "model": "SSR-1200"})
        output = capsys.readouterr().out
        assert "Gateway troubleshooting" in output

    def test_switch_device(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_table_timeout({"type": "switch", "model": "EX4300"})
        output = capsys.readouterr().out
        assert "Switch troubleshooting" in output

    def test_ap_device(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_forwarding_table_timeout({"type": "ap", "model": "AP45"})
        output = capsys.readouterr().out
        assert "Access Point troubleshooting" in output


class TestDisplayRoutingTableOutput:
    """Display formatted routing table results."""

    def test_with_raw_output(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1", "protocol": "BGP"}]),
            "session": "s",
        }
        ru._display_routing_table_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "ROUTING TABLE RESULTS" in output

    def test_no_data(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {"session": "s"}
        ru._display_routing_table_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "No routing table data" in output


class TestDisplaySsrRouteOutput:
    """Display formatted SSR/SRX routing results."""

    def test_ssr_format(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ssr_data = {
            "status": "SUCCESS",
            "message": "bgp routes",
            "columns": ["prefix"],
            "rows": [{"prefix": "10.0.0.0/8", "nextHops": "gw1", "vrfName": "default", "status": "active"}],
        }
        result = {"raw": json.dumps(ssr_data), "session": "s"}
        ru._display_ssr_route_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "SSR/SRX ROUTING TABLE RESULTS" in output

    def test_fallback_to_generic(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        # SSR parse fails (FAILED status) -> falls back to generic _parse_routing_table
        ssr_failed = {"status": "FAILED", "message": "not supported"}
        result = {
            "raw": json.dumps(ssr_failed),
            "session": "s",
        }
        ru._display_ssr_route_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "SSR/SRX ROUTING TABLE RESULTS" in output

    def test_no_data(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {"session": "s"}
        ru._display_ssr_route_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "No routing table data" in output


# ===================================================================
# SELECT DEVICE helpers
# ===================================================================


class TestSelectForwardingTableDevice:
    """Select site and device for forwarding table."""

    def test_no_site(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_site_fn"].return_value = None
        site, dev, info = ru._select_forwarding_table_device(False)
        assert site is None
        assert dev is None

    def test_no_device(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_device_fn"].return_value = None
        with patch("src.network.routing_utils.mistapi"):
            site, dev, info = ru._select_forwarding_table_device(False)
        assert dev is None

    def test_success(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "SSR"}]
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            site, dev, info = ru._select_forwarding_table_device(False)
        assert site == "site-1"
        assert dev == "dev-1"


class TestSelectRoutingTableDevice:
    """Select site and device for routing table."""

    def test_no_site(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_site_fn"].return_value = None
        site, dev, info = ru._select_routing_table_device(False)
        assert site is None

    def test_no_device(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_device_fn"].return_value = None
        with patch("src.network.routing_utils.mistapi"):
            site, dev, info = ru._select_routing_table_device(False)
        assert dev is None

    def test_guidance_cancel(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "SSR"}]
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            site, dev, info = ru._select_routing_table_device(False)
        assert site is None


class TestSelectSsrDevice:
    """Select site and SSR/SRX device."""

    def test_no_site(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_site_fn"].return_value = None
        site, dev, info = ru._select_ssr_device(False)
        assert site is None

    def test_no_device(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_device_fn"].return_value = None
        with patch("src.network.routing_utils.mistapi"):
            site, dev, info = ru._select_ssr_device(False)
        assert dev is None

    def test_compatibility_cancel(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "Other"}]
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            site, dev, info = ru._select_ssr_device(False)
        assert site is None


# ===================================================================
# ADDITIONAL COVERAGE: forwarding summary with multi-table, prefix groups
# ===================================================================


class TestDisplayForwardingSummaryDetailed:
    """Cover the multi-table and prefix group branches."""

    def test_multi_table_and_prefix_groups(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.1.0.0/16",
                "next_hop": "gw1",
                "interface": "eth0",
                "service": "internet",
                "table": "main",
                "type": "",
            },
            {
                "destination": "10.2.0.0/16",
                "next_hop": "gw2",
                "interface": "eth1",
                "service": "corp",
                "table": "vrf1",
                "type": "",
            },
        ]
        ru._display_forwarding_summary(entries)
        output = capsys.readouterr().out
        assert "Forwarding tables:" in output
        assert "Top prefix groups:" in output


class TestDisplayPrefixTableImplException:
    """Cover PrettyTable exception fallback."""

    def test_prettytable_exception_fallback(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [{"destination": "10.0.0.0/8", "next_hop": "gw1", "interface": "eth0", "service": "svc"}]
        with patch("src.network.routing_utils.PrettyTable", side_effect=RuntimeError("fail")):
            ru._display_prefix_table_impl(entries)
        output = capsys.readouterr().out
        assert "10.0.0.0/8" in output
        assert "gw1" in output


# ===================================================================
# ADDITIONAL COVERAGE: _display_routing_details exception fallback
# ===================================================================


class TestDisplayRoutingDetailsException:
    """Cover PrettyTable exception fallback for routing details."""

    def test_prettytable_exception_fallback(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "interface": "eth0",
                "protocol": "BGP",
                "active": True,
                "selected": True,
                "admin_distance": "170",
            },
        ]
        with patch("src.network.routing_utils.PrettyTable", side_effect=RuntimeError("fail")):
            ru._display_routing_details(entries)
        output = capsys.readouterr().out
        assert "10.0.0.0/8" in output
        assert "Active route" in output


# ===================================================================
# ADDITIONAL COVERAGE: _display_ssr_routing details + exception
# ===================================================================


class TestDisplaySsrRoutingDetailed:
    """Cover SSR display with protocols summary and exception fallback."""

    def test_protocol_summary(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "protocol": "BGP",
                "name": "r1",
                "status": "active",
                "selection_reason": "best",
                "weight": "0",
                "metric": "100",
                "local_preference": "100",
                "as_path": "65001",
                "vrf": "default",
            },
            {
                "destination": "172.16.0.0/12",
                "next_hop": "gw2",
                "protocol": "OSPF",
                "name": "r2",
                "status": "active",
                "selection_reason": "best",
                "weight": "0",
                "metric": "10",
                "local_preference": "",
                "as_path": "",
                "vrf": "mgmt",
            },
        ]
        ru._display_ssr_routing(entries)
        output = capsys.readouterr().out
        assert "BGP" in output
        assert "OSPF" in output
        assert "Total routing table entries: 2" in output

    def test_prettytable_exception_fallback(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "protocol": "BGP",
                "name": "r1",
                "status": "active",
                "selection_reason": "best",
                "weight": "0",
                "metric": "100",
                "local_preference": "100",
                "as_path": "65001",
                "vrf": "default",
            },
        ]
        with patch("src.network.routing_utils.PrettyTable", side_effect=RuntimeError("fail")):
            ru._display_ssr_routing(entries)
        output = capsys.readouterr().out
        assert "10.0.0.0/8" in output


class TestDisplaySsrRoutingQueryParams:
    """Cover empty entries with query params."""

    def test_empty_with_params(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru._display_ssr_routing([], {"protocol": "bgp"})
        output = capsys.readouterr().out
        assert "protocol: bgp" in output


# ===================================================================
# ADDITIONAL COVERAGE: _display_routing_summary with protocol counting
# ===================================================================


class TestDisplayRoutingSummaryDetailed:
    """Cover protocol counting and active/total reporting."""

    def test_multi_protocol_summary(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        entries = [
            {
                "destination": "10.0.0.0/8",
                "next_hop": "gw1",
                "interface": "eth0",
                "protocol": "BGP",
                "table": "inet.0",
                "active": True,
                "admin_distance": "170",
            },
            {
                "destination": "172.16.0.0/12",
                "next_hop": "gw2",
                "interface": "eth1",
                "protocol": "OSPF",
                "table": "inet.0",
                "active": False,
                "admin_distance": "110",
            },
        ]
        ru._display_routing_summary(entries)
        output = capsys.readouterr().out
        assert "Total routing table entries: 2" in output
        assert "BGP" in output
        assert "OSPF" in output
        assert "Active routes (marked with >):" in output


# ===================================================================
# ADDITIONAL COVERAGE: debug mode paths in _execute_*_command
# ===================================================================


class TestExecuteForwardingTableCommandDebug:
    """Cover debug output paths."""

    def test_debug_output(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session": "sess-abc-123"}
        mock_resp.text = '{"session": "sess-abc-123"}'
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_forwarding_table_command("site-1", "dev-1", {"prefix": "0.0.0.0/0"}, True)
        output = capsys.readouterr().out
        assert "[DEBUG] POST URL" in output
        assert "[DEBUG] HTTP Response Status" in output
        assert result == "sess-abc-123"


class TestExecuteRoutingTableCommandDebug:
    """Cover debug output paths in routing table command."""

    def test_debug_output(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session": "sess-def-456"}
        mock_resp.text = '{"session": "sess-def-456"}'
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_routing_table_command("site-1", "dev-1", {"protocol": "any"}, True)
        output = capsys.readouterr().out
        assert "[DEBUG]" in output
        assert result == "sess-def-456"


class TestExecuteSsrRouteCommandDebug:
    """Cover debug paths in SSR command."""

    def test_debug_output(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        resp = MagicMock()
        resp.data = {"session": "ssr-sess-789"}
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.showSiteSsrAndSrxRoutes.return_value = resp
            result = ru._execute_ssr_route_command("site-1", "dev-1", {"protocol": "bgp"}, True)
        output = capsys.readouterr().out
        assert "[DEBUG]" in output
        assert result == "ssr-sess-789"


# ===================================================================
# ADDITIONAL COVERAGE: _display_forwarding_table_output with debug + Output
# ===================================================================


class TestDisplayForwardingTableOutputDebug:
    """Cover debug mode and additional output fields."""

    def test_debug_extra_fields(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1"}]),
            "session": "s",
            "extra_field": "extra_value",
        }
        ru._display_forwarding_table_output(result, "dev-1", None, True)
        output = capsys.readouterr().out
        assert "[DEBUG] OTHER AVAILABLE FIELDS" in output

    def test_device_info_in_log(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1"}]),
            "session": "s",
        }
        ru._display_forwarding_table_output(result, "dev-1", {"type": "gateway", "name": "gw-main"}, False)
        output = capsys.readouterr().out
        assert "10.0.0.0/8" in output


# ===================================================================
# ADDITIONAL COVERAGE: _display_routing_table_output with debug + Output
# ===================================================================


class TestDisplayRoutingTableOutputDebug:
    """Cover debug mode and additional output fields."""

    def test_debug_extra_fields(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1", "protocol": "BGP"}]),
            "session": "s",
            "extra_field": "extra_value",
        }
        ru._display_routing_table_output(result, "dev-1", None, {}, True)
        output = capsys.readouterr().out
        assert "[DEBUG]" in output

    def test_with_output_field(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1", "protocol": "BGP"}]),
            "Output": json.dumps([{"prefix": "172.16.0.0/12", "nextHop": "gw2", "protocol": "OSPF"}]),
            "session": "s",
        }
        ru._display_routing_table_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "ADDITIONAL OUTPUT" in output

    def test_device_info_in_log(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        result = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1", "protocol": "BGP"}]),
            "session": "s",
        }
        ru._display_routing_table_output(result, "dev-1", {"type": "switch", "name": "sw-core"}, {}, False)
        output = capsys.readouterr().out
        assert "ROUTING TABLE RESULTS" in output


# ===================================================================
# ADDITIONAL COVERAGE: _display_ssr_route_output with debug + Output + device_info
# ===================================================================


class TestDisplaySsrRouteOutputDebug:
    """Cover debug and Output fields in SSR display."""

    def test_debug_extra_fields(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ssr_data = {
            "status": "SUCCESS",
            "columns": ["prefix"],
            "rows": [{"prefix": "10.0.0.0/8", "nextHops": "gw1", "vrfName": "default", "status": "active"}],
        }
        result = {
            "raw": json.dumps(ssr_data),
            "session": "s",
            "extra_field": "extra_value",
        }
        ru._display_ssr_route_output(result, "dev-1", None, {}, True)
        output = capsys.readouterr().out
        assert "[DEBUG]" in output

    def test_with_output_field(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ssr_data = {
            "status": "SUCCESS",
            "columns": ["prefix"],
            "rows": [{"prefix": "10.0.0.0/8", "nextHops": "gw1", "vrfName": "default", "status": "active"}],
        }
        ssr_data_alt = {
            "status": "SUCCESS",
            "columns": ["prefix"],
            "rows": [{"prefix": "172.16.0.0/12", "nextHops": "gw2", "vrfName": "mgmt", "status": "active"}],
        }
        result = {
            "raw": json.dumps(ssr_data),
            "Output": json.dumps(ssr_data_alt),
            "session": "s",
        }
        ru._display_ssr_route_output(result, "dev-1", None, {}, False)
        output = capsys.readouterr().out
        assert "ADDITIONAL OUTPUT" in output

    def test_device_info_in_log(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ssr_data = {
            "status": "SUCCESS",
            "columns": ["prefix"],
            "rows": [{"prefix": "10.0.0.0/8", "nextHops": "gw1"}],
        }
        result = {"raw": json.dumps(ssr_data), "session": "s"}
        ru._display_ssr_route_output(result, "dev-1", {"type": "gateway", "name": "ssr-edge"}, {}, False)
        output = capsys.readouterr().out
        assert "SSR/SRX ROUTING TABLE RESULTS" in output


# ===================================================================
# ADDITIONAL COVERAGE: full orchestrator happy path
# ===================================================================


class TestExecuteShowForwardingTableHappyPath:
    """Cover the full happy path through the forwarding table orchestrator."""

    def test_full_flow(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        # _get_device_info returns gateway
        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "SSR-1200"}]

        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        ws_mgr.wait_for_command_result.return_value = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1"}]),
            "session": "sess-1",
        }
        mock_deps["websocket_manager_factory"].return_value = ws_mgr

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.json.return_value = {"session": "sess-abc"}

        with (
            patch("src.network.routing_utils.mistapi") as mock_api,
            patch("src.network.routing_utils.requests") as mock_req,
            patch("src.network.routing_utils.time"),
        ):
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            mock_req.post.return_value = mock_http_resp
            ru.apisession.host = "api.mist.com"
            ru.apisession.apitoken = "token123"
            ru.execute_show_forwarding_table()

        ws_mgr.disconnect.assert_called()


class TestExecuteShowRoutingTableHappyPath:
    """Cover the full happy path through the routing table orchestrator."""

    def test_full_flow(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        mock_deps["select_device_fn"].return_value = "dev-1"

        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "switch", "model": "EX4300"}]

        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        ws_mgr.wait_for_command_result.return_value = {
            "raw": json.dumps([{"prefix": "10.0.0.0/8", "nextHop": "gw1", "protocol": "BGP"}]),
            "session": "sess-2",
        }
        mock_deps["websocket_manager_factory"].return_value = ws_mgr

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.json.return_value = {"session": "sess-def"}

        with (
            patch("src.network.routing_utils.mistapi") as mock_api,
            patch("src.network.routing_utils.requests") as mock_req,
            patch("src.network.routing_utils.time"),
        ):
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            mock_req.post.return_value = mock_http_resp
            ru.apisession.host = "api.mist.com"
            ru.apisession.apitoken = "token123"
            ru.execute_show_routing_table()

        ws_mgr.disconnect.assert_called()


class TestExecuteShowSsrRoutesHappyPath:
    """Cover the full happy path through SSR routes orchestrator."""

    def test_full_flow(self, ru: RoutingUtils, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""

        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "SSR-1200"}]

        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        ssr_result = {
            "status": "SUCCESS",
            "columns": ["prefix"],
            "rows": [{"prefix": "10.0.0.0/8", "nextHops": "gw1", "vrfName": "default", "status": "active"}],
        }
        ws_mgr.wait_for_command_result.return_value = {
            "raw": json.dumps(ssr_result),
            "session": "sess-3",
        }
        mock_deps["websocket_manager_factory"].return_value = ws_mgr

        api_resp = MagicMock()
        api_resp.data = {"session": "ssr-sess"}

        with (
            patch("src.network.routing_utils.mistapi") as mock_api,
            patch("src.network.routing_utils.time"),
        ):
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            mock_api.api.v1.sites.devices.showSiteSsrAndSrxRoutes.return_value = api_resp
            ru.execute_show_ssr_routes()

        ws_mgr.disconnect.assert_called()


# ===================================================================
# ADDITIONAL COVERAGE: env var fallback for host/token
# ===================================================================


class TestExecuteForwardingTableCommandEnvFallback:
    """Cover environment variable fallback for host/token."""

    def test_env_fallback(self, ru: RoutingUtils) -> None:
        ru.apisession.host = None
        ru.apisession.apitoken = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session": "env-sess"}
        with (
            patch("src.network.routing_utils.requests") as mock_req,
            patch.dict("os.environ", {"MIST_HOST": "env.mist.com", "MIST_APITOKEN": "env-tok"}),
        ):
            mock_req.post.return_value = mock_resp
            result = ru._execute_forwarding_table_command("site-1", "dev-1", {}, False)
        assert result == "env-sess"


class TestExecuteRoutingTableCommandEnvFallback:
    """Cover environment variable fallback for routing command."""

    def test_env_fallback(self, ru: RoutingUtils) -> None:
        ru.apisession.host = None
        ru.apisession.apitoken = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session": "env-sess-r"}
        with (
            patch("src.network.routing_utils.requests") as mock_req,
            patch.dict("os.environ", {"MIST_HOST": "env.mist.com", "MIST_APITOKEN": "env-tok"}),
        ):
            mock_req.post.return_value = mock_resp
            result = ru._execute_routing_table_command("site-1", "dev-1", {}, False)
        assert result == "env-sess-r"

    def test_no_host_no_env(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        ru.apisession.host = None
        ru.apisession.apitoken = None
        with patch.dict("os.environ", {}, clear=True):
            result = ru._execute_routing_table_command("site-1", "dev-1", {}, False)
        assert result is None

    def test_no_session_in_response(self, ru: RoutingUtils) -> None:
        ru.apisession.host = "api.mist.com"
        ru.apisession.apitoken = "token123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        with patch("src.network.routing_utils.requests") as mock_req:
            mock_req.post.return_value = mock_resp
            result = ru._execute_routing_table_command("site-1", "dev-1", {}, False)
        assert result is None


# ===================================================================
# ADDITIONAL COVERAGE: _get_device_info debug mode
# ===================================================================


class TestGetDeviceInfoDebug:
    """Cover debug mode paths in device info retrieval."""

    def test_debug_output(self, ru: RoutingUtils, capsys: pytest.CaptureFixture[str]) -> None:
        resp = MagicMock()
        resp.data = [{"id": "dev-1", "type": "gateway", "model": "SSR"}]
        with patch("src.network.routing_utils.mistapi") as mock_api:
            mock_api.api.v1.sites.devices.listSiteDevices.return_value = resp
            result = ru._get_device_info("site-1", "dev-1", "all", True)
        assert result is not None
        output = capsys.readouterr().out
        assert "[DEBUG]" in output


# ===================================================================
# ADDITIONAL COVERAGE: _connect_websocket debug mode
# ===================================================================


class TestConnectWebsocketDebug:
    """Cover debug paths in WebSocket connection."""

    def test_debug_output(
        self, ru: RoutingUtils, mock_deps: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        with patch("src.network.routing_utils.time"):
            result = ru._connect_websocket("site-1", "dev-1", True)
        assert result is ws_mgr
        output = capsys.readouterr().out
        assert "[DEBUG]" in output
