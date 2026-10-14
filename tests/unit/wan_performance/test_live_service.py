"""Check collection-to-history ordering and preserve old cache on failure."""

from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.portals.wan_performance.collection.live_service import LiveService


def test_refresh_commits_history_before_cache():
    """Publish only after the selected store accepts the complete batch."""
    store = MagicMock()
    history = MagicMock()
    service = LiveService(MagicMock(), "org-one", store, history)
    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [],
        "peers": [],
        "partial": False,
    }
    order = MagicMock()
    order.attach_mock(history.upsert, "write")
    order.attach_mock(store.publish, "publish")
    with patch(
        "src.interfaces.portals.wan_performance.collection.live_service.SnapshotClient.collect",
        return_value=snapshot,
    ):
        assert service.refresh() == snapshot
    assert [call[0] for call in order.mock_calls] == ["write", "publish"]
    store.acquire.assert_called_once_with("org-one")
    history.upsert.assert_called_once_with(())


def test_history_failure_preserves_previous_cache():
    """Do not label data as persisted after the database rejects the write."""
    store = MagicMock()
    history = MagicMock()
    history.upsert.side_effect = ConnectionError("history unavailable")
    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [],
        "peers": [],
    }
    with patch(
        "src.interfaces.portals.wan_performance.collection.live_service.SnapshotClient.collect",
        return_value=snapshot,
    ):
        with pytest.raises(ConnectionError, match="history unavailable"):
            LiveService(MagicMock(), "org-one", store, history).refresh()
    store.publish.assert_not_called()


def test_shared_admission_failure_has_no_sdk_call():
    """Check the Redis owner before constructing any outgoing data request."""
    store = MagicMock()
    store.acquire.side_effect = ConnectionError("cooldown")
    with patch("src.interfaces.portals.wan_performance.collection.live_service.SnapshotClient.collect") as collect:
        with pytest.raises(ConnectionError, match="cooldown"):
            LiveService(MagicMock(), "org-one", store, MagicMock()).refresh()
    collect.assert_not_called()


def test_expired_collection_lease_cannot_write_history_or_cache():
    """Refuse publication after collection loses its shared ownership."""
    store, history = MagicMock(), MagicMock()
    store.acquire.return_value.check.side_effect = ConnectionError("expired")
    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [],
        "peers": [],
    }
    with patch(
        "src.interfaces.portals.wan_performance.collection.live_service.SnapshotClient.collect", return_value=snapshot
    ):
        with pytest.raises(ConnectionError, match="expired"):
            LiveService(MagicMock(), "org-one", store, history).refresh()
    history.upsert.assert_not_called()
    store.publish.assert_not_called()
