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
    def _page_records(payload: Any) -> list[Any]:
        """Require a record list so malformed pages cannot prove completeness."""
        if isinstance(payload, dict):  # WHY: search responses wrap event rows in results.
            payload = payload.get("results")  # WHY: missing results cannot prove a successful empty search.
        if not isinstance(payload, list):  # WHY: malformed payloads must not enter the aggregate.
            raise ValueError("Other-device event page does not contain a record list")  # WHY: reject unsafe rows.
        return payload  # WHY: preserve the SDK row schema without altering records.

    @staticmethod
    def _collect_events(response: Any) -> list[Any] | None:
        """Collect every successful page or reject the entire incomplete result."""
        records: list[Any] = []  # WHY: keep accepted rows private until every page succeeds.
        while True:  # WHY: validate the first response and every promised subsequent response.
            status = getattr(response, "status_code", None)  # WHY: the SDK retains HTTP failures without raising.
            status = (
                status if isinstance(status, int) and not isinstance(status, bool) else None
            )  # WHY: booleans and private text cannot represent HTTP status values.
            if status is None or not 200 <= status < 300:  # WHY: only a successful HTTP status proves safety.
                logger.error(
                    "Other-device event page failed: HTTP %s", status if status is not None else "unavailable"
                )  # WHY: report safe status metadata without a response body or URL.
                return None  # WHY: discard all earlier rows rather than exporting incomplete data.
            records.extend(
                SiteOtherDeviceEventsExporter._page_records(response.data)
            )  # WHY: accept only a successful page with a valid row list.
            logger.debug("Collected %d other-device event rows", len(records))  # WHY: record each accepted page.
            if not response.next:  # WHY: the SDK marks a complete result with no next link.
                return records  # WHY: only complete rows can reach the writer.
            logger.info("Fetching the next other-device event page")  # WHY: trace each external page request.
            response = mistapi.get_next(
                mist_session=SourceDependencyResolver.apisession, response=response
            )  # WHY: preserve SDK authentication and URL handling without hiding page statuses.

    @staticmethod
    def _fetch_events(site_id: str) -> list[Any] | None:
        """Keep SDK and malformed-page failures inside the sanitized menu boundary."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        try:  # WHY: keep SDK failures inside the menu operation.
            logger.info("Calling searchSiteOtherDeviceEvents for site_id=%s", site_id)  # WHY: trace the API call.
            response = mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents(
                mh.apisession, site_id
            )  # WHY: preserve the existing endpoint and session contract.
            rawdata = SiteOtherDeviceEventsExporter._collect_events(response)  # WHY: validate all page statuses.
        except Exception:  # WHY: SDK calls and malformed remote pages have no shared exception type.
            logger.error(
                "Error fetching other-device events for the selected site"
            )  # WHY: report the request failure without private exception text.
            rawdata = None  # WHY: an exception cannot produce a complete export.
        if rawdata is None:  # WHY: HTTP failures and external exceptions use the same menu fallback.
            logger.info(
                "! Error fetching other-device event data. Please try again."
            )  # WHY: preserve the menu fallback without exposing response content.
        return rawdata  # WHY: preserve the difference between an empty success and a failed request.

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
        rawdata = SiteOtherDeviceEventsExporter._fetch_events(site_id)  # WHY: isolate remote failures from persistence.
        if rawdata is None:  # WHY: failed pages must not reach transformations or storage.
            return  # WHY: do not persist any rows from an incomplete request.
        logger.debug("Received %d other-device event rows", len(rawdata))  # WHY: report the API result count.
        SiteOtherDeviceEventsExporter._persist_events(
            rawdata, site_name
        )  # WHY: let local transformation and writer defects reach the caller.
