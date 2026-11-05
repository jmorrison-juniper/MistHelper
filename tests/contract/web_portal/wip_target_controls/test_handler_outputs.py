"""Prove the actual handlers, native SDK calls, local files, and output notices."""

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
import requests

from tests.support.wip_target_controls.native import NativeScenario
from tests.support.wip_target_controls.portal import ControlledPortal, OwnedOutputLifecycle
from web_portal.app import WebPortalApp
from web_portal.services.operation import OperationExecutor

WIFI_ROW = dict(
    data_source="client",
    hostname="Client",
    mac="aabbccddeeff",
    session_count="1",
    session_ssid="Lab",
    session_timestamp="100",
    site_id="site-alpha",
    site_name="Lab Site",
)


@pytest.fixture
def portal(tmp_path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> Iterator[ControlledPortal]:
    """Keep the real input bridge and local writer inside one owned temporary root."""
    caplog.set_level(logging.INFO)
    scenario = NativeScenario(tmp_path, monkeypatch)
    scenario.install()
    scenario.seed_site_cache()
    built = ControlledPortal(scenario)
    try:
        yield built
    finally:
        WebPortalApp.shutdown_app(built.app)
        built.executor._pool.shutdown(wait=True)
        assert scenario.network.calls == []
        OwnedOutputLifecycle.close(scenario)


class TestActualVirtualChassisOutput:
    """Menu 63 must reach the selected switch and produce a genuine VC result."""

    @staticmethod
    def _require_native_vc_calls(scenario: NativeScenario) -> None:
        """Require the exact selected native endpoint and both actual local writes."""
        assert scenario.session.calls == [
            {"uri": "/api/v1/sites/site-alpha/devices", "query": {"type": "all"}},
            {"uri": "/api/v1/sites/site-alpha/devices", "query": {"type": "all"}},
            {"uri": "/api/v1/sites/site-alpha/devices/switch-alpha/vc", "query": {}},
        ]
        assert [call["endpoint"] for call in scenario.router.calls] == [
            "getOrgInventory",
            "getSiteDeviceVirtualChassis",
        ]
        assert scenario.router.format_write.call_count == 2
        assert scenario.router.csv_write.call_count == 2

    def test_selected_switch_reaches_the_real_vc_handler_once(self, portal: ControlledPortal) -> None:
        """Neither cache discovery nor a fake output notice satisfies this contract."""
        result = portal.run("63", ["Lab Site", "Lab Switch"])
        scenario = portal.scenario
        assert result["status"] == "completed"
        assert result["output_files"] == ["VirtualChassis_Lab_Switch.csv", "SiteInventory.csv"]
        self._require_native_vc_calls(scenario)
        rows = scenario.read_rows("VirtualChassis_Lab_Switch.csv")
        assert rows == [{"members_0_serial": "CONTROLLED", "members_0_role": "master", "preprovisioned": "False"}]
        messages = [record["message"] for record in result["log_messages"]]
        assert "! Virtual chassis information exported to VirtualChassis_Lab_Switch.csv" in messages
        assert "   * Records exported: 1" in messages
        print("Checked 1 actual VC handler, 2 inventory requests, 1 VC request, 1 VC record, and 0 live HTTP calls.")

    @pytest.mark.parametrize("empty", [{}, []])
    def test_empty_vc_has_a_visible_reason_without_a_fabricated_file(
        self, portal: ControlledPortal, empty: dict | list
    ) -> None:
        """An empty actual API response is a valid no-record result."""
        portal.scenario.session.replies["/api/v1/sites/site-alpha/devices/switch-alpha/vc"] = (200, empty)
        result = portal.run("63", ["Lab Site", "Lab Switch"])
        assert result["status"] == "completed"
        assert result["output_files"] == []
        assert result["completion_message"] == (
            "Operation completed with no output file: ! No virtual chassis data found for device Lab Switch"
        )
        assert not (portal.scenario.root / "data" / "VirtualChassis_Lab_Switch.csv").exists()
        assert [call["endpoint"] for call in portal.scenario.router.calls] == ["getOrgInventory"]
        assert sum(call["uri"].endswith("/vc") for call in portal.scenario.session.calls) == 1


class TestActualClientOutputPreservation:
    """Client output is distinct from the site prompt cache."""

    @staticmethod
    def _actual_csv_target(scenario: NativeScenario, logical_target: str) -> str:
        """Require the requested target and real write count without testing suffix formatting."""
        assert scenario.router.format_write.call_count == 1
        assert scenario.router.format_write.call_args.args[1] == logical_target
        assert scenario.router.csv_write.call_count == 1
        filename = scenario.router.csv_write.call_args.args[1]
        assert Path(filename).suffix.casefold() == ".csv"
        assert filename not in ("SiteList.csv", "SiteInventory.csv")
        return filename

    def test_wifi_clients_retain_the_real_target_rows_and_writer_counts(self, portal: ControlledPortal) -> None:
        """Prove the requested target and actual rows without owning the separate filename formatter contract."""
        result = portal.run("64", ["Lab Site"])
        assert result["status"] == "completed"
        filename = self._actual_csv_target(portal.scenario, "SiteWiFiClients.CSV")
        assert result["output_files"] == [filename]
        assert portal.scenario.session.calls == [
            {"uri": "/api/v1/sites/site-alpha/clients/search", "query": {"limit": "1000"}},
            {"uri": "/api/v1/sites/site-alpha/clients/sessions/search", "query": {"limit": "1000"}},
        ]
        assert [call["endpoint"] for call in portal.scenario.router.calls] == ["listSiteWirelessClientsStats"]
        assert portal.scenario.read_rows(filename) == [WIFI_ROW]
        assert any(
            "WiFi data exported to SiteWiFiClients.CSV (1 clients, 1 sessions, 1 total records)" in record["message"]
            for record in result["log_messages"]
        )
        print(
            "Checked 1 WiFi handler, 1 client request, 1 session request, 1 actual CSV record, and 0 live HTTP calls."
        )

    def test_client_statistics_retain_the_selected_site_result(self, portal: ControlledPortal) -> None:
        """The site-name lookup and statistics endpoint remain native source calls."""
        result = portal.run("65", ["Lab Site"])
        assert result["status"] == "completed"
        assert result["output_files"] == ["SiteClients_Lab_Site.csv"]
        assert portal.scenario.session.calls == [
            {"uri": "/api/v1/orgs/controlled-org/sites", "query": {"limit": "1000"}},
            {"uri": "/api/v1/sites/site-alpha/stats/clients", "query": {"limit": "1000"}},
        ]
        assert portal.scenario.read_rows("SiteClients_Lab_Site.csv") == [
            {"hostname": "Client", "mac": "aabbccddeeff", "rssi": "-42"}
        ]
        assert [call["endpoint"] for call in portal.scenario.router.calls] == ["listSiteWirelessClientsStats"]
        assert portal.scenario.router.format_write.call_count == 1
        assert portal.scenario.router.csv_write.call_count == 1
        assert "! 1 client records exported to SiteClients_Lab_Site.csv" in [
            record["message"] for record in result["log_messages"]
        ]
        print("Checked 1 statistics handler, 1 site lookup, 1 statistics request, 1 CSV record, and 0 live HTTP calls.")


class TestNativeTransportFailurePreservation:
    """Named transport failures must not report an empty or successful VC result."""

    @pytest.mark.parametrize(
        ("status", "failure"),
        [
            (None, requests.Timeout("Controlled VC timeout")),
            (None, requests.ConnectionError("Controlled VC connection error")),
            (403, requests.HTTPError("Controlled HTTP 403 VC failure")),
            (503, requests.HTTPError("Controlled HTTP 503 VC failure")),
        ],
        ids=["timeout", "connection_error", "http_4xx_403", "http_5xx_503"],
    )
    def test_native_vc_transport_failure_names_the_cause(
        self, portal: ControlledPortal, status: int | None, failure: requests.RequestException
    ) -> None:
        """Exercise the existing caught-error boundary without changing HTTP payload policy."""
        if status is not None:
            response = requests.Response()
            response.status_code = status
            failure.response = response
        portal.scenario.session.replies["/api/v1/sites/site-alpha/devices/switch-alpha/vc"] = failure
        result = portal.run("63", ["Lab Site", "Lab Switch"])
        assert OperationExecutor.get_run_status(portal.executor, result["run_id"]) == result
        assert result["status"] == "failed"
        assert str(failure) in result["error_message"]
        assert "No virtual chassis data" not in result["error_message"]
        assert not (portal.scenario.root / "data" / "VirtualChassis_Lab_Switch.csv").exists()
        assert [call["endpoint"] for call in portal.scenario.router.calls] == ["getOrgInventory"]
        assert sum(call["uri"].endswith("/vc") for call in portal.scenario.session.calls) == 1
