"""Preserve required values, selector reasons, and keyboard recovery for menu 63."""

import json

import pytest
import requests
from playwright.sync_api import Locator, Page, expect

from tests.support.wip_target_controls.browser import BrowserCallbacks, BrowserJourney
from tests.support.wip_target_controls.native import NativeMistSession
from web_portal.services.operation import OperationExecutor


class TestUnavailableTargets:
    """Empty inventories and another device family must not supply a switch answer."""

    @pytest.mark.parametrize("inventory", [[], [{"id": "ap", "name": "Only AP", "type": "ap", "mac": "001122334499"}]])
    def test_no_switch_and_wrong_family_keep_run_disabled(
        self, wip_journey: BrowserJourney, selector_callbacks: BrowserCallbacks, inventory: list[dict]
    ) -> None:
        """The real switch-filtered native request must produce an explicit empty reason."""
        scenario = wip_journey.server.portal.scenario
        scenario.session.devices["site-alpha"] = inventory
        wip_journey.select("63")
        page = wip_journey.page
        expect(page.locator("#param-site_id")).to_be_enabled()
        page.locator("#param-site_id").select_option("Lab Site")
        device = page.locator("#param-device_id")
        expect(device).to_have_attribute("title", "The Mist API answered with no rows for this request.")
        expect(device).to_have_value("")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        assert scenario.session.calls == [
            {"uri": "/api/v1/orgs/controlled-org/sites", "query": {}},
            {"uri": "/api/v1/sites/site-alpha/devices", "query": {"type": "switch"}},
        ]
        assert selector_callbacks.counts() == {"site": 1, "device": 1}
        assert wip_journey.input_requests() == []
        assert scenario.router.calls == []

    @pytest.mark.parametrize(
        "fault",
        [(200, []), requests.Timeout("Controlled site timeout"), requests.ConnectionError("Controlled site failure")],
        ids=["empty_body_rows", "timeout", "connection_error"],
    )
    def test_site_empty_or_transport_failure_keeps_the_named_reason(
        self, wip_journey: BrowserJourney, fault: tuple[int, list] | requests.RequestException
    ) -> None:
        """A missing site cannot send a prompt answer or make a device request."""
        scenario = wip_journey.server.portal.scenario
        scenario.session.replies["/api/v1/orgs/controlled-org/sites"] = fault
        wip_journey.select("63")
        site = wip_journey.page.locator("#param-site_id")
        expect(site).to_be_enabled()
        reason = "The Mist API answered with no rows" if isinstance(fault, tuple) else type(fault).__name__
        assert reason in site.get_attribute("title")
        expect(site).to_have_value("")
        expect(wip_journey.page.get_by_test_id("run-btn")).to_be_disabled()
        assert len(scenario.session.calls) == 1
        assert wip_journey.input_requests() == []
        assert scenario.router.calls == []


