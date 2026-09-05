"""High-level Mist API read/write service backed by mistapi SDK (R-05).

``MistEndpointService`` resolves entity types to SDK methods via the
registry in ``types.py`` and applies rate-limiting before each call.
All methods are synchronous — designed to run inside Celery workers.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import mistapi

from src.shared.mist.types import MistEndpoint, MistEntityRegistry

if TYPE_CHECKING:
    from src.shared.mist.rate_limit import OrgRateLimiter

logger = logging.getLogger(__name__)

# WHY: bound the pagination loop so one endpoint cannot exhaust the worker heap.
# A sync of a large organization stays well under this count. Issue #1903.
MAX_PAGINATION_PAGES = 500

# WHY: name the status code so a reader does not have to recall it. Issue #1886.
HTTP_TOO_MANY_REQUESTS = 429
# WHY: cap outbound 429 retries so throttling cannot hang a worker forever.
MAX_429_RETRIES = 3
# WHY: the first backoff wait after a 429, before it doubles.
BASE_BACKOFF_SECONDS = 1.0
# WHY: never wait longer than this for one retry, even with a large Retry-After.
MAX_BACKOFF_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class ApiResult:
    """Thin wrapper around a mistapi response."""

    status_code: int
    data: dict[str, Any] | list[dict[str, Any]]

    @property
    def success(self) -> bool:
        """True when status_code is in the 2xx range."""
        return 200 <= self.status_code < 300

    @property
    def error(self) -> str | None:
        """Extract error detail from data on non-2xx responses."""
        if self.success:
            return None
        if isinstance(self.data, dict):
            return self.data.get("detail", str(self.data))
        return str(self.data)


class MistEndpointService:
    """Read and write Mist configuration via the SDK."""

    def __init__(
        self,
        session: mistapi.APISession,
        rate_limiter: OrgRateLimiter | None = None,
    ) -> None:
        self._session = session  # WHY: the authenticated per-org Mist SDK session.
        self._rate_limiter = rate_limiter  # WHY: optional org budget; None means none is enforced.

    # -- public read/write (max 25 lines) --------------------------------

    def read_entity(
        self,
        entity_type: str,
        ids: dict[str, str],
    ) -> ApiResult:
        """Fetch a single entity's current configuration from Mist."""
        # WHY: log before the outbound call.
        logger.info("Reading entity %s from Mist", entity_type)
        endpoint = MistEntityRegistry.get(entity_type)
        if endpoint.read_method is None:
            msg = f"No read_method for entity type: {entity_type!r}"
            raise AttributeError(msg)
        func = self._resolve_func(endpoint, endpoint.read_method)
        args = self._build_args(endpoint, ids)
        # WHY: apply rate limiting and 429 retry.
        response = self._invoke_with_protection(func, args)
        result = self._wrap(response)
        logger.debug(
            "Read %s returned status %d",
            entity_type,
            result.status_code,
        )  # WHY: summarize the outcome after the call.
        return result

    def write_entity(
        self,
        entity_type: str,
        ids: dict[str, str],
        body: dict[str, Any],
    ) -> ApiResult:
        """Push a full config payload to a single Mist entity."""
        logger.info("Writing entity %s to Mist", entity_type)  # WHY: log before the outbound call.
        endpoint = MistEntityRegistry.get(entity_type)
        if endpoint.write_method is None:
            msg = f"No write_method for entity type: {entity_type!r}"
            raise AttributeError(msg)
        func = self._resolve_func(endpoint, endpoint.write_method)
        args = self._build_args(endpoint, ids)
        # WHY: same protected call path.
        response = self._invoke_with_protection(func, {**args, "body": body})
        result = self._wrap(response)
        logger.debug(
            "Write %s returned status %d",
            entity_type,
            result.status_code,
        )  # WHY: summarize the outcome after the call.
        return result

    def list_all_entities(
        self,
        entity_type: str,
        ids: dict[str, str],
    ) -> ApiResult:
        """Fetch all pages of a list operation via the registry.

        The result carries the status code of the last page. If the call
        fails, the result holds the Mist error body and no data records.
        """
        # WHY: log before the outbound calls.
        logger.info("Listing entity %s from Mist", entity_type)
        endpoint = MistEntityRegistry.get(entity_type)
        if not endpoint.list_method:
            msg = f"No list_method for entity type: {entity_type!r}"
            raise AttributeError(msg)
        func = self._resolve_func(endpoint, endpoint.list_method)
        args = self._build_args(endpoint, ids)
        all_data, response = self._paginate(func, args)  # read the pages and the last response
        return self._list_result(entity_type, all_data, response)  # use the real status

    @staticmethod
    def _list_result(entity_type: str, rows: list, response: Any) -> ApiResult:
        """Build a list result from the status of the last page."""
        result = MistEndpointService._wrap(response)  # read the real status of that page
        if not result.success:  # a failed call must never report data records
            logger.warning(  # name the entity type and the status of the failure
                "Mist list of %s failed with status %s",
                entity_type,
                result.status_code,
            )
            return result  # give the caller the failure and the Mist error body
        logger.debug("Mist list of %s read %d records", entity_type, len(rows))  # log the end
        return ApiResult(status_code=result.status_code, data=rows)  # real status plus rows

    # -- internal helpers ------------------------------------------------

    @staticmethod
    def _resolve_func(
        endpoint: MistEndpoint,
        method_name: str,
    ) -> Any:
        """Dynamically import the SDK module and return the method."""
        parts = endpoint.api_module.split(".")
        mod_path = f"mistapi.api.v1.{'.'.join(parts)}"
        module = importlib.import_module(mod_path)
        return getattr(module, method_name)

    @staticmethod
    def _build_args(
        endpoint: MistEndpoint,
        ids: dict[str, str],
    ) -> dict[str, str]:
        """Map endpoint id_params to the provided *ids* dict."""
        args: dict[str, str] = {}
        for param in endpoint.id_params:
            if param not in ids:
                msg = f"Missing required id param: {param!r}"
                raise ValueError(msg)
            args[param] = ids[param]
        return args

    @staticmethod
    def _wrap(response: Any) -> ApiResult:
        """Normalise a mistapi response into an ``ApiResult``."""
        status = getattr(response, "status_code", 200)
        data = getattr(response, "data", response)
        if isinstance(data, str):
            data = {}
        return ApiResult(status_code=status, data=data)

    def _paginate(self, func: Any, args: dict[str, str]) -> tuple[list, Any]:
        """Follow SDK pagination and return the rows and the last response.

        The caller needs the last response, because ``list_all_entities``
        reports the status code of that page. Issue #1884.
        """
        all_data: list = []
        response = self._invoke_with_protection(func, args)  # WHY: protect the first page too.
        all_data.extend(self._extract_list(response))
        seen_cursors: set[str] = set()  # WHY: a repeated cursor means the API is looping.
        pages = 1  # WHY: the first page is already in all_data.
        while cursor := getattr(response, "next", None):
            if not self._accept_cursor(cursor, seen_cursors, pages, func):
                break  # WHY: the guard already logged the reason.
            # WHY: protect every later page too.
            response = self._invoke_with_protection(func, {**args, "next": cursor})
            all_data.extend(self._extract_list(response))
            pages += 1  # WHY: count the page against MAX_PAGINATION_PAGES.
        logger.debug(
            "Mist pagination read %d pages and %d rows",
            pages,
            len(all_data),
        )  # WHY: summarize the outcome after all pages.
        return all_data, response  # WHY: the caller reads the status of the last response.

    def _invoke_with_protection(
        self,
        func: Any,
        kwargs: dict[str, Any],
    ) -> Any:
        """Call an SDK function with rate limiting and 429 retry applied."""
        attempt = 0  # WHY: count attempts so the retry limit is enforced.
        while True:
            # WHY: respect the org budget before every attempt, including retries.
            self._acquire_rate_limit_slot()
            response = func(self._session, **kwargs)  # WHY: the real outbound Mist SDK call.
            # WHY: read the status the same way _wrap does.
            status = getattr(response, "status_code", 200)
            if status != HTTP_TOO_MANY_REQUESTS or attempt >= MAX_429_RETRIES:
                return response  # WHY: success, a non-429 error, or retries used up: stop here.
            # WHY: honor Retry-After or fall back to exponential backoff.
            delay = self._backoff_delay(response, attempt)
            logger.warning(
                "Mist API returned 429. Retry %d of %d in %.1fs.",
                attempt + 1,
                MAX_429_RETRIES,
                delay,
            )  # WHY: make the retry visible to operators, per issue #1886.
            time.sleep(delay)  # WHY: back off before the next attempt.
            attempt += 1  # WHY: count this attempt against the retry limit.

    def _acquire_rate_limit_slot(self) -> None:
        """Block on the org rate limiter before an outbound call, if configured."""
        if self._rate_limiter is None:
            return  # WHY: no limiter configured, for example a pre-org bootstrap call.
        try:
            # WHY: bridge the async limiter into this sync path.
            asyncio.run(self._rate_limiter.wait_and_acquire())
        except Exception as exc:
            logger.warning(
                "Rate limiter unavailable: %s. Proceeding without a slot.",
                exc,
            )  # WHY: fail open so a Redis outage does not block real Mist calls.

    @staticmethod
    def _backoff_delay(response: Any, attempt: int) -> float:
        """Compute the wait before the next 429 retry."""
        # WHY: default bounded backoff.
        exponential = min(BASE_BACKOFF_SECONDS * (2**attempt), MAX_BACKOFF_SECONDS)
        # WHY: some responses omit a headers attribute.
        headers = getattr(response, "headers", None)
        # WHY: honor the API hint when present.
        retry_after = headers.get("Retry-After") if headers else None
        if retry_after is None:
            return exponential  # WHY: no header, so use the default backoff.
        try:
            # WHY: cap even a large Retry-After value.
            return min(float(retry_after), MAX_BACKOFF_SECONDS)
        except (TypeError, ValueError):
            return exponential  # WHY: a malformed header falls back to the default backoff.

    @staticmethod
    def _accept_cursor(cursor: Any, seen: set[str], pages: int, func: Any) -> bool:
        """Return True when the loop may fetch one more page."""
        name = getattr(func, "__name__", "unknown")  # WHY: name the endpoint in the log.
        if pages >= MAX_PAGINATION_PAGES:  # WHY: bound the heap and the run time.
            logger.warning(
                "Pagination for %s stopped at the %d page limit. The result is incomplete.",
                name,
                MAX_PAGINATION_PAGES,
            )
            return False
        key = str(cursor)  # WHY: the cursor may be any type the SDK returns.
        if key in seen:  # WHY: a repeat means the loop would never end.
            logger.error(
                "Pagination for %s repeated a cursor. Stopping to avoid an endless loop.",
                name,
            )
            return False
        seen.add(key)  # WHY: record the cursor before the next call.
        return True

    @staticmethod
    def _extract_list(response: Any) -> list:
        """Extract list data from an SDK response."""
        data = getattr(response, "data", response)  # read the body of this page
        if isinstance(data, list):  # only a list body holds data records
            return data
        kind = type(data).__name__  # name the body type for the log line
        logger.debug("Mist page body is a %s and not a list, so drop it", kind)
        return []  # an error body must never become a data record
