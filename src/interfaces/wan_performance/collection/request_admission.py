"""Admit actual shared-session HTTP attempts with a rolling Redis request ledger."""

import hashlib
import logging
import os
import secrets
from typing import Any
from urllib.parse import urlsplit

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter

from src.foundation.persistence.db import DatabaseConfig

logger = logging.getLogger(__name__)


class RequestLedger:
    """Enforce the documented 5000-per-hour ceiling per authentication fingerprint."""

    SCRIPT = """
local time = redis.call('TIME')
local now = tonumber(time[1]) + tonumber(time[2]) / 1000000
for _, key in ipairs(KEYS) do
    redis.call('ZREMRANGEBYSCORE', key, '-inf', now - 3600)
    if redis.call('ZCARD', key) >= 5000 then return 0 end
end
for _, key in ipairs(KEYS) do
    redis.call('ZADD', key, now, ARGV[1])
    redis.call('EXPIRE', key, 3601)
end
return 1
"""

    def __init__(self, client: redis.Redis, org_id: str | None = None) -> None:
        """Use one existing Redis service shared by all configured workers."""
        self.client = client
        self.org_id = org_id

    @staticmethod
    def enabled() -> bool:
        """Enable shared accounting automatically for configured application storage."""
        mode = os.getenv("WAN_SHARED_ADMISSION", "auto").lower()
        if mode not in {"auto", "true", "false"}:
            raise ValueError("WAN_SHARED_ADMISSION must be auto, true, or false.")
        if mode != "auto":
            return mode == "true"
        if os.getenv("MISTHELPER_STANDALONE", "").lower() == "true":
            return False
        if os.getenv("REDIS_HOST", "").strip() or os.getenv("REDIS_PASSWORD", "").strip():
            return True
        return not DatabaseConfig.from_env().standalone_mode

    @classmethod
    def connect(cls, org_id: str | None = None) -> "RequestLedger":
        """Read current application Redis settings and refuse standalone admission."""
        config = DatabaseConfig.from_env()
        if config.standalone_mode:
            raise ConnectionError("Shared API request admission requires the configured Redis.")
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
            ),
            org_id,
        )

    def admit(self, request: PreparedRequest) -> None:
        """Reserve one actual attempt atomically without storing or logging credentials."""
        authentication = request.headers.get("Authorization") or request.headers.get("Cookie")
        if not authentication:
            raise ConnectionError("Shared API admission requires configured authentication.")
        fingerprint = hashlib.sha256(authentication.encode()).hexdigest()
        keys = [f"misthelper:api:v1:requests:{fingerprint}"]
        org_id = self._organization(request)
        if org_id:
            keys.append(f"misthelper:api:v1:org:{org_id}")
        logger.info("Reserve one shared Mist API request attempt.")
        if self.client.eval(self.SCRIPT, len(keys), *keys, secrets.token_hex(16)) != 1:
            raise ConnectionError("The shared Mist API hourly quota is exhausted.")
        logger.debug("Reserved one shared Mist API request attempt.")

    def _organization(self, request: PreparedRequest) -> str | None:
        """Use request org identity or selected context for site-scoped calls."""
        from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver

        parts = urlsplit(str(request.url)).path.split("/")
        if len(parts) > 4 and parts[3] == "orgs":
            return parts[4]
        org_id = self.org_id or getattr(SourceDependencyResolver, "org_id", None)
        if len(parts) > 3 and parts[3] == "sites" and not org_id:
            raise ConnectionError("Site API request admission requires a selected organization.")
        return org_id


class AdmittedAdapter(HTTPAdapter):
    """Count every network attempt and refuse retries hidden inside the transport."""

    def __init__(self, ledger: RequestLedger, default_timeout: int) -> None:
        """Keep a finite timeout and zero unaccounted urllib3 retries."""
        super().__init__(max_retries=0)
        self.ledger = ledger
        self.default_timeout = min(default_timeout, 30)

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: Any = None,
        verify: Any = True,
        cert: Any = None,
        proxies: Any = None,
    ) -> Response:
        """Admit all methods, including SDK pagination, retries, and fast-mode calls."""
        self.ledger.admit(request)
        if timeout is None:
            timeout = self.default_timeout
        if isinstance(timeout, (int, float)):
            timeout = min(timeout, 30)
        elif isinstance(timeout, tuple):
            timeout = tuple(min(value, 30) if value is not None else 30 for value in timeout)
        response = super().send(request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies)
        if response.status_code == 429:
            response.close()
            raise ConnectionError("Mist returned HTTP 429. No automatic SDK retry started.")
        return response
