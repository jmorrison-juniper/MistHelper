"""Systematic testing cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the read-only test-runner
flow lives in its own module. The extracted methods stay as methods of
a small wrapper class :class:`_MapsTesting`; ``__getattr__`` delegates
lookups that miss on the wrapper to the wrapped MapsManager so shared
state (``apisession``, ``_fetch_sites``) works without rewrites.

MapsManager keeps a slim ``run_systematic_test`` delegating method
because ``launch_viewer_standalone`` in the same file invokes it as
``maps_manager.run_systematic_test()``.
"""

from __future__ import annotations  # WHY: enable postponed annotations

import logging  # WHY: structured logging for test errors
import time  # WHY: timestamps and elapsed-time measurement
from collections.abc import Callable  # WHY: typed callback signatures
from dataclasses import dataclass, field  # WHY: frozen result aggregator
from typing import Any  # WHY: manager attributes are untyped

import mistapi

logger = logging.getLogger(__name__)  # WHY: module-scoped logger

_HEADER_SEP: str = "=" * 80  # WHY: banner divider reused across prints
_TIMESTAMP_FMT: str = "%Y-%m-%d %H:%M:%S"  # WHY: unified test-start timestamp
_LISTING_SAMPLE_LIMIT: int = 10  # WHY: cap sites scanned for map listing
_EXPORT_SAMPLE_LIMIT: int = 5  # WHY: cap sites scanned for export validation
_IMAGE_SAMPLE_LIMIT: int = 5  # WHY: cap sites scanned for image analysis
_HTTP_OK: int = 200  # WHY: expected mistapi listSiteMaps status code

_SKIPPED_TESTS: tuple[str, ...] = (  # WHY: unsafe/interactive ops not exercised
    "List site maps (requires site selection)",
    "View map details (requires site selection)",
    "Create site map (DESTRUCTIVE)",
    "Update map properties (DESTRUCTIVE)",
    "Delete site map (DESTRUCTIVE)",
    "Upload map image (DESTRUCTIVE)",
    "Auto-place APs (DESTRUCTIVE)",
    "Auto-orient APs (DESTRUCTIVE)",
    "Set device location (DESTRUCTIVE)",
    "Clone map (DESTRUCTIVE)",
    "Map replacement wizard (DESTRUCTIVE/Interactive)",
    "Interactive map viewer (requires Dash server)",
    "Bulk download images (resource intensive)",
    "Backup all maps (resource intensive)",
)


@dataclass(slots=True)
class _TestResults:  # WHY: mutable aggregator for pass/fail counts
    """Aggregate outcomes across the safe-test sequence."""

    passed: int = 0  # WHY: count of tests that returned True
    failed: int = 0  # WHY: count of tests that returned False or raised
    errors: list[str] = field(default_factory=list)  # WHY: human-readable failures

    def record_pass(self) -> None:  # WHY: expose intent-named mutator
        """Record a successful test outcome."""
        self.passed += 1  # WHY: bump passed counter

    def record_fail(self, description: str) -> None:  # WHY: pair mutator for failure
        """Record a failed test outcome with human message."""
        self.failed += 1  # WHY: bump failed counter
        self.errors.append(description)  # WHY: preserve error text for summary


def _print_header(started_at: float) -> None:  # WHY: banner extracted for length reduction
    """Print banner announcing the systematic test start."""
    print("\n" + _HEADER_SEP)  # WHY: visual separator opens report
    print("MAPS MANAGER - Systematic Test Mode")  # WHY: header title
    print(_HEADER_SEP)  # WHY: close top border
    print("Testing safe, non-destructive operations (GET only, no modifications)")  # WHY: scope note
    stamp = time.strftime(_TIMESTAMP_FMT, time.localtime(started_at))  # WHY: format start time
    print(f"Test started at: {stamp}")  # WHY: annotate log with wall clock
    print(_HEADER_SEP)  # WHY: divider before skipped list


