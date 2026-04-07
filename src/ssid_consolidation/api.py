"""Mist API adapter with retry and pagination helpers for SSID collection."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

LOGGER = logging.getLogger(__name__)
RETRYABLE_API_ERRORS = (
    AttributeError,
    RuntimeError,
    TypeError,
    ValueError,
)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry policy for Mist API requests.

    Args:
        max_retries: Maximum retry count for retryable failures.
        retry_delay: Base retry delay in seconds.
    """

    max_retries: int
    retry_delay: float


class MistApiAdapter:
    """Wrap `mistapi` calls with bounded retries and pagination expansion.

    Args:
        apisession: Active Mist API session object.
        mistapi_module: Imported `mistapi` package or a test double.
        org_id: Default organization ID for site lookups.
        retry_policy: Retry policy for retryable failures.
    """

    DEFAULT_PAGE_LIMIT = int(os.getenv("DEFAULT_API_PAGE_LIMIT", "1000"))

    def __init__(
        self,
        apisession: Any,
        mistapi_module: Any,
        org_id: str | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Store the Mist API session and retry configuration."""
        self.apisession = apisession
        self.mistapi = mistapi_module
        self.org_id = org_id
        self.retry_policy = self._resolve_retry_policy(retry_policy)

    def _resolve_retry_policy(self, retry_policy: RetryPolicy | None) -> RetryPolicy:
        """Resolve the retry policy from the argument or environment."""
        if retry_policy is not None:
            return retry_policy
        return RetryPolicy(
            max_retries=int(os.getenv("API_REQUEST_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("API_REQUEST_RETRY_DELAY", "5.0")),
        )

    def _call_with_retries(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call a Mist API function with exponential backoff on retryable failures."""
        last_response = None
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                response = fn(*args, **kwargs)
                last_response = response
                self._validate_response(response)
                return response
            except RETRYABLE_API_ERRORS as error:
                self._log_retry(attempt, error)
                if attempt < self.retry_policy.max_retries:
                    self._wait_for_retry(attempt)
        LOGGER.error(
            "MistApiAdapter: API call failed after %d attempts",
            self.retry_policy.max_retries + 1,
        )
        return last_response

    def _validate_response(self, response: Any) -> None:
        """Raise when the response does not contain a usable HTTP status."""
        status = getattr(response, "status_code", None)
        if status is None or (isinstance(status, int) and status >= 500):
            raise RuntimeError(f"Unusable response status={status}")

    def _log_retry(self, attempt: int, error: Exception) -> None:
        """Log one retry attempt for a failed Mist API call."""
        LOGGER.warning(
            "MistApiAdapter: call failed (attempt %d/%d): %s",
            attempt + 1,
            self.retry_policy.max_retries + 1,
            error,
        )

    def _wait_for_retry(self, attempt: int) -> None:
        """Sleep for the exponential backoff delay before the next retry."""
        time.sleep(self.retry_policy.retry_delay * (2**attempt))

    def _expand_paginated_response(self, response: Any, context: str) -> list[dict[str, Any]]:
        """Expand a Mist API paginated response into a list of dictionaries."""
        try:
            result = self.mistapi.get_all(response=response, mist_session=self.apisession)
        except (AttributeError, TypeError, ValueError):
            LOGGER.exception("MistApiAdapter: failed to expand %s response", context)
            return []
        if result is None:
            return []
        if isinstance(result, list):
            return result
        LOGGER.warning("MistApiAdapter: %s response did not expand to a list", context)
        return []

    def _get_site_wlan_endpoint(self) -> Callable[..., Any] | None:
        """Return the first supported site WLAN list function exposed by `mistapi`."""
        wlan_module = getattr(self.mistapi.api.v1.sites, "wlans", None)
        if wlan_module is None:
            return None
        for name in ("listSiteWLANS", "listSiteWlans", "listSiteWLanS"):
            endpoint = getattr(wlan_module, name, None)
            if callable(endpoint):
                return cast(Callable[..., Any], endpoint)
        return None

    def get_sites(self, org_id: str | None = None) -> list[dict[str, Any]]:
        """Return the site inventory for the resolved organization ID."""
        resolved_org_id = org_id or self.org_id
        if not resolved_org_id:
            raise ValueError("org_id is required for get_sites()")
        endpoint = self.mistapi.api.v1.orgs.sites.listOrgSites
        response = self._call_with_retries(
            endpoint,
            self.apisession,
            resolved_org_id,
            limit=self.DEFAULT_PAGE_LIMIT,
        )
        return self._expand_paginated_response(response, "sites")

    def get_site_wlans(self, site_id: str) -> list[dict[str, Any]]:
        """Return the WLAN list for a site, or an empty list when unavailable."""
        if not site_id:
            return []
        endpoint = self._get_site_wlan_endpoint()
        if endpoint is None:
            LOGGER.warning(
                "MistApiAdapter: no known WLAN list function found on mistapi for site %s",
                site_id,
            )
            return []
        response = self._call_with_retries(
            endpoint,
            self.apisession,
            site_id,
            limit=self.DEFAULT_PAGE_LIMIT,
        )
        return self._expand_paginated_response(response, f"wlans for {site_id}")
