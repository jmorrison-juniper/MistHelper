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


def test_cross_organization_gateway_target_stops_before_admission():
    """Never reserve quota or call the API for a target from another organization."""
    from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

    store = MagicMock()
    target = GatewayIdentity(SiteIdentity("another-org", "site-one"), "112233445566")
    with patch("src.interfaces.portals.wan_performance.collection.live_service.SnapshotClient.collect") as collect:
        with pytest.raises(ValueError, match="organization"):
            LiveService(MagicMock(), "org-one", store, MagicMock()).refresh(target)
    store.acquire.assert_not_called()
    collect.assert_not_called()


@pytest.mark.parametrize("failure", ["missing_port", "cross_org", "no_store", "quota", "expired", "storage"])
def test_port_history_refuses_invalid_scope_or_failed_ownership(failure):
    """Never publish a snapshot or claim persistence after a rejected port refresh."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, SiteIdentity

    store, history = MagicMock(), MagicMock()
    store.cached.return_value = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [{"org_id": "org-one", "site_id": "site-one", "mac": "aabbccddeeff", "port_id": "ge-0/0/0"}],
        "peers": [],
    }
    target = CircuitIdentity(
        GatewayIdentity(SiteIdentity("other" if failure == "cross_org" else "org-one", "site-one"), "aabbccddeeff"),
        "unknown" if failure == "missing_port" else "ge-0/0/0",
    )
    if failure == "quota":
        store.acquire.side_effect = ConnectionError("quota")
    elif failure == "expired":
        store.acquire.return_value.check.side_effect = ConnectionError("expired")
    elif failure == "storage":
        history.upsert.side_effect = ConnectionError("storage")
    with patch(
        "src.interfaces.portals.wan_performance.collection.live_service.GatewayInsights.collect_for_port",
        return_value={"samples": [], "partial": False},
    ) as collect:
        with pytest.raises((ValueError, ConnectionError)):
            LiveService(MagicMock(), "org-one", store, None if failure == "no_store" else history).refresh_port(target)
    store.publish.assert_not_called()
    if failure in {"missing_port", "cross_org", "no_store", "quota"}:
        collect.assert_not_called()
        history.upsert.assert_not_called()


def test_port_history_refresh_writes_before_return_without_replacing_snapshot():
    """Use configured history and shared organization ownership for the selected port."""
    from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, SiteIdentity

    store, history = MagicMock(), MagicMock()
    target = CircuitIdentity(GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff"), "ge-0/0/0")
    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [{"org_id": "org-one", "site_id": "site-one", "mac": "aabbccddeeff", "port_id": "ge-0/0/0"}],
        "peers": [],
    }
    store.cached.return_value = snapshot
    with patch(
        "src.interfaces.portals.wan_performance.collection.live_service.GatewayInsights.collect_for_port",
        return_value={"samples": [], "partial": False},
    ) as collect:
        assert LiveService(MagicMock(), "org-one", store, history).refresh_port(target) == 0
    collect.assert_called_once_with("org-one", target, None, None)
    store.acquire.assert_called_once_with("org-one")
    assert store.acquire.return_value.check.call_count == 1
    history.upsert.assert_called_once_with(())
    store.publish.assert_not_called()


def test_peer_history_refresh_uses_cached_path_and_shared_admission():
    """Collect and persist one peer series only for a validated cached path."""
    from datetime import UTC, datetime, timedelta

    from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords
    from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [],
        "peers": [
            {
                "org_id": "org-one",
                "site_id": "site-one",
                "mac": "aabbccddeeff",
                "port_id": "ge-0/0/0",
                "peer_site_id": "site-two",
                "peer_port_id": "ge-0/0/1",
                "peer_mac": "11:22:33:44:55:66",
                "type": "ipsec",
            }
        ],
    }
    store, history = MagicMock(), MagicMock()
    store.cached.return_value = snapshot
    target = SnapshotRecords.build(snapshot)[0].identity
    hour = datetime(2024, 1, 1, 12, tzinfo=UTC)
    sample = HourlyMeasurement(
        target,
        hour,
        hour + timedelta(minutes=10),
        {
            "loss": MetricMeasurement(0.25, "%"),
            "latency": MetricMeasurement(33.3, "ms"),
            "jitter": MetricMeasurement(4.5, "ms"),
            "mos": MetricMeasurement(4.2, "score"),
        },
        "live",
    )
    with patch(
        "src.interfaces.portals.wan_performance.collection.live_service.PeerQualityInsights.collect",
        return_value=(sample,),
    ) as collect:
        count = LiveService(MagicMock(), "org-one", store, history).refresh_peer(target)

    assert count == 1
    store.acquire.assert_called_once_with("org-one")
    collect.assert_called_once_with(target)
    store.acquire.return_value.check.assert_called_once_with()
    history.upsert.assert_called_once_with((sample,))
    store.publish.assert_not_called()


def test_peer_history_refresh_rejects_uncached_path_before_admission():
    """Refuse peer identifiers that do not match the selected cached snapshot."""
    from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords

    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [],
        "peers": [],
    }
    store = MagicMock()
    store.cached.return_value = snapshot
    target = SnapshotRecords.build(
        {
            **snapshot,
            "peers": [
                {
                    "org_id": "org-one",
                    "site_id": "site-one",
                    "mac": "aabbccddeeff",
                    "port_id": "ge-0/0/0",
                    "peer_site_id": "site-two",
                    "peer_port_id": "ge-0/0/1",
                    "peer_mac": "11:22:33:44:55:66",
                    "type": "ipsec",
                }
            ],
        }
    )[0].identity
    with patch("src.interfaces.portals.wan_performance.collection.live_service.PeerQualityInsights.collect") as collect:
        with pytest.raises(ValueError, match="absent from the cached organization"):
            LiveService(MagicMock(), "org-one", store, MagicMock()).refresh_peer(target)
    store.acquire.assert_not_called()
    collect.assert_not_called()


def test_peer_history_refresh_stops_when_cached_snapshot_is_unavailable():
    """Do not query or write peer history when Redis cannot provide the path identity."""
    store, history = MagicMock(), MagicMock()
    store.cached.side_effect = ConnectionError("cache unavailable")
    from src.interfaces.portals.wan_performance.domain.identity import (
        GatewayIdentity,
        PeerPathIdentity,
        SiteIdentity,
    )

    target = PeerPathIdentity(
        GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff"),
        "ge-0/0/0",
        "ge-0/0/1",
        "11:22:33:44:55:66",
        "path-key-1",
    )

    with patch("src.interfaces.portals.wan_performance.collection.live_service.PeerQualityInsights.collect") as collect:
        with pytest.raises(ConnectionError, match="cache unavailable"):
            LiveService(MagicMock(), "org-one", store, history).refresh_peer(target)

    store.acquire.assert_not_called()
    collect.assert_not_called()
    history.upsert.assert_not_called()
