"""Mist API client boundary for the PSK hygiene report."""

from __future__ import annotations

import logging
from typing import Any

import mistapi

logger = logging.getLogger(__name__)  # Keep client logs tied to this module.
DEFAULT_LIMIT = 1000  # Use the same high page size pattern as other organization exports.


class PskHygieneClient:
    """Fetch read-only organization PSK hygiene inputs."""

    def __init__(self, apisession: Any, org_id: str) -> None:
        """Store the Mist session and organization ID."""
        self.apisession = apisession  # Keep the active Mist session for SDK calls.
        self.org_id = org_id  # Keep the selected organization for each endpoint.

    def fetch_psks(self) -> list[dict[str, Any]]:
        """Fetch all organization PSK records."""
        logger.info("Fetching organization PSKs for hygiene scoring")  # Log before the read-only API call.
        response = mistapi.api.v1.orgs.psks.listOrgPsks(
            self.apisession, self.org_id, limit=DEFAULT_LIMIT
        )  # Request the first PSK page.
        records = self._records_from_response(response)  # Read all pages through the SDK helper.
        logger.debug("Fetched %d organization PSK records", len(records))  # Log the safe record count only.
        return records  # Return plain dictionaries for the model boundary.

    def fetch_wlans(self) -> list[dict[str, Any]]:
        """Fetch all organization WLAN records."""
        logger.info("Fetching organization WLANs for PSK SSID matching")  # Log before the read-only API call.
        response = mistapi.api.v1.orgs.wlans.listOrgWlans(
            self.apisession, self.org_id, limit=DEFAULT_LIMIT
        )  # Request the first WLAN page.
        records = self._records_from_response(response)  # Read all pages through the SDK helper.
        logger.debug("Fetched %d organization WLAN records", len(records))  # Log the safe record count only.
        return records  # Return plain dictionaries for the model boundary.

    def fetch_templates(self) -> list[dict[str, Any]]:
        """Fetch all organization template records."""
        logger.info("Fetching organization templates for PSK SSID matching")  # Log before the read-only API call.
        response = mistapi.api.v1.orgs.templates.listOrgTemplates(
            self.apisession, self.org_id, limit=DEFAULT_LIMIT
        )  # Request the first template page.
        records = self._records_from_response(response)  # Read all pages through the SDK helper.
        logger.debug("Fetched %d organization template records", len(records))  # Log the safe record count only.
        return records  # Return plain dictionaries for the model boundary.

    def _records_from_response(self, response: Any) -> list[dict[str, Any]]:
        """Return paginated SDK records as dictionaries."""
        records = mistapi.get_all(response=response, mist_session=self.apisession) or []  # Let the SDK handle pages.
        normalized = [dict(record) for record in records if isinstance(record, dict)]  # Copy only mapping records.
        logger.debug("Normalized %d paginated records", len(normalized))  # Log the safe normalized count only.
        return normalized  # Return copies so callers cannot mutate SDK internals.
