"""GatewayTestExporter -- gateway synthetic test result exporter.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 37).
Collects per-gateway synthetic test stats (fast-mode concurrent or sequential
paced path), tags each result with site/device identifiers, and writes a CSV
via the standard export backend. ``test_results_by_site`` remains a thin
delegator to the ``src.refactors.serial_cc.test_results_by_site`` service.

Direct imports cover stdlib + installed packages (mistapi, tqdm) plus the
extracted ``ValidationUtils`` (1014 P5). Live-global reads
(``apisession``, ``PROGRESS_EMITTER``, ``ProgressContext``, ``ConfigUtils``,
``GatewayExportUtils``, ``ConnectionPoolExecutor``,
``RateLimitingUtils``, ``DataProcessingUtils``, ``DataExporter``,
``FAST_MODE_*``, ``FastModeBackoffMultiplier``, ``FastModeSequentialMaxRetries``,
``_api_usage_cache``) are resolved via lazy ``mh = importlib.import_module("MistHelper")``
inside each helper. Callers continue to reach the class through the
``MistHelper.GatewayTestExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for synthetic-test lifecycle events.
import time  # WHY: op_start timing + inter-call sleep pacing.
from concurrent.futures import ThreadPoolExecutor, as_completed  # WHY: retry pool for failed devices.
from typing import Any  # WHY: mistapi payloads + heterogeneous stats dicts are duck-typed.

import mistapi  # WHY: direct call to getSiteDeviceSyntheticTest endpoint.
from tqdm import tqdm  # WHY: progress bar for sequential + retry loops.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.validation.validation_utils import ValidationUtils  # WHY: 1014 P5 direct import (FR-005).


class GatewayTestExporter:
    """Gateway Synthetic Test Exports.

    Handles synthetic test result exports and site-level test aggregation for gateways.
    Extracted from GatewayExportUtils.
    """

    @staticmethod
    def _resolve_misthelper_runtime() -> Any:
        """Load MistHelper and wire gateway dependencies before a gateway-test export begins."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy import preserves the extracted module's circular-import boundary.
        logging.info("Configuring gateway dependencies for gateway test export")  # WHY: record the required DI setup.
        mh._configure_gateway_module()  # WHY: gateway inventory needs its APICoreFetchUtils dependency.
        logging.debug(
            "Gateway dependencies configured for gateway test export"
        )  # WHY: confirm DI completed before API work.
        return mh  # WHY: callers also need MistHelper's session and runtime configuration.

    @staticmethod
    def synthetic_tests(fast: bool = False) -> None:
        """Collect + export synthetic test stats for all gateways (optional fast/concurrent path)."""
        mh = (
            GatewayTestExporter._resolve_misthelper_runtime()
        )  # WHY: wire GatewayExportUtils before its inventory lookup.
        logging.debug("[DEBUG] GatewayTestExporter.synthetic_tests invoked with fast=%s", fast)  # Entry trace.
        logging.info("[INFO] Collecting synthetic test stats for all gateways in the org...")  # Log start.
        if fast:  # Fast mode.
            logging.info(" Fast mode enabled: Using cached data and concurrent processing (synthetic tests)")
        emitter = mh.PROGRESS_EMITTER  # Progress emitter.
        if emitter:  # Emitter present.
            emitter.emit_progress_start("16", "synthetic_tests", 1)  # Signal progress start.
        op_start = time.time()  # Start the timer.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        gateway_devices = mh.GatewayExportUtils._get_devices_with_sites(org_id, fast=fast)  # List gateways.
        if not gateway_devices:  # No gateways.
            logging.warning("[WARN] No gateway devices found. Exiting synthetic tests export.")  # Warn.
            return  # Abort.
        all_stats: list[Any] = []  # Accumulate stats.
        if fast:  # Concurrent path.
            GatewayTestExporter._run_synthetic_fast_path(gateway_devices, all_stats)  # Fast pool.
        else:
            GatewayTestExporter._run_synthetic_sequential_path(gateway_devices, all_stats)  # Sequential.
        GatewayTestExporter._export_synthetic_results(all_stats, gateway_devices)  # Write CSV + log.
        GatewayTestExporter._emit_synthetic_complete(emitter, op_start, gateway_devices, all_stats)  # Done.

    @staticmethod
    def _emit_synthetic_complete(
        emitter: Any, op_start: float, gateway_devices: list[Any], all_stats: list[Any]
    ) -> None:
        """Emit final progress-complete signal if an emitter is configured."""
        if not emitter:  # No emitter — nothing to emit.
            return  # Skip silently.
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ProgressContext.
        emitter.emit_progress_complete(  # Signal progress complete.
            mh.ProgressContext("16", "synthetic_tests", len(gateway_devices)),
            len(all_stats),
            False,
            time.time() - op_start,
        )

    @staticmethod
    def _resolve_retry_defaults(max_retries: int | None, retry_delay: float | None) -> tuple[int, float]:
        """Apply FAST_MODE defaults for unset retry budget / delay (returns the tuple)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FAST_MODE_MAX_RETRIES + FAST_MODE_RETRY_DELAY.
        if max_retries is None:  # Default max retries.
            max_retries = mh.FAST_MODE_MAX_RETRIES  # Fast-mode default.
        if retry_delay is None:  # Default retry delay.
            retry_delay = mh.FAST_MODE_RETRY_DELAY  # Fast-mode default.
        return max_retries, retry_delay  # Tuple back to caller

    @staticmethod
    def fetch_synthetic_test_stats_with_retry(
        device_info: tuple[str, str, str, str],
        max_retries: int | None = None,
        retry_delay: float | None = None,
        connection_semaphore: Any = None,
    ) -> dict[str, Any] | None:
        """Fetch synthetic test stats for one gateway with retry + optional connection pool gating."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FastModeBackoffMultiplier.
        max_retries, retry_delay = GatewayTestExporter._resolve_retry_defaults(
            max_retries, retry_delay
        )  # Defaults via helper
        site_id, device_id, _, _ = device_info  # Unpack for backoff/error logs only (names unused here).
        for attempt in range(max_retries + 1):  # Bounded retry loop.
            stats = GatewayTestExporter._try_synthetic_fetch_attempt(
                device_info, attempt, connection_semaphore
            )  # One attempt.
            if stats is not None:  # Success.
                return stats  # Return tagged stats.
            if attempt >= max_retries:  # Out of retries.
                logging.error("! Final attempt failed for device %s at site %s", device_id, site_id)  # Final failure.
                return None  # Give up.
            backoff_delay = retry_delay * (mh.FastModeBackoffMultiplier.VALUE**attempt)  # Exponential backoff.
            logging.info(  # Log the retry.
                "! Fast retry in %.1fs (attempt %s/%s)", backoff_delay, attempt + 2, max_retries + 1
            )
            time.sleep(backoff_delay)  # Wait before retry.
        return None  # Defensive.

    @staticmethod
    def _try_synthetic_fetch_attempt(
        device_info: tuple[str, str, str, str], attempt: int, connection_semaphore: Any
    ) -> dict[str, Any] | None:
        """Single attempt: validate inputs, call API, tag stats, log success. Return stats or None."""
        site_id, device_id, _, _ = device_info  # Unpack for the call + logging (names unused directly here).
        try:
            ValidationUtils.validate_site_id(site_id, "synthetic_tests")  # Validate the site id.
            ValidationUtils.validate_device_id(device_id, "synthetic_tests")  # Validate the device id.
            stats = GatewayTestExporter._call_synthetic_endpoint(site_id, device_id, connection_semaphore)  # Call API.
            GatewayTestExporter._tag_synthetic_stats(stats, device_info, attempt)  # Tag + log success.
            return stats  # Return tagged stats.
        except Exception as exception:  # Fetch failed this attempt.
            logging.warning(  # Warn and let caller handle backoff/retry.
                "! Attempt %s failed for device %s at site %s: %s",
                attempt + 1,
                device_id,
                site_id,
                exception,
            )
            return None  # Signal failure to caller.

    @staticmethod
    def _tag_synthetic_stats(stats: dict[str, Any], device_info: tuple[str, str, str, str], attempt: int) -> None:
        """Mutate ``stats`` with site/device tags and log first-try vs retry success."""
        site_id, device_id, device_name, site_name = device_info  # Unpack the fields.
        stats["site_id"] = site_id  # Tag the site.
        stats["site_name"] = site_name  # Tag the site name.
        stats["device_id"] = device_id  # Tag the device.
        stats["device_name"] = device_name  # Tag the device name.
        if attempt > 0:  # After a retry.
            logging.info("! Retry %s successful for device %s at site %s", attempt, device_name, site_name)
        else:
            logging.info("! Collected synthetic test stats for device %s at site %s", device_name, site_name)

    @staticmethod
    def _call_synthetic_endpoint(site_id: str, device_id: str, connection_semaphore: Any) -> Any:
        """Call ``getSiteDeviceSyntheticTest`` with optional semaphore-gated concurrency."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession live global.
        if connection_semaphore:  # Pool present.
            with connection_semaphore:  # Acquire a slot.
                return mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(mh.apisession, site_id, device_id).data
        return mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(
            mh.apisession, site_id, device_id
        ).data  # Unsemaphored call.

    @staticmethod
    def _run_synthetic_fast_path(gateway_devices: list[Any], all_stats: list[Any]) -> None:
        """Concurrent pool execution with retry on failures + summary instrumentation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConnectionPoolExecutor.
        start_time = time.time()  # Start the timer.

        def fetch_device_stats(device_info: tuple[str, str, str, str], connection_semaphore: Any) -> Any:
            """Worker function that fetches synthetic test stats for a single device."""
            return GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
                device_info, connection_semaphore=connection_semaphore
            )

        successful_results, failed_devices = mh.ConnectionPoolExecutor.execute(  # Pool run.
            work_items=gateway_devices,
            worker_function=fetch_device_stats,
            batch_description="devices",
            retry_function=GatewayTestExporter._retry_failed_synthetic_devices,
        )
        duration = time.time() - start_time  # Compute the duration.
        all_stats.extend(successful_results)  # Collect the results.
        logging.info(  # Log the totals.
            " FAST MODE SUMMARY (synthetic tests): ok=%s fail=%s total=%s elapsed=%.2fs",
            len(successful_results),
            len(failed_devices),
            len(gateway_devices),
            duration,
        )

    @staticmethod
    def _retry_failed_synthetic_devices(
        failed_devices: list[Any], connection_semaphore: Any
    ) -> tuple[list[Any], list[Any]]:
        """Retry failed devices through a small dedicated pool. Return (results, still_failed)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FAST_MODE_RETRY_THREADS.
        from src.refactors.fast_mode_constants import (
            FAST_MODE_MAX_CONCURRENT_CONNECTIONS,
        )  # WHY: post-T-02 direct import from landing module (no more mh.SYMBOL bypass)

        retry_threads = min(  # Size the retry pool.
            mh.FAST_MODE_RETRY_THREADS,
            len(failed_devices),
            max(1, FAST_MODE_MAX_CONCURRENT_CONNECTIONS - 2),
        )
        if retry_threads <= 0:  # No threads available.
            logging.warning(" FAST MODE: No available threads for retry; skipping retries")
            return [], failed_devices  # Return original failures.
        retry_results: list[Any] = []  # Collect retry results.
        still_failed: list[Any] = []  # Track still-failed devices.
        with ThreadPoolExecutor(max_workers=retry_threads) as executor:  # Run the retry pool.
            retry_futures = GatewayTestExporter._submit_synthetic_retries(
                executor, failed_devices, connection_semaphore
            )  # Build future map.
            for future in tqdm(  # type: ignore[no-untyped-call]
                as_completed(retry_futures),
                total=len(retry_futures),
                desc="Retrying Failed",
                unit="device",
            ):
                GatewayTestExporter._record_retry_outcome(future, retry_futures, retry_results, still_failed)
        return retry_results, still_failed  # Return results and failures.

    @staticmethod
    def _submit_synthetic_retries(
        executor: ThreadPoolExecutor, failed_devices: list[Any], connection_semaphore: Any
    ) -> dict[Any, Any]:
        """Submit retry calls for every failed device and return the future->device map."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FAST_MODE_RETRY_MAX_RETRIES.
        return {  # Map futures to devices.
            executor.submit(
                GatewayTestExporter.fetch_synthetic_test_stats_with_retry,
                device_info,
                max_retries=mh.FAST_MODE_RETRY_MAX_RETRIES,
                connection_semaphore=connection_semaphore,
            ): device_info
            for device_info in failed_devices
        }

    @staticmethod
    def _record_retry_outcome(
        future: Any, retry_futures: dict[Any, Any], retry_results: list[Any], still_failed: list[Any]
    ) -> None:
        """Inspect one future's result, append to the matching bucket, log the outcome."""
        device_info = retry_futures[future]  # Resolve the device info.
        try:
            result = future.result()  # Read the result.
            if result:  # Have a result.
                retry_results.append(result)  # Collect it.
                logging.info(" FAST RETRY OK: %s", device_info[2])  # Log retry success.
            else:
                still_failed.append(device_info)  # Still failed.
                logging.error(" FAST RETRY FAIL: %s", device_info[2])  # Log retry failure.
        except Exception as exception:  # Retry raised.
            still_failed.append(device_info)  # Still failed.
            logging.error(" FAST RETRY EXC: %s -> %s", device_info[2], exception)  # Log exception.

    @staticmethod
    def _run_synthetic_sequential_path(gateway_devices: list[Any], all_stats: list[Any]) -> None:
        """Sequential processing with adaptive rate limiting (original behavior)."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of FastModeSequentialMaxRetries + RateLimitingUtils + apisession + _api_usage_cache.
        smoothed = None  # No smoothed delay yet.
        for device_info in tqdm(  # type: ignore[no-untyped-call]
            gateway_devices, desc="Gateway Devices", unit="device"
        ):
            result = GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
                device_info, max_retries=mh.FastModeSequentialMaxRetries.VALUE
            )
            if result:  # Have a result.
                all_stats.append(result)  # Collect it.
            smoothed, delay = mh.RateLimitingUtils.get_rate_limited_delay(  # type: ignore[no-untyped-call]
                smoothed, mh.apisession, mh._api_usage_cache
            )
            logging.info("[INFO] Sleeping for %.2fs.", delay)  # Log the sleep.
            time.sleep(delay)  # Pace the API.

    @staticmethod
    def _export_synthetic_results(all_stats: list[Any], gateway_devices: list[Any]) -> None:
        """Write the aggregated stats to CSV + log totals (or warn when empty)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if not all_stats:  # No results.
            logging.warning(" No synthetic test results found. CSV not created.")  # Warn.
            print("! No synthetic test results found. CSV not created.")  # Tell the user.
            return  # Nothing to write.
        filename = "AllGatewaySyntheticTests.csv"  # Build the CSV name.
        flattened = DataProcessingUtils.flatten_nested_fields(all_stats)  # Flatten nested fields.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(sanitized, filename)  # type: ignore[no-untyped-call]
        print(f"! {len(all_stats)} gateway synthetic test results exported to {filename}")  # Tell user.
        logging.info("! Synthetic test results saved to %s (%s records).", filename, len(all_stats))
        logging.info(  # Log the optimization summary.
            "! API Optimization: Saved %s listSiteDevices calls by using cached inventory",
            len(gateway_devices),
        )

    @staticmethod
    def test_results_by_site(fast: bool = False) -> None:  # Export tests by site.
        """Delegator: all logic lives in src/refactors/serial_cc/test_results_by_site.py."""
        GatewayTestExporter._resolve_misthelper_runtime()  # WHY: the service uses wired gateway helpers.
        from src.refactors.serial_cc.test_results_by_site import GatewayTestResultsService  # noqa: PLC0415

        GatewayTestResultsService.execute(fast=fast)  # Delegate to extracted service; keeps CC at A(1)
