"""Mist API client for menu 270, the Marvis Actions export and bulk resolve.

Why:
    One class holds every Mist API call of this feature. A test replaces one
    object, and the NOC endpoint report names each call that this class makes.

Evidence:
    The Mist UI reads and changes the Marvis Actions through the ``labs``
    endpoints below. The public OpenAPI document does not describe them.
    Research R1 to R6 in ``specs/3299-marvis-actions-bulk-resolve`` holds the
    read-only probes that confirmed each path, each query value, and each body.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions in the annotations of this module.

import json  # WHY: an HTTP error body reaches the results file as short JSON text.
import logging  # WHY: log an action before each API call and a summary after it.
from collections.abc import Mapping  # WHY: type the response payloads without a concrete class.
from dataclasses import dataclass, field  # WHY: one small result object carries the list read outcome.
from typing import Any  # WHY: the mistapi session and its responses carry no type hints.

import mistapi  # WHY: the site list uses the SDK helper and its paging support.

from src.marvis.actions.model import MarvisFieldReader  # WHY: turn a raw site name into trimmed text.

logger = logging.getLogger(__name__)  # WHY: name the logger for this module so a reader filters by source.

LIST_PATH = "/api/v1/labs/orgs/{org_id}/suggestion"  # WHY: the Marvis Actions list that the Mist UI reads.
RESOLVE_PATH = "/api/v1/labs/orgs/{org_id}/suggestions"  # WHY: the status change that the Mist UI sends.
SCHEMA_PATH = "/api/v1/labs/suggestions_schema"  # WHY: the topic names and the recommended actions.
MAX_LIST_PAGES = 100  # WHY: a guard against an API that never returns a short page.
SITE_PAGE_LIMIT = 1000  # WHY: the largest page that the site list accepts.
ERROR_TEXT_LIMIT = 300  # WHY: keep one results cell short enough to read.


@dataclass(slots=True)
class MarvisListResult:
    """The outcome of one full read of the Marvis Actions list.

    Attributes:
        rows: The raw rows, in the order that the API returned them.
        status_code: The HTTP status of the last page that the client read.
        complete: False when the page guard stopped the read early or when the read failed.
        problem: The reason of a failed read. An empty string means that the read worked.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)  # WHY: the raw rows of every page.
    status_code: int | None = None  # WHY: the HTTP status of the last page.
    complete: bool = True  # WHY: False when a part of the list is absent.
    problem: str = ""  # WHY: the reason of a failed read.


