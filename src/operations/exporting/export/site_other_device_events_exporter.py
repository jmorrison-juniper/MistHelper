"""Export site other-device events from the Mist API.

This module provides the menu entry for issue #1402.
"""

from __future__ import annotations  # WHY: keep type annotations compatible with the project target.

import logging  # WHY: record the export lifecycle for operators.
from typing import Any  # WHY: Mist event rows are untyped API dictionaries.

import mistapi  # WHY: call the verified site other-device event SDK operation.

from src.foundation.models.data.data_processing_utils import (  # WHY: reuse the shared export normalization pipeline.
    DataProcessingUtils,
)
from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Record export messages under this module.


class SiteOtherDeviceEventsExporter:
    """Export site other-device event search results."""

    @staticmethod
    def _persist_events(rawdata: list[Any], site_name: str) -> None:
        """Flatten and persist event rows for one site."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        if not rawdata:  # WHY: an empty search is valid and needs no output file.
            logger.info(
                "! No other-device event data found for this site"
            )  # WHY: tell the operator why no file exists.
            return  # WHY: avoid writing an empty export.
        logger.info("Flattening other-device event data")  # WHY: trace the transformation before it starts.
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # WHY: make nested API fields tabular.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # WHY: keep multiline values CSV-safe.
        logger.debug(
            "Prepared %d other-device event rows", len(sanitized_data)
        )  # WHY: report the transformed row count.
        filename = (
            f"SiteOtherDeviceEvents_{site_name.replace(' ', '_')}.csv"  # WHY: identify the site in the output name.
        )
        logger.info("Writing other-device events to %s", filename)  # WHY: trace the backend write.
        mh.DataExporter.write_with_format_selection(  # WHY: support every configured output backend.
            sanitized_data, filename, api_function_name="searchSiteOtherDeviceEvents"
        )
        logger.debug(
            "Persisted %d other-device event rows to %s", len(rawdata), filename
        )  # WHY: confirm the write result.
        logger.info(
            "! %d other-device event records exported to %s", len(rawdata), filename
        )  # WHY: show completion to the operator.

    @staticmethod
    def _page_records(response: Any, known_total: int) -> tuple[list[Any], int] | None:
        """Validate dictionary rows and present pagination metadata of a successful page."""
        payload = response.data  # WHY: the caller already proved a successful HTTP status.
        envelope = payload if isinstance(payload, dict) else {}  # WHY: only search envelopes carry a JSON total.
        rows = envelope.get("results", payload)  # WHY: accept list pages and documented results envelopes.
        headers = response.headers or {}  # WHY: the SDK can omit the header mapping.
        names = ("X-Page-Total", "X-Page-Limit", "X-Page-Page")  # WHY: the SDK derives list cursors from these.
        present = any(map(headers.__contains__, names))  # WHY: an empty header value is present, not absent.
        counts = [
            str(envelope.get("total", known_total)),
            *[*map(str, map(headers.get, names))] * present,
        ]  # WHY: an absent total keeps the known total, and missing present headers fail as text.
        if not (
            isinstance(rows, list)
            and all(isinstance(row, dict) for row in rows)
            and "".join(counts).isascii()
            and all(map(str.isdigit, counts))
            and max(map(len, counts)) <= 18
        ):  # WHY: malformed rows, metadata, or counts above 18 digits cannot prove a complete page.
            logger.error(
                "Other-device event page does not contain valid records or pagination metadata"
            )  # WHY: omit private payload and header values.
            return None  # WHY: handle known malformed data without catching unexpected local defects.
        return rows, int(counts[0])  # WHY: the documented JSON total counts rows across all pages.

    @staticmethod
    def _collect_events(response: Any) -> list[Any] | None:
        """Collect every successful page or reject the entire incomplete result."""
        records: list[Any] = []  # WHY: keep accepted rows private until every page succeeds.
        seen: set[str] = set()  # WHY: repeated cursors cannot prove progress or completion.
        total = 0  # WHY: no advertised total imposes no count requirement.
        while response is not None:  # WHY: failed external calls cannot contribute records.
            page = SiteOtherDeviceEventsExporter._page_records(response, total)  # WHY: admit only valid pages.
            if page is None:  # WHY: distinguish a failed response from a valid empty record list.
                return None  # WHY: discard all earlier rows rather than exporting incomplete data.
            records.extend(page[0])  # WHY: retain validated rows until pagination proves completeness.
            total = page[1]  # WHY: keep the most recent present total across pages without one.
            logger.debug("Collected %d other-device event rows", len(records))  # WHY: record each accepted page.
            cursor = response.next  # WHY: keep the next link private while validating progress.
            if cursor is None or cursor == "":  # WHY: preserve both SDK terminal cursor values.
                if len(records) < page[1]:  # WHY: the documented total counts matching rows across all pages.
                    logger.error("Other-device event pages ended before the advertised total")  # WHY: omit counts.
                    return None  # WHY: a terminal cursor cannot hide missing advertised rows.
                return records  # WHY: only complete rows can reach the writer.
            if (
                not isinstance(cursor, str)
                or cursor in seen
                or not (cursor[:8] == "/api/v1/" and cursor.replace(" ", "\n").isprintable())
            ):  # WHY: the SDK appends the cursor to the cloud host, so only a cloud API path keeps that host.
                logger.error(
                    "Other-device event page cursor is invalid, unsafe, or repeated"
                )  # WHY: omit private cursor text.
                return None  # WHY: handle known invalid remote cursors explicitly.
            seen.add(cursor)  # WHY: stop before issuing another request to a previously requested cursor.
            response = SiteOtherDeviceEventsExporter._fetch_events(response=response)  # WHY: isolate the SDK call only.
        return None  # WHY: discard earlier rows after any failed external call.

    @staticmethod
    def _fetch_events(site_id: str | None = None, response: Any = None) -> Any:
        """Contain exceptions from one SDK call without catching local collection defects."""
        session = SourceDependencyResolver.apisession  # WHY: resolve dependencies outside the external-call catch.
        logger.info("Requesting an other-device event page")  # WHY: trace the external request without its cursor.
        try:  # WHY: the installed SDK has no reliable common exception taxonomy.
            result = (
                mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents(session, site_id)
                if site_id is not None
                else mistapi.get_next(mist_session=session, response=response)
            )  # WHY: catch only the actual endpoint or next-page call.
        except Exception:  # WHY: retain the menu fallback for demonstrated external-call exceptions.
            logger.error(
                "Error fetching other-device events for the selected site"
            )  # WHY: report the request failure without private exception text.
            return None  # WHY: an external exception cannot produce a complete page.
        logger.debug("Other-device event page request completed")  # WHY: confirm the external call returned.
        status = getattr(result, "status_code", None)  # WHY: the SDK retains HTTP failures without raising.
        status = (
            status if isinstance(status, int) and not isinstance(status, bool) else None
        )  # WHY: missing responses, booleans, and private text cannot represent HTTP status values.
        if status is None or not 200 <= status < 300:  # WHY: only a successful HTTP status proves safety.
            logger.error(
                "Other-device event page failed: HTTP %s", status if status is not None else "unavailable"
            )  # WHY: report safe status metadata without a response body or URL.
            return None  # WHY: no failed page can contribute rows to an export.
        return result  # WHY: let local validation inspect the real SDK response outside this catch.

    @staticmethod
    def other_device_events() -> None:
        """Search and export other-device events for a selected site."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Site Other Device Events Search:")  # WHY: identify the selected menu action.
        logger.info("Starting searchSiteOtherDeviceEvents export")  # WHY: trace the operation before site selection.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(
            "other-device events search"
        )  # WHY: use the shared safe prompt.
        if resolved is None:  # WHY: stop when the operator does not select a site.
            return  # WHY: preserve the menu loop after a canceled selection.
        site_id, site_name = resolved  # WHY: preserve selected identifiers and the output filename.
        response = SiteOtherDeviceEventsExporter._fetch_events(site_id)  # WHY: contain only the external SDK call.
        rawdata = SiteOtherDeviceEventsExporter._collect_events(
            response
        )  # WHY: let unexpected local defects propagate.
        if rawdata is None:  # WHY: failed pages must not reach transformations or storage.
            logger.info(
                "! Error fetching other-device event data. Please try again."
            )  # WHY: preserve sanitized menu feedback for known remote failures.
            return  # WHY: do not persist any rows from an incomplete request.
        logger.debug("Received %d other-device event rows", len(rawdata))  # WHY: report the API result count.
        SiteOtherDeviceEventsExporter._persist_events(
            rawdata, site_name
        )  # WHY: let local transformation and writer defects reach the caller.