def _print_skipped_list(safe_count: int, skipped: tuple[str, ...]) -> None:  # WHY: keep printer isolated
    """Print skipped-operation counts and their names."""
    print(f"\n! {safe_count} safe operations will be tested")  # WHY: safe-test count summary
    print(f"! {len(skipped)} operations skipped (interactive/destructive/resource intensive)")  # WHY: counts
    print("\n Skipping unsafe operations:")  # WHY: introduce skip enumeration
    for skip in skipped:  # WHY: enumerate every skipped op by name
        print(f"   - {skip}")  # WHY: bullet each skipped label


def _print_summary(results: _TestResults, total: int, elapsed: float) -> None:  # WHY: summary printer
    """Print totals and any collected errors after the run."""
    print("\n" + _HEADER_SEP)  # WHY: visual break before summary
    print("TEST SUMMARY")  # WHY: summary section title
    print(_HEADER_SEP)  # WHY: close summary top divider
    print(f"Total tests: {total}")  # WHY: report suite size
    print(f"Passed: {results.passed}")  # WHY: report pass count
    print(f"Failed: {results.failed}")  # WHY: report fail count
    print(f"Elapsed time: {elapsed:.2f} seconds")  # WHY: expose runtime cost
    if results.errors:  # WHY: only enumerate errors when any exist
        print("\nErrors encountered:")  # WHY: intro line for error list
        for error in results.errors:  # WHY: emit each captured error
            print(f"   - {error}")  # WHY: bullet each error message
    if results.failed == 0:  # WHY: choose success or failure verdict
        print("\n[OK] All tests passed!")  # WHY: green-path verdict
    else:  # WHY: at least one failure requires callout
        print(f"\n[FAIL] {results.failed} test(s) failed")  # WHY: red-path verdict
    print(_HEADER_SEP)  # WHY: closing divider


def _invoke_test(name: str, func: Callable[[], bool], results: _TestResults) -> None:  # WHY: outcome dispatcher
    """Run a single named safe-test callback and record its outcome."""
    try:
        success = func()  # WHY: execute the test lambda
    except Exception as test_error:  # WHY: any exception counts as failure
        print(f"   [ERROR] {name} raised exception: {test_error}")  # WHY: surface exception
        results.record_fail(f"{name}: {type(test_error).__name__}: {test_error}")  # WHY: capture failure
        logging.exception("Test '%s' failed with exception", name)  # WHY: full traceback in log
        return  # WHY: exit early after logging the crash
    if success:  # WHY: distinguish true/false returns
        print(f"   [SUCCESS] {name} completed successfully")  # WHY: pass line
        results.record_pass()  # WHY: increment passed counter
        return  # WHY: skip failure branch
    print(f"   [FAILED] {name} returned failure")  # WHY: soft-fail line
    results.record_fail(f"{name}: returned False")  # WHY: record soft failure


def _run_safe_tests(safe_tests: list[tuple[str, Callable[[], bool]]]) -> _TestResults:  # WHY: loop core
    """Iterate through the safe-test list and collect outcomes."""
    results = _TestResults()  # WHY: fresh aggregator per run
    total = len(safe_tests)  # WHY: precomputed for numeric prefix
    for idx, (name, func) in enumerate(safe_tests, 1):  # WHY: 1-based numbering
        print(f"\n   [{idx}/{total}] Testing: {name}...")  # WHY: progress line
        _invoke_test(name, func, results)  # WHY: delegate outcome recording
    return results  # WHY: caller renders the summary


