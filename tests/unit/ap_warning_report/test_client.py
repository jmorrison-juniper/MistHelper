"""Prove complete, validated SDK reads and failure safety."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from requests import ConnectionError, RequestException, Timeout

from src.operations.exporting.ap_warning_report.client import (
    ApWarningClient,
    EventHistoryReader,
    PageReader,
    RecoveryEvidenceReader,
)

ORG_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize("key", [None, [], {}, 123])
def test_invalid_catalogue_key_cannot_enable_recovery(key: object, caplog: pytest.LogCaptureFixture) -> None:
    """Malformed catalogue keys retain uncertainty instead of failing the report."""
    response = SimpleNamespace(status_code=200, data=[{"key": key}], next=None)
    with patch("mistapi.api.v1.const.device_events.listDeviceEventsDefinitions", return_value=response):
        reader = RecoveryEvidenceReader(Mock(), ORG_ID, 1000)
    assert reader.catalogue_verified is False
    assert "AP event catalogue failed" in caplog.text


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 503])
def test_http_errors_reject_first_and_later_pages(status: int) -> None:
    """Neither an initial error nor a later error may produce partial rows."""
    reader = PageReader(Mock())
    failure = SimpleNamespace(status_code=status, data=[], next=None)
    with pytest.raises(RuntimeError, match=f"HTTP {status}"):
        reader.read(failure, "inventory")
    initial = SimpleNamespace(status_code=200, data=[{"id": "first"}], next="next-page")
    with patch("mistapi.get_next", return_value=failure), pytest.raises(RuntimeError, match=f"HTTP {status}"):
        reader.read(initial, "inventory")


def test_multiple_pages_are_complete_and_use_the_same_session() -> None:
    """The SDK next-page seam must receive the active authenticated session."""
    session = Mock()
    initial = SimpleNamespace(status_code=200, data=[{"id": "first"}], next="next-page")
    final = SimpleNamespace(status_code=200, data=[{"id": "second"}], next=None)
    with patch("mistapi.get_next", return_value=final) as next_page:
        assert PageReader(session).read(initial, "sites") == [{"id": "first"}, {"id": "second"}]
    next_page.assert_called_once_with(mist_session=session, response=initial)


@pytest.mark.parametrize("payload", [{}, None, "bad", [None], [3]])
def test_malformed_pages_fail(payload: object) -> None:
    """Invalid payload shapes cannot resemble empty successful collections."""
    response = SimpleNamespace(status_code=200, data=payload, next=None)
    with pytest.raises(ValueError, match="records"):
        PageReader(Mock()).read(response, "sites")


def test_missing_and_repeated_next_pages_fail() -> None:
    """An absent page or pagination cycle must not silently truncate the report."""
    initial = SimpleNamespace(status_code=200, data=[], next="same-page")
    for next_response in (None, initial):
        with patch("mistapi.get_next", return_value=next_response), pytest.raises(RuntimeError, match="page"):
            PageReader(Mock()).read(initial, "inventory")


def test_malformed_json_is_not_an_empty_report() -> None:
    """SDK parse failures retain raw text and must be rejected explicitly."""
    response = SimpleNamespace(status_code=200, data=[], raw_data="<html>invalid</html>", next=None)
    with pytest.raises(ValueError, match="parse"):
        PageReader(Mock()).read(response, "inventory")


def test_client_requests_each_site_statistics_and_ap_inventory() -> None:
    """Every site receives an all-status AP statistics request with the page size."""
    response = SimpleNamespace(status_code=200, data=[], next=None)
    site_response = SimpleNamespace(
        status_code=200,
        data=[{"id": "site-one"}, {"id": "site-two"}],
        next=None,
    )
    session = Mock()
    with (
        patch("mistapi.api.v1.const.ap_led_status.listApLedDefinition", return_value=response) as definitions,
        patch("mistapi.api.v1.orgs.sites.listOrgSites", return_value=site_response) as sites,
        patch("mistapi.api.v1.orgs.inventory.getOrgInventory", return_value=response) as inventory,
        patch("mistapi.api.v1.sites.stats.listSiteDevicesStats", return_value=response) as stats,
    ):
        assert ApWarningClient(session, ORG_ID, 37).read() == {
            "definitions": [],
            "sites": [{"id": "site-one"}, {"id": "site-two"}],
            "inventory": [],
            "stats": [],
        }
    definitions.assert_called_once_with(session)
    sites.assert_called_once_with(session, ORG_ID, limit=37)
    inventory.assert_called_once_with(session, ORG_ID, type="ap", limit=37)
    assert stats.call_args_list == [
        ((session, "site-one"), {"type": "ap", "status": "all", "limit": 37}),
        ((session, "site-two"), {"type": "ap", "status": "all", "limit": 37}),
    ]


def test_client_rejects_site_without_identifier_before_statistics() -> None:
    """A malformed site page cannot silently skip a site's statistics."""
    response = SimpleNamespace(status_code=200, data=[], next=None)
    sites_response = SimpleNamespace(status_code=200, data=[{"name": "No ID"}], next=None)
    with (
        patch("mistapi.api.v1.const.ap_led_status.listApLedDefinition", return_value=response),
        patch("mistapi.api.v1.orgs.sites.listOrgSites", return_value=sites_response),
        patch("mistapi.api.v1.orgs.inventory.getOrgInventory", return_value=response),
        patch("mistapi.api.v1.sites.stats.listSiteDevicesStats") as stats,
        pytest.raises(RuntimeError, match="source read failed"),
    ):
        ApWarningClient(Mock(), ORG_ID, 37).read()
    stats.assert_not_called()


