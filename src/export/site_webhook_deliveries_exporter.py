"""SiteWebhookDeliveriesExporter -- site+webhook delivery audit search export.

Added for spec 902 / issue #1410.  Wraps the Mist API
``searchSiteWebhooksDeliveries`` (``GET
/api/v1/sites/{site_id}/webhooks/{webhook_id}/events/search``) so operators
can inspect per-webhook delivery attempts (success/failure, status codes,
error messages) through the standard MistHelper menu + DataExporter pipeline
(CSV/SQLite/ArangoDB).

Why:
    Webhook delivery telemetry is essential for debugging misbehaving
    integrations, but the endpoint was absent from MistHelper's menu.  This
    exporter closes that gap while reusing the shared site-resolution +
    persistence scaffolding established by ``SiteWanUsageExporter`` (menu 198)
    and ``SiteDeviceExporter._resolve_site_for_stats()``.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw webhook rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for listSiteWebhooks + searchSiteWebhooksDeliveries.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten/escape helpers; keeps CSV output consistent with peers.
from src.utils.input_utils import InputUtils  # WHY: safe_input honors EOF/Ctrl-C per Constitution.


class SiteWebhookDeliveriesExporter:
    """Site Webhook Deliveries search exporter.

    Why:
        Sole MistHelper entry point for the ``searchSiteWebhooksDeliveries``
        operationId.  Static methods only -- no per-instance state, matching
        the pattern used by ``SiteWanUsageExporter`` / ``SiteClientExporter``.
    """

    @staticmethod
    def _select_webhook_id(site_id: str) -> tuple[str, str] | None:
        """Prompt the operator to pick a webhook for ``site_id``.

        Why:
            The delivery-search endpoint takes both ``site_id`` and
            ``webhook_id``.  Listing configured webhooks up-front lets the
            operator pick by 1-based index rather than pasting a UUID.

        Args:
            site_id: Resolved site UUID whose webhooks will be listed.

        Returns:
            ``(webhook_id, webhook_name)`` when a valid selection is made,
            otherwise ``None`` (no webhooks configured or invalid input).
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        logging.info(  # INFO trace before the listing SDK call (pre-call per Action Logging).
            "Listing webhooks for site_id=%s for delivery-search selection", site_id
        )
        response = mistapi.api.v1.sites.webhooks.listSiteWebhooks(  # SDK call -- enumerate webhooks.
            mh.apisession, site_id
        )
        webhooks = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
        if not webhooks:  # Site has no configured webhooks -- nothing to search deliveries for.
            print("! No webhooks configured for this site")  # ASCII-only user notice.
            logging.warning("No webhooks configured for site_id=%s", site_id)  # Warn for logs.
            return None
        for idx, wh in enumerate(webhooks, start=1):  # Enumerate with 1-based index for humans.
            print(f"  {idx}. {wh.get('name', '(unnamed)')}  [{wh.get('id', '?')}]")  # Show each webhook.
        raw = InputUtils.safe_input(  # WHY: safe_input handles EOF/Ctrl-C gracefully in SSH/CI.
            "Select webhook number: ", context="site_webhook_deliveries_selection"
        )
        return SiteWebhookDeliveriesExporter._resolve_webhook_choice(raw, webhooks)  # Validate + resolve.

    @staticmethod
    def _resolve_webhook_choice(raw: str, webhooks: list[dict[str, Any]]) -> tuple[str, str] | None:
        """Validate the raw selection string and return ``(id, name)`` or ``None``.

        Why:
            Extracted from ``_select_webhook_id`` to keep the caller under
            the 25-line 5-Item Rule ceiling; also makes the validation logic
            unit-testable in isolation.

        Args:
            raw: Trimmed user input from ``safe_input``.
            webhooks: List of webhook dicts returned by ``listSiteWebhooks``.

        Returns:
            ``(webhook_id, webhook_name)`` when the input parses to a valid
            1-based index, else ``None``.
        """
        if not raw.isdigit():  # Non-numeric input -- reject.
            print("! Invalid selection (not a number)")  # ASCII-only user notice.
            return None
        idx = int(raw)  # Parse the operator's 1-based choice.
        if not 1 <= idx <= len(webhooks):  # Out-of-range index.
            print(f"! Selection out of range (1..{len(webhooks)})")  # ASCII-only user notice.
            return None
        chosen = webhooks[idx - 1]  # Convert to 0-based access.
        return chosen.get("id", ""), chosen.get("name", chosen.get("id", "webhook"))  # Return id+name.

    @staticmethod
    def _persist_site_webhook_deliveries(rawdata: list[Any], site_name: str, webhook_name: str) -> None:
        """Flatten + persist delivery rows to a per-site+webhook file (or notify empty).

        Why:
            Empty responses are legitimate (a webhook that has never fired in
            the search window); we surface a friendly message rather than
            failing so scheduled runs stay quiet in that case.

        Args:
            rawdata: Raw list returned by ``mistapi.get_all`` for the delivery
                search response.  May be empty.
            site_name: Human-readable site name used in the output filename.
            webhook_name: Human-readable webhook name used in the output filename.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        if not rawdata:  # No delivery rows in the query window -- inform the operator.
            print("! No webhook delivery data found")  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe multiline escape.
        safe_site = site_name.replace(" ", "_")  # Filename-safe site token.
        safe_webhook = webhook_name.replace(" ", "_")  # Filename-safe webhook token.
        filename = f"SiteWebhookDeliveries_{safe_site}_{safe_webhook}.csv"  # Per-site+webhook filename.
        mh.DataExporter.write_with_format_selection(  # Persist through CSV/SQLite/Arango backend selector.
            sanitized_data, filename, api_function_name="searchSiteWebhooksDeliveries"
        )
        logging.debug(  # DEBUG-level count trace per Action Logging principle (post-call).
            "searchSiteWebhooksDeliveries persisted %d rows to %s", len(rawdata), filename
        )
        print(f"! {len(rawdata)} webhook delivery records exported to {filename}")  # User notice.

    @staticmethod
    def deliveries() -> None:
        """Search webhook deliveries for a site+webhook and export the results.

        Why:
            Interactive menu entry point (menu 199).  Delegates site
            resolution to the shared helper so behavior stays consistent with
            peer site-scoped exports, then prompts the operator to pick one
            of the site's configured webhooks.  Errors are logged and
            surfaced to the user rather than crashing the menu loop.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + shared helpers.
        print("Site Webhook Deliveries Search:")  # Menu header echoed to operator.
        logging.info(  # INFO trace before the API call per Action Logging principle (pre-call).
            "Starting searchSiteWebhooksDeliveries export..."
        )
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(  # Prompt + org/site resolution (shared).
            "webhook deliveries search"
        )
        if resolved is None:  # Operator declined selection or org unresolved -- helper already logged.
            return
        site_id, site_name = resolved  # Unpack resolved identifiers for the API call.
        webhook_choice = SiteWebhookDeliveriesExporter._select_webhook_id(site_id)  # Pick a webhook.
        if webhook_choice is None:  # No webhooks or invalid pick -- abort quietly.
            return
        webhook_id, webhook_name = webhook_choice  # Unpack selected webhook identifiers.
        try:
            logging.info(  # INFO trace immediately before the SDK call (with full context).
                "Calling searchSiteWebhooksDeliveries site_id=%s webhook_id=%s (%s)",
                site_id,
                webhook_id,
                webhook_name,
            )
            response = mistapi.api.v1.sites.webhooks.searchSiteWebhooksDeliveries(  # SDK call.
                mh.apisession, site_id, webhook_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            SiteWebhookDeliveriesExporter._persist_site_webhook_deliveries(  # Persist or notify empty.
                rawdata, site_name, webhook_name
            )
        except Exception as e:  # noqa: BLE001 -- surface any SDK/network error rather than crashing.
            logging.error(  # ERROR trace with full context for post-mortem correlation.
                "Error fetching webhook deliveries site=%s webhook=%s: %s",
                site_name,
                webhook_name,
                e,
            )
            print(f"! Error fetching webhook delivery data: {e}")  # ASCII-only user notice.
