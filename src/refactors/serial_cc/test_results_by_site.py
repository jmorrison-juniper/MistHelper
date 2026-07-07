"""Gateway synthetic test results export extracted from MistHelper GatewayTestExporter offender."""

import csv  # Read cached OrgInventory.csv to derive site IDs in fast mode
import importlib  # Late-import MistHelper to avoid circular src<->MistHelper dependency
import logging  # Emit action-level tracing required by coding standards
import time  # Measure elapsed duration for fast-mode summary and rate-limit delay
from types import SimpleNamespace  # Bundle runtime dependencies without a formal dataclass
from typing import Any  # MistHelper surface is dynamic; typed as Any at the boundary

from src.refactors.connection_pool_executor import ConnectionPoolExecutor  # Pool executor extracted per 1012 SC-003


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static cross-module imports."""
    logging.info("Resolving GatewayTestResultsService runtime dependencies from MistHelper")  # Log before import
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular src->MistHelper dependency
    logging.debug("Runtime dependencies resolved successfully")  # Log after successful resolution
    return SimpleNamespace(
        ConfigUtils=misthelper_module.ConfigUtils,  # Org ID prompt/cache utility
        CacheUtils=misthelper_module.CacheUtils,  # CSV cache existence checker
        OrgInventoryExporter=misthelper_module.OrgInventoryExporter,  # Inventory regeneration callback
        FilePathUtils=misthelper_module.FilePathUtils,  # Canonical data/ path resolver
        GatewayExportUtils=misthelper_module.GatewayExportUtils,  # API-based site-ID discovery
        ValidationUtils=misthelper_module.ValidationUtils,  # site_id format validator
        DataProcessingUtils=misthelper_module.DataProcessingUtils,  # Flatten and sanitise helpers
        DataExporter=misthelper_module.DataExporter,  # Persist output to configured backend
        RateLimitingUtils=misthelper_module.RateLimitingUtils,  # Adaptive rate-limit delay calculator
        # Pool manager -- distributes work items across a bounded connection semaphore (1012 SC-003 rename)
        execute_fn=ConnectionPoolExecutor.execute,
        mistapi=misthelper_module.mistapi,  # Mist SDK root
        apisession=misthelper_module.apisession,  # Active API session
        _api_usage_cache=getattr(misthelper_module, "_api_usage_cache", {}),  # API usage telemetry cache
        tqdm=misthelper_module.tqdm,  # Progress-bar wrapper used across MistHelper
    )


class GatewayTestResultsService:
    """Owns the gateway synthetic test results export workflow, formerly embedded in GatewayTestExporter."""

    @staticmethod
    def _fetch_site_tests(deps: SimpleNamespace, site_id: str, connection_semaphore: Any) -> list[dict[str, Any]]:
        """Fetch all synthetic test results for one site, honouring an optional connection semaphore."""
        logging.info("Fetching synthetic test results for site %s", site_id)  # Log before API call
        try:
            deps.ValidationUtils.validate_site_id(
                site_id, "GatewayTestResultsService._fetch_site_tests"
            )  # Reject malformed site_id before issuing API call
            response = GatewayTestResultsService._invoke_search_api(deps, site_id, connection_semaphore)
            results = GatewayTestResultsService._extract_tagged_results(response, site_id)  # Parse+tag
            logging.debug("Retrieved %d test results for site %s", len(results), site_id)  # Log after success
            return results  # Return tagged result rows for the caller to accumulate
        except Exception as exception:  # Non-fatal: skip this site and continue to the next
            logging.warning("Failed to fetch test results for site %s: %s", site_id, exception)  # Warn with context
            return []  # Return empty list so caller continues to the next site

    @staticmethod
    def _invoke_search_api(deps: SimpleNamespace, site_id: str, connection_semaphore: Any) -> Any:
        """Call searchSiteSyntheticTest, honouring an optional connection semaphore."""
        # WHY: extracted so _fetch_site_tests drops from 29 lines to <25 and CC from 6 to <=5.
        if connection_semaphore:  # Pool-managed path acquires semaphore before call
            with connection_semaphore:  # Limit concurrent connections via semaphore
                return deps.mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest(
                    deps.apisession, site_id
                )  # Fetch test results under semaphore
        return deps.mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest(
            deps.apisession, site_id
        )  # Sequential path — fetch test results directly without a semaphore

    @staticmethod
    def _extract_tagged_results(response: Any, site_id: str) -> list[dict[str, Any]]:
        """Return the results list from ``response.data``, tagging each row with ``site_id``."""
        # WHY: extracted so _fetch_site_tests drops from 29 lines to <25 and CC from 6 to <=5.
        if not hasattr(response, "data"):  # Guard against malformed API responses
            logging.warning("No data attribute in response for site %s", site_id)  # Warn for diagnostics
            return []  # Return empty list so caller accumulates cleanly
        results: list[dict[str, Any]] = (
            response.data.get("results", []) if isinstance(response.data, dict) else []
        )  # Extract result list from dict payload; empty list for unexpected shapes
        for result in results:  # Tag every row with its source site_id for downstream joins
            result["site_id"] = site_id  # Tag every row with its source site_id
        return results  # Hand back the tagged rows to the caller

    @staticmethod
    def _load_fast_site_ids(deps: SimpleNamespace) -> list[str]:
        """Derive site IDs with gateways from cached inventory CSV (fast-path optimisation)."""
        logging.info("Loading site IDs with gateways from cached OrgInventory.csv")  # Log before CSV read
        deps.CacheUtils.check_and_generate_csv(
            "OrgInventory.csv", deps.OrgInventoryExporter.inventory
        )  # Ensure cached CSV exists before opening it
        inventory_path = deps.FilePathUtils.get_csv_path("OrgInventory.csv")  # Resolve canonical data/ path
        with open(inventory_path, encoding="utf-8") as file:  # Open the cached inventory CSV
            reader = csv.DictReader(file)  # Parse rows as dicts keyed by header
            raw_ids = [
                str(row.get("site_id"))
                for row in reader
                if row.get("type") == "gateway" and row.get("site_id") and str(row.get("site_id")).strip()
            ]  # Extract site_ids for gateway-type rows only (excludes empty/None)
        deduped = list(dict.fromkeys(sorted(raw_ids)))  # Sort then deduplicate while preserving insertion order
        logging.info("Loaded %d site_ids with gateways from cached inventory", len(deduped))  # Log after CSV read
        return deduped  # Return deduplicated, sorted site_ids

    @classmethod
    def _collect_fast(cls, deps: SimpleNamespace, site_ids: list[str]) -> list[dict[str, Any]]:
        """Collect results concurrently via connection pool (fast-path)."""
        logging.info("Starting fast-mode concurrent fetch for %d sites", len(site_ids))  # Log before pool
        start_time = time.time()  # Track elapsed time for fast-mode summary logging
        successful_results, failed_sites = deps.execute_fn(  # Pool run via ConnectionPoolExecutor (1012 SC-003)
            work_items=site_ids,
            worker_function=lambda site_id, sem: cls._fetch_site_tests(deps, site_id, sem),
            batch_description="sites",
        )  # Distribute site fetches across the connection pool; lambda avoids ARCH-DELEGATE inner function
        flattened: list[dict[str, Any]] = []  # Accumulates flattened results from all site lists
        for site_list in successful_results:  # successful_results is a list-of-lists
            if isinstance(site_list, list):  # Defensive guard for unexpected pool result shapes
                flattened.extend(site_list)  # Flatten each site's result list into the accumulator
        duration = time.time() - start_time  # Compute elapsed seconds for the summary
        logging.info(
            "Fast-mode complete: ok_sites=%d fail_sites=%d total=%d records=%d elapsed=%.2fs",
            len(successful_results),
            len(failed_sites),
            len(site_ids),
            len(flattened),
            duration,
        )  # Structured summary log after pool completes
        return flattened  # Return flattened results from all sites

    @classmethod
    def _collect_sequential(cls, deps: SimpleNamespace, site_ids: list[str]) -> list[dict[str, Any]]:
        """Collect results sequentially with adaptive rate limiting (standard path)."""
        logging.info("Starting sequential fetch for %d sites with gateways", len(site_ids))  # Log before loop
        all_results: list[dict[str, Any]] = []  # Accumulates results across all sites
        smoothed = None  # Adaptive rate-limit smoothing state; reset at the start of each run
        for site_id in deps.tqdm(site_ids, desc="Sites", unit="site"):  # Iterate with progress bar
            results = cls._fetch_site_tests(deps, site_id, connection_semaphore=None)  # Fetch site results
            if results:  # Only extend when the site returned data
                all_results.extend(results)  # Add site results to accumulator
            smoothed, delay = deps.RateLimitingUtils.get_rate_limited_delay(
                smoothed, deps.apisession, deps._api_usage_cache
            )  # Compute adaptive delay from API usage telemetry
            time.sleep(delay)  # Honour rate-limit delay before the next site
        total_results = len(all_results)  # Precompute total count for log line brevity
        total_sites = len(site_ids)  # Precompute site count for log line brevity
        logging.info("Sequential fetch complete: %d results across %d sites", total_results, total_sites)
        return all_results  # Return accumulated results from all sites

    @staticmethod
    def _export_results(deps: SimpleNamespace, all_results: list[dict[str, Any]], fast: bool) -> None:
        """Flatten, sanitise, and persist results; emit user-facing summary."""
        if not all_results:  # No results found across all sites
            logging.warning("No test results found; CSV not created")  # Warn so operator can investigate
            print("! No gateway test results found. CSV not created.")  # User-facing empty-result message
            return  # Exit early — nothing to write
        filename = "AllGatewayTestResults.csv"  # Canonical output file name (contract with callers)
        logging.info("Exporting %d gateway test results to %s", len(all_results), filename)  # Log before export
        flattened = deps.DataProcessingUtils.flatten_nested_fields(all_results)  # Flatten nested structures
        sanitized = deps.DataProcessingUtils.escape_multiline(flattened)  # Sanitise multiline CSV fields
        deps.DataExporter.write_with_format_selection(sanitized, filename)  # Write to configured output backend
        logging.debug("Exported %d records to %s", len(sanitized), filename)  # Log after successful write
        print(f"! {len(all_results)} gateway test results exported to {filename}")  # User-facing count
        logging.info("All test results saved to %s (%d records)", filename, len(all_results))  # Trace final count
        if fast:  # Only log the fast-mode optimisation note when relevant
            logging.info(
                "API Optimization: Used cached inventory to derive site IDs, reducing API calls"
            )  # Inform operator why fast mode is faster

    @classmethod
    def execute(cls, fast: bool = False) -> None:
        """Export all synthetic test results for sites with gateways."""
        logging.info("Starting GatewayTestResultsService export (fast=%s)", fast)  # Log before workflow
        deps = _resolve_runtime_dependencies()  # Resolve all collaborators from MistHelper at call time
        print("Gateway Synthetic Test Results:")  # User-facing operation banner
        logging.info(
            "Searching all test results (including speed tests) for sites with gateways"
        )  # Trace workflow intent
        if fast:  # Announce fast-mode activation so operator can see it in logs
            logging.info("Fast mode: using cached inventory and concurrent site processing")  # Trace activation
        org_id = deps.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve target org (cached or prompted)
        logging.debug("Resolved org_id: %s", org_id)  # Trace org resolution
        site_ids = cls._resolve_site_ids(deps, org_id, fast)  # Discover sites with gateways
        if not site_ids:  # No gateway sites found in org
            logging.warning("No sites with gateways found for org %s", org_id)  # Warn for visibility
            return  # Exit early without producing an empty CSV
        all_results = cls._collect_fast(deps, site_ids) if fast else cls._collect_sequential(deps, site_ids)
        cls._export_results(deps, all_results, fast)  # Flatten, sanitise, and write results to CSV
        logging.info("GatewayTestResultsService export complete")  # Log after full workflow

    @classmethod
    def _resolve_site_ids(cls, deps: SimpleNamespace, org_id: str, fast: bool) -> list[str]:
        """Discover site IDs with gateways via cache (fast) or API (standard)."""
        logging.info("Resolving site IDs with gateways (fast=%s)", fast)  # Log before discovery
        if fast:  # Fast path: avoid full inventory API call by reading cached CSV
            try:
                site_ids = cls._load_fast_site_ids(deps)  # Load site IDs from cached OrgInventory CSV
                if site_ids:  # Cache hit
                    return site_ids  # Return cache-derived site IDs
                logging.warning("Fast-mode cache empty; falling back to API discovery")  # Warn about fallback
            except Exception as exception:  # Cache failure is non-fatal; fall back to API
                logging.warning("Fast-mode site derivation failed (%s); falling back to API", exception)  # Trace
        logging.info("Discovering site IDs via API for org %s", org_id)  # Log before API call
        raw = deps.GatewayExportUtils._get_site_ids_with_devices(org_id)  # Full API discovery; returns Any
        site_ids = list(raw) if raw else []  # Cast Any->list[str] for mypy (GatewayExportUtils returns list)
        logging.debug("API discovery returned %d site IDs", len(site_ids))  # Log after API call
        return site_ids  # Return API-discovered site IDs
