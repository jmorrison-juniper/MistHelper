"""Executes the site-scope insight metric export (menu 74)."""

from __future__ import annotations  # WHY: Defer annotation evaluation for cheap forward references

import logging  # WHY: Standard logging keeps ops-visible trace + error output aligned with legacy behaviour
from dataclasses import dataclass  # WHY: Frozen slotted bundle keeps helper signatures under STRUCT-PARAMS limit

from src.export import (
    site_insights_exporter as _parent,
)  # WHY: Parent module exposes mistapi / apisession / DataExporter globals

_BANNER = "Export Site Insight Metrics:"  # WHY: User-facing banner preserved verbatim from legacy implementation
_START_LOG = "Starting export of site insight metrics..."  # WHY: Ops-visible trace message on operation start
_REFRESH_PROMPT = "! Refreshing available insight metrics from Mist API..."  # WHY: User-facing progress preserved
# WHY: User-facing error surfaced when the const file returns no site-scope metrics
_EMPTY_METRICS_PROMPT = "! No metrics found for site scope. Check ConstInsightMetrics.csv file."
_EMPTY_METRICS_LOG = "No site-scope metrics found in const insight metrics"  # WHY: Failure log for missing const file
_NO_SITE_LOG = "No site selected. Exiting."  # WHY: Match legacy error log message verbatim on user cancel
_FILENAME_TEMPLATE = "SiteInsightMetrics_{site}.csv"  # WHY: Filename pattern preserved verbatim from legacy


@dataclass(frozen=True, slots=True)
class SiteRunContext:  # WHY: Frozen bundle collapses site identifiers into a single passable argument
    """Immutable per-run identifiers reused across the site export helpers."""

    site_id: str  # WHY: Mist site UUID scope for every insight API call
    site_name: str  # WHY: Best-effort site label for filename and log context


