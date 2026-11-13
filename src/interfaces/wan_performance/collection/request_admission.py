"""Admit actual shared-session HTTP attempts with a rolling Redis request ledger."""

import hashlib
import logging
import os
import secrets
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlsplit

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter

from src.foundation.persistence.db import DatabaseConfig

logger = logging.getLogger(__name__)
MAX_STATS_PAGE_LIMIT = 100
MAX_STATS_PAGES = 5


class StatsPageCollector:
    """Follow only bounded Mist search-after pages through shared admission."""

    def __init__(self, check: Callable[[], None], page_limit: int = 100, max_pages: int = 5) -> None:
        """Fix safe page and request caps before any search begins."""
        if not 1 <= page_limit <= MAX_STATS_PAGE_LIMIT or not 1 <= max_pages <= MAX_STATS_PAGES:
            raise ValueError("WAN stats pagination limits exceed the fixed collection bounds.")
        self.check = check
        self.page_limit = page_limit
        self.max_pages = max_pages

    def collect(self, request: Callable[[str | None], Any], label: str) -> tuple[list[dict[str, Any]], bool]:
        """Return validated rows and explicit truncation after at most five requests."""
        rows: list[dict[str, Any]] = []
        cursor, total = None, None
        seen: set[str] = set()
        for page_number in range(1, self.max_pages + 1):
            logger.info("Read WAN stats page %d for %s.", page_number, label)
            self.check()  # Reserve each actual API request through the shared admission boundary.
            page_rows, next_cursor, page_total = self._page(request(cursor), label)
            rows.extend(page_rows)  # Keep the complete bounded page for local identity filtering.
            logger.debug("Read %d rows from WAN stats page %d.", len(page_rows), page_number)
            if page_total is not None and total is not None and page_total != total:
                raise ValueError(f"{label} total changed during pagination.")
            total = page_total if page_total is not None else total
            if total is not None and len(rows) > total:
                raise ValueError(f"{label} returned more rows than its reported total.")
            if next_cursor is None:
                return rows, total > len(rows) if total is not None else len(page_rows) == self.page_limit
            if total is not None and len(rows) >= total:
                raise ValueError(f"{label} returned a continuation after its reported total.")
            if next_cursor in seen:
                raise ValueError(f"{label} repeated a search-after cursor.")
            seen.add(next_cursor)  # Refuse a pagination loop before the next request.
            cursor = next_cursor  # Send only the server-provided search-after token.
        return rows, True

    def _page(self, response: Any, label: str) -> tuple[list[dict[str, Any]], str | None, int | None]:
        """Validate one response envelope before accepting its rows or cursor."""
        if response.status_code != 200:
            logger.error("%s stats request failed with HTTP %s.", label, response.status_code)
            raise ConnectionError(f"{label} stats request failed with HTTP {response.status_code}.")
        data = response.data  # Read only the decoded SDK response, not an arbitrary next URL.
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError(f"{label} stats results must be an array.")
        rows = data["results"]
        if len(rows) > self.page_limit or any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"{label} stats results exceed the bounded object page.")
        total = data.get("total")
        if total is not None and (isinstance(total, bool) or not isinstance(total, int) or total < 0):
            raise ValueError(f"{label} stats total must be a non-negative integer.")
        return rows, self._cursor(data.get("next"), label), total

    @staticmethod
    def _cursor(value: object, label: str) -> str | None:
        """Extract one bounded search-after token without following its URL."""
        if value is None or value == "":
            return None
        if not isinstance(value, str) or len(value) > 4096 or any(ord(char) < 32 for char in value):
            raise ValueError(f"{label} stats next-page value must be a bounded URL string.")
        tokens = parse_qs(urlsplit(value).query, keep_blank_values=True).get("search_after", [])
        if len(tokens) != 1 or not tokens[0]:
            raise ValueError(f"{label} stats next-page URL has no unique search-after cursor.")
        return tokens[0]


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
