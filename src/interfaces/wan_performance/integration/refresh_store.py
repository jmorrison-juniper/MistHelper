"""Bound WAN-only refreshes across workers using the existing configured Redis."""

import json
import logging
import secrets

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from src.foundation.persistence.db import DatabaseConfig
from src.interfaces.wan_performance.domain.identity import IdentityValidator

logger = logging.getLogger(__name__)


class RefreshLease:
    """Retain an org cooldown after work so immediate refreshes cannot bypass it."""

    def __init__(self, client: redis.Redis, org_id: str, token: str) -> None:
        """Keep an opaque owner token out of logs and cache records."""
        self.client = client
        self.key = f"misthelper:wan:v1:refresh:{org_id}"
        self.token = token

    def check(self) -> None:
        """Refuse each subsequent request when ownership expires or changes."""
        if self.client.get(self.key) != self.token or self.client.ttl(self.key) < 60:
            raise ConnectionError("WAN refresh lease expired or changed owner.")


class RefreshStore:
    """Separate recent snapshots from durable history and fail closed on outage."""

    def __init__(self, client: redis.Redis) -> None:
        """Accept the configured public Redis client for deterministic tests."""
        self.client = client

    @classmethod
    def connect(cls, config: DatabaseConfig) -> "RefreshStore":
        """Use the existing Redis endpoint with finite connection and command waits."""
        if config.standalone_mode:
            raise ConnectionError("WAN refresh is unavailable without shared Redis.")
        return cls(
            redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password or None,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
                retry_on_timeout=False,
                retry=Retry(NoBackoff(), 0),
            )
        )

    def acquire(self, org_id: str) -> RefreshLease:
        """Allow at most one two-page WAN refresh every five minutes per org."""
        IdentityValidator.identifier(org_id, "org_id")
        token = secrets.token_hex(32)
        logger.info("Acquire shared WAN refresh admission for organization %s.", org_id)
        if not self.client.set(f"misthelper:wan:v1:refresh:{org_id}", token, nx=True, ex=300):
            raise ConnectionError("WAN refresh cooldown is active. Use the cached snapshot.")
        logger.debug("Shared WAN refresh admission granted.")
        return RefreshLease(self.client, org_id, token)

    def cached(self, org_id: str) -> dict[str, object] | None:
        """Read a recent snapshot without initiating any Mist request."""
        IdentityValidator.identifier(org_id, "org_id")
        raw = self.client.get(f"misthelper:wan:v1:snapshot:{org_id}")
        if raw is None:
            return None
        snapshot = json.loads(raw)
        if not isinstance(snapshot, dict) or snapshot.get("org_id") != org_id or snapshot.get("provenance") != "live":
            raise ValueError("WAN cached snapshot has invalid organization or live provenance.")
        return snapshot

    def publish(self, org_id: str, snapshot: dict[str, object]) -> None:
        """Cache only a complete live org snapshot for one hour, never history."""
        if snapshot.get("provenance") != "live":
            raise ValueError("WAN cache requires live provenance.")
        if snapshot.get("org_id") != IdentityValidator.identifier(org_id, "org_id"):
            raise ValueError("WAN cache organization does not match.")
        logger.info("Write the recent WAN snapshot cache for organization %s.", org_id)
        self.client.set(
            f"misthelper:wan:v1:snapshot:{org_id}", json.dumps(snapshot, allow_nan=False, sort_keys=True), ex=3600
        )
        logger.debug("Cached the recent WAN snapshot.")
