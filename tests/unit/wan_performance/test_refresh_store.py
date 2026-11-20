"""Check fail-closed refresh ownership and isolated snapshot cache behavior."""

import json
from unittest.mock import MagicMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from src.interfaces.wan_performance.integration.refresh_store import RefreshLease, RefreshStore


def test_only_one_org_refresh_wins():
    """Use atomic Redis admission rather than worker-local locks."""
    client = MagicMock()
    client.set.side_effect = [True, None]
    store = RefreshStore(client)
    lease = store.acquire("org-one")
    assert isinstance(lease, RefreshLease)
    with pytest.raises(ConnectionError, match="cooldown"):
        store.acquire("org-one")
    assert client.set.call_args.kwargs == {"nx": True, "ex": 300}


def test_outage_cannot_start_refresh():
    """Do not replace failed shared admission with an in-memory owner."""
    client = MagicMock()
    client.set.side_effect = RedisConnectionError("unavailable")
    with pytest.raises(RedisConnectionError):
        RefreshStore(client).acquire("org-one")


def test_expired_or_replaced_lease_refuses_next_call():
    """Stop API collection when a lease no longer belongs to the collector."""
    client = MagicMock()
    client.get.return_value = "another-owner"
    with pytest.raises(ConnectionError, match="expired"):
        RefreshLease(client, "org-one", "owner").check()


def test_cache_keys_are_separate_and_preserve_provenance():
    """Keep expiring snapshots distinct from application history."""
    client = MagicMock()
    store = RefreshStore(client)
    snapshot = {"org_id": "org-one", "provenance": "live", "ports": [], "peers": []}
    store.publish("org-one", snapshot)
    key = client.set.call_args.args[0]
    assert key == "misthelper:wan:v1:snapshot:org-one"
    assert client.set.call_args.kwargs == {"ex": 3600}
    client.get.return_value = client.set.call_args.args[1]
    assert store.cached("org-one") == snapshot


def test_synthetic_or_wrong_org_cannot_be_cached():
    """Reject offline fixtures and tenant mixing before a Redis write."""
    client = MagicMock()
    store = RefreshStore(client)
    with pytest.raises(ValueError, match="live"):
        store.publish("org-one", {"org_id": "org-one", "provenance": "synthetic"})
    with pytest.raises(ValueError, match="organization"):
        store.publish("org-one", {"org_id": "another-org", "provenance": "live"})
    client.set.assert_not_called()


def test_malformed_json_cache_is_not_empty_success():
    """Report invalid cache data rather than an apparently empty organization."""
    client = MagicMock()
    client.get.return_value = "{broken"
    with pytest.raises(json.JSONDecodeError):
        RefreshStore(client).cached("org-one")


def test_empty_body_cache_is_not_empty_success():
    """Distinguish an absent cache key from an empty invalid JSON body."""
    client = MagicMock()
    client.get.return_value = b""
    with pytest.raises(json.JSONDecodeError):
        RefreshStore(client).cached("org-one")


@pytest.mark.parametrize("remaining", [0, 1, 59])
def test_nearly_expired_owner_cannot_start_another_request(remaining):
    """Reserve enough lease lifetime for the bounded request timeout."""
    client = MagicMock()
    client.get.return_value = "owner"
    client.ttl.return_value = remaining
    with pytest.raises(ConnectionError, match="expired"):
        RefreshLease(client, "org-one", "owner").check()


def test_current_owner_with_remaining_lifetime_can_continue():
    """Keep valid ownership without deleting or releasing its cooldown."""
    client = MagicMock()
    client.get.return_value = "owner"
    client.ttl.return_value = 200
    RefreshLease(client, "org-one", "owner").check()
    assert client.ttl.call_args.args == ("misthelper:wan:v1:refresh:org-one",)
    client.delete.assert_not_called()
