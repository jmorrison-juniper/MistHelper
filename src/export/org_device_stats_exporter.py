"""OrgDeviceStatsExporter -- org device/port/VPN peer stats exporters (Menus 13-16).

Extracted from MistHelper.py during initiative 1013 (Cat B, position 45)
under the SC-001 facade pattern. Handles device stats, port stats, VPN
peer stats, and VC stats exports. Fast mode caches recent CSV
(CSV_FRESHNESS_MINUTES) and parallelizes site fetches with bounded
concurrency; non-fast mode issues one org-level paginated call.

Direct imports cover stdlib (concurrent.futures, csv, importlib, logging,
os, time) and third-party (tqdm). Every live-global read
(``CSV_FRESHNESS_MINUTES``, ``PROGRESS_EMITTER``, ``mistapi``,
``apisession``, ``TimeUtils``, ``APIDataFetcher``, ``ProgressContext``,
``OrgSiteExporter``, ``CacheUtils``, ``FilePathUtils``,
``DataProcessingUtils``, ``DataExporter``, ``ConfigUtils``,
``ConnectionPoolExecutor``, ``FAST_MODE_*`` constants,
``FastModeBackoffMultiplier``) is resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside the methods that
need them. Callers continue to reach the class through the
``MistHelper.OrgDeviceStatsExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import concurrent.futures  # WHY: as_completed for retry pool.
import csv  # WHY: parse cached SiteList.csv.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace + info/warn/error logging.
import os  # WHY: filesystem cache freshness checks.
import time  # WHY: wall-time epoch + elapsed timing.
from concurrent.futures import ThreadPoolExecutor  # WHY: bounded retry worker pool.

from tqdm import tqdm  # WHY: progress bar during retry pool.


class OrgDeviceStatsExporter:  # Org device-stats exporters.
    """Organization Device Statistics Exporter.

    Handles device stats, port stats, VPN peer stats, and VC stats exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def _device_stats_cache_hit(output_file: str, fast: bool) -> bool:
        """Return True if fast-mode cache for OrgDeviceStats can be reused."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CSV_FRESHNESS_MINUTES.
        if not (fast and os.path.exists(output_file)):  # Cache reuse needs both flag + file
            return False  # No cache path available
        try:
            mtime = os.path.getmtime(output_file)  # Read file modified time
            age_minutes = (time.time() - mtime) / 60.0  # Compute file age in minutes
            if age_minutes < mh.CSV_FRESHNESS_MINUTES:  # Cache still fresh
                logging.info(  # Log cache reuse
                    " Fast mode cache hit: %s is fresh (%.1fm < %sm); skipping fetch.",
                    output_file,
                    age_minutes,
                    mh.CSV_FRESHNESS_MINUTES,
                )
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # User notice
                return True  # Caller skips re-fetch
        except Exception as e:  # Freshness-check error
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, e)  # Log
        return False  # Cache stale or unreadable

    @staticmethod
    def device_stats(fast: bool = False):  # Export org device stats.
        """Export statistics for all devices in the organization to OrgDeviceStats.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live globals.
        output_file = "OrgDeviceStats.csv"  # Output filename
        if OrgDeviceStatsExporter._device_stats_cache_hit(output_file, fast):  # Fast cache check
            return  # Skip re-fetch when cache fresh
        logging.info("Starting export of organization device statistics...")  # Log start
        emitter = mh.PROGRESS_EMITTER  # Capture progress emitter
        if emitter:
            emitter.emit_progress_start("13", "device_stats", 1)  # Emit progress start
        op_start = time.time()  # Record operation start time
        hours = mh.TimeUtils.get_dynamic_lookback_hours(24, 1)  # Dynamic lookback hours
        mh.TimeUtils.log_dynamic_lookback("org device statistics export", hours)  # Log lookback window
        mh.APIDataFetcher(  # Fetch and write device stats
            title="Org Device Stats:",
            api_call=mh.mistapi.api.v1.orgs.stats.listOrgDevicesStats,
            filename=output_file,
            sort_key="type",
            type="all",
            duration=f"{hours}h",
            limit=1000,
        ).execute()
        if emitter:
            emitter.emit_progress_complete(
                mh.ProgressContext("13", "device_stats", 1), 1, False, time.time() - op_start
            )

    @staticmethod
    def _port_stats_cache_hit(output_file: str, fast: bool) -> bool:  # Check port-stats cache hit.
        """Return True when fast mode can safely reuse a fresh cached CSV."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CSV_FRESHNESS_MINUTES.
        if not (fast and os.path.exists(output_file)):  # Cache reuse needs flag + file
            return False  # No valid cache path
        try:  # Filesystem metadata lookup should never crash export path
            mtime = os.path.getmtime(output_file)  # Read last-modified time
            age_minutes = (time.time() - mtime) / 60.0  # Convert to minutes
            if age_minutes < mh.CSV_FRESHNESS_MINUTES:  # Fresh cache means skip API
                logging.info(
                    " Fast mode cache hit: %s is fresh (%.1fm < %sm); skipping fetch.",
                    output_file,
                    age_minutes,
                    mh.CSV_FRESHNESS_MINUTES,
                )  # Record why no API calls were made
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # User notice
                return True  # Caller can return early
        except Exception as exception:  # Cache metadata problems degrade gracefully
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, exception)  # Log fallback
        return False  # Cache missing, stale, or unreadable

    @staticmethod
    def _load_port_stats_sites_from_api(org_id: str) -> list[tuple[str | None, str]]:
        """API fallback path for loading port-stats sites when cache fails."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        site_response = mh.mistapi.api.v1.orgs.sites.listOrgSites(mh.apisession, org_id, limit=1000)  # API fallback
        site_data = mh.mistapi.get_all(response=site_response, mist_session=mh.apisession)  # Paginate
        sites = [
            (site.get("id"), site.get("name", "Unknown")) for site in site_data if site.get("id")
        ]  # Normalize into worker tuples
        logging.info("* Fetched %s sites from API", len(sites))  # API fallback count for cache-miss visibility
        logging.debug(
            "First site sample: %s, type: %s",
            sites[0] if sites else "No sites",
            type(sites[0]) if sites else "N/A",
        )  # One sample tuple for debug
        return sites  # Normalized site tuples for fast-mode worker pool

    @staticmethod
    def _log_first_site_sample(sites: list) -> None:
        """Emit a debug sample (first row + type) for cached-site lists, with empty-list fallback."""
        if sites:  # Non-empty: log the first row and its concrete type
            sample = sites[0]
            sample_type = type(sites[0])
        else:  # Empty: still emit placeholders so log lines stay parseable
            sample = "No sites"
            sample_type = "N/A"
        logging.debug("First site sample: %s, type: %s", sample, sample_type)  # Sample for malformed-row debug

    @staticmethod
    def _load_sites_from_cached_csv() -> list[tuple[str | None, str]] | None:
        """Read SiteList cache and return tuples, or ``None`` when the cache cannot be used."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils/OrgSiteExporter/FilePathUtils.
        try:  # Prefer cached site CSV to avoid extra API call
            mh.CacheUtils.check_and_generate_csv("SiteList.csv", mh.OrgSiteExporter.sites)  # Ensure CSV exists
            site_list_path = mh.FilePathUtils.get_csv_path("SiteList.csv")  # Resolve path
            with open(site_list_path, encoding="utf-8") as file:  # Open cached CSV
                reader = csv.DictReader(file)  # Parse rows
                sites = [
                    (row.get("id"), row.get("name", "Unknown")) for row in reader if row.get("id")
                ]  # Build tuple list used by pool workers
        except Exception as exception:  # Cache read failure -> signal API fallback
            logging.warning("* Could not use cached sites, fetching from API: %s", exception)  # Explain fallback
            return None
        logging.info("* Loaded %s sites from cached data", len(sites))  # Confirm cached count
        OrgDeviceStatsExporter._log_first_site_sample(sites)  # Debug sample for malformed rows
        return sites

    @staticmethod
    def _load_port_stats_sites(org_id: str) -> list[tuple[str | None, str]]:  # Load sites for port stats.
        """Load site identifiers and names for fast-mode per-site port stats collection."""
        sites = OrgDeviceStatsExporter._load_sites_from_cached_csv()  # Cache-first path
        if sites is not None:  # Cache hit (possibly empty list)
            return sites
        return OrgDeviceStatsExporter._load_port_stats_sites_from_api(org_id)  # API fallback

    @staticmethod
    def _attempt_site_port_stats_fetch(site_id, site_name, connection_semaphore):
        """Single fetch attempt for one site's port stats; returns list or raises."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        with connection_semaphore:  # Bound concurrent API calls
            response = mh.mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts(mh.apisession, site_id, limit=1000)
            port_stats = mh.mistapi.get_all(response=response, mist_session=mh.apisession)  # Paginate
        if not isinstance(port_stats, list):  # Defensive type check
            logging.error(
                "! API returned non-list type for site %s: type=%s, value=%s",
                site_name,
                type(port_stats),
                port_stats,
            )  # Log malformed payload
            return []  # Empty for malformed sites
        for stat in port_stats:  # Annotate each port row with site metadata
            stat["site_id"] = site_id  # Persist site identifier
            stat["site_name"] = site_name  # Persist site name
        return port_stats  # Annotated rows for caller

    @staticmethod
    def _handle_site_port_stats_retry(attempt, site_name, exception):
        """Backoff + log retry; return True if more attempts remain."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FAST_MODE_* + FastModeBackoffMultiplier.
        if attempt < mh.FAST_MODE_MAX_RETRIES:  # More retries remain
            backoff_delay = mh.FAST_MODE_RETRY_DELAY * (mh.FastModeBackoffMultiplier.VALUE**attempt)  # Backoff curve
            logging.warning("! Attempt %s failed for site %s: %s", attempt + 1, site_name, exception)  # Log fail
            logging.info(
                "! Retrying in %.1fs (attempt %s/%s)",
                backoff_delay,
                attempt + 2,
                mh.FAST_MODE_MAX_RETRIES + 1,
            )  # When next retry will occur
            time.sleep(backoff_delay)  # Pause before retry
            return True  # Continue loop
        logging.error("! Final attempt failed for site %s: %s", site_name, exception)  # Terminal failure
        return False  # No more retries

    @staticmethod
    def _fetch_site_port_stats(site_info, connection_semaphore):  # Fetch port stats for a site.
        """Fetch one site's switch/gateway port stats with bounded concurrency and retries."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FAST_MODE_MAX_RETRIES.
        site_id, site_name = site_info  # Unpack tuple
        for attempt in range(mh.FAST_MODE_MAX_RETRIES + 1):  # Retry loop
            try:
                port_stats = OrgDeviceStatsExporter._attempt_site_port_stats_fetch(
                    site_id, site_name, connection_semaphore
                )
                if attempt > 0:  # Retries that later succeed get info-level log
                    logging.info(
                        "! Retry %s successful for site %s (%s records)",
                        attempt,
                        site_name,
                        len(port_stats),
                    )  # Successful retry outcome
                else:
                    logging.debug("! Collected %s port stats from site %s", len(port_stats), site_name)  # First-try
                return port_stats  # Annotated rows
            except Exception as exception:  # Retry on transient failure
                if not OrgDeviceStatsExporter._handle_site_port_stats_retry(attempt, site_name, exception):
                    return []  # Final failure path
        return []  # Defensive fallback

    @staticmethod
    def _process_retry_future(future, retry_futures, retry_results, still_failed):
        """Resolve one retried-site future; mutate retry_results + still_failed."""
        site_info = retry_futures[future]  # Recover original site tuple
        try:
            result = future.result()  # Resolve retried site rows
            if result:  # Site recovered
                retry_results.extend(result)  # Merge recovered rows
                logging.info(" FAST RETRY OK: %s", site_info[1])  # Record recovered site
            else:  # Site still failed logically
                still_failed.append(site_info)  # Keep for summary
                logging.warning(" FAST RETRY EMPTY: %s", site_info[1])  # Record unresolved
        except Exception as exception:  # Future itself raised unexpectedly
            still_failed.append(site_info)  # Preserve in failure list
            logging.error(" FAST RETRY EXC: %s -> %s", site_info[1], exception)  # Log

    @staticmethod
    def _dispatch_site_port_retries(failed_sites, connection_semaphore, retry_threads, retry_results, still_failed):
        """Run bounded retry pool and partition outcomes into retry_results / still_failed in place."""
        with ThreadPoolExecutor(max_workers=retry_threads) as executor:  # Bounded retry concurrency
            retry_futures = {
                executor.submit(OrgDeviceStatsExporter._fetch_site_port_stats, s, connection_semaphore): s
                for s in failed_sites
            }
            futures_list = list(retry_futures.keys())  # Materialize for tqdm total
            with tqdm(total=len(futures_list), desc="Retrying Failed Sites", unit="site") as pbar:  # type: ignore[call-arg, no-untyped-call]
                for future in concurrent.futures.as_completed(futures_list):  # Handle results as they complete
                    OrgDeviceStatsExporter._process_retry_future(future, retry_futures, retry_results, still_failed)
                    pbar.update(1)  # Advance progress

    @staticmethod
    def _retry_failed_site_port_stats(failed_sites, connection_semaphore):  # Retry failed site port stats.
        """Retry previously failed site fetches using a smaller worker pool."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FAST_MODE_RETRY_THREADS/MAX_CONCURRENT.
        retry_results: list = []  # Successful retry rows
        still_failed: list = []  # Sites remaining failed after retries
        retry_threads = min(
            mh.FAST_MODE_RETRY_THREADS, len(failed_sites), max(1, mh.FAST_MODE_MAX_CONCURRENT_CONNECTIONS - 2)
        )  # Smaller retry pool
        if retry_threads <= 0:  # Defensive guard
            logging.warning(" FAST MODE: No available threads for retry; skipping retries")  # Explain skip
            return [], failed_sites  # Preserve failed sites
        OrgDeviceStatsExporter._dispatch_site_port_retries(
            failed_sites, connection_semaphore, retry_threads, retry_results, still_failed
        )
        return retry_results, still_failed  # Return recovered rows + unresolved sites

    @staticmethod
    def _flatten_site_port_results(successful_results):  # Flatten site port results.
        """Flatten pooled worker results into one list of port-stat rows."""
        all_port_stats = []  # Accumulate all site-level rows into one export list.
        for index, result_list in enumerate(
            successful_results
        ):  # Inspect each worker result for defensive type handling.
            logging.debug(
                "Processing result %s: type=%s, is_list=%s", index, type(result_list), isinstance(result_list, list)
            )  # Log shape of each pooled result before flattening.
            if isinstance(result_list, list):  # Only list payloads are valid worker outputs.
                all_port_stats.extend(result_list)  # Merge valid site rows into the combined export list.
            else:  # Unexpected worker payloads should be visible but not fatal.
                logging.warning(
                    "Unexpected result type at index %s: %s, value: %s", index, type(result_list), result_list
                )  # Surface unexpected worker output for debugging.
        return all_port_stats  # Return flattened org-wide port-stat list for sorting and export.

    @staticmethod
    def _save_device_port_stats_output(all_port_stats, output_file: str) -> None:  # Save device port stats output.
        """Sort, sanitize, and persist collected port-stat rows."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils/DataExporter.
        if not all_port_stats:  # Empty dataset should skip file creation and clearly tell the operator why.
            logging.warning(" No port statistics collected. CSV not created.")  # Log absence of exportable data.
            print("! No port statistics collected. CSV not created.")  # Tell operator no file was written.
            return  # Nothing to sort or write.
        try:  # Sorting is best-effort because some rows may lack MACs.
            all_port_stats = sorted(
                all_port_stats, key=lambda row: row.get("mac", "")
            )  # Sort by MAC to produce deterministic CSV ordering.
        except Exception as exception:  # Sorting failures should not block export.
            logging.debug("Could not sort by MAC: %s", exception)  # Record sort failure while continuing unsorted.
        flattened = mh.DataProcessingUtils.flatten_nested_fields(
            all_port_stats
        )  # Normalize nested API payloads into flat CSV-friendly records.
        sanitized = mh.DataProcessingUtils.escape_multiline(flattened)  # type: ignore[no-untyped-call]  # Escape embedded newlines so CSV stays row-stable.
        mh.DataExporter.write_with_format_selection(sanitized, output_file, api_function_name="searchSiteSwOrGwPorts")  # type: ignore[no-untyped-call]  # Persist to configured backend with endpoint metadata.
        print(
            f"! {len(all_port_stats)} port stat records exported to {output_file}"
        )  # Confirm output row count to the operator.
        logging.info(
            "! Port statistics saved to %s (%s records)", output_file, len(all_port_stats)
        )  # Record successful export count in logs.

    @staticmethod
    def _validate_fast_port_stats_start_time(start_time) -> None:
        """Defensive guard: fail loudly if start_time is not numeric (catches monkeypatch corruption)."""
        if isinstance(start_time, (int, float)):  # Normal numeric value -- nothing to do.
            return
        logging.error(
            "! CRITICAL: start_time is not a number! type=%s, value=%s", type(start_time), start_time
        )  # Surface impossible state.
        logging.error("! time module type: %s, time.time type: %s", type(time), type(time.time))  # Debugging context.
        raise TypeError(f"start_time must be a number, got {type(start_time)}")  # Elapsed calc would be invalid.

    @staticmethod
    def _log_fast_port_stats_summary(sites, failed_sites, all_port_stats, duration) -> None:
        """Emit operator-facing summary + structured log for fast-mode port stats run."""
        ok_count = len(sites) - len(failed_sites)  # Successful site count.
        fail_count = len(failed_sites)  # Failed site count.
        record_count = len(all_port_stats)  # Total port-stat rows collected.
        logging.info(
            " FAST MODE SUMMARY (port stats): sites_ok=%s sites_fail=%s records=%s elapsed=%.2fs",
            ok_count,
            fail_count,
            record_count,
            duration,
        )  # Structured run summary.
        print(
            f"* Fast mode: Collected {record_count} port stat records from {ok_count}/{len(sites)} sites in {duration:.1f}s"  # noqa: E501
        )  # Operator timing summary.

    @staticmethod
    def _run_fast_device_port_stats(output_file: str) -> None:  # Run fast device port stats.
        """Execute fast-mode site-parallel port stats collection and output."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils/ConnectionPoolExecutor.
        logging.info(
            "* Fast mode: Parallelizing port stats retrieval across sites"
        )  # Announce fast-mode collection strategy.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org ID once before site discovery.
        sites = OrgDeviceStatsExporter._load_port_stats_sites(org_id)  # Load normalized site tuples from cache or API.
        start_time = time.time()  # Capture start time for performance summary.
        OrgDeviceStatsExporter._validate_fast_port_stats_start_time(start_time)  # Defensive numeric-type guard.
        successful_results, failed_sites = (
            mh.ConnectionPoolExecutor.execute(  # Bounded-concurrency site collection with retry.
                work_items=sites,
                worker_function=OrgDeviceStatsExporter._fetch_site_port_stats,
                batch_description="sites",
                retry_function=OrgDeviceStatsExporter._retry_failed_site_port_stats,
            )
        )
        all_port_stats = OrgDeviceStatsExporter._flatten_site_port_results(
            successful_results
        )  # Collapse per-site results.
        duration = time.time() - start_time  # Elapsed seconds for operator summary.
        OrgDeviceStatsExporter._log_fast_port_stats_summary(
            sites, failed_sites, all_port_stats, duration
        )  # Emit summary log + print.
        OrgDeviceStatsExporter._save_device_port_stats_output(all_port_stats, output_file)  # Persist collected rows.

    @staticmethod
    def device_port_stats(fast: bool = False):  # noqa: C901, PLR0912, PLR0915
        """Export port-level statistics for switches and gateways to OrgDevicePortStats.csv.

        Fast mode caches recent CSV (CSV_FRESHNESS_MINUTES) and parallelizes site fetches with
        bounded concurrency. Non-fast mode issues one org-level paginated call. SECURITY: read-only.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of TimeUtils/APIDataFetcher/mistapi.
        output_file = "OrgDevicePortStats.csv"  # Stable filename for cache + downstream consumers.
        if OrgDeviceStatsExporter._port_stats_cache_hit(output_file, fast):  # Honor fast cache before API.
            return  # Fresh cache satisfied the request.
        logging.info("Starting export of organization device port statistics...")  # Log export start.
        hours = mh.TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve test-aware lookback window.
        mh.TimeUtils.log_dynamic_lookback("org device port statistics export", hours)  # Record chosen window.
        if fast:  # Fast mode = site-parallel collection.
            OrgDeviceStatsExporter._run_fast_device_port_stats(output_file)  # Execute decomposed fast-mode workflow.
            return  # Fast-mode path owns the full export.
        mh.APIDataFetcher(  # Non-fast mode = single org-level paginated fetch.
            title="Org Device Port Stats:",
            api_call=mh.mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
            filename=output_file,
            sort_key="mac",
            limit=1000,
        ).execute()  # Execute pagination + export.

    @staticmethod
    def _vpn_peer_stats_cache_hit(output_file: str, fast: bool) -> bool:
        """Return True if fast-mode cache for VPN peer stats is fresh; emit cache-hit log + print."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CSV_FRESHNESS_MINUTES.
        if not (fast and os.path.exists(output_file)):  # Either non-fast or no file yet.
            return False
        try:
            mtime = os.path.getmtime(output_file)  # Disk mtime for freshness math.
            age_minutes = (time.time() - mtime) / 60.0  # Age in minutes.
            if age_minutes < mh.CSV_FRESHNESS_MINUTES:  # Fresh enough to reuse.
                logging.info(
                    " Fast mode cache hit: %s is fresh (%.1fm < %sm); skipping fetch.",
                    output_file,
                    age_minutes,
                    mh.CSV_FRESHNESS_MINUTES,
                )  # Structured log.
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # Operator-facing.
                return True
        except Exception as e:  # Freshness check failed -- fall through to fetch.
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, e)  # Debug-only.
        return False

    @staticmethod
    def vpn_peer_stats(fast: bool = False):  # Export VPN peer stats.
        """Export VPN peer path statistics to OrgVPNPeerStats.csv.

        Fast mode reuses recent CSV; normal mode does an org-level paginated fetch. SECURITY: read-only.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live globals.
        output_file = "OrgVPNPeerStats.csv"  # Output filename.
        if OrgDeviceStatsExporter._vpn_peer_stats_cache_hit(output_file, fast):  # Honor fast cache.
            return  # Cache satisfied.
        logging.info("Starting export of organization VPN peer path statistics...")  # Log start.
        emitter = mh.PROGRESS_EMITTER  # Progress emitter (may be None).
        if emitter:  # Emitter present.
            emitter.emit_progress_start("15", "vpn_peer_stats", 1)  # Signal progress start.
        op_start = time.time()  # Start timer.
        hours = mh.TimeUtils.get_dynamic_lookback_hours(24, 1)  # Test-aware lookback.
        mh.TimeUtils.log_dynamic_lookback("org vpn peer path statistics export", hours)  # Record lookback.
        mh.APIDataFetcher(
            title="Org VPN Peer Stats:",
            api_call=mh.mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
            filename=output_file,
            sort_key="mac",
            duration=f"{hours}h",
            limit=1000,
        ).execute()  # Run paginated org-level fetch + export.
        if emitter:  # Signal progress complete on the emitter.
            emitter.emit_progress_complete(
                mh.ProgressContext("15", "vpn_peer_stats", 1), 1, False, time.time() - op_start
            )

    @staticmethod
    def switch_vc_stats():
        """Export virtual chassis stats (including stacking cable info) for all switches in the org."""
        from src.refactors.serial_cc.switch_vc_stats import SwitchVcStatsService

        SwitchVcStatsService.execute()
