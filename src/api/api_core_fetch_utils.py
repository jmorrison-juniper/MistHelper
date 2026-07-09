"""APICoreFetchUtils -- low-level Mist API fetch helpers.

Extracted from MistHelper.py during initiative 1014 (Cat E, position 10).
Canonical body lives here; MistHelper.py provides a top-level re-export
alias (``from src.api.api_core_fetch_utils import APICoreFetchUtils``) so
historical ``MistHelper.APICoreFetchUtils`` / ``mh.APICoreFetchUtils``
callers keep working.

The module-level ``apisession`` and ``DEFAULT_API_PAGE_LIMIT`` globals are
resolved lazily via ``importlib.import_module("MistHelper")`` inside method
bodies to keep FR-028 IG-health clean (no top-level MistHelper import
statement).
"""

from __future__ import annotations  # WHY: PEP 604 unions in annotations.

import importlib  # WHY: lazy MistHelper fetch of apisession + page-limit global.
import logging  # WHY: debug trace for API-response unwrap.
from typing import Any  # WHY: dynamic response-object annotation.

import mistapi  # WHY: dotted-path Mist API resolution + pagination helper.


class APICoreFetchUtils:  # Low-level Mist API fetch helpers.
    """Core API Fetch Utilities.

    Handles site and inventory fetching with pagination.
    Extracted from APIFetchUtils.
    """

    @staticmethod
    def all_sites_with_limit(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetch all sites with unified pagination.

        Args:
            org_id: The organization ID

        Returns:
            List of site dictionaries

        SECURITY: Read-only; no sensitive data logged.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + DEFAULT_API_PAGE_LIMIT.
        response = mistapi.api.v1.orgs.sites.listOrgSites(mh.apisession, org_id, limit=mh.DEFAULT_API_PAGE_LIMIT)
        return mistapi.get_all(response=response, mist_session=mh.apisession)  # type: ignore[no-any-return]

    @staticmethod
    def all_inventory_with_limit(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetch full org inventory with unified pagination.

        Args:
            org_id: The organization ID

        Returns:
            List of inventory dictionaries (includes all VC physical members)

        SECURITY: Read-only; no secrets in inventory object fields.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + DEFAULT_API_PAGE_LIMIT.
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(
            mh.apisession, org_id, vc=True, limit=mh.DEFAULT_API_PAGE_LIMIT
        )  # vc=True includes all physical VC member devices
        return mistapi.get_all(response=response, mist_session=mh.apisession)  # type: ignore[no-any-return]

    @staticmethod
    def get_api_response_data(response: Any) -> Any:
        """Return a mistapi response's .data payload, or the response itself when .data is absent."""
        logging.debug("Unwrapping API response payload (type=%s)", type(response).__name__)  # Trace unwrap calls
        return getattr(response, "data", response)  # mistapi carries parsed JSON on .data; fall back to the raw object
