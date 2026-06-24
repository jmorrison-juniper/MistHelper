"""Gateway statistics exporter extracted from MistHelper.py."""

from __future__ import annotations

import concurrent.futures
import csv
import logging
import threading
import time
from typing import Any

apisession: Any = None
mistapi: Any = None
ConfigUtils: Any = None
ValidationUtils: Any = None
DataProcessingUtils: Any = None
DataExporter: Any = None
RateLimitingUtils: Any = None
CacheUtils: Any = None
FilePathUtils: Any = None
execute_with_connection_pool_management: Any = None
FAST_MODE_MAX_RETRIES: int = 2
FAST_MODE_RETRY_DELAY: float = 0.5
_api_usage_cache: Any = None
tqdm: Any = None
GatewayExportUtilsRef: Any = None


def configure_gateway_stats_exporter_dependencies(
    *,
    apisession_dependency: Any,
    mistapi_dependency: Any,
    config_utils: Any,
    validation_utils: Any,
    data_processing_utils: Any,
    data_exporter: Any,
    rate_limiting_utils: Any,
    cache_utils: Any,
    file_path_utils: Any,
    connection_pool_fn: Any,
    fast_mode_max_retries: int,
    fast_mode_retry_delay: float,
    api_usage_cache: Any,
    tqdm_module: Any,
    gateway_export_utils_ref: Any,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global mistapi
    global ConfigUtils
    global ValidationUtils
    global DataProcessingUtils
    global DataExporter
    global RateLimitingUtils
    global CacheUtils
    global FilePathUtils
    global execute_with_connection_pool_management
    global FAST_MODE_MAX_RETRIES
    global FAST_MODE_RETRY_DELAY
    global _api_usage_cache
    global tqdm
    global GatewayExportUtilsRef

    apisession = apisession_dependency
    mistapi = mistapi_dependency
    ConfigUtils = config_utils
    ValidationUtils = validation_utils
    DataProcessingUtils = data_processing_utils
    DataExporter = data_exporter
    RateLimitingUtils = rate_limiting_utils
    CacheUtils = cache_utils
    FilePathUtils = file_path_utils
    execute_with_connection_pool_management = connection_pool_fn
    FAST_MODE_MAX_RETRIES = fast_mode_max_retries
    FAST_MODE_RETRY_DELAY = fast_mode_retry_delay
    _api_usage_cache = api_usage_cache
    tqdm = tqdm_module
    GatewayExportUtilsRef = gateway_export_utils_ref


class GatewayStatsExporter:
    """Gateway device statistics and WAN conflict export helpers."""

    WAN_PORT_COLUMNS = [f"if_stat_ge-{port}_ips" for port in ["0/0/0", "0/0/1", "0/0/2"]]

    @staticmethod
    def _fetch_one_device_stats(device_info, fast, connection_semaphore=None):
        """Fetch single-device stats with bounded retry; return enriched dict or failure record."""
        max_retries = FAST_MODE_MAX_RETRIES  # Use configured retry ceiling.
        retry_delay = FAST_MODE_RETRY_DELAY  # Use configured base retry delay.
        site_id, device_id, device_name, site_name = device_info  # Unpack device tuple.
        for attempt in range(max_retries + 1):
            try:
                ValidationUtils.validate_site_id(site_id, "device_stats")  # Validate site_id before call.
                ValidationUtils.validate_device_id(device_id, "device_stats")  # Validate device_id before call.
                logging.info(
                    "Calling getSiteDeviceStats for device %s at site %s", device_name, site_name
                )  # Log before API call.
                if connection_semaphore:
                    with connection_semaphore:
                        stats = mistapi.api.v1.sites.stats.getSiteDeviceStats(
                            apisession, site_id, device_id
                        ).data  # Bounded-concurrent API call.
                else:
                    stats = mistapi.api.v1.sites.stats.getSiteDeviceStats(
                        apisession, site_id, device_id
                    ).data  # Sequential API call.
                stats["site_id"] = site_id  # Enrich record with site_id.
                stats["site_name"] = site_name  # Enrich record with site_name.
                stats["device_id"] = device_id  # Enrich record with device_id.
                stats["device_name"] = device_name  # Enrich record with device_name.
                if attempt > 0:
                    logging.info("! Retry %s successful for device %s at site %s", attempt, device_name, site_name)
                else:
                    logging.debug("! Collected device stats for gateway %s at site %s", device_name, site_name)
                return stats  # Return enriched stats record.
            except Exception as exception:
                if attempt < max_retries:
                    backoff_delay = retry_delay * (2**attempt) if not fast else retry_delay  # Compute backoff.
                    logging.warning(
                        "! Attempt %s failed for device %s at site %s: %s",
                        attempt + 1,
                        device_name,
                        site_name,
                        exception,
                    )
                    logging.info("! Retrying in %s seconds...", backoff_delay)
                    time.sleep(backoff_delay)  # Sleep before retry.
                else:
                    logging.error(
                        "! Failed to fetch device stats for %s at site %s after %s attempts: %s",
                        device_name,
                        site_name,
                        max_retries + 1,
                        exception,
                    )
                    return {
                        "site_id": site_id,
                        "site_name": site_name,
                        "device_id": device_id,
                        "device_name": device_name,
                        "error": str(exception),
                        "status": "failed",
                    }  # Return failure record so downstream still tallies attempt.

    @staticmethod
    def _process_devices_concurrent(gateway_devices):
        """Fetch device stats concurrently with thread pool; return aggregated results."""
        logging.info("! Fast mode: Processing %s gateway devices concurrently...", len(gateway_devices))
        max_workers = min(10, len(gateway_devices))  # Cap worker count to prevent connection overuse.
        connection_semaphore = threading.Semaphore(max_workers)  # Bound concurrent connections.
        all_stats: list = []  # Accumulate per-device stats records.
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    GatewayStatsExporter._fetch_one_device_stats,
                    device_info,
                    True,
                    connection_semaphore,
                ): device_info
                for device_info in gateway_devices
            }  # Submit one task per gateway device.
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Gateway Device Stats",
                unit="device",
            ):
                device_info = futures[future]  # Resolve original device tuple for error reporting.
                try:
                    result = future.result()  # Collect per-device result.
                    if result:
                        all_stats.append(result)  # Append non-empty result.
                except Exception as exception:
                    site_id, device_id, device_name, site_name = device_info  # Unpack for error log.
                    logging.error(
                        "! Concurrent processing failed for device %s at site %s: %s", device_name, site_name, exception
                    )
        return all_stats  # Return aggregated stats list.

    @staticmethod
    def _process_devices_sequential(gateway_devices, fast):
        """Fetch device stats sequentially; return aggregated results."""
        logging.info("! Processing %s gateway devices sequentially...", len(gateway_devices))
        all_stats: list = []  # Accumulate per-device stats records.
        for index, device_info in enumerate(tqdm(gateway_devices, desc="Gateway Device Stats", unit="device"), 1):
            _, _, device_name, site_name = device_info  # Unpack for progress log.
            logging.debug("! Processing device %s/%s: %s at %s", index, len(gateway_devices), device_name, site_name)
            result = GatewayStatsExporter._fetch_one_device_stats(device_info, fast)  # Fetch single device.
            if result:
                all_stats.append(result)  # Append non-empty result.
        return all_stats  # Return aggregated stats list.

    @staticmethod
    def _export_stats(all_stats, gateway_devices):
        """Flatten, export, and summarize collected gateway device stats."""
        if not all_stats:
            logging.warning(" No gateway device statistics found. CSV not created.")
            return  # Nothing to export.
        sanitized = []  # Accumulate flattened records.
        for stats in all_stats:
            flat_record = DataProcessingUtils.flatten_dict(stats)  # Flatten nested dict for CSV.
            sanitized.append(flat_record)  # Append flattened record.
        filename = "AllGatewayDeviceStats.csv"  # Output filename preserved verbatim.
        logging.info("Saving sanitized gateway stats to %s", filename)  # Log before save action.
        DataExporter.write_with_format_selection(sanitized, filename)  # Persist data to output backend.
        logging.info("! Gateway device statistics saved to %s (%s records).", filename, len(all_stats))
        logging.info("! API Optimization: Collected detailed stats for %s gateways", len(gateway_devices))
        successful_requests = len([stats for stats in all_stats if stats.get("status") != "failed"])
        failed_requests = len(all_stats) - successful_requests  # Compute failure tally.
        if failed_requests > 0:
            logging.warning("! %s requests failed out of %s total", failed_requests, len(all_stats))
        else:
            logging.info("! All %s requests completed successfully", successful_requests)

    @staticmethod
    def device_stats(fast: bool = False) -> None:
        """Collect and export detailed gateway device statistics."""
        logging.info("[INFO] Collecting detailed device statistics for all gateways in the org...")
        if fast:
            logging.info(" Fast mode enabled: Using cached data and concurrent processing")
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org_id via standard pathway.
        gateway_devices = GatewayExportUtilsRef._get_devices_with_sites(org_id, fast=fast)  # Fetch device set.
        if not gateway_devices:
            logging.warning("[WARN] No gateway devices found. Exiting gateway device stats export.")
            return  # Exit when no devices available.
        if fast and len(gateway_devices) > 10:
            all_stats = GatewayStatsExporter._process_devices_concurrent(gateway_devices)  # Concurrent path.
        else:
            all_stats = GatewayStatsExporter._process_devices_sequential(gateway_devices, fast)  # Sequential.
        GatewayStatsExporter._export_stats(all_stats, gateway_devices)  # Export collected stats.

    @staticmethod
    def device_stats_with_freshness(fast: bool = False) -> None:
        """Export gateway device stats with freshness check."""
        output_file = "AllGatewayDeviceStats.csv"
        if CacheUtils.check_and_generate_csv(output_file, lambda: GatewayStatsExporter.device_stats(fast=fast)):
            logging.info("! %s already exists and is fresh - using cached data", output_file)
        else:
            logging.info("! %s was generated or refreshed", output_file)

    @staticmethod
    def wan_port_conflicts() -> None:
        """Analyze gateway WAN ports for internal IP conflicts and export report."""
        logging.info(" Starting WAN port IP conflict analysis for individual gateway devices...")
        gateway_data = GatewayStatsExporter._load_gateway_stats_for_conflicts()
        if not gateway_data:
            return
        conflicts_found = GatewayStatsExporter._analyze_all_gateway_conflicts(gateway_data)
        GatewayStatsExporter._export_conflict_results(conflicts_found)

    @staticmethod
    def _load_gateway_stats_for_conflicts():
        """Load gateway stats CSV required for conflict analysis."""
        stats_file = "AllGatewayDeviceStats.csv"
        CacheUtils.check_and_generate_csv(stats_file, lambda: GatewayStatsExporter.device_stats(fast=True))
        stats_path = FilePathUtils.get_csv_path(stats_file)
        try:
            with open(stats_path, encoding="utf-8") as csvfile:
                gateway_data = list(csv.DictReader(csvfile))
            logging.info("! Loaded %s gateway device records for analysis", len(gateway_data))
            return gateway_data
        except Exception as exception:
            logging.error("! Failed to load %s: %s", stats_file, exception)
            print(f"! Failed to load {stats_file}: {exception}")
            return None

    @staticmethod
    def _analyze_all_gateway_conflicts(gateway_data):
        """Analyze all gateway rows for WAN IP duplication conflicts."""
        logging.info(" Analyzing individual gateways for internal WAN port IP conflicts...")
        conflicts_found = []
        for index, row in enumerate(gateway_data):
            device_conflicts = GatewayStatsExporter._analyze_device_ip_conflicts(row, index)
            conflicts_found.extend(device_conflicts)
        return conflicts_found

    @staticmethod
    def _analyze_device_ip_conflicts(row, index):
        """Analyze one gateway row for duplicated WAN IP addresses."""
        device_name = row.get("device_name", row.get("name", f"Device_{index}"))
        site_name = row.get("site_name", "Unknown Site")
        device_ips = GatewayStatsExporter._collect_device_wan_ips(row)
        conflicts = GatewayStatsExporter._find_ip_conflicts(device_ips, device_name)
        return GatewayStatsExporter._build_conflict_records(conflicts, device_name, site_name)

    @staticmethod
    def _collect_device_wan_ips(row):
        """Collect WAN IP address to port mapping for one device row."""
        device_ips: dict[str, list[str]] = {}
        for col in GatewayStatsExporter.WAN_PORT_COLUMNS:
            if col in row and row[col] and str(row[col]).strip():
                ip_value = str(row[col]).strip()
                if ip_value not in ["", "nan", "None", "null"]:
                    port = col.replace("if_stat_ge-", "").replace("_ips", "")
                    device_ips.setdefault(ip_value, []).append(port)
        return device_ips

    @staticmethod
    def _find_ip_conflicts(device_ips, device_name):
        """Find IP values mapped to more than one WAN port."""
        conflicts = []
        for ip_address, ports in device_ips.items():
            if len(ports) > 1:
                conflicts.append({"value": ip_address, "ports": ports})
                logging.warning("! IP conflict in %s: %s on ports %s", device_name, ip_address, ", ".join(ports))
        return conflicts

    @staticmethod
    def _build_conflict_records(conflicts, device_name, site_name):
        """Build flattened CSV records for per-port conflict entries."""
        records = []
        for conflict in conflicts:
            for port in conflict["ports"]:
                records.append(
                    {
                        "device_name": device_name,
                        "site_name": site_name,
                        "port_name": f"ge-{port}",
                        "port_ip": conflict["value"],
                        "conflict_type": "IP Address Conflict",
                        "conflict_with_ports": ", ".join([p for p in conflict["ports"] if p != port]),
                    }
                )
        return records

    @staticmethod
    def _export_conflict_results(conflicts_found):
        """Persist and display WAN conflict analysis results."""
        if not conflicts_found:
            logging.info(" No internal WAN port IP conflicts found")
            print(" No internal WAN port IP conflicts found - healthy WAN port configurations")
            return

        output_file = "GatewayWANPortConflicts.csv"
        conflicts_found.sort(key=lambda x: (x.get("device_name", ""), x.get("port_name", "")))
        DataExporter.write_with_format_selection(conflicts_found, output_file)

        unique_gateways = {r.get("device_name", "Unknown") for r in conflicts_found}
        logging.info("! Exported %s conflicts from %s gateways", len(conflicts_found), len(unique_gateways))
        print(f"! WAN port IP conflicts exported to {output_file} ({len(conflicts_found)} records)")
        print(f"! Summary: {len(unique_gateways)} gateways with IP conflicts")

        GatewayStatsExporter._display_conflict_samples(conflicts_found)

    @staticmethod
    def _display_conflict_samples(conflicts_found):
        """Print a short conflict sample section for quick operator review."""
        print("\n  Sample WAN Port IP Conflicts Found:")
        for idx, record in enumerate(conflicts_found[:10], 1):
            print(f"{idx:2d}. {record.get('device_name', 'Unknown')} ({record.get('site_name', 'Unknown Site')})")
            print(f"    Port {record.get('port_name', 'Unknown')} has IP {record.get('port_ip', 'Unknown')}")
            print(f"    Conflicts with: {record.get('conflict_with_ports', 'Unknown')}\n")

        if len(conflicts_found) > 10:
            print(f"... and {len(conflicts_found) - 10} more conflicted ports")
