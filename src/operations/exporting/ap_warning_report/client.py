"""Read complete AP report sources through the authenticated Mist SDK."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit
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
    """Read definitions, sites, inventory, and site statistics for one organization."""

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
        sites = reader.read(
            mistapi.api.v1.orgs.sites.listOrgSites(self._session, self._org_id, limit=self._limit), "sites"
        )
        return {
            "definitions": reader.read(
                mistapi.api.v1.const.ap_led_status.listApLedDefinition(self._session), "definitions"
            ),
            "sites": sites,
            "inventory": self._inventory(reader),
            "stats": self._statistics(reader, sites),
        }

    def _inventory(self, reader: PageReader) -> list[dict[str, Any]]:
        """Read AP inventory without a site or connection filter."""
        logger.info("Requesting AP inventory")
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(
            self._session, self._org_id, type="ap", limit=self._limit
        )
        return reader.read(response, "inventory")

    def _statistics(self, reader: PageReader, sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Read complete AP statistics from every site, including disconnected APs."""
        rows: list[dict[str, Any]] = []  # WHY: The report needs one complete list after every site succeeds.
        for site in sites:  # WHY: Site-scoped statistics expose AP trouble omitted by the organization list.
            site_id = site.get("id")  # WHY: The SDK requires the site UUID for this endpoint.
            if not isinstance(site_id, str) or not site_id:  # WHY: A missing site ID must not skip site data.
                raise ValueError("An organization site has no valid identifier")  # WHY: Fail before any partial report.
            logger.info("Requesting AP statistics for site %s", site_id)  # WHY: Operators need to locate each read.
            response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                self._session, site_id, type="ap", status="all", limit=self._limit
            )  # WHY: Include offline APs and keep every request within the configured page limit.
            site_rows = reader.read(response, f"site {site_id} statistics")  # WHY: Reject failed or partial pages.
            rows.extend(site_rows)  # WHY: Join site results before selecting recent trouble.
            logger.debug(
                "Read AP statistics for site %s records=%d", site_id, len(site_rows)
            )  # WHY: Record read coverage.
        logger.debug("Read site AP statistics records=%d", len(rows))  # WHY: Summarize total site response coverage.
        return rows  # WHY: Return only after every site request completes.


class EventHistoryReader:
    """Read a bounded candidate history without treating a partial search as complete."""

    def __init__(self, session: Any, org_id: str, limit: int) -> None:
        """Retain the authenticated scope and supported page size."""
        self.session, self.org_id, self.limit = session, org_id, limit

    def read(self, mac: str, end: float) -> dict[str, Any]:
        """Keep failed or incomplete history explicit so it cannot clear a warning."""
        result: dict[str, Any] = {"events": [], "history_start": end - 3600, "history_end": end}
        logger.info("Reading bounded AP recovery history for %s", mac)
        try:
            result.update(self._pages(mac, end))
        except (RequestException, RuntimeError, ValueError, AttributeError) as error:
            logger.error("AP recovery history failed for %s (%s)", mac, type(error).__name__)
            result["evidence_status"] = "history_unavailable"
        logger.debug("AP recovery history for %s status=%s", mac, result["evidence_status"])
        return result

    def _pages(self, mac: str, end: float) -> dict[str, Any]:
        """Drain at most ten SDK pages and require a stable total and terminal page."""
        events: list[dict[str, Any]] = []
        cursor, total = None, None
        visited: set[str] = set()
        for _page in range(10):
            response = self._request(mac, end, cursor)
            if response is not None and response.status_code != 200:
                logger.error("AP event history returned HTTP %s for %s", response.status_code, mac)
                return {"events": events, "evidence_status": f"history_http_{response.status_code}"}
            body = EventSearchMetadata.body(response)
            if (body.get("start"), body.get("end")) != (end - 3600, end):
                raise ValueError("The AP event search did not confirm the requested time window")
            if total is not None and body["total"] != total:
                raise ValueError("The AP event search total changed during pagination")
            total = body["total"]
            events.extend(body["results"])
            cursor = EventSearchMetadata.cursor(body)
            if not cursor:
                status = "complete" if len(events) == total else "history_truncated"
                return {"events": events, "evidence_status": status}
            if cursor in visited:
                raise ValueError("The AP event search repeated a cursor")
            visited.add(cursor)
        return {"events": events, "evidence_status": "history_truncated"}

    def _request(self, mac: str, end: float, cursor: str | None) -> Any:
        """Request one AP-scoped page through the shared authenticated SDK session."""
        return mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
            self.session,
            self.org_id,
            mac=mac,
            device_type="ap",
            start=str(end - 3600),
            end=str(end),
            limit=self.limit,
            sort="timestamp",
            search_after=cursor,
        )


