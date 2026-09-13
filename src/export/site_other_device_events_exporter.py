"""Export site other-device events from the Mist API.

This module provides the menu entry for issue #1402.
"""

from __future__ import annotations  # WHY: keep type annotations compatible with the project target.

import importlib  # WHY: load MistHelper lazily and avoid an import cycle.
import logging  # WHY: record the export lifecycle for operators.
from typing import Any  # WHY: Mist event rows are untyped API dictionaries.

import mistapi  # WHY: call the verified site other-device event SDK operation.

from src.data.data_processing_utils import (  # WHY: reuse the shared export normalization pipeline.
    DataProcessingUtils,
)


class SiteOtherDeviceEventsExporter:
    """Export site other-device event search results."""

    @staticmethod
    def _persist_events(rawdata: list[Any], site_name: str) -> None:
        """Flatten and persist event rows for one site."""
        mh = importlib.import_module("MistHelper")  # WHY: obtain the shared DataExporter after module loading.
        if not rawdata:  # WHY: an empty search is valid and needs no output file.
            logging.info(
                "! No other-device event data found for this site"
            )  # WHY: tell the operator why no file exists.
            return  # WHY: avoid writing an empty export.
        logging.info("Flattening other-device event data")  # WHY: trace the transformation before it starts.
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # WHY: make nested API fields tabular.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # WHY: keep multiline values CSV-safe.
        logging.debug(
            "Prepared %d other-device event rows", len(sanitized_data)
        )  # WHY: report the transformed row count.
        filename = (
            f"SiteOtherDeviceEvents_{site_name.replace(' ', '_')}.csv"  # WHY: identify the site in the output name.
        )
        logging.info("Writing other-device events to %s", filename)  # WHY: trace the backend write.
        mh.DataExporter.write_with_format_selection(  # WHY: support every configured output backend.
            sanitized_data, filename, api_function_name="searchSiteOtherDeviceEvents"
        )
        logging.debug(
            "Persisted %d other-device event rows to %s", len(rawdata), filename
        )  # WHY: confirm the write result.
        logging.info(
            "! %d other-device event records exported to %s", len(rawdata), filename
        )  # WHY: show completion to the operator.

    @staticmethod
    def other_device_events() -> None:
        """Search and export other-device events for a selected site."""
        mh = importlib.import_module("MistHelper")  # WHY: obtain the session and shared site resolver lazily.
        logging.info("Site Other Device Events Search:")  # WHY: identify the selected menu action.
        logging.info("Starting searchSiteOtherDeviceEvents export")  # WHY: trace the operation before site selection.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(
            "other-device events search"
        )  # WHY: use the shared safe prompt.
        if resolved is None:  # WHY: stop when the operator does not select a site.
            return  # WHY: preserve the menu loop after a cancelled selection.
        site_id, site_name = resolved  # WHY: pass the resolved identifiers to the SDK and output path.
        try:  # WHY: keep SDK failures inside the menu operation.
            logging.info(
                "Calling searchSiteOtherDeviceEvents for site_id=%s (%s)", site_id, site_name
            )  # WHY: trace the API call.
            response = (
                mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents(  # WHY: call the verified SDK operation.
                    mh.apisession, site_id
                )
            )
            rawdata = mistapi.get_all(
                response=response, mist_session=mh.apisession
            )  # WHY: retrieve every paged event row.
            logging.debug("Received %d other-device event rows", len(rawdata))  # WHY: report the API result count.
            SiteOtherDeviceEventsExporter._persist_events(
                rawdata, site_name
            )  # WHY: route rows through the shared writer.
        except Exception as error:  # WHY: surface network and SDK failures without a traceback.
            logging.error(
                "Error fetching other-device events for site %s: %s", site_name, error
            )  # WHY: preserve site context.
            logging.info(
                "! Error fetching other-device event data: %s", error
            )  # WHY: give the operator an actionable message.
