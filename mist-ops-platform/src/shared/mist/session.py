"""Mist APISession factory with Vault token retrieval and caching (R-07).

Creates ``mistapi.APISession`` objects with credentials retrieved from
HashiCorp Vault and cached briefly in Redis to avoid repeated lookups.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import hvac
import mistapi

from src.shared.config.settings import AppSettings, get_settings
from src.shared.mist.rate_limit import OrgRateLimiter

if TYPE_CHECKING:
    from redis import Redis as SyncRedis
    from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)

TOKEN_CACHE_TTL = 300  # seconds (5 min)
VAULT_SECRET_PREFIX = "secret/data/mist/tokens"  # nosec B105 - This is a Vault path, not a secret.


class MistSessionFactory:
    """Build ``mistapi.APISession`` instances for a given org."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        redis: SyncRedis | None = None,
        rate_redis: AsyncRedis | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._redis = redis or self._build_redis_client()
        self._vault = self._build_vault_client()
        self._rate_redis = rate_redis  # WHY: optional async client, built lazily if not injected.

    # -- public API (max 25 lines each) --------------------------------

    def create_session(self, org_id: str) -> mistapi.APISession:
        """Return a ready-to-use session for *org_id*."""
        token = self._resolve_token(org_id)
        session = mistapi.APISession(
            host=self._settings.mist_api_host,
            apitoken=token,
        )
        return session

    def create_rate_limiter(self, org_id: str) -> OrgRateLimiter | None:
        """Build an org-scoped Mist API rate limiter, or None if unavailable."""
        # WHY: log before building the limiter.
        logger.info("Building rate limiter for org %s", org_id)
        # WHY: reuse one cached async client for every org.
        redis_client = self._get_async_redis_client()
        if redis_client is None:
            logger.warning(
                "Rate limiter disabled for org %s: no async Redis client",
                org_id,
            )  # WHY: explain the fail-open path so operators see it in logs.
            return None
        # WHY: one bucket per org, per rate_limit.py R-06.
        limiter = OrgRateLimiter(redis_client, org_id)
        # WHY: confirm the result after the action.
        logger.debug("Rate limiter ready for org %s", org_id)
        return limiter

    # -- internal helpers ------------------------------------------------

    def _resolve_token(self, org_id: str) -> str:
        """Retrieve token from cache, then Vault, then env fallback."""
        cached = self._read_cache(org_id)
        if cached:
            return cached

        token = self._read_vault(org_id)
        if token:
            self._write_cache(org_id, token)
            return token

        # Fallback to global env token
        if self._settings.mist_api_token:
            return self._settings.mist_api_token

        msg = f"No Mist API token for org {org_id}"
        raise RuntimeError(msg)

    def _read_vault(self, org_id: str) -> str | None:
        """Fetch API token from Vault KV v2."""
        if not self._vault:
            return None
        try:
            path = f"{VAULT_SECRET_PREFIX}/{org_id}"
            secret = self._vault.secrets.kv.v2.read_secret_version(
                path=path,
                raise_on_deleted_version=True,
            )
            return secret["data"]["data"].get("api_token")
        except Exception:
            logger.debug("Vault lookup failed for org %s", org_id)
            return None

    def _read_cache(self, org_id: str) -> str | None:
        """Read cached token from Redis."""
        if not self._redis:
            return None
        key = f"mist_token:{org_id}"
        value = self._redis.get(key)
        return value.decode() if isinstance(value, bytes) else value

    def _write_cache(self, org_id: str, token: str) -> None:
        """Cache token in Redis with TTL."""
        if not self._redis:
            return
        key = f"mist_token:{org_id}"
        self._redis.setex(key, TOKEN_CACHE_TTL, token)

    def _build_vault_client(self) -> hvac.Client | None:
        """Build Vault client if configured."""
        addr = self._settings.vault_addr
        tok = self._settings.vault_token
        if not addr or not tok:
            logger.info("Vault not configured — using env token only")
            return None
        client = hvac.Client(url=addr, token=tok)
        if not client.is_authenticated():
            logger.warning("Vault auth failed — falling back to env token")
            return None
        return client

    def _build_redis_client(self) -> SyncRedis | None:
        """Connect to Redis for token caching."""
        try:
            import redis as redis_lib

            from src.shared.redis_timeouts import redis_timeout_kwargs

            logger.info("Redis token cache client build starts.")  # Announce the connect attempt.
            # WHY: a client with no socket limit holds this worker forever on a silent host.
            client = redis_lib.Redis.from_url(
                self._settings.redis_url,
                **redis_timeout_kwargs(),
            )
            client.ping()
            logger.debug("Redis token cache client build done.")  # Confirm the live connection.
            return client
        except Exception:
            logger.debug("Redis not available for token cache")
            return None

    def _get_async_redis_client(self) -> AsyncRedis | None:
        """Lazily build and cache the async Redis client for rate limiting."""
        if self._rate_redis is not None:
            return self._rate_redis  # WHY: reuse the cached client instead of reconnecting.
        try:
            # WHY: lazy import, matches the sync client pattern.
            import redis.asyncio as redis_async_lib

            from src.shared.redis_timeouts import redis_timeout_kwargs

            logger.info("Async Redis rate limit client build starts.")  # Announce the connect.
            # WHY: the same socket limits stop a silent host from holding the rate limiter.
            self._rate_redis = redis_async_lib.Redis.from_url(
                self._settings.redis_url,
                **redis_timeout_kwargs(),
            )
            logger.debug("Async Redis rate limit client build done.")  # Confirm the client exists.
            return self._rate_redis
        except Exception:
            # WHY: fail open, like the token cache.
            logger.debug("Async Redis not available for rate limiting")
            return None


@lru_cache(maxsize=1)
def get_session_factory() -> MistSessionFactory:
    """Return a singleton factory (no per-request overhead)."""
    return MistSessionFactory()