@pytest.mark.parametrize("limit", [0, 1001, True])
def test_invalid_page_limit_fails_before_reads(limit: int) -> None:
    """The client accepts only the supported page-size range."""
    with pytest.raises(ValueError, match="page limit"):
        ApWarningClient(Mock(), ORG_ID, limit)


def test_invalid_organization_fails_before_reads() -> None:
    """A missing or invalid organization must not reach the SDK."""
    with pytest.raises(ValueError, match="organization"):
        ApWarningClient(Mock(), "not-an-organization", 1000)


def test_real_client_hides_transport_exception_text(caplog: pytest.LogCaptureFixture) -> None:
    """The actual SDK boundary must not expose a credential in an exception message."""
    marker = "SYNTHETIC_PRIVATE_MARKER"
    with (
        patch("mistapi.api.v1.const.ap_led_status.listApLedDefinition", side_effect=RequestException(marker)),
        pytest.raises(RuntimeError, match="source read failed") as failure,
    ):
        ApWarningClient(Mock(), ORG_ID, 1000).read()
    assert marker not in str(failure.value)
    assert marker not in caplog.text


@pytest.mark.parametrize("error_type", [Timeout, ConnectionError])
def test_timeout_and_connection_error_fail_the_read(error_type: type[RequestException]) -> None:
    """Transport failures cannot become an empty successful organization."""
    with (
        patch("mistapi.api.v1.const.ap_led_status.listApLedDefinition", side_effect=error_type),
        pytest.raises(RuntimeError, match="source read failed"),
    ):
        ApWarningClient(Mock(), ORG_ID, 1000).read()


def test_empty_body_fails_instead_of_reporting_zero_rows() -> None:
    """An absent parsed body is not the documented empty list response."""
    empty = SimpleNamespace(status_code=200, data=None, raw_data="", next=None)
    with pytest.raises(ValueError, match="object records"):
        PageReader(Mock()).read(empty, "inventory")


@pytest.mark.parametrize("status", [403, 429, 503])
def test_recovery_history_http_failure_is_explicit(status: int) -> None:
    """A failed candidate lookup retains its HTTP evidence status."""
    response = SimpleNamespace(status_code=status, data={"error": "controlled"}, next=None)
    with patch("mistapi.api.v1.orgs.devices.searchOrgDeviceEvents", return_value=response):
        result = EventHistoryReader(Mock(), ORG_ID, 1000).read("000000000001", 1794003720)
    assert result["evidence_status"] == f"history_http_{status}"
    assert result["events"] == []


def test_recovery_history_drains_server_cursor_and_checks_total() -> None:
    """The reader sends AP scope, bounded UTC epochs, and the actual server cursor."""
    event = {"mac": "000000000001", "timestamp": 1794003423, "type": "AP_CONNECTED"}
    pages = [
        SimpleNamespace(
            status_code=200,
            data={
                "results": [event],
                "total": 2,
                "next": "/x?search_after=opaque",
                "start": 1794000120,
                "end": 1794003720,
            },
        ),
        SimpleNamespace(status_code=200, data={"results": [event], "total": 2, "start": 1794000120, "end": 1794003720}),
    ]
    with patch("mistapi.api.v1.orgs.devices.searchOrgDeviceEvents", side_effect=pages) as search:
        result = EventHistoryReader(Mock(), ORG_ID, 1).read("000000000001", 1794003720)
    assert result["evidence_status"] == "complete"
    assert len(result["events"]) == 2
    assert search.call_args.kwargs == {
        "mac": "000000000001",
        "device_type": "ap",
        "start": "1794000120",
        "end": "1794003720",
        "limit": 1,
        "sort": "timestamp",
        "search_after": "opaque",
    }


@pytest.mark.parametrize(
    "body",
    [
        {"results": [], "total": 1},
        {"results": [], "total": 0, "next": "missing-cursor"},
        {"results": [], "total": True},
        {"results": "invalid", "total": 0},
        {"results": []},
    ],
)
def test_incomplete_or_malformed_history_is_not_complete(body: dict) -> None:
    """Missing pages and malformed metadata must not become negative evidence."""
    response = SimpleNamespace(status_code=200, data=body)
    with patch("mistapi.api.v1.orgs.devices.searchOrgDeviceEvents", return_value=response):
        result = EventHistoryReader(Mock(), ORG_ID, 1000).read("000000000001", 1794003720)
    assert result["evidence_status"] in ("history_truncated", "history_unavailable")


def test_recovery_history_page_budget_never_accepts_truncation() -> None:
    """Ten changing cursors consume the budget but cannot establish recovery."""
    pages = [
        SimpleNamespace(
            status_code=200,
            data={"results": [], "total": 1, "next": f"/x?search_after={page}", "start": 1794000120, "end": 1794003720},
        )
        for page in range(10)
    ]
    with patch("mistapi.api.v1.orgs.devices.searchOrgDeviceEvents", side_effect=pages) as search:
        result = EventHistoryReader(Mock(), ORG_ID, 1000).read("000000000001", 1794003720)
    assert search.call_count == 10
    assert result["evidence_status"] == "history_truncated"
