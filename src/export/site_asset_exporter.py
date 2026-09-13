"""SiteAssetExporter -- site-level BLE asset and asset-filter export operations.

Added for specs 666, 667, 668 and 670 (issues #1416, #1417, #1418 and #1419).
Wraps four read-only Mist API operations so operators reach them through the
standard MistHelper menu and DataExporter pipeline (CSV, SQLite, or ArangoDB).

Covered operations:
    - ``getSiteAssetsOfInterest`` (menu 210) -- BLE beacons that match an Asset
      or an AssetFilter.
    - ``getSiteAssetFilter`` (menu 211) -- one asset filter by identifier.
    - ``getSiteAsset`` (menu 212) -- one asset by identifier.

Why:
    These endpoints were absent from the menu, so operators had to write custom
    code to read asset data. This exporter closes that gap and reuses the shared
    site-resolution and persistence scaffolding that the peer site exporters use.

Warning: the ``**mistapi SDK module**`` line in the source specs is wrong for
several of these operations. See issue #1757. The module paths below were
resolved against the installed SDK.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw asset rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for the asset, assetfilter, and stats endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.


class SiteAssetExporter:
    """Site asset and asset-filter exporter.

    Why:
        Provides the only MistHelper entry points for the site asset
        operationIds. Static methods only, with no per-instance state, which
        matches the pattern that ``SiteClientExporter`` established.
    """

    @staticmethod
    def _normalize_payload(response_payload: Any) -> list[dict[str, Any]]:
        """Normalize a get-by-id payload to a list of dict rows.

        Why:
            The get-by-id endpoints return one object, but ``DataExporter``
            expects iterable rows. Wrapping here keeps every caller uniform.

        Args:
            response_payload: The decoded body from the SDK response. May be a
                dict, a list, or None.

        Returns:
            A list of dict rows, which is empty when the payload carries no data.
        """
        if response_payload is None:  # An empty body is a legitimate result, so return no rows.
            return []
        if isinstance(response_payload, list):  # Defensive support for list payloads from wrappers and mocks.
            rows = [row for row in response_payload if isinstance(row, dict)]  # Keep only dict rows.
            logging.debug("Normalized list payload to %d dict rows", len(rows))  # Coercion trace.
            return rows
        if isinstance(response_payload, dict):  # The expected SDK path returns one object as a dict.
            logging.debug("Normalized dict payload to a single-row list")  # Coercion trace.
            return [response_payload]
        logging.warning(  # An unexpected type means the SDK contract changed, so say so instead of failing.
            "Unexpected payload type %s; treating it as an empty result",
            type(response_payload).__name__,
        )
        return []

    @staticmethod
    def _persist(rawdata: list[Any], filename: str, api_function_name: str, label: str) -> None:
        """Flatten and persist rows, or tell the operator when there are none.

        Why:
            An empty response is legitimate, for example a site with no assets.
            We report it plainly so scheduled runs stay quiet in that case.

        Args:
            rawdata: The raw rows returned by the endpoint. May be empty.
            filename: The output filename to write under ``data/``.
            api_function_name: The operationId used to route the primary-key strategy.
            label: A human-readable noun used in the operator messages.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rawdata:  # No rows, so inform the operator and return.
            logging.info("! No %s data found", label)  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Make multiline values CSV-safe.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=api_function_name
        )
        logging.debug("%s persisted %d rows to %s", api_function_name, len(rawdata), filename)  # Post-call count.
        logging.info("! %d %s records exported to %s", len(rawdata), label, filename)  # User notice with count.

    @staticmethod
    def _prompt_identifier(prompt_text: str, context: str) -> str | None:
        """Prompt for one required identifier and reject an empty answer.

        Why:
            The get-by-id operations cannot run without their identifier, and
            ``safe_input`` keeps the prompt safe under SSH and container EOF.

        Args:
            prompt_text: The text shown to the operator.
            context: A tag recorded in the logs to locate the prompt.

        Returns:
            The trimmed identifier, or None when the operator gave no answer.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils keeps the import acyclic.
        logging.info("Prompting the operator for %s", context)  # Action log before the prompt.
        value = str(  # WHY: the lazy module attribute is untyped, so pin the declared str return.
            mh.InputUtils.safe_input(  # safe_input enforces EOF-safe prompting.
                prompt_text,
                allow_empty=False,  # An empty identifier is invalid for the API path.
                context=context,
            )
        ).strip()  # Strip whitespace so stray spaces do not pass validation.
        logging.debug("Completed the %s prompt with value_present=%s", context, bool(value))  # Prompt result trace.
        if not value:  # A blank answer, an EOF, or an interrupt must abort before any API call.
            logging.error("No value provided for %s. Exiting.", context)  # Abort reason.
            logging.info("! No identifier supplied. Exiting.")  # User-facing cancel line.
            return None
        return value

    @staticmethod
    def assets_of_interest() -> None:
        """Export the BLE beacons that match an Asset or an AssetFilter (menu 210).

        Why:
            Interactive menu entry point for ``getSiteAssetsOfInterest``. Site
            resolution is delegated to the shared helper so behavior matches the
            peer site-scoped exports.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site Assets Of Interest:")  # Menu header echoed to the operator.
        logging.info("Starting the getSiteAssetsOfInterest export...")  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("assets of interest")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        try:
            logging.info("Calling getSiteAssetsOfInterest for site_id=%s (%s)", site_id, site_name)  # Pre-call log.
            response = mistapi.api.v1.sites.stats.getSiteAssetsOfInterest(  # SDK call with default filters.
                mh.apisession, site_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            filename = f"SiteAssetsOfInterest_{site_name.replace(' ', '_')}.csv"  # Per-site filename.
            SiteAssetExporter._persist(rawdata, filename, "getSiteAssetsOfInterest", "assets of interest")
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching assets of interest for site %s: %s", site_name, e)  # Failure context.
            logging.info("! Error fetching assets of interest: %s", e)  # ASCII-only user notice.

    @staticmethod
    def asset_filter() -> None:
        """Export one site asset filter by identifier (menu 211).

        Why:
            Interactive menu entry point for ``getSiteAssetFilter``. The endpoint
            needs both a site and an asset-filter identifier.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site Asset Filter Detail:")  # Menu header echoed to the operator.
        logging.info("Starting the getSiteAssetFilter export...")  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("asset filter detail")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        assetfilter_id = SiteAssetExporter._prompt_identifier(  # Ask for the required filter identifier.
            "Enter Asset Filter ID for getSiteAssetFilter: ",
            "site_asset_exporter.getSiteAssetFilter.assetfilter_id",
        )
        if assetfilter_id is None:  # The prompt helper already logged the cancellation.
            return
        try:
            logging.info(  # Pre-call log with full context.
                "Calling getSiteAssetFilter for site_id=%s assetfilter_id=%s", site_id, assetfilter_id
            )
            response = mistapi.api.v1.sites.assetfilters.getSiteAssetFilter(  # SDK get-by-id call.
                mh.apisession, site_id, assetfilter_id
            )
            payload = getattr(response, "data", response)  # Support both object and dict responses.
            rows = SiteAssetExporter._normalize_payload(payload)  # Normalize the single object to rows.
            filename = f"SiteAssetFilter_{site_name.replace(' ', '_')}_{assetfilter_id.replace('-', '_')}.csv"
            SiteAssetExporter._persist(rows, filename, "getSiteAssetFilter", "asset filter")
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching asset filter %s for site %s: %s", assetfilter_id, site_name, e)
            logging.info("! Error fetching asset filter detail: %s", e)  # ASCII-only user notice.

    @staticmethod
    def asset() -> None:
        """Export one site asset by identifier (menu 212).

        Why:
            Interactive menu entry point for ``getSiteAsset``. The endpoint needs
            both a site and an asset identifier.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site Asset Detail:")  # Menu header echoed to the operator.
        logging.info("Starting the getSiteAsset export...")  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("asset detail")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        asset_id = SiteAssetExporter._prompt_identifier(  # Ask for the required asset identifier.
            "Enter Asset ID for getSiteAsset: ",
            "site_asset_exporter.getSiteAsset.asset_id",
        )
        if asset_id is None:  # The prompt helper already logged the cancellation.
            return
        try:
            logging.info("Calling getSiteAsset for site_id=%s asset_id=%s", site_id, asset_id)  # Pre-call log.
            response = mistapi.api.v1.sites.assets.getSiteAsset(mh.apisession, site_id, asset_id)  # SDK get-by-id call.
            payload = getattr(response, "data", response)  # Support both object and dict responses.
            rows = SiteAssetExporter._normalize_payload(payload)  # Normalize the single object to rows.
            filename = f"SiteAsset_{site_name.replace(' ', '_')}_{asset_id.replace('-', '_')}.csv"
            SiteAssetExporter._persist(rows, filename, "getSiteAsset", "asset")
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching asset %s for site %s: %s", asset_id, site_name, e)  # Failure context.
            logging.info("! Error fetching asset detail: %s", e)  # ASCII-only user notice.
