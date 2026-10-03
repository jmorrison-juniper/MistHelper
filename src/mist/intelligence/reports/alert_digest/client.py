"""Mist API client for alert digest and alarm acknowledgement."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

import json  # Format error bodies for acknowledgement result messages.
import logging  # Record each API call before and after execution.
from collections.abc import Mapping  # Type raw response dictionaries.
from dataclasses import dataclass, field  # Carry paged list results in a small value object.
from typing import Any  # Accept mistapi response objects without type hints.

import mistapi  # Use the installed Mist SDK methods required by the feature.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.

ALARM_PAGE_LIMIT = 1000  # Request the largest supported page to reduce API calls.
MAX_ALARM_PAGES = 100  # Stop a broken paging loop before it runs forever.
HTTP_OK = 200  # The Mist API returns HTTP 200 for successful alarm calls.
ERROR_TEXT_LIMIT = 300  # Keep operator log cells readable.


@dataclass(slots=True)
class AlertDigestListResult:
    """The outcome of one paged alarm search."""

    rows: list[dict[str, Any]] = field(default_factory=list)  # Hold usable rows from the response.
    status_code: int | None = None  # Preserve the status of the last page.
    complete: bool = True  # False when a guard or page error stops the read.
    problem: str = ""  # Explain why a list read failed.


class AlertDigestClient:
    """Wrap the Mist alarm endpoints used by menus 280 and 281."""

    def __init__(self, apisession: Any, org_id: str, page_limit: int = ALARM_PAGE_LIMIT) -> None:
        """Keep the Mist session and organization for all alarm calls."""
        self._apisession = apisession  # Store the active Mist session for SDK calls.
        self._org_id = org_id  # Store the selected organization identifier.
        self._page_limit = max(1, int(page_limit))  # Prevent an invalid limit from creating an endless read.

    def list_alarm_definitions(self) -> list[dict[str, Any]]:
        """Read alarm definitions from the Mist constants endpoint."""
        logger.info("Reading alarm definitions")  # Log before the API call.
        response = mistapi.api.v1.const.alarm_defs.listAlarmDefinitions(self._apisession)  # Call the SDK method.
        problem = self._page_problem(response, "alarm definitions")  # Validate status and shape.
        if problem:  # A failed definition read cannot support category mapping.
            logger.error("The alarm definition read failed: %s", problem)  # Surface the failed read.
            return []  # Return no definitions, so categories become unknown.
        rows = [row for row in response.data if isinstance(row, dict)]  # Keep only object rows.
        logger.debug("Read %d alarm definitions", len(rows))  # Log result count.
        return rows  # Return raw definition rows for the model.

    def list_org_sites(self) -> list[dict[str, Any]]:
        """Read organization sites for site-name output."""
        logger.info("Reading organization sites for alert digest")  # Log before the API call.
        response = mistapi.api.v1.orgs.sites.listOrgSites(
            self._apisession, self._org_id, limit=self._page_limit
        )  # Read org sites with the shared page limit.
        status = getattr(response, "status_code", None)  # Read the SDK response status.
        if status != HTTP_OK:  # A failed site read should not stop the digest.
            problem = "No HTTP answer arrived." if status is None else f"HTTP {status}"  # Summarize the failure.
            logger.warning("The alert digest site read failed: %s", problem)  # Surface the site lookup issue.
            return []  # Continue with site identifiers when names are unavailable.
        rows = mistapi.get_all(response=response, mist_session=self._apisession)  # Page through site rows.
        sites = [row for row in rows if isinstance(row, dict)]  # Keep only object rows for the name map.
        logger.debug("Read %d organization sites for alert digest", len(sites))  # Log result count.
        return sites  # Return raw site rows for the model.

    def search_alarms(self, lookback_hours: int) -> AlertDigestListResult:
        """Read every alarm page in the lookback window."""
        logger.info("Searching org %s alarms for %d hours", self._org_id, lookback_hours)  # Log before search.
        rows: list[dict[str, Any]] = []  # Collect usable rows from each page.
        links: set[str] = set()  # Track next links to stop a paging loop.
        response = self._read_first_alarm_page(lookback_hours)  # Read the first page with query values.
        for page in range(1, MAX_ALARM_PAGES + 1):  # Bound the paging loop.
            problem = self._alarm_page_problem(response)  # Validate this page before reading rows.
            if problem:  # A partial list must not look complete.
                return AlertDigestListResult([], getattr(response, "status_code", None), False, problem)  # Fail closed.
            results = response.data["results"]  # The problem check proved this list exists.
            rows.extend(row for row in results if isinstance(row, dict))  # Keep only object rows.
            link = str(response.data.get("next") or "")  # Read the next link, if present.
            if not results or not link:  # Empty or final page ends the list.
                logger.debug("Read %d alarms on %d pages", len(rows), page)  # Log result count.
                return AlertDigestListResult(rows, response.status_code)  # Return complete rows.
            if link in links or page == MAX_ALARM_PAGES:  # Stop repeated links or guard overflow.
                break  # Return guarded partial rows below.
            links.add(link)  # Remember this link before reading the next page.
            response = self._read_next_alarm_page(response, page + 1)  # Follow the SDK next page helper.
        return self._guard_result(rows, len(links) + 1)  # Return partial rows with a warning.

    def acknowledge_alarms(
        self, alarm_ids: list[str], note: str = "Acknowledged by MistHelper alert digest"
    ) -> tuple[int | None, str]:
        """Send one bulk acknowledgement request."""
        body = {"alarm_ids": alarm_ids, "note": note}  # Build the body required by the Mist API.
        logger.info("Acknowledging %d alarms for org %s", len(alarm_ids), self._org_id)  # Log before the API call.
        response = mistapi.api.v1.orgs.alarms.ackOrgMultipleAlarms(self._apisession, self._org_id, body=body)  # Send.
        status = getattr(response, "status_code", None)  # Preserve the returned HTTP status.
        logger.debug("The alarm acknowledgement request returned HTTP %s", status)  # Log result status.
        return self._change_result(status, getattr(response, "data", None))  # Return status and error text.

    def unacknowledge_alarms(
        self, alarm_ids: list[str], note: str = "Unacknowledged by MistHelper alert digest"
    ) -> tuple[int | None, str]:
        """Send one bulk unacknowledgement request."""
        body = {"alarm_ids": alarm_ids, "note": note}  # Build the body required by the Mist API.
        logger.info("Unacknowledging %d alarms for org %s", len(alarm_ids), self._org_id)  # Log before the API call.
        response = mistapi.api.v1.orgs.alarms.unackOrgMultipleAlarms(self._apisession, self._org_id, body=body)  # Send.
        status = getattr(response, "status_code", None)  # Preserve the returned HTTP status.
        logger.debug("The alarm unacknowledgement request returned HTTP %s", status)  # Log result status.
        return self._change_result(status, getattr(response, "data", None))  # Return status and error text.

    def _read_first_alarm_page(self, lookback_hours: int) -> Any:
        """Read the first alarm search page."""
        logger.info("Reading alert digest alarm page 1")  # Log before the SDK call.
        response = mistapi.api.v1.orgs.alarms.searchOrgAlarms(  # Call the public alarm search endpoint.
            self._apisession,
            self._org_id,
            duration=f"{lookback_hours}h",
            limit=self._page_limit,
        )
        logger.debug("Alert digest alarm page 1 returned HTTP %s", getattr(response, "status_code", None))  # Log.
        return response  # Return the response for validation.

    def _read_next_alarm_page(self, response: Any, page: int) -> Any:
        """Follow the next link of one alarm search page."""
        logger.info("Reading alert digest alarm page %d", page)  # Log before the SDK helper call.
        next_response = mistapi.get_next(self._apisession, response)  # Follow the server-provided next link.
        logger.debug("Alert digest alarm page %d returned HTTP %s", page, getattr(next_response, "status_code", None))
        return next_response  # Return the response for validation.

    @classmethod
    def _alarm_page_problem(cls, response: Any) -> str:
        """Return a problem string for an unusable alarm page."""
        if response is None:  # The SDK returned no page after a next link.
            return "The alarm search returned no next page."  # Explain the missing page.
        return cls._page_problem(response, "alarm search")  # Reuse status and shape validation.

    @staticmethod
    def _page_problem(response: Any, label: str) -> str:
        """Return a problem string for an unusable SDK response."""
        status = getattr(response, "status_code", None)  # Read the SDK response status.
        if status is None:  # No HTTP answer arrived.
            return "No HTTP answer arrived. Read the mistapi line in script.log."  # Tell the operator where to look.
        if status != HTTP_OK:  # Any non-200 response is not a complete read.
            return f"The {label} returned HTTP {status}."  # Name the failing read.
        data = getattr(response, "data", None)  # Read the response body.
        if label == "alarm definitions":  # The definition endpoint returns a list.
            return "" if isinstance(data, list) else "The alarm definitions response is not a list."  # Validate list.
        return (
            ""
            if isinstance(data, Mapping) and isinstance(data.get("results"), list)
            else "The response holds no results list."
        )

    @staticmethod
    def _guard_result(rows: list[dict[str, Any]], pages: int) -> AlertDigestListResult:
        """Return partial rows when the page guard stops the read."""
        logger.warning(
            "The alarm search stopped at page %d. The digest holds the first %d alarms only.", pages, len(rows)
        )
        return AlertDigestListResult(rows, HTTP_OK, complete=False)  # Keep partial rows and mark incomplete.

    @staticmethod
    def _change_result(status: int | None, data: Any) -> tuple[int | None, str]:
        """Return status and an error message for an alarm state change."""
        if isinstance(status, int) and 200 <= status < 300:  # Mist accepted the state change.
            return status, ""  # No error message is needed.
        if status is None:  # No HTTP answer arrived.
            return status, "No HTTP answer arrived. Read the mistapi line in script.log."  # Explain missing status.
        detail = json.dumps(data, sort_keys=True, default=str) if data else ""  # Format the response body safely.
        return status, f"HTTP {status} {detail}".strip()[:ERROR_TEXT_LIMIT]  # Keep the cell short.
