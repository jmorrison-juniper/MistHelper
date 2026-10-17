"""Verify independently authored gateway insight collection with synthetic SDK responses."""

import sqlite3
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.portals.wan_performance.collection.snapshot_client import GatewayInsights
from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, SiteIdentity
from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec

DEVICE_ID = "00000000-0000-0000-0000-000000000001"
TARGET = GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff")


@pytest.fixture(autouse=True)
def device_quality_response():
    """Keep selected-port device insight tests on bounded synthetic responses."""
    from src.interfaces.portals.wan_performance.collection import snapshot_client

    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    response = SimpleNamespace(
        status_code=200,
        data={
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "interval": 3600,
            "rt": [start.isoformat()],
            "avg_loss": [0.25],
            "avg_jitter": [4.5],
            "avg_latency": [33.3],
        },
    )
    with (
        patch.object(snapshot_client, "getSiteInsightMetricsForDevice", return_value=response) as request,
        patch.object(
            snapshot_client,
            "searchOrgDeviceEvents",
            return_value=SimpleNamespace(status_code=200, data={"results": []}),
        ),
    ):
        yield request


def test_selected_port_insights_collect_rates_and_quality_with_bounded_calls(device_quality_response):
    """Collect source-compatible rates and link health for one exact port and hour."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    target = CircuitIdentity(TARGET, "ge-0/0/1")
    device, metadata, series = responses("10m")
    session, admission = MagicMock(), MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ) as discovery,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ) as catalog,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ) as metrics,
    ):
        result = GatewayInsights(session, admission).collect_for_port("org-one", target, 100, "up")
    assert discovery.call_count == 1
    assert catalog.call_count == 1
    assert metrics.call_count == 1
    assert device_quality_response.call_count == 1
    assert admission.check.call_count == 5
    assert metrics.call_args.args[3] == "rx_bps,tx_bps"
    assert metrics.call_args.kwargs["port_id"] == target.port_name
    assert metrics.call_args.kwargs["limit"] == 6 and metrics.call_args.kwargs["page"] == 1
    device_quality_response.assert_called_once_with(
        session,
        "site-one",
        "wan_link_health",
        "aabbccddeeff",
        port_id=target.port_name,
        start=str(series.data["start"]),
        end=str(series.data["end"]),
        interval="1h",
        limit=1,
        page=1,
    )
    records = SnapshotRecords.build(
        {
            "org_id": "org-one",
            "provenance": "live",
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "ports": [],
            "peers": [],
            "insights": result,
        }
    )
    assert len(records) == 1
    assert records[0].identity == target
    assert records[0].hour_start_utc.isoformat() == series.data["rt"][0]
    assert records[0].metrics["rx_bps"].value == 0
    assert records[0].metrics["tx_bps"].unit == "bit/s"
    assert records[0].metrics["avg_loss_pct"].value == 0.25
    assert records[0].metrics["avg_jitter_ms"].value == 4.5
    assert records[0].metrics["avg_latency_ms"].value == 33.3
    assert records[0].metrics["utilization_pct"].raw_values == (0.0,) * 6
    assert RecordCodec.decode(RecordCodec.encode(records[0])) == records[0]


def test_selected_port_accepts_response_array_named_for_requested_metric():
    """Map the API's explicit one-metric response key without guessing series order."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    device, metadata, series = responses("10m")
    series.data["rx_bps"] = [None] * 6
    series.data["tx_bps"] = ["12"] * 6
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ) as discovery,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ) as metrics,
    ):
        result = GatewayInsights(MagicMock(), MagicMock()).collect_for_port(
            "org-one", CircuitIdentity(TARGET, "ge-0/0/1"), 100, "up"
        )

    assert discovery.call_count == 1
    assert metrics.call_count == 1
    assert [sample["value"] for sample in result["samples"][:2]] == [None, 12.0]
    assert [sample["metric"] for sample in result["samples"][2:5]] == [
        "avg_loss_pct",
        "avg_jitter_ms",
        "avg_latency_ms",
    ]
    records = SnapshotRecords.build(
        {
            "org_id": "org-one",
            "provenance": "live",
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "ports": [],
            "peers": [],
            "insights": result,
        }
    )
    assert records[0].metrics["rx_bps"].value is None
    assert records[0].metrics["rx_bps"].missing_reason == "The API snapshot has no value."
    assert records[0].metrics["tx_bps"].value == 12


