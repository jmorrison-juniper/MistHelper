"""Verify current snapshot caching and refresh ownership."""

import json

import pytest

from src.interfaces.wan_performance.integration.refresh_store import RefreshStore


class FakeRedis:
    """Store values and lease expiry for isolated tests."""

    def __init__(self) -> None:
        """Initialize an empty in-memory store."""
        self.values: dict[str, str] = {}  # Keep test keys separate.
        self.expiry: dict[str, int] = {}  # Track requested expiration.

    def set(self, key: str, value: str, **options: object) -> bool:
        """Apply Redis set and NX behavior."""
        if options.get("nx") and key in self.values:  # Refuse an existing lease.
            return False  # Preserve the first refresh owner.
        self.values[key] = value  # Store the selected value.
        if isinstance(options.get("ex"), int):  # Keep the expiration value.
            self.expiry[key] = options["ex"]  # Record lease or cache lifetime.
        return True  # Report a successful write.

    def get(self, key: str) -> str | None:
        """Return a stored value or a cache miss."""
        return self.values.get(key)  # Preserve Redis read semantics.

    def ttl(self, key: str) -> int:
        """Return a controlled lease lifetime."""
        return self.expiry.get(key, 0)  # Use zero for expired or absent keys.


class TestRefreshStore:
    """Test current-state controls without a live Redis service."""

    def test_only_one_org_refresh_wins(self) -> None:
        """Keep one five-minute owner for each organization."""
        client = FakeRedis()  # Create isolated shared state.
        store = RefreshStore(client)  # Use the fake Redis client.
        lease = store.acquire("org-one")  # Reserve the first refresh.
        assert lease.key.endswith("org-one")  # Keep the tenant in the lease key.
        assert client.expiry[lease.key] == 300  # Enforce the five-minute cooldown.
        with pytest.raises(ConnectionError, match="cooldown"):  # Refuse a concurrent refresh.
            store.acquire("org-one")  # Do not start duplicate work.

    @pytest.mark.parametrize("remaining", [0, 59])  # Cover expired and nearly expired leases.
    def test_expired_lease_refuses_next_request(self, remaining: int) -> None:
        """Require at least one minute of ownership before each request."""
        client = FakeRedis()  # Create isolated state.
        lease = RefreshStore(client).acquire("org-one")  # Reserve a refresh.
        client.expiry[lease.key] = remaining  # Model the remaining lease time.
        with pytest.raises(ConnectionError, match="lease"):  # Require refusal.
            lease.check()  # Stop before the next request.

    def test_cache_is_org_scoped_and_keeps_live_provenance(self) -> None:
        """Store one live snapshot under its matching organization."""
        store = RefreshStore(FakeRedis())  # Create isolated current-state storage.
        snapshot = {"org_id": "org-one", "provenance": "live", "ports": []}  # Build one live source result.
        store.publish("org-one", snapshot)  # Cache the complete snapshot.
        assert store.cached("org-one") == snapshot  # Read the selected tenant.
        assert store.cached("org-two") is None  # Keep cache keys isolated.

    def test_non_live_or_wrong_org_snapshots_are_rejected(self) -> None:
        """Refuse synthetic data and cross-organization writes."""
        store = RefreshStore(FakeRedis())  # Create isolated storage.
        with pytest.raises(ValueError, match="live"):  # Require source validation.
            store.publish("org-one", {"org_id": "org-one", "provenance": "synthetic"})  # Refuse synthetic data.
        with pytest.raises(ValueError, match="does not match"):  # Require tenant validation.
            store.publish("org-one", {"org_id": "org-two", "provenance": "live"})  # Refuse wrong tenant.

    @pytest.mark.parametrize("value", ["{", "", "[]"])  # Cover malformed and wrong-shaped cache values.
    def test_malformed_cache_is_not_empty_success(self, value: str) -> None:
        """Report invalid cache data instead of returning an empty snapshot."""
        client = FakeRedis()  # Create isolated storage.
        client.values["misthelper:wan:v1:snapshot:org-one"] = value  # Insert malformed data.
        with pytest.raises((json.JSONDecodeError, ValueError)):  # Require explicit cache failure.
            RefreshStore(client).cached("org-one")  # Reject invalid cache content.
