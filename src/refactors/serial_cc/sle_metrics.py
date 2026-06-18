"""SLE metrics export orchestration extracted from MistHelper offender #9."""

import importlib
import logging
import time
from types import SimpleNamespace


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static src imports."""
    misthelper_module = importlib.import_module("MistHelper")
    return SimpleNamespace(
        ConfigUtils=misthelper_module.ConfigUtils,
        PROGRESS_EMITTER=getattr(misthelper_module, "PROGRESS_EMITTER", None),
        TimeUtils=misthelper_module.TimeUtils,
        DataProcessingUtils=misthelper_module.DataProcessingUtils,
        DataExporter=misthelper_module.DataExporter,
        mistapi=misthelper_module.mistapi,
        apisession=misthelper_module.apisession,
    )


class SLEMetricsService:
    """Owns organization SLE metrics export flow formerly embedded in MistHelper."""

    @staticmethod
    def execute(fast: bool = False):  # noqa: C901, PLR0912, PLR0915
        """Run the organization SLE metrics export workflow."""
        deps = _resolve_runtime_dependencies()

        print("Export Organization SLE Metrics:")
        logging.info("Starting export of organization SLE metrics...")
        org_id = deps.ConfigUtils.get_cached_or_prompted_org_id()

        sle_categories = [
            "wifi",  # WiFi/wireless SLE metrics
            "wan",  # WAN connectivity SLE metrics
            "wired",  # Wired network SLE metrics
        ]

        org_sle_specialized_metrics = [
            "summary",  # Org summary SLE data
            "sites-sle",  # Sites SLE aggregation
            "worst-sites-by-sle",  # Worst performing sites SLE analysis
        ]
        duration_value = "7d"
        if fast:
            sle_categories = ["wifi"]
            org_sle_specialized_metrics = ["summary"]
            duration_value = f"{deps.TimeUtils.get_dynamic_lookback_hours(default_hours=24, test_hours=1)}h"
            logging.info(
                "Fast mode enabled for option 66: using smoke path (categories=%s, specialized=%s, duration=%s)",
                sle_categories,
                org_sle_specialized_metrics,
                duration_value,
            )

        total_items = len(org_sle_specialized_metrics) + len(sle_categories)
        emitter = deps.PROGRESS_EMITTER
        if emitter:
            emitter.emit_progress_start("66", "sle_metrics", total_items)
        op_start = time.time()
        items_done = 0

        all_sle_data = []
        metrics_retrieved = 0
        metrics_failed = 0

        print(f"! Retrieving organization SLE data using {len(sle_categories)} service categories...")
        print(f"! Also attempting {len(org_sle_specialized_metrics)} specialized SLE aggregation metrics...")

        try:
            for metric in org_sle_specialized_metrics:  # First loop: specialized metrics
                try:
                    logging.debug(f"Attempting to retrieve specialized SLE metric: {metric}")

                    if "worst-sites" in metric or "sites-sle" in metric:
                        for sle_category in sle_categories:
                            try:
                                response = deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(
                                    deps.apisession, org_id, sle=sle_category, duration=duration_value, limit=1000
                                )
                                sites_sle_data = (
                                    deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []
                                )

                                if sites_sle_data:
                                    aggregated_result = {
                                        "sle_metric_type": f"{metric}_{sle_category}",
                                        "org_id": org_id,
                                        "sle_category": sle_category,
                                        "data_source": "org_sites_sle_aggregated",
                                        "total_sites": len(sites_sle_data),
                                        "sites_analyzed": sites_sle_data,
                                        "metric_name": metric,
                                    }

                                    if "worst-sites" in metric:
                                        aggregated_result["analysis_type"] = "worst_sites_identification"

                                    all_sle_data.append(aggregated_result)
                                    metrics_retrieved += 1
                                    logging.debug(
                                        f"Successfully retrieved sites SLE data for metric analysis: {metric} with SLE: {sle_category} ({len(sites_sle_data)} sites)"  # noqa: E501
                                    )
                                else:
                                    logging.debug(
                                        f"No sites SLE data available for metric: {metric} with SLE: {sle_category}"
                                    )
                            except Exception as sites_error:
                                logging.debug(
                                    f"Failed to get sites SLE data for metric '{metric}' with SLE '{sle_category}': {sites_error}"  # noqa: E501
                                )
                                continue
                    else:
                        response = deps.mistapi.api.v1.orgs.insights.getOrgSle(
                            deps.apisession, org_id, metric, duration=duration_value
                        )
                        sle_data = getattr(response, "data", response) or {}

                        if sle_data:
                            sle_data["sle_metric_type"] = metric
                            sle_data["org_id"] = org_id
                            sle_data["data_source"] = "org_sle_specialized"
                            all_sle_data.append(sle_data)
                            metrics_retrieved += 1
                            logging.debug(f"Successfully retrieved specialized SLE data for metric: {metric}")
                        else:
                            logging.debug(f"No data available for specialized SLE metric: {metric}")
                            metrics_failed += 1

                except Exception as metric_error:
                    metrics_failed += 1
                    logging.debug(f"Failed to get specialized SLE data for metric '{metric}': {metric_error}")
                    continue
                finally:
                    items_done += 1
                    if emitter:
                        emitter.emit_progress_tick(
                            "66", "sle_metrics", total_items, metric, items_done, total_items - items_done
                        )

            for sle_category in sle_categories:  # Second loop: aggregated SLE by category
                try:
                    logging.debug(f"Attempting to retrieve aggregated SLE data for category: {sle_category}")
                    response = deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(
                        deps.apisession, org_id, sle=sle_category, duration=duration_value, limit=1000
                    )
                    sites_sle_data = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []

                    if sites_sle_data:
                        org_aggregated = {
                            "sle_category": sle_category,
                            "org_id": org_id,
                            "data_source": "org_aggregated_from_sites",
                            "total_sites": len(sites_sle_data),
                            "sites_data": sites_sle_data,
                        }

                        if sites_sle_data:
                            org_aggregated["summary_calculated"] = True

                        all_sle_data.append(org_aggregated)
                        metrics_retrieved += 1
                        logging.debug(
                            f"Successfully aggregated SLE data for {len(sites_sle_data)} sites in category: {sle_category}"  # noqa: E501
                        )
                    else:
                        logging.debug(f"No sites SLE data available for category: {sle_category}")
                        metrics_failed += 1

                except Exception as category_error:
                    metrics_failed += 1
                    logging.debug(f"Failed to get SLE data for category '{sle_category}': {category_error}")
                    continue
                finally:
                    items_done += 1
                    if emitter:
                        emitter.emit_progress_tick(
                            "66", "sle_metrics", total_items, sle_category, items_done, total_items - items_done
                        )

            print(f"! SLE data retrieval completed: {metrics_retrieved} successful, {metrics_failed} failed")
            logging.info(f"Org SLE data: {metrics_retrieved} retrieved successfully, {metrics_failed} failed")

            if all_sle_data:
                processed = deps.DataProcessingUtils.flatten_nested_fields(all_sle_data)
                processed = deps.DataProcessingUtils.escape_multiline(processed)
                deps.DataExporter.save_data_to_output(processed, "OrgSLEMetrics.csv")
                print(f"! {metrics_retrieved} organization SLE data sources exported to OrgSLEMetrics.csv")
                logging.info(
                    f"Exported {len(processed)} org SLE data points from {metrics_retrieved} sources to OrgSLEMetrics.csv"  # noqa: E501
                )
            else:
                print("! 0 organization SLE metrics exported to OrgSLEMetrics.csv (no data available)")
                logging.warning("No org SLE data available - all sources failed or returned empty")
                deps.DataExporter.save_data_to_output([], "OrgSLEMetrics.csv")

        except Exception as exception:
            print(f"! Error exporting organization SLE metrics: {exception}")
            logging.error(f"Failed to export org SLE metrics: {exception}")
            deps.DataExporter.save_data_to_output([], "OrgSLEMetrics.csv")
        if emitter:
            emitter.emit_progress_complete("66", "sle_metrics", total_items, items_done, False, time.time() - op_start)
