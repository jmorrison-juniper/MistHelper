"""Coordinate current WAN refreshes and cache recent live snapshots."""

import json
import logging
import secrets
from typing import Any

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from src.foundation.persistence.db import DatabaseConfig
from src.interfaces.wan_performance.domain.identity import IdentityValidator

logger = logging.getLogger(__name__)


class RefreshLease:
    """Keep refresh ownership valid for the duration of collection."""

    def __init__(self, client: Any, org_id: str, token: str) -> None:
        """Keep an opaque owner token outside logs and cache values."""
        self.client = client  # Reuse the shared store.
        self.key = f"misthelper:wan:v1:refresh:{org_id}"  # Scope the lease to one organization.
        self.token = token  # Keep the current owner token private.

    def check(self) -> None:
        """Refuse collection after lease expiry or replacement."""
        if self.client.get(self.key) != self.token or self.client.ttl(self.key) < 60:  # Require 60 seconds remaining.
            raise ConnectionError("WAN refresh lease expired or changed owner.")  # Stop before the next request.


class RefreshStore:
    """Keep current snapshots separate from durable history."""

    def __init__(self, client: Any) -> None:
        """Accept a shared store client for production or isolated tests."""
        self.client = client  # Use the caller-selected store.

    @classmethod
    def connect(cls, config: DatabaseConfig) -> RefreshStore:  # Return the configured snapshot store.
        """Connect to the configured Redis service with finite waits."""
        if config.standalone_mode:  # Standalone mode has no shared refresh lock.
            raise ConnectionError("WAN refresh is unavailable without shared Redis.")  # Fail closed.
        client = redis.Redis(  # Reuse the configured shared Redis service.
            host=config.redis_host,  # Keep the configured endpoint.
            port=config.redis_port,  # Keep the configured port.
            password=config.redis_password or None,  # Use only the configured secret.
            decode_responses=True,  # Read stored records as text.
            socket_connect_timeout=1,  # Bound connection setup.
            socket_timeout=1,  # Bound each store operation.
            retry_on_timeout=False,  # Do not hide store attempts.
            retry=Retry(NoBackoff(), 0),  # Prevent implicit retry loops.
        )
        return cls(client)  # Return the shared current-state store.

    def acquire(self, org_id: str) -> RefreshLease:
        """Allow one refresh every five minutes for each organization."""
        valid_org = IdentityValidator.identifier(org_id, "org_id")  # Validate the cache key.
        token = secrets.token_hex(32)  # Create an unpredictable owner token.
        key = f"misthelper:wan:v1:refresh:{valid_org}"  # Use a versioned lease key.
        logger.info("Acquire shared WAN refresh admission for organization %s.", valid_org)  # Record safe scope.
        if not self.client.set(key, token, nx=True, ex=300):  # Reserve one five-minute refresh window.
            raise ConnectionError("WAN refresh cooldown is active. Use the cached snapshot.")  # Refuse duplicate work.
        logger.debug("Shared WAN refresh admission granted.")  # Record successful ownership.
        return RefreshLease(self.client, valid_org, token)  # Return the lease for per-request checks.

    def cached(self, org_id: str) -> dict[str, object] | None:
        """Read recent live data without making a Mist request."""
        valid_org = IdentityValidator.identifier(org_id, "org_id")  # Validate the cache key.
        raw = self.client.get(f"misthelper:wan:v1:snapshot:{valid_org}")  # Read only this organization.
        if raw is None:  # A cache miss is distinct from malformed data.
            return None  # Let the caller decide whether to refresh.
        snapshot = json.loads(raw)  # Reject malformed JSON rather than returning an empty snapshot.
        if not isinstance(snapshot, dict):  # Require one snapshot object.
            raise ValueError("WAN cached snapshot must be an object.")  # Report invalid cache shape.
        if snapshot.get("org_id") != valid_org or snapshot.get("provenance") != "live":  # Enforce tenant and source.
            raise ValueError("WAN cached snapshot has invalid organization or live provenance.")  # Fail closed.
        return snapshot  # Return only the validated current snapshot.

    def publish(self, org_id: str, snapshot: dict[str, object]) -> None:
        """Cache one live snapshot for one hour after scope validation."""
        valid_org = IdentityValidator.identifier(org_id, "org_id")  # Validate the cache key.
        if snapshot.get("provenance") != "live":  # Reject synthetic or unknown source data.
            raise ValueError("WAN cache requires live provenance.")  # Keep source class explicit.
        if snapshot.get("org_id") != valid_org:  # Prevent cross-organization cache writes.
            raise ValueError("WAN cache organization does not match.")  # Refuse tenant mismatch.
        encoded = json.dumps(snapshot, allow_nan=False, sort_keys=True)  # Reject non-finite cached values.
        logger.info("Write the recent WAN snapshot cache for organization %s.", valid_org)  # Record safe scope.
        self.client.set(f"misthelper:wan:v1:snapshot:{valid_org}", encoded, ex=3600)  # Keep current data for one hour.
        logger.debug("Cached the recent WAN snapshot.")  # Record successful publication.
