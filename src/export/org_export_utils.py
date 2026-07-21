"""OrgExportUtils -- generic org-level data export helpers.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 47).
Groups org-level export helpers (SLE, insight metrics, NAC, audit logs, etc.)
under a single static-method facade. All methods are static -- no state is kept
on the class. Callers continue to reach it through the
``MistHelper.OrgExportUtils`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper globals without circular load.
import logging  # WHY: structured trace for export lifecycle events.
import time  # WHY: sites_sle_summary progress timer.
from typing import Any  # WHY: raw insight rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for org export endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.time.time_utils import TimeUtils  # WHY: 1014 P6 direct import (FR-005).

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.


class OrgExportUtils:
    """Centralized organization-level data export utilities.

    Groups all export_org_* functions for better code organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    # Org-level switch/gateway insight metrics accept only byte-throughput choices. The count-type
    # choices in the constants ('total_*_count', 'num_used_*') are valid solely at site/switch scope
    # and return HTTP 400 "Bad Syntax" at org scope, so org expansion is restricted to this set.
    _ORG_VALID_METRIC_CHOICES = ("bytes", "rx_bytes", "tx_bytes")  # Org-scope-valid parameterized metric choices

    @staticmethod
    def export_data(api_call, data_type, sort_key="name", limit=1000, **api_kwargs):  # Export an org endpoint.
        """Generic org-data export: build Org<DataType>.csv from `api_call`, pass `limit`/extras as API kwargs."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        logging.info("Starting export of organization %s...", data_type)  # Log start.

        # Create filename from data_type
        safe_data_type = data_type.replace(" ", "").replace("-", "").title()  # Sanitize for filename.
        filename = f"Org{safe_data_type}.csv"  # Build the CSV name.

        fetcher_kwargs = dict(api_kwargs)  # Copy extra kwargs.
        if limit is not None:  # Limit provided.
            fetcher_kwargs["limit"] = limit  # Set the page limit.

        mh.APIDataFetcher(  # Fetch and write.
            title=f"Organization {data_type.title()}:",
            api_call=api_call,
            filename=filename,
            sort_key=sort_key,
            **fetcher_kwargs,
        ).execute()

    @staticmethod
    def _collect_one_sle_type(
        org_id: str,
        sle_type: str,
        all_sites_sle_data: list,
    ) -> None:
        """Fetch sites-SLE rows for one type and append (tagged) into the shared accumulator."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession global.
        try:
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(  # Call the SLE API for this type.
                mh.apisession, org_id, sle=sle_type, duration="7d", limit=1000
            )
            sites_sle_data = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all rows.
            for site_data in sites_sle_data:  # Tag each row with its SLE type.
                site_data["sle_type"] = sle_type  # Record the SLE type on the row.
                all_sites_sle_data.append(site_data)  # Collect into accumulator.
            logging.debug("Retrieved SLE data for %s sites with SLE type: %s", len(sites_sle_data), sle_type)
        except Exception as exception:  # Fetch failed -- skip this type but continue overall.
            logging.warning("Failed to get sites SLE data for type %s: %s", sle_type, exception)  # Warn and skip.

    @staticmethod
    def _persist_sites_sle_summary(all_sites_sle_data: list) -> None:
        """Persist aggregated sites-SLE rows to OrgSitesSLESummary.csv (or write empty + warn)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if all_sites_sle_data:  # Have data -- flatten + write + tell user.
            processed = DataProcessingUtils.flatten_nested_fields(all_sites_sle_data)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]  # CSV-safe.
            mh.DataExporter.write_with_format_selection(processed, "OrgSitesSLESummary.csv")  # type: ignore[no-untyped-call]
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! %d sites SLE summary exported to OrgSitesSLESummary.csv", len(processed))  # Tell the user.
            logging.info("Exported %s sites SLE summary to OrgSitesSLESummary.csv", len(processed))  # Log count.
            return  # Done.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.warning(
            "! 0 sites SLE summary exported to OrgSitesSLESummary.csv (no data available)"
        )  # Tell user zero.
        logging.warning("No sites SLE data available for organization")  # Warn no data.
        mh.DataExporter.write_with_format_selection([], "OrgSitesSLESummary.csv")  # type: ignore[no-untyped-call]

    @staticmethod
    def _gather_all_sites_sle(org_id: str, sle_types: list, emitter: Any) -> tuple[list, int]:
        """Walk SLE types, accumulate rows, tick progress per type; return (rows, items_done)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ProgressContext class.
        all_sites_sle_data: list = []  # Accumulator for SLE rows across types.
        items_done = 0  # Items processed counter.
        for sle_type in sle_types:  # Fetch each SLE type.
            OrgExportUtils._collect_one_sle_type(org_id, sle_type, all_sites_sle_data)  # Fetch + tag + accumulate.
            items_done += 1  # Count this item regardless of success/failure.
            if emitter:  # Emitter present -- tick progress for UI.
                emitter.emit_progress_tick(
                    mh.ProgressContext("67", "sites_sle_summary", len(sle_types)),
                    sle_type,
                    items_done,
                    len(sle_types) - items_done,
                )
        return all_sites_sle_data, items_done  # Caller persists + emits completion.

    @staticmethod
    def sites_sle_summary():  # Export sites SLE summary.
        """Export SLE summary metrics for all sites in the organization to OrgSitesSLESummary.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils, PROGRESS_EMITTER, ProgressContext.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Export Organization Sites SLE Summary:")  # Header.
        logging.info("Starting export of sites SLE summary...")  # Log start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        sle_types = ["wifi", "wired", "wan"]  # SLE types to fetch.
        emitter = mh.PROGRESS_EMITTER  # Progress emitter handle.
        if emitter:  # Emitter present.
            emitter.emit_progress_start("67", "sites_sle_summary", len(sle_types))  # Signal progress start.
        op_start = time.time()  # Start the timer.
        all_sites_sle_data, items_done = OrgExportUtils._gather_all_sites_sle(  # Walk types + tick.
            org_id, sle_types, emitter
        )
        OrgExportUtils._persist_sites_sle_summary(all_sites_sle_data)  # Write CSV (or empty placeholder).
        if emitter:  # Emitter present.
            emitter.emit_progress_complete(  # Signal progress complete.
                mh.ProgressContext("67", "sites_sle_summary", len(sle_types)),
                items_done,
                False,
                time.time() - op_start,
            )

    @staticmethod
    def _metric_choice_list(definition: Any) -> list[str]:  # Choices for one metric definition.
        """Return the 'metric' sub-parameter choices for one insight-metric definition, or []."""
        if not isinstance(definition, dict):  # Definition payload must be a mapping
            return []  # No choices to extract
        params = definition.get("params")  # Parameter specs block (may be absent)
        if not isinstance(params, dict):  # Params must be a mapping to hold a 'metric' spec
            return []  # No choices to extract
        metric_param = params.get("metric")  # The 'metric' sub-parameter spec, if any
        if not isinstance(metric_param, dict):  # Spec must be a mapping to hold choices
            return []  # No choices to extract
        choices = metric_param.get("choices")  # Allowed values the API enumerates for this metric
        return list(choices) if isinstance(choices, list) else []  # Normalize to a plain list

    @staticmethod
    def _org_valid_choices(choices: list[str]) -> list[str]:  # Keep org-scope-valid choices only.
        """Filter metric choices down to the byte-throughput set the org-scope endpoint accepts."""
        return [choice for choice in choices if choice in OrgExportUtils._ORG_VALID_METRIC_CHOICES]  # Drop count-type

    @staticmethod
    def _extract_metric_choices(definitions: Any) -> dict[str, list[str]]:  # Build the parameterized map.
        """Extract {metric_name: [choices]} from a listInsightMetrics definitions mapping."""
        parameterized: dict[str, list[str]] = {}  # Accumulates metrics that require a 'metric' choice
        if not isinstance(definitions, dict):  # Guard against unexpected payload shapes
            return parameterized  # Nothing to extract
        for metric_name, definition in definitions.items():  # Inspect every metric definition
            declared = OrgExportUtils._metric_choice_list(definition)  # All choices the metric declares
            choices = OrgExportUtils._org_valid_choices(declared)  # Restrict to org-scope-valid choices
            if choices:  # Only metrics with at least one org-valid choice are expandable here
                parameterized[metric_name] = choices  # Record the org-valid sub-metric choices
        return parameterized  # Completed metric -> choices mapping

    @staticmethod
    def _load_parameterized_metric_choices() -> dict[str, list[str]]:  # Discover parameterized metrics.
        """Return {metric_name: [choices]} for org insight metrics requiring a 'metric' sub-parameter.

        Some org insight metrics (e.g. switch-metrics, gateway-metrics) declare a 'metric'
        query parameter in their constants definition. getOrgSle cannot supply it, so a bare
        call returns HTTP 400 "Bad Syntax". Reading the live constants lets callers expand each
        such metric into one request per valid choice instead of failing.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession global.
        logging.info("Loading parameterized insight-metric choices from Mist constants...")  # Trace the lookup
        try:  # The constants call may fail offline -> degrade to no expansion
            response = mistapi.api.v1.const.insight_metrics.listInsightMetrics(
                mh.apisession
            )  # GET /const/insight_metrics
            definitions = getattr(response, "data", response) or {}  # Unwrap to the metric -> definition map
        except Exception as exception:  # Any failure simply disables expansion this run
            logging.error("Failed to load insight-metric constants for parameter expansion: %s", exception)  # Trace
            return {}  # No parameterized map available
        parameterized = OrgExportUtils._extract_metric_choices(definitions)  # Pull choices from the definitions
        logging.debug("Discovered %s parameterized org insight metrics", len(parameterized))  # Trace the count
        return parameterized  # Map of metric -> required choices

    @staticmethod
    def _fetch_single_metric_choice(
        org_id: str, metric: str, choice: str, duration: str
    ) -> dict[str, Any] | None:  # One (metric, choice) GET.
        """Issue the org-insight GET for one (metric, choice) pair; return a tagged record or None."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession global.
        uri = f"/api/v1/orgs/{org_id}/insights/{metric}"  # Org insight endpoint for this parameterized metric
        query = {"metric": choice, "duration": duration}  # Required 'metric' choice plus the lookback window
        logging.debug("Fetching parameterized metric %s with metric=%s", metric, choice)  # Trace the attempt
        session = mh.apisession  # Local handle so the Any | None global can be narrowed below
        if session is None:  # No authenticated session available (defensive guard)
            logging.error("No API session available to fetch parameterized metric %s", metric)  # Trace the gap
            return None  # Cannot fetch without a session
        try:  # Per-choice failures must not abort the whole export
            response = session.mist_get(uri=uri, query=query)  # Low-level GET (SDK cannot pass query 'metric')
            payload = getattr(response, "data", None)  # Unwrap the response data payload
        except Exception as exception:  # Network/HTTP failure for this specific choice
            logging.debug("Failed to fetch %s metric=%s: %s", metric, choice, exception)  # Trace the miss
            return None  # Signal failure to the caller
        if not payload:  # Empty payload means no data for this choice
            return None  # Signal empty to the caller
        record = dict(payload) if isinstance(payload, dict) else {"results": payload}  # Normalize to a dict row
        record["metric_type"] = f"{metric}:{choice}"  # Tag the composite metric type for the export
        record["org_id"] = org_id  # Tag the owning org
        record["metric_param"] = choice  # Tag which sub-metric this row represents
        return record  # Completed tagged record

    @staticmethod
    def _fetch_parameterized_org_metric(
        org_id: str, metric: str, choices: list[str], duration: str
    ) -> tuple[list[dict[str, Any]], int, int]:  # Expand a metric across its choices.
        """Fetch one parameterized org insight metric across each required 'metric' choice.

        getOrgSle cannot pass the required 'metric' query parameter, so this issues the GET
        directly for each choice. Returns (records, retrieved, failed).
        """
        records: list[dict[str, Any]] = []  # Collected per-choice time-series records
        retrieved = 0  # Successful choice fetches
        failed = 0  # Failed or empty choice fetches
        for choice in choices:  # Each valid sub-metric value (e.g. bytes, rx_bytes, total_port_count)
            record = OrgExportUtils._fetch_single_metric_choice(org_id, metric, choice, duration)  # One GET
            if record:  # Choice returned a usable payload
                records.append(record)  # Keep the tagged record
                retrieved += 1  # Count the success
            else:  # No data or the request failed
                failed += 1  # Count the miss
        logging.debug("Parameterized metric %s: %s retrieved, %s failed", metric, retrieved, failed)  # Trace totals
        return records, retrieved, failed  # Aggregate result for this metric

    @staticmethod
    def _insight_is_worst_sites_metric(metric: str) -> bool:
        """Return True when a metric needs site-level SLE analysis (issue #470: hoisted to keep dispatch CC low)."""
        return "worst-sites" in metric or metric in (
            "sites-sle",
            "sites-sle-filtered",
        )  # These metrics require getOrgSitesSle rather than the plain getOrgSle endpoint.

    @staticmethod
    def _insight_build_sites_result(
        org_id: str, metric: str, sle_category: str, sites_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build one aggregated site-SLE insight result row for a metric+category pair."""
        return {  # One aggregated record describing this metric/category combination.
            "metric_type": f"{metric}_{sle_category}",  # Composite metric+category identifier.
            "org_id": org_id,  # Tag the owning org.
            "sle_category": sle_category,  # Record which SLE category this row covers.
            "data_source": "sites_sle_analysis",  # Mark the provenance of this aggregated row.
            "total_sites": len(sites_data),  # How many sites contributed to this category.
            "sites_data": sites_data,  # The raw per-site SLE rows for downstream normalization.
            "original_metric": metric,  # Preserve the requesting metric name.
        }

    @staticmethod
    def _insight_fetch_one_sle_category(org_id: str, metric: str, sle_category: str) -> dict[str, Any] | None:
        """Fetch one SLE category's site data; return aggregated result row, or None when empty/failed."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession global.
        try:  # Isolate this category so one failure doesn't abort the others.
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(  # Call the sites-SLE API for this category.
                mh.apisession, org_id, sle=sle_category, duration="7d", limit=1000
            )
            sites_data = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all site rows.
            if not sites_data:  # Category empty -- log and return None.
                logging.debug("No sites data for insight metric: %s with SLE: %s", metric, sle_category)
                return None  # No data for this category.
            logging.debug(  # Trace the successful category fetch with its site count.
                "Got %s sites for insight metric: %s SLE: %s", len(sites_data), metric, sle_category
            )
            return OrgExportUtils._insight_build_sites_result(org_id, metric, sle_category, sites_data)
        except Exception as sites_error:  # Category fetch failed; log and report None without counting a failure.
            logging.debug("Failed to get sites data for metric '%s' SLE '%s': %s", metric, sle_category, sites_error)
            return None  # Treat the failed category as no data.

    @staticmethod
    def _insight_fetch_worst_sites_sle(org_id: str, metric: str) -> tuple[list[dict[str, Any]], int, int]:
        """Fetch one site-SLE metric across wifi/wan/wired categories; return (records, retrieved, failed)."""
        records: list[dict[str, Any]] = []  # Aggregated per-category insight results for this metric.
        retrieved = 0  # Count of categories that returned usable site data.
        for sle_category in ("wifi", "wan", "wired"):  # The three SLE service categories to analyze.
            result = OrgExportUtils._insight_fetch_one_sle_category(org_id, metric, sle_category)  # One category fetch.
            if result is not None:  # The category returned usable data.
                records.append(result)  # Collect the aggregated category result.
                retrieved += 1  # Count this category as a successful retrieval.
        return records, retrieved, 0  # Failures are absorbed per-category, so the failed count stays zero here.

    @staticmethod
    def _insight_fetch_default_metric(org_id: str, metric: str) -> tuple[list[dict[str, Any]], int, int]:
        """Fetch one ordinary metric via getOrgSle; return (records, retrieved, failed)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession global.
        response = mistapi.api.v1.orgs.insights.getOrgSle(
            mh.apisession, org_id, metric, duration="7d"
        )  # Direct SLE GET.
        insight_data = getattr(response, "data", response) or {}  # Unwrap the response payload; default to empty.
        if insight_data:  # The metric returned a usable payload.
            insight_data["metric_type"] = metric  # Tag the metric name onto the payload.
            insight_data["org_id"] = org_id  # Tag the owning org onto the payload.
            logging.debug("Successfully retrieved org insight data for metric: %s", metric)  # Trace the success.
            return [insight_data], 1, 0  # One retrieved record, no failures.
        logging.debug("No data available for org metric: %s", metric)  # Trace the empty payload.
        return [], 0, 1  # No data counts as a single failed metric (matches the original behavior).

    @staticmethod
    def _insight_fetch_one_metric(
        org_id: str, metric: str, parameterized_metrics: dict[str, list[str]]
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Dispatch one metric to the right fetch strategy; return (records, retrieved, failed)."""
        try:  # Any metric-level failure is caught here so the overall loop continues.
            logging.debug("Attempting to retrieve org insight metric: %s", metric)  # Trace the attempt.
            if metric in parameterized_metrics:  # Parameterized metric -> expand across its required 'metric' choices.
                records, ok, fail = OrgExportUtils._fetch_parameterized_org_metric(  # One GET per valid choice.
                    org_id, metric, parameterized_metrics[metric], "7d"
                )
                logging.debug("Expanded parameterized metric %s into %s records", metric, len(records))  # Trace expand.
                return records, ok, fail  # Hand back the per-choice aggregate.
            if OrgExportUtils._insight_is_worst_sites_metric(metric):  # Site-SLE metric -> per-category analysis.
                return OrgExportUtils._insight_fetch_worst_sites_sle(org_id, metric)  # Fetch across wifi/wan/wired.
            return OrgExportUtils._insight_fetch_default_metric(org_id, metric)  # Ordinary metric -> single getOrgSle.
        except Exception as metric_error:  # The metric failed entirely; count it and keep going.
            logging.debug("Failed to get org insight data for metric '%s': %s", metric, metric_error)  # Trace failure.
            return [], 0, 1  # No records, one failed metric.

    @staticmethod
    def _insight_fetch_sites_sle_summary(org_id: str) -> tuple[list[dict[str, Any]], int, int]:
        """Fetch the org-wide sites SLE summary; return (records, retrieved, failed)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession global.
        try:  # Isolate the summary fetch so its failure doesn't abort the export.
            logging.debug("Attempting to retrieve org sites SLE summary")  # Trace the attempt.
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(
                mh.apisession, org_id, duration="7d", limit=100
            )  # GET.
            sites_data = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all summary rows.
            if sites_data:  # The summary returned site rows.
                for item in sites_data:  # Tag each row with its metric type and org.
                    item["metric_type"] = "org_sites_sle_summary"  # Mark these as the sites SLE summary.
                    item["org_id"] = org_id  # Tag the owning org.
                logging.debug("Successfully retrieved org sites SLE data for %s sites", len(sites_data))  # Trace count.
                return list(sites_data), 1, 0  # All rows as records; counts as one successful retrieval.
            return [], 0, 0  # No summary data; neither retrieved nor failed (matches original).
        except Exception as sites_error:  # Summary fetch failed.
            logging.debug("Failed to get org sites SLE summary: %s", sites_error)  # Trace the failure.
            return [], 0, 1  # Count the summary as a single failure.

    @staticmethod
    def _insight_collect_all_metrics(
        org_id: str, org_metrics: list[str], parameterized_metrics: dict[str, list[str]]
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Retrieve every org-scope metric plus the sites SLE summary; return (all_records, retrieved, failed)."""
        all_insight_data: list[dict[str, Any]] = []  # Accumulate every metric's records.
        metrics_retrieved = 0  # Running count of successful retrievals.
        metrics_failed = 0  # Running count of failed or empty retrievals.
        for metric in org_metrics:  # Process each org-scoped metric independently.
            records, retrieved, failed = OrgExportUtils._insight_fetch_one_metric(  # Dispatch to the right strategy.
                org_id, metric, parameterized_metrics
            )
            all_insight_data.extend(records)  # Collect this metric's records.
            metrics_retrieved += retrieved  # Fold in its successful count.
            metrics_failed += failed  # Fold in its failed count.
        summary_records, summary_ok, summary_fail = OrgExportUtils._insight_fetch_sites_sle_summary(org_id)  # Summary.
        all_insight_data.extend(summary_records)  # Collect the summary rows.
        metrics_retrieved += summary_ok  # Fold in the summary success count.
        metrics_failed += summary_fail  # Fold in the summary failure count.
        return all_insight_data, metrics_retrieved, metrics_failed  # Hand the aggregate back to the orchestrator.

    @staticmethod
    def _insight_normalize_records(all_insight_data: list[dict[str, Any]], org_id: str) -> dict[str, list]:  # type: ignore[type-arg]
        """Normalize raw insight rows into the four output buckets (summary, time_series, results, sites_data)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InsightMetricsUtils helper.
        buckets: dict[str, list] = {  # type: ignore[type-arg]  # One list per normalized output file.
            "summary": [],  # Rows destined for OrgMetricsSummary.csv.
            "time_series": [],  # Rows destined for OrgMetricsTimeSeries.csv.
            "results": [],  # Rows destined for OrgMetricsResults.csv.
            "sites_data": [],  # Rows destined for OrgSitesData.csv.
        }
        for metric_data in all_insight_data:  # Normalize each raw metric record.
            normalized = mh.InsightMetricsUtils.parse_to_normalized_data(
                metric_data, org_id
            )  # Split into the 4 buckets.
            for key in buckets:  # Fold each bucket's rows into the accumulator.
                buckets[key].extend(normalized[key])  # Collect this record's contribution to the bucket.
        return buckets  # Return the four populated buckets.

    @staticmethod
    def _insight_export_normalized(all_insight_data: list[dict[str, Any]], org_id: str, metrics_retrieved: int) -> None:
        """Normalize the insight rows and export them to the four normalized CSVs plus the legacy combined file."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter helpers.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Parsing metrics into normalized data structures...")  # Tell the user normalization is starting.
        buckets = OrgExportUtils._insight_normalize_records(all_insight_data, org_id)  # Build the 4 output buckets.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Exporting to normalized CSV files...")  # Tell the user the writes are starting.
        outputs = [  # Drive the four normalized writes from one table to avoid repeated blocks.
            (buckets["summary"], "OrgMetricsSummary.csv", "summary"),  # Summary file + its label.
            (buckets["time_series"], "OrgMetricsTimeSeries.csv", "time series"),  # Time-series file + label.
            (buckets["results"], "OrgMetricsResults.csv", "results"),  # Results file + label.
            (buckets["sites_data"], "OrgSitesData.csv", "sites"),  # Sites file + label.
        ]
        for rows, filename, label in outputs:  # Write each normalized bucket to its CSV.
            processed = DataProcessingUtils.escape_multiline(rows)  # type: ignore[no-untyped-call]  # Escape newlines.
            mh.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]  # Write it.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  !? %d %s records -> %s", len(processed), label, filename)  # Report row count.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "\n! Successfully exported %d organization insight metrics to 4 normalized CSV files",
            metrics_retrieved,
        )  # Summarize the export for the user.
        logging.info(  # Log the export totals for traceability.
            "Exported %s org insight data points from %s metrics to normalized CSV files",
            len(all_insight_data),
            metrics_retrieved,
        )
        OrgExportUtils._insight_write_combined(all_insight_data)  # Also write the combined compatibility file.

    @staticmethod
    def _insight_write_combined(all_insight_data: list[dict[str, Any]]) -> None:
        """Write the flattened combined insight file (OrgInsightMetrics_Legacy.csv) for backward compatibility."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter helpers.
        processed_combined = DataProcessingUtils.flatten_nested_fields(all_insight_data)  # Flatten for combined.
        processed_combined = DataProcessingUtils.escape_multiline(processed_combined)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(processed_combined, "OrgInsightMetrics_Legacy.csv")  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("  !? Legacy format maintained -> OrgInsightMetrics_Legacy.csv")  # Confirm the file write.

    @staticmethod
    def _insight_write_empty_outputs(include_legacy: bool = True) -> None:
        """Write empty normalized CSVs so downstream consumers always see the expected files."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        files = [  # The four normalized output files are always written.
            "OrgMetricsSummary.csv",
            "OrgMetricsTimeSeries.csv",
            "OrgMetricsResults.csv",
            "OrgSitesData.csv",
        ]
        if include_legacy:  # The no-data and error paths also write the legacy combined file.
            files.append("OrgInsightMetrics_Legacy.csv")  # Include the legacy file when requested.
        for filename in files:  # Write an empty dataset to each output file.
            mh.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # Empty write.

    @staticmethod
    def _insight_setup_or_empty() -> list[str] | None:
        """Refresh and load org-scope metrics; write empty outputs and return None when none exist."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InsightMetricsUtils helper.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Export Organization Insight Metrics (Normalized):")  # Header for the operation.
        logging.info("Starting export of organization insight metrics with normalized structure...")  # Log start.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Refreshing available insight metrics from Mist API...")  # Tell the user about the refresh.
        mh.InsightMetricsUtils.export_const_insight_metrics()  # Refresh ConstInsightMetrics.csv before scope filtering.
        org_metrics = mh.InsightMetricsUtils.get_by_scope("org")  # Load the metrics that support org scope.
        if not org_metrics:  # No org-scope metrics are available.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No metrics found for org scope. Check ConstInsightMetrics.csv file.")  # Tell the user.
            logging.error("No org-scope metrics found in const insight metrics")  # Log the error condition.
            OrgExportUtils._insight_write_empty_outputs(include_legacy=False)  # Write the 4 empty normalized files.
            return None  # Signal the orchestrator to abort.
        return org_metrics  # Hand the org-scope metric list back to the orchestrator.

    @staticmethod
    def _insight_report_totals(metrics_retrieved: int, metrics_failed: int) -> None:
        """Print and log the retrieval totals for the insight-metrics run."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! Metric retrieval completed: %d successful, %d failed", metrics_retrieved, metrics_failed
        )  # Tell user.
        logging.info(
            "Org insight metrics: %s retrieved successfully, %s failed", metrics_retrieved, metrics_failed
        )  # Log the retrieval totals for traceability.

    @staticmethod
    def insight_metrics():
        """Export organization-wide insight metrics to normalized CSV files."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        org_metrics = OrgExportUtils._insight_setup_or_empty()  # Refresh + load org metrics (None means abort early).
        if org_metrics is None:  # Setup wrote empty outputs and signaled there is nothing to export.
            return  # Abort the export.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org to query.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! Retrieving %d different organization insight metrics...", len(org_metrics)
        )  # Tell the user the count.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Processing each metric individually with proper error handling...")  # Explain per-metric.
        parameterized_metrics = OrgExportUtils._load_parameterized_metric_choices()  # Metrics needing a 'metric' param.
        try:  # Guard the whole fetch-and-export so a failure still leaves consistent empty outputs.
            all_insight_data, metrics_retrieved, metrics_failed = OrgExportUtils._insight_collect_all_metrics(  # Fetch.
                org_id, org_metrics, parameterized_metrics
            )
            OrgExportUtils._insight_report_totals(metrics_retrieved, metrics_failed)  # Report + log the totals.
            if all_insight_data:  # At least one metric returned data.
                OrgExportUtils._insight_export_normalized(all_insight_data, org_id, metrics_retrieved)  # Write CSVs.
            else:  # Every metric failed or returned empty.
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.warning("! 0 organization insight metrics exported (no data available)")  # Tell the user zero.
                logging.warning("No org insight data available - all metrics failed or returned empty")  # Warn no data.
                OrgExportUtils._insight_write_empty_outputs(include_legacy=True)  # Write the 5 empty files.
        except Exception as exception:  # The export failed unexpectedly.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("! Error exporting organization insight metrics: %s", exception)  # Tell the user.
            logging.error("Failed to export org insight metrics: %s", exception)  # Log the failure with context.
            OrgExportUtils._insight_write_empty_outputs(include_legacy=True)  # Write the 5 empty files on error.

    @staticmethod
    def _nac_clients():  # Export NAC clients.
        """Export NAC clients to OrgNacClients.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClients, data_type="nac clients", sort_key="mac"
        )

    @staticmethod
    def _nac_tags():  # Export NAC tags.
        """Export NAC tags to OrgNacTags.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nactags.listOrgNacTags, data_type="nac tags", sort_key="name"
        )

    @staticmethod
    def _nac_portals():  # Export NAC portals.
        """Export NAC portals to OrgNacPortals.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nacportals.listOrgNacPortals, data_type="nac portals", sort_key="name"
        )

    @staticmethod
    def _nac_rules():  # Export NAC rules.
        """Export NAC rules to OrgNacRules.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nacrules.listOrgNacRules, data_type="nac rules", sort_key="name"
        )

    @staticmethod
    def _nac_events():  # Export NAC events.
        """Export NAC events to OrgNacEvents.csv."""
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve lookback hours.
        TimeUtils.log_dynamic_lookback("org NAC events export", hours)  # Log the window.
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClientEvents,
            data_type="nac events",
            sort_key="timestamp",
            duration=f"{hours}h",
        )

    @staticmethod
    def _assets():  # Export assets.
        """Export organization assets to OrgAssets.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgAssets, data_type="assets", sort_key="name"
        )

    @staticmethod
    def _bgp_peers():  # Export BGP peers.
        """Export BGP peer data to OrgBgpPeers.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgBgpStats, data_type="bgp peers", sort_key="peer_ip"
        )

    @staticmethod
    def _tunnel_stats():  # Export tunnel stats.
        """Export tunnel statistics to OrgTunnelStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgTunnelsStats, data_type="tunnel stats", sort_key="name"
        )

    @staticmethod
    def _site_stats():  # Export site stats.
        """Export site statistics to OrgSiteStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.listOrgSiteStats, data_type="site stats", sort_key="name"
        )

    @staticmethod
    def _mxedge_stats():  # Export Mist Edge stats.
        """Export MX Edge statistics to OrgMxedgeStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.listOrgMxEdgesStats, data_type="mx edge stats", sort_key="name"
        )

    @staticmethod
    def e911_report():  # Export E911 report.
        """Export E911 report for the organization to OrgE911Report.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.exports.getOrgE911Report,
            data_type="e911 report",
            sort_key="name",
            limit=None,  # pyright: ignore[reportArgumentType] - getOrgE911Report takes no limit param
        )

    @staticmethod
    def jsi_pbn():  # Export JSI PBN.
        """Export JSI PBN (Product Bulletin Notifications) data to OrgJsiPbn.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.jsi.searchOrgJsiPbn,
            data_type="jsi pbn",
            sort_key="id",
        )

    @staticmethod
    def jsi_sirt():  # Export JSI SIRT.
        """Export JSI SIRT (Security Incident Response Team) advisories to OrgJsiSirt.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.jsi.searchOrgJsiSirt,
            data_type="jsi sirt",
            sort_key="id",
        )

    @staticmethod
    def jsi_assets():  # Export JSI Assets and Contracts.
        """Export JSI assets & contract search results to OrgJsiAssets.csv.

        Why:
            Spec 865 / issue #1373 registers the ``searchOrgJsiAssetsAndContracts``
            endpoint so operators can pull the JSI inventory (assets plus their
            contract coverage) alongside the existing ``jsi_pbn`` / ``jsi_sirt``
            reports.  Delegating to :meth:`export_data` keeps this consistent with
            the sibling JSI exports (prompt for org, paginate, multi-backend write)
            and lets the pre-registered primary-key strategy for
            ``searchOrgJsiAssetsAndContracts`` drive downstream dedup / SQL loads.
        """
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts,
            data_type="jsi assets",  # Drives the export filename -> OrgJsiAssets.csv.
            sort_key="serial",  # Matches the PK strategy index on `serial` for stable ordering.
        )

    @staticmethod
    def mist_edge_events():  # Export Org Mist Edge Events.
        """Export Org Mist Edge Events search results to OrgMistEdgeEvents.csv.

        Why:
            Spec 866 / issue #1374 registers the ``searchOrgMistEdgeEvents``
            endpoint so operators can pull org-wide Mist Edge event history
            alongside the sibling per-site ``SiteMistEdgeEventsExporter``
            (menu 201).  Delegating to :meth:`export_data` reuses the shared
            prompt-for-org + paginate + multi-backend write scaffold, and
            lets the pre-registered composite PK strategy for
            ``searchOrgMistEdgeEvents`` (id + mxedge_id + timestamp) drive
            downstream dedup / SQL loads without duplicates.
        """
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.mxedges.searchOrgMistEdgeEvents,
            data_type="mist edge events",  # Drives the export filename -> OrgMistEdgeEvents.csv.
            sort_key="timestamp",  # Matches the composite PK ordering (newest events sort naturally).
        )

    @staticmethod
    def ospf_stats():  # Export OSPF stats.
        """Export OSPF adjacency statistics for the organization to OrgOspfStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgOspfStats,
            data_type="ospf stats",
            sort_key="mac",
        )

    @staticmethod
    def _security_intel_profiles():  # Export security intel profiles.
        """Export security intelligence profiles to OrgSecurityIntelProfiles.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles,
            data_type="security intel profiles",
            sort_key="name",
        )

    @staticmethod
    def _invites():  # Export invites.
        """Export organization invites to OrgInvites.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.invites.listOrgInvites, data_type="invites", sort_key="email"
        )

    @staticmethod
    def _build_audit_log_kwargs(full_history: bool, duration: str | None) -> dict[str, Any]:
        """Resolve API kwargs (limit + duration/start) for org audit-log listing based on caller flags."""
        kwargs: dict[str, Any] = {"limit": 1000}  # Base API params.
        if duration:  # Caller-supplied duration takes priority.
            kwargs["duration"] = duration  # Set explicit duration string.
            logging.info("Exporting audit logs for duration: %s", duration)  # Log the window.
            return kwargs  # Done.
        if not full_history:  # No duration, recent-only mode.
            hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve lookback hours.
            TimeUtils.log_dynamic_lookback("audit logs export", hours)  # Log the window.
            kwargs["duration"] = f"{hours}h"  # Set the duration.
            logging.info("Exporting only last %s hours of audit logs (duration=%sh).", hours, hours)
            return kwargs  # Done.
        kwargs["start"] = 0  # Full history from start.
        logging.info("Exporting full audit log history (start=0).")  # Log full history.
        return kwargs  # Done.

    @staticmethod
    def audit_logs(full_history: bool = False, duration: str | None = None) -> None:  # Export audit logs.
        """Export org audit logs (24h/explicit duration/full history) to OrgAuditLogs.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + apisession + helpers.
        logging.info("Menu #22: Starting audit logs export")  # Log start.
        logging.debug("ENTRY: OrgExportUtils.audit_logs(full_history=%s, duration=%s)", full_history, duration)
        try:
            org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
            kwargs = OrgExportUtils._build_audit_log_kwargs(full_history, duration)  # Resolve API kwargs.
            logging.debug("Making API call with parameters: %s", kwargs)  # Trace the params.
            response = mistapi.api.v1.orgs.logs.listOrgAuditLogs(mh.apisession, org_id, **kwargs)  # List audit logs.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            if not rawdata:  # No rows.
                logging.warning(" No audit logs returned from API.")  # Warn none returned.
                logging.debug("EXIT: OrgExportUtils.audit_logs - no data")  # Trace exit.
                return  # Abort.
            data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
            data = DataProcessingUtils.escape_multiline(data)  # type: ignore[no-untyped-call]
            mh.DataExporter.write_with_format_selection(data, "OrgAuditLogs.csv")  # type: ignore[no-untyped-call]
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! %d audit logs exported to OrgAuditLogs.csv", len(data))  # Tell the user.
            logging.info("Completed audit logs export and wrote results to OrgAuditLogs.csv.")  # Log completion.
            logging.info("Menu #22: Audit logs export completed - %s records", len(data))  # Log the count.
            logging.debug("EXIT: OrgExportUtils.audit_logs - success")  # Trace success.
        except Exception as e:  # Export failed.
            logging.error("Failed to export audit logs: %s", e)  # Log the error.
            logging.debug("EXIT: OrgExportUtils.audit_logs - error")  # Trace exit.
            raise  # Re-raise to caller.

    @staticmethod
    def sle_metrics(fast: bool = False):  # noqa: C901, PLR0912, PLR0915
        """Export organization-wide SLE (Service Level Experience) metrics to OrgSLEMetrics.csv."""
        from src.refactors.serial_cc.sle_metrics import SLEMetricsService  # Import the SLE service.

        SLEMetricsService.execute(fast)  # Run the SLE export.

    @staticmethod
    def ssid_template_consolidation() -> None:  # Consolidate SSID templates.
        """SSID template consolidation workflow (Menu #145). Delegates to src.ssid_consolidation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession, DEFAULT_API_PAGE_LIMIT, helpers.
        from src.ssid_consolidation.ssid_template_consolidation import (  # noqa: PLC0415
            SSIDTemplateConsolidationManager as _Impl,
        )

        _Impl.execute(  # Delegate to the impl.
            apisession=mh.apisession,
            page_limit=mh.DEFAULT_API_PAGE_LIMIT,
            safe_input_fn=mh.InputUtils.safe_input,
            write_data_fn=mh.DataExporter.write_with_format_selection,
            get_org_id_fn=mh.ConfigUtils.get_cached_or_prompted_org_id,
        )

    @staticmethod
    def e911_bssid_compliance_report() -> None:  # E911 BSSID compliance report.
        """E911 BSSID compliance report (Menu #89). Delegates to src.reports.e911_bssid."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + apisession + helpers.
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        if not current_org_id:  # No org.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No organization selected. Exiting.")  # Tell the user.
            return  # Abort.
        mh.E911BSSIDReportGenerator.execute(  # Run the report.
            apisession=mh.apisession,
            page_limit=mh.DEFAULT_API_PAGE_LIMIT,
            org_id=current_org_id,
            safe_input_fn=mh.InputUtils.safe_input,
            write_data_fn=mh.DataExporter.write_with_format_selection,
        )
