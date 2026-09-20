"""SiteClientExporter -- site-level client/beacon/wifi export operations.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 14).
Handles site-level client data, WiFi clients, and beacon exports.  All methods
are static -- no state is kept on the class.  Callers continue to reach it
through the ``MistHelper.SiteClientExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import logging  # WHY: structured trace for export lifecycle events.
import time  # WHY: adaptive retry backoff sleep for rate-limited endpoint calls.
from typing import Any  # WHY: raw client rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for listSiteWirelessClientsStats + beacons endpoints.

from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)
from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.export.site_export_utils import SiteExportUtils  # WHY: Pattern 1 inline construction for beacons export.
from src.export.wan_client_events_exporter import (
    WanClientEventsExporter,
)  # WHY: spec 899 / issue #1407 -- delegate WAN client event search to dedicated exporter.
from src.export.wifi_clients_exporter import WifiClientsExporter  # Extracted WiFi export orchestrator.
from src.utils.tqdm_wrapper import (
    tqdm,
)  # WHY: 1015 T-14 -- import directly from canonical wrapper (eliminates mh.tqdm).

logger = logging.getLogger(__name__)  # Use a module logger for non-exception export messages.

_GET_SITE_BEACON_API_FUNCTION_NAME = "getSiteBeacon"  # WHY: operation id for PK routing.
_GET_SITE_BEACON_FILENAME_PREFIX = "SiteBeacon"  # WHY: deterministic prefix keeps per-request artifacts discoverable.
_GET_SITE_BEACON_FALLBACK_RETRIES = 2  # WHY: bounded fallback retry count when runtime retry config is unavailable.


class SiteClientExporter:
    """Site Client Data Exporter.

    Handles site-level client data, WiFi clients, and beacon exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def _persist_site_clients(rawdata: list[Any], site_name: str) -> None:
        """Flatten + persist site-clients rows to a per-site CSV (or tell the user when empty)."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        if not rawdata:  # No clients -- tell the user and return.
            # WHY: user notice.
            logger.info("! No client data found for this site")
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe.
        filename = f"SiteClients_{site_name.replace(' ', '_')}.csv"  # Per-site CSV name.
        mh.DataExporter.write_with_format_selection(
            sanitized_data, filename, api_function_name="listSiteWirelessClientsStats"
        )  # Persist.
        # WHY: user notice with count.
        logger.info("! %d client records exported to %s", len(rawdata), filename)

    @staticmethod
    def clients() -> None:
        """Export client data for a site to SiteClients.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Site Client Statistics:")  # WHY: header.
        logger.info("Starting export of site client statistics...")  # Trace start.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(  # Prompt + org/site resolution (shared).
            "client statistics"
        )
        if resolved is None:  # Abort signaled by resolver.
            return
        site_id, site_name = resolved  # Unpack resolved identifiers.
        try:
            response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(mh.apisession, site_id, limit=1000)
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            SiteClientExporter._persist_site_clients(rawdata, site_name)  # Persist or tell user empty.
        except Exception as e:  # Fetch failed.
            logging.error("Error fetching client stats for site %s: %s", site_name, e)  # Log the error.
            # WHY: tell the user.
            logging.info("! Error fetching client data: %s", e)

    @staticmethod
    def client_insights() -> None:
        """Delegated site client insights entrypoint preserved for compatibility."""
        # WHY: local import keeps the serial_cc service optional at module-load time.
        from src.refactors.serial_cc.site_client_insights import SiteClientInsightsService

        SiteClientInsightsService.execute()  # Run the insights export.

    @staticmethod
    def _normalize_client_mac_or_none(client_mac: str) -> str | None:
        """Validate and normalize client MAC for site insights endpoints."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        if not client_mac:  # Empty input.
            return None
        if not mh.PacketCaptureManager.validate_mac_address(client_mac):  # Invalid MAC.
            return None
        return mh.PacketCaptureManager.normalize_mac_address(client_mac)  # Normalized MAC.

    @staticmethod
    def wifi_clients(site_id: str | None = None) -> None:
        """Compatibility facade that delegates WiFi client export to extracted exporter."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info(
            "Delegating wifi_clients to WifiClientsExporter"
        )  # Log before constructing extracted exporter dependencies.
        exporter = WifiClientsExporter(  # Preserve existing utility wiring to avoid behavior drift.
            cache_utils=mh.CacheUtils,
            org_site_exporter=mh.OrgSiteExporter,
            prompt_utils=mh.PromptUtils,
            file_path_utils=mh.FilePathUtils,
            data_processing_utils=DataProcessingUtils,
            data_exporter=mh.DataExporter,
            mistapi_module=mistapi,
            apisession=mh.apisession,
        )
        logger.debug("Initialized WifiClientsExporter for site_id=%s", site_id)  # Log exporter construction completion.
        exporter.execute(site_id=site_id)  # Delegate export execution while preserving facade signature.
        logger.debug("Completed delegated wifi_clients export workflow")  # Log delegated exporter completion.

    @staticmethod
    def wan_client_events(site_id: str | None = None) -> None:
        """Facade delegating WAN client event search to :class:`WanClientEventsExporter`.

        Why:
            Spec 899 / issue #1407 registers a new menu item that surfaces
            ``mistapi.api.v1.sites.wan_clients.events.search.searchSiteWanClientEvents``.
            Keeping the delegation shape identical to :meth:`wifi_clients`
            preserves the SiteClientExporter facade pattern and avoids
            leaking dataclass wiring into ``MistHelper.py``'s menu dict.

        Args:
            site_id: Optional preselected site UUID; ``None`` prompts the
                operator for a site via the injected ``PromptUtils``.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info(
            "Delegating wan_client_events to WanClientEventsExporter"
        )  # WHY: trace facade dispatch for the WAN client event exporter.
        exporter = WanClientEventsExporter(  # WHY: build orchestrator with the same injected deps used by wifi_clients.
            cache_utils=mh.CacheUtils,  # WHY: reuse cached site-name resolver so we skip a redundant listSites call.
            org_site_exporter=mh.OrgSiteExporter,  # WHY: shared site-list emitter feeds the CSV cache fallback lookup.
            prompt_utils=mh.PromptUtils,  # WHY: interactive site selection mirrors sibling site exporters.
            file_path_utils=mh.FilePathUtils,  # WHY: shared SiteList.csv discovery keeps behavior consistent.
            data_processing_utils=DataProcessingUtils,  # WHY: canonical flatten/escape helper for CSV safety.
            data_exporter=mh.DataExporter,  # WHY: multi-backend writer via write_with_format_selection.
            mistapi_module=mistapi,  # WHY: SDK module hosting the wan_clients.events.search endpoint + get_all pager.
            apisession=mh.apisession,  # WHY: authenticated mistapi session shared across all menu actions.
        )
        logger.debug(
            "Initialized WanClientEventsExporter for site_id=%s", site_id
        )  # WHY: capture construction for diagnostics.
        exporter.execute(site_id=site_id)  # WHY: run the fetch + persist pipeline defined by the extracted exporter.
        logger.debug(
            "Completed delegated wan_client_events export workflow"
        )  # WHY: mark facade completion for log timeline correlation.

    @staticmethod
    def beacons() -> None:
        """Export beacons for a site to SiteBeacons.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        SiteExportUtils(
            apisession=mh.apisession,
            PromptUtils=mh.PromptUtils,
            ConfigUtils=mh.ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=mh.DataExporter,
            TimeUtils=mh.TimeUtils,
            EnhancedSSHRunner=mh.EnhancedSSHRunner,
            InsightMetricsUtils=mh.InsightMetricsUtils,
            PacketCaptureManager=mh.PacketCaptureManager,
            APICoreFetchUtils=mh.APICoreFetchUtils,
            check_fn=mh.IsDebugMode.check,
            PrettyTable=mh.PrettyTable,
            tqdm=tqdm,  # 1015 T-14: canonical import from src.utils.tqdm_wrapper (no mh.* reach-back).
            mistapi=mh.mistapi,
        )._export_data(  # Shared export scaffolding handles prompting + CSV write.
            api_call=mistapi.api.v1.sites.beacons.listSiteBeacons, data_type="beacons", sort_key="name"
        )

    @staticmethod
    def _prompt_site_beacon_identifiers() -> tuple[str, str] | None:
        """Prompt for site/beacon IDs through safe_input and reject empty responses."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Prompting operator for site_id required by getSiteBeacon")  # WHY: action log before first prompt.
        site_id = mh.InputUtils.safe_input(  # WHY: safe_input enforces EOF/interrupt-safe prompting semantics.
            "Enter Site ID for getSiteBeacon: ",  # WHY: explicit site-id prompt.
            allow_empty=False,  # WHY: empty identifiers are invalid for the API path contract.
            context="site_client_exporter.getSiteBeacon.site_id",  # WHY: prompt context tag.
        ).strip()  # WHY: strip whitespace so accidental spaces do not bypass empty-input validation.
        logger.debug(
            "Completed site_id prompt for getSiteBeacon with value_present=%s",
            bool(site_id),
        )  # WHY: prompt result trace.
        if not site_id:  # WHY: blank/EOF/interrupt should abort cleanly before any API call.
            logger.error("No site_id provided for getSiteBeacon. Exiting.")  # WHY: abort reason.
            logger.info("! No site selected. Exiting.")  # WHY: user-facing cancel line.
            return None  # WHY: signal caller to terminate flow without side effects.
        logger.info("Prompting operator for beacon_id required by getSiteBeacon")  # WHY: pre-prompt log.
        beacon_id = mh.InputUtils.safe_input(  # WHY: safe_input keeps beacon prompt EOF-safe in SSH/container sessions.
            "Enter Beacon ID for getSiteBeacon: ",  # WHY: explicit beacon-id prompt.
            allow_empty=False,  # WHY: empty beacon identifiers are invalid for the endpoint contract.
            context="site_client_exporter.getSiteBeacon.beacon_id",  # WHY: prompt context tag.
        ).strip()  # WHY: trim accidental whitespace before validation and filename generation.
        logger.debug(
            "Completed beacon_id prompt for getSiteBeacon with value_present=%s",
            bool(beacon_id),
        )  # WHY: prompt result trace.
        if not beacon_id:  # WHY: blank/EOF/interrupt should abort before reaching SDK call.
            logger.error("No beacon_id provided for getSiteBeacon. Exiting.")  # WHY: abort reason.
            logger.info("! No beacon selected. Exiting.")  # WHY: user-facing cancel line.
            return None  # WHY: signal caller to stop without invoking the API.
        return site_id, beacon_id  # WHY: both required identifiers are now validated and ready for API invocation.

    @staticmethod
    def _normalize_site_beacon_payload(response_payload: Any) -> list[dict[str, Any]]:
        """Normalize getSiteBeacon response payload to list-of-dicts for exporter compatibility."""
        if response_payload is None:  # WHY: empty payload should flow through as an empty export dataset.
            return []  # WHY: callers rely on list semantics for empty-result handling.
        if isinstance(response_payload, list):  # WHY: defensive support for list payloads from wrappers/mocks.
            normalized_rows = [row for row in response_payload if isinstance(row, dict)]  # WHY: keep only dict rows.
            logger.debug(
                "Normalized list payload for getSiteBeacon to %d dict rows",
                len(normalized_rows),
            )  # WHY: coercion trace.
            return normalized_rows  # WHY: list payload already matches exporter shape after dict filtering.
        if isinstance(response_payload, dict):  # WHY: expected SDK path returns one beacon object as a dict.
            logger.debug("Normalized dict payload for getSiteBeacon to single-row list")  # WHY: coercion trace.
            return [response_payload]  # WHY: DataExporter expects iterable rows; wrap single dict into list.
        logger.warning(
            "Unexpected getSiteBeacon payload type %s; treating as empty result",
            type(response_payload).__name__,
        )  # WHY: diagnose odd payload.
        return []  # WHY: safest fallback for unsupported payload types is an empty dataset.

    @staticmethod
    def _build_site_beacon_filename(site_id: str, beacon_id: str) -> str:
        """Build deterministic per-request export filename for getSiteBeacon output."""
        sanitized_site_id = site_id.replace("-", "_")  # WHY: normalize punctuation for filenames.
        sanitized_beacon_id = beacon_id.replace("-", "_")  # WHY: keep identifier formatting consistent.
        filename = (  # WHY: deterministic artifact naming.
            f"{_GET_SITE_BEACON_FILENAME_PREFIX}_{sanitized_site_id}_{sanitized_beacon_id}.csv"
        )
        logger.debug("Built deterministic getSiteBeacon filename: %s", filename)  # WHY: artifact trace.
        return filename  # WHY: caller persists output using this stable filename.

    @staticmethod
    def _fetch_site_beacon_with_retry(site_id: str, beacon_id: str) -> list[dict[str, Any]]:
        """Fetch one site beacon with adaptive delay retries on 429-style failures."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        retry_limit = getattr(  # WHY: resolve configured retry cap while preserving behavior when setting is absent.
            getattr(mh, "FastModeSequentialMaxRetries", None),  # WHY: tolerate missing retry config.
            "VALUE",  # WHY: project standard stores retry count on VALUE class attribute.
            _GET_SITE_BEACON_FALLBACK_RETRIES,  # WHY: fallback keeps retries bounded when config object is missing.
        )
        smoothed_delay = None  # WHY: seed RateLimitingUtils smoothing state for adaptive-delay retries.
        first_error: RuntimeError | None = None  # WHY: preserve the first failure across rate-limit retries.
        for attempt in range(retry_limit + 1):  # WHY: include initial attempt plus configured retry attempts.
            logger.info(
                "Calling getSiteBeacon for site_id=%s beacon_id=%s (attempt %d/%d)",
                site_id,
                beacon_id,
                attempt + 1,
                retry_limit + 1,
            )  # WHY: pre-call log.
            try:  # WHY: isolate request failures so 429 can trigger adaptive retry path.
                response = mistapi.api.v1.sites.beacons.getSiteBeacon(  # WHY: SDK get-by-id call.
                    mh.apisession,  # WHY: authenticated API session required by mistapi endpoint functions.
                    site_id=site_id,  # WHY: endpoint path parameter selecting the site container.
                    beacon_id=beacon_id,  # WHY: endpoint path parameter selecting the specific beacon resource.
                )
                payload = getattr(response, "data", response)  # WHY: support object and dict responses.
                rows = SiteClientExporter._normalize_site_beacon_payload(payload)  # WHY: normalize to list rows.
                logger.debug(
                    "getSiteBeacon call succeeded with %d normalized rows",
                    len(rows),
                )  # WHY: post-call summary.
                return rows  # WHY: successful fetch ends retry loop immediately.
            except RuntimeError as exception:  # WHY: capture runtime API failures for retry/abort decisioning.
                if first_error is None:  # WHY: the first rate-limit failure can hold the root cause.
                    first_error = exception  # WHY: later attempts can carry follow-on transport symptoms.
                logging.error(
                    "getSiteBeacon API call failed on attempt %d/%d: %s",
                    attempt + 1,
                    retry_limit + 1,
                    exception,
                )  # WHY: failure details.
                if "429" not in str(exception):  # WHY: only rate-limit errors should enter adaptive retry delay path.
                    if first_error is not exception:  # WHY: a prior retry failure must remain visible to the caller.
                        raise first_error from None  # WHY: preserve the first cause without chaining later symptoms.
                    raise  # WHY: first-attempt non-rate-limit exceptions still bubble unchanged.
                if attempt >= retry_limit:  # WHY: avoid sleeping when no retries remain.
                    raise first_error from None  # WHY: propagate the original rate-limit failure after exhaustion.
                logging.info(  # WHY: pre-delay log.
                    "Rate-limit signal detected; calculating adaptive delay before retry"
                )
                delay_helper = mh.RateLimitingUtils.get_rate_limited_delay  # WHY: adaptive delay helper reference.
                (
                    smoothed_delay,
                    delay_seconds,
                ) = delay_helper(  # type: ignore[no-untyped-call]
                    smoothed_delay,  # WHY: keep smoothing state across retries.
                    mh.apisession,  # WHY: RateLimitingUtils inspects API usage counters through live session object.
                    mh._api_usage_cache,  # WHY: shared mutable cache stores usage snapshots across calls.
                )
                logging.debug(
                    "Adaptive retry delay resolved to %.3f seconds for getSiteBeacon",
                    delay_seconds,
                )  # WHY: delay summary.
                time.sleep(delay_seconds)  # WHY: enforce adaptive backoff interval before retrying the API call.
        return []  # WHY: unreachable safety fallback keeps static analyzers aware of list return type.

    @staticmethod
    def get_site_beacon() -> None:
        """Run getSiteBeacon prompt -> fetch -> export workflow."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Export Site Beacon Detail:")  # WHY: operator-facing header for new menu operation.
        logger.info("Starting getSiteBeacon workflow...")  # WHY: start boundary log for observability timelines.
        identifiers = SiteClientExporter._prompt_site_beacon_identifiers()  # WHY: gather validated identifiers.
        if identifiers is None:  # WHY: prompt helper already logged cancellation/EOF details.
            return  # WHY: stop cleanly when required identifiers were not provided.
        site_id, beacon_id = identifiers  # WHY: unpack validated identifiers for API request and filename construction.
        try:  # WHY: top-level guard keeps menu operation from crashing on API/runtime failures.
            rows = SiteClientExporter._fetch_site_beacon_with_retry(  # WHY: fetch with 429 retry path.
                site_id,
                beacon_id,
            )
        except Exception as exception:  # WHY: error path should surface clear logs and exit gracefully.
            logging.error(
                "! Error fetching site beacon detail for site_id=%s beacon_id=%s: %s",
                site_id,
                beacon_id,
                exception,
            )  # WHY: structured failure context.
            logging.info("! Error fetching site beacon detail: %s", exception)  # WHY: user-facing error line.
            return  # WHY: do not attempt export after fetch failure.
        if not rows:  # WHY: empty payload should end cleanly without writing empty artifacts.
            logger.warning(
                "! getSiteBeacon returned no data for site_id=%s beacon_id=%s",
                site_id,
                beacon_id,
            )  # WHY: no-data warning.
            logger.info("! No beacon data found for the specified identifiers.")  # WHY: user-facing no-data line.
            return  # WHY: skip export when endpoint returns no rows.
        filename = SiteClientExporter._build_site_beacon_filename(site_id, beacon_id)  # WHY: deterministic filename.
        logger.info("Persisting %d getSiteBeacon row(s) to %s", len(rows), filename)  # WHY: pre-write log.
        mh.DataExporter.write_with_format_selection(  # WHY: canonical multi-backend write path.
            rows,  # WHY: normalized row payload from endpoint response.
            filename,  # WHY: deterministic export filename derived from site+beacon identifiers.
            api_function_name=_GET_SITE_BEACON_API_FUNCTION_NAME,  # WHY: explicit operation id for PK strategy.
        )
        logger.debug(
            "Persisted getSiteBeacon payload with row_count=%d filename=%s",
            len(rows),
            filename,
        )  # WHY: post-write summary.
        logger.info("! Exported site beacon detail to %s", filename)  # WHY: user-facing success message.
