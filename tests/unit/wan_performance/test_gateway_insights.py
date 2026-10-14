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


def responses(status=200):
    """Build a bounded synthetic window with explicit catalog units and scope."""
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    device = {"id": DEVICE_ID, "org_id": "org-one", "site_id": "site-one", "mac": "aabbccddeeff"}
    metadata = {
        name: {
            "unit": "bit/s",
            "type": "timeseries",
            "scopes": ["gateway"],
            "intervals": {"1h": {"interval": 3600, "max_age": 7200}},
        }
        for name in ("rx_bps", "tx_bps")
    }
    series = {
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
        "interval": 3600,
        "rt": [start.isoformat()],
        "results": ["0"],
    }
    return device, metadata, SimpleNamespace(status_code=status, data=series)


def test_insights_use_actual_device_uuid_catalog_and_single_metric_queries():
    """Never derive a device UUID from its MAC or assume positional multi-metric mapping."""
    device, metadata, series = responses()
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
    assert metrics.call_count == 2
    assert admission.check.call_count == 4
    assert metrics.call_args.kwargs["limit"] == 1
    assert metrics.call_args.kwargs["page"] == 1
    assert metrics.call_args.args[2] == DEVICE_ID
    assert {call.args[3] for call in metrics.call_args_list} == {"rx_bps", "tx_bps"}
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

    device, metadata, series = responses()
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
    assert metrics.call_count == 2
    assert metrics.call_args.args[2] == device["id"]
    assert result["gateway"] == device
    assert result["partial"] is False
    assert admission.check.call_count == 4


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
    metric_responses = [
        (
            SimpleNamespace(status_code=200, data={**series.data, "rt": [], "results": []})
            if name in empty_metrics
            else series
        )
        for name in ("rx_bps", "tx_bps")
    ]
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
            side_effect=metric_responses,
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
    assert store.acquire.return_value.check.call_count == 8
    store.publish.assert_called_once_with("org-one", snapshot)
