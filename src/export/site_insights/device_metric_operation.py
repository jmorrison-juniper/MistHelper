"""Executes the device-scope insight metric export (menu 76)."""

from __future__ import annotations  # WHY: Defer annotation evaluation for cheap forward references

import logging  # WHY: Standard logging keeps ops-visible trace + error output aligned with legacy behaviour
from dataclasses import dataclass  # WHY: Frozen slotted bundle keeps helper signatures under STRUCT-PARAMS limit

from src.export import site_insights_exporter as _parent  # WHY: Parent exposes globals + classification helpers

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

    @staticmethod
    def execute() -> None:  # WHY: Menu 76 dispatcher entry point invoked by MistHelper top-level menu
        """Top-level entry point invoked by the menu dispatcher for menu 76."""
        print("Export Site Device Insights:")  # WHY: User-facing banner preserved verbatim from legacy implementation
        logging.info("Starting export of site device insights...")  # WHY: Trace operation start for ops visibility
        DeviceMetricOperation._refresh_const_metrics()  # WHY: Refresh ConstInsightMetrics.csv before reading it
        prompts = DeviceMetricOperation._prompt_site_and_device()  # WHY: Run both selection prompts up front
        if prompts is None:
            return  # WHY: Helper already logged the cancel reason; exit cleanly
        context = DeviceMetricOperation._build_context(*prompts)  # WHY: Resolve names, MAC, and validate MAC once
        if context is None:
            return  # WHY: Helper already surfaced the specific validation failure
        DeviceMetricOperation._run_export(context)  # WHY: Orchestrate filter + collect + finalize using bundled context

    @staticmethod
    def _refresh_const_metrics() -> None:  # WHY: Isolated call keeps execute() short and testable
        """Refresh ConstInsightMetrics.csv so metric lists reflect the latest API surface."""
        print("! Refreshing available insight metrics from Mist API...")  # WHY: User-facing progress preserved verbatim
        _parent.InsightMetricsUtils.export_const_insight_metrics()  # WHY: Refresh cache before scope-filtering metrics

    @staticmethod
    def _prompt_site_and_device() -> tuple[str, str] | None:  # WHY: Two prompts share cancel semantics
        """Prompt for site then device; return None on either cancel."""
        site_id = _parent.PromptUtils.select_site()  # WHY: Existing prompt utility handles cancel / invalid input
        if not site_id:
            logging.error("No site selected. Exiting.")  # WHY: Match legacy error log message verbatim
            return None
        device_id = _parent.PromptUtils.select_device(site_id)  # WHY: Device prompt is scoped by site
        if not device_id:
            logging.error("No device selected. Exiting.")  # WHY: Match legacy error log message verbatim
            return None
        return site_id, device_id  # WHY: Both selections succeeded; pass to downstream context builder

    @staticmethod
    def _build_context(site_id: str, device_id: str) -> DeviceRunContext | None:  # WHY: Consolidate lookup + validation
        """Resolve names + MAC and return the immutable per-run context, or None on validation failure."""
        site_name = DeviceMetricOperation._resolve_site_name(site_id)  # WHY: Best-effort site label
        device_info = DeviceMetricOperation._resolve_device_info(site_id, device_id)  # WHY: Dict with name/mac/model
        normalized_mac = DeviceMetricOperation._validate_mac(  # WHY: Bail on missing / malformed MAC
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

    @staticmethod
    def _run_export(context: DeviceRunContext) -> None:  # WHY: Orchestrates the post-validation export pipeline
        """Filter compatible metrics, collect responses, and finalize output for the resolved device."""
        filename = DeviceMetricOperation._build_filename(context)  # WHY: Sanitized output path
        device_metrics = DeviceMetricOperation._filter_metrics(context.device_model)  # WHY: Skip incompatible metrics
        if not device_metrics:
            DeviceMetricOperation._emit_empty_metric_list(filename)  # WHY: Consistent empty-file emit on missing const
            return
        all_data, retrieved = DeviceMetricOperation._collect_metrics(context, device_metrics)  # WHY: Per-metric loop
        DeviceMetricOperation._finalize(all_data, retrieved, filename, context)  # WHY: Flatten + save + summary

    @staticmethod
    def _emit_empty_metric_list(filename: str) -> None:  # WHY: Defensive branch used when const file is empty
        """Emit the empty-file + error trio when scope filter yields zero metrics."""
        print(_EMPTY_METRICS_PROMPT)  # WHY: User-facing error preserved verbatim
        logging.error(_EMPTY_METRICS_LOG)  # WHY: Persist failure cause in the log
        _parent.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]

    @staticmethod
    def _resolve_site_name(site_id: str) -> str:  # WHY: Named lookup keeps execute path narrative
        """Best-effort site-name lookup; fall back to site_id when API call fails."""
        try:
            response = _parent.mistapi.api.v1.sites.listSites(  # WHY: API call may raise on auth / network
                _parent.apisession, site_id
            )
            sites = _parent.mistapi.get_all(  # WHY: Materialize paged result list
                response=response, mist_session=_parent.apisession
            )
            return next(  # WHY: Match by id; fall back to id on miss
                (site["name"] for site in sites if site["id"] == site_id), site_id
            )
        except Exception:
            return site_id  # WHY: Silent fallback preserves legacy behaviour for offline / degraded API

    @staticmethod
    def _resolve_device_info(site_id: str, device_id: str) -> dict:  # WHY: Return dict decouples caller from API shape
        """Best-effort device-name / MAC / model lookup; return shaped dict with defaults on failure."""
        try:
            response = _parent.mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: type=all covers switches/gateways
                _parent.apisession,
                site_id,
                type="all",
            )
            devices = _parent.mistapi.get_all(  # WHY: Materialize paged result list
                response=response, mist_session=_parent.apisession
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
        except Exception:
            pass  # WHY: Degrade gracefully so the rest of the flow can still emit a friendly error
        return {"name": device_id, "mac": None, "model": ""}  # WHY: Defaults match legacy fallback exactly

    @staticmethod
    def _validate_mac(device_id: str, device_name: str, device_mac: str | None) -> str | None:  # WHY: Guard MAC use
        """Confirm MAC is present and well-formed; print + log error and return None on failure."""
        if not device_mac:
            print(_MISSING_MAC_PROMPT.format(name=device_name))  # WHY: User-facing error preserved verbatim
            logging.error("Could not find MAC address for device %s", device_id)  # WHY: Persist failure cause
            return None
        normalized = _parent.SiteInsightsExporter._normalize_device_mac_or_none(device_mac)  # WHY: Reuse normalizer
        if not normalized:
            print(_INVALID_MAC_PROMPT.format(name=device_name, mac=device_mac))  # WHY: User-facing error preserved
            logging.error(  # WHY: Persist failure cause with device id + raw MAC for triage
                "Invalid device MAC address format for device %s: %s", device_id, device_mac
            )
            return None
        return normalized  # WHY: Normalized MAC is safe to pass to the insight API

    @staticmethod
    def _build_filename(context: DeviceRunContext) -> str:  # WHY: Single-arg helper mirrors the SiteMetric peer
        """Build the sanitized output filename used by both CSV and DB exports."""
        site_token = _parent.EnhancedSSHRunner.sanitize_filename(  # WHY: Reuse filename sanitizer
            context.site_name or context.site_id
        )
        device_token = _parent.EnhancedSSHRunner.sanitize_filename(  # WHY: Reuse filename sanitizer
            context.device_name or context.device_id
        )
        return _FILENAME_TEMPLATE.format(site=site_token, device=device_token)  # WHY: Preserve legacy filename shape

    @staticmethod
    def _filter_metrics(device_model: str) -> list[str]:  # WHY: Compatible-metric list drives per-metric loop
        """Filter the device-scope metric list to those compatible with this device's platform."""
        metrics = _parent.InsightMetricsUtils.get_by_scope("device")  # WHY: Pull device-scope list from cache
        platform = _parent.SiteInsightsExporter._classify_device_platform(device_model)  # WHY: AP / switch / gateway
        return [  # WHY: Keep only metrics the platform classifier deems compatible
            metric
            for metric in metrics
            if _parent.SiteInsightsExporter._metric_compatible_with_platform(metric, platform)
        ]

    @staticmethod
    def _collect_metrics(  # WHY: Two-arg loop replaces the legacy six-arg gathering signature
        context: DeviceRunContext,
        device_metrics: list[str],
    ) -> tuple[list[dict], int]:
        """Iterate the device-scope metric list and collect any insight data the API returns."""
        all_device_data: list[dict] = []  # WHY: Accumulator for every non-empty metric response
        retrieved = 0  # WHY: User-facing counter shown in final summary line
        print(  # WHY: Progress preserved verbatim with original device-name interpolation
            f"! Retrieving {len(device_metrics)} different device insight metrics for {context.device_name}..."
        )
        for metric in device_metrics:  # WHY: One API call per metric; individual failures must not abort the batch
            data = DeviceMetricOperation._fetch_one_metric(context, metric)  # WHY: Enriched dict or None
            if data is not None:
                all_device_data.append(data)  # WHY: Append enriched record for export
                retrieved += 1  # WHY: Bump only on successful, non-empty payload
        return all_device_data, retrieved  # WHY: Downstream finalize consumes both list and count

    @staticmethod
    def _fetch_one_metric(context: DeviceRunContext, metric: str) -> dict | None:  # WHY: Per-metric API + annotate
        """Fetch a single device insight metric, returning the enriched dict or None on miss / error."""
        try:
            response = _parent.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice(  # WHY: Device endpoint
                _parent.apisession,
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
        return DeviceMetricOperation._annotate_row(raw, metric, context)  # WHY: Annotate + short-circuit empty payload

    @staticmethod
    def _annotate_row(raw: dict, metric: str, context: DeviceRunContext) -> dict | None:  # WHY: Split enrichment out
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

    @staticmethod
    def _finalize(  # WHY: Dispatcher chooses success / empty / error emit path
        all_device_data: list[dict],
        retrieved: int,
        filename: str,
        context: DeviceRunContext,
    ) -> None:
        """Flatten, escape, and save collected data; emit summary user output."""
        try:
            if all_device_data:
                DeviceMetricOperation._export_with_data(  # WHY: Non-empty path writes flattened rows and summary
                    all_device_data, retrieved, filename, context
                )
                return
            DeviceMetricOperation._export_empty(filename, context)  # WHY: Zero-data path still emits an empty file
        except Exception as exception:
            DeviceMetricOperation._export_error(exception, filename, context)  # WHY: Guarantee file emit on failure

    @staticmethod
    def _export_with_data(  # WHY: Isolated success path keeps _finalize under STRUCT-LENGTH limit
        all_device_data: list[dict],
        retrieved: int,
        filename: str,
        context: DeviceRunContext,
    ) -> None:
        """Flatten, escape, and write the non-empty result set; log the success summary."""
        processed = _parent.DataProcessingUtils.flatten_nested_fields(all_device_data)  # WHY: Flatten nested API objs
        processed = _parent.DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
        _parent.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]
        print(f"! {retrieved} device insight metrics exported to {filename}")  # WHY: User-facing summary preserved
        logging.info(  # WHY: Persist success summary at info level for ops visibility
            "Exported %s device insight metrics for %s at %s to %s",
            retrieved,
            context.device_name,
            context.site_name,
            filename,
        )

    @staticmethod
    def _export_empty(filename: str, context: DeviceRunContext) -> None:  # WHY: Zero-data emit path
        """Emit user-visible zero-data summary and write an empty file for consistency."""
        print(f"! 0 device insights exported to {filename} (no data available)")  # WHY: User-facing summary preserved
        logging.warning(  # WHY: Distinguish empty result from error for ops triage
            "No device insight data available for %s at %s",
            context.device_name,
            context.site_name,
        )
        _parent.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]

    @staticmethod
    def _export_error(  # WHY: Exception emit path - preserve failure visibility while still writing a file
        exception: Exception,
        filename: str,
        context: DeviceRunContext,
    ) -> None:
        """Log the failure with full context and emit an empty file so downstream consumers still see output."""
        print(f"! Error exporting device insights: {exception}")  # WHY: User-facing error preserved verbatim
        logging.error(  # WHY: Persist failure cause with both site and device context for triage
            "Failed to export device insights for %s at %s: %s",
            context.device_name,
            context.site_name,
            exception,
        )
        _parent.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]
