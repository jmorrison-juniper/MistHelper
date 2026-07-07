"""AuditAnalysisOps -- Menu #25 audit log analysis operations.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 12).
Fetches org audit logs, filters noise, and generates Mermaid + HTML reports.
All methods are static -- no state is kept on the class.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach module globals + helper classes without circular load.
import logging  # WHY: structured trace for API/analysis stages.
import os  # WHY: cross-platform path building for report output.

import mistapi  # WHY: audit-logs API + get_all pagination helper.

from src.audit.analyzer import AuditLogAnalyzer  # Audit log analysis engine for timeline/report generation.
from src.audit.filter import AuditLogFilter  # Audit log filtering to remove noise and system events.
from src.audit.renderer import AuditReportRenderer  # Mermaid timeline + HTML report rendering.
from src.audit.time_parser import TimeRangeParser  # Audit log time range parsing (7d, 4w, etc.).


class AuditAnalysisOps:
    """Menu #25: Audit Log Analysis operations."""

    @staticmethod
    def _prompt_audit_time_range_input() -> str:
        """Capture the audit-log time-range input string (test-mode fixed default or interactive prompt)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of IS_TEST_MODE + InputUtils.
        if mh.IS_TEST_MODE:  # Use a fixed time range so --test runs without interactive input.
            return "7d"  # Default to 7 days in test mode; skips the safe_input prompt.
        print("\nTime range examples: 7d, 4w, 3m, 1y, 6w-2w (6 weeks ago to 2 weeks ago)")
        return mh.InputUtils.safe_input("Enter time range [7d]: ", context="audit_analysis").strip()

    @staticmethod
    def _fetch_filtered_audit_entries(org_id, time_range):  # type: ignore[no-untyped-def]
        """Call Mist audit-logs API for the chosen org+time-range and return paginated entries (None on failure)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession module global.
        api_kwargs = TimeRangeParser.to_api_kwargs(time_range)  # Convert to API start/end params.
        try:
            logging.info(
                "Fetching audit logs for org %s with range %s",
                org_id,
                time_range.description,
            )  # Log before API call.
            response = mistapi.api.v1.orgs.logs.listOrgAuditLogs(mh.apisession, org_id, **api_kwargs, limit=1000)
            entries = mistapi.get_all(response=response, mist_session=mh.apisession) or []
            logging.debug("Retrieved %d raw audit log entries", len(entries))
            return entries
        except Exception as exc:  # noqa: BLE001  # API-side exceptions are logged and swallowed by design.
            logging.error("API call failed: %s", exc)  # Log API failure with context.
            return None

    @staticmethod
    def _render_audit_analysis_reports(analysis) -> None:  # type: ignore[no-untyped-def]
        """Render the analysis to both the Mermaid markdown file and the interactive HTML file."""
        renderer = AuditReportRenderer()  # Initialize report generator.
        md_path = os.path.join("data", "OrgAuditAnalysis.md")  # Mermaid timeline output path.
        renderer.render_mermaid(analysis, md_path)
        print(f"Mermaid report: {md_path}")
        html_path = os.path.join("data", "OrgAuditAnalysis.html")  # Interactive HTML output path.
        renderer.render_html(analysis, html_path)
        print(f"HTML report: {html_path}")

    @staticmethod
    def audit_log_analysis():  # type: ignore[no-untyped-def]
        """Fetch org audit logs, filter noise, generate analysis reports."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils + ConfigUtils helper classes.
        if mh.CacheUtils.fast_cache_hit("OrgAuditAnalysis.md"):  # Skip if cached report exists.
            return
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org context.
        if not org_id:
            return
        time_input = AuditAnalysisOps._prompt_audit_time_range_input()  # Test-mode default or interactive prompt.
        parser = TimeRangeParser()  # Parse human-readable time range.
        try:
            time_range = parser.parse(time_input)  # Convert input to TimeRange object.
        except ValueError as exc:
            logging.error("Invalid time range: %s", exc)
            return
        print(f"\nFetching audit logs for: {time_range.description}")
        entries = AuditAnalysisOps._fetch_filtered_audit_entries(org_id, time_range)  # API call + paginate.
        if entries is None:  # API failed (already logged inside helper).
            return
        print(f"Retrieved {len(entries)} raw entries")
        log_filter = AuditLogFilter()  # Noise filter.
        filtered, stats = log_filter.filter_with_stats(entries)  # Remove noise entries with stats.
        print(f"Filtered: {stats['kept_count']} kept, {stats['removed_count']} noise removed")
        analyzer = AuditLogAnalyzer()  # Pattern analyzer.
        analysis = analyzer.analyze(filtered, time_range.description)  # Detect patterns and anomalies.
        AuditAnalysisOps._render_audit_analysis_reports(analysis)  # Markdown + HTML reports.
