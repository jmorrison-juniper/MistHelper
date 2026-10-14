"""Verify bounded SDK collection without production credentials or automatic refresh."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.portals.wan_performance.collection.snapshot_client import SnapshotClient


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
    port_call.assert_called_once_with(session, "org-one", device_type="gateway", limit=100)
    peer_call.assert_called_once_with(session, "org-one", duration="1h", limit=100)
    assert admission.check.call_count == 2
    assert result["ports"] == [{"port_id": "ge-0/0/0"}]
    assert result["partial"] is True


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
