"""Reserve shared request capacity before the Mist transport sends a request."""

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
    """Track request attempts by credential and organization in shared Redis."""

    LIMIT = 5000  # Keep a fixed ceiling for each rolling hour.
    SCRIPT = """local time = redis.call('TIME')
local now = tonumber(time[1]) + tonumber(time[2]) / 1000000
for _, key in ipairs(KEYS) do
    redis.call('ZREMRANGEBYSCORE', key, '-inf', now - 3600)
    if redis.call('ZCARD', key) >= tonumber(ARGV[1]) then return 0 end
end
for _, key in ipairs(KEYS) do
    redis.call('ZADD', key, now, ARGV[2])
    redis.call('EXPIRE', key, 3601)
end
return 1"""  # Reserve all matching quotas in one atomic operation.

    def __init__(self, client: Any, org_id: str | None = None) -> None:
        """Use one shared Redis client for all configured workers."""
        self.client = client  # Keep the injected store for deterministic tests.
        self.org_id = org_id  # Preserve explicit organization context when available.

    @staticmethod
    def enabled() -> bool:
        """Enable shared accounting when application storage uses Redis."""
        mode = os.getenv("WAN_SHARED_ADMISSION", "auto").lower()  # Read the explicit opt-in once.
        if mode not in {"auto", "true", "false"}:  # Reject ambiguous configuration.
            raise ValueError("WAN_SHARED_ADMISSION must be auto, true, or false.")  # Fail on invalid settings.
        if mode != "auto":  # Respect an explicit operator choice.
            return mode == "true"  # Keep explicit off and on values distinct.
        return not DatabaseConfig.from_env().standalone_mode  # Use shared admission with configured Redis.

    @classmethod
    def connect(cls, org_id: str | None = None) -> RequestLedger:  # Return the configured shared request ledger.
        """Connect to the configured shared Redis service with finite waits."""
        config = DatabaseConfig.from_env()  # Read the existing application store settings.
        if config.standalone_mode:  # Shared accounting cannot use local-only mode.
            raise ConnectionError("Shared API request admission requires configured Redis.")  # Fail closed.
        client = redis.Redis(  # Reuse the configured Redis service.
            host=config.redis_host,  # Keep the configured endpoint.
            port=config.redis_port,  # Keep the configured port.
            password=config.redis_password or None,  # Use only the configured secret.
            decode_responses=True,  # Read store results as text.
            socket_connect_timeout=1,  # Bound connection setup.
            socket_timeout=1,  # Bound each store operation.
            retry_on_timeout=False,  # Do not hide store attempts.
            retry=Retry(NoBackoff(), 0),  # Prevent implicit store retries.
        )
        return cls(client, org_id)  # Return the shared request ledger.

    def admit(self, request: PreparedRequest) -> None:
        """Reserve one actual request attempt without storing credentials."""
        authentication = request.headers.get("Authorization") or request.headers.get("Cookie")  # Read auth locally.
        if not authentication:  # Anonymous requests cannot share a safe identity key.
            raise ConnectionError("Shared API admission requires configured authentication.")  # Fail closed.
        fingerprint = hashlib.sha256(authentication.encode()).hexdigest()  # Store only a one-way credential key.
        keys = [f"misthelper:api:v1:requests:{fingerprint}"]  # Count attempts for this credential.
        org_id = self._organization(request)  # Resolve the tenant bucket before reservation.
        if org_id:  # Include cross-credential organization control when known.
            keys.append(f"misthelper:api:v1:org:{org_id}")  # Share the organization ceiling.
        logger.info("Reserve one shared Mist API request attempt.")  # Record the operation without auth data.
        result = self.client.eval(
            self.SCRIPT, len(keys), *keys, self.LIMIT, secrets.token_hex(16)
        )  # Reserve atomically.
        if result != 1:  # Reject a full quota or a malformed result.
            raise ConnectionError("The shared Mist API hourly quota is exhausted.")  # Stop before network access.
        logger.debug("Reserved one shared Mist API request attempt.")  # Record successful reservation.

    def _organization(self, request: PreparedRequest) -> str | None:
        """Use the request path or selected context for organization scope."""
        path = urlsplit(str(request.url)).path.split("/")  # Parse only the URL path.
        if len(path) > 4 and path[3] == "orgs":  # Organization requests expose the tenant in the path.
            return path[4]  # Use the source organization value.
        if len(path) > 3 and path[3] == "sites" and not self.org_id:  # Site requests need a tenant context.
            raise ConnectionError("Site API request admission requires a selected organization.")  # Fail closed.
        return self.org_id  # Retain the selected organization for site requests.


class AdmittedAdapter(HTTPAdapter):
    """Admit each HTTP attempt and prevent hidden transport retries."""

    def __init__(self, ledger: RequestLedger, default_timeout: int) -> None:
        """Keep zero adapter retries and a finite default timeout."""
        super().__init__(max_retries=0)  # Prevent unaccounted urllib3 retries.
        self.ledger = ledger  # Share the request counter across workers.
        self.default_timeout = min(default_timeout, 30)  # Bound waits before connecting.

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: Any = None,
        verify: Any = True,
        cert: Any = None,
        proxies: Any = None,
    ) -> Response:
        """Reserve every request and stop before a retry after HTTP 429."""
        self.ledger.admit(request)  # Count the actual request before transport.
        if timeout is None:  # Apply the configured timeout when the caller has none.
            timeout = self.default_timeout  # Keep the request bounded.
        if isinstance(timeout, (int, float)):  # Cap a scalar timeout.
            timeout = min(timeout, 30)  # Prevent long transport waits.
        elif isinstance(timeout, tuple):  # Cap separate connect and read timeouts.
            timeout = tuple(min(value, 30) if value is not None else 30 for value in timeout)  # Bound each value.
        response = super().send(request, stream, timeout, verify, cert, proxies)  # Send one admitted attempt.
        if response.status_code == 429:  # Refuse a hidden SDK retry after rate limiting.
            response.close()  # Release the response before raising.
            raise ConnectionError("Mist returned HTTP 429. No automatic SDK retry started.")  # Fail explicitly.
        return response  # Return the single admitted response.