class MarvisActionsClient:
    """Read and change the Marvis Actions of one organization.

    Why:
        The list read, the schema read, the site read, and the resolve request
        share one session and one organization. The class keeps both, so each
        call needs only its own values.
    """

    def __init__(self, apisession: Any, org_id: str, page_limit: int) -> None:
        """Keep the session, the organization, and the page size.

        Args:
            apisession: The live mistapi session.
            org_id: The organization that owns the actions.
            page_limit: The number of rows to request on each list page.
        """
        self._apisession = apisession  # WHY: one shared session serves every call.
        self._org_id = org_id  # WHY: every path of this feature names the organization.
        self._page_limit = max(1, int(page_limit))  # WHY: a page size below 1 would never end the read.

    def list_actions(self) -> MarvisListResult:
        """Read every page of the Marvis Actions list.

        Returns:
            The rows. If one page fails, the result holds no rows and names the problem.
        """
        logger.info("Reading the Marvis Actions list for org %s", self._org_id)  # WHY: action log before the read.
        rows: list[dict[str, Any]] = []  # WHY: collect the rows of every page.
        rows_read = 0  # WHY: count every raw item, so the total check matches the API count.
        for page in range(1, MAX_LIST_PAGES + 1):  # WHY: the first page of this endpoint is page 1.
            response = self._read_page(page)  # WHY: read one page.
            problem = self._page_problem(response)  # WHY: one bad page makes the whole list unsafe.
            if problem:  # WHY: a partial list must not reach a file or a resolve.
                return MarvisListResult([], response.status_code, False, problem)  # WHY: no rows on a failure.
            results = response.data["results"]  # WHY: the page problem check proved that this list exists.
            rows.extend(row for row in results if isinstance(row, dict))  # WHY: skip an item that is not a row.
            rows_read += len(results)  # WHY: the API total counts the raw items.
            if self._is_last_page(response.data, len(results), rows_read):  # WHY: stop at the last page.
                logger.debug("Read %d Marvis Action rows on %d pages", len(rows), page)  # WHY: result summary.
                return MarvisListResult(rows, response.status_code)  # WHY: the read is complete.
        return self._guard_result(rows)  # WHY: the page guard stopped the read before the last page.

    def read_schema(self) -> list[dict[str, Any]]:
        """Read the Marvis topic schema.

        Returns:
            The schema entries, or an empty list when the read fails. The built-in names still apply.
        """
        logger.info("Reading the Marvis topic schema")  # WHY: action log before the read.
        response = self._apisession.mist_get(SCHEMA_PATH)  # WHY: the schema holds the recommended actions.
        data = response.data  # WHY: the response body.
        entries = data.get("data") if isinstance(data, Mapping) else None  # WHY: the entries sit under "data".
        if response.status_code != 200 or not isinstance(entries, list):  # WHY: the names are optional.
            logger.warning(  # WHY: the export continues, and the operator learns why a column is empty.
                "The Marvis topic schema read returned HTTP %s. The recommended_action column stays empty.",
                response.status_code,
            )
            return []  # WHY: the built-in catalog still names every known topic.
        logger.debug("The Marvis topic schema holds %d entries", len(entries))  # WHY: result summary.
        return [entry for entry in entries if isinstance(entry, dict)]  # WHY: skip an entry that is not an object.

    def read_site_names(self) -> dict[str, str]:
        """Read the name of every site in the organization.

        Returns:
            The site name for each site identifier, or an empty map when the read fails.
        """
        logger.info("Reading the site names for org %s", self._org_id)  # WHY: action log before the read.
        sites_api = mistapi.api.v1.orgs.sites  # WHY: the SDK module of the organization site endpoints.
        response = sites_api.listOrgSites(self._apisession, self._org_id, limit=SITE_PAGE_LIMIT)  # WHY: page 1.
        if response.status_code != 200:  # WHY: the site names are optional.
            logger.warning(  # WHY: the export continues, and the operator learns why a column is empty.
                "The site list read returned HTTP %s. The site_name column stays empty.", response.status_code
            )
            return {}  # WHY: the rows still carry the site identifier.
        sites = mistapi.get_all(response=response, mist_session=self._apisession)  # WHY: read every site page.
        names = {  # WHY: map each identifier to its name for the row builder.
            MarvisFieldReader.text(site.get("id")): MarvisFieldReader.text(site.get("name"))
            for site in sites
            if isinstance(site, Mapping)
        }
        logger.debug("Read %d site names", len(names))  # WHY: result summary.
        return names  # WHY: the builder adds the name to each row.

    def resolve_action(self, body: dict[str, Any]) -> tuple[int | None, str]:
        """Send one status change for one action.

        Args:
            body: The request body. It names the action through its ``row_key``.

        Returns:
            The HTTP status and an empty string on success, or the HTTP status and the error text.
        """
        response = self._apisession.mist_put(RESOLVE_PATH.format(org_id=self._org_id), body=body)  # WHY: one PUT.
        status = response.status_code  # WHY: mistapi returns an HTTP error as a status, not as an exception.
        logger.debug("The resolve request returned HTTP %s", status)  # WHY: result summary.
        if isinstance(status, int) and 200 <= status < 300:  # WHY: every 2xx status means that Mist accepted it.
            return status, ""  # WHY: no error text on success.
        return status, self._error_text(status, response.data)  # WHY: keep the reason for the results file.

    def _read_page(self, page: int) -> Any:
        """Read one page of the Marvis Actions list and return the mistapi response."""
        query = {  # WHY: the same query values that the Mist UI sends.
            "query": "get_suggestion",  # WHY: ask for the action rows, not a count or a time series.
            "resolve_wcid": "true",  # WHY: return the names of the impacted wireless clients.
            "limit": str(self._page_limit),  # WHY: the number of rows on each page.
            "page": str(page),  # WHY: the page number, starting at 1.
        }
        logger.info("Reading Marvis Actions page %d", page)  # WHY: action log before the read.
        response = self._apisession.mist_get(LIST_PATH.format(org_id=self._org_id), query=query)  # WHY: one GET.
        logger.debug("Marvis Actions page %d returned HTTP %s", page, response.status_code)  # WHY: result summary.
        return response  # WHY: the caller checks the status and the body.

    @staticmethod
    def _page_problem(response: Any) -> str:
        """Return the reason that a page is not usable, or an empty string."""
        if response.status_code is None:  # WHY: mistapi returns no status when no HTTP answer arrived.
            return "No HTTP answer arrived. Read the mistapi line in script.log."  # WHY: point to the cause.
        if response.status_code != 200:  # WHY: any other status means that the page holds no rows.
            return f"The API returned HTTP {response.status_code}."  # WHY: name the status.
        data = response.data  # WHY: the response body.
        if not isinstance(data, Mapping) or not isinstance(data.get("results"), list):  # WHY: a changed shape.
            return "The response holds no results list."  # WHY: name the shape problem.
        return ""  # WHY: the page is usable.

    def _is_last_page(self, data: Mapping[str, Any], results_count: int, rows_read: int) -> bool:
        """Return True when the page just read is the last page of the list."""
        if results_count == 0:  # WHY: an empty page ends the list.
            return True  # WHY: no more rows exist.
        total = MarvisFieldReader.integer(data.get("total"))  # WHY: the API states the full row count on each page.
        if total is not None:  # WHY: the stated total is the most exact stop rule.
            return rows_read >= total  # WHY: the next page would be empty.
        page_size = MarvisFieldReader.integer(data.get("limit")) or self._page_limit  # WHY: the API can cap it.
        return results_count < page_size  # WHY: without a total, a short page is the last page.

    @staticmethod
    def _guard_result(rows: list[dict[str, Any]]) -> MarvisListResult:
        """Warn the operator, and return the rows that the read collected before the page guard."""
        logger.warning(  # WHY: the operator must know that the list can be incomplete.
            "The Marvis Actions list reached the guard of %d pages. The list holds the first %d rows only.",
            MAX_LIST_PAGES,
            len(rows),
        )
        return MarvisListResult(rows, 200, complete=False)  # WHY: keep the rows, and mark the read incomplete.

    @staticmethod
    def _error_text(status: int | None, data: Any) -> str:
        """Return the short error text of a failed resolve request."""
        if status is None:  # WHY: no HTTP answer arrived.
            return "No HTTP answer arrived. Read the mistapi line in script.log."  # WHY: point to the cause.
        detail = json.dumps(data, sort_keys=True, default=str) if data else ""  # WHY: the error body of Mist.
        return f"HTTP {status} {detail}".strip()[:ERROR_TEXT_LIMIT]  # WHY: keep the results cell short.
