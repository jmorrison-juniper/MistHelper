"""Real capture device endpoints must report every lost later page."""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.capture import devices
from tests.unit.upgrade_portal.capture_page_loss.cases import Cases, NativePages, OfflineChecks, OfflineSession


class TestCapturePageLoss(OfflineChecks):
    """Cover physical inventory and all-family statistics at their real boundary."""

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    @pytest.mark.parametrize("fault", Cases.FAILURES, ids=[fault[0] for fault in Cases.FAILURES])
    def test_later_http_4xx_5xx_malformed_json_empty_body_and_none(self, name: str, fault: tuple[Any, ...]) -> None:
        """Keep the first page and the exact failed status for every native fault."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, fault))
        result = self.read(name, session)
        assert result == devices.DeviceRead(
            endpoint.section, [Cases.row(name)], [NativePages.reason(endpoint.section, fault[1])]
        )
        self.assert_calls(session, endpoint)

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    def test_whole_pages_preserve_values_and_order(self, name: str) -> None:
        """A complete paged read remains complete."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        result = self.read(name, session)
        assert (result.records, result.partial_reasons) == ([Cases.row(name, number) for number in range(1, 4)], [])
        self.assert_calls(session, endpoint, good=3, lost=False)

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    def test_fault_after_two_good_pages_preserves_both(self, name: str) -> None:
        """A failed third page must not discard the second valid page."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[5], good=2))
        result = self.read(name, session)
        assert result == devices.DeviceRead(
            endpoint.section, [Cases.row(name), Cases.row(name, 2)], [NativePages.reason(endpoint.section, 503)]
        )
        self.assert_calls(session, endpoint, good=2)

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    @pytest.mark.parametrize("error", [TimeoutError("offline timeout"), ConnectionError("offline connection error")])
    def test_timeout_and_connection_error_keep_prior_rows(self, name: str, error: Exception) -> None:
        """A raised later transport fault reports a lost page with status zero."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        session.faults[endpoint.link(2)] = error
        result = self.read(name, session)
        assert result == devices.DeviceRead(
            endpoint.section, [Cases.row(name)], [NativePages.reason(endpoint.section, 0)]
        )
        self.assert_calls(session, endpoint)

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    def test_valid_empty_read_has_no_partial_reason(self, name: str) -> None:
        """Zero rows do not prove a lost page."""
        session = OfflineSession()
        result = self.read(name, session)
        assert (result.records, result.partial_reasons) == ([], [])
        self.assert_calls(session, Cases.ENDPOINTS[name], good=1, lost=False)

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    def test_first_transport_exception_reports_the_existing_read_failure(self, name: str) -> None:
        """The actual initial SDK request can raise without an HTTP status."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.first[endpoint.path] = TimeoutError("offline initial timeout")
        result = self.read(name, session)
        assert (result.records, result.partial_reasons) == (
            [],
            [NativePages.reason(endpoint.section, 0, "read_failed")],
        )
        self.assert_calls(session, endpoint, good=1, lost=False)

    @pytest.mark.parametrize("name", ["inventory", "statistics"])
    @pytest.mark.parametrize("fault", [Cases.FAILURES[0], Cases.FAILURES[5], Cases.FAILURES[-1]])
    def test_first_page_fault_keeps_its_existing_classification(self, name: str, fault: tuple[Any, ...]) -> None:
        """A failed first page is not a lost later page and requests no next page."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, [NativePages.failure(endpoint, fault, page=1)])
        result = self.read(name, session)
        reason = "read_failed" if fault[1] == 0 else "cloud_error_status"
        assert (result.records, result.partial_reasons) == (
            [],
            [NativePages.reason(endpoint.section, fault[1], reason)],
        )
        self.assert_calls(session, endpoint, good=1, lost=False)

    @staticmethod
    def read(name: str, session: OfflineSession) -> devices.DeviceRead:
        """Call the actual public capture reader with its unchanged arguments."""
        if name == "inventory":
            return devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        return devices.read_device_statistics(session, Cases.SITE_ID, page_limit=1)
