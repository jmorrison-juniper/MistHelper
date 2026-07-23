"""SiteAnomalyExporter -- site + device + client anomaly event exporters.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 43).
Consolidates site-level, device-level, and client-level anomaly event
exports via mistapi anomaly endpoints, with mistapi logger suppression
during the fetch loop and CSV rendering via DataExporter.

Direct imports cover stdlib (functools, importlib, logging) plus typing
(Any, Callable). Every live-global read (``PromptUtils``,
``EnhancedSSHRunner``, ``AnomalyMetricsDiscovery``, ``mistapi``,
``apisession``, ``DataProcessingUtils``, ``DataExporter``,
``PromptClientUtils``) is resolved via lazy ``mh =
importlib.import_module("MistHelper")`` inside the methods that need
them. Callers continue to reach the class through the
``MistHelper.SiteAnomalyExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import functools  # WHY: partial-bind per-metric fetch callables in builder lambdas.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace + mistapi logger suppression by name.
from collections.abc import Callable  # WHY: fetch_builder is Callable[[str], Callable].
from typing import Any  # WHY: row rows are dict[str, Any].

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.


class SiteAnomalyExporter:  # Site anomaly exporters.
    """Site Anomaly and Event Exporter.

    Handles site-level anomaly events and insight metrics exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def anomaly_events():
        """Export comprehensive anomaly events for a selected site to SiteAnomalyEvents_[SiteName].csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils + EnhancedSSHRunner.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Export Site Anomaly Events:")  # User-visible header.
        logger.info("Starting export of site anomaly events...")  # Trace start of export.
        site_id = mh.PromptUtils.select_site()  # Prompt the user for a site.
        if not site_id:  # No site chosen.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No site selected. Exiting.")  # Tell the user.
            return  # Abort the export.
        site_name = SiteAnomalyExporter._anomaly_resolve_site_name(site_id)  # Resolve display name for filename.
        filename = f"SiteAnomalyEvents_{mh.EnhancedSSHRunner.sanitize_filename(site_name)}.csv"  # Build CSV name.
        metrics = SiteAnomalyExporter._discover_site_anomaly_metrics()  # Discover anomaly metric names.
        if not metrics:  # Nothing to fetch.
            return  # Abort the export.
        try:
            data, count = SiteAnomalyExporter._aggregate_site_anomaly_data(site_id, site_name, metrics)  # Fetch.
            SiteAnomalyExporter._export_anomaly_data(data, filename, "site anomaly event", count, site_name)  # CSV
        except Exception as exception:  # Broader export failure (flatten/write).
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("! Error exporting site anomaly events: %s", exception)  # Tell the user.
            logger.error("Failed to export site anomaly events for %s: %s", site_name, exception)  # Log it.

    @staticmethod
    def device_anomaly_events():
        """Export device anomaly events to SiteDeviceAnomalyEvents_[Site]_[Device].csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Export Site Device Anomaly Events:")  # User-visible header.
        logger.info("Starting export of site device anomaly events...")  # Trace start of export.
        site_id = mh.PromptUtils.select_site()  # Prompt the user for a site.
        if not site_id:  # No site chosen.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No site selected. Exiting.")  # Tell the user.
            return  # Abort the export.
        site_name = SiteAnomalyExporter._anomaly_resolve_site_name(site_id)  # Resolve display name.
        selection = mh.PromptUtils.select_device_id_from_inventory(site_id)  # Prompt for a device.
        if not selection:  # No device chosen.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No device selected. Exiting.")  # Tell the user.
            return  # Abort the export.
        device_mac, device_name = selection[0], selection[1]  # Unpack the MAC and display name.
        filename = SiteAnomalyExporter._build_device_filename(site_name, device_name)  # Build the CSV name.
        metrics = ["ap_availability", "throughput", "capacity"]  # Device anomaly metric names.
        try:
            data, count = SiteAnomalyExporter._aggregate_device_anomaly_data(
                site_id, site_name, device_mac, device_name, metrics
            )  # Loop + fetch each metric.
            SiteAnomalyExporter._export_anomaly_data(data, filename, "device anomaly event", count, device_name)  # CSV
        except Exception as exception:  # Broader export failure (flatten/write).
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("! Error exporting device anomaly events: %s", exception)  # Tell the user.
            logger.error("Failed to export device anomaly events for %s: %s", device_name, exception)  # Log it.

    @staticmethod
    def _build_device_filename(site_name: str, device_name: str) -> str:
        """Build the device anomaly CSV filename from sanitized site + device names."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of EnhancedSSHRunner.
        sanitized_site = mh.EnhancedSSHRunner.sanitize_filename(site_name)  # Sanitize the site name.
        sanitized_device = mh.EnhancedSSHRunner.sanitize_filename(device_name)  # Sanitize the device name.
        return f"SiteDeviceAnomalyEvents_{sanitized_site}_{sanitized_device}.csv"  # Compose CSV name.

    @staticmethod
    def _discover_site_anomaly_metrics() -> list[str]:
        """Discover potential site anomaly metric names, announce them, return [] when none found."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of AnomalyMetricsDiscovery.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Discovering potential anomaly metrics from Mist API definitions...")  # Tell the user.
        potential = mh.AnomalyMetricsDiscovery.discover()  # Pull discovery list from CSV.
        names = [info["metric_name"] for info in potential]  # Extract just the metric names.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Found %s potential anomaly metrics:", len(names))  # Tell the user the count.
        for info in potential:  # Show each metric to the user.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  - %s: %s...", info["metric_name"], info["description"][:60])  # Trim long descriptions.
        if not names:  # No metrics discovered at all.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No potential anomaly metrics found. Please check ConstInsightMetrics.csv availability.")
        return names  # Return the names (possibly empty).

    @staticmethod
    def _fetch_one_anomaly_metric(
        fetch_callable: Any, metric: str, tags: dict[str, str], scope: tuple[str, str]
    ) -> dict[str, Any] | None:
        """Invoke fetch_callable() for one metric, tag the result, return data dict or None on no-data/error."""
        display_label, data_type = scope  # Unpack the scope tuple for printing + tagging.
        try:
            response = fetch_callable()  # Issue the API call (callable is already bound via functools.partial).
            data = getattr(response, "data", response) or {}  # Unwrap data; default empty.
            if data:  # API returned actual data for this metric.
                data["metric_type"] = metric  # Tag the metric name.
                data["data_type"] = data_type  # Tag the data type for downstream consumers.
                for key, value in tags.items():  # Apply caller-supplied tags (site_id, site_name, ...).
                    data[key] = value  # Set each tag on the result row.
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.info("!? Retrieved %s %s", metric, display_label)  # Tell the user.
                logger.debug("Successfully retrieved %s %s for %s", metric, display_label, tags)  # Trace success.
                return data  # Return the tagged row.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! No %s %s available", metric, display_label)  # Tell the user the metric had no data.
            logger.info("No %s %s available for %s", metric, display_label, tags)  # Log the absence.
            return None  # Signal caller to skip.
        except Exception as metric_error:  # This metric's fetch failed.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! Error retrieving %s %s: %s", metric, display_label, metric_error)  # Tell the user.
            logger.warning("Error retrieving %s %s for %s: %s", metric, display_label, tags, metric_error)  # Warn.
            return None  # Signal caller to skip.

    @staticmethod
    def _run_anomaly_metric_loop(
        metrics: list[str],
        fetch_builder: Callable[[str], Callable],
        tags: dict[str, Any],
        scope: tuple[str, str],
    ) -> tuple[list[dict[str, Any]], int]:
        """Loop metrics with mistapi loggers silenced; build fetch with fetch_builder(metric); collect tagged rows."""
        original_levels = SiteAnomalyExporter._anomaly_suppress_mistapi_loggers()  # Quiet mistapi internal loggers.
        rows: list[dict[str, Any]] = []  # Accumulator for successful rows.
        count = 0  # Number of metrics that returned data.
        try:
            for metric in metrics:  # Fetch each metric.
                fetch = fetch_builder(metric)  # Build per-metric fetch callable.
                row = SiteAnomalyExporter._fetch_one_anomaly_metric(fetch, metric, tags, scope)  # Fetch + tag.
                if row is not None:  # Metric returned data.
                    rows.append(row)  # Collect the row.
                    count += 1  # Bump the success counter.
        finally:
            SiteAnomalyExporter._anomaly_restore_loggers(original_levels)  # Always restore loggers.
        return rows, count  # Hand the aggregate back to the orchestrator.

    @staticmethod
    def _aggregate_site_anomaly_data(
        site_id: str, site_name: str, metrics: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        """Loop site anomaly metrics with mistapi loggers silenced; return (rows, success_count)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        tags = {"site_id": site_id, "site_name": site_name}  # Tags attached to every row.
        scope = ("anomaly events", "site_anomaly_events")  # Display label + data_type tag.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Retrieving %s different site anomaly events...", len(metrics))  # Tell the user.
        builder = lambda metric: functools.partial(  # noqa: E731 — bind site-anomaly fetch per metric.
            mh.mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents, mh.apisession, site_id, metric
        )
        return SiteAnomalyExporter._run_anomaly_metric_loop(metrics, builder, tags, scope)  # Shared loop.

    @staticmethod
    def _aggregate_device_anomaly_data(
        site_id: str, site_name: str, device_mac: str, device_name: str, metrics: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        """Loop device anomaly metrics with mistapi loggers silenced; return (rows, success_count)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        tags = {  # Tags attached to every row.
            "site_id": site_id,
            "site_name": site_name,
            "device_mac": device_mac,
            "device_name": device_name,
        }
        scope = ("device anomaly data", "device_anomaly_events")  # Display label + data_type tag.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! Retrieving %s different device anomaly events for %s...", len(metrics), device_name
        )  # Tell the user.
        builder = lambda metric: functools.partial(  # noqa: E731 — bind device-anomaly fetch per metric.
            mh.mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForDevice,
            mh.apisession,
            site_id,
            metric,
            device_mac,
        )
        return SiteAnomalyExporter._run_anomaly_metric_loop(metrics, builder, tags, scope)  # Shared loop.

    @staticmethod
    def _export_anomaly_data(
        data_list: list[dict[str, Any]], filename: str, label: str, success_count: int, scope_name: str
    ) -> None:
        """Flatten + escape + write the aggregated anomaly rows, or write an empty CSV when there is no data."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if data_list:  # At least one metric returned data.
            processed = DataProcessingUtils.flatten_nested_fields(data_list)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
            mh.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! %s %s types exported to %s", success_count, label, filename)  # Tell the user the count.
            logger.info("Exported %s %s types for %s to %s", success_count, label, scope_name, filename)  # Log.
        else:  # No data from any metric.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! 0 %ss exported to %s (no data available)", label, filename)  # Tell the user zero.
            logger.warning("No %s available for %s", label, scope_name)  # Warn about the empty result.
            mh.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]

    _CLIENT_ANOMALY_METRICS = (  # Client-specific anomaly metrics (verified working) shared by the count + loop.
        "successful_connect",  # Note: uses underscore, not hyphen for the client endpoint.
        "roaming",  # Client roaming issues.
        "throughput",  # Client throughput anomalies.
    )

    @staticmethod
    def _anomaly_resolve_site_name(site_id: str) -> str:
        """Resolve the human-readable site name for a site_id, falling back to the id on lookup failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        try:  # The site-name lookup is best-effort; the id is an acceptable fallback for the filename.
            response = mh.mistapi.api.v1.sites.listSites(mh.apisession, site_id)  # List the site.
            sites = mh.mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            return next((site["name"] for site in sites if site["id"] == site_id), site_id)  # Resolve site name.
        except Exception:  # Lookup failed.
            return site_id  # Fall back to the id.

    @staticmethod
    def _anomaly_lookup_client_hostname(site_id: str, client_mac: str) -> str:
        """Look up a client's hostname from its wireless stats, falling back to the MAC on failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        try:  # Hostname enrichment is best-effort; the MAC is an acceptable fallback.
            response = mh.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(  # List client stats.
                mh.apisession, site_id, limit=100, duration="1d"
            )
            clients = getattr(response, "data", response) or []  # Unwrap data; default empty.
            for client in clients:  # Find the matching client.
                if client.get("mac") == client_mac:  # MAC matches.
                    return client.get("hostname", client.get("name", "Unknown"))  # Read the hostname.
            return "Unknown"  # No matching client found in the stats.
        except Exception as exception:  # Lookup failed.
            logger.warning("Could not retrieve client hostname for %s: %s", client_mac, exception)  # Warn the failure.
            return client_mac  # Fall back to the MAC address.

    @staticmethod
    def _anomaly_suppress_mistapi_loggers() -> dict:  # type: ignore[type-arg]
        """Raise mistapi logger levels to CRITICAL to keep the console clean; return their original levels."""
        mistapi_loggers = [
            "apirequest",
            "apiresponse",
            "mistapi",
            "mistapi.apirequest",
            "mistapi.apiresponse",
        ]  # Names.
        original_levels = {}  # Save original levels for later restoration.
        for logger_name in mistapi_loggers:  # Quiet each mistapi logger.
            logger_instance = logging.getLogger(logger_name)  # Get the logger.
            original_levels[logger_name] = logger_instance.level  # Remember its level.
            logger_instance.setLevel(logging.CRITICAL)  # Suppress ERROR logs temporarily.
        return original_levels  # Original levels keyed by logger name.

    @staticmethod
    def _anomaly_restore_loggers(original_levels: dict) -> None:  # type: ignore[type-arg]
        """Restore mistapi logger levels saved by _anomaly_suppress_mistapi_loggers."""
        for logger_name, original_level in original_levels.items():  # Restore each logger level.
            logging.getLogger(logger_name).setLevel(original_level)  # Restore the saved level.

    @staticmethod
    def _anomaly_fetch_one_metric(
        site_id: str, client_mac: str, site_name: str, client_hostname: str, metric: str
    ) -> dict | None:  # type: ignore[type-arg]
        """Fetch one client anomaly metric and tag it with site/client metadata; return the record, or None if empty."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        # Get client anomalies for this metric.
        response = mh.mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForClient(
            mh.apisession, site_id, client_mac, metric
        )
        client_anomaly_data = getattr(response, "data", response) or {}  # Unwrap data; default empty.
        if not client_anomaly_data:  # The metric returned no data.
            return None  # Signal an empty metric.
        client_anomaly_data["metric_type"] = metric  # Tag the metric.
        client_anomaly_data["site_id"] = site_id  # Tag the site.
        client_anomaly_data["site_name"] = site_name  # Tag the site name.
        client_anomaly_data["client_mac"] = client_mac  # Tag the client MAC.
        client_anomaly_data["client_hostname"] = client_hostname  # Tag the hostname.
        client_anomaly_data["data_type"] = "client_anomaly_events"  # Tag the data type.
        return client_anomaly_data  # The tagged anomaly record.

    @staticmethod
    def _anomaly_handle_metric_result(record: dict | None, metric: str, client_mac: str, all_data: list) -> int:  # type: ignore[type-arg]
        """Record one fetched metric: append + announce on data, announce 'none' otherwise; return 1 if kept else 0."""
        if record is not None:  # The metric returned data.
            all_data.append(record)  # Collect the row.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("!? Retrieved %s client anomaly data", metric)  # Tell the user.
            logger.debug("Successfully retrieved %s client anomaly data for %s", metric, client_mac)  # Trace.
            return 1  # One successful metric.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! No %s client anomaly data available", metric)  # Tell the user none.
        logger.info("No %s client anomaly data available for %s", metric, client_mac)  # Log none.
        return 0  # No data for this metric.

    @staticmethod
    def _anomaly_collect_metrics(
        site_id: str, client_mac: str, site_name: str, client_hostname: str
    ) -> tuple[list, int]:  # type: ignore[type-arg]
        """Fetch all client anomaly metrics for one client; return (records, retrieved_count)."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! Retrieving %s different client anomaly events for %s (%s)...",
            len(SiteAnomalyExporter._CLIENT_ANOMALY_METRICS),
            client_mac,
            client_hostname,
        )  # Tell the user how many metrics will be fetched.
        all_client_anomaly_data = []  # Accumulate anomaly rows.
        metrics_retrieved = 0  # Success count.
        for metric in SiteAnomalyExporter._CLIENT_ANOMALY_METRICS:  # Fetch each metric independently.
            try:  # Isolate per-metric failures so one bad metric doesn't abort the rest.
                record = SiteAnomalyExporter._anomaly_fetch_one_metric(  # Fetch + tag one metric.
                    site_id, client_mac, site_name, client_hostname, metric
                )
                metrics_retrieved += SiteAnomalyExporter._anomaly_handle_metric_result(  # Record + announce outcome.
                    record, metric, client_mac, all_client_anomaly_data
                )
            except Exception as metric_error:  # Metric fetch failed.
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.warning("! Error retrieving %s client anomaly data: %s", metric, metric_error)  # Tell the user.
                logger.warning(
                    "Error retrieving %s client anomaly data for %s: %s", metric, client_mac, metric_error
                )  # Warn the failure.
        return all_client_anomaly_data, metrics_retrieved  # Collected rows and the success count.

    @staticmethod
    def _anomaly_export(all_data: list, metrics_retrieved: int, client_mac: str, filename: str) -> None:  # type: ignore[type-arg]
        """Flatten and write the collected client anomaly rows to CSV (writes an empty file when there is no data)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if all_data:  # At least one metric returned data.
            processed = DataProcessingUtils.flatten_nested_fields(all_data)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
            mh.DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! %s client anomaly event types exported to %s", metrics_retrieved, filename)  # Tell the user.
            logger.info(
                "Exported %s client anomaly event types for %s to %s", metrics_retrieved, client_mac, filename
            )  # Log the export.
        else:  # No metric returned data.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning(
                "! 0 client anomaly events exported to %s (no data available)", filename
            )  # Tell the user zero.
            logger.warning("No client anomaly events available for %s", client_mac)  # Warn none.
            mh.DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # Empty file.

    @staticmethod
    def _anomaly_prepare() -> tuple | None:  # type: ignore[type-arg]
        """Prompt for a site and client, resolve names + hostname, and build the output filename.

        Returns (site_id, site_name, client_mac, client_hostname, filename), or None when the
        operator cancels at the site or client selection prompt.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils + PromptClientUtils + SSH.
        site_id = mh.PromptUtils.select_site()  # Select a site.
        if not site_id:  # No site selected.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No site selected. Exiting.")  # Tell the user.
            return None  # Abort.
        site_name = SiteAnomalyExporter._anomaly_resolve_site_name(site_id)  # Resolve site name for the filename.
        client_mac, _, _ = mh.PromptClientUtils.select_client(site_id)  # Select a client (only MAC is used).
        if not client_mac:  # No client selected.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No client selected. Exiting.")  # Tell the user.
            return None  # Abort.
        client_hostname = SiteAnomalyExporter._anomaly_lookup_client_hostname(site_id, client_mac)  # Hostname lookup.
        sanitized_site_name = mh.EnhancedSSHRunner.sanitize_filename(site_name)  # Sanitize the site name.
        filename = f"SiteClientAnomalyEvents_{sanitized_site_name}_{client_mac.replace(':', '')}.csv"  # Output name.
        return site_id, site_name, client_mac, client_hostname, filename  # Resolved context for the export.

    @staticmethod
    def client_anomaly_events():
        """Export client-specific anomaly events for a selected client to a per-site/per-client CSV.

        Prompts for a site and client, fetches the successful_connect / roaming / throughput
        anomaly metrics, and writes SiteClientAnomalyEvents_[SiteName]_[ClientMAC].csv.
        """
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Export Site Client Anomaly Events:")  # Header.
        logger.info("Starting export of site client anomaly events...")  # Log start.
        prepared = SiteAnomalyExporter._anomaly_prepare()  # Prompt + resolve site/client/filename.
        if prepared is None:  # Operator cancelled at a selection prompt.
            return  # Abort.
        site_id, site_name, client_mac, client_hostname, filename = prepared  # Unpack the resolved context.
        original_levels = SiteAnomalyExporter._anomaly_suppress_mistapi_loggers()  # Quiet mistapi loggers.
        try:  # Guard the fetch/export so logger levels are always restored in finally.
            all_data, metrics_retrieved = SiteAnomalyExporter._anomaly_collect_metrics(  # Fetch all metrics.
                site_id, client_mac, site_name, client_hostname
            )
            SiteAnomalyExporter._anomaly_export(all_data, metrics_retrieved, client_mac, filename)  # Write the CSV.
        except Exception as exception:  # Export failed.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("! Error exporting client anomaly events: %s", exception)  # Tell the user.
            logger.error("Failed to export client anomaly events for %s: %s", client_mac, exception)  # Log the error.
        finally:  # Always restore the mistapi logger levels.
            SiteAnomalyExporter._anomaly_restore_loggers(original_levels)  # Restore logger levels.
