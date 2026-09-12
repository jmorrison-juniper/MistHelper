"""Executes the site-scope insight metric export (menu 74)."""

from __future__ import annotations  # WHY: Defer annotation evaluation for cheap forward references

import logging  # WHY: Standard logging keeps ops-visible trace + error output aligned with legacy behaviour
from dataclasses import dataclass  # WHY: Frozen slotted bundle keeps helper signatures under STRUCT-PARAMS limit

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

    def __init__(  # WHY: Constructor injection replaces module globals from parent module
        self,
        *,
        apisession,
        PromptUtils,
        DataProcessingUtils,
        DataExporter,
        EnhancedSSHRunner,
        InsightMetricsUtils,
        mistapi,
    ) -> None:
        """Store injected dependencies on the instance for use by operation methods."""
        self.apisession = apisession  # WHY: bind session for insight API calls.
        self.PromptUtils = PromptUtils  # WHY: bind prompt helpers for site selection.
        self.DataProcessingUtils = DataProcessingUtils  # WHY: bind flatten/escape helpers for CSV output.
        self.DataExporter = DataExporter  # WHY: bind backend writer for CSV/SQLite output.
        self.EnhancedSSHRunner = EnhancedSSHRunner  # WHY: bind filename sanitizer.
        self.InsightMetricsUtils = InsightMetricsUtils  # WHY: bind insight metric helpers.
        self.mistapi = mistapi  # WHY: bind mistapi module for API dispatch.

    def execute(self) -> None:  # WHY: Menu 74 dispatcher entry point invoked by MistHelper top-level menu
        """Top-level entry point invoked by the menu dispatcher for menu 74."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(_BANNER)
        logging.info(_START_LOG)  # WHY: Trace operation start for ops visibility
        context = self._prompt_and_build_context()  # WHY: Resolve site id + name, or bail on cancel
        if context is None:
            return  # WHY: Helper already logged the cancel reason. Exit cleanly
        self._run_export(context)  # WHY: Orchestrate refresh + collect + finalize using bundled context

    def _prompt_and_build_context(self) -> SiteRunContext | None:  # WHY: Consolidate prompt + name lookup for execute()
        """Prompt for site selection and resolve name. Return None on cancel."""
        site_id = self._prompt_site_id()  # WHY: Bail out early if user cancels selection
        if not site_id:
            return None  # WHY: Prompt helper already logged the cancel reason for ops visibility
        site_name = self._resolve_site_name(site_id)  # WHY: Best-effort site label for filename and logs
        return SiteRunContext(site_id=site_id, site_name=site_name)  # WHY: Freeze identifiers into an immutable bundle

    def _run_export(self, context: SiteRunContext) -> None:  # WHY: Orchestrates the post-selection export pipeline
        """Refresh const metrics, collect responses, and finalize output for the resolved site."""
        filename = self._build_filename(context)  # WHY: Sanitized output path mirroring legacy naming
        self._refresh_const_metrics()  # WHY: Refresh ConstInsightMetrics.csv before reading it
        site_metrics = self.InsightMetricsUtils.get_by_scope("site")  # WHY: Pull site-scope list from cache
        if not site_metrics:
            self._emit_empty_metric_list(filename)  # WHY: Defensive: missing const file emits empty file
            return
        all_data, retrieved = self._collect_metrics(context, site_metrics)  # WHY: Per-metric API loop
        self._finalize(all_data, retrieved, filename, context)  # WHY: Flatten + save + summary print

    def _refresh_const_metrics(self) -> None:  # WHY: Isolated call keeps execute() short and testable
        """Refresh ConstInsightMetrics.csv so metric lists reflect the latest API surface."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(_REFRESH_PROMPT)
        self.InsightMetricsUtils.export_const_insight_metrics()  # WHY: Refresh cache before scope-filtering metrics

    def _emit_empty_metric_list(self, filename: str) -> None:  # WHY: Defensive branch used when const file is empty
        """Emit the empty-file + error trio when scope filter yields zero metrics."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(_EMPTY_METRICS_PROMPT)
        logging.error(_EMPTY_METRICS_LOG)  # WHY: Persist failure cause in the log
        self.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # WHY: Emit empty file for downstream consistency

    def _prompt_site_id(self) -> str | None:  # WHY: Wrap prompt in cancel-aware helper for execute()
        """Prompt the user for a site selection. Return None when the user cancels."""
        site_id = self.PromptUtils.select_site()  # WHY: Existing prompt utility handles cancel / invalid input
        if not site_id:
            logging.error(_NO_SITE_LOG)  # WHY: Match legacy error log message verbatim
            return None
        return site_id  # WHY: Selection succeeded. Downstream will resolve name and run export

    def _resolve_site_name(
        self, site_id: str
    ) -> str:  # WHY: Best-effort name lookup keeps execute path narrative clean
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

    def _build_filename(self, context: SiteRunContext) -> str:  # WHY: Single-arg helper mirrors the DeviceMetric peer
        """Build the sanitized output filename used by both CSV and DB exports."""
        sanitized = self.EnhancedSSHRunner.sanitize_filename(  # WHY: Reuse filename sanitizer from SSH runner
            context.site_name or context.site_id
        )
        return _FILENAME_TEMPLATE.format(site=sanitized)  # WHY: Preserve legacy filename shape

    def _collect_metrics(  # WHY: Two-arg loop replaces the legacy three-arg gathering signature
        self,
        context: SiteRunContext,
        site_metrics: list[str],
    ) -> tuple[list[dict], int]:
        """Iterate the metric list and collect any insight data the API returns."""
        all_insight_data: list[dict] = []  # WHY: Accumulator for every non-empty metric response
        retrieved = 0  # WHY: User-facing counter shown in the final summary line
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Retrieving %s different site insight metrics...", len(site_metrics))
        for metric in site_metrics:  # WHY: One API call per metric. Individual failures must not abort the batch
            data = self._fetch_one_metric(context, metric)  # WHY: Enriched dict or None
            if data is not None:
                all_insight_data.append(data)  # WHY: Append the enriched per-metric record for export
                retrieved += 1  # WHY: Bump only on successful, non-empty payload
        return all_insight_data, retrieved  # WHY: Downstream finalize consumes both list and count

    def _fetch_one_metric(self, context: SiteRunContext, metric: str) -> dict | None:  # WHY: Per-metric API + annotate
        """Fetch a single site insight metric, returning the enriched dict or None on miss / error."""
        try:
            response = self.mistapi.api.v1.sites.insights.getSiteInsightMetrics(  # WHY: Single-metric API call
                self.apisession,
                context.site_id,
                metric,
            )
            raw = getattr(response, "data", response) or {}  # WHY: Mistapi returns raw dict or wrapper with .data
        except Exception as exception:
            logging.debug(  # WHY: Non-fatal per-metric failure - continue with next metric
                "Failed to get site insight data for metric %s: %s", metric, exception
            )
            return None
        return self._annotate_row(raw, metric, context)  # WHY: Annotate + short-circuit empty payload

    @staticmethod
    def _annotate_row(raw: dict, metric: str, context: SiteRunContext) -> dict | None:  # WHY: Pure annotation helper
        """Copy scope labels into the row and return None for empty payloads."""
        if not raw:
            logging.debug("No data available for metric: %s", metric)  # WHY: Trace empty payload at debug level only
            return None
        raw["metric_type"] = metric  # WHY: Annotate row with metric name for export readability
        raw["site_id"] = context.site_id  # WHY: Annotate row with site id for downstream joins
        raw["site_name"] = context.site_name  # WHY: Annotate row with site name for export readability
        logging.debug("Retrieved site insight data for metric: %s", metric)  # WHY: Trace success at debug level only
        return raw  # WHY: Enriched row ready for CSV / DB export

    def _finalize(  # WHY: Dispatcher chooses success / empty / error emit path
        self,
        all_insight_data: list[dict],
        retrieved: int,
        filename: str,
        context: SiteRunContext,
    ) -> None:
        """Flatten, escape, and save collected data. Emit summary user output."""
        try:
            if all_insight_data:
                self._export_with_data(  # WHY: Non-empty path writes flattened rows and summary
                    all_insight_data, retrieved, filename, context
                )
                return
            self._export_empty(filename, context)  # WHY: Zero-data path still emits an empty file
        except Exception as exception:
            self._export_error(exception, filename, context)  # WHY: Guarantee file emit on failure

    def _export_with_data(  # WHY: Isolated success path keeps _finalize under STRUCT-LENGTH limit
        self,
        all_insight_data: list[dict],
        retrieved: int,
        filename: str,
        context: SiteRunContext,
    ) -> None:
        """Flatten, escape, and write the non-empty result set. Log the success summary."""
        processed = self.DataProcessingUtils.flatten_nested_fields(all_insight_data)  # WHY: Flatten nested API objs
        processed = self.DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]  # WHY: CSV-safe text
        self.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]  # WHY: Write to disk / DB
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! %s site insight metrics exported to %s", retrieved, filename)
        logging.info(  # WHY: Persist success summary at info level for ops visibility
            "Exported %d site insight metrics for %s to %s",
            retrieved,
            context.site_name,
            filename,
        )

    def _export_empty(self, filename: str, context: SiteRunContext) -> None:  # WHY: Zero-data emit path
        """Emit user-visible zero-data summary and write an empty file for consistency."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! 0 insight metrics exported to %s (no data available)", filename)
        logging.warning("No insight data available for site %s", context.site_name)  # WHY: Distinguish empty from error
        self.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # WHY: Emit empty file for consistency

    def _export_error(  # WHY: Exception emit path - preserve failure visibility while still writing a file
        self,
        exception: Exception,
        filename: str,
        context: SiteRunContext,
    ) -> None:
        """Log the failure with full context and emit an empty file so downstream consumers still see output."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Error exporting site insight metrics: %s", exception)
        logging.error(  # WHY: Persist failure cause with site context for triage
            "Failed to export site insight metrics for %s: %s", context.site_name, exception
        )
        self.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # WHY: Always emit a file for consistency
