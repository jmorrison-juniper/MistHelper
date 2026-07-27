"""Gateway statistics exporter extracted from MistHelper.py."""

from __future__ import annotations  # WHY: postpone hint evaluation for forward refs across helpers.

import concurrent.futures  # WHY: bounded thread pool for concurrent per-device stats fetches.
import csv  # WHY: parse cached gateway stats CSV during WAN conflict analysis.
import logging  # WHY: structured logging for entry/exit, retries, and errors.
import threading  # WHY: Semaphore bounds concurrent Mist API connections.
import time  # WHY: sleep between bounded retries when fetching device stats.
from typing import Any  # WHY: opaque types for injected utility modules.

# WHY: ConnectionPoolExecutor is DI-injected via the execute_fn slot (1012 SC-003). No direct import needed.

STATS_CSV_FILENAME: str = "AllGatewayDeviceStats.csv"  # WHY: canonical output CSV. Consumed by conflict analysis.
CONFLICTS_CSV_FILENAME: str = "GatewayWANPortConflicts.csv"  # WHY: canonical WAN conflict output filename.
WAN_PORT_IDS: tuple[str, ...] = ("0/0/0", "0/0/1", "0/0/2")  # WHY: gateway WAN ports monitored for IP conflicts.
EMPTY_IP_TOKENS: frozenset[str] = frozenset({"", "nan", "None", "null"})  # WHY: cells treated as missing IPs.
CONCURRENT_WORKER_CAP: int = 10  # WHY: cap thread pool to avoid overwhelming the Mist API connection pool.
CONCURRENT_FAST_THRESHOLD: int = 10  # WHY: fast mode only switches to threads above this device count.
STATUS_FAILED: str = "failed"  # WHY: legacy failure marker preserved verbatim in exported records.
UNKNOWN_SITE_NAME: str = "Unknown Site"  # WHY: fallback site label preserved from legacy behaviour.
UNKNOWN_LABEL: str = "Unknown"  # WHY: fallback label preserved for missing operator-visible fields.
SAMPLE_CONFLICT_LIMIT: int = 10  # WHY: preserve legacy top-N sample size in operator output.

apisession: Any = None  # WHY: Mist API session slot populated at wiring time.
mistapi: Any = None  # WHY: mistapi SDK module slot populated at wiring time.
ConfigUtils: Any = None  # WHY: config helpers facade (org id resolver).
ValidationUtils: Any = None  # WHY: shared input validators.
DataProcessingUtils: Any = None  # WHY: flatten/normalise helpers for CSV output.
DataExporter: Any = None  # WHY: writes report data with format selection.
RateLimitingUtils: Any = None  # WHY: adaptive delay helpers for API pacing.
CacheUtils: Any = None  # WHY: CSV cache generator facade.
FilePathUtils: Any = None  # WHY: resolves CSV cache file locations.
# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute.
# See specs/1012-misthelper-refactor-hot-functions/spec.md.
# WHY: renamed from execute_with_connection_pool_management per 1012 SC-003. DI-injected pool runner.
execute_fn: Any = None
FAST_MODE_MAX_RETRIES: int = 2  # WHY: retry cap for fast-mode API calls.
FAST_MODE_RETRY_DELAY: float = 0.5  # WHY: base delay (seconds) between retries.
_api_usage_cache: Any = None  # WHY: shared API usage cache reference.
tqdm: Any = None  # WHY: progress bar dependency reference.
GatewayExportUtilsRef: Any = None  # WHY: sibling module handle used to fetch gateway device inventory.

WAN_PORT_COLUMNS: tuple[str, ...] = tuple(f"if_stat_ge-{port}_ips" for port in WAN_PORT_IDS)  # WHY: cached names.

_KWARG_TO_MODULE_SLOT: dict[str, str] = {  # WHY: table-driven map collapses 15-parameter configure signature.
    "apisession_dependency": "apisession",
    "mistapi_dependency": "mistapi",
    "config_utils": "ConfigUtils",
    "validation_utils": "ValidationUtils",
    "data_processing_utils": "DataProcessingUtils",
    "data_exporter": "DataExporter",
    "rate_limiting_utils": "RateLimitingUtils",
    "cache_utils": "CacheUtils",
    "file_path_utils": "FilePathUtils",
    "execute_fn": "execute_fn",
    "fast_mode_max_retries": "FAST_MODE_MAX_RETRIES",
    "fast_mode_retry_delay": "FAST_MODE_RETRY_DELAY",
    "api_usage_cache": "_api_usage_cache",
    "tqdm_module": "tqdm",
    "gateway_export_utils_ref": "GatewayExportUtilsRef",
}