class TestNamedFailuresAndRecovery:
    """HTTP and transport failures remain distinct from a valid empty list."""

    @staticmethod
    def _recover_at_another_site(page: Page, device: Locator) -> None:
        """Require a fresh unselected switch after the operator changes the site."""
        page.locator("#param-site_id").select_option("Recovery <Site>")
        expect(device.locator("option[value='Recovery <Switch>']")).to_have_count(1)
        expect(device).to_have_value("")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()

    @pytest.mark.parametrize(
        "status_case",
        [
            (403, json.dumps({"error": "Controlled HTTP 403 selector failure"}), "Controlled HTTP 403"),
            (503, json.dumps({"error": "Controlled HTTP 503 selector failure"}), "Controlled HTTP 503"),
            (200, b"bad json", "status 200"),
            (200, b"", "status 200"),
        ],
        ids=["http_4xx_403", "http_5xx_503", "malformed_json", "empty_body"],
    )
    def test_device_http_or_body_failure_names_the_cause_and_another_site_recovers(
        self, wip_journey: BrowserJourney, status_case: tuple[int, str | bytes, str]
    ) -> None:
        """Use exact HTTP boundaries while keeping current payload policy unchanged."""
        page = wip_journey.page
        portal = wip_journey.server.portal
        status, body, cause = status_case
        portal.ledger.answers["/api/operations/sites/site-alpha/devices"] = (body, status)
        wip_journey.select("63")
        expect(page.locator("#param-site_id")).to_be_enabled()
        page.locator("#param-site_id").select_option("Lab Site")
        device = page.locator("#param-device_id")
        expect(device).to_be_enabled()
        assert cause in device.get_attribute("title")
        assert "No devices found" not in device.get_attribute("title")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        self._recover_at_another_site(page, device)
        assert portal.scenario.session.calls[-1] == {
            "uri": "/api/v1/sites/site beta%?&/devices",
            "query": {"type": "switch"},
        }
        assert wip_journey.input_requests() == []
        assert OperationExecutor.get_active_runs(portal.executor) == []

    @pytest.mark.parametrize(
        "failure", [requests.Timeout("Device timeout"), requests.ConnectionError("Device connection")]
    )
    def test_native_device_transport_failure_is_not_a_no_devices_result(
        self, wip_journey: BrowserJourney, failure: requests.RequestException
    ) -> None:
        """The native SDK transport exception must keep its existing named failure reason."""
        portal = wip_journey.server.portal
        portal.scenario.session.replies["/api/v1/sites/site-alpha/devices"] = failure
        wip_journey.select("63")
        page = wip_journey.page
        expect(page.locator("#param-site_id")).to_be_enabled()
        page.locator("#param-site_id").select_option("Lab Site")
        device = page.locator("#param-device_id")
        expect(device).to_be_enabled()
        assert type(failure).__name__ in device.get_attribute("title")
        assert "No devices found" not in device.get_attribute("title")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        assert len(portal.scenario.session.calls) == 2
        assert wip_journey.input_requests() == []
        assert OperationExecutor.get_active_runs(portal.executor) == []


class TestTargetIdentityAndKeyboard:
    """Names remain text and identifiers remain separate native endpoint values."""

    @staticmethod
    def _select_targets_with_keyboard(page: Page) -> Locator:
        """Use the measured native type-ahead and Tab behavior on real labelled controls."""
        site = page.get_by_label("Site", exact=False)
        expect(site).to_be_enabled()
        site.focus()
        site.press("r")
        expect(site).to_have_value("Recovery <Site>")
        device = page.get_by_label("Switch", exact=False)
        expect(device).to_be_enabled()
        site.press("Tab")
        expect(device).to_be_focused()
        device.press("r")
        return device

    def test_encoded_site_escaped_names_and_keyboard_reach_the_selected_switch_once(
        self, wip_journey: BrowserJourney, selector_callbacks: BrowserCallbacks
    ) -> None:
        """The real input bridge resolves the safe labels to native site and device identities."""
        page = wip_journey.page
        wip_journey.select("63")
        device = self._select_targets_with_keyboard(page)
        expect(device).to_have_value("Recovery <Switch>")
        assert device.locator("option:checked").get_attribute("data-device-id") == "switch-beta"
        assert device.locator("option:checked").get_attribute("data-device-mac") == "001122334477"
        assert page.locator("#parameterFields img").count() == 0
        device.press("Tab")
        expect(page.get_by_test_id("run-btn")).to_be_focused()
        with page.expect_response(lambda response: response.url.endswith("/api/operations/run")) as started:
            page.keyboard.press("Enter")
        result = wip_journey.server.portal.wait(started.value.json()["run_id"])
        assert result["output_files"][0] == "VirtualChassis_Recovery_<Switch>.csv"
        assert wip_journey.input_requests()[0]["parameters"]["input_answers"] == [
            "Recovery <Site>",
            "Recovery <Switch>",
        ]
        assert selector_callbacks.counts() == {"site": 1, "device": 1}

    def test_clearing_or_changing_site_resets_the_required_switch(self, wip_journey: BrowserJourney) -> None:
        """A previous switch must not survive a blank or different site."""
        page = wip_journey.page
        wip_journey.select("63")
        expect(page.locator("#param-site_id")).to_be_enabled()
        page.locator("#param-site_id").select_option("Lab Site")
        expect(page.locator("#param-device_id")).to_be_enabled()
        page.locator("#param-device_id").select_option("Lab Switch")
        expect(page.get_by_test_id("run-btn")).to_be_enabled()
        page.locator("#param-site_id").select_option("")
        expect(page.locator("#param-device_id")).to_have_value("")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        page.locator("#param-site_id").select_option("Recovery <Site>")
        expect(page.locator("#param-device_id option[value='Recovery <Switch>']")).to_have_count(1)
        expect(page.locator("#param-device_id")).to_have_value("")
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        assert wip_journey.input_requests() == []