def test_raw_utilization_p95_and_congestion_durations_use_aligned_10_minute_samples():
    """Calculate source hourly p95 and observed threshold occupancy from raw samples."""
    timestamps = [f"2024-01-01T{hour:02d}:{minute:02d}:00+00:00" for minute in range(0, 60, 10) for hour in [12]]
    receive = {
        "metric": "rx_bps",
        "hour_start_utc": "2024-01-01T12:00:00+00:00",
        "points": [{"timestamp": timestamp, "value": 0.0} for timestamp in timestamps],
    }
    transmit_values = (50_000_000, 750_000_000, 850_000_000, 950_000_000, 100_000_000, 0)
    transmit = {
        "metric": "tx_bps",
        "hour_start_utc": receive["hour_start_utc"],
        "points": [
            {"timestamp": timestamp, "value": value}
            for timestamp, value in zip(timestamps, transmit_values, strict=True)
        ],
    }

    utilization = GatewayInsights._utilization([receive, transmit], 1000)

    assert utilization["raw_values"] == (5.0, 75.0, 85.0, 95.0, 10.0, 0.0)
    assert utilization["value"] == 95.0
    assert utilization["sample_count"] == 6
    assert utilization["coverage_fraction"] == 1
    assert [metric["value"] for metric in utilization["congestion_metrics"]] == [30, 20, 10]


def test_event_search_paginates_and_matches_only_the_selected_port():
    """Use the organization event cursor and source link-event duration semantics."""
    device, _, _ = responses()
    start = datetime(2024, 1, 1, 12, tzinfo=UTC)
    end = start + timedelta(hours=1)
    rows = [
        {
            "type": "GW_PORT_DOWN",
            "timestamp": (start + timedelta(minutes=10)).isoformat(),
            "text": "Port ge-0/0/1 down",
        },
        {"type": "GW_PORT_UP", "timestamp": (start + timedelta(minutes=40)).isoformat(), "port_id": "ge-0/0/1"},
        {"type": "GW_PORT_DOWN", "timestamp": (start + timedelta(minutes=20)).isoformat(), "port_id": "ge-0/0/10"},
    ]
    pages = [
        SimpleNamespace(status_code=200, data={"results": rows, "next": "/events?search_after=cursor%2Bone"}),
        SimpleNamespace(status_code=200, data={"results": []}),
    ]
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgDeviceEvents",
        side_effect=pages,
    ) as request:
        result = GatewayInsights(MagicMock(), MagicMock())._status_events(device, "ge-0/0/1", start, end, None)

    metrics = {metric["metric"]: metric for metric in result["metrics"]}
    assert result["complete"] is True
    assert (result["page_count"], result["event_count"]) == (2, 2)
    assert metrics["down_minutes"]["value"] == 30
    assert metrics["up_minutes"]["value"] == 20
    assert metrics["up_minutes"]["coverage_fraction"] == pytest.approx(50 / 60)
    assert metrics["flap_count"]["value"] == 2
    assert request.call_count == 2
    assert request.call_args_list[0].kwargs["type"] == "GW_PORT_UP,GW_PORT_DOWN,GW_WAN_UP,GW_WAN_DOWN"
    assert request.call_args_list[1].kwargs["search_after"] == "cursor+one"


@pytest.mark.parametrize(("status", "expected"), [(True, (60, 0)), (False, (0, 60)), (None, (None, None))])
def test_no_event_window_uses_cached_state_only_as_source_fallback(status, expected):
    """Use cached state for a no-event hour and keep unknown status unknown."""
    end = datetime(2024, 1, 1, 13, tzinfo=UTC)
    metrics = {metric["metric"]: metric for metric in GatewayInsights._status_metrics([], end, status, True)}
    assert (metrics["up_minutes"]["value"], metrics["down_minutes"]["value"]) == expected
    assert metrics["flap_count"]["value"] == 0


def test_event_search_page_cap_marks_status_unknown():
    """Do not treat a truncated status event window as complete availability."""
    device, _, _ = responses()
    start = datetime(2024, 1, 1, 12, tzinfo=UTC)
    next_page = SimpleNamespace(status_code=200, data={"results": [], "next": "/events?search_after=next"})
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgDeviceEvents",
        return_value=next_page,
    ) as request:
        result = GatewayInsights(MagicMock(), MagicMock())._status_events(
            device, "ge-0/0/1", start, start + timedelta(hours=1), True
        )
    assert result["complete"] is False
    assert result["page_count"] == 5
    assert request.call_count == 5
    assert all(metric["value"] is None for metric in result["metrics"])