def _sampled_sites(sites: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:  # WHY: window helper
    """Return the first ``limit`` sites when the list exceeds the cap."""
    return sites[:limit] if len(sites) > limit else sites  # WHY: bounded sampling window


def _list_site_maps(apisession: Any, site_id: Any) -> list[dict[str, Any]]:
    """Return maps for one site or an empty list on HTTP/parse failure."""
    resp = mistapi.api.v1.sites.maps.listSiteMaps(apisession, site_id=site_id)  # WHY: sample-only fetch
    if resp.status_code != _HTTP_OK or not resp.data:  # WHY: guard on non-200 or empty payload
        return []  # WHY: caller expects a list, never None
    data: list[dict[str, Any]] = resp.data  # WHY: hoist typed alias for return
    return data  # WHY: give caller the raw map records


def _safe_list_site_maps(apisession: Any, site_id: Any, warn_context: str) -> list[dict[str, Any]]:
    """List maps for a site, logging and swallowing exceptions."""
    try:
        return _list_site_maps(apisession, site_id)  # WHY: happy path
    except Exception as site_error:  # WHY: sampling loop must not abort on one site
        logging.debug("Skipping site during %s: %s", warn_context, site_error)  # WHY: soft skip
        return []  # WHY: keep the accumulator flow going


def _count_maps_across_sites(apisession: Any, sites: list[dict[str, Any]]) -> tuple[int, int]:
    """Return (total maps, sites-with-maps) across the sampled sites."""
    total_maps = 0  # WHY: rolling map counter
    sites_with_maps = 0  # WHY: rolling site counter
    for site in sites:  # WHY: sample each site once
        maps = _safe_list_site_maps(apisession, site.get("id"), "map sampling")
        if maps:  # WHY: only count sites that returned anything
            total_maps += len(maps)  # WHY: accumulate map count
            sites_with_maps += 1  # WHY: bump site counter
    return total_maps, sites_with_maps  # WHY: two-tuple keeps caller simple


def _collect_export_records(apisession: Any, sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect map export descriptors for the sampled sites."""
    export_data: list[dict[str, Any]] = []  # WHY: accumulator for map records
    for site in sites:  # WHY: iterate each sampled site once
        site_id = site.get("id")  # WHY: keyed lookup for logging
        site_name = site.get("name", "Unknown")  # WHY: default when name missing
        maps = _safe_list_site_maps(apisession, site_id, "export validation")
        for map_data in maps:  # WHY: flatten each site's maps into export rows
            export_data.append(  # WHY: build export record dict
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "map_id": map_data.get("id"),
                    "map_name": map_data.get("name"),
                }
            )
    return export_data  # WHY: caller reports len() only


def _tally_map_images(apisession: Any, sites: list[dict[str, Any]]) -> tuple[int, int]:
    """Return (with_images, without_images) counts across sampled sites."""
    with_images = 0  # WHY: counter for maps carrying a url
    without_images = 0  # WHY: counter for maps missing a url
    for site in sites:  # WHY: iterate each sampled site once
        maps = _safe_list_site_maps(apisession, site.get("id"), "image analysis")
        for map_data in maps:  # WHY: check each map's url attribute
            if map_data.get("url"):  # WHY: url presence = image uploaded
                with_images += 1  # WHY: bump images-present counter
            else:  # WHY: no url means no uploaded image
                without_images += 1  # WHY: bump missing-images counter
    return with_images, without_images  # WHY: caller reports counts


class _MapsTesting:
    """Wrapper class holding the extracted testing methods."""

    def __init__(self, maps_manager: Any) -> None:
        """Store the wrapped MapsManager for attribute delegation."""
        self._mm = maps_manager  # WHY: retain manager for shared state

    def __getattr__(self, name: str) -> Any:
        """Delegate missing lookups to the wrapped MapsManager."""
        mm = self.__dict__.get("_mm")  # WHY: avoid recursion during broken init
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)  # WHY: mimic default AttributeError semantics
        return getattr(mm, name)  # WHY: forward attribute access to manager

    def run_systematic_test(self) -> bool:
        """Run systematic test of safe Maps Manager operations.

        Returns:
            bool: True if all tests passed, False if any failed.
        """
        started_at = time.time()  # WHY: capture start for elapsed calc
        _print_header(started_at)  # WHY: emit banner section
        safe_tests: list[tuple[str, Callable[[], bool]]] = [  # WHY: name/callback pairs
            ("Fetch sites list", self._test_fetch_sites),
            ("List all org maps", self._test_list_all_org_maps),
            ("Export all site maps", self._test_export_all_site_maps),
            ("Maps without images report", self._test_maps_without_images),
        ]
        _print_skipped_list(len(safe_tests), _SKIPPED_TESTS)  # WHY: enumerate skipped ops
        print("\n Testing safe operations:")  # WHY: intro line for iteration
        results = _run_safe_tests(safe_tests)  # WHY: aggregate outcomes
        _print_summary(results, len(safe_tests), time.time() - started_at)  # WHY: render report
        return results.failed == 0  # WHY: True only when zero failures

    def _test_fetch_sites(self) -> bool:
        """Test fetching sites list."""
        sites = self._fetch_sites()  # WHY: delegate to manager helper
        if sites is None:  # WHY: None signals API failure
            return False  # WHY: propagate failure to runner
        print(f"       Found {len(sites)} sites in organization")  # WHY: report count
        return True  # WHY: success path

    def _test_list_all_org_maps(self) -> bool:
        """Test listing all org maps (non-interactive version)."""
        try:
            sites = self._fetch_sites()  # WHY: fetch site catalog
            if not sites:  # WHY: no sites means nothing to test
                print("       No sites found - skipping map listing")
                return True  # WHY: empty catalog is not a failure
            sampled = _sampled_sites(sites, _LISTING_SAMPLE_LIMIT)  # WHY: bound scan cost
            print(f"       Checking maps for {len(sampled)} sites (of {len(sites)} total)...")
            total_maps, sites_with_maps = _count_maps_across_sites(
                self.apisession, sampled
            )  # WHY: aggregate across sample
            print(f"       Found {total_maps} maps across {sites_with_maps} sites (sampled)")
            return True  # WHY: report success
        except Exception as e:  # WHY: any unexpected error becomes test failure
            logging.error("_test_list_all_org_maps failed: %s", e)  # WHY: surface for debug
            return False  # WHY: propagate to runner

    def _test_export_all_site_maps(self) -> bool:
        """Test export all site maps functionality (collect data without writing)."""
        try:
            sites = self._fetch_sites()  # WHY: fetch site catalog
            if not sites:  # WHY: nothing to export when empty
                print("       No sites found - skipping export test")
                return True  # WHY: empty catalog is not a failure
            sampled = _sampled_sites(sites, _EXPORT_SAMPLE_LIMIT)  # WHY: bound scan cost
            export_data = _collect_export_records(self.apisession, sampled)  # WHY: gather records
            print(f"       Export data structure validated: {len(export_data)} map records")
            return True  # WHY: successful validation path
        except Exception as e:  # WHY: unexpected error path
            logging.error("_test_export_all_site_maps failed: %s", e)  # WHY: surface for debug
            return False  # WHY: propagate to runner

    def _test_maps_without_images(self) -> bool:
        """Test maps without images report (data collection only)."""
        try:
            sites = self._fetch_sites()  # WHY: fetch site catalog
            if not sites:  # WHY: nothing to analyse when empty
                print("       No sites found - skipping report test")
                return True  # WHY: empty catalog is not a failure
            sampled = _sampled_sites(sites, _IMAGE_SAMPLE_LIMIT)  # WHY: bound scan cost
            with_images, without_images = _tally_map_images(self.apisession, sampled)  # WHY: aggregate image presence
            print(f"       Image analysis: {with_images} with images, " f"{without_images} without (sampled)")
            return True  # WHY: successful validation path
        except Exception as e:  # WHY: unexpected error path
            logging.error("_test_maps_without_images failed: %s", e)  # WHY: surface for debug
            return False  # WHY: propagate to runner


def run_systematic_test(maps_manager: Any) -> bool:
    """Entry point mirroring MapsManager.run_systematic_test.

    Kept as a module-level factory so callers can invoke the test
    runner without instantiating :class:`_MapsTesting` directly.
    """
    return _MapsTesting(maps_manager).run_systematic_test()  # WHY: delegation seam preserved