class TestPendingTargetResponses:
    """Pending metadata and previous device responses must not admit a stale run."""

    @pytest.mark.parametrize("status", [403, 503], ids=["http_4xx_403", "http_5xx_503"])
    def test_metadata_http_failure_keeps_run_disabled_and_retry_preserves_required_targets(
        self, wip_journey: BrowserJourney, status: int
    ) -> None:
        """A failed metadata request must not look like an operation with no required controls."""
        portal = wip_journey.server.portal
        path = "/api/operations/parameters/63"
        cause = f"Controlled HTTP {status} parameter failure"
        portal.ledger.answers[path] = (json.dumps({"error": cause}), status)
        wip_journey.select("63")
        page = wip_journey.page
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        expect(page.locator("#parameterError")).to_be_visible()
        expect(page.locator("#parameterErrorMsg")).to_have_text(cause)
        assert portal.scenario.session.calls == []
        assert wip_journey.input_requests() == []
        assert OperationExecutor.get_active_runs(portal.executor) == []
        portal.ledger.answers.pop(path)
        page.locator("#parameterError button").click()
        expect(page.get_by_label("Site", exact=False)).to_be_enabled()
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        expect(page.get_by_test_id("wip-caution")).to_be_visible()

    def test_run_waits_for_required_metadata(self, wip_journey: BrowserJourney) -> None:
        """The initial selection must not briefly enable Run before its target descriptors arrive."""
        page = wip_journey.page
        held = NativeMistSession.HeldResponse((200, {}))
        wip_journey.server.portal.ledger.holds["/api/operations/parameters/63"] = held
        page.locator("button.accordion-button", has_text="Work In Progress").click()
        page.locator('.op-item[data-menu="63"]').click()
        assert held.arrived.wait(10), "The actual parameter request did not reach its controlled hold."
        expect(page.get_by_test_id("wip-caution")).to_be_visible()
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        assert wip_journey.input_requests() == []
        held.release.set()
        expect(page.locator("#param-site_id")).to_be_enabled()
        expect(page.get_by_test_id("run-btn")).to_be_disabled()

    def test_previous_device_response_cannot_replace_another_site_selection(
        self, wip_journey: BrowserJourney, selector_callbacks: BrowserCallbacks
    ) -> None:
        """Release the actual old response after the current switch is selected."""
        portal = wip_journey.server.portal
        held = NativeMistSession.HeldResponse((200, portal.scenario.session.devices["site-alpha"][:1]))
        portal.scenario.session.replies["/api/v1/sites/site-alpha/devices"] = held
        wip_journey.select("63")
        page = wip_journey.page
        expect(page.locator("#param-site_id")).to_be_enabled()
        page.locator("#param-site_id").select_option("Lab Site")
        assert held.arrived.wait(10), "The old actual device request did not reach its controlled hold."
        expect(page.get_by_test_id("run-btn")).to_be_disabled()
        page.locator("#param-site_id").select_option("Recovery <Site>")
        expect(page.locator("#param-device_id option[value='Recovery <Switch>']")).to_have_count(1)
        page.locator("#param-device_id").select_option("Recovery <Switch>")
        with page.expect_response(lambda response: "/sites/site-alpha/devices" in response.url):
            held.release.set()
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        expect(page.locator("#param-device_id")).to_have_value("Recovery <Switch>")
        expect(page.locator("#param-device_id option[value='Lab Switch']")).to_have_count(0)
        expect(page.get_by_test_id("run-btn")).to_be_enabled()
        assert selector_callbacks.counts() == {"site": 1, "device": 2}
        assert wip_journey.input_requests() == []
