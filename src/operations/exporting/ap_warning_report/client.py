"""Read complete AP report sources through the authenticated Mist SDK."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import mistapi
from requests import RequestException

from src.mist.access.api.response_integrity import ResponseIntegrityChecker

logger = logging.getLogger(__name__)


class PageReader:
    """Reject incomplete or malformed SDK pages before report generation."""

    def __init__(self, session: Any) -> None:
        """Retain the existing session and its transport controls."""
        self._session = session

    def read(self, response: Any, subject: str) -> list[dict[str, Any]]:
        """Collect every SDK page or fail without returning partial rows."""
        logger.info("Reading AP report source %s", subject)
        rows: list[dict[str, Any]] = []
        visited: set[str] = set()
        try:
            while True:
                rows.extend(self._validate(response, subject))
                if not response.next:
                    break
                response = self._next(response, subject, visited)
        except (RuntimeError, ValueError, AttributeError, RequestException) as error:
            logger.error("AP report source %s failed (%s)", subject, type(error).__name__)
            raise
        logger.debug("Read AP report source %s records=%d", subject, len(rows))
        return rows

    @staticmethod
    def _validate(response: Any, subject: str) -> list[dict[str, Any]]:
        """Check status, parse integrity, and the collection shape on each page."""
        if response is None:
            raise RuntimeError(f"Missing AP report page for {subject}")
        if response.status_code != 200:
            raise RuntimeError(f"AP report source {subject} returned HTTP {response.status_code}")
        if ResponseIntegrityChecker.body_failed_to_parse(response):
            raise ValueError(f"AP report source {subject} did not parse")
        payload = response.data
        if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
            raise ValueError(f"AP report source {subject} must contain object records")
        return payload

    def _next(self, response: Any, subject: str, visited: set[str]) -> Any:
        """Use SDK pagination while refusing a repeated or invalid cursor."""
        cursor = response.next
        if not isinstance(cursor, str) or cursor in visited:
            raise RuntimeError(f"Invalid or repeated AP report page for {subject}")
        visited.add(cursor)
        logger.info("Reading the next AP report page for %s", subject)
        following = mistapi.get_next(mist_session=self._session, response=response)
        logger.debug("Received the next AP report page for %s", subject)
        return following


class ApWarningClient:
    """Read definitions, sites, inventory, and statistics for one organization."""

    def __init__(self, session: Any, org_id: str, page_limit: int) -> None:
        """Validate the request scope before any SDK operation."""
        try:
            self._org_id = str(UUID(org_id))
        except (ValueError, TypeError, AttributeError):
            raise ValueError("A valid organization identifier is required for the AP report") from None
        if isinstance(page_limit, bool) or not isinstance(page_limit, int) or not 1 <= page_limit <= 1000:
            raise ValueError("The AP report page limit must be between 1 and 1000")
        self._session, self._limit = session, page_limit

    def read(self) -> dict[str, list[dict[str, Any]]]:
        """Complete every source read before returning data for persistence."""
        reader = PageReader(self._session)
        logger.info("Reading AP report sources for organization %s", self._org_id)
        try:
            sources = self._fetch(reader)
        except (RequestException, RuntimeError, ValueError, AttributeError) as error:
            logger.error("AP report source read failed for organization %s (%s)", self._org_id, type(error).__name__)
            raise RuntimeError("The AP report source read failed. No report was written.") from None
        logger.debug("Read all AP report sources for organization %s", self._org_id)
        return sources

    def _fetch(self, reader: PageReader) -> dict[str, list[dict[str, Any]]]:
        """Use explicit SDK arguments for every required source."""
        return {
            "definitions": reader.read(
                mistapi.api.v1.const.ap_led_status.listApLedDefinition(self._session), "definitions"
            ),
            "sites": reader.read(
                mistapi.api.v1.orgs.sites.listOrgSites(self._session, self._org_id, limit=self._limit), "sites"
            ),
            "inventory": self._inventory(reader),
            "stats": self._statistics(reader),
        }

    def _inventory(self, reader: PageReader) -> list[dict[str, Any]]:
        """Read AP inventory without a site or connection filter."""
        logger.info("Requesting AP inventory")
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(
            self._session, self._org_id, type="ap", limit=self._limit
        )
        return reader.read(response, "inventory")

    def _statistics(self, reader: PageReader) -> list[dict[str, Any]]:
        """Read trouble evidence for both connected and disconnected APs."""
        logger.info("Requesting AP statistics")
        response = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
            self._session, self._org_id, type="ap", status="all", limit=self._limit
        )
        return reader.read(response, "statistics")