@pytest.mark.parametrize("status", [400, 429, 500])
def test_event_search_http_errors_stop_the_port_history(status):
    """Propagate event API client, quota, and server failures."""
    device, _, _ = responses()
    start = datetime(2024, 1, 1, 12, tzinfo=UTC)
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgDeviceEvents",
        return_value=SimpleNamespace(status_code=status, data={}),
    ):
        with pytest.raises(ConnectionError, match=str(status)):
            GatewayInsights(MagicMock(), MagicMock())._status_events(
                device, "ge-0/0/1", start, start + timedelta(hours=1), True
            )


def test_event_search_timeout_is_not_converted_to_empty_status():
    """Propagate event request timeouts rather than storing zero flaps or healthy time."""
    device, _, _ = responses()
    start = datetime(2024, 1, 1, 12, tzinfo=UTC)
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgDeviceEvents",
        side_effect=TimeoutError("read timed out"),
    ):
        with pytest.raises(TimeoutError, match="read timed out"):
            GatewayInsights(MagicMock(), MagicMock())._status_events(
                device, "ge-0/0/1", start, start + timedelta(hours=1), True
            )


@pytest.mark.parametrize("violation", ["scope", "unit", "max_age", "interval", "alignment", "ambiguous_mapping"])
def test_selected_port_refuses_unverified_insight_contract(violation):
    """Do not assign an hourly port rate when catalog or returned alignment disagrees."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    device, metadata, series = responses("10m")
    if violation == "scope":
        metadata["rx_bps"]["scopes"] = ["client"]
    elif violation == "unit":
        metadata["rx_bps"]["unit"] = "ms"
    elif violation == "max_age":
        metadata["rx_bps"]["intervals"]["10m"]["max_age"] = 0
    elif violation == "interval":
        metadata["rx_bps"]["intervals"]["10m"]["interval"] = 300
    elif violation == "ambiguous_mapping":
        series.data["rx_bps"] = ["0"]
    else:
        series.data["rt"] = [datetime.now(UTC).isoformat()]
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        with pytest.raises(ValueError):
            GatewayInsights(MagicMock(), MagicMock()).collect_for_port(
                "org-one", CircuitIdentity(TARGET, "ge-0/0/1"), 100, "up"
            )


@pytest.mark.parametrize("failure", ["http_400", "http_500", "quota", "truncation"])
def test_selected_port_stops_on_request_failure_or_partial_hour(failure):
    """A rejected or paginated response cannot become complete persisted port history."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    device, metadata, series = responses("10m")
    admission = MagicMock()
    if failure == "quota":
        admission.check.side_effect = [None, None, ConnectionError("quota")]
    elif failure == "truncation":
        series.data["next"] = "/more"
    else:
        series.status_code = int(failure.removeprefix("http_"))
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        with pytest.raises((ConnectionError, ValueError)):
            GatewayInsights(MagicMock(), admission).collect_for_port(
                "org-one", CircuitIdentity(TARGET, "ge-0/0/1"), 100, "up"
            )


@pytest.mark.parametrize("empty", [False, True])
def test_selected_port_insights_persist_to_existing_sqlite_without_snapshot_change(tmp_path, empty):
    """Connect the bounded collector to actual configured-history serialization."""
    from src.interfaces.portals.wan_performance.collection.live_service import LiveService
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity
    from src.interfaces.portals.wan_performance.integration.sqlite_history import SQLiteHistory

    path = tmp_path / "application.db"
    sqlite3.connect(path).close()
    history = SQLiteHistory(path)
    device, metadata, series = responses("10m")
    if empty:
        series.data.update(rt=[], rx_bps=[], tx_bps=[])
    target = CircuitIdentity(TARGET, "ge-0/0/1")
    store = MagicMock()
    store.cached.return_value = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "ports": [{**device, "port_id": target.port_name, "speed": 100}],
        "peers": [],
    }
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        assert LiveService(MagicMock(), "org-one", store, history).refresh_port(target) == 1
    start, end = (datetime.fromtimestamp(series.data[name], UTC) for name in ("start", "end"))
    retained = history.read(target, start, end)
    assert len(retained) == 1
    assert set(retained[0].metrics) == {
        "rx_bps",
        "tx_bps",
        "avg_loss_pct",
        "avg_jitter_ms",
        "avg_latency_ms",
        "utilization_pct",
        "congestion_minutes_over_70_pct",
        "congestion_minutes_over_80_pct",
        "congestion_minutes_over_90_pct",
        "up_minutes",
        "down_minutes",
        "flap_count",
    }
    assert retained[0].metrics["rx_bps"].value == (None if empty else 0)
    assert retained[0].metrics["rx_bps"].missing_reason == ("The API snapshot has no value." if empty else None)
    assert retained[0].hour_start_utc == start
    assert retained[0].identity == target
    assert store.acquire.return_value.check.call_count == 6
    store.publish.assert_not_called()


