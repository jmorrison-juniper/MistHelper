"""InsightMetricsUtils -- Mist insight-metrics helpers.

Extracted from MistHelper.py during initiative 1014 (Cat E, position 11).
Canonical body lives here; MistHelper.py provides a top-level re-export
alias (``from src.analytics.insight_metrics_utils import InsightMetricsUtils``)
so historical ``MistHelper.InsightMetricsUtils`` / ``mh.InsightMetricsUtils``
callers keep working.

Cross-class references (``ConstDefinitionsExporter``) and the module-level
``apisession`` global are resolved lazily via
``importlib.import_module("MistHelper")`` inside method bodies to keep
FR-028 IG-health clean (no top-level MistHelper import statement).
"""

from __future__ import annotations  # WHY: PEP 604 unions in annotations.

import csv  # WHY: CSV parsing for ConstInsightMetrics.csv.
import importlib  # WHY: lazy MistHelper fetch of ConstDefinitionsExporter + apisession.
import logging  # WHY: debug/trace + failure reporting.
import os  # WHY: path join + existence checks for cache CSV.
from typing import Any  # WHY: dynamic payload annotations.


class InsightMetricsUtils:  # Insight-metrics helpers.
    """Utilities for working with Mist insight metrics.

    Provides functionality to export, filter, and normalize insight metrics data
    from the Mist API. All methods are static to avoid unnecessary instantiation.
    """

    @staticmethod
    def export_const_insight_metrics() -> None:  # Export const insight metrics.
        """Export available const insight metrics via the ConstDefinitionsExporter.

        Refreshes data/ConstInsightMetrics.csv so scope-filtering helpers can read it.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConstDefinitionsExporter + apisession.
        print("Export Available Insight Metrics:")  # User-facing banner for the const insight metrics export
        print("! Note: This function now uses the dynamic comprehensive const export system")  # Tell the user.
        print("! For best results, consider using Menu 82: Export All Const Definitions")  # Tell the user.
        logging.info("Legacy const insight metrics export called - using ConstDefinitionsExporter class")

        exporter = mh.ConstDefinitionsExporter(mh.apisession)  # type: ignore[no-untyped-call]
        exporter.export_all()  # Run the dynamic export.

        insight_metrics_file = os.path.join("data", "ConstInsightMetrics.csv")  # Expected output file.
        if os.path.exists(insight_metrics_file):  # File present.
            print("! ConstInsightMetrics.csv is available in the dynamic export results")  # Tell the user.
        else:
            print("! Warning: ConstInsightMetrics.csv was not created during dynamic export")

    @staticmethod
    def _should_skip_row(metric_name: str, scopes: str) -> bool:
        """Return True when a row is incomplete or uses a template-placeholder name."""
        if not metric_name or not scopes:  # Incomplete row — missing required fields
            return True
        return "{" in metric_name or "}" in metric_name  # Template placeholders are skip candidates

    @staticmethod
    def _row_matches_scope(row, normalized_target_scope: str) -> str | None:  # type: ignore[no-untyped-def]
        """Return ``metric_name`` when the row supports the target scope, else None to signal skip."""
        scopes = row.get("scopes", "")  # Scope string for this metric
        metric_name = row.get("metric_name", "")  # Display name
        if InsightMetricsUtils._should_skip_row(metric_name, scopes):  # Delegate skip-checks
            return None
        parsed_scopes = InsightMetricsUtils._parse_scopes(scopes)  # Tokenize scopes
        return metric_name if normalized_target_scope in parsed_scopes else None  # Match check

    @staticmethod
    def _collect_metrics_for_scope(reader, normalized_target_scope: str) -> list[str]:
        """Walk CSV rows and return metric names supporting the given scope."""
        matches = (InsightMetricsUtils._row_matches_scope(row, normalized_target_scope) for row in reader)  # Per-row
        return [name for name in matches if name]  # Drop None skips

    @staticmethod
    def get_by_scope(target_scope: str) -> list[str]:  # List metrics for a scope.
        """Read ConstInsightMetrics.csv and return metrics supporting ``target_scope``."""
        csv_path = os.path.join("data", "ConstInsightMetrics.csv")  # CSV path.
        normalized_target_scope = (target_scope or "").strip().lower()  # Normalize the target scope.
        try:
            if not os.path.exists(csv_path):  # File missing.
                logging.warning("ConstInsightMetrics.csv not found at %s", csv_path)  # Warn it is missing.
                return []  # Return empty.
            with open(csv_path, encoding="utf-8") as csvfile:  # Open the CSV.
                reader = csv.DictReader(csvfile)  # Parse rows.
                metrics_for_scope = InsightMetricsUtils._collect_metrics_for_scope(reader, normalized_target_scope)
            logging.debug(  # Trace the count.
                "Found %s metrics for scope '%s': %s", len(metrics_for_scope), target_scope, metrics_for_scope
            )
            return metrics_for_scope  # Return the metrics.
        except Exception as exception:  # Read failed.
            logging.error("Error reading ConstInsightMetrics.csv: %s", exception)  # Log the error.
            return []  # Return empty.

    @staticmethod
    def _parse_scopes(scopes_text: str) -> set[str]:  # Parse a scopes string.
        """Parse scope strings from CSV into normalized tokens."""
        if not scopes_text:  # Empty input.
            return set()  # Empty set.
        normalized = scopes_text.strip().lower()  # Lowercase it.
        normalized = normalized.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
        normalized = normalized.replace(";", ",")  # Normalize separators.
        tokens = [token.strip() for token in normalized.split(",") if token.strip()]  # Split into tokens.
        return set(tokens)  # Return the token set.

    @staticmethod
    def _log_normalization_summary(metric_type: str, normalized_data: dict[str, list]) -> None:  # type: ignore[type-arg]
        """Emit debug trace of normalized metric counts per bucket."""
        logging.debug(  # Trace the parse.
            "Normalized metric %s: %s summary, %s time series, %s results, %s sites",
            metric_type,  # Metric type label.
            len(normalized_data["summary"]),  # Summary row count.
            len(normalized_data["time_series"]),  # Time series row count.
            len(normalized_data["results"]),  # Results row count.
            len(normalized_data["sites_data"]),  # Sites row count.
        )

    @staticmethod
    def parse_to_normalized_data(metric_data: dict, org_id: str) -> dict[str, list]:  # type: ignore[type-arg]
        """Parse one insight metric into 'summary'/'time_series'/'results'/'sites_data' lists."""
        normalized_data: dict[str, list] = {"summary": [], "time_series": [], "results": [], "sites_data": []}  # type: ignore[type-arg]
        try:
            metric_type = metric_data.get("metric_type", "unknown")  # Read the metric type.
            normalized_data["summary"].append(  # Add summary record.
                InsightMetricsUtils._extract_summary(metric_data, org_id, metric_type)
            )
            normalized_data["time_series"].extend(  # Add time series rows.
                InsightMetricsUtils._extract_time_series(metric_data, org_id, metric_type)
            )
            normalized_data["results"] = InsightMetricsUtils._extract_results(metric_data, org_id, metric_type)
            normalized_data["sites_data"] = InsightMetricsUtils._extract_sites_data(metric_data, org_id, metric_type)
            InsightMetricsUtils._log_normalization_summary(metric_type, normalized_data)  # Trace counts.
        except Exception as exception:  # Parse failed.
            logging.error("Error parsing insight metric data: %s", exception)  # Log the error.
            logging.debug("Failed metric data structure: %s", metric_data)  # Trace the structure.
        return normalized_data  # Return normalized data.

    SUMMARY_SCALAR_FIELDS = (  # Scalar fields copied verbatim from the raw metric payload.
        "ap-health",
        "ap-redundancy",
        "capacity",
        "coverage",
        "num_active_wan_tunnels",
        "num_aps",
        "num_auth",
        "num_auth_failure",
        "num_auth_total",
        "num_client",
        "num_clients",
        "num_gateways",
        "num_mdm_client",
        "num_mxedges",
        "num_mxtunnels",
        "num_nac_clients",
        "num_switches",
        "num_wan_clients",
        "num_wired_clients",
        "successful-connect",
        "throughput",
        "time-to-connect",
    )

    @staticmethod
    def _build_summary_base(metric_data: dict, org_id: str, metric_type: str) -> dict:  # type: ignore[type-arg]
        """Build the fixed-key portion of the summary record (org/metric metadata)."""
        return {  # Header fields common to every metric type.
            "org_id": org_id,  # Tenant org id.
            "metric_type": metric_type,  # Logical metric name.
            "data_source": metric_data.get("data_source", ""),  # API data source.
            "start_time": metric_data.get("start", ""),  # Window start epoch.
            "end_time": metric_data.get("end", ""),  # Window end epoch.
            "interval_seconds": metric_data.get("interval", ""),  # Bucket interval.
            "limit": metric_data.get("limit", ""),  # Page limit echoed back.
            "total_sites": metric_data.get("total_sites", ""),  # Total sites count.
            "page": metric_data.get("page", ""),  # Current page index.
            "sle_category": metric_data.get("sle_category", ""),  # SLE category, if any.
            "original_metric": metric_data.get("original_metric", ""),  # Original metric key.
            "roaming": metric_data.get("roaming", ""),  # Roaming subtotal.
            "total": metric_data.get("total", ""),  # Total counter.
            "totalTunnelCount": metric_data.get("totalTunnelCount", ""),  # Tunnel count.
        }

    @staticmethod
    def _extract_summary(metric_data: dict, org_id: str, metric_type: str) -> dict:  # type: ignore[type-arg]
        """Extract summary data from metric."""
        summary_data = InsightMetricsUtils._build_summary_base(metric_data, org_id, metric_type)  # Header.
        for field_name in InsightMetricsUtils.SUMMARY_SCALAR_FIELDS:  # Append present scalars.
            if field_name in metric_data:  # Field present.
                summary_data[field_name] = metric_data[field_name]  # Copy the value.
        return summary_data  # Return the summary.

    @staticmethod
    def _extract_time_series(metric_data: dict, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Extract time series data from metric."""
        time_series_records = []  # type: ignore[var-annotated]

        rt_field = metric_data.get("rt", "")  # Read the rt field.
        if not InsightMetricsUtils._is_csv_string(rt_field):  # Not a CSV series.
            return time_series_records  # No time-series.

        timestamps = rt_field.split(",")  # Split the timestamps.
        time_series_fields = ["num_clients", "num_aps", "num_gateways", "num_switches", "num_mxedges", "num_mxtunnels"]

        for field_name in time_series_fields:  # Walk each field.
            field_data = metric_data.get(field_name, "")  # Read the field.
            time_series_records.extend(  # Append this field's time-series points (empty when not a CSV series)
                InsightMetricsUtils._field_time_series_points(field_name, field_data, timestamps, org_id, metric_type)
            )

        return time_series_records  # Return the series.

    @staticmethod
    def _is_csv_string(value: Any) -> bool:  # Detect a non-empty comma-separated string
        """Return True when value is a non-empty string containing at least one comma (a CSV series)."""
        return bool(value and isinstance(value, str) and "," in value)  # Truthy + str + contains a comma

    @staticmethod
    def _field_time_series_points(
        field_name: str,
        field_data: Any,
        timestamps: list[str],
        org_id: str,
        metric_type: str,
    ) -> list[dict]:  # type: ignore[type-arg]
        """Pair one CSV field's values with the timestamps into time-series point records (skipping empties)."""
        if not InsightMetricsUtils._is_csv_string(field_data):  # Not a CSV series.
            return []  # No points for this field.
        values = field_data.split(",")  # Split the values.
        points = []  # Collect this field's points.
        for index, (timestamp, value) in enumerate(zip(timestamps, values, strict=False)):  # Pair timestamp+value
            if value and value != "None":  # Skip empty/placeholder values.
                points.append(  # Collect the point.
                    {
                        "org_id": org_id,
                        "metric_type": metric_type,
                        "timestamp": timestamp.strip(),
                        "value": value.strip(),
                        "value_type": field_name,
                        "sequence_order": index,
                    }
                )
        return points  # Time-series points for this field.

    @staticmethod
    def _parse_results_key(key: str) -> tuple[str, str] | None:
        """Split a 'results_<index>_<field>' key into (index, field); return None if pattern fails."""
        if not (key.startswith("results_") and "_" in key):  # Only results_* keys are valid here.
            return None  # Reject non-matching keys.
        parts = key.split("_", 2)  # Split into at most 3 parts: ['results', index, field].
        if len(parts) < 3:  # Too few parts -- no field component.
            return None  # Reject malformed keys.
        return parts[1], parts[2]  # (index, field).

    @staticmethod
    def _ensure_result_row(
        results_data: list[dict],  # type: ignore[type-arg]
        result_index,  # type: ignore[no-untyped-def]
        org_id: str,
        metric_type: str,
    ) -> dict:
        """Return the existing row matching ``result_index`` from ``results_data`` or append+return a new one."""
        existing = next((r for r in results_data if r["result_index"] == result_index), None)  # Lookup
        if existing is not None:  # Reuse existing row
            return existing
        new_row = {  # New row with normalized index
            "org_id": org_id,
            "metric_type": metric_type,
            "result_index": int(result_index) if result_index.isdigit() else result_index,
        }
        results_data.append(new_row)  # Append into caller-owned list
        return new_row

    @staticmethod
    def _extract_results(metric_data: dict, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Extract results array data from metric."""
        results_data: list[dict] = []  # Accumulator
        for key, value in metric_data.items():  # Walk metric fields
            parsed = InsightMetricsUtils._parse_results_key(key)  # Parse the key shape
            if parsed is None:  # Not a results_* field
                continue
            result_index, result_field = parsed  # Unpack
            row = InsightMetricsUtils._ensure_result_row(results_data, result_index, org_id, metric_type)
            row[result_field] = value  # Set the field on the row
        return results_data

    @staticmethod
    def _extract_sites_data(metric_data: dict, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Extract sites data from metric."""
        sites_data = metric_data.get("sites_data", [])  # Read sites data.
        sites_records = InsightMetricsUtils._extract_sites_list(sites_data, org_id, metric_type)  # List-payload rows
        InsightMetricsUtils._merge_keyed_sites(metric_data, org_id, metric_type, sites_records)  # Merge sites_data_*
        return sites_records  # Return the sites.

    @staticmethod
    def _extract_sites_list(sites_data: Any, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Build site rows from a list-payload sites_data, tagging each dict site with org_id/metric_type."""
        sites_records = []  # Collect site rows.
        if isinstance(sites_data, list):  # List payload.
            for site_data in sites_data:  # Walk sites.
                if isinstance(site_data, dict):  # Dict site.
                    site_record = {"org_id": org_id, "metric_type": metric_type}  # Tag the site.
                    site_record.update(site_data)  # Merge the data.
                    sites_records.append(site_record)  # Collect the row.
        return sites_records  # Site rows from the list payload.

    @staticmethod
    def _merge_keyed_sites(
        metric_data: dict,  # type: ignore[type-arg]
        org_id: str,
        metric_type: str,
        sites_records: list[dict],  # type: ignore[type-arg]
    ) -> None:
        """Merge flattened sites_data_* keys into sites_records (find-or-create each site by index)."""
        for key, value in metric_data.items():  # Walk metric fields.
            parsed = InsightMetricsUtils._parse_keyed_site_field(key)  # (site_index, site_field) or None to skip
            if parsed is None:  # Not a sites_data_* field.
                continue  # Skip it.
            site_index, site_field = parsed  # Unpack the parsed index/field.
            site = InsightMetricsUtils._find_or_create_site(sites_records, site_index, org_id, metric_type)  # Find row
            site[site_field] = value  # Set the field.

    @staticmethod
    def _parse_keyed_site_field(key: str) -> tuple[str, str] | None:  # Parse a sites_data_* flattened key
        """Return (site_index, site_field) for a sites_data_* key, or None when the key is not a valid site field."""
        if not (key.startswith("sites_data_") and "_" in key):  # Only sites_data_* keys.
            return None  # Not a site field.
        parts = key.split("_", 2)  # Split the key.
        if len(parts) < 3:  # Too few parts.
            return None  # Skip it.
        site_index = parts[2]  # Site index.
        site_field = parts[3] if len(parts) > 3 else "value"  # Site field (defaults to 'value').
        return site_index, site_field  # Parsed index and field.

    @staticmethod
    def _find_or_create_site(
        sites_records: list[dict],  # type: ignore[type-arg]
        site_index: str,
        org_id: str,
        metric_type: str,
    ) -> dict:  # type: ignore[type-arg]
        """Return the existing site row matching site_index+metric_type, or create, append, and return a new one."""
        existing_site = next(  # Find existing site.
            (s for s in sites_records if s.get("site_index") == site_index and s.get("metric_type") == metric_type),
            None,
        )
        if existing_site is not None:  # Found a matching row.
            return existing_site  # Reuse it.
        new_site = {"org_id": org_id, "metric_type": metric_type, "site_index": site_index}  # Start a new site.
        sites_records.append(new_site)  # Collect it.
        return new_site  # The newly created row.
