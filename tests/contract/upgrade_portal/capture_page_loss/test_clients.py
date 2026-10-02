"""The real collector must retain wireless rows and reasons in its final capture."""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.capture import clients
from tests.unit.upgrade_portal.capture_page_loss.cases import Cases, NativePages, OfflineChecks, OfflineSession


class TestFinalWirelessCapture(OfflineChecks):
    """Check the actual document rather than a tuple that a caller can discard."""

    @pytest.mark.parametrize("fault", Cases.FAILURES, ids=[fault[0] for fault in Cases.FAILURES])
    def test_later_http_4xx_5xx_malformed_json_empty_body_and_none(self, fault: tuple[Any, ...]) -> None:
        """The final wireless reason names the real lost page and retains its prior client."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, fault))
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == [
            {"mac": "aabbcc000001", "hostname": "client-1", "device_mac": "001122000001", "ssid": "Corp", "rssi": -51}
        ]
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", fault[1]), "source": "wireless_statistics"}
        ]
        assert document["capture_status"] == "partial"
        self.assert_calls(session, endpoint)

    def test_whole_pages_keep_the_complete_join_and_no_reason(self) -> None:
        """Complete statistics retain values and the existing address order."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == [
            {
                "mac": f"aabbcc0000{number:02x}",
                "hostname": f"client-{number}",
                "device_mac": "001122000001",
                "ssid": "Corp",
                "rssi": -50 - number,
            }
            for number in range(1, 4)
        ]
        assert (document["capture_status"], document["partial_reasons"]) == ("complete", [])
        self.assert_calls(session, endpoint, good=3, lost=False)

    def test_fault_after_two_good_pages_keeps_both_clients(self) -> None:
        """The final capture retains all clients from both prior valid pages."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[5], good=2))
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == [
            {
                "mac": f"aabbcc0000{number:02x}",
                "hostname": f"client-{number}",
                "device_mac": "001122000001",
                "ssid": "Corp",
                "rssi": -50 - number,
            }
            for number in range(1, 3)
        ]
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", 503), "source": "wireless_statistics"}
        ]
        self.assert_calls(session, endpoint, good=2)

    @pytest.mark.parametrize("error", [TimeoutError("offline timeout"), ConnectionError("offline connection error")])
    def test_timeout_and_connection_error_preserve_the_first_client(self, error: Exception) -> None:
        """A later transport exception reaches the final capture with status zero."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        session.faults[endpoint.link(2)] = error
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == [
            {"mac": "aabbcc000001", "hostname": "client-1", "device_mac": "001122000001", "ssid": "Corp", "rssi": -51}
        ]
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", 0), "source": "wireless_statistics"}
        ]
        self.assert_calls(session, endpoint)

    def test_valid_empty_clients_remain_complete(self) -> None:
        """An empty successful statistics list must not create a failure."""
        session = OfflineSession()
        document = self.capture(session, tier=2)
        assert document["clients"] == {"wired": [], "wireless": [], "guest": []}
        assert (document["capture_status"], document["partial_reasons"]) == ("complete", [])
        self.assert_calls(session, Cases.ENDPOINTS["wireless"], good=1, lost=False)

    @pytest.mark.parametrize("name", ["wired", "wireless_search", "guest"])
    @pytest.mark.parametrize("fault", [Cases.FAILURES[0], Cases.FAILURES[5]])
    def test_unaffected_map_reads_still_report_the_existing_visible_failure(
        self, name: str, fault: tuple[Any, ...]
    ) -> None:
        """The three map reads must not become success-shaped fallback reads."""
        endpoint = Cases.ENDPOINTS[name]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, fault))
        document = self.capture(session, tier=2)
        rows = ("clients_wired", "clients_guest") if name in ("wired", "guest") else ("clients_wireless",)
        assert document["partial_reasons"] == [
            {**NativePages.reason(row, 0, "read_failed"), "source": endpoint.section} for row in rows
        ]
        assert document["capture_status"] == "partial"
        self.assert_calls(session, endpoint)

    def test_direct_wireless_reader_does_not_hide_a_partial_statistics_result(self) -> None:
        """The direct reader stays loud when no collector receives the partial reason."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[4]))
        with pytest.raises(RuntimeError, match="wireless statistics read is partial"):
            clients.read_wireless_clients(session, Cases.SITE_ID)
        self.assert_calls(session, endpoint)

    def test_direct_complete_statistics_keep_the_existing_wireless_join(self) -> None:
        """The typed statistics result preserves signal fields and search-only fields."""
        endpoint = Cases.ENDPOINTS["wireless"]
        search = Cases.ENDPOINTS["wireless_search"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None))
        session.install(search, [search.answer([{"mac": "aabbcc000001", "random_mac": True}], 1, 1)])
        records = clients.read_wireless_clients(session, Cases.SITE_ID)
        assert [record.to_dict() for record in records] == [
            {
                "mac": "aabbcc000001",
                "hostname": "client-1",
                "device_mac": "001122000001",
                "ssid": "Corp",
                "rssi": -51,
                "random_mac": True,
            }
        ]
        self.assert_calls(session, endpoint, good=1, lost=False)
        self.assert_calls(session, search, good=1, lost=False)

    @pytest.mark.parametrize("fault", [Cases.FAILURES[0], Cases.FAILURES[5], Cases.FAILURES[6], Cases.FAILURES[-1]])
    def test_first_statistics_fault_reaches_the_final_capture(self, fault: tuple[Any, ...]) -> None:
        """A first statistics fault retains the standard first-page reason and status."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, [NativePages.failure(endpoint, fault, page=1)])
        document = self.capture(session, tier=2)
        reason = (
            "read_failed" if fault[1] == 0 else "unexpected_response_shape" if fault[1] == 200 else "cloud_error_status"
        )
        assert document["clients"]["wireless"] == []
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", fault[1], reason), "source": "wireless_statistics"}
        ]
        assert document["capture_status"] == "partial"
        self.assert_calls(session, endpoint, good=1, lost=False)

    @pytest.mark.parametrize("record", [None, "not a record", 5])
    def test_malformed_later_statistics_record_is_visible_in_the_final_capture(self, record: Any) -> None:
        """A malformed later row must not create a complete-looking client section."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        pages = NativePages.series(endpoint, None, good=3)
        pages[1] = endpoint.answer([record], 2, 3)
        session.install(endpoint, pages)
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == [
            {"mac": "aabbcc000001", "hostname": "client-1", "device_mac": "001122000001", "ssid": "Corp", "rssi": -51}
        ]
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", 200), "source": "wireless_statistics"}
        ]
        self.assert_calls(session, endpoint)

    def test_initial_malformed_statistics_record_reaches_the_final_capture(self) -> None:
        """The statistics row-copy error stays inside the read boundary."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.install(endpoint, [endpoint.answer([None], 1, 1)])
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == []
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", 0, "read_failed"), "source": "wireless_statistics"}
        ]
        self.assert_calls(session, endpoint, good=1, lost=False)

    def test_initial_transport_exception_reaches_the_final_capture(self) -> None:
        """The existing group error boundary preserves an initial request failure."""
        endpoint = Cases.ENDPOINTS["wireless"]
        session = OfflineSession()
        session.first[endpoint.path] = ConnectionError("offline initial connection error")
        document = self.capture(session, tier=2)
        assert document["clients"]["wireless"] == []
        assert document["partial_reasons"] == [
            {**NativePages.reason("clients_wireless", 0, "read_failed"), "source": "wireless_statistics"}
        ]
        self.assert_calls(session, endpoint, good=1, lost=False)
