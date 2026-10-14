"""Verify independently authored gateway insight collection with synthetic SDK responses."""

import sqlite3
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.portals.wan_performance.collection.snapshot_client import GatewayInsights
from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity
from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec

DEVICE_ID = "00000000-0000-0000-0000-000000000001"


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
        result = GatewayInsights(session, admission).collect("org-one")
    devices.assert_called_once_with(session, "org-one", type="gateway", limit=1, page=1)
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
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one")


@pytest.mark.parametrize("body", ["", "{malformed-json"])
def test_gateway_discovery_rejects_empty_body_and_malformed_json(body):
    """Exercise actual SDK body parsing and stop before metric discovery."""
    from mistapi.__api_response import APIResponse
    from requests import Response

    response = Response()
    response.status_code = 200
    response._content = body.encode()
    parsed = APIResponse(response, "https://api.invalid/api/v1/orgs/org-one/stats/devices")
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.listOrgDevicesStats", return_value=parsed
        ),
        patch("src.interfaces.portals.wan_performance.collection.snapshot_client.listInsightMetrics") as catalog,
    ):
        with pytest.raises(ValueError, match="array"):
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one")
    catalog.assert_not_called()
    assert parsed.raw_data == body


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
            GatewayInsights(MagicMock(), MagicMock()).collect("org-one")


def test_bounded_refresh_persists_gateway_history_before_cache_publication(tmp_path):
    """Connect the real collector, domain model, and existing-file SQLite repository."""
    from src.interfaces.portals.wan_performance.collection.live_service import LiveService
    from src.interfaces.portals.wan_performance.domain.identity import SiteIdentity
    from src.interfaces.portals.wan_performance.integration.sqlite_history import SQLiteHistory

    path = tmp_path / "application.db"
    sqlite3.connect(path).close()
    repository = SQLiteHistory(path)
    device, metadata, series = responses()
    store = MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=SimpleNamespace(status_code=200, data={"results": []}),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats",
            return_value=SimpleNamespace(status_code=200, data={"results": []}),
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
            return_value=series,
        ),
    ):
        snapshot = LiveService(MagicMock(), "org-one", store, repository).refresh()
    identity = GatewayIdentity(SiteIdentity("org-one", "site-one"), device["mac"])
    start, end = (datetime.fromtimestamp(series.data[name], UTC) for name in ("start", "end"))
    records = repository.read(identity, start, end)
    assert len(records) == 1
    assert records[0].metrics["rx_bps"].value == 0
    assert store.acquire.return_value.check.call_count == 8
    store.publish.assert_called_once_with("org-one", snapshot)
