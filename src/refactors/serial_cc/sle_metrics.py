"""SLE metrics export orchestration extracted from MistHelper offender #9."""

import importlib
import logging
import time
from types import SimpleNamespace
from typing import Any

from src.dataclasses.progress_event import ProgressContext  # Issue #470: bundle progress identity for emit_progress_*.


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static src imports."""
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular src->MistHelper dependency
    return SimpleNamespace(
        ConfigUtils=misthelper_module.ConfigUtils,
        PROGRESS_EMITTER=getattr(misthelper_module, "PROGRESS_EMITTER", None),
        TimeUtils=misthelper_module.TimeUtils,
        DataProcessingUtils=misthelper_module.DataProcessingUtils,
        DataExporter=misthelper_module.DataExporter,
        mistapi=misthelper_module.mistapi,
        apisession=misthelper_module.apisession,
    )


class _SleProgressTracker:
    """Encapsulates SLE export progress emission and the shared items-done counter."""

    def __init__(self, emitter: Any, total_items: int) -> None:
        self._emitter = emitter  # Optional progress emitter (None when progress disabled)
        self._total = total_items  # Total work units for this run
        self._done = 0  # Units completed so far (advanced once per metric/category)
        self._start = time.time()  # Wall-clock start used for the completion duration

    def start(self) -> None:
        """Emit the progress-start event when an emitter is configured."""
        if self._emitter:  # Only emit when progress tracking is active
            self._emitter.emit_progress_start("66", "sle_metrics", self._total)  # Announce total work

    def tick(self, label: str) -> None:
        """Advance the done counter by one and emit a progress tick."""
        self._done += 1  # One more metric/category finished (success or failure)
        if self._emitter:  # Only emit when progress tracking is active
            self._emitter.emit_progress_tick(
                ProgressContext("66", "sle_metrics", self._total), label, self._done, self._total - self._done
            )  # Report current label and remaining count (issue #470: identity bundled into ProgressContext)

    def complete(self) -> None:
        """Emit the progress-complete event with elapsed duration."""
        if self._emitter:  # Only emit when progress tracking is active
            self._emitter.emit_progress_complete(
                ProgressContext("66", "sle_metrics", self._total), self._done, False, time.time() - self._start
            )  # Final event with elapsed seconds (issue #470: identity bundled into ProgressContext)


class SLEMetricsService:
    """Owns organization SLE metrics export flow formerly embedded in MistHelper."""

    @staticmethod
    def _build_run_config(deps: SimpleNamespace, fast: bool) -> SimpleNamespace:
        """Build the category/metric/duration configuration, honoring fast smoke mode."""
        sle_categories = ["wifi", "wan", "wired"]  # WiFi, WAN, and wired SLE service categories
        specialized_metrics = ["summary", "sites-sle", "worst-sites-by-sle"]  # Org-level specialized aggregations
        duration_value = "7d"  # Default lookback window
        if fast:  # Fast mode collapses to a minimal smoke path
            sle_categories = ["wifi"]  # Single category for the smoke run
            specialized_metrics = ["summary"]  # Single specialized metric for the smoke run
            lookback_hours = deps.TimeUtils.get_dynamic_lookback_hours(default_hours=24, test_hours=1)  # Short window
            duration_value = f"{lookback_hours}h"  # Hour-scale duration for fast mode
            logging.info(
                "Fast mode enabled for option 66: using smoke path (categories=%s, specialized=%s, duration=%s)",
                sle_categories,
                specialized_metrics,
                duration_value,
            )  # Trace the reduced smoke configuration
        return SimpleNamespace(
            sle_categories=sle_categories,
            specialized_metrics=specialized_metrics,
            duration_value=duration_value,
        )  # Bundle the resolved run configuration

    @staticmethod
    def _build_sites_aggregated_record(
        metric: str, org_id: str, sle_category: str, sites_sle_data: list[Any]
    ) -> dict[str, Any]:
        """Build one aggregated SLE record for a metric/category and tag worst-site analyses."""
        # WHY: extracted so _fetch_category_sites keeps CC low and _fetch_sites_aggregated shrinks.
        aggregated_result: dict[str, Any] = {
            "sle_metric_type": f"{metric}_{sle_category}",  # Composite key for downstream consumers
            "org_id": org_id,  # Owning org UUID
            "sle_category": sle_category,  # WiFi/WAN/wired category
            "data_source": "org_sites_sle_aggregated",  # Marks the aggregation path used
            "total_sites": len(sites_sle_data),  # Count of sites in the returned page set
            "sites_analyzed": sites_sle_data,  # Underlying per-site SLE payloads
            "metric_name": metric,  # Original metric name for cross-reference
        }
        if "worst-sites" in metric:  # Tag worst-site analyses for downstream consumers
            aggregated_result["analysis_type"] = "worst_sites_identification"  # Mark analysis intent
        return aggregated_result  # Ready for accumulation into all_sle_data

    @staticmethod
    def _fetch_category_sites(
        deps: SimpleNamespace, org_id: str, metric: str, sle_category: str, config: SimpleNamespace
    ) -> dict[str, Any] | None:
        """Fetch one category's sites SLE data and return an aggregated record (or None if empty)."""
        # WHY: returns dict|None instead of taking all_sle_data by ref to stay under STRUCT-PARAMS (5).
        response = deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(
            deps.apisession, org_id, sle=sle_category, duration=config.duration_value, limit=1000
        )  # Query org sites SLE for this category
        sites_sle_data = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # Page all
        if not sites_sle_data:  # No sites returned for this category
            logging.debug("No sites SLE data available for metric: %s with SLE: %s", metric, sle_category)  # Empty
            return None  # Category produced no data
        logging.debug(
            "Retrieved sites SLE for %s/%s (%s sites)", metric, sle_category, len(sites_sle_data)
        )  # Trace success with site count
        return SLEMetricsService._build_sites_aggregated_record(metric, org_id, sle_category, sites_sle_data)

    @staticmethod
    def _fetch_sites_aggregated(
        deps: SimpleNamespace, org_id: str, metric: str, config: SimpleNamespace, all_sle_data: list[Any]
    ) -> int:
        """Fetch per-category sites SLE data for a worst-sites/sites-sle metric; return retrieved count."""
        retrieved = 0  # Successful per-category fetches for this metric
        for sle_category in config.sle_categories:  # Iterate each service category for this aggregated metric
            try:  # Per-category failures are non-fatal and skip to the next category
                record = SLEMetricsService._fetch_category_sites(deps, org_id, metric, sle_category, config)
                if record is not None:  # Helper returned an aggregated record for this category
                    all_sle_data.append(record)  # Accumulate the aggregated record
                    retrieved += 1  # Count this successful category fetch
            except Exception as sites_error:  # Category-level API failure - log and continue
                logging.debug(
                    "Failed sites SLE for metric '%s' with SLE '%s': %s", metric, sle_category, sites_error
                )  # Trace the per-category failure
        return retrieved  # Total successful category fetches for this metric

    @staticmethod
    def _fetch_single_sle(
        deps: SimpleNamespace, org_id: str, metric: str, config: SimpleNamespace, all_sle_data: list[Any]
    ) -> tuple[int, int]:
        """Fetch a single org-level specialized SLE metric; return (retrieved, failed) deltas."""
        response = deps.mistapi.api.v1.orgs.insights.getOrgSle(
            deps.apisession, org_id, metric, duration=config.duration_value
        )  # Query the single specialized org SLE metric
        sle_data = getattr(response, "data", response) or {}  # Normalize to the data payload (or empty)
        if sle_data:  # Metric returned data
            sle_data["sle_metric_type"] = metric  # Tag the metric type
            sle_data["org_id"] = org_id  # Tag the owning org
            sle_data["data_source"] = "org_sle_specialized"  # Tag the data source
            all_sle_data.append(sle_data)  # Accumulate the specialized record
            logging.debug("Successfully retrieved specialized SLE data for metric: %s", metric)  # Trace success
            return 1, 0  # One retrieved, none failed
        logging.debug("No data available for specialized SLE metric: %s", metric)  # Trace empty result
        return 0, 1  # None retrieved, one failed (no data)

    @classmethod
    def _fetch_specialized_metric(
        cls, deps: SimpleNamespace, org_id: str, metric: str, config: SimpleNamespace, all_sle_data: list[Any]
    ) -> tuple[int, int]:
        """Dispatch one specialized metric to the sites-aggregated or single-SLE path."""
        if "worst-sites" in metric or "sites-sle" in metric:  # Aggregated metrics iterate sites per category
            retrieved = cls._fetch_sites_aggregated(deps, org_id, metric, config, all_sle_data)  # Per-category fetch
            return retrieved, 0  # Aggregated path never marks a metric-level failure (per-category errors continue)
        return cls._fetch_single_sle(deps, org_id, metric, config, all_sle_data)  # Single specialized SLE fetch

    @classmethod
    def _run_specialized_loop(
        cls,
        deps: SimpleNamespace,
        org_id: str,
        config: SimpleNamespace,
        all_sle_data: list[Any],
        progress: "_SleProgressTracker",
    ) -> tuple[int, int]:
        """Run the specialized-metrics loop; return cumulative (retrieved, failed)."""
        retrieved = 0  # Cumulative successful specialized fetches
        failed = 0  # Cumulative failed specialized fetches
        for metric in config.specialized_metrics:  # First loop: specialized org metrics
            try:  # Whole-metric failures are non-fatal
                metric_retrieved, metric_failed = cls._fetch_specialized_metric(
                    deps, org_id, metric, config, all_sle_data
                )  # Fetch one specialized metric
                retrieved += metric_retrieved  # Add this metric's successes
                failed += metric_failed  # Add this metric's failures
            except Exception as metric_error:  # Unexpected metric-level failure
                failed += 1  # Count the failed metric
                logging.debug("Failed to get specialized SLE data for metric '%s': %s", metric, metric_error)  # Trace
            finally:  # Always advance progress for this metric, success or failure
                progress.tick(metric)  # One work unit done
        return retrieved, failed  # Cumulative specialized results

    @staticmethod
    def _fetch_aggregated_category(
        deps: SimpleNamespace, org_id: str, sle_category: str, config: SimpleNamespace, all_sle_data: list[Any]
    ) -> tuple[int, int]:
        """Fetch org-aggregated SLE data for one category; return (retrieved, failed) deltas."""
        response = deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(
            deps.apisession, org_id, sle=sle_category, duration=config.duration_value, limit=1000
        )  # Query org sites SLE for this category
        sites_sle_data = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # Page all sites
        if sites_sle_data:  # Category returned sites
            org_aggregated = {
                "sle_category": sle_category,
                "org_id": org_id,
                "data_source": "org_aggregated_from_sites",
                "total_sites": len(sites_sle_data),
                "sites_data": sites_sle_data,
                "summary_calculated": True,
            }  # Build the org-aggregated record (summary always calculated when sites exist)
            all_sle_data.append(org_aggregated)  # Accumulate the aggregated record
            logging.debug(
                "Successfully aggregated SLE data for %s sites in category: %s", len(sites_sle_data), sle_category
            )  # Trace success with site count
            return 1, 0  # One retrieved, none failed
        logging.debug("No sites SLE data available for category: %s", sle_category)  # Trace empty category
        return 0, 1  # None retrieved, one failed (no data)

    @classmethod
    def _run_category_loop(
        cls,
        deps: SimpleNamespace,
        org_id: str,
        config: SimpleNamespace,
        all_sle_data: list[Any],
        progress: "_SleProgressTracker",
    ) -> tuple[int, int]:
        """Run the per-category aggregation loop; return cumulative (retrieved, failed)."""
        retrieved = 0  # Cumulative successful category fetches
        failed = 0  # Cumulative failed category fetches
        for sle_category in config.sle_categories:  # Second loop: aggregated SLE by category
            try:  # Per-category failures are non-fatal
                category_retrieved, category_failed = cls._fetch_aggregated_category(
                    deps, org_id, sle_category, config, all_sle_data
                )  # Fetch one category's aggregation
                retrieved += category_retrieved  # Add this category's successes
                failed += category_failed  # Add this category's failures
            except Exception as category_error:  # Unexpected category-level failure
                failed += 1  # Count the failed category
                logging.debug("Failed to get SLE data for category '%s': %s", sle_category, category_error)  # Trace
            finally:  # Always advance progress for this category, success or failure
                progress.tick(sle_category)  # One work unit done
        return retrieved, failed  # Cumulative category results

    @staticmethod
    def _export_results(deps: SimpleNamespace, all_sle_data: list[Any], metrics_retrieved: int) -> None:
        """Flatten and export collected SLE data, or write an empty file when none was collected."""
        if all_sle_data:  # Data was collected from at least one source
            processed = deps.DataProcessingUtils.flatten_nested_fields(all_sle_data)  # Flatten nested SLE structures
            processed = deps.DataProcessingUtils.escape_multiline(processed)  # Escape multiline fields for CSV
            deps.DataExporter.write_with_format_selection(processed, "OrgSLEMetrics.csv")  # Write the export file
            print(f"! {metrics_retrieved} organization SLE data sources exported to OrgSLEMetrics.csv")  # User summary
            logging.info(
                "Exported %s org SLE data points from %s sources to OrgSLEMetrics.csv",
                len(processed),
                metrics_retrieved,
            )  # Trace export volume
        else:  # No data collected from any source
            print("! 0 organization SLE metrics exported to OrgSLEMetrics.csv (no data available)")  # User summary
            logging.warning("No org SLE data available - all sources failed or returned empty")  # Warn on empty run
            deps.DataExporter.write_with_format_selection(
                [], "OrgSLEMetrics.csv"
            )  # Write an empty export for consistency

    @classmethod
    def _run_retrieval(
        cls,
        deps: SimpleNamespace,
        org_id: str,
        config: SimpleNamespace,
        all_sle_data: list[Any],
        progress: "_SleProgressTracker",
    ) -> None:
        """Run both retrieval loops and export; write empty CSV on any top-level failure."""
        # WHY: extracted from execute so execute stays under the 25-line STRUCT-LENGTH limit.
        try:  # Guard the whole retrieval+export so progress always completes
            spec_ok, spec_fail = cls._run_specialized_loop(deps, org_id, config, all_sle_data, progress)  # Loop 1
            cat_ok, cat_fail = cls._run_category_loop(deps, org_id, config, all_sle_data, progress)  # Loop 2
            metrics_retrieved = spec_ok + cat_ok  # Total successful fetches
            metrics_failed = spec_fail + cat_fail  # Total failed fetches
            print(f"! SLE data retrieval completed: {metrics_retrieved} successful, {metrics_failed} failed")  # Summary
            logging.info("Org SLE data: %s retrieved successfully, %s failed", metrics_retrieved, metrics_failed)
            cls._export_results(deps, all_sle_data, metrics_retrieved)  # Flatten + export (or write empty)
        except Exception as exception:  # Any unexpected top-level failure still writes an empty export
            print(f"! Error exporting organization SLE metrics: {exception}")  # User-facing error
            logging.error("Failed to export org SLE metrics: %s", exception)  # Trace the failure
            deps.DataExporter.write_with_format_selection([], "OrgSLEMetrics.csv")  # Write empty export on failure

    @classmethod
    def execute(cls, fast: bool = False) -> None:
        """Run the organization SLE metrics export workflow."""
        deps = _resolve_runtime_dependencies()  # Resolve MistHelper collaborators at call time
        print("Export Organization SLE Metrics:")  # User-facing banner
        logging.info("Starting export of organization SLE metrics...")  # Trace workflow start
        org_id = deps.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve target org (cached or prompted)
        config = cls._build_run_config(deps, fast)  # Resolve categories/metrics/duration (honors fast mode)
        total_items = len(config.specialized_metrics) + len(config.sle_categories)  # Total progress work units
        progress = _SleProgressTracker(deps.PROGRESS_EMITTER, total_items)  # Encapsulate progress + items-done counter
        progress.start()  # Emit the progress-start event
        all_sle_data: list[Any] = []  # Accumulates every SLE record across both loops
        print(f"! Retrieving organization SLE data using {len(config.sle_categories)} service categories...")  # Info
        print(f"! Also attempting {len(config.specialized_metrics)} specialized SLE aggregation metrics...")  # Info
        cls._run_retrieval(deps, org_id, config, all_sle_data, progress)  # Run both loops + export (or empty)
        progress.complete()  # Always emit the progress-complete event
