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

if TYPE_CHECKING:
    from redis import Redis as SyncRedis

logger = logging.getLogger(__name__)

TOKEN_CACHE_TTL = 300  # seconds (5 min)
VAULT_SECRET_PREFIX = "secret/data/mist/tokens"


class MistSessionFactory:
    """Build ``mistapi.APISession`` instances for a given org."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        redis: SyncRedis | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._redis = redis or self._build_redis_client()
        self._vault = self._build_vault_client()

    # -- public API (max 25 lines each) --------------------------------

    def create_session(self, org_id: str) -> mistapi.APISession:
        """Return a ready-to-use session for *org_id*."""
        token = self._resolve_token(org_id)
        session = mistapi.APISession(
            host=self._settings.mist_api_host,
            apitoken=token,
        )
        return session

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

            client = redis_lib.Redis.from_url(self._settings.redis_url)
            client.ping()
            return client
        except Exception:
            logger.debug("Redis not available for token cache")
            return None


@lru_cache(maxsize=1)
def get_session_factory() -> MistSessionFactory:
    """Return a singleton factory (no per-request overhead)."""
    return MistSessionFactory()
