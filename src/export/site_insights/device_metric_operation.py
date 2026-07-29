"""Executes the device-scope insight metric export (menu 76)."""

from __future__ import annotations  # WHY: Defer annotation evaluation for cheap forward references

import logging  # WHY: Standard logging keeps ops-visible trace + error output aligned with legacy behaviour
from dataclasses import dataclass  # WHY: Frozen slotted bundle keeps helper signatures under STRUCT-PARAMS limit

from src.export.site_insights_exporter import SiteInsightsExporter  # WHY: Static classifier + MAC normalizer access

_EMPTY_METRICS_PROMPT = (
    "! No metrics found for device scope. Check ConstInsightMetrics.csv file."  # WHY: Reused literal
)
_EMPTY_METRICS_LOG = "No device-scope metrics found in const insight metrics"  # WHY: Reused failure log message
_FILENAME_TEMPLATE = "SiteDeviceInsights_{site}_{device}.csv"  # WHY: Filename pattern preserved verbatim from legacy
_MISSING_MAC_PROMPT = "! Error: Could not find MAC address for device {name}"  # WHY: User-facing missing-MAC message
_INVALID_MAC_PROMPT = "! Invalid device MAC address format for {name}: {mac}"  # WHY: User-facing invalid-MAC message


@dataclass(frozen=True, slots=True)
class DeviceRunContext:  # WHY: Frozen bundle collapses six-param signatures under STRUCT-PARAMS limit
    """Immutable per-run identifiers reused across the device export helpers."""

    site_id: str  # WHY: Mist site UUID scope for every insight API call
    site_name: str  # WHY: Best-effort site label for filename and log context
    device_id: str  # WHY: Mist device UUID used in per-metric annotations and logs
    device_name: str  # WHY: Human-readable device label for filename and user output
    device_mac: str  # WHY: Normalized MAC required by getSiteInsightMetricsForDevice endpoint
    device_model: str  # WHY: Device model string drives platform-compatibility metric filter


