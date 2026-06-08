"""Executes the site-scope insight metric export (menu 74)."""

from __future__ import annotations

import logging

from src.export import (
    site_insights_exporter as _parent,
)  # Parent module exposes mistapi / apisession / DataExporter globals


class SiteMetricOperation:
    """Decomposed replacement for SiteInsightsExporter.insight_metrics()."""

    @staticmethod
    def execute() -> None:
        """Top-level entry point invoked by the menu dispatcher for menu 74."""
        print("Export Site Insight Metrics:")  # User-facing banner preserved verbatim from the legacy implementation
        logging.info("Starting export of site insight metrics...")  # Trace operation start for ops visibility

        site_id = SiteMetricOperation._prompt_site_id()  # Bail out early if user cancels selection
        if not site_id:
            return

        site_name = SiteMetricOperation._resolve_site_name(site_id)  # Best-effort site label for filename and log lines
        filename = SiteMetricOperation._build_filename(
            site_id, site_name
        )  # Sanitized output path mirroring legacy naming

        print("! Refreshing available insight metrics from Mist API...")  # User-facing progress preserved verbatim
        _parent.InsightMetricsUtils.export_legacy()  # Refresh ConstInsightMetrics.csv cache before reading from it

        site_metrics = _parent.InsightMetricsUtils.get_by_scope(
            "site"
        )  # Pull the site-scope metric list from the refreshed cache
        if not site_metrics:  # Defensive: missing const file should not silently produce an empty CSV
            print(
                "! No metrics found for site scope. Check ConstInsightMetrics.csv file."
            )  # User-facing error preserved verbatim
            logging.error("No site-scope metrics found in const insight metrics")  # Persist failure cause in the log
            _parent.DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]  # Emit empty file for downstream consistency
            return

        all_data, metrics_retrieved = SiteMetricOperation._collect_metrics(  # Run the per-metric API loop
            site_id,
            site_name,
            site_metrics,
        )
        SiteMetricOperation._finalize(
            all_data, metrics_retrieved, filename, site_name
        )  # Flatten + save + summary print

    @staticmethod
    def _prompt_site_id() -> str | None:
        """Prompt the user for a site selection; return None when the user cancels."""
        site_id = _parent.PromptUtils.select_site()  # Existing prompt utility handles cancel / invalid input
        if not site_id:
            logging.error("No site selected. Exiting.")  # Match legacy error log message verbatim
            return None
        return site_id

    @staticmethod
    def _resolve_site_name(site_id: str) -> str:
        """Best-effort site-name lookup; fall back to site_id when API call fails."""
        try:
            response = _parent.mistapi.api.v1.sites.listSites(
                _parent.apisession, site_id
            )  # API call may raise on auth / network
            sites = _parent.mistapi.get_all(
                response=response, mist_session=_parent.apisession
            )  # Materialize paged result list
            return next(
                (site["name"] for site in sites if site["id"] == site_id), site_id
            )  # Match by id; fall back to id on miss
        except Exception:
            return site_id  # Silent fallback preserves legacy behaviour for offline / degraded API

    @staticmethod
    def _build_filename(site_id: str, site_name: str) -> str:
        """Build the sanitized output filename used by both CSV and DB exports."""
        sanitized = _parent.EnhancedSSHRunner.sanitize_filename(
            site_name or site_id
        )  # Reuse filename sanitizer from SSH runner
        return (
            f"SiteInsightMetrics_{sanitized}.csv"  # Filename pattern preserved verbatim from the legacy implementation
        )

    @staticmethod
    def _collect_metrics(
        site_id: str,
        site_name: str,
        site_metrics: list[str],
    ) -> tuple[list[dict], int]:
        """Iterate the metric list and collect any insight data the API returns."""
        all_insight_data: list[dict] = []  # Accumulator for every non-empty metric response
        metrics_retrieved = 0  # User-facing counter shown in the final summary line
        print(f"! Retrieving {len(site_metrics)} different site insight metrics...")  # Progress preserved verbatim
        for metric in site_metrics:  # One API call per metric name; individual failures must not abort the batch
            data = SiteMetricOperation._fetch_one_metric(site_id, site_name, metric)  # Returns enriched dict or None
            if data is not None:
                all_insight_data.append(data)  # Append the enriched per-metric record for export
                metrics_retrieved += 1  # Bump only on successful, non-empty payload
        return all_insight_data, metrics_retrieved

    @staticmethod
    def _fetch_one_metric(site_id: str, site_name: str, metric: str) -> dict | None:
        """Fetch a single site insight metric, returning the enriched dict or None on miss / error."""
        try:
            response = _parent.mistapi.api.v1.sites.insights.getSiteInsightMetrics(  # Single metric API call
                _parent.apisession,
                site_id,
                metric,
            )
            insight_data = (
                getattr(response, "data", response) or {}
            )  # Mistapi may return either raw dict or object with .data
            if not insight_data:
                logging.debug("No data available for metric: %s", metric)  # Trace empty payload at debug level only
                return None
            insight_data["metric_type"] = metric  # Annotate row with metric name for export readability
            insight_data["site_id"] = site_id  # Annotate row with site id for downstream joins
            insight_data["site_name"] = site_name  # Annotate row with site name for export readability
            logging.debug("Retrieved site insight data for metric: %s", metric)  # Trace success at debug level only
            return insight_data
        except Exception as exception:
            logging.debug(
                "Failed to get site insight data for metric %s: %s", metric, exception
            )  # Per-metric failure is non-fatal
            return None

    @staticmethod
    def _finalize(
        all_insight_data: list[dict],
        metrics_retrieved: int,
        filename: str,
        site_name: str,
    ) -> None:
        """Flatten, escape, and save collected data; emit summary user output."""
        try:
            if all_insight_data:
                processed = _parent.DataProcessingUtils.flatten_nested_fields(
                    all_insight_data
                )  # Flatten nested API objects
                processed = _parent.DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]  # CSV-safe text
                _parent.DataExporter.save_data_to_output(processed, filename)  # type: ignore[no-untyped-call]  # Write to disk / DB
                print(
                    f"! {metrics_retrieved} site insight metrics exported to {filename}"
                )  # User-facing summary preserved
                logging.info(  # Persist success summary at info level for ops visibility
                    "Exported %d site insight metrics for %s to %s",
                    metrics_retrieved,
                    site_name,
                    filename,
                )
                return
            print(f"! 0 insight metrics exported to {filename} (no data available)")  # User-facing summary preserved
            logging.warning("No insight data available for site %s", site_name)  # Distinguish empty result from error
            _parent.DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]  # Emit empty file for consistency
        except Exception as exception:
            print(f"! Error exporting site insight metrics: {exception}")  # User-facing error preserved verbatim
            logging.error(
                "Failed to export site insight metrics for %s: %s", site_name, exception
            )  # Persist failure cause
            _parent.DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]  # Always emit a file for consistency