class SiteMetricOperation:
    """Decomposed replacement for SiteInsightsExporter.insight_metrics()."""

    @staticmethod
    def execute() -> None:  # WHY: Menu 74 dispatcher entry point invoked by MistHelper top-level menu
        """Top-level entry point invoked by the menu dispatcher for menu 74."""
        print(_BANNER)  # WHY: User-facing banner preserved verbatim from legacy implementation
        logging.info(_START_LOG)  # WHY: Trace operation start for ops visibility
        context = SiteMetricOperation._prompt_and_build_context()  # WHY: Resolve site id + name, or bail on cancel
        if context is None:
            return  # WHY: Helper already logged the cancel reason; exit cleanly
        SiteMetricOperation._run_export(context)  # WHY: Orchestrate refresh + collect + finalize using bundled context

    @staticmethod
    def _prompt_and_build_context() -> SiteRunContext | None:  # WHY: Consolidate prompt + name lookup for execute()
        """Prompt for site selection and resolve name; return None on cancel."""
        site_id = SiteMetricOperation._prompt_site_id()  # WHY: Bail out early if user cancels selection
        if not site_id:
            return None  # WHY: Prompt helper already logged the cancel reason for ops visibility
        site_name = SiteMetricOperation._resolve_site_name(site_id)  # WHY: Best-effort site label for filename and logs
        return SiteRunContext(site_id=site_id, site_name=site_name)  # WHY: Freeze identifiers into an immutable bundle

    @staticmethod
    def _run_export(context: SiteRunContext) -> None:  # WHY: Orchestrates the post-selection export pipeline
        """Refresh const metrics, collect responses, and finalize output for the resolved site."""
        filename = SiteMetricOperation._build_filename(context)  # WHY: Sanitized output path mirroring legacy naming
        SiteMetricOperation._refresh_const_metrics()  # WHY: Refresh ConstInsightMetrics.csv before reading it
        site_metrics = _parent.InsightMetricsUtils.get_by_scope("site")  # WHY: Pull site-scope list from cache
        if not site_metrics:
            SiteMetricOperation._emit_empty_metric_list(filename)  # WHY: Defensive: missing const file emits empty file
            return
        all_data, retrieved = SiteMetricOperation._collect_metrics(context, site_metrics)  # WHY: Per-metric API loop
        SiteMetricOperation._finalize(all_data, retrieved, filename, context)  # WHY: Flatten + save + summary print

    @staticmethod
    def _refresh_const_metrics() -> None:  # WHY: Isolated call keeps execute() short and testable
        """Refresh ConstInsightMetrics.csv so metric lists reflect the latest API surface."""
        print(_REFRESH_PROMPT)  # WHY: User-facing progress preserved verbatim from legacy implementation
        _parent.InsightMetricsUtils.export_const_insight_metrics()  # WHY: Refresh cache before scope-filtering metrics

    @staticmethod
    def _emit_empty_metric_list(filename: str) -> None:  # WHY: Defensive branch used when const file is empty
        """Emit the empty-file + error trio when scope filter yields zero metrics."""
        print(_EMPTY_METRICS_PROMPT)  # WHY: User-facing error preserved verbatim from legacy implementation
        logging.error(_EMPTY_METRICS_LOG)  # WHY: Persist failure cause in the log
        _parent.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # WHY: Emit empty file for downstream consistency

    @staticmethod
    def _prompt_site_id() -> str | None:  # WHY: Wrap prompt in cancel-aware helper for execute()
        """Prompt the user for a site selection; return None when the user cancels."""
        site_id = _parent.PromptUtils.select_site()  # WHY: Existing prompt utility handles cancel / invalid input
        if not site_id:
            logging.error(_NO_SITE_LOG)  # WHY: Match legacy error log message verbatim
            return None
        return site_id  # WHY: Selection succeeded; downstream will resolve name and run export

    @staticmethod
    def _resolve_site_name(site_id: str) -> str:  # WHY: Best-effort name lookup keeps execute path narrative clean
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
    def _build_filename(context: SiteRunContext) -> str:  # WHY: Single-arg helper mirrors the DeviceMetric peer
        """Build the sanitized output filename used by both CSV and DB exports."""
        sanitized = _parent.EnhancedSSHRunner.sanitize_filename(  # WHY: Reuse filename sanitizer from SSH runner
            context.site_name or context.site_id
        )
        return _FILENAME_TEMPLATE.format(site=sanitized)  # WHY: Preserve legacy filename shape

    @staticmethod
    def _collect_metrics(  # WHY: Two-arg loop replaces the legacy three-arg gathering signature
        context: SiteRunContext,
        site_metrics: list[str],
    ) -> tuple[list[dict], int]:
        """Iterate the metric list and collect any insight data the API returns."""
        all_insight_data: list[dict] = []  # WHY: Accumulator for every non-empty metric response
        retrieved = 0  # WHY: User-facing counter shown in the final summary line
        print(f"! Retrieving {len(site_metrics)} different site insight metrics...")  # WHY: Progress preserved verbatim
        for metric in site_metrics:  # WHY: One API call per metric; individual failures must not abort the batch
            data = SiteMetricOperation._fetch_one_metric(context, metric)  # WHY: Enriched dict or None
            if data is not None:
                all_insight_data.append(data)  # WHY: Append the enriched per-metric record for export
                retrieved += 1  # WHY: Bump only on successful, non-empty payload
        return all_insight_data, retrieved  # WHY: Downstream finalize consumes both list and count

    @staticmethod
    def _fetch_one_metric(context: SiteRunContext, metric: str) -> dict | None:  # WHY: Per-metric API + annotate
        """Fetch a single site insight metric, returning the enriched dict or None on miss / error."""
        try:
            response = _parent.mistapi.api.v1.sites.insights.getSiteInsightMetrics(  # WHY: Single-metric API call
                _parent.apisession,
                context.site_id,
                metric,
            )
            raw = getattr(response, "data", response) or {}  # WHY: Mistapi returns raw dict or wrapper with .data
        except Exception as exception:
            logging.debug(  # WHY: Non-fatal per-metric failure - continue with next metric
                "Failed to get site insight data for metric %s: %s", metric, exception
            )
            return None
        return SiteMetricOperation._annotate_row(raw, metric, context)  # WHY: Annotate + short-circuit empty payload

    @staticmethod
    def _annotate_row(raw: dict, metric: str, context: SiteRunContext) -> dict | None:  # WHY: Split enrichment out
        """Copy scope labels into the row and return None for empty payloads."""
        if not raw:
            logging.debug("No data available for metric: %s", metric)  # WHY: Trace empty payload at debug level only
            return None
        raw["metric_type"] = metric  # WHY: Annotate row with metric name for export readability
        raw["site_id"] = context.site_id  # WHY: Annotate row with site id for downstream joins
        raw["site_name"] = context.site_name  # WHY: Annotate row with site name for export readability
        logging.debug("Retrieved site insight data for metric: %s", metric)  # WHY: Trace success at debug level only
        return raw  # WHY: Enriched row ready for CSV / DB export

    @staticmethod
    def _finalize(  # WHY: Dispatcher chooses success / empty / error emit path
        all_insight_data: list[dict],
        retrieved: int,
        filename: str,
        context: SiteRunContext,
    ) -> None:
        """Flatten, escape, and save collected data; emit summary user output."""
        try:
            if all_insight_data:
                SiteMetricOperation._export_with_data(  # WHY: Non-empty path writes flattened rows and summary
                    all_insight_data, retrieved, filename, context
                )
                return
            SiteMetricOperation._export_empty(filename, context)  # WHY: Zero-data path still emits an empty file
        except Exception as exception:
            SiteMetricOperation._export_error(exception, filename, context)  # WHY: Guarantee file emit on failure

    @staticmethod
    def _export_with_data(  # WHY: Isolated success path keeps _finalize under STRUCT-LENGTH limit
        all_insight_data: list[dict],
        retrieved: int,
        filename: str,
        context: SiteRunContext,
    ) -> None:
        """Flatten, escape, and write the non-empty result set; log the success summary."""
        processed = _parent.DataProcessingUtils.flatten_nested_fields(all_insight_data)  # WHY: Flatten nested API objs
        processed = _parent.DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]  # WHY: CSV-safe text
        _parent.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]  # WHY: Write to disk / DB
        print(f"! {retrieved} site insight metrics exported to {filename}")  # WHY: User-facing summary preserved
        logging.info(  # WHY: Persist success summary at info level for ops visibility
            "Exported %d site insight metrics for %s to %s",
            retrieved,
            context.site_name,
            filename,
        )

    @staticmethod
    def _export_empty(filename: str, context: SiteRunContext) -> None:  # WHY: Zero-data emit path
        """Emit user-visible zero-data summary and write an empty file for consistency."""
        print(f"! 0 insight metrics exported to {filename} (no data available)")  # WHY: User-facing summary preserved
        logging.warning("No insight data available for site %s", context.site_name)  # WHY: Distinguish empty from error
        _parent.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # WHY: Emit empty file for consistency

    @staticmethod
    def _export_error(  # WHY: Exception emit path - preserve failure visibility while still writing a file
        exception: Exception,
        filename: str,
        context: SiteRunContext,
    ) -> None:
        """Log the failure with full context and emit an empty file so downstream consumers still see output."""
        print(f"! Error exporting site insight metrics: {exception}")  # WHY: User-facing error preserved verbatim
        logging.error(  # WHY: Persist failure cause with site context for triage
            "Failed to export site insight metrics for %s: %s", context.site_name, exception
        )
        _parent.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # WHY: Always emit a file for consistency