class EventSearchMetadata:
    """Validate event search bodies and server-provided pagination cursors."""

    @staticmethod
    def body(response: Any) -> dict[str, Any]:
        """Validate the documented search object before reading its records."""
        if response is None or response.status_code != 200:
            raise RuntimeError("The AP event search did not return HTTP 200")
        body = response.data
        if ResponseIntegrityChecker.body_failed_to_parse(response) or not isinstance(body, dict):
            raise ValueError("The AP event search body is invalid")
        rows, total = body.get("results"), body.get("total")
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError("The AP event search requires object records")
        if type(total) is not int or total < len(rows):  # Boolean counts cannot prove a complete search.
            raise ValueError("The AP event search requires a valid total")
        return body

    @staticmethod
    def cursor(body: dict[str, Any]) -> str | None:
        """Use only the server cursor instead of constructing a pagination value."""
        next_url = body.get("next")
        if next_url in (None, ""):
            return None
        if not isinstance(next_url, str):
            raise ValueError("The AP event cursor is invalid")
        values = parse_qs(urlsplit(next_url).query).get("search_after", [])
        if len(values) != 1 or not values[0]:
            raise ValueError("The AP event cursor is missing")
        return values[0]


class RecoveryEvidenceReader:
    """Collect event and fresh-statistics evidence only for report candidates."""

    def __init__(self, session: Any, org_id: str, limit: int) -> None:
        """Share authentication and establish whether cloud event names are verified."""
        self.session = session
        self.history = EventHistoryReader(session, org_id, limit)
        self.catalogue_verified = self._catalogue()

    def _catalogue(self) -> bool:
        """Require the live cloud connection keys before accepting recovery."""
        logger.info("Reading AP connection event definitions")
        try:
            response = mistapi.api.v1.const.device_events.listDeviceEventsDefinitions(self.session)
            rows = PageReader(self.session).read(response, "device event definitions")
            if any(not isinstance(row.get("key"), str) for row in rows):
                raise ValueError("The AP event catalogue requires text keys")
            keys = {row.get("key") for row in rows}
            verified = {"AP_CONNECTED", "AP_DISCONNECTED"} <= keys
        except (RequestException, RuntimeError, ValueError, AttributeError) as error:
            logger.error("AP event catalogue failed (%s)", type(error).__name__)
            return False
        if not verified:
            logger.error("The AP event catalogue lacks cloud connection event keys")
        logger.debug("AP connection event catalogue verified=%s", verified)
        return verified

    def read(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Retain missing fresh statistics or failed history without claiming recovery."""
        statistics = self._statistics(candidate)
        cutoff = datetime.now(UTC).timestamp()
        evidence = self.history.read(candidate["mac"], cutoff)
        if not self.catalogue_verified and evidence["evidence_status"] == "complete":
            evidence["evidence_status"] = "catalogue_unavailable"
        evidence.update(statistics=statistics, catalogue_verified=self.catalogue_verified)
        return evidence

    def _statistics(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Read the actual device statistics without manufacturing a device identifier."""
        if not candidate.get("device_id") or not candidate.get("site_id"):
            logger.error("AP recovery statistics lack a device or site identifier for %s", candidate["mac"])
            return {}
        logger.info("Refreshing AP recovery statistics for %s", candidate["mac"])
        try:
            response = mistapi.api.v1.sites.stats.getSiteDeviceStats(
                self.session, candidate["site_id"], candidate["device_id"]
            )
            if response.status_code != 200 or ResponseIntegrityChecker.body_failed_to_parse(response):
                raise RuntimeError("Fresh AP statistics did not return a valid HTTP 200 response")
            if not isinstance(response.data, dict):
                raise ValueError("Fresh AP statistics require an object")
            logger.debug("Refreshed AP recovery statistics for %s", candidate["mac"])
            return response.data
        except (RequestException, RuntimeError, ValueError, AttributeError) as error:
            logger.error("Fresh AP statistics failed for %s (%s)", candidate["mac"], type(error).__name__)
            return {}