@pytest.mark.parametrize("status", [400, 403, 429, 500, 503])
def test_port_quality_http_errors_are_not_stored_as_empty_success(device_quality_response, status):
    """Stop a selected-port refresh when the quality request fails."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    device, metadata, series = responses("10m")
    device_quality_response.return_value.status_code = status
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        with pytest.raises(ConnectionError, match=str(status)):
            GatewayInsights(MagicMock(), MagicMock()).collect_for_port(
                "org-one", CircuitIdentity(TARGET, "ge-0/0/1"), 100, "up"
            )


def test_port_quality_timeout_is_not_stored_as_empty_success(device_quality_response):
    """Propagate a device insight timeout instead of writing missing metrics."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    device, metadata, series = responses("10m")
    device_quality_response.side_effect = TimeoutError("read timed out")
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        with pytest.raises(TimeoutError, match="read timed out"):
            GatewayInsights(MagicMock(), MagicMock()).collect_for_port(
                "org-one", CircuitIdentity(TARGET, "ge-0/0/1"), 100, "up"
            )


def test_port_quality_missing_arrays_remain_unknown(device_quality_response):
    """Persist missing quality values as unknown without inventing zero samples."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity

    device, metadata, series = responses("10m")
    response = device_quality_response.return_value
    response.data["rt"] = []
    response.data.update(avg_loss=[], avg_jitter=[], avg_latency=[])
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        result = GatewayInsights(MagicMock(), MagicMock()).collect_for_port(
            "org-one", CircuitIdentity(TARGET, "ge-0/0/1"), 100, None
        )
    record = SnapshotRecords.build(
        {
            "org_id": "org-one",
            "provenance": "live",
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "ports": [],
            "peers": [],
            "insights": result,
        }
    )[0]
    assert record.metrics["avg_loss_pct"].value is None
    assert record.metrics["avg_loss_pct"].missing_reason == "The API snapshot has no value."


def responses(interval="1h", status=200):
    """Build a bounded synthetic window with explicit catalog units and scope."""
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    device = {"id": DEVICE_ID, "org_id": "org-one", "site_id": "site-one", "mac": "aabbccddeeff"}
    interval_seconds = {"10m": 600, "1h": 3600}[interval]
    sample_count = {"10m": 6, "1h": 1}[interval]
    metadata = {
        name: {
            "unit": "bit/s",
            "type": "timeseries",
            "scopes": ["gateway"],
            "intervals": {
                "10m": {"interval": 600, "max_age": 86400},
                "1h": {"interval": 3600, "max_age": 7200},
            },
        }
        for name in ("rx_bps", "tx_bps")
    }
    series = {
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
        "interval": interval_seconds,
        "rt": [(start + timedelta(seconds=interval_seconds * index)).isoformat() for index in range(sample_count)],
        "rx_bps": [0] * sample_count,
        "tx_bps": [0] * sample_count,
    }
    return device, metadata, SimpleNamespace(status_code=status, data=series)


def test_insights_use_actual_device_uuid_catalog_and_named_metric_arrays():
    """Never derive a device UUID from its MAC or assume positional metric mapping."""
    device, metadata, series = responses("1h")
    session, admission = MagicMock(), MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device], next=None),
        ) as devices,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ) as metrics,
    ):
        result = GatewayInsights(session, admission).collect("org-one", TARGET)
    devices.assert_called_once_with(
        session, "org-one", type="gateway", site_id="site-one", mac="aabbccddeeff", limit=2, page=1
    )
    assert metrics.call_count == 1
    assert admission.check.call_count == 3
    assert metrics.call_args.kwargs["limit"] == 1
    assert metrics.call_args.kwargs["page"] == 1
    assert metrics.call_args.args[2] == DEVICE_ID
    assert metrics.call_args.args[3] == "rx_bps,tx_bps"
    snapshot = {
        "org_id": "org-one",
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "ports": [],
        "peers": [],
        "insights": result,
        "provenance": "live",
    }
    records = SnapshotRecords.build(snapshot)
    assert len(records) == 1
    assert isinstance(records[0].identity, GatewayIdentity)
    assert records[0].metrics["rx_bps"].value == 0
    assert records[0].metrics["rx_bps"].unit == "bit/s"
    assert RecordCodec.decode(RecordCodec.encode(records[0])) == records[0]


@pytest.mark.parametrize("status", [400, 403, 429, 500, 503])
def test_gateway_insight_http_errors_are_not_empty_success(status):
    """Refuse malformed or rejected discovery before additional SDK calls."""
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
        return_value=SimpleNamespace(status_code=status),
    ):
        with pytest.raises(ConnectionError, match=str(status)):
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one", TARGET)


def test_selected_gateway_discovery_uses_exact_site_mac_and_returned_uuid():
    """Support a second selected gateway without deriving its UUID or increasing the request bound."""
    from src.interfaces.portals.wan_performance.domain.identity import SiteIdentity

    device, metadata, series = responses("1h")
    device.update(id="00000000-0000-0000-0000-000000000002", site_id="site-two", mac="112233445566")
    target = GatewayIdentity(SiteIdentity("org-one", "site-two"), "112233445566")
    session, admission = MagicMock(), MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ) as discovery,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ) as metrics,
    ):
        result = GatewayInsights(session, admission).collect("org-one", target)
    discovery.assert_called_once_with(
        session, "org-one", type="gateway", site_id="site-two", mac="112233445566", limit=2, page=1
    )
    assert metrics.call_count == 1
    assert metrics.call_args.args[2] == device["id"]
    assert result["gateway"] == device
    assert result["partial"] is False
    assert admission.check.call_count == 3


@pytest.mark.parametrize("rows", ["wrong_site", "wrong_mac", "duplicate", "absent"])
def test_selected_gateway_rejects_ambiguous_or_mismatched_discovery(rows):
    """Never select another gateway after a scoped discovery mismatch."""
    from src.interfaces.portals.wan_performance.domain.identity import SiteIdentity

    device, _, _ = responses()
    target = GatewayIdentity(SiteIdentity("org-one", "site-one"), device["mac"])
    if rows == "wrong_site":
        device["site_id"] = "another-site"
    elif rows == "wrong_mac":
        device["mac"] = "112233445566"
    data = [] if rows == "absent" else [device, device] if rows == "duplicate" else [device]
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=data),
        ),
        patch("src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics") as catalog,
    ):
        with pytest.raises(ValueError):
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one", target)
    catalog.assert_not_called()


def test_overview_refresh_is_two_pages_without_gateway_discovery():
    """Keep overview requests bounded and retain explicit port-page truncation."""
    from src.interfaces.portals.wan_performance.collection.snapshot_client import SnapshotClient

    admission = MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=SimpleNamespace(status_code=200, data={"results": [], "total": 200}),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats",
            return_value=SimpleNamespace(status_code=200, data={"results": []}),
        ),
        patch("src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats") as discovery,
    ):
        result = SnapshotClient(MagicMock(), admission).collect("org-one")
    assert result["partial"] is True
    assert result["insights"] == {"samples": [], "partial": False}
    assert admission.check.call_count == 2
    discovery.assert_not_called()


@pytest.mark.parametrize("failure", ["http_400", "http_500", "admission"])
def test_selected_gateway_stops_on_metric_errors_or_lost_admission(failure):
    """Keep scoped metric requests under the same admission and HTTP failure contracts."""
    from src.interfaces.portals.wan_performance.domain.identity import SiteIdentity

    device, metadata, series = responses()
    target = GatewayIdentity(SiteIdentity("org-one", "site-one"), device["mac"])
    admission = MagicMock()
    if failure == "admission":
        admission.check.side_effect = [None, None, ConnectionError("expired admission")]
    else:
        series.status_code = int(failure.removeprefix("http_"))
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device]),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ) as metrics,
    ):
        with pytest.raises(ConnectionError, match="expired admission" if failure == "admission" else "HTTP"):
            GatewayInsights(MagicMock(), admission).collect("org-one", target)
    assert metrics.call_count == (0 if failure == "admission" else 1)
    assert admission.check.call_count == 3


@pytest.mark.parametrize("body", [b"", b"{bad json"])
def test_gateway_discovery_rejects_empty_body_and_malformed_json(body):
    """Exercise actual SDK body parsing and stop before metric discovery."""
    from mistapi.__api_response import APIResponse
    from requests import Response

    response = Response()
    response.status_code = 200
    response._content = body
    parsed = APIResponse(response, "https://api.invalid/api/v1/orgs/org-one/stats/devices")
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats", return_value=parsed
        ),
        patch("src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics") as catalog,
    ):
        with pytest.raises(ValueError, match="array"):
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one", TARGET)
    catalog.assert_not_called()
    assert parsed.raw_data == body.decode()


@pytest.mark.parametrize("change", ["alignment", "scope", "unit", "retention", "identity"])
def test_gateway_insights_reject_unverified_contracts(change):
    """Reject wrong tenant, units, scope, retention, and timestamp alignment."""
    device, metadata, series = responses()
    if change == "alignment":
        series.data["rt"] = []
    elif change == "identity":
        device["org_id"] = "another-org"
    elif change == "scope":
        metadata["rx_bps"]["scopes"] = ["ap"]
    elif change == "unit":
        metadata["rx_bps"]["unit"] = ""
    else:
        metadata["rx_bps"]["intervals"]["1h"]["max_age"] = 0
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device], next=None),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=series,
        ),
    ):
        with pytest.raises(ValueError):
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one", TARGET)


@pytest.mark.parametrize("empty_metrics", [(), ("rx_bps",), ("rx_bps", "tx_bps")])
@pytest.mark.parametrize("second_gateway", [False, True])
def test_bounded_refresh_persists_gateway_history_before_cache_publication(tmp_path, empty_metrics, second_gateway):
    """Connect the real collector, domain model, and existing-file SQLite repository."""
    from src.interfaces.portals.wan_performance.collection.live_service import LiveService
    from src.interfaces.portals.wan_performance.domain.identity import SiteIdentity
    from src.interfaces.portals.wan_performance.integration.sqlite_history import SQLiteHistory

    path = tmp_path / "application.db"
    sqlite3.connect(path).close()
    repository = SQLiteHistory(path)
    device, metadata, series = responses()
    metric_data = dict(series.data)
    if len(empty_metrics) == 2:
        metric_data["rt"] = []
        metric_data.update({name: [] for name in empty_metrics})
    else:
        metric_data.update({name: [None] for name in empty_metrics})
    metric_response = SimpleNamespace(status_code=200, data=metric_data)
    port = {**device, "port_id": "ge-0/0/0", "rx_bps": 40, "tx_bps": 80}
    peer = {
        **port,
        "peer_mac": "11:22:33:44:55:66",
        "peer_site_id": "site-two",
        "peer_port_id": "ge-0/0/1",
        "type": "ipsec",
        "loss": 0,
        "latency": 10,
        "jitter": 2,
    }
    if second_gateway:
        device = {**device, "id": "00000000-0000-0000-0000-000000000002", "site_id": "site-two", "mac": "112233445566"}
        port = {**port, "site_id": device["site_id"], "mac": device["mac"]}
        peer = {**peer, "site_id": device["site_id"], "mac": device["mac"]}
    target = GatewayIdentity(SiteIdentity("org-one", device["site_id"]), device["mac"])
    store = MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=SimpleNamespace(status_code=200, data={"results": [port]}),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats",
            return_value=SimpleNamespace(status_code=200, data={"results": [peer]}),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats",
            return_value=SimpleNamespace(status_code=200, data=[device], next=None),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics",
            return_value=SimpleNamespace(status_code=200, data=metadata),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.getSiteInsightMetricsForGateway",
            return_value=metric_response,
        ),
    ):
        snapshot = LiveService(MagicMock(), "org-one", store, repository).refresh(target)
    identity = target
    start, end = (datetime.fromtimestamp(series.data[name], UTC) for name in ("start", "end"))
    records = repository.read(identity, start, end)
    assert len(records) == 1
    for name in ("rx_bps", "tx_bps"):
        metric = records[0].metrics[name]
        assert metric.value == (None if name in empty_metrics else 0)
        assert metric.unit == "bit/s"
        assert metric.missing_reason == ("The API snapshot has no value." if name in empty_metrics else None)
    observations = SnapshotRecords.build(snapshot)
    assert len(observations) == 3
    for record in observations:
        assert repository.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1)) == (
            record,
        )
    assert store.acquire.return_value.check.call_count == 7
    store.publish.assert_called_once_with("org-one", snapshot)
