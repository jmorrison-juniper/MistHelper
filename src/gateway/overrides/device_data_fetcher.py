"""Live device port_config + if_stat fetching with optional connection-pool fast mode."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
import threading  # Type-hint reference for the connection semaphore passed into worker
from typing import Any  # Generic typing for nested API JSON payloads

from .. import gateway_override_analyzer as _deps  # Module-level dependency holder set by configure_*


class DeviceDataFetcher:
    """Fetch (port_configs, interface_stats) per device, choosing fast vs sequential mode."""

    @staticmethod
    def fetch_all(
        devices_with_overrides: dict[str, dict[str, Any]],
        fast: bool,
    ) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
        """Return {device_id: (port_configs, interface_stats)} for every override-flagged device."""
        logging.info(  # Announce the fetch phase with mode + device count for operator visibility
            "Fetching live device data for %d devices (fast=%s)",
            len(devices_with_overrides),
            fast,
        )
        if fast and len(devices_with_overrides) > 5:  # Fast mode only pays off above the small-batch threshold
            cache = DeviceDataFetcher._fetch_fast(devices_with_overrides)  # Parallel via connection-pool helper
        else:
            cache = DeviceDataFetcher._fetch_sequential(devices_with_overrides)  # One device at a time
        logging.debug("Live data cache populated for %d devices", len(cache))  # Confirm cache size after action
        return cache  # Caller uses this cache to build per-port report rows in the third pass

    @staticmethod
    def _fetch_fast(
        devices_with_overrides: dict[str, dict[str, Any]],
    ) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
        """Parallel fetch using the shared connection-pool execution helper."""
        logging.info(" Using fast mode with connection pool management for device data fetching...")  # legacy log
        work_items = list(devices_with_overrides.items())  # Stable ordering for deterministic logs and retries
        successful_results, failed_devices = _deps.execute_with_connection_pool_management(  # Pool-managed run
            work_items=work_items,
            worker_function=DeviceDataFetcher._worker_fetch_device_data,
            batch_description="override devices",
            retry_function=None,
        )
        cache = DeviceDataFetcher._build_cache_from_results(successful_results, failed_devices)  # Merge results
        logging.info(  # Legacy summary log preserved verbatim for downstream log parsers
            "! Fast mode: Fetched data for %d/%d devices with connection pool protection",
            len(successful_results),
            len(work_items),
        )
        return cache  # Returned to fetch_all for handoff to the third pass

    @staticmethod
    def _build_cache_from_results(
        successful_results: list[tuple[str, dict[str, Any], dict[str, Any]]],
        failed_devices: list[tuple[str, Any]],
    ) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
        """Merge worker results + failed-device entries into the unified device data cache."""
        logging.debug("Merging %d successes + %d failures into cache", len(successful_results), len(failed_devices))
        cache: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}  # Final cache keyed by device_id
        for device_id_result, port_configs, interface_stats in successful_results:  # Successful pool workers
            cache[device_id_result] = (port_configs, interface_stats)  # Store live data for third-pass consumer
        for failed_item in failed_devices:  # Pool-managed helper returns (device_id, info) tuples on failure
            device_id_failed = failed_item[0]  # First tuple element is the original device_id key
            cache[device_id_failed] = ({}, {})  # Empty dicts so third pass still emits a row (with blanks)
        return cache  # Caller logs the totals and proceeds with reporting

    @staticmethod
    def _worker_fetch_device_data(
        device_info: tuple[str, dict[str, Any]],
        connection_semaphore: threading.Semaphore,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Pool worker: fetch port_config + if_stat for one device while holding a slot."""
        device_id_inner = device_info[0]  # First element of the (device_id, info) tuple from work_items
        device_data = device_info[1]  # Second element holds device_name/site_id and friends
        device_name_inner = device_data["device_name"]  # Used purely for log breadcrumbs on failure
        site_id_inner = device_data["site_id"]  # Required for the Mist API path
        with connection_semaphore:  # Honor the global connection-pool slot count from the helper
            port_configs = DeviceDataFetcher._fetch_port_configs(site_id_inner, device_id_inner, device_name_inner)
            interface_stats = DeviceDataFetcher._fetch_interface_stats(
                site_id_inner, device_id_inner, device_name_inner
            )
            return (device_id_inner, port_configs, interface_stats)  # Tuple shape required by pool helper

    @staticmethod
    def _fetch_sequential(
        devices_with_overrides: dict[str, dict[str, Any]],
    ) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
        """Sequential fetch (no connection pool) for small batches or non-fast mode."""
        logging.info("Sequential fetch for %d devices (no connection pool)", len(devices_with_overrides))  # trace
        cache: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}  # Same shape as fast-mode cache
        for device_id, device_info in devices_with_overrides.items():  # One device per iteration
            device_name = device_info["device_name"]  # For breadcrumbs in API error logs
            site_id = device_info["site_id"]  # Required for the Mist API path
            port_configs = DeviceDataFetcher._fetch_port_configs(site_id, device_id, device_name)  # 1 API call
            interface_stats = DeviceDataFetcher._fetch_interface_stats(site_id, device_id, device_name)  # 1 API
            cache[device_id] = (port_configs, interface_stats)  # Same key shape as fast-mode cache
        return cache  # Caller logs totals and proceeds to reporting

    @staticmethod
    def _fetch_port_configs(site_id: str, device_id: str, device_name: str) -> dict[str, Any]:
        """Fetch the port_config dict for one device, returning {} on any API failure."""
        logging.debug("Fetching port_config for %s (%s)", device_name, device_id)  # trace before API call
        try:
            resp = _deps.mistapi.api.v1.sites.devices.getSiteDevice(_deps.apisession, site_id, device_id)  # API
            device_config_data = getattr(resp, "data", {})  # Defensive: SDK may return objects without .data
            return device_config_data.get("port_config", {})  # Missing key still returns the empty dict
        except Exception as exception:  # noqa: BLE001  # Legacy contract: do not crash compliance report
            logging.warning(  # Legacy warning format preserved verbatim for downstream log parsers
                "[WARN] Could not fetch device config for %s (%s): %s",
                device_name,
                device_id,
                exception,
            )
            return {}  # Empty dict so third pass emits a row with blank values rather than aborting

    @staticmethod
    def _fetch_interface_stats(site_id: str, device_id: str, device_name: str) -> dict[str, Any]:
        """Fetch the if_stat dict for one device, returning {} on any API failure."""
        logging.debug("Fetching if_stat for %s (%s)", device_name, device_id)  # trace before API call
        try:
            stats_resp = _deps.mistapi.api.v1.sites.stats.getSiteDeviceStats(  # Mist stats API call
                _deps.apisession, site_id, device_id
            )
            stats_data = getattr(stats_resp, "data", {})  # Defensive: SDK may return objects without .data
            return stats_data.get("if_stat", {})  # Missing key still returns the empty dict
        except Exception as exception:  # noqa: BLE001  # Legacy contract: do not crash compliance report
            DeviceDataFetcher._log_stats_failure(device_name, device_id, exception)  # Specialized warning helper
            return {}  # Empty dict so third pass emits a row with blank values rather than aborting

    @staticmethod
    def _log_stats_failure(device_name: str, device_id: str, exception: Exception) -> None:
        """Emit the legacy warning message for a stats fetch failure, branching on 403 vs other errors."""
        message = str(exception)  # Stringify once for the substring check below
        if "403" in message or "Forbidden" in message:  # 403 is common when token lacks stats permission
            logging.warning(  # Legacy message preserved verbatim for downstream log parsers
                "[WARN] Insufficient permissions to fetch device stats for %s (%s): 403 Forbidden",
                device_name,
                device_id,
            )
            return  # Distinguished log line for permission errors aids operator triage
        logging.warning(  # All other errors use the generic legacy warning line
            "[WARN] Could not fetch device stats for %s (%s): %s",
            device_name,
            device_id,
            exception,
        )
