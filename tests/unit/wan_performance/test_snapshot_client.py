"""Verify bounded SDK collection without production credentials or automatic refresh."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.portals.wan_performance.collection.snapshot_client import SnapshotClient
from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, SiteIdentity


@pytest.fixture(autouse=True)
def isolated_gateway_insights():
    """Keep these port/peer tests isolated from the separately tested gateway SDK calls."""
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.GatewayInsights.collect",
        return_value={"samples": [], "partial": False},
    ):
        yield


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 503])
def test_http_errors_stop_collection(status):
    """Do not persist partial success or retry a rejected request."""
    session = MagicMock()
    admission = MagicMock()
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=SimpleNamespace(status_code=status),
        ),
        patch("src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats") as peers,
    ):
        with pytest.raises(ConnectionError, match=str(status)):
            SnapshotClient(session, admission).collect("org-one")
    peers.assert_not_called()


def test_fixed_two_calls_and_truncated_results():
    """Keep the cap explicit and never follow a server next URL."""
    session = MagicMock()
    admission = MagicMock()
    ports = SimpleNamespace(status_code=200, data={"results": [{"port_id": "ge-0/0/0"}], "next": "https://unsafe"})
    peers = SimpleNamespace(status_code=200, data={"results": [], "total": 0})
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=ports,
        ) as port_call,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats",
            return_value=peers,
        ) as peer_call,
    ):
        result = SnapshotClient(session, admission).collect("org-one")
    port_call.assert_called_once_with(session, "org-one", device_type="gateway", mac=None, limit=100)
    peer_call.assert_called_once_with(session, "org-one", mac=None, site_id=None, duration="1h", limit=100)
    assert admission.check.call_count == 2
    assert result["ports"] == [{"port_id": "ge-0/0/0"}]
    assert result["partial"] is True


@pytest.mark.parametrize("site_id,mac", [("site-one", "aabbccddeeff"), ("site-two", "112233445566")])
def test_selected_pages_use_exact_sdk_filters(site_id, mac):
    """Scope both snapshot pages to either selected gateway without extra page requests."""
    session, admission = MagicMock(), MagicMock()
    target = GatewayIdentity(SiteIdentity("org-one", site_id), mac)
    row = {"site_id": site_id, "mac": mac}
    response = SimpleNamespace(status_code=200, data={"results": [row]})
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=response,
        ) as ports,
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats",
            return_value=response,
        ) as peers,
    ):
        result = SnapshotClient(session, admission).collect("org-one", target)
    ports.assert_called_once_with(session, "org-one", device_type="gateway", mac=mac, limit=100)
    peers.assert_called_once_with(session, "org-one", mac=mac, site_id=site_id, duration="1h", limit=100)
    assert result["ports"] == [row]
    assert result["peers"] == [row]
    assert admission.check.call_count == 2


@pytest.mark.parametrize(
    "count,metadata,partial",
    [(99, {}, False), (100, {}, True), (100, {"total": 100}, False), (100, {"total": 101}, True)],
)
def test_full_page_without_completeness_evidence_is_partial(count, metadata, partial):
    """Never label a capped page complete when the server supplies no total."""
    rows = [{"port_id": str(index)} for index in range(count)]
    returned, actual_partial = SnapshotClient._page(
        SimpleNamespace(status_code=200, data={"results": rows, **metadata})
    )
    assert returned == rows
    assert actual_partial is partial


@pytest.mark.parametrize("field", ["site_id", "mac"])
def test_selected_pages_refuse_mismatched_returned_identity(field):
    """Stop before insight collection when a filtered page returns another gateway or site."""
    target = GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff")
    row = {"site_id": "site-one", "mac": "aabbccddeeff", field: "different"}
    with (
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
            return_value=SimpleNamespace(status_code=200, data={"results": [row]}),
        ),
        patch(
            "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgPeerPathStats",
            return_value=SimpleNamespace(status_code=200, data={"results": []}),
        ),
        patch("src.interfaces.portals.wan_performance.collection.snapshot_client.GatewayInsights.collect") as insights,
    ):
        with pytest.raises(ValueError, match="selected site and gateway"):
            SnapshotClient(MagicMock(), MagicMock()).collect("org-one", target)
    insights.assert_not_called()


def test_admission_failure_makes_zero_calls():
    """Refuse uncoordinated work when the shared lease is absent or expired."""
    admission = MagicMock()
    admission.check.side_effect = ConnectionError("lease unavailable")
    with patch("src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts") as call:
        with pytest.raises(ConnectionError, match="lease unavailable"):
            SnapshotClient(MagicMock(), admission).collect("org-one")
    call.assert_not_called()


def test_malformed_result_is_not_empty_success():
    """Reject invalid SDK payloads instead of hiding response errors."""
    with patch(
        "src.interfaces.portals.wan_performance.collection.snapshot_client.searchOrgSwOrGwPorts",
        return_value=SimpleNamespace(status_code=200, data={"results": "invalid"}),
    ):
        with pytest.raises(ValueError, match="results"):
            SnapshotClient(MagicMock(), MagicMock()).collect("org-one")
