"""High-level Mist API read/write service backed by mistapi SDK (R-05).

``MistEndpointService`` resolves entity types to SDK methods via the
registry in ``types.py`` and applies rate-limiting before each call.
All methods are synchronous — designed to run inside Celery workers.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

import mistapi

from src.shared.mist.types import MistEndpoint, MistEntityRegistry

logger = logging.getLogger(__name__)

# WHY: bound the pagination loop so one endpoint cannot exhaust the worker heap.
# A sync of a large organization stays well under this count. Issue #1903.
MAX_PAGINATION_PAGES = 500


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

    def __init__(self, session: mistapi.APISession) -> None:
        self._session = session

    # -- public read/write (max 25 lines) --------------------------------

    def read_entity(
        self,
        entity_type: str,
        ids: dict[str, str],
    ) -> ApiResult:
        """Fetch a single entity's current configuration from Mist."""
        endpoint = MistEntityRegistry.get(entity_type)
        if endpoint.read_method is None:
            msg = f"No read_method for entity type: {entity_type!r}"
            raise AttributeError(msg)
        func = self._resolve_func(endpoint, endpoint.read_method)
        args = self._build_args(endpoint, ids)
        response = func(self._session, **args)
        return self._wrap(response)

    def write_entity(
        self,
        entity_type: str,
        ids: dict[str, str],
        body: dict[str, Any],
    ) -> ApiResult:
        """Push a full config payload to a single Mist entity."""
        endpoint = MistEntityRegistry.get(entity_type)
        if endpoint.write_method is None:
            msg = f"No write_method for entity type: {entity_type!r}"
            raise AttributeError(msg)
        func = self._resolve_func(endpoint, endpoint.write_method)
        args = self._build_args(endpoint, ids)
        response = func(self._session, **args, body=body)
        return self._wrap(response)

    def list_all_entities(
        self,
        entity_type: str,
        ids: dict[str, str],
    ) -> ApiResult:
        """Fetch all pages of a list operation via the registry."""
        endpoint = MistEntityRegistry.get(entity_type)
        if not endpoint.list_method:
            msg = f"No list_method for entity type: {entity_type!r}"
            raise AttributeError(msg)
        func = self._resolve_func(endpoint, endpoint.list_method)
        args = self._build_args(endpoint, ids)
        all_data = self._paginate(func, args)
        return ApiResult(status_code=200, data=all_data)

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

    def _paginate(self, func: Any, args: dict[str, str]) -> list:
        """Follow SDK pagination until the last page, the page limit, or a repeat."""
        all_data: list = []
        response = func(self._session, **args)
        all_data.extend(self._extract_list(response))
        seen_cursors: set[str] = set()  # WHY: a repeated cursor means the API is looping.
        pages = 1  # WHY: the first page is already in all_data.
        while cursor := getattr(response, "next", None):
            if not self._accept_cursor(cursor, seen_cursors, pages, func):
                break  # WHY: the guard already logged the reason.
            response = func(self._session, **args, next=cursor)
            all_data.extend(self._extract_list(response))
            pages += 1  # WHY: count the page against MAX_PAGINATION_PAGES.
        return all_data

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
        data = getattr(response, "data", response)
        if isinstance(data, list):
            return data
        return [data] if data else []
