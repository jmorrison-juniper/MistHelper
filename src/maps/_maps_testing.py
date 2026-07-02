"""Systematic testing cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~207 LOC read-only
test-runner flow lives in its own module. The extracted methods stay as
methods of a small wrapper class :class:`_MapsTesting`; ``__getattr__``
delegates lookups that miss on the wrapper to the wrapped MapsManager,
so ``self.apisession``, ``self.get_current_site``, and other shared
state work without rewrites.

MapsManager keeps a slim ``run_systematic_test`` delegating method
because ``launch_viewer_standalone`` in the same file invokes it as
``maps_manager.run_systematic_test()``.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class _MapsTesting:
    """Wrapper class holding the extracted testing methods."""

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    def run_systematic_test(self) -> bool:
        """Run systematic test of safe, non-destructive Maps Manager operations.

        Tests read-only operations that don't require user input:
        - Fetching sites
        - Listing all org maps
        - Exporting maps data
        - Analytics operations

        Returns:
            bool: True if all tests passed, False if any failed
        """
        import time

        start_time = time.time()

        print("\n" + "=" * 80)
        print("MAPS MANAGER - Systematic Test Mode")
        print("=" * 80)
        print("Testing safe, non-destructive operations (GET only, no modifications)")
        print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Define safe tests (read-only operations that don't need site selection input)
        safe_tests = [
            ("Fetch sites list", self._test_fetch_sites),
            ("List all org maps", self._test_list_all_org_maps),
            ("Export all site maps", self._test_export_all_site_maps),
            ("Maps without images report", self._test_maps_without_images),
        ]

        # Skip tests that require interactive site selection or are destructive
        skipped_tests = [
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
        ]

        print(f"\n! {len(safe_tests)} safe operations will be tested")
        print(f"! {len(skipped_tests)} operations skipped (interactive/destructive/resource intensive)")

        print("\n Skipping unsafe operations:")
        for skip in skipped_tests:
            print(f"   - {skip}")

        print("\n Testing safe operations:")

        results = {"passed": 0, "failed": 0, "errors": []}

        for idx, (test_name, test_func) in enumerate(safe_tests, 1):
            print(f"\n   [{idx}/{len(safe_tests)}] Testing: {test_name}...")
            try:
                success = test_func()
                if success:
                    print(f"   [SUCCESS] {test_name} completed successfully")
                    results["passed"] += 1
                else:
                    print(f"   [FAILED] {test_name} returned failure")
                    results["failed"] += 1
                    results["errors"].append(f"{test_name}: returned False")
            except Exception as test_error:
                print(f"   [ERROR] {test_name} raised exception: {test_error}")
                results["failed"] += 1
                results["errors"].append(f"{test_name}: {type(test_error).__name__}: {test_error}")
                logging.exception("Test '%s' failed with exception", test_name)

        # Summary
        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests: {len(safe_tests)}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Elapsed time: {elapsed:.2f} seconds")

        if results["errors"]:
            print("\nErrors encountered:")
            for error in results["errors"]:
                print(f"   - {error}")

        all_passed = results["failed"] == 0
        if all_passed:
            print("\n[OK] All tests passed!")
        else:
            print(f"\n[FAIL] {results['failed']} test(s) failed")

        print("=" * 80)
        return all_passed

    def _test_fetch_sites(self) -> bool:
        """Test fetching sites list."""
        sites = self._fetch_sites()
        if sites is None:
            return False
        print(f"       Found {len(sites)} sites in organization")
        return True

    def _test_list_all_org_maps(self) -> bool:
        """Test listing all org maps (non-interactive version)."""
        try:
            sites = self._fetch_sites()
            if not sites:
                print("       No sites found - skipping map listing")
                return True  # Not a failure, just no data

            total_maps = 0
            sites_with_maps = 0

            # Only check first 10 sites to avoid long test times
            test_sites = sites[:10] if len(sites) > 10 else sites
            print(f"       Checking maps for {len(test_sites)} sites (of {len(sites)} total)...")

            for site in test_sites:
                site_id = site.get("id")
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)
                    if maps_response.status_code == 200 and maps_response.data:
                        map_count = len(maps_response.data)
                        total_maps += map_count
                        sites_with_maps += 1
                except Exception as site_error:
                    logging.debug("Skipping site during map sampling: %s", site_error)

            print(f"       Found {total_maps} maps across {sites_with_maps} sites (sampled)")
            return True
        except Exception as e:
            logging.error("_test_list_all_org_maps failed: %s", e)
            return False

    def _test_export_all_site_maps(self) -> bool:
        """Test export all site maps functionality (collect data without writing)."""
        try:
            sites = self._fetch_sites()
            if not sites:
                print("       No sites found - skipping export test")
                return True

            # Just verify we can collect the data structure
            export_data = []
            test_sites = sites[:5] if len(sites) > 5 else sites  # Limit to first 5 for speed

            for site in test_sites:
                site_id = site.get("id")
                site_name = site.get("name", "Unknown")
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)
                    if maps_response.status_code == 200 and maps_response.data:
                        for map_data in maps_response.data:
                            export_data.append(
                                {
                                    "site_id": site_id,
                                    "site_name": site_name,
                                    "map_id": map_data.get("id"),
                                    "map_name": map_data.get("name"),
                                }
                            )
                except Exception as site_error:
                    logging.debug("Skipping site during export validation: %s", site_error)

            print(f"       Export data structure validated: {len(export_data)} map records")
            return True
        except Exception as e:
            logging.error("_test_export_all_site_maps failed: %s", e)
            return False

    def _test_maps_without_images(self) -> bool:
        """Test maps without images report (data collection only)."""
        try:
            sites = self._fetch_sites()
            if not sites:
                print("       No sites found - skipping report test")
                return True

            maps_without_images = 0
            maps_with_images = 0
            test_sites = sites[:5] if len(sites) > 5 else sites

            for site in test_sites:
                site_id = site.get("id")
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)
                    if maps_response.status_code == 200 and maps_response.data:
                        for map_data in maps_response.data:
                            if map_data.get("url"):
                                maps_with_images += 1
                            else:
                                maps_without_images += 1
                except Exception as site_error:
                    logging.debug("Skipping site during image analysis: %s", site_error)

            print(f"       Image analysis: {maps_with_images} with images, {maps_without_images} without (sampled)")
            return True
        except Exception as e:
            logging.error("_test_maps_without_images failed: %s", e)
            return False


def run_systematic_test(maps_manager: Any) -> bool:
    """Entry point mirroring MapsManager.run_systematic_test.

    Kept as a module-level factory so callers can invoke the test
    runner without instantiating :class:`_MapsTesting` directly.
    """
    return _MapsTesting(maps_manager).run_systematic_test()
