"""Real Chromium journeys through the actual controller, SDK, and packet card."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from src.websocket_streams.live.captures.runner import PacketCaptureRunner
from tests.e2e.websocket_streams.conftest import BrowserCapture
from tests.unit.websocket_streams.live.captures.support.sdk import Identities


class TestLongPacketBrowser:
    """Prove the operator duration and cloud stop without a replacement renderer."""

    @staticmethod
    def select_capture(page: Page, fixture: BrowserCapture) -> None:
        """Open the real tab and select its real SDK catalog entry."""
        page.goto(f"{fixture.url}/websockets", wait_until="networkidle")
        page.get_by_test_id("ws-catalog-entry-ap.remotePcapWired").click()
        page.get_by_test_id("ws-field-site_id").select_option(Identities.SITE)
        page.get_by_test_id("ws-field-device_id").select_option(Identities.DEVICE)

    @pytest.mark.parametrize("duration", [120, 3600])
    def test_card_receives_late_records_and_stop_reaches_cloud(
        self, page: Page, browser_capture: BrowserCapture, duration: int
    ) -> None:
        """Use a real short stream while the controlled clock spans the selected duration."""
        fixture = browser_capture
        self.select_capture(page, fixture)
        page.get_by_test_id("ws-field-duration").fill(str(duration))
        page.get_by_test_id("ws-field-num_packets").fill("10000")
        page.get_by_test_id("ws-start-button").click()
        expect(page.get_by_test_id("ws-session-state")).to_have_text("State: Live")
        assert fixture.stream.state.acknowledgements == 1
        for timestamp in [59, 61, duration - 1]:
            fixture.harness.clock.advance(timestamp)
            fixture.stream.packet(timestamp)
            expect(page.get_by_test_id("ws-output")).to_contain_text(f"{timestamp} 192.0.2.1 -> 192.0.2.2 TCP 64")
        page.get_by_test_id("ws-stop-button").click()
        expect(page.get_by_test_id("ws-session-state")).to_have_text("State: Stopped")
        expect(page.get_by_test_id("ws-session-reason")).to_contain_text("Mist accepted the stop request")
        names = [action[0] for action in fixture.harness.api.script.actions]
        assert names.count("POST") == names.count("DELETE") == 1
        session = next(iter(fixture.harness.manager._sessions.values()))
        assert isinstance(session.runner, PacketCaptureRunner)
        session.runner.worker.join(timeout=2.0)
        client = session.runner._monitor.connection.client
        assert not session.runner.worker.is_alive() and not client.ready()
        assert not client._thread.is_alive() and not client._callback_thread.is_alive()
        assert fixture.stream.state.clients == set()

    def test_form_has_exact_bounds_and_refuses_invalid_duration(
        self, page: Page, browser_capture: BrowserCapture
    ) -> None:
        """Run the actual JavaScript guard before any start request."""
        self.select_capture(page, browser_capture)
        duration = page.get_by_test_id("ws-field-duration")
        expect(duration).to_have_attribute("min", "60")
        expect(duration).to_have_attribute("max", "3600")
        expect(duration).to_have_value("60")
        for invalid in ["59", "3601", "٦٠", "9" * 5000]:
            duration.evaluate("(element, value) => { element.type = 'text'; element.value = value; }", invalid)
            page.get_by_test_id("ws-start-form").evaluate(
                "form => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))"
            )
            expect(page.get_by_test_id("ws-start-error")).to_have_text("Type a whole duration from 60 to 3600 seconds.")
        assert [action[0] for action in browser_capture.harness.api.script.actions].count("POST") == 0
        assert browser_capture.stream.state.acknowledgements == 0

    def test_failed_cloud_stop_stays_failed_on_the_card(self, page: Page, browser_capture: BrowserCapture) -> None:
        """Show a refused DELETE instead of a successful stream-only stop."""
        fixture = browser_capture
        self.select_capture(page, fixture)
        page.get_by_test_id("ws-field-duration").fill("120")
        page.get_by_test_id("ws-start-button").click()
        expect(page.get_by_test_id("ws-session-state")).to_have_text("State: Live")
        fixture.stream.packet(1)
        expect(page.get_by_test_id("ws-output")).to_contain_text("192.0.2.1")
        fixture.harness.api.script.stop.status = 500
        page.get_by_test_id("ws-stop-button").click()
        expect(page.get_by_test_id("ws-session-state")).to_have_text("State: Failed")
        expect(page.get_by_test_id("ws-session-reason")).to_contain_text("HTTP 500")
        assert [action[0] for action in fixture.harness.api.script.actions].count("DELETE") == 1
        assert fixture.stream.state.clients == set()

    def test_packet_text_is_escaped_in_the_actual_card(self, page: Page, browser_capture: BrowserCapture) -> None:
        """Preserve text rendering rather than execute packet fields as markup."""
        fixture = browser_capture
        self.select_capture(page, fixture)
        page.get_by_test_id("ws-start-button").click()
        expect(page.get_by_test_id("ws-session-state")).to_have_text("State: Live")
        session = next(iter(fixture.harness.manager._sessions.values()))
        event = {
            "event": "data",
            "channel": f"/sites/{Identities.SITE}/pcaps",
            "data": {
                "capture_id": Identities.CAPTURE,
                "pcap_dict": {"src_ip": "<img src=x onerror=window.packetExecuted=1>"},
            },
        }
        session.runner._monitor.connection.feed.message(event)
        expect(page.get_by_test_id("ws-output")).to_contain_text("<img src=x onerror=window.packetExecuted=1>")
        assert page.get_by_test_id("ws-output").locator("img").count() == 0
        assert page.evaluate("window.packetExecuted") is None
