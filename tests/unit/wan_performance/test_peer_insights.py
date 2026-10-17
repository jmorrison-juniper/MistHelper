"""Verify source-shaped VPN peer insight collection with mocked Mist responses."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.interfaces.portals.wan_performance.collection.peer_insights import PeerQualityInsights
from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, PeerPathIdentity, SiteIdentity

TARGET = PeerPathIdentity(
    GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff"),
    "ge-0/0/1",
    "ge-0/0/2",
    "11:22:33:44:55:66",
    "path-key-1",
)


def response_for(query: dict[str, str], rows: list[object], **extra: object) -> SimpleNamespace:
    """Build a bounded response envelope with explicitly supplied result rows."""
    return SimpleNamespace(
        status_code=200,
        data={
            "start": int(query["start"]),
            "end": int(query["end"]),
            "interval": 3600,
            "results": rows,
            **extra,
        },
    )


def success_response(uri: str, query: dict[str, str]) -> SimpleNamespace:
    """Build one mocked sample at the exact start of the requested UTC hour."""
    return response_for(
        query,
        [
            {
                "timestamp": int(query["start"]),
                "loss": 0.25,
                "latency": 33.3,
                "jitter": 4.5,
                "mos": 4.2,
            }
        ],
    )


def test_collect_sends_exact_peer_filter_through_admitted_session() -> None:
    """Use the documented peer filters and persist the source quality fields."""
    session, admission = MagicMock(), MagicMock()
    session.mist_get.side_effect = success_response

    records = PeerQualityInsights(session, admission).collect(TARGET)

    session.mist_get.assert_called_once()
    uri = session.mist_get.call_args.kwargs["uri"]
    query = session.mist_get.call_args.kwargs["query"]
    assert uri == "/api/v1/sites/site-one/insights/device/aabbccddeeff/vpn_peer-metrics"
    assert query["interval"] == "1h"
    assert query["limit"] == "2"
    assert query["peer_mac"] == TARGET.peer_mac
    assert query["port_id"] == TARGET.port_name
    assert query["peer_port_id"] == TARGET.peer_port_id
    assert int(query["end"]) - int(query["start"]) == 3600
    admission.check.assert_called_once_with()
    assert len(records) == 1
    assert records[0].identity == TARGET
    assert records[0].metrics["loss"].value == 0.25
    assert records[0].metrics["latency"].value == 33.3
    assert records[0].metrics["jitter"].value == 4.5
    assert records[0].metrics["mos"].value == 4.2


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500])
def test_collect_rejects_http_errors(status: int) -> None:
    """Surface client, authorization, rate-limit, and server failures."""
    session, admission = MagicMock(), MagicMock()
    session.mist_get.return_value = SimpleNamespace(status_code=status, data={})

    with pytest.raises(ConnectionError, match=f"HTTP {status}"):
        PeerQualityInsights(session, admission).collect(TARGET)

    admission.check.assert_called_once_with()


def test_collect_accepts_empty_results_without_inventing_peer_samples() -> None:
    """Keep a valid empty series distinct from zero-valued quality metrics."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(query, [])

    records = PeerQualityInsights(session, MagicMock()).collect(TARGET)

    assert records == ()


def test_collect_keeps_missing_source_metrics_unknown() -> None:
    """Preserve absent source values instead of converting them to zero."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(
        query, [{"timestamp": int(query["start"]), "loss": None}]
    )

    records = PeerQualityInsights(session, MagicMock()).collect(TARGET)

    assert len(records) == 1
    assert all(metric.value is None for metric in records[0].metrics.values())


def test_collect_rejects_rows_outside_the_requested_hour() -> None:
    """Refuse a response timestamp outside the bounded request interval."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(
        query,
        [{"timestamp": int(query["end"]), "loss": 0, "latency": 1, "jitter": 1, "mos": 4}],
    )

    with pytest.raises(ValueError, match="outside the requested hour"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


def test_collect_rejects_duplicate_hour_samples() -> None:
    """Prevent ambiguous replacement when a response repeats one hourly key."""
    session = MagicMock()

    def duplicate(uri: str, query: dict[str, str]) -> SimpleNamespace:
        row = {"timestamp": int(query["start"]), "loss": 0, "latency": 1, "jitter": 1, "mos": 4}
        return response_for(query, [row, dict(row)])

    session.mist_get.side_effect = duplicate

    with pytest.raises(ValueError, match="duplicate hourly timestamps"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


def test_collect_rejects_malformed_response_shape() -> None:
    """Do not interpret malformed response data as an empty history."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(query, [None])

    with pytest.raises(ValueError, match="contain objects"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


@pytest.mark.parametrize("timestamp", [float("inf"), 10**100])
def test_collect_rejects_out_of_range_timestamps(timestamp: float | int) -> None:
    """Reject timestamps that cannot map to a valid UTC instant."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(
        query, [{"timestamp": timestamp, "loss": 0, "latency": 1, "jitter": 1, "mos": 4}]
    )

    with pytest.raises(ValueError, match="timestamp"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


def test_collect_rejects_excess_response_rows() -> None:
    """Refuse more records or pagination links than the bounded query permits."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(query, [{}, {}, {}])

    with pytest.raises(ValueError, match="fixed two-row page"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


def test_collect_rejects_paginated_response() -> None:
    """Do not follow a continuation beyond the one-request query ceiling."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(query, [], next="https://mist.example/next")

    with pytest.raises(ValueError, match="requested bounded window"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


def test_collect_rejects_response_window_mismatch() -> None:
    """Reject a successful response that reports another interval."""
    session = MagicMock()
    session.mist_get.side_effect = lambda uri, query: response_for(query, [], interval=600)

    with pytest.raises(ValueError, match="requested bounded window"):
        PeerQualityInsights(session, MagicMock()).collect(TARGET)


def test_collect_stops_before_transport_when_admission_fails() -> None:
    """Do not send an API request when the shared organization lease is denied."""
    session, admission = MagicMock(), MagicMock()
    admission.check.side_effect = ConnectionError("admission denied")

    with pytest.raises(ConnectionError, match="admission denied"):
        PeerQualityInsights(session, admission).collect(TARGET)

    session.mist_get.assert_not_called()


def test_collect_propagates_transport_timeout() -> None:
    """Keep SDK timeouts visible to the portal error handler."""
    session, admission = MagicMock(), MagicMock()
    session.mist_get.side_effect = TimeoutError("request timed out")

    with pytest.raises(TimeoutError, match="request timed out"):
        PeerQualityInsights(session, admission).collect(TARGET)

    admission.check.assert_called_once_with()