class DeviceMetricOperation:
    """Decomposed replacement for SiteInsightsExporter.device_insights()."""

    def __init__(  # WHY: Constructor injection replaces module globals from parent module
        self,
        *,
        apisession,
        PromptUtils,
        DataProcessingUtils,
        DataExporter,
        EnhancedSSHRunner,
        InsightMetricsUtils,
        PacketCaptureManager,
        mistapi,
    ) -> None:
        """Store injected dependencies on the instance for use by operation methods."""
        self.apisession = apisession  # WHY: bind session for insight API calls.
        self.PromptUtils = PromptUtils  # WHY: bind prompt helpers for site/device selection.
        self.DataProcessingUtils = DataProcessingUtils  # WHY: bind flatten/escape helpers for CSV output.
        self.DataExporter = DataExporter  # WHY: bind backend writer for CSV/SQLite output.
        self.EnhancedSSHRunner = EnhancedSSHRunner  # WHY: bind filename sanitizer.
        self.InsightMetricsUtils = InsightMetricsUtils  # WHY: bind insight metric helpers.
        self.mistapi = mistapi  # WHY: bind mistapi module for API dispatch.
        # WHY: Sibling insights exporter instance provides MAC normalizer using PacketCaptureManager.
        self._insights_exporter = SiteInsightsExporter(PacketCaptureManager=PacketCaptureManager)

    def execute(self) -> None:  # WHY: Menu 76 dispatcher entry point invoked by MistHelper top-level menu
        """Top-level entry point invoked by the menu dispatcher for menu 76."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Export Site Device Insights:")
        logging.info("Starting export of site device insights...")  # WHY: Trace operation start for ops visibility
        self._refresh_const_metrics()  # WHY: Refresh ConstInsightMetrics.csv before reading it
        prompts = self._prompt_site_and_device()  # WHY: Run both selection prompts up front
        if prompts is None:
            return  # WHY: Helper already logged the cancel reason. Exit cleanly
        context = self._build_context(*prompts)  # WHY: Resolve names, MAC, and validate MAC once
        if context is None:
            return  # WHY: Helper already surfaced the specific validation failure
        self._run_export(context)  # WHY: Orchestrate filter + collect + finalize using bundled context

    def _refresh_const_metrics(self) -> None:  # WHY: Isolated call keeps execute() short and testable
        """Refresh ConstInsightMetrics.csv so metric lists reflect the latest API surface."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Refreshing available insight metrics from Mist API...")
        self.InsightMetricsUtils.export_const_insight_metrics()  # WHY: Refresh cache before scope-filtering metrics

    def _prompt_site_and_device(self) -> tuple[str, str] | None:  # WHY: Two prompts share cancel semantics
        """Prompt for site then device. Return None on either cancel."""
        site_id = self.PromptUtils.select_site()  # WHY: Existing prompt utility handles cancel / invalid input
        if not site_id:
            logging.error("No site selected. Exiting.")  # WHY: Match legacy error log message verbatim
            return None
        device_id = self.PromptUtils.select_device(site_id)  # WHY: Device prompt is scoped by site
        if not device_id:
            logging.error("No device selected. Exiting.")  # WHY: Match legacy error log message verbatim
            return None
        return site_id, device_id  # WHY: Both selections succeeded. Pass to downstream context builder

    def _build_context(
        self, site_id: str, device_id: str
    ) -> DeviceRunContext | None:  # WHY: Consolidate lookup + validation
        """Resolve names + MAC and return the immutable per-run context, or None on validation failure."""
        site_name = self._resolve_site_name(site_id)  # WHY: Best-effort site label
        device_info = self._resolve_device_info(site_id, device_id)  # WHY: Dict with name/mac/model
        normalized_mac = self._validate_mac(  # WHY: Bail on missing / malformed MAC
            device_id, device_info["name"], device_info["mac"]
        )
        if normalized_mac is None:
            return None  # WHY: Helper already surfaced the validation error to user and log
        return DeviceRunContext(  # WHY: Freeze all downstream identifiers into a single bundle
            site_id=site_id,
            site_name=site_name,
            device_id=device_id,
            device_name=device_info["name"],
            device_mac=normalized_mac,
            device_model=device_info.get("model", ""),
        )

    def _run_export(self, context: DeviceRunContext) -> None:  # WHY: Orchestrates the post-validation export pipeline
        """Filter compatible metrics, collect responses, and finalize output for the resolved device."""
        filename = self._build_filename(context)  # WHY: Sanitized output path
        device_metrics = self._filter_metrics(context.device_model)  # WHY: Skip incompatible metrics
        if not device_metrics:
            self._emit_empty_metric_list(filename)  # WHY: Consistent empty-file emit on missing const
            return
        all_data, retrieved = self._collect_metrics(context, device_metrics)  # WHY: Per-metric loop
        self._finalize(all_data, retrieved, filename, context)  # WHY: Flatten + save + summary

    def _emit_empty_metric_list(self, filename: str) -> None:  # WHY: Defensive branch used when const file is empty
        """Emit the empty-file + error trio when scope filter yields zero metrics."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(_EMPTY_METRICS_PROMPT)
        logging.error(_EMPTY_METRICS_LOG)  # WHY: Persist failure cause in the log
        self.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]

    def _resolve_site_name(self, site_id: str) -> str:  # WHY: Named lookup keeps execute path narrative
        """Best-effort site-name lookup. Fall back to site_id when API call fails."""
        try:
            response = self.mistapi.api.v1.sites.listSites(  # WHY: API call may raise on auth / network
                self.apisession, site_id
            )
            sites = self.mistapi.get_all(  # WHY: Materialize paged result list
                response=response, mist_session=self.apisession
            )
            return next(  # WHY: Match by id. Fall back to id on miss
                (site["name"] for site in sites if site["id"] == site_id), site_id
            )
        except Exception:
            return site_id  # WHY: Silent fallback preserves legacy behaviour for offline / degraded API

    def _resolve_device_info(
        self, site_id: str, device_id: str
    ) -> dict:  # WHY: Return dict decouples caller from API shape
        """Best-effort device-name / MAC / model lookup. Return shaped dict with defaults on failure."""
        try:
            response = self.mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: type=all covers switches/gateways
                self.apisession,
                site_id,
                type="all",
            )
            devices = self.mistapi.get_all(  # WHY: Materialize paged result list
                response=response, mist_session=self.apisession
            )
            device = next(  # WHY: Locate the device by id within the site
                (dev for dev in devices if dev["id"] == device_id), None
            )
            if device:
                return {  # WHY: Found the device: extract the three fields we need downstream
                    "name": device["name"],
                    "mac": device["mac"],
                    "model": device.get("model", ""),
                }
        except Exception as error:  # WHY: a lookup failure must not stop the friendly error message below.
            # WHY: Degrade gracefully so the rest of the flow can still emit a friendly error
            logging.debug("Device lookup failed for %s: %s", device_id, error)  # Make the failure visible.
        return {"name": device_id, "mac": None, "model": ""}  # WHY: Defaults match legacy fallback exactly

    def _validate_mac(
        self, device_id: str, device_name: str, device_mac: str | None
    ) -> str | None:  # WHY: Guard MAC use
        """Confirm MAC is present and well-formed. Print + log error and return None on failure."""
        if not device_mac:
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(_MISSING_MAC_PROMPT.format(name=device_name))
            logging.error("Could not find MAC address for device %s", device_id)  # WHY: Persist failure cause
            return None
        normalized = self._insights_exporter._normalize_device_mac_or_none(device_mac)  # WHY: Reuse normalizer
        if not normalized:
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(_INVALID_MAC_PROMPT.format(name=device_name, mac=device_mac))
            logging.error(  # WHY: Persist failure cause with device id + raw MAC for triage
                "Invalid device MAC address format for device %s: %s", device_id, device_mac
            )
            return None
        return normalized  # WHY: Normalized MAC is safe to pass to the insight API

    def _build_filename(self, context: DeviceRunContext) -> str:  # WHY: Single-arg helper mirrors the SiteMetric peer
        """Build the sanitized output filename used by both CSV and DB exports."""
        site_token = self.EnhancedSSHRunner.sanitize_filename(  # WHY: Reuse filename sanitizer
            context.site_name or context.site_id
        )
        device_token = self.EnhancedSSHRunner.sanitize_filename(  # WHY: Reuse filename sanitizer
            context.device_name or context.device_id
        )
        return _FILENAME_TEMPLATE.format(site=site_token, device=device_token)  # WHY: Preserve legacy filename shape

    def _filter_metrics(self, device_model: str) -> list[str]:  # WHY: Compatible-metric list drives per-metric loop
        """Filter the device-scope metric list to those compatible with this device's platform."""
        metrics = self.InsightMetricsUtils.get_by_scope("device")  # WHY: Pull device-scope list from cache
        platform = SiteInsightsExporter._classify_device_platform(device_model)  # WHY: AP / switch / gateway
        return [  # WHY: Keep only metrics the platform classifier deems compatible
            metric for metric in metrics if SiteInsightsExporter._metric_compatible_with_platform(metric, platform)
        ]

    def _collect_metrics(  # WHY: Two-arg loop replaces the legacy six-arg gathering signature
        self,
        context: DeviceRunContext,
        device_metrics: list[str],
    ) -> tuple[list[dict], int]:
        """Iterate the device-scope metric list and collect any insight data the API returns."""
        all_device_data: list[dict] = []  # WHY: Accumulator for every non-empty metric response
        retrieved = 0  # WHY: User-facing counter shown in final summary line
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(
            "! Retrieving %s different device insight metrics for %s...",
            len(device_metrics),
            context.device_name,
        )
        for metric in device_metrics:  # WHY: One API call per metric. Individual failures must not abort the batch
            data = self._fetch_one_metric(context, metric)  # WHY: Enriched dict or None
            if data is not None:
                all_device_data.append(data)  # WHY: Append enriched record for export
                retrieved += 1  # WHY: Bump only on successful, non-empty payload
        return all_device_data, retrieved  # WHY: Downstream finalize consumes both list and count

    def _fetch_one_metric(
        self, context: DeviceRunContext, metric: str
    ) -> dict | None:  # WHY: Per-metric API + annotate
        """Fetch a single device insight metric, returning the enriched dict or None on miss / error."""
        try:
            response = self.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice(  # WHY: Device endpoint
                self.apisession,
                context.site_id,
                metric,
                context.device_mac,
            )
            raw = getattr(response, "data", response) or {}  # WHY: Mistapi returns dict or wrapper with .data
        except Exception as exception:
            logging.debug(  # WHY: Non-fatal per-metric failure - continue with next metric
                "Failed to get device insight data for metric %s: %s", metric, exception
            )
            return None
        return self._annotate_row(raw, metric, context)  # WHY: Annotate + short-circuit empty payload

    @staticmethod
    def _annotate_row(raw: dict, metric: str, context: DeviceRunContext) -> dict | None:  # WHY: Pure annotation helper
        """Copy scope labels into the row and return None for empty payloads."""
        if not raw:
            logging.debug("No data available for device metric: %s", metric)  # WHY: Trace empty payload at debug only
            return None
        raw["metric_type"] = metric  # WHY: Annotate row with metric name for export readability
        raw["site_id"] = context.site_id  # WHY: Annotate row with site id for downstream joins
        raw["site_name"] = context.site_name  # WHY: Annotate row with site name for export readability
        raw["device_id"] = context.device_id  # WHY: Annotate row with device id for downstream joins
        raw["device_name"] = context.device_name  # WHY: Annotate row with device name for export readability
        raw["device_mac"] = context.device_mac  # WHY: Annotate row with normalized MAC for downstream joins
        logging.debug("Retrieved device insight data for metric: %s", metric)  # WHY: Trace success at debug level
        return raw  # WHY: Enriched row ready for CSV / DB export

    def _finalize(  # WHY: Dispatcher chooses success / empty / error emit path
        self,
        all_device_data: list[dict],
        retrieved: int,
        filename: str,
        context: DeviceRunContext,
    ) -> None:
        """Flatten, escape, and save collected data. Emit summary user output."""
        try:
            if all_device_data:
                self._export_with_data(  # WHY: Non-empty path writes flattened rows and summary
                    all_device_data, retrieved, filename, context
                )
                return
            self._export_empty(filename, context)  # WHY: Zero-data path still emits an empty file
        except Exception as exception:
            self._export_error(exception, filename, context)  # WHY: Guarantee file emit on failure

    def _export_with_data(  # WHY: Isolated success path keeps _finalize under STRUCT-LENGTH limit
        self,
        all_device_data: list[dict],
        retrieved: int,
        filename: str,
        context: DeviceRunContext,
    ) -> None:
        """Flatten, escape, and write the non-empty result set. Log the success summary."""
        processed = self.DataProcessingUtils.flatten_nested_fields(all_device_data)  # WHY: Flatten nested API objs
        processed = self.DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
        self.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! %s device insight metrics exported to %s", retrieved, filename)
        logging.info(  # WHY: Persist success summary at info level for ops visibility
            "Exported %s device insight metrics for %s at %s to %s",
            retrieved,
            context.device_name,
            context.site_name,
            filename,
        )

    def _export_empty(self, filename: str, context: DeviceRunContext) -> None:  # WHY: Zero-data emit path
        """Emit user-visible zero-data summary and write an empty file for consistency."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! 0 device insights exported to %s (no data available)", filename)
        logging.warning(  # WHY: Distinguish empty result from error for ops triage
            "No device insight data available for %s at %s",
            context.device_name,
            context.site_name,
        )
        self.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]

    def _export_error(  # WHY: Exception emit path - preserve failure visibility while still writing a file
        self,
        exception: Exception,
        filename: str,
        context: DeviceRunContext,
    ) -> None:
        """Log the failure with full context and emit an empty file so downstream consumers still see output."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Error exporting device insights: %s", exception)
        logging.error(  # WHY: Persist failure cause with both site and device context for triage
            "Failed to export device insights for %s at %s: %s",
            context.device_name,
            context.site_name,
            exception,
        )
        self.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]