def configure_gateway_stats_exporter_dependencies(**deps: Any) -> None:  # WHY: variadic-kwargs collapse for 15 slots.
    """Configure runtime dependencies from MistHelper orchestration layer."""
    globals().update(  # WHY: bulk-assign module slots using table-driven kwarg->slot map.
        {slot: deps[kwarg] for kwarg, slot in _KWARG_TO_MODULE_SLOT.items()}
    )


def _call_get_site_device_stats(  # WHY: encapsulate semaphore-vs-unbounded API call selection.
    site_id: str, device_id: str, semaphore: threading.Semaphore | None
) -> dict:
    """Invoke Mist getSiteDeviceStats optionally bounded by a connection semaphore."""
    if semaphore is None:  # WHY: sequential path skips connection bounding.
        return mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, site_id, device_id).data  # WHY: unbounded.
    with semaphore:  # WHY: concurrent path caps in-flight API connections.
        return mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, site_id, device_id).data  # WHY: bounded.


def _enrich_stats_record(stats: dict, device_info: tuple[str, str, str, str]) -> dict:  # WHY: attach identifiers.
    """Attach site/device identifiers to a raw stats dict so downstream CSV output is complete."""
    site_id, device_id, device_name, site_name = device_info  # WHY: unpack the four-tuple once.
    stats["site_id"] = site_id  # WHY: enrich for CSV row correlation.
    stats["site_name"] = site_name  # WHY: preserve legacy column name.
    stats["device_id"] = device_id  # WHY: enrich for CSV row correlation.
    stats["device_name"] = device_name  # WHY: preserve legacy column name.
    return stats  # WHY: return enriched record so caller can persist directly.


def _build_failure_record(  # WHY: legacy record shape keeps failure attempts in downstream tallies.
    device_info: tuple[str, str, str, str], exception: Exception
) -> dict:
    """Return failure record preserving legacy shape so downstream tallies still see the attempt."""
    site_id, device_id, device_name, site_name = device_info  # WHY: unpack for record construction.
    return {  # WHY: preserve legacy failure record shape verbatim.
        "site_id": site_id,
        "site_name": site_name,
        "device_id": device_id,
        "device_name": device_name,
        "error": str(exception),
        "status": STATUS_FAILED,
    }


def _compute_backoff(attempt: int, retry_delay: float, fast: bool) -> float:  # WHY: retry timing helper.
    """Return retry delay for this attempt (exponential unless fast mode disables backoff)."""
    if fast:  # WHY: fast mode uses flat delay so retries do not stretch the run.
        return retry_delay  # WHY: skip exponential growth for the fast path.
    return retry_delay * (2**attempt)  # WHY: exponential backoff for the standard path.


def _log_retry_failure(  # WHY: consolidate legacy warning phrasing at retry boundary.
    attempt: int, device_info: tuple[str, str, str, str], exception: Exception
) -> None:
    """Emit warning + retry banner preserving legacy phrasing."""
    _, _, device_name, site_name = device_info  # WHY: unpack for log context only.
    logging.warning(  # WHY: preserve legacy attempt-failed warning phrasing.
        "! Attempt %s failed for device %s at site %s: %s", attempt + 1, device_name, site_name, exception
    )


def _log_terminal_failure(  # WHY: consolidate legacy error phrasing when retries are exhausted.
    device_info: tuple[str, str, str, str], max_attempts: int, exception: Exception
) -> None:
    """Emit terminal error log after all retries exhausted."""
    _, _, device_name, site_name = device_info  # WHY: unpack for log context only.
    logging.error(  # WHY: preserve legacy terminal failure phrasing.
        "! Failed to fetch device stats for %s at site %s after %s attempts: %s",
        device_name,
        site_name,
        max_attempts,
        exception,
    )


