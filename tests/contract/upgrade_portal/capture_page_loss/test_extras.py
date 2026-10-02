"""All four tier 3 endpoints must carry lost-page evidence into the final capture."""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.capture import extras
from tests.unit.upgrade_portal.capture_page_loss.cases import Cases, NativePages, OfflineChecks, OfflineSession


class TestFinalExtraCapture(OfflineChecks):
    """Check retained rows and both report-row and source names."""

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    @pytest.mark.parametrize("fault", Cases.FAILURES, ids=[fault[0] for fault in Cases.FAILURES])
    def test_later_http_4xx_5xx_malformed_json_empty_body_and_none(self, name: str, fault: tuple[Any, ...]) -> None:
        """Each final extra reason carries the lost page's status and available rows."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, fault))
        document = self.capture(session)
        self.assert_rows(document, name, good=1)
        assert document["partial_reasons"] == self.reasons(name, fault[1])
        assert document["capture_status"] == "partial"
        self.assert_calls(session, endpoint)

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    def test_whole_pages_preserve_rows_and_no_reason(self, name: str) -> None:
        """A complete extra read keeps its exact successful values and order."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        document = self.capture(session)
        self.assert_rows(document, name, good=3)
        assert (document["capture_status"], document["partial_reasons"]) == ("complete", [])
        self.assert_calls(session, endpoint, good=3, lost=False)

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    def test_fault_after_two_good_pages_keeps_both(self, name: str) -> None:
        """No extra reader may discard the second valid page after a failure."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[5], good=2))
        document = self.capture(session)
        self.assert_rows(document, name, good=2)
        assert document["partial_reasons"] == self.reasons(name, 503)
        self.assert_calls(session, endpoint, good=2)

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    @pytest.mark.parametrize("error", [TimeoutError("offline timeout"), ConnectionError("offline connection error")])
    def test_timeout_and_connection_error_keep_prior_extra_rows(self, name: str, error: Exception) -> None:
        """Transport exceptions become status zero, not the first page's success."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        session.faults[endpoint.link(2)] = error
        document = self.capture(session)
        self.assert_rows(document, name, good=1)
        assert document["partial_reasons"] == self.reasons(name, 0)
        self.assert_calls(session, endpoint)

    def test_valid_empty_extra_sections_remain_complete(self) -> None:
        """Every valid empty extra section carries no failure."""
        session = OfflineSession()
        document = self.capture(session)
        assert document["extras"] == dict.fromkeys(extras.SECTION_NAMES, [])
        assert (document["capture_status"], document["partial_reasons"]) == ("complete", [])
        assert session.links == []

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    @pytest.mark.parametrize("fault", [Cases.FAILURES[0], Cases.FAILURES[5], Cases.FAILURES[-1]])
    def test_first_page_refusal_keeps_the_existing_extra_status_reason(self, name: str, fault: tuple[Any, ...]) -> None:
        """A first-page status fault remains cloud_error_status, including an absent status."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, [NativePages.failure(endpoint, fault, page=1)])
        document = self.capture(session)
        self.assert_rows(document, name, good=0)
        expected = [dict(reason, reason="cloud_error_status") for reason in self.reasons(name, fault[1])]
        assert document["partial_reasons"] == expected
        assert document["capture_status"] == "partial"
        self.assert_calls(session, endpoint, good=1, lost=False)

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    @pytest.mark.parametrize("record", [None, "not a record", 5])
    def test_malformed_later_record_keeps_the_available_extra_rows(self, name: str, record: Any) -> None:
        """Malformed later rows stay inside the read boundary and preserve prior pages."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        pages = NativePages.series(endpoint, None, good=3)
        pages[1] = endpoint.answer([record], 2, 3)
        session.install(endpoint, pages)
        document = self.capture(session)
        self.assert_rows(document, name, good=1)
        assert document["partial_reasons"] == self.reasons(name, 200)
        self.assert_calls(session, endpoint)

    @pytest.mark.parametrize("name", ["ports", "tunnels", "bgp_peers", "alarms"])
    @pytest.mark.parametrize("broken_row", [False, True])
    def test_first_transport_or_record_error_keeps_the_existing_extra_failure(
        self, name: str, broken_row: bool
    ) -> None:
        """The optional section boundary remains loud for an initial exception."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        if broken_row:
            session.install(endpoint, [endpoint.answer([None], 1, 1)])
        else:
            session.first[endpoint.path] = TimeoutError("offline initial timeout")
        document = self.capture(session)
        self.assert_rows(document, name, good=0)
        assert document["partial_reasons"] == [
            dict(reason, reason="cloud_call_failed") for reason in self.reasons(name, 0)
        ]
        self.assert_calls(session, endpoint, good=1, lost=False)

    @staticmethod
    def reasons(name: str, status: int) -> list[dict[str, Any]]:
        """Preserve both port sources and the existing report-row mapping."""
        sources = ("switch_ports", "poe") if name == "ports" else (name,)
        row = "alarms" if name == "alarms" else "extras"
        return [{**NativePages.reason(row, status), "source": source} for source in sources]

    @staticmethod
    def assert_rows(document: dict[str, Any], name: str, good: int) -> None:
        """Check every retained value, including both shared port projections."""
        expected = [Cases.row(name, number) for number in range(1, good + 1)]
        if name != "ports":
            assert document["extras"][name] == expected
            return
        port_fields = (
            "mac",
            "port_id",
            "up",
            "speed",
            "full_duplex",
            "port_usage",
            "mac_count",
            "neighbor_mac",
            "neighbor_port_desc",
            "neighbor_system_name",
        )
        power_fields = ("mac", "port_id", "poe_disabled", "poe_mode", "poe_on", "poe_priority", "power_draw")
        assert document["extras"]["switch_ports"] == [
            {field: row.get(field) for field in port_fields} for row in expected
        ]
        assert document["extras"]["poe"] == [{field: row.get(field) for field in power_fields} for row in expected]
