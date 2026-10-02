"""Native fleet pages retain evidence without changing settle decisions."""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade import gate
from tests.unit.upgrade_portal.capture_page_loss.cases import Cases, NativePages, OfflineChecks, OfflineSession


class TestFleetPageLoss(OfflineChecks):
    """Assert the actual FleetRead, exact query, and pure downstream decisions."""

    @pytest.mark.parametrize("fault", Cases.FAILURES, ids=[fault[0] for fault in Cases.FAILURES])
    def test_later_http_4xx_5xx_malformed_json_empty_body_and_none(self, fault: tuple[Any, ...]) -> None:
        """Every later refusal reports its own status beside the retained reading."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, fault))
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result == gate.FleetRead(
            {"001122000001": gate.GateReading("001122000001", "23.4R2.13", 46, 1001)},
            [NativePages.reason(endpoint.section, fault[1])],
        )
        self.assert_calls(session, endpoint)

    def test_whole_pages_keep_every_reading_and_no_partial_reason(self) -> None:
        """The fleet still reads all families with the exact original fields."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        expected = {
            f"0011220000{number:02x}": gate.GateReading(
                f"0011220000{number:02x}", "23.4R2.13", 45 + number, 1000 + number
            )
            for number in range(1, 4)
        }
        assert (result.readings, result.partial_reasons) == (expected, [])
        self.assert_calls(session, endpoint, good=3, lost=False)

    def test_fault_after_two_good_pages_keeps_both_readings(self) -> None:
        """A failed third page preserves both prior native readings."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[5], good=2))
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result.readings == {
            "001122000001": gate.GateReading("001122000001", "23.4R2.13", 46, 1001),
            "001122000002": gate.GateReading("001122000002", "23.4R2.13", 47, 1002),
        }
        assert result.partial_reasons == [NativePages.reason(endpoint.section, 503)]
        self.assert_calls(session, endpoint, good=2)

    @pytest.mark.parametrize("error", [TimeoutError("offline timeout"), ConnectionError("offline connection error")])
    def test_timeout_and_connection_error_keep_the_available_reading(self, error: Exception) -> None:
        """A raised later fault does not replace available evidence with an empty fleet."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        session.faults[endpoint.link(2)] = error
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result.readings == {"001122000001": gate.GateReading("001122000001", "23.4R2.13", 46, 1001)}
        assert result.partial_reasons == [NativePages.reason(endpoint.section, 0)]
        self.assert_calls(session, endpoint)

    def test_valid_empty_fleet_remains_successful(self) -> None:
        """A valid zero-row response carries no partial reason."""
        session = OfflineSession()
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result == gate.FleetRead({}, [])
        self.assert_calls(session, Cases.ENDPOINTS["fleet"], good=1, lost=False)

    @pytest.mark.parametrize("fault", [Cases.FAILURES[0], Cases.FAILURES[5], Cases.FAILURES[6], Cases.FAILURES[-1]])
    def test_first_page_fault_keeps_its_status_and_classification(self, fault: tuple[Any, ...]) -> None:
        """No first-page fault may request a next page or escape the fleet boundary."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.install(endpoint, [NativePages.failure(endpoint, fault, page=1)])
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        reason = (
            "read_failed" if fault[1] == 0 else "unexpected_response_shape" if fault[1] == 200 else "cloud_error_status"
        )
        assert result == gate.FleetRead({}, [NativePages.reason(endpoint.section, fault[1], reason)])
        self.assert_calls(session, endpoint, good=1, lost=False)

    @pytest.mark.parametrize("record", [None, "not a record", 5])
    def test_malformed_later_record_stays_inside_the_fleet_boundary(self, record: Any) -> None:
        """The fleet keeps the prior reading rather than crashing during row conversion."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        pages = NativePages.series(endpoint, None, good=3)
        pages[1] = endpoint.answer([record], 2, 3)
        session.install(endpoint, pages)
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result == gate.FleetRead(
            {"001122000001": gate.GateReading("001122000001", "23.4R2.13", 46, 1001)},
            [NativePages.reason(endpoint.section, 200)],
        )
        self.assert_calls(session, endpoint)

    def test_initial_transport_and_malformed_record_failures_remain_visible(self) -> None:
        """The first-page error boundary also contains the reading conversion."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.first[endpoint.path] = TimeoutError("offline initial timeout")
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result == gate.FleetRead({}, [NativePages.reason(endpoint.section, 0, "read_failed")])
        session.install(endpoint, [endpoint.answer([None], 1, 1)])
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result == gate.FleetRead({}, [NativePages.reason(endpoint.section, 0, "read_failed")])
        assert session.links == []

    def test_partial_read_keeps_the_existing_settle_wait_and_missing_evidence_rule(self) -> None:
        """Available evidence can advance, but an absent reading never proves a reboot."""
        endpoint = Cases.ENDPOINTS["fleet"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[4]))
        result = gate.read_fleet_statistics(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        target = gate.GateTarget("001122000001", "switch", "21.4R3.15", 9000, "23.4R2.13")
        signals = gate.GateSignals(reconnected=True, reading=result.readings[target.mac])
        progress = gate.advance(target, gate.GateProgress(), signals, 1000.0)
        assert progress == gate.GateProgress(True, 1000.0, None, "23.4R2.13", 1001)
        assert gate.is_settled(gate.advance(target, progress, gate.GateSignals(), 1059.0)) is False
        assert gate.is_settled(gate.advance(target, progress, gate.GateSignals(), 1060.0)) is True
        missing = gate.GateTarget("001122000002", "switch", "21.4R3.15", 9000, "23.4R2.13")
        assert gate.advance(
            missing, gate.GateProgress(), gate.GateSignals(reconnected=True), 1060.0
        ) == gate.GateProgress(reconnected=True)
        assert result.partial_reasons == [NativePages.reason(endpoint.section, 503)]