def _attempt_fetch_stats(  # WHY: single bounded fetch attempt with validation + logging.
    device_info: tuple[str, str, str, str], connection_semaphore: threading.Semaphore | None
) -> dict:
    """Execute one bounded fetch attempt returning an enriched stats record."""
    site_id, device_id, device_name, site_name = device_info  # WHY: unpack for validation + log context.
    ValidationUtils.validate_site_id(site_id, "device_stats")  # WHY: validate before API call.
    ValidationUtils.validate_device_id(device_id, "device_stats")  # WHY: validate before API call.
    logging.info("Calling getSiteDeviceStats for device %s at site %s", device_name, site_name)  # WHY: pre-log.
    stats = _call_get_site_device_stats(site_id, device_id, connection_semaphore)  # WHY: bounded API call.
    return _enrich_stats_record(stats, device_info)  # WHY: add identifiers for CSV export.


def _log_attempt_success(  # WHY: log retry vs first-try success distinctly for operator clarity.
    attempt: int, device_info: tuple[str, str, str, str]
) -> None:
    """Emit success log preserving legacy retry-vs-first-try phrasing."""
    _, _, device_name, site_name = device_info  # WHY: unpack for log context only.
    if attempt > 0:  # WHY: distinguish retry success from first-try success.
        logging.info(  # WHY: retry-success banner keeps parity with legacy log wording.
            "! Retry %s successful for device %s at site %s", attempt, device_name, site_name
        )
        return  # WHY: retry-success path already logged — skip debug fallthrough.
    logging.debug(  # WHY: first-try success uses debug so normal runs stay quiet.
        "! Collected device stats for gateway %s at site %s", device_name, site_name
    )


