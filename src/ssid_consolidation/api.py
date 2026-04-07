"""Minimal Mist API adapter with retry and pagination helpers for SSID collection.

This adapter intentionally implements a small, well-tested surface that the
Collector can call: `get_sites()` and `get_site_wlans()`. It wraps MistAPI
calls with exponential backoff and uses `mistapi.get_all()` to handle
pagination.
"""
from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any


class MistApiAdapter:
    """Adapter wrapping `mistapi` module + apisession with retries.

    Args:
        apisession: The mistapi session object (from MistHelper)
        mistapi_module: The imported `mistapi` package
        org_id: Optional org_id to default calls
    """

    DEFAULT_PAGE_LIMIT = int(os.getenv("DEFAULT_API_PAGE_LIMIT", "1000"))

    def __init__(
        self,
        apisession: Any,
        mistapi_module: Any,
        org_id: str | None = None,
        *,
        max_retries: int | None = None,
        retry_delay: float | None = None,
    ):
        self.apisession = apisession
        self.mistapi = mistapi_module
        self.org_id = org_id
        self.max_retries = (
            max_retries
            if max_retries is not None
            else int(os.getenv("API_REQUEST_MAX_RETRIES", "3"))
        )
        self.retry_delay = (
            retry_delay
            if retry_delay is not None
            else float(os.getenv("API_REQUEST_RETRY_DELAY", "5.0"))
        )

    def _call_with_retries(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        last_resp = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = fn(*args, **kwargs)
                last_resp = resp
                status = getattr(resp, "status_code", None)
                # Consider None (mistapi swallowed error) or 5xx as failure
                if status is None or (isinstance(status, int) and status >= 500):
                    raise RuntimeError(f"Unusable response status={status}")
                return resp
            except Exception as e:
                logging.warning("MistApiAdapter: call failed (attempt %d/%d): %s", attempt + 1, self.max_retries + 1, e)
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
        logging.error("MistApiAdapter: API call failed after %d attempts", self.max_retries + 1)
        return last_resp

    def get_sites(self, org_id: str | None = None) -> list[dict[str, Any]]:
        """Return list of sites for the org.

        Uses `mistapi.api.v1.orgs.sites.listOrgSites` and `mistapi.get_all`.
        """
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id is required for get_sites()")

        fn = self.mistapi.api.v1.orgs.sites.listOrgSites
        resp = self._call_with_retries(fn, self.apisession, org, limit=self.DEFAULT_PAGE_LIMIT)
        try:
            result = self.mistapi.get_all(response=resp, mist_session=self.apisession)  # type: ignore[no-any-return]
            # Normalize None -> empty list for callers
            return result if result is not None else []
        except Exception:
            logging.exception("MistApiAdapter: failed to expand paginated sites response")
            return []

    def get_site_wlans(self, site_id: str) -> list[dict[str, Any]]:
        """Return list of WLANs for a site.

        Tries common variant names for the endpoint and returns an empty
        list on any failure to keep collector fallback simple.
        """
        if not site_id:
            return []

        # Try a few plausible function names for the site WLANs endpoint
        candidates = [
            (self.mistapi.api.v1.sites.wlans, "listSiteWLANS"),
            (self.mistapi.api.v1.sites.wlans, "listSiteWlans"),
            (self.mistapi.api.v1.sites.wlans, "listSiteWLanS"),
        ]

        for module, name in candidates:
            fn = getattr(module, name, None)
            if fn:
                resp = self._call_with_retries(fn, self.apisession, site_id, limit=self.DEFAULT_PAGE_LIMIT)
                try:
                    result = self.mistapi.get_all(response=resp, mist_session=self.apisession)  # type: ignore[no-any-return]
                    return result if result is not None else []
                except Exception:
                    logging.exception("MistApiAdapter: failed to expand paginated wlans response for %s", site_id)
                    return []

        logging.warning("MistApiAdapter: no known WLAN list function found on mistapi for site %s", site_id)
        return []
