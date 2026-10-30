"""Run shipped WIP controls and actual handler outputs through the browser."""

import pytest
from playwright.sync_api import Page, expect

from tests.support.wip_target_controls.browser import BrowserCallbacks, BrowserJourney
from web_portal.services.operation import OperationExecutor


class TestCurrentWipControls:
    """Three current rows and one normal row must retain their real controls."""

    @staticmethod
    def _choose_switch(page: Page) -> None:
        """Select both real controls and require the intermediate Run refusal."""
        expect(page.get_by_test_id("param-site_id")).to_be_enabled()
        page.get_by_test_id("param-site_id").select_option("Lab Site")
        expect(page.get_by_test_id("param-device_id")).to_be_enabled()
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        page.get_by_test_id("param-device_id").select_option("Lab Switch")
        expect(page.get_by_test_id("run-btn")).to_be_enabled()

    @staticmethod
    def _require_vc_output(journey: BrowserJourney, result: dict) -> None:
        """Measure actual CSV rows, visible notices, and native exporter metadata."""
        scenario = journey.server.portal.scenario
        assert result["output_files"][0] == "VirtualChassis_Lab_Switch.csv"
        assert scenario.read_rows(result["output_files"][0]) == [
            {"members_0_serial": "CONTROLLED", "members_0_role": "master", "preprovisioned": "False"}
        ]
        expect(journey.page.locator("#outputFileList")).to_contain_text("VirtualChassis_Lab_Switch.csv")
        expect(journey.page.get_by_test_id("log-viewer")).to_contain_text("Virtual chassis information exported to")
        assert [call["endpoint"] for call in scenario.router.calls] == [
            "getOrgInventory",
            "getSiteDeviceVirtualChassis",
        ]
        assert scenario.router.format_write.call_count == 2
        assert scenario.router.csv_write.call_count == 2

    def test_switch_and_caution_appear_before_a_real_vc_run(
        self, wip_journey: BrowserJourney, selector_callbacks: BrowserCallbacks
    ) -> None:
        """This flow fails against the original missing-control and warning state."""
        page = wip_journey.page
        wip_journey.select("63")
        caution = page.get_by_test_id("wip-caution")
        expect(caution).to_be_visible()
        expect(caution).to_contain_text("Caution:")
        expect(caution).to_contain_text("Work In Progress")
        expect(caution).to_contain_text("Verify the result")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        self._choose_switch(page)
        result = wip_journey.run()
        self._require_vc_output(wip_journey, result)
        assert wip_journey.input_requests() == [
            {"menu_number": "63", "parameters": {"input_answers": ["Lab Site", "Lab Switch"]}}
        ]
        assert selector_callbacks.counts() == {"site": 1, "device": 1}
        assert wip_journey.server.portal.scenario.network.calls == []

    def test_empty_vc_keeps_the_visible_no_record_notice(self, wip_journey: BrowserJourney) -> None:
        """A real empty VC response must not create a success-shaped placeholder file."""
        scenario = wip_journey.server.portal.scenario
        scenario.session.replies["/api/v1/sites/site-alpha/devices/switch-alpha/vc"] = (200, {})
        wip_journey.select("63")
        page = wip_journey.page
        self._choose_switch(page)
        result = wip_journey.run()
        expect(page.locator("#statusMessage")).to_contain_text("No virtual chassis data found")
        expect(page.get_by_test_id("log-viewer")).to_contain_text("No virtual chassis data")
        assert result["status"] == "completed"
        assert result["output_files"] == []
        assert not (scenario.root / "data" / "VirtualChassis_Lab_Switch.csv").exists()

    @pytest.mark.parametrize("body", [b"bad json", b""], ids=["malformed_json", "empty_body"])
    def test_invalid_parameter_body_reports_failure_before_run(self, wip_journey: BrowserJourney, body: bytes) -> None:
        """A real malformed or empty response body must not admit an operation with no controls."""
        portal = wip_journey.server.portal
        portal.ledger.answers["/api/operations/parameters/63"] = (body, 200)
        wip_journey.select("63")
        expect(wip_journey.page.get_by_test_id("run-btn")).to_be_disabled()
        expect(wip_journey.page.locator("#parameterErrorMsg")).to_contain_text("status 200")
        assert wip_journey.input_requests() == []
        assert OperationExecutor.get_active_runs(portal.executor) == []
        assert portal.scenario.session.calls == []
        assert portal.scenario.router.csv_write.call_count == 0


class TestCurrentClientControls:
    """Preserve site-only controls, real writes, and target-versus-cache evidence."""

    @staticmethod
    def _export_client_rows(journey: BrowserJourney, number: str) -> None:
        """Select the actual site control and inspect the real writer's reported output."""
        page = journey.page
        journey.select(number)
        expect(page.get_by_test_id("wip-caution")).to_be_visible()
        expect(page.get_by_test_id("param-site_id")).to_be_enabled()
        expect(page.locator("#parameterFields select")).to_have_count(1)
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        page.get_by_test_id("param-site_id").select_option("Lab Site")
        result = journey.run()
        scenario = journey.server.portal.scenario
        filename = scenario.router.csv_write.call_args.args[1]
        assert result["output_files"] == [filename]
        assert filename not in ("SiteList.csv", "SiteInventory.csv")
        assert len(scenario.read_rows(filename)) == 1

    def test_client_rows_keep_one_site_and_normal_selection_clears_the_caution(
        self, wip_journey: BrowserJourney, selector_callbacks: BrowserCallbacks
    ) -> None:
        """Do not require a buggy filename or carry WIP guidance into a normal row."""
        for number in ("64", "65"):
            self._export_client_rows(wip_journey, number)
        page = wip_journey.page
        wip_journey.select("11")
        expect(page.get_by_test_id("wip-caution")).to_be_hidden()
        expect(page.locator("#parameterFields select")).to_have_count(0)
        expect(page.get_by_test_id("run-btn")).to_be_enabled()
        assert selector_callbacks.counts() == {"site": 2, "device": 0}
        boundary = wip_journey.server.portal.scenario.router
        assert [call.args[1] for call in boundary.format_write.call_args_list] == [
            "SiteWiFiClients.CSV",
            "SiteClients_Lab_Site.csv",
        ]
        assert boundary.csv_write.call_count == 2
        assert [call["endpoint"] for call in boundary.calls] == ["listSiteWirelessClientsStats"] * 2
        assert [call["parameters"]["input_answers"] for call in wip_journey.input_requests()] == [
            ["Lab Site"],
            ["Lab Site"],
        ]
        print("Checked 3 browser rows, 2 client runs, 2 real output records, and 1 normal-row caution reset.")