class GatewayStatsExporter:  # WHY: namespace class kept for legacy call-sites in MistHelper.py.
    """Gateway device statistics and WAN conflict export helpers."""

    WAN_PORT_COLUMNS = list(WAN_PORT_COLUMNS)  # WHY: preserve public list attribute for legacy callers.

    @staticmethod
    def _fetch_one_device_stats(  # WHY: bounded-retry per-device fetch wrapper for concurrent executor.
        device_info: tuple[str, str, str, str],
        fast: bool,
        connection_semaphore: threading.Semaphore | None = None,
    ) -> dict:
        """Fetch single-device stats with bounded retry. Return enriched dict or failure record."""
        max_retries = FAST_MODE_MAX_RETRIES  # WHY: use configured retry ceiling.
        retry_delay = FAST_MODE_RETRY_DELAY  # WHY: use configured base retry delay.
        for attempt in range(max_retries + 1):  # WHY: N retries means N+1 total attempts.
            try:
                stats = _attempt_fetch_stats(device_info, connection_semaphore)  # WHY: one bounded attempt.
                _log_attempt_success(attempt, device_info)  # WHY: legacy success/retry log.
                return stats  # WHY: successful stats short-circuits remaining retry budget.
            except Exception as exception:  # pylint: disable=broad-exception-caught  # WHY: retry on any error.
                if attempt >= max_retries:  # WHY: exhausted budget — record terminal failure.
                    _log_terminal_failure(device_info, max_retries + 1, exception)  # WHY: terminal log line.
                    return _build_failure_record(device_info, exception)  # WHY: emit failure row for CSV.
                _log_retry_failure(attempt, device_info, exception)  # WHY: log non-terminal attempt.
                backoff_delay = _compute_backoff(attempt, retry_delay, fast)  # WHY: compute delay for retry.
                logging.info("! Retrying in %s seconds...", backoff_delay)  # WHY: legacy banner before sleep.
                time.sleep(backoff_delay)  # WHY: sleep before next attempt.
        return _build_failure_record(device_info, RuntimeError("retry loop exited"))  # WHY: defensive fallback.

    @staticmethod
    def _submit_concurrent_fetches(  # WHY: builds future->device_info map for error-attributed collection.
        executor: concurrent.futures.ThreadPoolExecutor,
        gateway_devices: list[tuple[str, str, str, str]],
        connection_semaphore: threading.Semaphore,
    ) -> dict[concurrent.futures.Future, tuple[str, str, str, str]]:
        """Submit one bounded fetch per device and return future->device_info map for error reporting."""
        return {  # WHY: dict comprehension keeps submit + info-mapping in one atomic expression.
            executor.submit(  # WHY: each submission runs bounded fetch with shared semaphore.
                GatewayStatsExporter._fetch_one_device_stats,
                device_info,
                True,
                connection_semaphore,
            ): device_info
            for device_info in gateway_devices  # WHY: iterate devices to fan-out concurrent work.
        }

    @staticmethod
    def _collect_concurrent_results(  # WHY: drains futures into ordered stats list preserving per-error logs.
        futures: dict[concurrent.futures.Future, tuple[str, str, str, str]],
    ) -> list[dict]:
        """Drain completed futures into a stats list preserving legacy per-error logging."""
        all_stats: list[dict] = []  # WHY: accumulate per-device stats records.
        for future in tqdm(  # WHY: tqdm progress bar for as_completed ordering.
            concurrent.futures.as_completed(futures),  # WHY: yield as futures finish, not submission order.
            total=len(futures),  # WHY: pin total so bar tracks completion percentage.
            desc="Gateway Device Stats",  # WHY: bar label matches legacy operator expectation.
            unit="device",  # WHY: legacy per-device count unit for tqdm output.
        ):
            device_info = futures[future]  # WHY: resolve original tuple for error context.
            try:
                result = future.result()  # WHY: raises if the worker itself failed.
                if result:  # WHY: skip empty/None records.
                    all_stats.append(result)  # WHY: retain successful stats for CSV emit.
            except Exception as exception:  # pylint: disable=broad-exception-caught  # WHY: log + continue.
                _, _, device_name, site_name = device_info  # WHY: unpack for error log.
                logging.error(  # WHY: legacy error banner surfaces per-device failure to operator.
                    "! Concurrent processing failed for device %s at site %s: %s",
                    device_name,
                    site_name,
                    exception,
                )
        return all_stats  # WHY: return aggregated per-device stats list.

    @staticmethod
    def _process_devices_concurrent(  # WHY: fan-out concurrent path used by fast mode.
        gateway_devices: list[tuple[str, str, str, str]],
    ) -> list[dict]:
        """Fetch device stats concurrently with a bounded thread pool. Return aggregated results."""
        logging.info("! Fast mode: Processing %s gateway devices concurrently...", len(gateway_devices))  # WHY: banner.
        max_workers = min(CONCURRENT_WORKER_CAP, len(gateway_devices))  # WHY: cap workers to avoid conn overuse.
        connection_semaphore = threading.Semaphore(max_workers)  # WHY: bound concurrent API connections.
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:  # WHY: managed pool cleanup.
            futures = GatewayStatsExporter._submit_concurrent_fetches(  # WHY: submit one task per device.
                executor, gateway_devices, connection_semaphore
            )
            return GatewayStatsExporter._collect_concurrent_results(futures)  # WHY: drain futures to list.

    @staticmethod
    def _process_devices_sequential(  # WHY: sequential fallback path for non-fast mode.
        gateway_devices: list[tuple[str, str, str, str]], fast: bool
    ) -> list[dict]:
        """Fetch device stats sequentially. Return aggregated results."""
        logging.info("! Processing %s gateway devices sequentially...", len(gateway_devices))  # WHY: legacy banner.
        all_stats: list[dict] = []  # WHY: accumulate per-device stats records.
        for index, device_info in enumerate(  # WHY: enumerate to keep legacy "index/total" progress log.
            tqdm(gateway_devices, desc="Gateway Device Stats", unit="device"), 1
        ):
            _, _, device_name, site_name = device_info  # WHY: unpack for progress log.
            logging.debug(  # WHY: debug-level progress log keeps normal runs quiet.
                "! Processing device %s/%s: %s at %s", index, len(gateway_devices), device_name, site_name
            )
            result = GatewayStatsExporter._fetch_one_device_stats(device_info, fast)  # WHY: fetch single device.
            if result:  # WHY: skip empty results.
                all_stats.append(result)  # WHY: retain non-empty stats record.
        return all_stats  # WHY: return aggregated per-device stats list.

    @staticmethod
    def _flatten_stats(all_stats: list[dict]) -> list[dict]:  # WHY: dedicated flatten step for CSV emission.
        """Flatten nested per-device stats dicts into CSV-safe rows."""
        return [DataProcessingUtils.flatten_dict(stats) for stats in all_stats]  # WHY: single pass flatten.

    @staticmethod
    def _log_export_summary(  # WHY: legacy operator summary of success/failure tallies.
        all_stats: list[dict], gateway_devices: list[tuple[str, str, str, str]]
    ) -> None:
        """Emit legacy export summary with success/failure tallies."""
        logging.info(  # WHY: emit CSV path + record count for post-run confirmation.
            "! Gateway device statistics saved to %s (%s records).", STATS_CSV_FILENAME, len(all_stats)
        )
        logging.info(  # WHY: API-optimization banner surfaces device-count served.
            "! API Optimization: Collected detailed stats for %s gateways", len(gateway_devices)
        )
        successful_requests = sum(  # WHY: count non-failed rows for pass/fail tally.
            1 for stats in all_stats if stats.get("status") != STATUS_FAILED
        )
        failed_requests = len(all_stats) - successful_requests  # WHY: compute failure tally.
        if failed_requests > 0:  # WHY: emit warn when any request failed.
            logging.warning(  # WHY: warn banner surfaces partial-failure count for operator.
                "! %s requests failed out of %s total", failed_requests, len(all_stats)
            )
            return  # WHY: warn path already logged — skip the all-success info line.
        logging.info(  # WHY: info banner confirms full-success run for operator.
            "! All %s requests completed successfully", successful_requests
        )

    @staticmethod
    def _export_stats(  # WHY: single funnel for flatten + persist + summarise pipeline.
        all_stats: list[dict], gateway_devices: list[tuple[str, str, str, str]]
    ) -> None:
        """Flatten, export, and summarize collected gateway device stats."""
        if not all_stats:  # WHY: guard clause — nothing to export.
            logging.warning(" No gateway device statistics found. CSV not created.")  # WHY: legacy warn banner.
            return  # WHY: short-circuit empty payload path.
        sanitized = GatewayStatsExporter._flatten_stats(all_stats)  # WHY: CSV-safe rows.
        logging.info("Saving sanitized gateway stats to %s", STATS_CSV_FILENAME)  # WHY: pre-save log.
        DataExporter.write_with_format_selection(sanitized, STATS_CSV_FILENAME)  # WHY: persist rows.
        GatewayStatsExporter._log_export_summary(all_stats, gateway_devices)  # WHY: legacy tallies.

    @staticmethod
    def device_stats(fast: bool = False) -> None:  # WHY: public entrypoint for gateway stats export flow.
        """Collect and export detailed gateway device statistics."""
        logging.info(  # WHY: legacy INFO banner marks start of stats collection run.
            "[INFO] Collecting detailed device statistics for all gateways in the org..."
        )
        if fast:  # WHY: legacy banner announcing fast-mode path.
            logging.info(" Fast mode enabled: Using cached data and concurrent processing")  # WHY: fast-mode banner.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # WHY: resolve org id via standard pathway.
        gateway_devices = GatewayExportUtilsRef._get_devices_with_sites(org_id, fast=fast)  # WHY: inventory.
        if not gateway_devices:  # WHY: guard clause — no devices means nothing to export.
            logging.warning("[WARN] No gateway devices found. Exiting gateway device stats export.")  # WHY: exit warn.
            return  # WHY: short-circuit empty-inventory path.
        if fast and len(gateway_devices) > CONCURRENT_FAST_THRESHOLD:  # WHY: switch to threads for large fleets.
            all_stats = GatewayStatsExporter._process_devices_concurrent(gateway_devices)  # WHY: concurrent path.
        else:
            all_stats = GatewayStatsExporter._process_devices_sequential(gateway_devices, fast)  # WHY: sequential.
        GatewayStatsExporter._export_stats(all_stats, gateway_devices)  # WHY: persist + summarise.

    @staticmethod
    def device_stats_with_freshness(fast: bool = False) -> None:
        """Export gateway device stats with freshness check."""
        output_file = STATS_CSV_FILENAME  # WHY: canonical output CSV name.
        if CacheUtils.check_and_generate_csv(
            output_file, lambda: GatewayStatsExporter.device_stats(fast=fast)
        ):  # WHY: cache hit returns True. Miss regenerates via the lambda.
            logging.info("! %s already exists and is fresh - using cached data", output_file)
            return
        logging.info("! %s was generated or refreshed", output_file)

    @staticmethod
    def wan_port_conflicts() -> None:
        """Analyze gateway WAN ports for internal IP conflicts and export report."""
        logging.info(" Starting WAN port IP conflict analysis for individual gateway devices...")
        gateway_data = GatewayStatsExporter._load_gateway_stats_for_conflicts()  # WHY: load base CSV.
        if not gateway_data:  # WHY: guard clause — nothing to analyze.
            return
        conflicts_found = GatewayStatsExporter._analyze_all_gateway_conflicts(gateway_data)  # WHY: scan rows.
        GatewayStatsExporter._export_conflict_results(conflicts_found)  # WHY: persist + display.

    @staticmethod
    def _load_gateway_stats_for_conflicts() -> list[dict] | None:
        """Load gateway stats CSV required for conflict analysis."""
        stats_file = STATS_CSV_FILENAME  # WHY: canonical input filename.
        CacheUtils.check_and_generate_csv(
            stats_file, lambda: GatewayStatsExporter.device_stats(fast=True)
        )  # WHY: ensure the base CSV exists.
        stats_path = FilePathUtils.get_csv_path(stats_file)  # WHY: resolve logical name to filesystem path.
        try:
            with open(stats_path, encoding="utf-8") as csvfile:  # WHY: UTF-8 by convention for CSV cache.
                gateway_data = list(csv.DictReader(csvfile))  # WHY: materialise rows for repeated iteration.
            logging.info("! Loaded %s gateway device records for analysis", len(gateway_data))
            return gateway_data
        except Exception as exception:  # pylint: disable=broad-exception-caught  # WHY: preserve legacy message.
            logging.error("! Failed to load %s: %s", stats_file, exception)
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("! Failed to load %s: %s", stats_file, exception)
            return None

    @staticmethod
    def _analyze_all_gateway_conflicts(gateway_data: list[dict]) -> list[dict]:
        """Analyze all gateway rows for WAN IP duplication conflicts."""
        logging.info(" Analyzing individual gateways for internal WAN port IP conflicts...")
        conflicts_found: list[dict] = []  # WHY: accumulator for all per-device conflict records.
        for index, row in enumerate(gateway_data):  # WHY: single pass across gateway rows.
            device_conflicts = GatewayStatsExporter._analyze_device_ip_conflicts(row, index)
            conflicts_found.extend(device_conflicts)  # WHY: append per-device records to global list.
        return conflicts_found

    @staticmethod
    def _analyze_device_ip_conflicts(row: dict, index: int) -> list[dict]:
        """Analyze one gateway row for duplicated WAN IP addresses."""
        device_name = row.get("device_name", row.get("name", f"Device_{index}"))  # WHY: legacy fallback chain.
        site_name = row.get("site_name", UNKNOWN_SITE_NAME)  # WHY: legacy fallback text.
        device_ips = GatewayStatsExporter._collect_device_wan_ips(row)  # WHY: map ip -> ports.
        conflicts = GatewayStatsExporter._find_ip_conflicts(device_ips, device_name)  # WHY: filter duplicates.
        return GatewayStatsExporter._build_conflict_records(conflicts, device_name, site_name)  # WHY: rows.

    @staticmethod
    def _extract_wan_ip_cell(row: dict, column: str) -> str | None:
        """Return the WAN IP cell value or None when it should be ignored."""
        raw_value = row.get(column)  # WHY: dict lookup once.
        if not raw_value:  # WHY: skip missing/empty values without str conversion.
            return None
        ip_value = str(raw_value).strip()  # WHY: normalise before compare.
        if ip_value in EMPTY_IP_TOKENS:  # WHY: skip legacy sentinel values.
            return None
        return ip_value

    @staticmethod
    def _collect_device_wan_ips(row: dict) -> dict[str, list[str]]:
        """Collect WAN IP address to port mapping for one device row."""
        device_ips: dict[str, list[str]] = {}  # WHY: ip -> list of ports where that ip appears.
        for column in GatewayStatsExporter.WAN_PORT_COLUMNS:  # WHY: only monitored WAN columns.
            ip_value = GatewayStatsExporter._extract_wan_ip_cell(row, column)  # WHY: normalise + filter.
            if ip_value is None:  # WHY: skip empty/sentinel cells.
                continue
            port = column.replace("if_stat_ge-", "").replace("_ips", "")  # WHY: derive canonical port id.
            device_ips.setdefault(ip_value, []).append(port)  # WHY: accumulate ports per IP.
        return device_ips

    @staticmethod
    def _find_ip_conflicts(device_ips: dict[str, list[str]], device_name: str) -> list[dict]:
        """Find IP values mapped to more than one WAN port."""
        conflicts: list[dict] = []  # WHY: accumulate multi-port entries only.
        for ip_address, ports in device_ips.items():  # WHY: single pass over device map.
            if len(ports) <= 1:  # WHY: single-port entries are not conflicts.
                continue
            conflicts.append({"value": ip_address, "ports": ports})  # WHY: keep as structured record.
            logging.warning(  # WHY: preserve legacy per-conflict warning line.
                "! IP conflict in %s: %s on ports %s", device_name, ip_address, ", ".join(ports)
            )
        return conflicts

    @staticmethod
    def _build_conflict_records(conflicts: list[dict], device_name: str, site_name: str) -> list[dict]:
        """Build flattened CSV records for per-port conflict entries."""
        records: list[dict] = []  # WHY: one record per (conflict, port) pair.
        for conflict in conflicts:  # WHY: iterate multi-port conflict entries.
            for port in conflict["ports"]:  # WHY: emit one row per port so CSV keeps flat shape.
                records.append(
                    {
                        "device_name": device_name,
                        "site_name": site_name,
                        "port_name": f"ge-{port}",
                        "port_ip": conflict["value"],
                        "conflict_type": "IP Address Conflict",
                        "conflict_with_ports": ", ".join(
                            [other for other in conflict["ports"] if other != port]
                        ),  # WHY: list peer ports without duplicating current port.
                    }
                )
        return records

    @staticmethod
    def _export_conflict_results(conflicts_found: list[dict]) -> None:
        """Persist and display WAN conflict analysis results."""
        if not conflicts_found:  # WHY: guard clause — nothing to export or display.
            logging.info(" No internal WAN port IP conflicts found")
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(" No internal WAN port IP conflicts found - healthy WAN port configurations")
            return
        conflicts_found.sort(key=lambda x: (x.get("device_name", ""), x.get("port_name", "")))  # WHY: stable.
        DataExporter.write_with_format_selection(conflicts_found, CONFLICTS_CSV_FILENAME)  # WHY: persist rows.
        unique_gateways = {row.get("device_name", UNKNOWN_LABEL) for row in conflicts_found}  # WHY: dedupe.
        logging.info("! Exported %s conflicts from %s gateways", len(conflicts_found), len(unique_gateways))
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(
            "! WAN port IP conflicts exported to %s (%s records)",
            CONFLICTS_CSV_FILENAME,
            len(conflicts_found),
        )
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Summary: %s gateways with IP conflicts", len(unique_gateways))
        GatewayStatsExporter._display_conflict_samples(conflicts_found)  # WHY: emit operator-facing sample.

    @staticmethod
    def _display_conflict_samples(conflicts_found: list[dict]) -> None:
        """Print a short conflict sample section for quick operator review."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("\n  Sample WAN Port IP Conflicts Found:")
        for idx, record in enumerate(conflicts_found[:SAMPLE_CONFLICT_LIMIT], 1):  # WHY: top-N sample only.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(
                "%2d. %s (%s)",
                idx,
                record.get("device_name", UNKNOWN_LABEL),
                record.get("site_name", UNKNOWN_SITE_NAME),
            )
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(
                "    Port %s has IP %s",
                record.get("port_name", UNKNOWN_LABEL),
                record.get("port_ip", UNKNOWN_LABEL),
            )
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("    Conflicts with: %s\n", record.get("conflict_with_ports", UNKNOWN_LABEL))
        if len(conflicts_found) > SAMPLE_CONFLICT_LIMIT:  # WHY: only emit trailer when truncation happened.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("... and %s more conflicted ports", len(conflicts_found) - SAMPLE_CONFLICT_LIMIT)
