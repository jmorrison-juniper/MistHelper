#!/usr/bin/env python3
"""MapsManager - Interactive Map Viewer for Mist Networks.

This module contains the MapsManager class for managing site floor plans
and maps in Juniper Mist Cloud. It provides:
- Interactive web-based map viewer (Dash/Plotly)
- Map inventory and export operations
- Device placement and auto-placement operations
- Zone and wayfinding path visualization
- Connected client visualization
- RF coverage heatmaps

Can be run standalone or imported by MistHelper.py for Menu 112 integration.

Usage:
    Standalone:     python maps_manager.py [--menu] [--org ORG_ID]
    As module:      Menu option 112 in MistHelper.py (40. Interactive Map Viewer)

Author: Joseph Morrison (jmorrison@juniper.net)
Version: 26.01.09.18.00
"""

# ============================================================================
# IMPORTS
# ============================================================================

import csv
import importlib.util
import logging
import os
import sys
from datetime import datetime
from typing import Any

# Optional visualization imports — use find_spec for availability checks
PLOTLY_AVAILABLE = importlib.util.find_spec("plotly") is not None
DASH_AVAILABLE = importlib.util.find_spec("dash") is not None
PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None

if PLOTLY_AVAILABLE:
    import plotly.graph_objects as go
else:
    go = None

# Dash symbols (Input, Output, State, etc.) are imported locally
# in methods that need them, since they require dash to be installed.
Dash = None
html = None
dcc = None

try:
    import requests
except ImportError:
    requests = None

try:
    from tqdm import tqdm
except ImportError:

    def tqdm(iterable, **_kwargs):
        """No-op fallback for tqdm progress bar."""
        return iterable


# Mist API import
try:
    import mistapi  # type: ignore[import-untyped]
except ImportError:
    mistapi = None  # type: ignore[assignment]

# Configure module logger
logger = logging.getLogger(__name__)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Page limit configuration
try:
    _raw_page_limit_env = os.environ.get("MIST_PAGE_LIMIT", "1000").strip()
    _parsed_limit = int(_raw_page_limit_env)
except Exception:
    _parsed_limit = 1000

DEFAULT_API_PAGE_LIMIT = max(1, min(_parsed_limit, 1000))


def flatten_dict_recursively(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
    """Recursively flatten a nested dictionary structure."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict_recursively(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], dict):
                for idx, item in enumerate(v):
                    items.extend(flatten_dict_recursively(item, f"{new_key}{sep}{idx}", sep=sep).items())
            else:
                items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def sanitize_filename(filename: str) -> str:
    """Sanitize a string for use as a filename."""
    if not filename:
        return "unnamed"
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    filename = filename.strip(" .")
    return filename[:100] if filename else "unnamed"


def _check_env_override() -> bool:
    """Check explicit container override environment variables."""
    true_values = {"1", "true", "yes", "on"}
    for explicit_var in ("MISTHELPER_FORCE_CONTAINER_LOOP", "MISTHELPER_CONTAINER"):
        value = os.environ.get(explicit_var, "").strip().lower()
        if value in true_values:
            logging.debug(f"Container detection: override via {explicit_var}={value}")
            return True
    return False


def _check_sentinel_files() -> bool:
    """Check for container sentinel files."""
    if os.path.exists("/.dockerenv"):
        logging.debug("Container detection: /.dockerenv present")
        return True
    return False


def _check_container_env_vars() -> bool:
    """Check well-known container environment variables."""
    container_env_vars = [
        "CONTAINER",
        "DOCKER_CONTAINER",
        "PODMAN_CONTAINER",
        "KUBERNETES_SERVICE_HOST",
        "CONTAINERD_NAMESPACE",
    ]
    for env_var in container_env_vars:
        if os.environ.get(env_var):
            logging.debug(f"Container detection: environment variable {env_var} present")
            return True
    return False


def _check_cgroup_markers() -> bool:
    """Check cgroup content for container indicators."""
    try:
        with open("/proc/1/cgroup", encoding="utf-8", errors="ignore") as cgroup_file:
            cgroup_content = cgroup_file.read().lower()
            for indicator in ("docker", "containerd", "podman", "lxc"):
                if indicator in cgroup_content:
                    logging.debug(f"Container detection: cgroup indicator '{indicator}' found")
                    return True
    except (FileNotFoundError, PermissionError):
        pass
    return False


def _check_runtime_user() -> bool:
    """Check if running as container user 'misthelper'."""
    try:
        import pwd  # Unix only

        current_user_name = pwd.getpwuid(os.getuid()).pw_name  # type: ignore[attr-defined]
        if current_user_name == "misthelper":
            logging.debug("Container detection: running as user 'misthelper'")
            return True
    except Exception:
        logging.debug("Container detection: user lookup failed (non-Unix or unavailable)")
    return False


def _check_app_path() -> bool:
    """Check for canonical container path /app with sshd presence."""
    try:
        this_file_dir = os.path.abspath(os.path.dirname(__file__))
        if this_file_dir.startswith("/app") and os.path.exists("/app/MistHelper.py"):
            if os.path.exists("/usr/sbin/sshd"):
                logging.debug("Container detection: /app path with MistHelper.py and sshd present")
                return True
    except Exception:
        logging.debug("Container detection: path heuristic check failed")
    return False


def is_running_in_container() -> bool:
    """Determine if execution appears to be inside a container.

    Detection strategy is deliberately multi-factor and conservative. A positive
    result enables continuous interactive looping behavior.

    SECURITY: Only boolean enabling of loop behavior; no privileged actions.
    """
    checks = [
        _check_env_override,
        _check_sentinel_files,
        _check_container_env_vars,
        _check_cgroup_markers,
        _check_runtime_user,
        _check_app_path,
    ]
    try:
        for check in checks:
            if check():
                return True
    except Exception as container_detection_error:
        logging.debug(f"Container detection failed with exception: {container_detection_error}")

    logging.debug("Container detection: no container indicators found - running in direct mode")
    return False


def write_data_with_format_selection(
    data: list[dict[str, Any]],
    filename: str,
    _format_override: str | None = None,
    _api_function_name: str | None = None,
) -> bool:
    """Write data to CSV format (standalone mode)."""
    if not data:
        logger.warning("write_data_with_format_selection: No data to write")
        return False

    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(data_dir, f"{safe_filename}.csv")

    try:
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        fieldnames = sorted(all_keys)

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Data written to {filepath} ({len(data)} rows)")
        print(f"   Data saved to: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error writing CSV: {e}")
        return False


class MapsManager:
    """Comprehensive Maps Management System for Mist Sites.

    Provides interactive management of site floor plans and maps including:
    - Map inventory and export operations
    - Image download and upload capabilities
    - Map creation and configuration
    - Device placement and auto-placement operations
    - Analytics and reporting
    """

    def __init__(self, api_session, organization_id):
        """Initialize MapsManager with API session and org context."""
        self.apisession = api_session
        self.org_id = organization_id
        self.current_site_id = None
        self.current_site_name = None
        logging.info(f"MapsManager initialized for organization: {self.org_id}")

    def _fetch_sites(self):
        """Fetch all sites using instance API session (not global)."""
        try:
            resp = mistapi.api.v1.orgs.sites.listOrgSites(  # type: ignore[union-attr]
                self.apisession, self.org_id, limit=DEFAULT_API_PAGE_LIMIT
            )
            return mistapi.get_all(response=resp, mist_session=self.apisession)  # type: ignore[union-attr]
        except Exception as e:
            logging.error(f"MapsManager._fetch_sites error: {e}")
            return []

    def select_site(self):
        """Prompt user to select a site and cache the selection."""
        # Use instance method to fetch sites (works in standalone mode)
        sites = self._fetch_sites()
        if not sites:
            print("\n! No sites found in organization")
            return False

        # Sort sites by name for easier selection
        sites_sorted = sorted(sites, key=lambda x: x.get("name", "").lower())

        print("\nAvailable Sites:")
        print("-" * 60)
        for idx, site in enumerate(sites_sorted):
            print(f"  [{idx}] {site.get('name', 'Unnamed')}")
        print("-" * 60)

        try:
            selection = input("Enter site index or name: ").strip()

            # Try as index first
            try:
                site_idx = int(selection)
                if 0 <= site_idx < len(sites_sorted):
                    selected_site = sites_sorted[site_idx]
                    site_id = selected_site.get("id")
                    site_name = selected_site.get("name", "Unknown")
                else:
                    print("\n! Invalid index")
                    return False
            except ValueError:
                # Try as name match
                matches = [s for s in sites_sorted if selection.lower() in s.get("name", "").lower()]
                if len(matches) == 1:
                    selected_site = matches[0]
                    site_id = selected_site.get("id")
                    site_name = selected_site.get("name", "Unknown")
                elif len(matches) > 1:
                    print(f"\n! Multiple matches found ({len(matches)}). Please be more specific.")
                    return False
                else:
                    print("\n! No matching site found")
                    return False

            self.current_site_id = site_id
            self.current_site_name = site_name
            print(f"\n   Site selected: {site_name}")
            logging.info(f"MapsManager site selection: {site_name} ({site_id})")
            return True

        except EOFError:
            logging.info("EOF detected during site selection")
            return False

    def get_current_site(self):
        """Get current site selection, prompting if not set."""
        if not self.current_site_id:
            print("\n! No site currently selected. Please select a site first.")
            if not self.select_site():
                return None, None
        return self.current_site_id, self.current_site_name

    def _select_map_from_site(self, site_id, site_name, return_all_maps=False):
        """Select a map from a site.

        Returns map_id or None, optionally returns (map_id, maps_list).
        """
        try:
            # Fetch maps for the site
            maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)

            if maps_response.status_code != 200:
                print(f"\n! Failed to fetch maps: HTTP {maps_response.status_code}")
                return (None, []) if return_all_maps else None

            maps = maps_response.data
            if not maps:
                print(f"\n! No maps found for site: {site_name}")
                return (None, []) if return_all_maps else None

            # Auto-select if only one map available
            if len(maps) == 1:
                selected_map = maps[0]
                map_name = selected_map.get("name", "Unnamed")
                print(f"\nAuto-selecting only available map: {map_name}")
                result_id = selected_map.get("id")
                return (result_id, maps) if return_all_maps else result_id

            # Display map selection
            print(f"\nMaps for site: {site_name}")
            print(f"{'-' * 80}")
            for idx, map_item in enumerate(maps, 1):
                map_name = map_item.get("name", "Unnamed")
                map_type = map_item.get("type", "N/A")
                has_image = "with image" if "url" in map_item else "no image"
                print(f"  {idx}. {map_name} ({map_type}) - {has_image}")
            print(f"{'-' * 80}")

            selection = input("\nSelect map number (or 0 to cancel): ").strip()
            try:
                map_idx = int(selection) - 1
                if map_idx < 0:
                    return (None, maps) if return_all_maps else None
                if map_idx >= len(maps):
                    print("\n! Invalid selection")
                    return (None, maps) if return_all_maps else None

                selected_map = maps[map_idx]
                result_id = selected_map.get("id")
                return (result_id, maps) if return_all_maps else result_id

            except ValueError:
                print("\n! Invalid input - please enter a number")
                return (None, maps) if return_all_maps else None

        except EOFError:
            logging.info("EOF detected during map selection")
            return (None, []) if return_all_maps else None
        except Exception as e:
            logging.error(f"Error selecting map: {e}", exc_info=True)
            print(f"\n! Error selecting map: {e}")
            return (None, []) if return_all_maps else None

    def _backup_download_image(self, map_data, map_name, backup_reason):
        """Download map image for backup. Returns (filename, content) or (None, None)."""
        from datetime import datetime

        import requests

        image_url = map_data.get("url")
        if not image_url:
            return None, None

        try:
            file_ext = ".png"
            if "." in image_url:
                url_ext = image_url.rsplit(".", 1)[-1].split("?")[0].lower()
                if url_ext in ["png", "jpg", "jpeg", "gif", "svg", "webp"]:
                    file_ext = f".{url_ext}"

            safe_map_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in map_name)
            safe_map_name = safe_map_name.strip().replace(" ", "_")[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"map_backup_{safe_map_name}_{backup_reason}_{timestamp}{file_ext}"

            data_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(data_dir, exist_ok=True)

            response = requests.get(image_url, timeout=60)
            if response.status_code == 200:
                image_path = os.path.join(data_dir, image_filename)
                with open(image_path, "wb") as img_file:
                    img_file.write(response.content)
                image_size_kb = len(response.content) / 1024
                logging.info(f"Map image backed up: {image_filename} ({image_size_kb:.1f} KB)")
                return image_filename, (safe_map_name, timestamp)
            logging.warning(f"Could not download map image: HTTP {response.status_code}")
        except Exception as img_err:
            logging.warning(f"Image backup failed: {img_err}")
        return None, None

    def _backup_fetch_items(self, api_session, site_id, map_id, api_call, item_name):
        """Fetch items from API and filter to map. Returns list of matching items."""
        try:
            response = api_call(api_session, site_id=site_id)
            if response.status_code == 200:
                all_items = response.data if isinstance(response.data, list) else []
                map_items = [item for item in all_items if item.get("map_id") == map_id]
                logging.debug(f"Backup includes {len(map_items)} {item_name} for map {map_id}")
                return map_items
            logging.warning(f"Could not fetch {item_name} for backup: HTTP {response.status_code}")
        except Exception as err:
            logging.debug(f"{item_name} backup skipped: {err}")
        return []

    def _backup_fetch_device_placements(self, api_session, site_id, map_id):
        """Fetch device placements on a specific map."""
        try:
            devices_response = mistapi.api.v1.sites.devices.listSiteDevices(api_session, site_id=site_id, type="all")
            if devices_response.status_code == 200:
                all_devices = devices_response.data if isinstance(devices_response.data, list) else []
                placements = []
                for device in all_devices:
                    if device.get("map_id") == map_id and ("x" in device or "y" in device):
                        placements.append(
                            {
                                "id": device.get("id"),
                                "name": device.get("name"),
                                "mac": device.get("mac"),
                                "type": device.get("type"),
                                "model": device.get("model"),
                                "map_id": device.get("map_id"),
                                "x": device.get("x"),
                                "y": device.get("y"),
                                "orientation": device.get("orientation"),
                                "height": device.get("height"),
                            }
                        )
                logging.debug(f"Backup includes {len(placements)} device placements for map {map_id}")
                return placements
            logging.warning(f"Could not fetch devices for backup: HTTP {devices_response.status_code}")
        except Exception as device_err:
            logging.warning(f"Device placement backup failed: {device_err}")
        return []

    def _backup_write_file(self, geometry_backup, map_name, backup_reason, name_timestamp=None):
        """Write backup data to JSON file. Returns file path."""
        import json
        from datetime import datetime

        if name_timestamp:
            safe_map_name, timestamp = name_timestamp
        else:
            safe_map_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in map_name)
            safe_map_name = safe_map_name.strip().replace(" ", "_")[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_filename = f"map_backup_{safe_map_name}_{backup_reason}_{timestamp}.json"
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        backup_path = os.path.join(data_dir, backup_filename)

        with open(backup_path, "w", encoding="utf-8") as backup_file:
            json.dump(geometry_backup, backup_file, indent=2, ensure_ascii=False)
        return backup_path, backup_filename

    def _backup_print_summary(self, backup_filename, image_filename, geometry_backup):
        """Print backup summary to console."""
        counts = [
            ("Image", "Yes" if image_filename else None),
            ("Walls", len((geometry_backup.get("geometry") or {}).get("wall_path", {}).get("nodes", [])) or None),
            (
                "Wayfinding",
                len((geometry_backup.get("geometry") or {}).get("wayfinding_path", {}).get("nodes", [])) or None,
            ),
            ("Zones", len(geometry_backup.get("zones", [])) or None),
            ("Devices", len(geometry_backup.get("device_placements", [])) or None),
            ("Beacons", len(geometry_backup.get("beacons", [])) or None),
            ("VBeacons", len(geometry_backup.get("vbeacons", [])) or None),
        ]
        summary = ", ".join(f"{k}: {v}" for k, v in counts if v) or "Empty map"
        logging.info(f"Map backup saved: {backup_filename} ({summary})")
        print(f"\n   [*] Map backup saved: {backup_filename}")
        if image_filename:
            print(f"       Image: {image_filename}")
        print(f"       {summary}")

    def _backup_map_geometry(self, api_session, site_id, map_id, map_name, backup_reason="manual"):
        """Backup map geometry data (walls, zones, wayfinding paths) to JSON file.

        Called automatically before destructive operations (delete) and during cloning
        to preserve geometry data that would otherwise be lost.

        Returns:
            str: Path to backup file if successful, None if failed.
        """
        from datetime import datetime

        try:
            logging.info(f"Map geometry backup initiated - map: {map_name} ({map_id}), reason: {backup_reason}")

            map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)
            if map_response.status_code != 200:
                logging.error(f"Map backup failed: Could not fetch map data - HTTP {map_response.status_code}")
                return None

            map_data = map_response.data

            geometry_backup = {
                "backup_info": {
                    "timestamp": datetime.now().isoformat(),
                    "reason": backup_reason,
                    "map_id": map_id,
                    "map_name": map_name,
                    "site_id": site_id,
                },
                "map_properties": {
                    key: map_data.get(key)
                    for key in [
                        "name",
                        "type",
                        "width",
                        "height",
                        "width_m",
                        "height_m",
                        "ppm",
                        "orientation",
                        "origin_x",
                        "origin_y",
                        "latlng",
                        "latlng_tl",
                        "latlng_br",
                        "locked",
                        "view",
                        "occupancy_limit",
                        "flags",
                        "url",
                        "thumbnail_url",
                    ]
                },
                "geometry": {
                    "wall_path": map_data.get("wall_path"),
                    "wayfinding_path": map_data.get("wayfinding_path"),
                    "wayfinding": map_data.get("wayfinding"),
                    "sitesurvey_path": map_data.get("sitesurvey_path"),
                },
            }

            # Download image
            image_filename, name_timestamp = self._backup_download_image(map_data, map_name, backup_reason)
            if image_filename:
                geometry_backup["backup_info"]["image_file"] = image_filename

            # Fetch related entities
            geometry_backup["device_placements"] = self._backup_fetch_device_placements(api_session, site_id, map_id)
            geometry_backup["zones"] = self._backup_fetch_items(
                api_session, site_id, map_id, mistapi.api.v1.sites.zones.listSiteZones, "zones"
            )
            geometry_backup["beacons"] = self._backup_fetch_items(
                api_session, site_id, map_id, mistapi.api.v1.sites.beacons.listSiteBeacons, "beacons"
            )
            geometry_backup["vbeacons"] = self._backup_fetch_items(
                api_session, site_id, map_id, mistapi.api.v1.sites.vbeacons.listSiteVBeacons, "vbeacons"
            )

            # Write and summarize
            backup_path, backup_filename = self._backup_write_file(
                geometry_backup, map_name, backup_reason, name_timestamp
            )
            self._backup_print_summary(backup_filename, image_filename, geometry_backup)

            return backup_path

        except Exception as backup_error:
            logging.error(f"Map geometry backup failed: {backup_error}", exc_info=True)
            print(f"\n   [!] Warning: Could not backup map geometry: {backup_error}")
            return None

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
                logging.error(f"Test '{test_name}' failed with exception", exc_info=True)

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
            logging.error(f"_test_list_all_org_maps failed: {e}")
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
            logging.error(f"_test_export_all_site_maps failed: {e}")
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
            logging.error(f"_test_maps_without_images failed: {e}")
            return False

    def _build_menu_dispatch(self) -> dict:
        """Build menu choice to handler mapping."""
        return {
            "S": self.select_site,
            "1": self.list_site_maps,
            "2": self.export_site_maps,
            "3": self.view_map_details,
            "4": self.create_site_map,
            "5": self.update_map_properties,
            "6": self.delete_site_map,
            "7": self.upload_map_image,
            "8": self.view_devices_on_map,
            "9": self.auto_place_aps,
            "10": self.auto_orient_aps,
            "11": self.set_device_location,
            "12": self.clone_map,
            "13": self.intelligent_map_replacement_wizard,
            "20": self.list_all_org_maps,
            "21": self.export_all_site_maps,
            "22": self.export_maps_with_images,
            "23": self.bulk_download_org_images,
            "24": self.backup_all_maps,
            "25": self.maps_without_images_report,
            "30": self.map_coverage_analytics,
            "31": self.device_density_analytics,
            "32": self.map_usage_statistics,
            "40": self.interactive_map_viewer,
        }

    def _print_menu(self) -> None:
        """Display the Maps Manager menu."""
        print("\n" + "=" * 80)
        print("MAPS MANAGER - Site Floorplan & Map Operations")
        if self.current_site_name:
            print(f"Current Site: {self.current_site_name}")
        print("=" * 80)
        print("\nSite Selection:")
        print("  S. Select different site")
        print("\nMap Inventory & Export:")
        print("  1. List maps for current site")
        print("  2. Export maps for current site to CSV/SQLite")
        print("  3. View detailed map information")
        print("\nMap Creation & Modification:")
        print("  4. Create new site map")
        print("  5. Update map properties")
        print("  6. Delete site map")
        print("  7. Upload/replace map image")
        print("  12. Clone/duplicate map")
        print("  13. Intelligent map replacement wizard")
        print("\nDevice Placement:")
        print("  8. View devices on map")
        print("  9. Auto-place APs on map")
        print("  10. Auto-orient APs on map")
        print("  11. Set AP/device location manually")
        print("\nBulk Operations (All Sites):")
        print("  20. List all site maps across organization")
        print("  21. Export all site maps to CSV/SQLite")
        print("  22. Export maps with image metadata")
        print("  23. Download all org map images")
        print("  24. Backup all maps (metadata + images)")
        print("  25. Maps without images report")
        print("\nAnalytics & Reporting:")
        print("  30. Map coverage analytics")
        print("  31. Device density by map")
        print("  32. Map usage statistics")
        print("\nVisualization & Editing:")
        print("  40. Interactive map viewer (view/edit devices, walls, zones)")
        print("\n  0. Return to main menu")
        print("=" * 80)

    def run_interactive_menu(self):
        """Main interactive menu loop for Maps Manager."""
        print("\n" + "=" * 80)
        print("MAPS MANAGER - Initial Site Selection")
        print("=" * 80)
        print("\nPlease select a site to work with:")
        if not self.select_site():
            print("\n! Site selection required. Returning to main menu.")
            return

        dispatch = self._build_menu_dispatch()

        while True:
            self._print_menu()

            try:
                choice = input("\nEnter your selection number now: ").strip().upper()
            except EOFError:
                logging.info("EOF detected in MapsManager menu - session disconnected")
                return

            if choice == "0":
                logging.info("Exiting Maps Manager")
                return

            handler = dispatch.get(choice)
            if handler:
                handler()
            else:
                print(f"\n! Invalid selection: '{choice}'. Please enter a valid option.")
                logging.warning(f"Invalid Maps Manager menu selection: {choice}")

    def list_site_maps(self):
        """Display list of maps for currently selected site."""
        print("\n" + "-" * 80)
        print("LIST SITE MAPS - Current Site")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            print(f"\nFetching maps for site: {site_name}")
            maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)

            if maps_response.status_code != 200:
                print(f"\n! Failed to fetch maps: HTTP {maps_response.status_code}")
                return

            maps = maps_response.data
            if not maps:
                print(f"\n! No maps found for site: {site_name}")
                return

            # Display summary
            print(f"\n{'-' * 80}")
            print(f"Total Maps Found: {len(maps)}")
            print(f"{'-' * 80}")
            print(f"{'Map Name':<35} {'Type':<15} {'Dimensions':<20} {'Image':<8}")
            print(f"{'-' * 80}")

            for map_item in maps:
                map_name = map_item.get("name", "Unnamed")[:34]
                map_type = map_item.get("type", "N/A")[:14]
                width = map_item.get("width", 0)
                height = map_item.get("height", 0)
                dimensions = f"{width}x{height}" if width and height else "N/A"
                has_image = "Yes" if "url" in map_item else "No"
                print(f"{map_name:<35} {map_type:<15} {dimensions:<20} {has_image:<8}")

            print(f"{'-' * 80}")
            logging.info(f"Listed {len(maps)} maps for site {site_name}")

        except Exception as e:
            logging.error(f"Error listing site maps: {e}", exc_info=True)
            print(f"\n! Error listing maps: {e}")

    def list_all_org_maps(self):
        """Display summary list of all maps across organization sites."""
        print("\n" + "-" * 80)
        print("LIST ALL ORGANIZATION MAPS - All Sites")
        print("-" * 80)

        try:
            # Fetch all sites
            sites = self._fetch_sites()
            if not sites:
                print("\n! No sites found in organization")
                return

            print(f"\nFetching maps from {len(sites)} sites...")
            all_maps = []

            for site in tqdm(sites, desc="Scanning sites", unit="site"):
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site["id"])

                    if maps_response.status_code == 200:
                        maps = maps_response.data
                        for map_item in maps:
                            all_maps.append(
                                {
                                    "site_id": site["id"],
                                    "site_name": site.get("name", "Unknown"),
                                    "map_id": map_item.get("id", "N/A"),
                                    "map_name": map_item.get("name", "Unnamed"),
                                    "type": map_item.get("type", "N/A"),
                                    "width": map_item.get("width", 0),
                                    "height": map_item.get("height", 0),
                                    "has_image": "url" in map_item,
                                }
                            )
                except Exception as e:
                    logging.debug(f"Error fetching maps for site {site['id']}: {e}")
                    continue

            if not all_maps:
                print("\n! No maps found across all sites")
                return

            # Display summary
            print(f"\n{'-' * 80}")
            print(f"Total Maps Found: {len(all_maps)}")
            print(f"{'-' * 80}")
            print(f"{'Site Name':<30} {'Map Name':<25} {'Type':<15} {'Image':<8}")
            print(f"{'-' * 80}")

            for map_item in all_maps:
                site_name = map_item["site_name"][:29]
                map_name = map_item["map_name"][:24]
                map_type = map_item["type"][:14]
                has_image = "Yes" if map_item["has_image"] else "No"
                print(f"{site_name:<30} {map_name:<25} {map_type:<15} {has_image:<8}")

            print(f"{'-' * 80}")
            logging.info(f"Listed {len(all_maps)} maps from {len(sites)} sites")

        except Exception as e:
            logging.error(f"Error listing site maps: {e}", exc_info=True)
            print(f"\n! Error listing maps: {e}")

    def export_site_maps(self):
        """Export maps for currently selected site to CSV/SQLite."""
        print("\n" + "-" * 80)
        print("EXPORT SITE MAPS - Current Site")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            print(f"\nExporting maps for site: {site_name}")
            maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)

            if maps_response.status_code != 200:
                print(f"\n! Failed to fetch maps: HTTP {maps_response.status_code}")
                return

            maps = maps_response.data
            if not maps:
                print(f"\n! No maps found for site: {site_name}")
                return

            # Flatten and prepare data
            maps_data = []
            for map_item in maps:
                flattened = flatten_dict_recursively(map_item)
                flattened["site_id"] = site_id
                flattened["site_name"] = site_name
                flattened["org_id"] = self.org_id
                maps_data.append(flattened)

            # Write to dual output format
            safe_site_name = sanitize_filename(site_name or "unknown_site")
            filename = f"SiteMaps_{safe_site_name}"
            write_data_with_format_selection(maps_data, filename, api_function_name="listSiteMaps")

            print(f"\n{'-' * 80}")
            print(f"Export completed: {len(maps_data)} maps exported")
            print(f"{'-' * 80}")
            logging.info(f"Exported {len(maps_data)} maps from site {site_name}")

        except Exception as e:
            logging.error(f"Error exporting site maps: {e}", exc_info=True)
            print(f"\n! Error during export: {e}")

    def export_all_site_maps(self):
        """Export all site maps across organization to CSV/SQLite with full metadata."""
        print("\n" + "-" * 80)
        print("EXPORT ALL ORGANIZATION MAPS - All Sites")
        print("-" * 80)

        try:
            sites = self._fetch_sites()
            if not sites:
                print("\n! No sites found in organization")
                return

            print(f"\nExporting maps from {len(sites)} sites...")
            all_maps_data = []

            for site in tqdm(sites, desc="Exporting maps", unit="site"):
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site["id"])

                    if maps_response.status_code == 200:
                        maps = maps_response.data
                        for map_item in maps:
                            # Flatten nested structures
                            flattened = flatten_dict_recursively(map_item)
                            flattened["site_id"] = site["id"]
                            flattened["site_name"] = site.get("name", "Unknown")
                            flattened["org_id"] = self.org_id
                            all_maps_data.append(flattened)
                except Exception as e:
                    logging.debug(f"Error exporting maps for site {site['id']}: {e}")
                    continue

            if not all_maps_data:
                print("\n! No maps found to export")
                return

            # Write to dual output format
            filename = "SiteMaps_Export"
            write_data_with_format_selection(all_maps_data, filename, api_function_name="listSiteMaps")

            print(f"\n{'-' * 80}")
            print(f"Export completed: {len(all_maps_data)} maps exported")
            print(f"{'-' * 80}")
            logging.info(f"Exported {len(all_maps_data)} maps from {len(sites)} sites")

        except Exception as e:
            logging.error(f"Error exporting site maps: {e}", exc_info=True)
            print(f"\n! Error during export: {e}")

    def export_maps_with_images(self):
        """Export maps metadata focusing on image information."""
        print("\n" + "-" * 80)
        print("EXPORT MAPS WITH IMAGE METADATA")
        print("-" * 80)

        try:
            sites = self._fetch_sites()
            if not sites:
                print("\n! No sites found in organization")
                return

            print(f"\nScanning {len(sites)} sites for maps with images...")
            maps_with_images = []

            for site in tqdm(sites, desc="Scanning for images", unit="site"):
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site["id"])

                    if maps_response.status_code == 200:
                        maps = maps_response.data
                        for map_item in maps:
                            if "url" in map_item or "thumbnail_url" in map_item:
                                flattened = flatten_dict_recursively(map_item)
                                flattened["site_id"] = site["id"]
                                flattened["site_name"] = site.get("name", "Unknown")
                                flattened["org_id"] = self.org_id
                                maps_with_images.append(flattened)
                except Exception as e:
                    logging.debug(f"Error scanning site {site['id']}: {e}")
                    continue

            if not maps_with_images:
                print("\n! No maps with images found")
                return

            filename = "SiteMaps_WithImages"
            write_data_with_format_selection(maps_with_images, filename, api_function_name="listSiteMaps")

            print(f"\n{'-' * 80}")
            print(f"Export completed: {len(maps_with_images)} maps with images")
            print(f"{'-' * 80}")
            logging.info(f"Exported {len(maps_with_images)} maps with images")

        except Exception as e:
            logging.error(f"Error exporting maps with images: {e}", exc_info=True)
            print(f"\n! Error during export: {e}")

    def download_site_map_images(self):
        """Download map images to local disk."""
        print("\n" + "-" * 80)
        print("DOWNLOAD SITE MAP IMAGES")
        print("-" * 80)

        try:
            # Prompt for site selection
            site_id, _ = self.get_current_site()
            if not site_id:
                print("\n! No site selected")
                return

            # Get site name for display
            sites = self._fetch_sites()
            site_name = next((s.get("name", "Unknown") for s in sites if s["id"] == site_id), "Unknown")

            print(f"\nFetching maps for site: {site_name}")
            maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)

            if maps_response.status_code != 200:
                print(f"\n! Failed to fetch maps: {maps_response.status_code}")
                return

            maps = maps_response.data
            maps_with_images = [m for m in maps if "url" in m]

            if not maps_with_images:
                print(f"\n! No maps with images found for site: {site_name}")
                return

            print(f"\nFound {len(maps_with_images)} maps with images")

            # Create download directory
            import os

            download_dir = os.path.join("data", "map_images", sanitize_filename(site_name))
            os.makedirs(download_dir, exist_ok=True)

            print(f"Downloading to: {download_dir}")

            import requests

            downloaded = 0

            for map_item in tqdm(maps_with_images, desc="Downloading", unit="image"):
                try:
                    map_name = map_item.get("name", "unnamed")
                    map_id = map_item.get("id", "unknown")
                    image_url = map_item.get("url")

                    if not image_url:
                        continue

                    # Determine file extension from URL or default to .png
                    file_ext = ".png"
                    if "." in image_url:
                        url_ext = image_url.rsplit(".", 1)[-1].split("?")[0]
                        if url_ext.lower() in ["png", "jpg", "jpeg", "gif", "svg"]:
                            file_ext = f".{url_ext.lower()}"

                    filename = f"{sanitize_filename(map_name)}_{map_id[:8]}{file_ext}"
                    filepath = os.path.join(download_dir, filename)

                    response = requests.get(image_url, timeout=30)
                    if response.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                        downloaded += 1
                    else:
                        logging.warning(f"Failed to download {map_name}: HTTP {response.status_code}")

                except Exception as e:
                    logging.error(f"Error downloading map image {map_item.get('id')}: {e}")
                    continue

            print(f"\n{'-' * 80}")
            print(f"Downloaded {downloaded} of {len(maps_with_images)} images")
            print(f"Location: {download_dir}")
            print(f"{'-' * 80}")
            logging.info(f"Downloaded {downloaded} map images to {download_dir}")

        except Exception as e:
            logging.error(f"Error downloading map images: {e}", exc_info=True)
            print(f"\n! Error downloading images: {e}")

    def view_map_details(self):
        """View detailed information for a specific map."""
        print("\n" + "-" * 80)
        print("VIEW MAP DETAILS")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            # Fetch maps for the site
            maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)

            if maps_response.status_code != 200:
                print(f"\n! Failed to fetch maps: {maps_response.status_code}")
                return

            maps = maps_response.data
            if not maps:
                print(f"\n! No maps found for site: {site_name}")
                return

            # Auto-select if only one map available
            if len(maps) == 1:
                selected_map = maps[0]
                map_name = selected_map.get("name", "Unnamed")
                map_id = selected_map.get("id")
                print(f"\nAuto-selecting only available map: {map_name}")
            else:
                # Display map selection
                print(f"\nMaps for site: {site_name}")
                print(f"{'-' * 80}")
                for idx, map_item in enumerate(maps, 1):
                    map_name = map_item.get("name", "Unnamed")
                    map_type = map_item.get("type", "N/A")
                    print(f"  {idx}. {map_name} ({map_type})")
                print(f"{'-' * 80}")

                try:
                    selection = input("\nSelect map number (or 0 to cancel): ").strip()
                    map_idx = int(selection) - 1

                    if map_idx < 0 or map_idx >= len(maps):
                        print("\n! Invalid selection")
                        return

                    selected_map = maps[map_idx]
                    map_id = selected_map.get("id")
                except ValueError:
                    print("\n! Invalid input - please enter a number")
                    return
                except EOFError:
                    logging.info("EOF detected during map selection")
                    return

            # Fetch detailed map info
            detail_response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)

            if detail_response.status_code != 200:
                print(f"\n! Failed to fetch map details: {detail_response.status_code}")
                return

            map_details = detail_response.data

            # Display details
            print(f"\n{'-' * 80}")
            print(f"MAP DETAILS: {map_details.get('name', 'Unnamed')}")
            print(f"{'-' * 80}")
            print(f"Map ID: {map_details.get('id', 'N/A')}")
            print(f"Type: {map_details.get('type', 'N/A')}")
            print(f"Width: {map_details.get('width', 0)} pixels")
            print(f"Height: {map_details.get('height', 0)} pixels")
            print(f"PPM (Pixels per meter): {map_details.get('ppm', 'N/A')}")
            print(f"Orientation: {map_details.get('orientation', 0)} degrees")
            print(f"Has Image: {'Yes' if 'url' in map_details else 'No'}")

            if "url" in map_details:
                print(f"Image URL: {map_details['url'][:80]}...")

            if "latlng" in map_details:
                latlng = map_details["latlng"]
                print(f"Coordinates: {latlng.get('lat')}, {latlng.get('lng')}")

            if "wayfinding" in map_details:
                print("Wayfinding Enabled: Yes")

            print(f"{'-' * 80}")
            logging.info(f"Viewed details for map {map_id}")

        except Exception as e:
            logging.error(f"Error viewing map details: {e}", exc_info=True)
            print(f"\n! Error viewing map details: {e}")

    def create_site_map(self):
        """Create a new site map with basic configuration."""
        print("\n" + "-" * 80)
        print("CREATE NEW SITE MAP")
        print("-" * 80)
        print("\n! Note: This creates a map placeholder. Upload image separately (Menu 7)")

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            print(f"\nCreating map for site: {site_name}")
            print(f"{'-' * 80}")

            # Gather map configuration
            try:
                map_name = input("Enter map name: ").strip()
                if not map_name:
                    print("\n! Map name is required")
                    return

                print("\nMap type options:")
                print("  1. image (standard floor plan)")
                print("  2. google (Google Maps integration)")
                print("  3. baidu (Baidu Maps integration)")
                map_type_choice = input("Select type (1-3, default=1): ").strip() or "1"

                type_map = {"1": "image", "2": "google", "3": "baidu"}
                map_type = type_map.get(map_type_choice, "image")

                # Optional: dimensions (only for image type)
                width = None
                height = None
                ppm = None

                if map_type == "image":
                    width_input = input("Enter width in pixels (default=1024): ").strip()
                    height_input = input("Enter height in pixels (default=768): ").strip()
                    ppm_input = input("Enter pixels per meter (default=10): ").strip()

                    width = int(width_input) if width_input else 1024
                    height = int(height_input) if height_input else 768
                    ppm = float(ppm_input) if ppm_input else 10.0

                # Build map payload
                map_payload: dict[str, Any] = {"name": map_name, "type": map_type}

                if width:
                    map_payload["width"] = width
                if height:
                    map_payload["height"] = height
                if ppm:
                    map_payload["ppm"] = ppm

                # Create the map
                print(f"\nCreating map '{map_name}'...")
                create_response = mistapi.api.v1.sites.maps.createSiteMap(
                    self.apisession, site_id=site_id, body=map_payload
                )

                if create_response.status_code in [200, 201]:
                    created_map = create_response.data
                    print(f"\n{'-' * 80}")
                    print("Map created successfully!")
                    print(f"Map ID: {created_map.get('id')}")
                    print(f"Name: {created_map.get('name')}")
                    print(f"Type: {created_map.get('type')}")
                    print(f"{'-' * 80}")
                    logging.info(f"Created map {created_map.get('id')} for site {site_id}")
                else:
                    print(f"\n! Failed to create map: HTTP {create_response.status_code}")
                    logging.error(f"Map creation failed: {create_response.status_code} - {create_response.data}")

            except ValueError as ve:
                print(f"\n! Invalid input: {ve}")
            except EOFError:
                logging.info("EOF detected during map creation")
                return

        except Exception as e:
            logging.error(f"Error creating site map: {e}", exc_info=True)
            print(f"\n! Error creating map: {e}")

    def clone_map(self):
        """Clone/duplicate an existing map at the current site including image, walls, paths, and zones."""
        logging.info("clone_map operation initiated")
        print("\n" + "-" * 80)
        print("CLONE/DUPLICATE MAP")
        print("-" * 80)
        print("! This will clone ALL map data: image, walls, paths, zones, wayfinding, etc.")

        site_id, site_name = self.get_current_site()
        if not site_id:
            logging.warning("clone_map aborted: No site selected")
            return

        logging.debug(f"clone_map - Site: {site_name} (ID: {site_id})")

        try:
            import os
            import tempfile

            import requests

            # Get source map selection
            print("\nSelect the map to clone:")
            source_map_id = self._select_map_from_site(site_id, site_name)
            if not source_map_id:
                logging.info("clone_map aborted: No source map selected")
                return

            logging.info(f"Cloning map - source_map_id: {source_map_id}")

            # Fetch complete source map details
            print("\nFetching source map details...")
            logging.debug(f"Calling getSiteMap API - site_id: {site_id}, map_id: {source_map_id}")
            source_response = mistapi.api.v1.sites.maps.getSiteMap(
                self.apisession, site_id=site_id, map_id=source_map_id
            )

            logging.debug(f"getSiteMap response: HTTP {source_response.status_code}")
            if source_response.status_code != 200:
                logging.error(f"Failed to fetch source map - HTTP {source_response.status_code}")
                print(f"\n! Failed to fetch source map: HTTP {source_response.status_code}")
                return

            source_map = source_response.data

            # Display source map info with all cloneable attributes
            print(f"\n{'-' * 80}")
            print(f"Source Map: {source_map.get('name', 'Unnamed')}")
            print(f"Type: {source_map.get('type', 'N/A')}")
            print(f"Dimensions: {source_map.get('width', 'N/A')}x{source_map.get('height', 'N/A')}")
            print(f"PPM: {source_map.get('ppm', 'N/A')}")
            print(f"Has Image: {'Yes' if 'url' in source_map else 'No'}")
            print(f"Has Walls: {'Yes' if 'wall_path' in source_map else 'No'}")
            print(f"Has Wayfinding: {'Yes' if 'wayfinding_path' in source_map else 'No'}")
            print(f"{'-' * 80}")

            # Prompt for new map name
            default_name = f"{source_map.get('name', 'Map')} (Copy)"
            new_name = input(f"\nEnter name for cloned map [{default_name}]: ").strip()
            if not new_name:
                new_name = default_name

            logging.info(f"Creating clone with new name: {new_name}")

            # Build complete clone payload - copy ALL relevant properties
            clone_payload = {"name": new_name, "type": source_map.get("type", "image")}
            logging.debug(f"Base clone payload: {clone_payload}")

            # Copy dimensional properties
            if "width" in source_map:
                clone_payload["width"] = source_map["width"]
            if "height" in source_map:
                clone_payload["height"] = source_map["height"]
            if "height_m" in source_map:
                clone_payload["height_m"] = source_map["height_m"]
            if "ppm" in source_map:
                clone_payload["ppm"] = source_map["ppm"]
            if "orientation" in source_map:
                clone_payload["orientation"] = source_map["orientation"]

            # Copy location data
            if "latlng" in source_map:
                clone_payload["latlng"] = source_map["latlng"]
            if "latlng_br" in source_map:
                clone_payload["latlng_br"] = source_map["latlng_br"]
            if "origin_x" in source_map:
                clone_payload["origin_x"] = source_map["origin_x"]
            if "origin_y" in source_map:
                clone_payload["origin_y"] = source_map["origin_y"]

            # Copy wayfinding configuration
            if "wayfinding" in source_map:
                clone_payload["wayfinding"] = source_map["wayfinding"]
            if "wayfinding_path" in source_map:
                clone_payload["wayfinding_path"] = source_map["wayfinding_path"]

            # Copy wall paths (critical for RF modeling)
            if "wall_path" in source_map:
                clone_payload["wall_path"] = source_map["wall_path"]

            # Copy site survey paths
            if "sitesurvey_path" in source_map:
                clone_payload["sitesurvey_path"] = source_map["sitesurvey_path"]

            # Copy other map-specific settings
            if "occupancy_limit" in source_map:
                clone_payload["occupancy_limit"] = source_map["occupancy_limit"]
            if "locked" in source_map:
                clone_payload["locked"] = source_map["locked"]
            if "view" in source_map:
                clone_payload["view"] = source_map["view"]

            # Check for zones on source map to include in clone plan
            source_zones_count = 0
            try:
                zones_check = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)
                if zones_check.status_code == 200:
                    source_zones_count = len([z for z in zones_check.data if z.get("map_id") == source_map_id])
            except Exception as zone_error:
                logging.debug("Could not fetch zone count for clone plan: %s", zone_error)

            # Display clone plan
            print(f"\n{'-' * 80}")
            print("Clone Plan:")
            print(f"  New name: {new_name}")
            print("  Will copy: dimensions, orientation, location data, wayfinding, walls")
            print(f"  Image: {'Yes - will download and re-upload' if 'url' in source_map else 'No image to copy'}")
            print(
                f"  Zones: {source_zones_count} zone(s) will be cloned"
                if source_zones_count > 0
                else "  Zones: None found on source map"
            )
            print(f"{'-' * 80}")

            confirm = input("\nProceed with full clone? (yes/no): ").strip().lower()
            if confirm not in ["yes", "y"]:
                print("\n! Clone cancelled")
                return

            # Download image to temporary file if present
            image_temp_path = None
            if "url" in source_map:
                try:
                    print("\nDownloading map image...")
                    image_url = source_map["url"]

                    # Determine file extension
                    file_ext = ".png"
                    if "." in image_url:
                        url_ext = image_url.rsplit(".", 1)[-1].split("?")[0]
                        if url_ext.lower() in ["png", "jpg", "jpeg", "gif", "svg"]:
                            file_ext = f".{url_ext.lower()}"

                    # Create temporary file
                    temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)
                    os.close(temp_fd)

                    # Download image
                    response = requests.get(image_url, timeout=60)
                    if response.status_code == 200:
                        with open(image_temp_path, "wb") as f:
                            f.write(response.content)
                        print(f"Downloaded image ({len(response.content) / 1024:.1f} KB)")
                    else:
                        print(f"! Warning: Failed to download image (HTTP {response.status_code})")
                        if image_temp_path and os.path.exists(image_temp_path):
                            os.remove(image_temp_path)
                        image_temp_path = None

                except Exception as e:
                    logging.error(f"Error downloading map image: {e}")
                    print(f"! Warning: Could not download image: {e}")
                    if image_temp_path and os.path.exists(image_temp_path):
                        os.remove(image_temp_path)
                    image_temp_path = None

            # Create the cloned map
            print("\nCreating cloned map...")
            clone_response = mistapi.api.v1.sites.maps.createSiteMap(
                self.apisession, site_id=site_id, body=clone_payload
            )

            if clone_response.status_code not in [200, 201]:
                print(f"\n! Failed to clone map: HTTP {clone_response.status_code}")
                logging.error(f"Map clone failed: {clone_response.status_code} - {clone_response.data}")
                # Clean up temp file
                if image_temp_path and os.path.exists(image_temp_path):
                    os.remove(image_temp_path)
                return

            cloned_map = clone_response.data
            cloned_map_id = cloned_map.get("id")

            if not cloned_map_id:
                print("\n! Error: Cloned map has no ID")
                logging.error("Cloned map missing ID in response")
                return

            print(f"\n{'-' * 80}")
            print("Map structure cloned successfully!")
            print(f"Cloned Map ID: {cloned_map_id}")
            print(f"Name: {cloned_map.get('name')}")
            print(f"{'-' * 80}")

            # Upload image to cloned map if we have one
            if image_temp_path and os.path.exists(image_temp_path):
                try:
                    print("\nUploading image to cloned map...")
                    upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(  # type: ignore[union-attr]
                        self.apisession, site_id=site_id, map_id=str(cloned_map_id), file=image_temp_path
                    )

                    if upload_response.status_code in [200, 201]:
                        print("Image uploaded successfully!")
                        logging.info(f"Image uploaded to cloned map {cloned_map_id}")
                    else:
                        print(f"! Warning: Failed to upload image: HTTP {upload_response.status_code}")
                        logging.error(f"Image upload to cloned map failed: {upload_response.status_code}")

                except Exception as e:
                    logging.error(f"Error uploading image to cloned map: {e}")
                    print(f"! Warning: Could not upload image to cloned map: {e}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(image_temp_path):
                        os.remove(image_temp_path)

            # Clone zones that belong to the source map
            zones_cloned = 0
            zones_failed = 0
            try:
                print("\nCloning zones...")
                zones_response = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)

                if zones_response.status_code == 200:
                    all_zones = zones_response.data
                    # Filter zones that belong to the source map
                    source_map_zones = [z for z in all_zones if z.get("map_id") == source_map_id]
                    logging.info(f"Found {len(source_map_zones)} zones on source map to clone")

                    if source_map_zones:
                        for zone in source_map_zones:
                            try:
                                # Build zone payload for cloned map
                                zone_payload = {
                                    "name": zone.get("name", "Unnamed Zone"),
                                    "map_id": cloned_map_id,
                                    "vertices": zone.get("vertices", []),
                                }

                                # Copy optional zone properties if present
                                if "type" in zone:
                                    zone_payload["type"] = zone["type"]
                                if "z" in zone:
                                    zone_payload["z"] = zone["z"]

                                # Create zone on cloned map
                                zone_response = mistapi.api.v1.sites.zones.createSiteZone(
                                    self.apisession, site_id=site_id, body=zone_payload
                                )

                                if zone_response.status_code in [200, 201]:
                                    zones_cloned += 1
                                    logging.debug(f"Cloned zone '{zone.get('name')}' to new map")
                                else:
                                    zones_failed += 1
                                    logging.warning(
                                        f"Failed to clone zone '{zone.get('name')}': HTTP {zone_response.status_code}"
                                    )

                            except Exception as zone_error:
                                zones_failed += 1
                                logging.error(f"Error cloning zone '{zone.get('name')}': {zone_error}")

                        print(f"Zones cloned: {zones_cloned} (failed: {zones_failed})")
                    else:
                        print("No zones found on source map to clone")
                else:
                    logging.warning(f"Failed to fetch zones for cloning - HTTP {zones_response.status_code}")
                    print("! Warning: Could not fetch zones for cloning")

            except Exception as zones_error:
                logging.error(f"Error during zone cloning: {zones_error}", exc_info=True)
                print(f"! Warning: Zone cloning failed: {zones_error}")

            # Display final summary
            print(f"\n{'-' * 80}")
            print("CLONE COMPLETE")
            print(f"{'-' * 80}")
            print(f"Original Map: {source_map.get('name')}")
            print(f"Cloned Map: {new_name}")
            print(f"Cloned Map ID: {cloned_map_id}")
            print("\nCloned elements:")
            print(f"  -> Dimensions: {clone_payload.get('width', 'N/A')}x{clone_payload.get('height', 'N/A')}")
            print(f"  -> PPM: {clone_payload.get('ppm', 'N/A')}")
            print(f"  -> Walls: {'Yes' if 'wall_path' in clone_payload else 'No'}")
            print(f"  -> Wayfinding: {'Yes' if 'wayfinding_path' in clone_payload else 'No'}")
            print(f"  -> Image: {'Yes' if image_temp_path else 'No'}")
            print(f"  -> Zones: {zones_cloned} cloned" + (f" ({zones_failed} failed)" if zones_failed > 0 else ""))
            print(f"{'-' * 80}")

            logging.info(
                f"Successfully cloned map {source_map_id} to {cloned_map_id} at site {site_id} (zones: {zones_cloned})"
            )

        except EOFError:
            logging.info("EOF detected during map clone")
            return
        except Exception as e:
            logging.error(f"Error cloning map: {e}", exc_info=True)
            print(f"\n! Error cloning map: {e}")

    def intelligent_map_replacement_wizard(self):
        """Intelligent Map Replacement Wizard.

        Replaces a floor plan image while intelligently preserving and translating:
        - Device placements (APs, switches, gateways) with coordinate scaling
        - Zones with vertex coordinate translation
        - Walls and wayfinding paths
        - Beacons and virtual beacons

        Supports different scale/dimension scenarios:
        1. Same dimensions - direct replacement
        2. Different dimensions, same scale - coordinate translation
        3. Different dimensions, different scale - intelligent scaling with preview
        """
        logging.info("intelligent_map_replacement_wizard initiated")
        print("\n" + "=" * 80)
        print("INTELLIGENT MAP REPLACEMENT WIZARD")
        print("=" * 80)
        print("\nThis wizard helps you replace a floor plan image while preserving")
        print("device placements, zones, walls, and other map data.")
        print("\nThe wizard will:")
        print("  1. Backup current map data")
        print("  2. Analyze dimension and scale differences")
        print("  3. Calculate coordinate translations")
        print("  4. Preview affected devices/zones")
        print("  5. Apply changes with confirmation")
        print("=" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            logging.warning("Map replacement wizard aborted: No site selected")
            return

        logging.debug(f"Map replacement wizard - Site: {site_name} (ID: {site_id})")

        try:
            import os

            from PIL import Image

            # Step 1: Select the map to update
            print("\n" + "-" * 80)
            print("STEP 1: Select Map to Replace")
            print("-" * 80)

            map_id = self._select_map_from_site(site_id, site_name)
            if not map_id:
                logging.info("Map replacement wizard aborted: No map selected")
                return

            # Fetch current map details
            print("\nFetching current map data...")
            current_map_response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)

            if current_map_response.status_code != 200:
                print(f"\n! Failed to fetch map details: HTTP {current_map_response.status_code}")
                return

            current_map = current_map_response.data
            map_name = current_map.get("name", "Unnamed")

            # Display current map info
            print(f"\n{'-' * 80}")
            print(f"Current Map: {map_name}")
            print(f"{'-' * 80}")
            print(f"  Type: {current_map.get('type', 'N/A')}")
            print(f"  Pixel Dimensions: {current_map.get('width', 'N/A')} x {current_map.get('height', 'N/A')} px")
            print(f"  Physical Size: {current_map.get('width_m', 'N/A')} x {current_map.get('height_m', 'N/A')} meters")
            print(f"  Scale (PPM): {current_map.get('ppm', 'N/A')} pixels/meter")
            print(f"  Has Image: {'Yes' if 'url' in current_map else 'No'}")
            print(f"  Has Walls: {'Yes' if current_map.get('wall_path', {}).get('nodes') else 'No'}")
            print(f"  Has Wayfinding: {'Yes' if current_map.get('wayfinding_path', {}).get('nodes') else 'No'}")

            # Store original properties
            original_width_px = current_map.get("width", 0)
            original_height_px = current_map.get("height", 0)
            original_ppm = current_map.get("ppm", 1)
            original_width_m = current_map.get("width_m", 0)

            # Count devices on this map
            devices_on_map = []
            try:
                devices_response = mistapi.api.v1.sites.devices.listSiteDevices(
                    self.apisession, site_id=site_id, type="all"
                )
                if devices_response.status_code == 200:
                    all_devices = devices_response.data if isinstance(devices_response.data, list) else []
                    devices_on_map = [d for d in all_devices if d.get("map_id") == map_id]
            except Exception as device_error:
                logging.debug("Could not fetch devices for map detail: %s", device_error)

            # Count zones on this map
            zones_on_map = []
            try:
                zones_response = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)
                if zones_response.status_code == 200:
                    zones_on_map = [z for z in zones_response.data if z.get("map_id") == map_id]
            except Exception as zone_error:
                logging.debug("Could not fetch zones for map detail: %s", zone_error)
            beacons_on_map = []
            vbeacons_on_map = []
            try:
                beacons_response = mistapi.api.v1.sites.beacons.listSiteBeacons(self.apisession, site_id=site_id)
                if beacons_response.status_code == 200:
                    beacons_on_map = [b for b in beacons_response.data if b.get("map_id") == map_id]

                vbeacons_response = mistapi.api.v1.sites.vbeacons.listSiteVBeacons(self.apisession, site_id=site_id)
                if vbeacons_response.status_code == 200:
                    vbeacons_on_map = [v for v in vbeacons_response.data if v.get("map_id") == map_id]
            except Exception as beacon_error:
                logging.debug("Could not fetch beacons for map detail: %s", beacon_error)

            print("\nAssets on this map:")
            print(f"  Devices: {len(devices_on_map)}")
            print(f"  Zones: {len(zones_on_map)}")
            print(f"  BLE Beacons: {len(beacons_on_map)}")
            print(f"  Virtual Beacons: {len(vbeacons_on_map)}")
            wall_nodes = len(current_map.get("wall_path", {}).get("nodes", []))
            wayfinding_nodes = len(current_map.get("wayfinding_path", {}).get("nodes", []))
            print(f"  Wall Nodes: {wall_nodes}")
            print(f"  Wayfinding Nodes: {wayfinding_nodes}")

            # Step 2: Get new image file
            print(f"\n{'-' * 80}")
            print("STEP 2: Select New Floor Plan Image")
            print("-" * 80)
            print("\nEnter the path to the new floor plan image:")
            print("Supported formats: PNG, JPG, JPEG, GIF")

            try:
                file_path = input("File path: ").strip()
            except EOFError:
                logging.info("EOF detected during file path input")
                return

            # Clean up path
            file_path = file_path.strip('"').strip("'")

            if not file_path:
                print("\n! No file path provided")
                return

            if not os.path.exists(file_path):
                print(f"\n! File not found: {file_path}")
                return

            if not os.path.isfile(file_path):
                print(f"\n! Path is not a file: {file_path}")
                return

            # Validate file extension
            valid_extensions = [".png", ".jpg", ".jpeg", ".gif"]
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in valid_extensions:
                print(f"\n! Invalid file type: {file_ext}")
                print(f"Supported types: {', '.join(valid_extensions)}")
                return

            # Get new image dimensions
            try:
                with Image.open(file_path) as img:
                    new_width_px, new_height_px = img.size
                    print(f"\nNew image dimensions: {new_width_px} x {new_height_px} pixels")
            except Exception as img_err:
                print(f"\n! Failed to read image dimensions: {img_err}")
                return

            # Step 3: Determine scaling mode
            print(f"\n{'-' * 80}")
            print("STEP 3: Configure Scaling")
            print("-" * 80)

            # Check if dimensions are the same
            same_dimensions = new_width_px == original_width_px and new_height_px == original_height_px

            if same_dimensions:
                print("\nImage dimensions match exactly - no coordinate translation needed.")
                scale_x = 1.0
                scale_y = 1.0
                new_ppm = original_ppm
                scaling_mode = "none"
            else:
                print("\nDimension comparison:")
                print(f"  Original: {original_width_px} x {original_height_px} px")
                print(f"  New:      {new_width_px} x {new_height_px} px")

                width_ratio = new_width_px / original_width_px if original_width_px > 0 else 1
                height_ratio = new_height_px / original_height_px if original_height_px > 0 else 1

                print(
                    f"\n  Width ratio:  {width_ratio:.4f}x"
                    f" ({'+' if width_ratio > 1 else ''}{((width_ratio - 1) * 100):.1f}%)"
                )
                print(
                    f"  Height ratio: {height_ratio:.4f}x"
                    f" ({'+' if height_ratio > 1 else ''}{((height_ratio - 1) * 100):.1f}%)"
                )

                # Check if aspect ratio is preserved
                aspect_diff = abs(width_ratio - height_ratio)
                if aspect_diff < 0.01:
                    print("\n  Aspect ratio: Preserved (uniform scaling)")
                else:
                    print(f"\n  WARNING: Aspect ratio differs by {aspect_diff:.2%}")
                    print("  This may cause device placements to appear distorted.")

                print("\nScaling options:")
                print("  1. Proportional - Scale all coordinates by image ratio (recommended)")
                print("  2. Preserve Physical - Keep real-world positions, update PPM only")
                print("  3. Manual PPM - Enter new pixels-per-meter value manually")
                print("  4. No Scaling - Replace image only, keep all coordinates unchanged")

                try:
                    scale_choice = input("\nSelect scaling mode [1]: ").strip() or "1"
                except EOFError:
                    logging.info("EOF detected during scale mode selection")
                    return

                if scale_choice == "1":
                    # Proportional scaling
                    scale_x = width_ratio
                    scale_y = height_ratio
                    new_ppm = original_ppm  # PPM stays same, coordinates scale
                    scaling_mode = "proportional"
                    print(f"\nUsing proportional scaling: x={scale_x:.4f}, y={scale_y:.4f}")

                elif scale_choice == "2":
                    # Preserve physical dimensions - adjust PPM
                    scale_x = 1.0
                    scale_y = 1.0
                    if original_width_m and original_width_m > 0:
                        new_ppm = new_width_px / original_width_m
                    else:
                        new_ppm = new_width_px / (original_width_px / original_ppm) if original_ppm else 1
                    scaling_mode = "preserve_physical"
                    print(f"\nPreserving physical positions. New PPM: {new_ppm:.2f}")

                elif scale_choice == "3":
                    # Manual PPM entry
                    try:
                        new_ppm_input = input(f"Enter new PPM (current: {original_ppm:.2f}): ").strip()
                        new_ppm = float(new_ppm_input) if new_ppm_input else original_ppm
                    except (ValueError, EOFError):
                        print("Invalid PPM value, using original")
                        new_ppm = original_ppm
                    scale_x = width_ratio
                    scale_y = height_ratio
                    scaling_mode = "manual_ppm"
                    print(f"\nUsing manual PPM: {new_ppm:.2f}, scaling: x={scale_x:.4f}, y={scale_y:.4f}")

                else:
                    # No scaling
                    scale_x = 1.0
                    scale_y = 1.0
                    new_ppm = original_ppm
                    scaling_mode = "none"
                    print("\nNo coordinate scaling - image replacement only")

            # Step 4: Create backup
            print(f"\n{'-' * 80}")
            print("STEP 4: Creating Backup")
            print("-" * 80)

            print("\nBacking up current map data...")
            backup_file = self._backup_map_geometry(
                api_session=self.apisession,
                site_id=site_id,
                map_id=map_id,
                map_name=map_name,
                backup_reason="pre_replacement",
            )

            if backup_file:
                print(f"Backup saved: {backup_file}")
            else:
                print("! Warning: Backup may not have completed fully")
                try:
                    proceed = input("Continue anyway? (yes/no): ").strip().lower()
                    if proceed not in ["yes", "y"]:
                        print("\n! Operation cancelled")
                        return
                except EOFError:
                    return

            # Step 5: Preview changes
            print(f"\n{'-' * 80}")
            print("STEP 5: Preview Changes")
            print("-" * 80)

            print(f"\nMap: {map_name}")
            print("\nImage Changes:")
            print(f"  Dimensions: {original_width_px}x{original_height_px} -> {new_width_px}x{new_height_px} px")
            print(f"  PPM: {original_ppm:.2f} -> {new_ppm:.2f}")
            print(f"  Scaling Mode: {scaling_mode}")

            if scaling_mode != "none" and (scale_x != 1.0 or scale_y != 1.0):
                print(f"\nCoordinate Translation (scale_x={scale_x:.4f}, scale_y={scale_y:.4f}):")

                # Preview device translations
                if devices_on_map:
                    print(f"\n  Devices ({len(devices_on_map)}):")
                    for _, device in enumerate(devices_on_map[:5]):  # Show first 5
                        old_x = device.get("x", 0)
                        old_y = device.get("y", 0)
                        new_x = old_x * scale_x
                        new_y = old_y * scale_y
                        name = device.get("name", device.get("mac", "Unknown"))
                        print(f"    {name}: ({old_x:.1f}, {old_y:.1f}) -> ({new_x:.1f}, {new_y:.1f})")
                    if len(devices_on_map) > 5:
                        print(f"    ... and {len(devices_on_map) - 5} more devices")

                # Preview zone translations
                if zones_on_map:
                    print(f"\n  Zones ({len(zones_on_map)}):")
                    for _, zone in enumerate(zones_on_map[:3]):
                        zone_name = zone.get("name", "Unnamed")
                        vertex_count = len(zone.get("vertices", []))
                        print(f"    {zone_name}: {vertex_count} vertices will be scaled")
                    if len(zones_on_map) > 3:
                        print(f"    ... and {len(zones_on_map) - 3} more zones")

                if wall_nodes > 0 or wayfinding_nodes > 0:
                    print("\n  Geometry:")
                    if wall_nodes > 0:
                        print(f"    {wall_nodes} wall nodes will be scaled")
                    if wayfinding_nodes > 0:
                        print(f"    {wayfinding_nodes} wayfinding nodes will be scaled")
            else:
                print("\n  No coordinate changes required (same dimensions or no scaling selected)")

            # Step 6: Confirm and apply
            print(f"\n{'-' * 80}")
            print("STEP 6: Confirm and Apply")
            print("-" * 80)

            print("\n! WARNING: This will modify the map and update all device/zone positions.")
            print("! A backup has been saved. Review the preview above before proceeding.")

            try:
                confirm = input("\nType 'REPLACE' to proceed: ").strip()
            except EOFError:
                logging.info("EOF detected during confirmation")
                return

            if confirm != "REPLACE":
                print("\n! Operation cancelled")
                return

            logging.info(f"Map replacement confirmed for map {map_id} with scaling_mode={scaling_mode}")

            # Apply changes
            print("\nApplying changes...")
            errors = []

            # 6a. Update map properties (dimensions, PPM)
            print("  Updating map properties...")
            try:
                map_update = {"width": new_width_px, "height": new_height_px, "ppm": new_ppm}

                # Calculate new physical dimensions
                if new_ppm and new_ppm > 0:
                    map_update["width_m"] = new_width_px / new_ppm
                    map_update["height_m"] = new_height_px / new_ppm

                # Scale wall paths if needed
                if scaling_mode == "proportional" and (scale_x != 1.0 or scale_y != 1.0):
                    if current_map.get("wall_path", {}).get("nodes"):
                        scaled_wall_path = {"nodes": []}
                        for node in current_map["wall_path"]["nodes"]:
                            scaled_node = {}
                            for key, value in node.items():
                                if key == "x" and isinstance(value, (int, float)):
                                    scaled_node[key] = value * scale_x
                                elif key == "y" and isinstance(value, (int, float)):
                                    scaled_node[key] = value * scale_y
                                else:
                                    scaled_node[key] = value
                            scaled_wall_path["nodes"].append(scaled_node)
                        map_update["wall_path"] = scaled_wall_path
                        logging.debug(f"Scaled {len(scaled_wall_path['nodes'])} wall nodes")

                    if current_map.get("wayfinding_path", {}).get("nodes"):
                        scaled_wf_path = {"nodes": []}
                        for node in current_map["wayfinding_path"]["nodes"]:
                            scaled_node = {}
                            for key, value in node.items():
                                if key == "x" and isinstance(value, (int, float)):
                                    scaled_node[key] = value * scale_x
                                elif key == "y" and isinstance(value, (int, float)):
                                    scaled_node[key] = value * scale_y
                                else:
                                    scaled_node[key] = value
                            scaled_wf_path["nodes"].append(scaled_node)
                        map_update["wayfinding_path"] = scaled_wf_path
                        logging.debug(f"Scaled {len(scaled_wf_path['nodes'])} wayfinding nodes")

                update_response = mistapi.api.v1.sites.maps.updateSiteMap(
                    self.apisession, site_id=site_id, map_id=map_id, body=map_update
                )

                if update_response.status_code == 200:
                    print("    Map properties updated successfully")
                else:
                    errors.append(f"Map update failed: HTTP {update_response.status_code}")
                    print(f"    ! Failed to update map: HTTP {update_response.status_code}")

            except Exception as map_err:
                errors.append(f"Map update error: {map_err}")
                print(f"    ! Error updating map: {map_err}")

            # 6b. Upload new image
            print("  Uploading new image...")
            try:
                upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(
                    self.apisession, site_id=site_id, map_id=map_id, file=file_path
                )

                if upload_response.status_code in [200, 201]:
                    print("    Image uploaded successfully")
                else:
                    errors.append(f"Image upload failed: HTTP {upload_response.status_code}")
                    print(f"    ! Failed to upload image: HTTP {upload_response.status_code}")

            except Exception as img_err:
                errors.append(f"Image upload error: {img_err}")
                print(f"    ! Error uploading image: {img_err}")

            # 6c. Update device positions
            if devices_on_map and scaling_mode == "proportional" and (scale_x != 1.0 or scale_y != 1.0):
                print(f"  Updating {len(devices_on_map)} device positions...")
                devices_updated = 0
                devices_failed = 0

                for device in devices_on_map:
                    try:
                        device_id = device.get("id")
                        old_x = device.get("x", 0)
                        old_y = device.get("y", 0)
                        new_x = old_x * scale_x
                        new_y = old_y * scale_y

                        device_update = {"x": new_x, "y": new_y}

                        update_dev_response = mistapi.api.v1.sites.devices.updateSiteDevice(
                            self.apisession, site_id=site_id, device_id=device_id, body=device_update
                        )

                        if update_dev_response.status_code == 200:
                            devices_updated += 1
                        else:
                            devices_failed += 1
                            logging.warning(
                                f"Device update failed for {device_id}: HTTP {update_dev_response.status_code}"
                            )

                    except Exception as dev_err:
                        devices_failed += 1
                        logging.error(f"Device update error for {device.get('id')}: {dev_err}")

                print(f"    Devices updated: {devices_updated}, failed: {devices_failed}")
                if devices_failed > 0:
                    errors.append(f"{devices_failed} device updates failed")

            # 6d. Update zone positions
            if zones_on_map and scaling_mode == "proportional" and (scale_x != 1.0 or scale_y != 1.0):
                print(f"  Updating {len(zones_on_map)} zone positions...")
                zones_updated = 0
                zones_failed = 0

                for zone in zones_on_map:
                    try:
                        zone_id = zone.get("id")
                        vertices = zone.get("vertices", [])

                        if vertices:
                            scaled_vertices = []
                            for vertex in vertices:
                                scaled_vertex = {"x": vertex.get("x", 0) * scale_x, "y": vertex.get("y", 0) * scale_y}
                                scaled_vertices.append(scaled_vertex)

                            zone_update = {"vertices": scaled_vertices}

                            update_zone_response = mistapi.api.v1.sites.zones.updateSiteZone(
                                self.apisession, site_id=site_id, zone_id=zone_id, body=zone_update
                            )

                            if update_zone_response.status_code == 200:
                                zones_updated += 1
                            else:
                                zones_failed += 1
                                logging.warning(
                                    f"Zone update failed for {zone_id}: HTTP {update_zone_response.status_code}"
                                )
                        else:
                            zones_updated += 1  # No vertices to update

                    except Exception as zone_err:
                        zones_failed += 1
                        logging.error(f"Zone update error for {zone.get('id')}: {zone_err}")

                print(f"    Zones updated: {zones_updated}, failed: {zones_failed}")
                if zones_failed > 0:
                    errors.append(f"{zones_failed} zone updates failed")

            # 6e. Update beacon positions
            if beacons_on_map and scaling_mode == "proportional" and (scale_x != 1.0 or scale_y != 1.0):
                print(f"  Updating {len(beacons_on_map)} beacon positions...")
                beacons_updated = 0
                beacons_failed = 0

                for beacon in beacons_on_map:
                    try:
                        beacon_id = beacon.get("id")
                        old_x = beacon.get("x", 0)
                        old_y = beacon.get("y", 0)

                        beacon_update = {"x": old_x * scale_x, "y": old_y * scale_y}

                        update_beacon_response = mistapi.api.v1.sites.beacons.updateSiteBeacon(
                            self.apisession, site_id=site_id, beacon_id=beacon_id, body=beacon_update
                        )

                        if update_beacon_response.status_code == 200:
                            beacons_updated += 1
                        else:
                            beacons_failed += 1

                    except Exception as beacon_err:
                        beacons_failed += 1
                        logging.error(f"Beacon update error: {beacon_err}")

                print(f"    Beacons updated: {beacons_updated}, failed: {beacons_failed}")
                if beacons_failed > 0:
                    errors.append(f"{beacons_failed} beacon updates failed")

            # 6f. Update virtual beacon positions
            if vbeacons_on_map and scaling_mode == "proportional" and (scale_x != 1.0 or scale_y != 1.0):
                print(f"  Updating {len(vbeacons_on_map)} virtual beacon positions...")
                vbeacons_updated = 0
                vbeacons_failed = 0

                for vbeacon in vbeacons_on_map:
                    try:
                        vbeacon_id = vbeacon.get("id")
                        old_x = vbeacon.get("x", 0)
                        old_y = vbeacon.get("y", 0)

                        vbeacon_update = {"x": old_x * scale_x, "y": old_y * scale_y}

                        update_vbeacon_response = mistapi.api.v1.sites.vbeacons.updateSiteVBeacon(
                            self.apisession, site_id=site_id, vbeacon_id=vbeacon_id, body=vbeacon_update
                        )

                        if update_vbeacon_response.status_code == 200:
                            vbeacons_updated += 1
                        else:
                            vbeacons_failed += 1

                    except Exception as vbeacon_err:
                        vbeacons_failed += 1
                        logging.error(f"Virtual beacon update error: {vbeacon_err}")

                print(f"    Virtual beacons updated: {vbeacons_updated}, failed: {vbeacons_failed}")
                if vbeacons_failed > 0:
                    errors.append(f"{vbeacons_failed} virtual beacon updates failed")

            # Summary
            print(f"\n{'=' * 80}")
            print("MAP REPLACEMENT COMPLETE")
            print("=" * 80)
            print(f"\nMap: {map_name}")
            print(f"New Dimensions: {new_width_px} x {new_height_px} px")
            print(f"New PPM: {new_ppm:.2f}")
            print(f"Scaling Mode: {scaling_mode}")

            if errors:
                print(f"\n! Completed with {len(errors)} warning(s):")
                for err in errors:
                    print(f"  - {err}")
                print(f"\nBackup file: {backup_file}")
                print("Use the backup to restore if needed.")
            else:
                print("\nAll changes applied successfully!")
                print(f"Backup file: {backup_file}")

            logging.info(
                f"Map replacement wizard completed for {map_id}: scaling_mode={scaling_mode}, errors={len(errors)}"
            )

        except EOFError:
            logging.info("EOF detected in map replacement wizard")
            return
        except ImportError as import_err:
            print(f"\n! Missing required dependency: {import_err}")
            print("Install with: pip install Pillow")
            logging.error(f"Map replacement wizard import error: {import_err}")
            return
        except Exception as e:
            logging.error(f"Error in map replacement wizard: {e}", exc_info=True)
            print(f"\n! Error: {e}")

    def maps_without_images_report(self):
        """Generate report of maps that don't have uploaded images."""
        print("\n" + "-" * 80)
        print("MAPS WITHOUT IMAGES REPORT")
        print("-" * 80)

        try:
            sites = self._fetch_sites()
            if not sites:
                print("\n! No sites found in organization")
                return

            print(f"\nScanning {len(sites)} sites for maps without images...")
            maps_without_images = []
            total_maps_scanned = 0

            for site in tqdm(sites, desc="Scanning sites", unit="site"):
                try:
                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site["id"])

                    if maps_response.status_code == 200:
                        maps = maps_response.data
                        total_maps_scanned += len(maps)
                        for map_item in maps:
                            if "url" not in map_item:
                                maps_without_images.append(
                                    {
                                        "site_id": site["id"],
                                        "site_name": site.get("name", "Unknown"),
                                        "map_id": map_item.get("id"),
                                        "map_name": map_item.get("name", "Unnamed"),
                                        "type": map_item.get("type", "N/A"),
                                        "width": map_item.get("width", 0),
                                        "height": map_item.get("height", 0),
                                        "org_id": self.org_id,
                                    }
                                )
                except Exception as e:
                    logging.debug(f"Error scanning site {site['id']}: {e}")
                    continue

            print(f"\nTotal maps scanned: {total_maps_scanned}")

            if not maps_without_images:
                print("\n" + "-" * 80)
                print(f"All {total_maps_scanned} maps have images uploaded!")
                print("-" * 80)
                return

            # Display report
            print(f"\n{'-' * 80}")
            print(f"MAPS WITHOUT IMAGES: {len(maps_without_images)} found")
            print(f"{'-' * 80}")
            print(f"{'Site Name':<30} {'Map Name':<30} {'Type':<15}")
            print(f"{'-' * 80}")

            for map_item in maps_without_images:
                site_name = map_item["site_name"][:29]
                map_name = map_item["map_name"][:29]
                map_type = map_item["type"][:14]
                print(f"{site_name:<30} {map_name:<30} {map_type:<15}")

            print(f"{'-' * 80}")

            # Export to CSV/SQLite
            filename = "MapsWithoutImages_Report"
            write_data_with_format_selection(maps_without_images, filename, api_function_name="listSiteMaps")

            logging.info(f"Generated report: {len(maps_without_images)} maps without images")

        except Exception as e:
            logging.error(f"Error generating maps report: {e}", exc_info=True)
            print(f"\n! Error generating report: {e}")

    # Placeholder methods for future implementation
    def _collect_property_input(self, prompt, current_value, value_type=str):
        """Collect a single property update from user with type validation."""
        raw = input(f"{prompt} [{current_value}]: ").strip()
        if not raw:
            return None
        if value_type is str:
            return raw
        try:
            return value_type(raw)
        except ValueError:
            print("! Invalid value, skipping")
            return None

    def _collect_map_updates(self, current_map):
        """Collect all map property updates from user input."""
        print("\nEnter new values (press Enter to keep current value):")
        fields = [
            ("name", "Map name", current_map.get("name", ""), str),
            ("width", "Width in pixels", current_map.get("width", ""), int),
            ("height", "Height in pixels", current_map.get("height", ""), int),
            ("ppm", "Pixels per meter", current_map.get("ppm", ""), float),
            ("orientation", "Orientation in degrees", current_map.get("orientation", 0), int),
        ]
        payload = {}
        for key, label, current, vtype in fields:
            value = self._collect_property_input(label, current, vtype)
            if value is not None:
                payload[key] = value
        return payload

    def update_map_properties(self):
        """Update existing map properties (name, dimensions, orientation, etc.)."""
        print("\n" + "-" * 80)
        print("UPDATE MAP PROPERTIES")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            map_id = self._select_map_from_site(site_id, site_name)
            if not map_id:
                return

            map_response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)
            if map_response.status_code != 200:
                print(f"\n! Failed to fetch map details: HTTP {map_response.status_code}")
                return

            current_map = map_response.data

            print("\nCurrent Map Properties:")
            print(f"{'-' * 80}")
            for label, key in [("Name", "name"), ("Type", "type")]:
                print(f"{label}: {current_map.get(key, 'N/A')}")
            print(f"Width: {current_map.get('width', 'N/A')} pixels")
            print(f"Height: {current_map.get('height', 'N/A')} pixels")
            print(f"PPM (Pixels per meter): {current_map.get('ppm', 'N/A')}")
            print(f"Orientation: {current_map.get('orientation', 0)} degrees")
            print(f"{'-' * 80}")

            update_payload = self._collect_map_updates(current_map)
            if not update_payload:
                print("\n! No changes specified")
                return

            print(f"\n{'-' * 80}")
            print("Changes to apply:")
            for key, value in update_payload.items():
                print(f"  {key}: {value}")
            print(f"{'-' * 80}")

            confirm = input("\nApply these changes? (yes/no): ").strip().lower()
            if confirm not in ["yes", "y"]:
                print("\n! Update cancelled")
                return

            print("\nApplying changes...")
            update_response = mistapi.api.v1.sites.maps.updateSiteMap(
                self.apisession, site_id=site_id, map_id=map_id, body=update_payload
            )
            if update_response.status_code in [200, 201]:
                print(f"\n{'-' * 80}")
                print("Map updated successfully!")
                print(f"{'-' * 80}")
                logging.info(f"Updated map {map_id} for site {site_id}")
            else:
                print(f"\n! Failed to update map: HTTP {update_response.status_code}")
                logging.error(f"Map update failed: {update_response.status_code}")

        except EOFError:
            logging.info("EOF detected during map update")
            return
        except Exception as e:
            logging.error(f"Error updating map properties: {e}", exc_info=True)
            print(f"\n! Error updating map: {e}")

    def delete_site_map(self):
        """Delete a site map with confirmation."""
        print("\n" + "-" * 80)
        print("DELETE SITE MAP")
        print("-" * 80)
        print("\n! WARNING: This action cannot be undone!")

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            # Get map selection
            map_id = self._select_map_from_site(site_id, site_name)
            if not map_id:
                return

            # Fetch current map details for display
            map_response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)

            if map_response.status_code != 200:
                print(f"\n! Failed to fetch map details: HTTP {map_response.status_code}")
                return

            current_map = map_response.data

            # Display map details before deletion
            print(f"\n{'-' * 80}")
            print("Map to be deleted:")
            print(f"  Name: {current_map.get('name', 'N/A')}")
            print(f"  Type: {current_map.get('type', 'N/A')}")
            print(f"  ID: {map_id}")
            print(f"{'-' * 80}")

            # Safety confirmation
            print("\nType 'DELETE' in uppercase to confirm deletion:")
            confirmation = input("Confirmation: ").strip()

            if confirmation != "DELETE":
                print("\n! Deletion cancelled")
                logging.info(f"Map deletion cancelled by user for map {map_id}")
                return

            # Perform deletion
            print("\nDeleting map...")
            delete_response = mistapi.api.v1.sites.maps.deleteSiteMap(self.apisession, site_id=site_id, map_id=map_id)

            if delete_response.status_code in [200, 204]:
                print(f"\n{'-' * 80}")
                print("Map deleted successfully!")
                print(f"{'-' * 80}")
                logging.info(f"Deleted map {map_id} from site {site_id}")
            else:
                print(f"\n! Failed to delete map: HTTP {delete_response.status_code}")
                logging.error(f"Map deletion failed: {delete_response.status_code} - {delete_response.data}")

        except EOFError:
            logging.info("EOF detected during map deletion")
            return
        except Exception as e:
            logging.error(f"Error deleting site map: {e}", exc_info=True)
            print(f"\n! Error deleting map: {e}")

    def upload_map_image(self):
        """Upload or replace map image file (multipart upload)."""
        logging.info("upload_map_image operation initiated")
        print("\n" + "-" * 80)
        print("UPLOAD/REPLACE MAP IMAGE")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            logging.warning("upload_map_image aborted: No site selected")
            return

        logging.debug(f"upload_map_image - Site: {site_name} (ID: {site_id})")

        try:
            # Get map selection
            map_id = self._select_map_from_site(site_id, site_name)
            if not map_id:
                return

            # Prompt for image file path
            import os

            print("\nEnter the path to the image file:")
            print("Supported formats: PNG, JPG, JPEG, GIF, SVG")
            file_path = input("File path: ").strip()

            # Remove quotes if user pasted path with quotes
            file_path = file_path.strip('"').strip("'")

            if not file_path:
                print("\n! No file path provided")
                return

            if not os.path.exists(file_path):
                print(f"\n! File not found: {file_path}")
                return

            if not os.path.isfile(file_path):
                print(f"\n! Path is not a file: {file_path}")
                return

            # Validate file extension
            valid_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg"]
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in valid_extensions:
                print(f"\n! Invalid file type: {file_ext}")
                print(f"Supported types: {', '.join(valid_extensions)}")
                return

            # Check file size (warn if > 10MB)
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            if file_size_mb > 10:
                print(f"\n! Warning: File size is {file_size_mb:.2f}MB")
                confirm = input("Continue with upload? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    print("\n! Upload cancelled")
                    return

            print(f"\nFile: {os.path.basename(file_path)}")
            print(f"Size: {file_size_mb:.2f}MB")

            # Confirm upload
            confirm = input("\nUpload this image to the selected map? (yes/no): ").strip().lower()
            if confirm not in ["yes", "y"]:
                print("\n! Upload cancelled")
                return

            # Perform upload using mistapi
            print("\nUploading image...")

            # Use mistapi's addSiteMapImageFile method
            with open(file_path, "rb"):
                upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(
                    self.apisession, site_id=site_id, map_id=map_id, file=file_path
                )

            if upload_response.status_code in [200, 201]:
                print(f"\n{'-' * 80}")
                print("Image uploaded successfully!")
                print(f"{'-' * 80}")
                logging.info(f"Uploaded image to map {map_id} for site {site_id}")
            else:
                print(f"\n! Failed to upload image: HTTP {upload_response.status_code}")
                logging.error(f"Image upload failed: {upload_response.status_code} - {upload_response.data}")

        except EOFError:
            logging.info("EOF detected during image upload")
            return
        except Exception as e:
            logging.error(f"Error uploading map image: {e}", exc_info=True)
            print(f"\n! Error uploading image: {e}")

    def view_devices_on_map(self):
        """Display all devices placed on a specific map."""
        print("\n" + "-" * 80)
        print("VIEW DEVICES ON MAP")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            return

        try:
            # Get map selection
            map_id = self._select_map_from_site(site_id, site_name)
            if not map_id:
                return

            # Fetch devices for the site
            print(f"\nFetching devices for site: {site_name}")
            devices_response = mistapi.api.v1.sites.devices.listSiteDevices(
                self.apisession, site_id=site_id, type="all"
            )

            if devices_response.status_code != 200:
                print(f"\n! Failed to fetch devices: HTTP {devices_response.status_code}")
                return

            all_devices = devices_response.data

            # Filter devices that are on this specific map
            devices_on_map = []
            for device in all_devices:
                if device.get("map_id") == map_id:
                    devices_on_map.append(device)

            if not devices_on_map:
                print("\n! No devices placed on this map")
                return

            # Display devices
            print(f"\n{'-' * 80}")
            print(f"Devices on Map: {len(devices_on_map)} found")
            print(f"{'-' * 80}")
            print(f"{'Device Name':<30} {'Type':<10} {'Model':<20} {'X,Y Coordinates':<20}")
            print(f"{'-' * 80}")

            for device in devices_on_map:
                device_name = device.get("name", "Unnamed")[:29]
                device_type = device.get("type", "N/A")[:9]
                device_model = device.get("model", "N/A")[:19]
                x_coord = device.get("x", "N/A")
                y_coord = device.get("y", "N/A")
                coordinates = f"{x_coord},{y_coord}"
                print(f"{device_name:<30} {device_type:<10} {device_model:<20} {coordinates:<20}")

            print(f"{'-' * 80}")

            # Optional: Export to CSV
            export_choice = input("\nExport to CSV? (yes/no): ").strip().lower()
            if export_choice in ["yes", "y"]:
                devices_data = []
                for device in devices_on_map:
                    flattened = flatten_dict_recursively(device)
                    flattened["site_id"] = site_id
                    flattened["site_name"] = site_name
                    devices_data.append(flattened)

                filename = f"MapDevices_{sanitize_filename(site_name or 'unknown_site')}"
                write_data_with_format_selection(devices_data, filename, api_function_name="listSiteDevices")
                print(f"\n   Exported {len(devices_data)} devices")

            logging.info(f"Viewed {len(devices_on_map)} devices on map {map_id}")

        except EOFError:
            logging.info("EOF detected during view devices")
            return
        except Exception as e:
            logging.error(f"Error viewing devices on map: {e}", exc_info=True)
            print(f"\n! Error viewing devices: {e}")

    def auto_place_aps(self):
        """Automatically place APs on map using Mist auto-placement."""
        print("\n! Feature coming soon: Auto-place APs")
        logging.info("auto_place_aps called (placeholder)")

    def auto_orient_aps(self):
        """Automatically orient APs on map."""
        print("\n! Feature coming soon: Auto-orient APs")
        logging.info("auto_orient_aps called (placeholder)")

    def set_device_location(self):
        """Manually set AP/device coordinates on map."""
        print("\n! Feature coming soon: Set device location")
        logging.info("set_device_location called (placeholder)")

    def bulk_download_org_images(self):
        """Download all map images across entire organization."""
        print("\n" + "-" * 80)
        print("BULK DOWNLOAD ORG MAP IMAGES")
        print("-" * 80)

        try:
            sites = self._fetch_sites()
            if not sites:
                print("\n! No sites found in organization")
                return

            print(f"\nScanning {len(sites)} sites for maps with images...")

            import os

            import requests

            # Create base download directory
            base_dir = os.path.join("data", "map_images_org_backup")
            os.makedirs(base_dir, exist_ok=True)

            total_maps = 0
            total_downloaded = 0

            for site in tqdm(sites, desc="Processing sites", unit="site"):
                try:
                    site_id = site["id"]
                    site_name = site.get("name", "Unknown")

                    maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)

                    if maps_response.status_code != 200:
                        continue

                    maps = maps_response.data
                    maps_with_images = [m for m in maps if "url" in m]

                    if not maps_with_images:
                        continue

                    # Create site-specific directory
                    site_dir = os.path.join(base_dir, sanitize_filename(site_name))
                    os.makedirs(site_dir, exist_ok=True)

                    for map_item in maps_with_images:
                        total_maps += 1
                        try:
                            map_name = map_item.get("name", "unnamed")
                            map_id = map_item.get("id", "unknown")
                            image_url = map_item.get("url")

                            if not image_url:
                                continue

                            # Determine file extension
                            file_ext = ".png"
                            if "." in image_url:
                                url_ext = image_url.rsplit(".", 1)[-1].split("?")[0]
                                if url_ext.lower() in ["png", "jpg", "jpeg", "gif", "svg"]:
                                    file_ext = f".{url_ext.lower()}"

                            filename = f"{sanitize_filename(map_name)}_{map_id[:8]}{file_ext}"
                            filepath = os.path.join(site_dir, filename)

                            # Skip if already downloaded
                            if os.path.exists(filepath):
                                total_downloaded += 1
                                continue

                            response = requests.get(image_url, timeout=30)
                            if response.status_code == 200:
                                with open(filepath, "wb") as f:
                                    f.write(response.content)
                                total_downloaded += 1
                            else:
                                logging.warning(
                                    f"Failed to download {site_name}/{map_name}: HTTP {response.status_code}"
                                )

                        except Exception as e:
                            logging.error(f"Error downloading map image {map_item.get('id')}: {e}")
                            continue

                except Exception as e:
                    logging.debug(f"Error processing site {site['id']}: {e}")
                    continue

            print(f"\n{'-' * 80}")
            print("Download completed!")
            print(f"Total maps found: {total_maps}")
            print(f"Successfully downloaded: {total_downloaded}")
            print(f"Location: {base_dir}")
            print(f"{'-' * 80}")
            logging.info(f"Bulk downloaded {total_downloaded} of {total_maps} map images to {base_dir}")

        except Exception as e:
            logging.error(f"Error bulk downloading map images: {e}", exc_info=True)
            print(f"\n! Error during bulk download: {e}")

    def backup_all_maps(self):
        """Complete backup of all maps (metadata + images)."""
        print("\n! Feature coming soon: Backup all maps")
        logging.info("backup_all_maps called (placeholder)")

    def map_coverage_analytics(self):
        """Analyze RF coverage patterns by map."""
        print("\n! Feature coming soon: Map coverage analytics")
        logging.info("map_coverage_analytics called (placeholder)")

    def device_density_analytics(self):
        """Analyze device density and distribution by map."""
        print("\n! Feature coming soon: Device density analytics")
        logging.info("device_density_analytics called (placeholder)")

    def map_usage_statistics(self):
        """Generate usage statistics for maps."""
        print("\n! Feature coming soon: Map usage statistics")
        logging.info("map_usage_statistics called (placeholder)")

    def interactive_map_viewer(self):
        """Interactive map viewer with Plotly/Dash for viewing and editing.

        Supports:
        - Floor plan image display
        - Toggleable overlays: walls, zones, wayfinding paths
        - Device visualization: APs, switches, gateways with orientation indicators
        - Click-to-edit device locations
        - Save changes back to Mist Cloud
        """
        logging.info("Interactive map viewer initiated")
        print("\n" + "-" * 80)
        print("INTERACTIVE MAP VIEWER")
        print("-" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            logging.warning("Interactive map viewer aborted: No site selected")
            return

        logging.debug(f"Interactive map viewer - Site: {site_name} (ID: {site_id})")

        try:
            # Explicitly check and install required visualization packages
            print("\nChecking visualization dependencies...")
            logging.info("Starting visualization dependency check")
            required_packages = {"plotly": "plotly>=5.14.0", "dash": "dash>=2.9.0"}
            optional_viz_packages = {"kaleido": "kaleido>=0.2.1", "matplotlib": "matplotlib>=3.5.0"}

            # Trigger installation check through global import_manager instance
            # Access the global import_manager variable created at module initialization in MistHelper.py
            # When running standalone, import_manager may not exist - skip dependency checks in that case
            _import_manager = globals().get("import_manager")

            if _import_manager is not None:
                for package_name, package_spec in required_packages.items():
                    logging.debug(f"Checking required package: {package_name} ({package_spec})")
                    _import_manager.import_module_safely(
                        package_name,
                        package_spec=package_spec,
                        required=False,  # Don't fail if can't install
                        skip_deps=False,  # Allow installation
                        skip_upgrade=True,  # Don't check for upgrades
                    )
                    logging.debug(f"Package {package_name} check completed")

                # Optional packages (best-effort)
                for package_name, package_spec in optional_viz_packages.items():
                    try:
                        logging.debug(f"Checking optional package: {package_name} ({package_spec})")
                        _import_manager.import_module_safely(
                            package_name, package_spec=package_spec, required=False, skip_deps=False, skip_upgrade=True
                        )
                        logging.debug(f"Optional package {package_name} installed/verified")
                    except Exception as e:
                        logging.debug(f"Optional package {package_name} unavailable: {e}")
            else:
                logging.debug("import_manager not available (standalone mode) - skipping package installation checks")

            # Now attempt imports
            if not importlib.util.find_spec("plotly"):
                logging.error("plotly not available")
                print("\n! Missing required package: plotly")
                print("! Install with: pip install plotly dash")
                confirm = input("\nWould you like to continue without interactive features? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    logging.info("User declined matplotlib fallback")
                    return
                # Fallback to basic matplotlib if available
                if not importlib.util.find_spec("matplotlib"):
                    logging.error("matplotlib fallback also not available")
                    print("\n! No visualization libraries available")
                    print("! Install plotly: pip install plotly dash")
                    print("! Or matplotlib: pip install matplotlib")
                    return
                print("\n! Using matplotlib fallback (view-only mode)")
                logging.info("Successfully imported matplotlib for fallback mode")
                use_plotly = False
            else:
                logging.info("Successfully imported plotly modules")
                use_plotly = True
                logging.debug("Using Plotly/Dash mode for interactive viewer")

            # Select map to view and get list of all maps for dropdown
            logging.debug(f"Prompting user to select map from site {site_name}")  # nosec B608 — not SQL, just logging
            map_id, all_maps = self._select_map_from_site(site_id, site_name, return_all_maps=True)
            if not map_id:
                logging.info("Map viewer aborted: No map selected")
                return

            logging.debug(f"Selected map_id: {map_id}, Total maps available: {len(all_maps)}")

            # Fetch map details
            print("\nLoading map data...")
            logging.info(f"Fetching map details - site_id: {site_id}, map_id: {map_id}")
            map_response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)

            logging.debug(f"getSiteMap API response: HTTP {map_response.status_code}")
            if map_response.status_code != 200:
                logging.error(
                    f"Failed to fetch map details - HTTP {map_response.status_code}, "
                    f"Response: {map_response.data if hasattr(map_response, 'data') else 'No data'}"
                )
                print(f"\n! Failed to fetch map: HTTP {map_response.status_code}")
                return

            map_data = map_response.data
            map_name = map_data.get("name", "Unnamed")
            map_width = map_data.get("width", 1000)
            map_height = map_data.get("height", 1000)
            map_ppm = map_data.get("ppm", 0)

            logging.info(f"Map loaded: {map_name} (ID: {map_id})")
            logging.debug(
                f"Map dimensions: {map_width}x{map_height}px, PPM: {map_ppm}, "
                f"Orientation: {map_data.get('orientation', 0)}"
            )
            logging.debug(
                f"Map has image: {'url' in map_data}, Has walls: {'wall_path' in map_data}, "
                f"Has wayfinding: {'wayfinding_path' in map_data}"
            )

            print(f"\nMap: {map_name}")
            print(f"Dimensions: {map_width}x{map_height} pixels")

            # Check if map has been scaled - PPM of 0 or very low indicates unscaled map
            if not map_ppm or map_ppm == 0:
                logging.warning(
                    f"MAP NOT SCALED: Map '{map_name}' has PPM=0 - image has not been scaled in Mist Portal"
                )
                print("\n" + "!" * 60)
                print("! WARNING: This map image has NOT been scaled!")
                print("! RF coverage heatmap and location features will not work correctly.")
                print("! Please scale this map in Mist Portal: Location > Set Scale")
                print("!" * 60 + "\n")

            # Fetch devices on this map (use stats API for status information)
            print("Loading devices...")
            logging.info(f"Fetching device stats for site {site_id} (type=all)")
            devices_response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                self.apisession, site_id=site_id, limit=1000
            )

            logging.debug(f"listSiteDevicesStats API response: HTTP {devices_response.status_code}")
            if devices_response.status_code != 200:
                logging.error(f"Failed to fetch devices - HTTP {devices_response.status_code}")
                print(f"\n! Failed to fetch devices: HTTP {devices_response.status_code}")
                devices_on_map = []
            else:
                all_devices = devices_response.data
                logging.debug(f"Total devices at site: {len(all_devices)}")
                devices_on_map = [d for d in all_devices if d.get("map_id") == map_id]
                logging.info(f"Devices on selected map: {len(devices_on_map)}")

                # Log device type breakdown
                device_type_counts = {}
                for device in devices_on_map:
                    device_type = device.get("type", "unknown")
                    device_type_counts[device_type] = device_type_counts.get(device_type, 0) + 1
                logging.debug(f"Device breakdown on map: {device_type_counts}")

            print(f"Devices on map: {len(devices_on_map)}")

            # Fetch zones for this site
            logging.info(f"Fetching zones for site {site_id}")
            try:
                zones_response = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)

                if zones_response.status_code == 200:
                    all_zones = zones_response.data
                    # Filter zones that are on this specific map
                    zones_on_map = [z for z in all_zones if z.get("map_id") == map_id]
                    logging.info(f"Total zones at site: {len(all_zones)}, Zones on this map: {len(zones_on_map)}")
                    logging.debug(f"Zones on map: {zones_on_map}")
                else:
                    logging.warning(f"Failed to fetch zones - HTTP {zones_response.status_code}")
                    zones_on_map = []
            except Exception as zone_error:
                logging.error(f"Error fetching zones: {zone_error}", exc_info=True)
                zones_on_map = []

            print(f"Zones on map: {len(zones_on_map)}")

            # Fetch connected clients for the site to display on map
            clients_on_map = []
            try:
                logging.info(f"Fetching connected wireless client stats for site {site_id}")
                # Use stats API which includes location data (x, y, map_id)
                clients_response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
                    self.apisession, site_id=site_id, limit=1000
                )

                if clients_response.status_code == 200:
                    # Use get_all to handle pagination
                    all_clients = mistapi.get_all(response=clients_response, mist_session=self.apisession)
                    logging.info(f"Total wireless clients retrieved: {len(all_clients)}")

                    # Log all unique map_ids to see what we have
                    client_map_ids = set(c.get("map_id") for c in all_clients if c.get("map_id"))
                    logging.info(f"Client map_ids found: {client_map_ids}")
                    logging.info(f"Looking for map_id: {map_id}")

                    # Filter clients that have map location data matching this map
                    clients_on_map = [
                        c
                        for c in all_clients
                        if c.get("map_id") == map_id and c.get("x") is not None and c.get("y") is not None
                    ]
                    logging.info(f"Clients on this map (after filtering): {len(clients_on_map)}")

                    if clients_on_map:
                        logging.info(f"Sample client data: {clients_on_map[0]}")
                    elif all_clients:
                        logging.warning(
                            f"No clients matched map_id {map_id}. "
                            f"Sample of all clients: {all_clients[0] if all_clients else 'none'}"
                        )
                else:
                    logging.warning(f"Failed to fetch client stats - HTTP {clients_response.status_code}")
            except Exception as client_error:
                logging.error(f"Error fetching client stats: {client_error}", exc_info=True)

            print(f"Connected clients on map: {len(clients_on_map)}")

            # Fetch RF coverage data from Mist API
            coverage_data = None
            try:
                logging.info(f"Fetching RF coverage data for map {map_id}")
                coverage_url = f"/api/v1/sites/{site_id}/location/coverage"
                coverage_params = {
                    "resolution": "fine",
                    "duration": "1d",
                    "map_id": map_id,
                    "type": "client",
                    "from_apollo": "true",  # Undocumented: forces Apollo backend instead of PostgreSQL
                }

                coverage_response = self.apisession.mist_get(coverage_url, query=coverage_params)

                if coverage_response.status_code == 200:
                    coverage_data = coverage_response.data

                    # Check for error response structure
                    if isinstance(coverage_data, dict) and "exception" in coverage_data:
                        exception_str = str(coverage_data.get("exception", ""))

                        if "psycopg2" in exception_str or "database" in exception_str.lower():
                            logging.warning(
                                "RF Coverage temporarily unavailable: Mist backend database connectivity issue"
                            )
                            logging.debug(f"Coverage API backend error: {exception_str}")
                        else:
                            logging.error(
                                f"Coverage API returned error response (first 500 chars): {exception_str[:500]}"
                            )
                            logging.debug(f"Coverage API full error response: {exception_str}")
                            logging.debug(
                                f"Error details - Query: {coverage_data.get('query')}, URI: {coverage_data.get('uri')}"
                            )

                        coverage_data = None
                        print("  Note: RF Coverage heatmap unavailable (Mist backend issue) - continuing without it")
                    else:
                        result_count = len(coverage_data.get("results", [])) if coverage_data else 0
                        logging.info(f"RF coverage data retrieved: {result_count} grid points")
                else:
                    logging.warning(f"Failed to fetch RF coverage data - HTTP {coverage_response.status_code}")
                    coverage_data = None
            except Exception as coverage_error:
                logging.error(f"Error fetching RF coverage data: {coverage_error}", exc_info=True)
                coverage_data = None

            # Fetch all sites for site selector dropdown in the viewer
            print("Loading organization sites...")
            all_sites = self._fetch_sites()
            logging.info(f"Fetched {len(all_sites)} sites for site selector dropdown")

            if use_plotly:
                logging.info(f"Launching Plotly/Dash viewer for map {map_name}")
                self._launch_plotly_viewer(
                    map_data,
                    devices_on_map,
                    zones_on_map,
                    clients_on_map,
                    site_id,
                    site_name,
                    map_id,
                    coverage_data,
                    all_maps,
                    all_sites,
                )
            else:
                logging.info(f"Launching matplotlib fallback viewer for map {map_name}")
                self._launch_matplotlib_viewer(map_data, devices_on_map)

        except EOFError:
            logging.info("EOF detected during interactive map viewer")
            return
        except Exception as e:
            logging.error(f"Error in interactive map viewer: {e}", exc_info=True)
            print(f"\n! Error launching map viewer: {e}")

    def _launch_plotly_viewer(
        self,
        map_data,
        devices,
        zones,
        clients,
        site_id,
        site_name,
        map_id,
        coverage_data=None,
        all_maps=None,
        all_sites=None,
    ):
        """Launch interactive Plotly/Dash map viewer with edit capabilities, client display, and RF coverage heatmap."""
        coverage_count = len(coverage_data.get("results", [])) if coverage_data else 0
        all_maps = all_maps or []
        all_sites = all_sites or []
        logging.info(
            f"_launch_plotly_viewer called - site: {site_name} ({site_id}), "
            f"map_id: {map_id}, devices: {len(devices)}, zones: {len(zones)}, "
            f"clients: {len(clients)}, coverage: {coverage_count}, "
            f"available_maps: {len(all_maps)}, available_sites: {len(all_sites)}"
        )
        import os
        import webbrowser
        from math import cos, pi, radians, sin

        import plotly.graph_objects as go

        try:
            logging.debug("Importing Dash modules for interactive viewer")
            import dash
            from dash import Dash, Input, Output, State, dcc, html, no_update

            logging.info(f"Dash version: {dash.__version__}")
        except ImportError as e:
            logging.error(f"Failed to import Dash, falling back to static view: {e}", exc_info=True)
            print("\n! Dash not available - using static Plotly view only")
            print("! Install with: pip install dash")
            self._create_static_plotly_map(map_data, devices)
            return

        print("\n" + "-" * 80)
        print("LAUNCHING INTERACTIVE MAP VIEWER")
        print("-" * 80)
        print("! Opening web browser with interactive map...")
        print("! Features:")
        print("!   - Toggle layers (walls, zones, wayfinding, devices, clients)")
        print("!   - Live data refresh (clients update every 30s, RF every 5min)")
        print("!   - Ruler tool - Draw lines to measure distances")
        print("!   - Connected client visualization (green dots)")
        print("!   - Click devices/clients to see details")
        print("!   - Drag devices to new positions (future: save to cloud)")
        print("!   - Pan and zoom")
        print("! Press Ctrl+C in terminal to stop server")
        print("-" * 80)

        # Create Dash app with dark theme
        # update_title="" prevents "Updating..." flash in browser tab during callbacks
        # suppress_callback_exceptions=True is required for allow_duplicate=True on callback outputs
        logging.debug("Creating Dash application instance")
        app = Dash(__name__, update_title="", title="MistHelper Map Viewer", suppress_callback_exceptions=True)

        # Inject custom CSS for dark mode and responsive design
        app.index_string = """
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                            Roboto, "Helvetica Neue", Arial, sans-serif;
                        background-color: #1a1a1a;
                        color: #e0e0e0;
                    }
                    #react-entry-point {
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                    }
                    .main-container {
                        flex: 1;
                        display: flex;
                        overflow: hidden;
                    }
                    .map-container {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        padding: 15px;
                        overflow: hidden;
                    }
                    .sidebar {
                        width: 280px;
                        background-color: #2d2d2d;
                        padding: 20px;
                        overflow-y: auto;
                        border-left: 1px solid #444;
                        box-shadow: -2px 0 10px rgba(0,0,0,0.3);
                    }
                    h1 {
                        margin: 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-size: 24px;
                        font-weight: 600;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    }
                    h3 {
                        color: #a0a0ff;
                        font-size: 16px;
                        margin-top: 0;
                        margin-bottom: 15px;
                        border-bottom: 2px solid #444;
                        padding-bottom: 8px;
                    }
                    .sidebar p {
                        margin: 8px 0;
                        color: #b0b0b0;
                        font-size: 14px;
                    }
                    .sidebar hr {
                        border: none;
                        border-top: 1px solid #444;
                        margin: 20px 0;
                    }
                    /* Custom checkbox styling */
                    .sidebar label {
                        color: #d0d0d0 !important;
                        cursor: pointer;
                        transition: color 0.2s;
                    }
                    .sidebar label:hover {
                        color: #ffffff !important;
                    }
                    /* Graph container */
                    #map-display {
                        height: 100% !important;
                        width: 100% !important;
                    }
                    .js-plotly-plot {
                        height: 100% !important;
                    }
                    /* Info badges */
                    .info-badge {
                        display: inline-block;
                        padding: 4px 12px;
                        background-color: #3d3d3d;
                        border-radius: 12px;
                        margin: 4px 0;
                        font-size: 13px;
                        color: #a0a0ff;
                    }
                    .device-detail {
                        background-color: #3d3d3d;
                        padding: 12px;
                        border-radius: 8px;
                        margin: 8px 0;
                        border-left: 3px solid #667eea;
                    }
                    .device-detail strong {
                        color: #a0a0ff;
                    }
                    /* Dark theme dropdown styling */
                    .dark-dropdown .Select-control {
                        background-color: #3d3d3d !important;
                        border-color: #555 !important;
                    }
                    .dark-dropdown .Select-menu-outer {
                        background-color: #3d3d3d !important;
                        border-color: #555 !important;
                    }
                    .dark-dropdown .Select-option {
                        background-color: #3d3d3d !important;
                        color: #e0e0e0 !important;
                    }
                    .dark-dropdown .Select-option:hover,
                    .dark-dropdown .Select-option.is-focused {
                        background-color: #505050 !important;
                        color: #ffffff !important;
                    }
                    .dark-dropdown .Select-value-label,
                    .dark-dropdown .Select-placeholder {
                        color: #e0e0e0 !important;
                    }
                    .dark-dropdown .Select-arrow {
                        border-color: #888 transparent transparent !important;
                    }
                    /* NOTE: CSS text-shadow doesn't work on Plotly SVG text elements.
                       Text labels use annotations with bgcolor/bordercolor instead. */
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        """

        # Build figure
        logging.debug("Building Plotly figure")
        fig = go.Figure()

        # Set map dimensions and get PPM for unit conversions
        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)
        ppm = map_data.get("ppm", 10)  # pixels per meter, default to 10 if not set
        logging.debug(f"Map canvas dimensions: {map_width}x{map_height}, PPM from map: {ppm}")

        # Validate PPM using client data if available
        # Clients have both pixel coords (x, y) and meter coords (x_m, y_m) - we can verify PPM
        if clients and len(clients) > 0:
            ppm_samples = []
            for client in clients[:10]:  # Check first 10 clients
                x_px = client.get("x")
                x_m = client.get("x_m")
                y_px = client.get("y")
                y_m = client.get("y_m")
                if x_px and x_m and x_m > 0:
                    ppm_samples.append(x_px / x_m)
                if y_px and y_m and y_m > 0:
                    ppm_samples.append(y_px / y_m)

            if ppm_samples:
                calculated_ppm = sum(ppm_samples) / len(ppm_samples)
                ppm_ratio = calculated_ppm / ppm if ppm > 0 else 0

                if abs(ppm_ratio - 1.0) > 0.1:  # More than 10% difference
                    logging.warning(
                        f"PPM MISMATCH DETECTED! Map PPM={ppm}, "
                        f"Calculated from clients={calculated_ppm:.1f} (ratio: {ppm_ratio:.2f}x)"
                    )
                    logging.warning("Map may not be scaled correctly. Using calculated PPM for coverage heatmap.")
                    ppm = calculated_ppm
                else:
                    logging.debug(f"PPM validation passed: map={ppm}, calculated={calculated_ppm:.1f}")

        # Add map image if available
        # Note: Plotly uses bottom-left origin, but we keep Mist's coordinate system (top-left origin)
        # by inverting the Y-axis in the layout
        if "url" in map_data:
            logging.debug(f"Adding map background image: {map_data.get('url')[:100]}...")
            fig.add_layout_image(
                source=map_data["url"],
                x=0,
                y=0,
                sizex=map_width,
                sizey=map_height,
                xref="x",
                yref="y",
                sizing="stretch",
                layer="below",
            )
        else:
            logging.warning("Map has no background image URL")

        # Add walls if present
        if "wall_path" in map_data and map_data["wall_path"]:
            wall_path = map_data["wall_path"]
            logging.debug(f"Wall path data structure: {wall_path}")

            if "nodes" in wall_path:
                logging.info(f"Processing {len(wall_path['nodes'])} wall path nodes")

                # Wall paths are SEGMENTS, not a continuous line
                # Each node has 'edges' that define which other nodes it connects to
                # We need to draw individual line segments based on edges

                # First, build a lookup of nodes by name
                node_lookup = {}
                for node in wall_path["nodes"]:
                    node_name = node.get("name", "")
                    pos = node.get("position", {})
                    if node_name and pos:
                        node_lookup[node_name] = pos
                        logging.debug(
                            f"Wall node '{node_name}': x={pos.get('x')}, "
                            f"y={pos.get('y')}, edges={node.get('edges', {})}"
                        )

                # Now draw segments based on edges
                for node in wall_path["nodes"]:
                    node_name = node.get("name", "")
                    node_pos = node.get("position", {})
                    edges = node.get("edges", {})

                    if not node_pos or not edges:
                        continue

                    # Draw a line from this node to each connected node
                    for edge_name in edges.keys():
                        if edge_name in node_lookup:
                            target_pos = node_lookup[edge_name]

                            # Draw segment
                            fig.add_trace(
                                go.Scatter(
                                    x=[node_pos.get("x", 0), target_pos.get("x", 0)],
                                    y=[node_pos.get("y", 0), target_pos.get("y", 0)],
                                    mode="lines",
                                    name="Walls",
                                    line=dict(color="#ff3333", width=4),
                                    visible=True,
                                    showlegend=False,
                                    hoverinfo="skip",
                                )
                            )

                # Add one invisible trace just for the legend
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="lines",
                        name="Walls",
                        line=dict(color="#ff3333", width=4),
                        visible=True,
                        showlegend=True,
                    )
                )

        # Add wayfinding paths if present
        if "wayfinding_path" in map_data and map_data["wayfinding_path"]:
            wf_path = map_data["wayfinding_path"]
            logging.debug(f"Wayfinding path data structure: {wf_path}")

            if "nodes" in wf_path:
                logging.info(f"Processing {len(wf_path['nodes'])} wayfinding path nodes")

                # Wayfinding paths also use edge-based segments like walls
                # Build node lookup
                node_lookup = {}
                for node in wf_path["nodes"]:
                    node_name = node.get("name", "")
                    pos = node.get("position", {})
                    if node_name and pos:
                        node_lookup[node_name] = pos
                        logging.debug(
                            f"Wayfinding node '{node_name}': x={pos.get('x')}, "
                            f"y={pos.get('y')}, edges={node.get('edges', {})}"
                        )

                # Draw segments based on edges
                for node in wf_path["nodes"]:
                    node_name = node.get("name", "")
                    node_pos = node.get("position", {})
                    edges = node.get("edges", {})

                    if not node_pos or not edges:
                        continue

                    # Draw a line from this node to each connected node
                    for edge_name in edges.keys():
                        if edge_name in node_lookup:
                            target_pos = node_lookup[edge_name]

                            # Draw segment
                            fig.add_trace(
                                go.Scatter(
                                    x=[node_pos.get("x", 0), target_pos.get("x", 0)],
                                    y=[node_pos.get("y", 0), target_pos.get("y", 0)],
                                    mode="lines+markers",
                                    name="Wayfinding",
                                    line=dict(color="#4488ff", width=3, dash="dash"),
                                    marker=dict(size=8, color="#4488ff"),
                                    visible=True,
                                    showlegend=False,
                                    hoverinfo="skip",
                                )
                            )

                # Add one invisible trace just for the legend
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="lines+markers",
                        name="Wayfinding",
                        line=dict(color="#4488ff", width=3, dash="dash"),
                        marker=dict(size=8, color="#4488ff"),
                        visible=True,
                        showlegend=True,
                    )
                )

        # Add zones if present
        if zones and len(zones) > 0:
            logging.info(f"Processing {len(zones)} zones on this map")
            zone_colors = [
                "rgba(255,165,0,0.2)",
                "rgba(0,255,255,0.2)",
                "rgba(255,0,255,0.2)",
                "rgba(255,255,0,0.2)",
                "rgba(0,255,0,0.2)",
                "rgba(128,0,255,0.2)",
            ]

            for idx, zone in enumerate(zones):
                zone_name = zone.get("name", f"Zone {idx + 1}")
                vertices = zone.get("vertices", [])

                logging.debug(f"Zone '{zone_name}': {len(vertices)} vertices - {vertices}")

                if vertices and len(vertices) >= 3:
                    # Extract x,y coordinates from vertices
                    zone_x = [v.get("x", 0) for v in vertices]
                    zone_y = [v.get("y", 0) for v in vertices]
                    # Close the polygon
                    zone_x.append(zone_x[0])
                    zone_y.append(zone_y[0])

                    color = zone_colors[idx % len(zone_colors)]
                    border_color = color.replace("0.2", "0.8")  # More opaque border

                    logging.debug(f"Drawing zone '{zone_name}' with {len(zone_x)} points")

                    fig.add_trace(
                        go.Scatter(
                            x=zone_x,
                            y=zone_y,
                            mode="lines",
                            name=f"Zone: {zone_name}",
                            line=dict(color=border_color, width=2, dash="dot"),
                            fill="toself",
                            fillcolor=color,
                            opacity=1.0,  # Don't apply additional opacity - it's in the color
                            visible=True,
                            showlegend=True,
                            hovertext=f"Zone: {zone_name}",
                            hoverinfo="text",
                        )
                    )

                    # Add zone name label at upper-left corner
                    min_x = min(zone_x)
                    min_y = min(zone_y)
                    fig.add_annotation(
                        x=min_x + 10,  # Small offset from corner
                        y=min_y + 10,
                        text=f"<b>{zone_name}</b>",
                        showarrow=False,
                        font=dict(size=14, color="white", family="Arial Black"),
                        bgcolor=border_color.replace("0.8", "0.9"),
                        bordercolor="white",
                        borderwidth=2,
                        borderpad=4,
                        xanchor="left",
                        yanchor="top",
                        name="Zone Label",  # For toggle control
                    )
                else:
                    logging.warning(f"Zone '{zone_name}' has insufficient vertices: {len(vertices)}")
        else:
            logging.info("No zones found on this map")

        # Add validation paths (site survey paths) if present
        if "sitesurvey_path" in map_data and map_data["sitesurvey_path"]:
            sitesurvey_paths = map_data["sitesurvey_path"]
            logging.info(f"Processing {len(sitesurvey_paths)} validation paths")

            for path_idx, path in enumerate(sitesurvey_paths):
                path_name = path.get("name", f"Path {path_idx + 1}")
                path_coords = path.get("coordinate", [])

                if path_coords and len(path_coords) >= 2:
                    # Extract coordinates
                    path_x = [coord.get("x", 0) for coord in path_coords]
                    path_y = [coord.get("y", 0) for coord in path_coords]

                    # Draw validation path as connected line with markers
                    fig.add_trace(
                        go.Scatter(
                            x=path_x,
                            y=path_y,
                            mode="lines+markers",
                            name=f"Validation: {path_name}",
                            line=dict(color="#ff00ff", width=3, dash="dot"),
                            marker=dict(size=10, color="#ff00ff", symbol="diamond", line=dict(color="white", width=2)),
                            visible=True,
                            showlegend=True,
                            hovertext=f"Validation Path: {path_name}<br>{len(path_coords)} points",
                            hoverinfo="text",
                        )
                    )

                    # Add path name label at start point
                    fig.add_annotation(
                        x=path_x[0],
                        y=path_y[0] - 20,
                        text=f"<b>{path_name}</b>",
                        showarrow=False,
                        font=dict(size=11, color="white", family="Arial Black"),
                        bgcolor="rgba(255,0,255,0.9)",
                        bordercolor="white",
                        borderwidth=2,
                        borderpad=3,
                        xanchor="center",
                        yanchor="bottom",
                    )

                    logging.debug(f"Added validation path '{path_name}' with {len(path_coords)} points")
                else:
                    logging.warning(f"Validation path '{path_name}' has insufficient coordinates: {len(path_coords)}")
        else:
            logging.info("No validation paths found on this map")

        # Add connected clients if present
        if clients and len(clients) > 0:
            logging.info(f"Processing {len(clients)} connected clients on this map")
            logging.debug(f"Client sample data: {clients[0] if clients else 'None'}")
            client_x = []
            client_y = []
            client_hover = []
            client_names = []

            for client in clients:
                x = client.get("x")
                y = client.get("y")
                client_mac = client.get("mac", "unknown")
                client_map_id = client.get("map_id", "none")
                logging.debug(
                    f"Client {client_mac}: x={x}, y={y}, map_id={client_map_id} (looking for map_id={map_id})"
                )
                if x is not None and y is not None:
                    client_x.append(x)
                    client_y.append(y)

                    # Use hostname or MAC for label
                    hostname = client.get("hostname", "")
                    label = hostname if hostname else client_mac[-8:]
                    client_names.append(label)

                    # Build hover text with client details
                    hover = "<b>Client</b><br>"
                    hover += f"MAC: {client.get('mac', 'N/A')}<br>"
                    hover += f"Hostname: {client.get('hostname', 'N/A')}<br>"
                    hover += f"SSID: {client.get('ssid', 'N/A')}<br>"
                    hover += f"AP: {client.get('ap_name', 'N/A')}<br>"
                    hover += f"Band: {client.get('band', 'N/A')}<br>"
                    hover += f"Signal: {client.get('rssi', 'N/A')} dBm<br>"
                    hover += f"Position: ({x}, {y})"
                    client_hover.append(hover)

            if client_x:
                # Add client markers
                fig.add_trace(
                    go.Scatter(
                        x=client_x,
                        y=client_y,
                        mode="markers",
                        name="Clients",
                        marker=dict(
                            symbol="circle",
                            size=12,
                            color="#00ff00",  # Bright green
                            line=dict(color="white", width=2),
                            opacity=0.9,
                        ),
                        hovertext=client_hover,
                        hoverinfo="text",
                        visible=True,
                        showlegend=True,
                    )
                )

                # Add client name labels with shadow effect using annotations
                for _, (x, y, name) in enumerate(zip(client_x, client_y, client_names, strict=True)):
                    fig.add_annotation(
                        x=x,
                        y=y - 10,  # Position above marker
                        text=f"<b>{name}</b>",
                        showarrow=False,
                        font=dict(size=9, color="white", family="Arial"),
                        bgcolor="rgba(0,128,0,0.9)",
                        bordercolor="white",
                        borderwidth=1,
                        borderpad=2,
                        xanchor="center",
                        yanchor="bottom",
                        name="Clients Label",  # For toggle control
                    )
                logging.info(
                    f"Added {len(client_x)} clients to map visualization (out of {len(clients)} total clients)"
                )
            else:
                logging.warning(f"Found {len(clients)} clients but none have x,y coordinates")
        else:
            logging.info("No connected clients found on this map")

        # Add devices by type with LARGER, more visible markers
        device_types = {"ap": [], "switch": [], "gateway": []}
        for device in devices:
            device_type = device.get("type", "unknown")
            if device_type in device_types and "x" in device and "y" in device:
                device_types[device_type].append(device)

        # Enhanced colors and symbols for device types - with status-based coloring
        # Status colors: connected (green), disconnected (red), upgrading (orange/amber)
        type_config = {
            "ap": {
                "symbol": "triangle-up",
                "name": "Access Points",
                "size": 20,
                "colors": {
                    "connected": "#00ff00",  # Bright green
                    "disconnected": "#ff0000",  # Bright red
                    "upgrading": "#ff8800",  # Orange/amber
                },
            },
            "switch": {
                "symbol": "square",
                "name": "Switches",
                "size": 18,
                "colors": {
                    "connected": "#00ccff",  # Cyan
                    "disconnected": "#ff0000",  # Bright red
                    "upgrading": "#ff8800",  # Orange/amber
                },
            },
            "gateway": {
                "symbol": "diamond",
                "name": "Gateways",
                "size": 20,
                "colors": {
                    "connected": "#ff00ff",  # Magenta
                    "disconnected": "#ff0000",  # Bright red
                    "upgrading": "#ff8800",  # Orange/amber
                },
            },
        }

        for device_type, type_cfg in type_config.items():
            type_devices = device_types[device_type]
            if type_devices:
                x_coords = [d["x"] for d in type_devices]
                y_coords = [d["y"] for d in type_devices]  # Keep Mist Y-coordinates as-is
                names = [d.get("name", d.get("mac", "Unknown")) for d in type_devices]
                orientations = [d.get("orientation", 0) for d in type_devices]

                # Debug log device orientations
                for device in type_devices:
                    device_name = device.get("name", "Unnamed")
                    device_orientation = device.get("orientation", 0)
                    logging.debug(f"Device '{device_name}': orientation={device_orientation}")

                # Determine status and color for each device
                colors = []
                statuses = []
                for device in type_devices:
                    # Check device status
                    # Status can be: 'connected', 'disconnected', or check for upgrade in progress
                    status = device.get("status", "disconnected")

                    # Check if upgrading (upgrade_status field or checking for active upgrade)
                    if device.get("upgrade_status") or device.get("fwupdate", {}).get("progress") is not None:
                        device_status = "upgrading"
                    elif status == "connected":
                        device_status = "connected"
                    else:
                        device_status = "disconnected"

                    statuses.append(device_status)
                    colors.append(type_cfg["colors"][device_status])

                hover_text = []
                for device, device_status in zip(type_devices, statuses, strict=True):
                    text = f"<b>{device.get('name', 'Unnamed')}</b><br>"
                    text += f"Type: {device.get('type', 'N/A')}<br>"
                    text += f"Model: {device.get('model', 'N/A')}<br>"
                    text += f"MAC: {device.get('mac', 'N/A')}<br>"
                    text += f"Status: <b>{device_status.upper()}</b><br>"
                    if device_status == "upgrading":
                        progress = device.get("fwupdate", {}).get("progress", "N/A")
                        text += f"Upgrade Progress: {progress}%<br>" if progress != "N/A" else ""
                    text += f"Position: ({device.get('x', 'N/A')}, {device.get('y', 'N/A')})<br>"
                    text += f"Orientation: {device.get('orientation', 0)}deg"
                    hover_text.append(text)

                # Add device markers with status-based colors
                fig.add_trace(
                    go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        mode="markers",
                        name=type_cfg["name"],
                        marker=dict(
                            symbol=type_cfg["symbol"],
                            size=type_cfg["size"],
                            color=colors,  # Status-based color array
                            line=dict(color="white", width=2),
                            opacity=0.9,
                        ),
                        hovertext=hover_text,
                        hoverinfo="text",
                        visible=True,
                        showlegend=True,
                    )
                )

                # Add device name labels with shadow effect using annotations
                for _, (x, y, name, device_color) in enumerate(zip(x_coords, y_coords, names, colors, strict=True)):
                    fig.add_annotation(
                        x=x,
                        y=y - 15,  # Position above marker
                        text=f"<b>{name}</b>",
                        showarrow=False,
                        font=dict(size=11, color="white", family="Arial Black"),
                        bgcolor="rgba(0,0,0,0.85)",
                        bordercolor=device_color,  # Match device status color
                        borderwidth=2,
                        borderpad=3,
                        xanchor="center",
                        yanchor="bottom",
                        name=f"{type_cfg['name']} Label",  # For toggle control
                    )

                # Add mesh links for APs if mesh topology exists
                if device_type == "ap":
                    mesh_links_added = 0
                    for _, device in enumerate(type_devices):
                        # Check if this AP has mesh info
                        mesh_uplink = device.get("mesh_uplink")
                        if mesh_uplink:
                            # Find the uplink AP
                            for uplink_device in type_devices:
                                if uplink_device.get("mac") == mesh_uplink:
                                    # Draw mesh link
                                    fig.add_trace(
                                        go.Scatter(
                                            x=[device["x"], uplink_device["x"]],
                                            y=[device["y"], uplink_device["y"]],
                                            mode="lines",
                                            line=dict(color="rgba(255,0,255,0.4)", width=2, dash="dash"),
                                            name="Mesh Link",
                                            showlegend=(mesh_links_added == 0),  # Only show in legend once
                                            hoverinfo="skip",
                                        )
                                    )
                                    mesh_links_added += 1
                                    break
                    if mesh_links_added > 0:
                        logging.info(f"Added {mesh_links_added} mesh links between APs")

                # Add Mist-style orientation indicators: crosshair + directional dot
                # Use status-based colors for crosshair and orientation dot
                for _, (x, y, angle, _device, device_color, _device_status) in enumerate(
                    zip(x_coords, y_coords, orientations, type_devices, colors, statuses, strict=True)
                ):
                    # Crosshair at device location (always visible) - LARGER SIZE with status color
                    crosshair_size = 40  # Increased from 25 to 40

                    # Horizontal line
                    fig.add_trace(
                        go.Scatter(
                            x=[x - crosshair_size, x + crosshair_size],
                            y=[y, y],
                            mode="lines",
                            line=dict(color=device_color, width=3),  # Status-based color
                            name=f"{type_cfg['name']} Orientation",  # Name for toggle control
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

                    # Vertical line
                    fig.add_trace(
                        go.Scatter(
                            x=[x, x],
                            y=[y - crosshair_size, y + crosshair_size],
                            mode="lines",
                            line=dict(color=device_color, width=3),  # Status-based color
                            name=f"{type_cfg['name']} Orientation",  # Name for toggle control
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

                    # Directional dot showing orientation (always visible for clarity)
                    dot_distance = 50  # Increased from 35 to 50

                    # Convert Mist orientation to standard cartesian coordinates:
                    # - Mist: 0 deg = up (north), 90 deg = right (east), 180 deg = down, 270 deg = left
                    # - Math: 0 deg = right (east), 90 deg = up (north), counter-clockwise
                    # - Y-axis: Mist uses top-left origin with Y increasing downward
                    # Conversion: math_angle = 90 deg - mist_angle, then flip Y component
                    math_angle = 90 - angle
                    dot_x = x + dot_distance * cos(radians(math_angle))
                    dot_y = y - dot_distance * sin(radians(math_angle))  # Subtract because Y increases downward

                    fig.add_trace(
                        go.Scatter(
                            x=[dot_x],
                            y=[dot_y],
                            mode="markers",
                            marker=dict(
                                size=16,  # Increased from 10 to 16
                                color=device_color,  # Status-based color
                                line=dict(color="white", width=2),
                            ),
                            name=f"{type_cfg['name']} Orientation",  # Name for toggle control
                            showlegend=False,
                            hovertext=f"Orientation: {angle} deg",
                            hoverinfo="text",
                        )
                    )

        # Add beacons (vBeacons and BLE beacons) if present in map data
        if "vbeacons" in map_data and map_data["vbeacons"]:
            vbeacons = map_data["vbeacons"]
            logging.info(f"Processing {len(vbeacons)} virtual beacons")

            beacon_x = []
            beacon_y = []
            beacon_hover = []
            beacon_names = []

            for beacon in vbeacons:
                x = beacon.get("x")
                y = beacon.get("y")
                if x is not None and y is not None:
                    beacon_x.append(x)
                    beacon_y.append(y)

                    name = beacon.get("name", "Unnamed Beacon")
                    beacon_names.append(name)

                    hover = f"<b>Virtual Beacon: {name}</b><br>"
                    hover += f"UUID: {beacon.get('uuid', 'N/A')}<br>"
                    hover += f"Major: {beacon.get('major', 'N/A')}<br>"
                    hover += f"Minor: {beacon.get('minor', 'N/A')}<br>"
                    hover += f"Power: {beacon.get('power', 'N/A')}<br>"
                    hover += f"Position: ({x}, {y})"
                    beacon_hover.append(hover)

            if beacon_x:
                # Add virtual beacon markers
                fig.add_trace(
                    go.Scatter(
                        x=beacon_x,
                        y=beacon_y,
                        mode="markers",
                        name="Virtual Beacons",
                        marker=dict(
                            symbol="circle",
                            size=14,
                            color="#00ff00",  # Green for virtual beacons
                            line=dict(color="white", width=2),
                            opacity=0.9,
                        ),
                        hovertext=beacon_hover,
                        hoverinfo="text",
                        visible=True,
                        showlegend=True,
                    )
                )

                # Add beacon name labels
                for _, (x, y, name) in enumerate(zip(beacon_x, beacon_y, beacon_names, strict=True)):
                    fig.add_annotation(
                        x=x,
                        y=y - 12,
                        text=f"<b>{name}</b>",
                        showarrow=False,
                        font=dict(size=9, color="white", family="Arial"),
                        bgcolor="rgba(0,200,0,0.9)",
                        bordercolor="white",
                        borderwidth=1,
                        borderpad=2,
                        xanchor="center",
                        yanchor="bottom",
                        name="Virtual Beacons Label",  # For toggle control
                    )

                # Add coverage circles for vBeacons based on power
                for beacon in vbeacons:
                    x = beacon.get("x")
                    y = beacon.get("y")
                    power = beacon.get("power", 0)  # Power in dBm

                    if x is not None and y is not None:
                        # Estimate coverage radius based on power (rough approximation)
                        # Higher power = larger radius
                        # Typical range: -12 to +4 dBm
                        base_radius = 50  # Base radius in pixels
                        power_factor = (power + 12) / 16  # Normalize -12 to +4 range
                        radius = base_radius + (power_factor * 100)

                        # Create circle using parametric plot
                        theta = [i * 2 * pi / 50 for i in range(51)]
                        circle_x = [x + radius * cos(t) for t in theta]
                        circle_y = [y + radius * sin(t) for t in theta]

                        fig.add_trace(
                            go.Scatter(
                                x=circle_x,
                                y=circle_y,
                                mode="lines",
                                line=dict(color="rgba(0,255,0,0.3)", width=1, dash="dash"),
                                fill="toself",
                                fillcolor="rgba(0,255,0,0.05)",
                                name="vBeacon Coverage",
                                showlegend=False,
                                hoverinfo="skip",
                            )
                        )

                logging.info(f"Added {len(beacon_x)} virtual beacons to map")
        else:
            logging.info("No virtual beacons found on this map")

        # Add BLE beacons if present
        if "beacons" in map_data and map_data["beacons"]:
            ble_beacons = map_data["beacons"]
            logging.info(f"Processing {len(ble_beacons)} BLE beacons")

            ble_x = []
            ble_y = []
            ble_hover = []
            ble_names = []

            for beacon in ble_beacons:
                x = beacon.get("x")
                y = beacon.get("y")
                if x is not None and y is not None:
                    ble_x.append(x)
                    ble_y.append(y)

                    name = beacon.get("name", beacon.get("mac", "Unnamed"))
                    ble_names.append(name)

                    hover = f"<b>BLE Beacon: {name}</b><br>"
                    hover += f"MAC: {beacon.get('mac', 'N/A')}<br>"
                    hover += f"Type: {beacon.get('type', 'N/A')}<br>"
                    hover += f"Power: {beacon.get('power', 'N/A')}<br>"
                    hover += f"Position: ({x}, {y})"
                    ble_hover.append(hover)

            if ble_x:
                # Add BLE beacon markers
                fig.add_trace(
                    go.Scatter(
                        x=ble_x,
                        y=ble_y,
                        mode="markers",
                        name="BLE Beacons",
                        marker=dict(
                            symbol="circle",
                            size=14,
                            color="#00bfff",  # Cyan for BLE beacons
                            line=dict(color="white", width=2),
                            opacity=0.9,
                        ),
                        hovertext=ble_hover,
                        hoverinfo="text",
                        visible=True,
                        showlegend=True,
                    )
                )

                # Add BLE beacon name labels
                for _, (x, y, name) in enumerate(zip(ble_x, ble_y, ble_names, strict=True)):
                    fig.add_annotation(
                        x=x,
                        y=y - 12,
                        text=f"<b>{name}</b>",
                        showarrow=False,
                        font=dict(size=9, color="white", family="Arial"),
                        bgcolor="rgba(0,191,255,0.9)",
                        bordercolor="white",
                        borderwidth=1,
                        borderpad=2,
                        xanchor="center",
                        yanchor="bottom",
                        name="BLE Beacons Label",  # For toggle control
                    )

                logging.info(f"Added {len(ble_x)} BLE beacons to map")
        else:
            logging.info("No BLE beacons found on this map")

        # Add RF Coverage Heatmap from Mist API data
        if coverage_data and "results" in coverage_data and len(coverage_data.get("results", [])) > 0:
            logging.info(f"Processing RF coverage data - {len(coverage_data.get('results', []))} grid points")

            # API returns coordinates in METERS - must convert to pixels using PPM
            result_def = coverage_data.get("result_def", [])
            results = coverage_data.get("results", [])
            gridsize_meters = coverage_data.get("gridsize", 1)

            logging.debug(f"Coverage result_def: {result_def}")
            logging.debug(f"Coverage gridsize: {gridsize_meters} meters, PPM: {ppm}")

            # Find indices for data fields
            try:
                x_idx = result_def.index("x")
                y_idx = result_def.index("y")
                max_rssi_idx = result_def.index("max_rssi")
                avg_rssi_idx = result_def.index("avg_rssi")
            except ValueError as e:
                logging.error(f"Coverage data missing expected fields: {e}")
                x_idx, y_idx, max_rssi_idx, avg_rssi_idx = 0, 1, 4, 5

            # Build grid data structure for heatmap
            grid_data = {}
            for result in results:
                if len(result) <= max(x_idx, y_idx, max_rssi_idx, avg_rssi_idx):
                    continue

                x_meters = result[x_idx]
                y_meters = result[y_idx]
                pixel_x = x_meters * ppm
                pixel_y = y_meters * ppm
                max_rssi = result[max_rssi_idx]

                grid_data[(pixel_x, pixel_y)] = max_rssi

            if grid_data:
                # Auto-scale color range based on actual data
                all_rssi_values = [v for v in grid_data.values() if v is not None]
                if all_rssi_values:
                    min_rssi = min(all_rssi_values)  # Most negative (weakest)
                    max_rssi = max(all_rssi_values)  # Closest to zero (strongest)
                    logging.info(f"RF Coverage RSSI range: {min_rssi} dBm (weakest) to {max_rssi} dBm (strongest)")
                else:
                    min_rssi = -100
                    max_rssi = -40

                # Convert to regular grid for Heatmap trace
                unique_x = sorted(set(x for x, y in grid_data.keys()))
                unique_y = sorted(set(y for x, y in grid_data.keys()))

                # Diagnostic logging for coordinate alignment debugging
                logging.info(f"HEATMAP DEBUG - Map dimensions: {map_width}x{map_height} pixels, PPM: {ppm}")
                logging.info(
                    f"HEATMAP DEBUG - Coverage X range: {min(unique_x):.1f} to {max(unique_x):.1f} pixels "
                    f"(from {min(unique_x) / ppm:.1f}m to {max(unique_x) / ppm:.1f}m)"
                )
                logging.info(
                    f"HEATMAP DEBUG - Coverage Y range: {min(unique_y):.1f} to {max(unique_y):.1f} pixels "
                    f"(from {min(unique_y) / ppm:.1f}m to {max(unique_y) / ppm:.1f}m)"
                )
                logging.info(
                    f"HEATMAP DEBUG - Grid size: {len(unique_x)} x {len(unique_y)} = {len(grid_data)} data points"
                )

                # Create Z matrix for heatmap - use None for missing data points
                # This prevents artificial values from being interpolated
                z_matrix = []
                for y_val in unique_y:
                    row = []
                    for x_val in unique_x:
                        rssi = grid_data.get((x_val, y_val), None)  # None for missing - no fake data
                        row.append(rssi)
                    z_matrix.append(row)

                # Custom colorscale: red (strongest/closest to 0) -> blue (weakest/most negative)
                colorscale = [
                    [0.0, "rgb(0, 0, 255)"],  # Blue (weakest/most negative)
                    [0.33, "rgb(0, 255, 0)"],  # Green
                    [0.50, "rgb(255, 255, 0)"],  # Yellow
                    [0.67, "rgb(255, 165, 0)"],  # Orange
                    [1.0, "rgb(255, 0, 0)"],  # Red (strongest/closest to 0)
                ]

                fig.add_trace(
                    go.Heatmap(
                        x=unique_x,
                        y=unique_y,
                        z=z_matrix,
                        colorscale=colorscale,
                        zmin=min_rssi,  # Auto-scale to actual data range
                        zmax=max_rssi,
                        opacity=0.5,
                        name="RF Coverage",
                        hovertemplate="X: %{x}<br>Y: %{y}<br>RSSI: %{z} dBm<extra></extra>",
                        visible=False,
                        showscale=True,  # Show color scale legend
                        colorbar=dict(
                            title=dict(text="RSSI (dBm)", side="right", font=dict(size=12, color="white")),
                            thickness=20,
                            len=0.5,
                            y=0.95,
                            yanchor="top",
                            x=1.02,
                            tickfont=dict(size=10, color="white"),
                            tickmode="linear",
                            tick0=min_rssi,
                            dtick=(max_rssi - min_rssi) / 5,  # Show 6 tick marks
                            outlinewidth=1,
                            outlinecolor="white",
                        ),
                        connectgaps=True,  # Interpolate across gaps for smooth coverage
                        zsmooth="best",  # Smooth interpolation between data points
                    )
                )

                logging.info(
                    f"Added RF Coverage heatmap: {len(grid_data)} cells "
                    f"({gridsize_meters}m grid) with auto-scaled colors ({min_rssi} to {max_rssi} dBm)"
                )
            else:
                logging.warning("No valid coverage grid data to visualize")
        elif coverage_data:
            logging.warning("Coverage data received but no results")
        else:
            logging.info("No RF coverage data available")

        # Add map origin marker (coordinate reference point)
        origin = map_data.get("origin", {}) or {}
        origin_x = origin.get("x", 0)
        origin_y = origin.get("y", 0)

        fig.add_trace(
            go.Scatter(
                x=[origin_x],
                y=[origin_y],
                mode="markers+text",
                name="Map Origin",
                marker=dict(symbol="x", size=20, color="yellow", line=dict(width=3, color="black")),
                text=["Origin (0,0)"],
                textposition="top center",
                textfont=dict(size=12, color="yellow"),
                visible=False,
                showlegend=True,
            )
        )

        # Update layout with dark theme and responsive sizing
        fig.update_layout(
            title={"text": f"Map: {map_data.get('name', 'Unnamed')}", "font": {"size": 20, "color": "#e0e0e0"}},
            xaxis=dict(
                range=[-50, map_width + 50],  # Add margins to show full map
                visible=True,
                title="X (pixels)",
                gridcolor="#444",
                zerolinecolor="#666",
                color="#b0b0b0",
                constrain="domain",  # Keep zoom within bounds
            ),
            yaxis=dict(
                range=[map_height + 50, -50],  # Inverted range with margins: Mist uses top-left origin
                visible=True,
                title="Y (pixels)",
                scaleanchor="x",
                scaleratio=1,
                gridcolor="#444",
                zerolinecolor="#666",
                color="#b0b0b0",
                constrain="domain",  # Keep zoom within bounds
            ),
            autosize=True,
            hovermode="closest",
            showlegend=True,
            uirevision="constant",  # Prevent auto-ranging to data - maintain user's view
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(45,45,45,0.9)",
                bordercolor="#667eea",
                borderwidth=2,
                font=dict(color="#e0e0e0", size=12),
            ),
            plot_bgcolor="#1a1a1a",
            paper_bgcolor="#1a1a1a",
            margin=dict(l=50, r=50, t=80, b=50),
            dragmode="zoom",  # Default to zoom, users can select drawing tools
            newshape=dict(line=dict(color="cyan", width=3), fillcolor="rgba(0,255,255,0.2)", opacity=0.8),
            # Store PPM for unit conversions in annotations
            meta={"ppm": ppm, "origin_x": map_data.get("origin_x", 0), "origin_y": map_data.get("origin_y", 0)},
        )

        # Add origin crosshair marker (blue crosshair at origin point)
        origin_x = map_data.get("origin_x", 0)
        origin_y = map_data.get("origin_y", 0)
        crosshair_size = 40

        # Horizontal line of origin crosshair
        fig.add_trace(
            go.Scatter(
                x=[origin_x - crosshair_size, origin_x + crosshair_size],
                y=[origin_y, origin_y],
                mode="lines",
                line=dict(color="#00bfff", width=3),  # Deep sky blue
                name="Origin",
                showlegend=True,
                hovertext=f"Origin: ({origin_x}, {origin_y})",
                hoverinfo="text",
            )
        )

        # Vertical line of origin crosshair
        fig.add_trace(
            go.Scatter(
                x=[origin_x, origin_x],
                y=[origin_y - crosshair_size, origin_y + crosshair_size],
                mode="lines",
                line=dict(color="#00bfff", width=3),  # Deep sky blue
                showlegend=False,
                hovertext=f"Origin: ({origin_x}, {origin_y})",
                hoverinfo="text",
            )
        )

        # Center dot of origin crosshair
        fig.add_trace(
            go.Scatter(
                x=[origin_x],
                y=[origin_y],
                mode="markers",
                marker=dict(size=12, color="#00bfff", line=dict(color="white", width=2)),
                name="Origin Point",
                showlegend=False,
                hovertext=f"Origin: ({origin_x}, {origin_y})",
                hoverinfo="text",
            )
        )

        # Build map dropdown options for switching between maps
        map_dropdown_options: list = [{"label": m.get("name", "Unnamed"), "value": m.get("id")} for m in all_maps]

        # Build site dropdown options for switching between sites (sorted by name)
        sites_sorted = sorted(all_sites, key=lambda x: x.get("name", "").lower())
        site_dropdown_options: list = [
            {"label": s.get("name", "Unnamed Site"), "value": s.get("id")} for s in sites_sorted
        ]

        # Create responsive Dash layout with dark theme
        app.layout = html.Div(
            [
                # Header with title and utilities buttons
                html.Div(
                    [
                        # Site selector dropdown
                        html.Div(
                            [
                                html.Span("Site: ", style={"fontSize": "14px", "color": "#888", "marginRight": "5px"}),
                                dcc.Dropdown(
                                    id="site-selector-dropdown",
                                    options=site_dropdown_options,
                                    value=site_id,
                                    clearable=False,
                                    searchable=True,
                                    style={"width": "250px", "display": "inline-block", "verticalAlign": "middle"},
                                    className="dark-dropdown",
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": "20px", "verticalAlign": "middle"},
                        ),
                        # Map selector dropdown
                        html.Div(
                            [
                                html.Span("Map: ", style={"fontSize": "14px", "color": "#888", "marginRight": "5px"}),
                                dcc.Dropdown(
                                    id="map-selector-dropdown",
                                    options=map_dropdown_options,
                                    value=map_id,
                                    clearable=False,
                                    searchable=False,
                                    style={"width": "200px", "display": "inline-block", "verticalAlign": "middle"},
                                    className="dark-dropdown",
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": "30px", "verticalAlign": "middle"},
                        ),
                        html.Div(
                            [
                                # Live Data Refresh Controls - moved to header
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id="auto-refresh-toggle",
                                            options=[{"label": " Auto-Refresh", "value": "enabled"}],
                                            value=["enabled"],  # Enabled by default
                                            labelStyle={
                                                "display": "inline-block",
                                                "fontSize": "12px",
                                                "color": "#e0e0e0",
                                            },
                                            style={"display": "inline-block", "marginRight": "10px"},
                                        ),
                                        html.Button(
                                            "Refresh",
                                            id="manual-refresh-btn",
                                            n_clicks=0,
                                            style={
                                                "marginRight": "15px",
                                                "padding": "6px 12px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#00ff00",
                                                "border": "1px solid #00ff00",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "12px",
                                                "verticalAlign": "middle",
                                            },
                                        ),
                                        html.Span(
                                            id="countdown-display",
                                            children="Clients: 30s | RF: 5m",
                                            style={
                                                "fontSize": "11px",
                                                "color": "#667eea",
                                                "marginRight": "15px",
                                                "verticalAlign": "middle",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "inline-block",
                                        "marginRight": "20px",
                                        "padding": "5px 10px",
                                        "backgroundColor": "#1a1a1a",
                                        "borderRadius": "4px",
                                        "border": "1px solid #444",
                                    },
                                ),
                                html.Button(
                                    "[AUTO] Auto-Zone",
                                    id="auto-zone-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#667eea",
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                    },
                                ),
                                html.Button(
                                    "[PIN] Add vBeacon",
                                    id="add-vbeacon-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00ff00",
                                        "border": "1px solid #00ff00",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[ANT] Add Beacon",
                                    id="add-beacon-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00bfff",
                                        "border": "1px solid #00bfff",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[IMG] Change Image",
                                    id="change-image-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #667eea",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[DEL] Remove Image",
                                    id="remove-image-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #667eea",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[EDIT] Rename",
                                    id="rename-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #667eea",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[X] Delete",
                                    id="delete-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#ff4444",
                                        "border": "1px solid #ff4444",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[+] Clone",
                                    id="clone-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00ff88",
                                        "border": "1px solid #00ff88",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                    },
                                ),
                                html.Div(
                                    id="utilities-status",
                                    style={
                                        "display": "inline-block",
                                        "marginLeft": "20px",
                                        "color": "#a0a0ff",
                                        "fontSize": "13px",
                                    },
                                ),
                            ],
                            style={"display": "inline-block", "float": "right"},
                        ),
                    ],
                    style={"padding": "15px 20px", "borderBottom": "2px solid #667eea", "backgroundColor": "#2a2a2a"},
                ),
                # Clone map input panel (hidden by default)
                html.Div(
                    id="clone-panel",
                    children=[
                        html.Div(
                            [
                                html.Span(
                                    "[+] Clone Map: ",
                                    style={"color": "#00ff88", "fontWeight": "bold", "marginRight": "10px"},
                                ),
                                dcc.Input(
                                    id="clone-name-input",
                                    type="text",
                                    placeholder=f"{map_data.get('name', 'Map')} (Copy)",
                                    value=f"{map_data.get('name', 'Map')} (Copy)",
                                    style={
                                        "width": "300px",
                                        "padding": "8px 12px",
                                        "backgroundColor": "#2a2a2a",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #00ff88",
                                        "borderRadius": "4px",
                                        "marginRight": "10px",
                                    },
                                ),
                                html.Button(
                                    "Execute Clone",
                                    id="execute-clone-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#00ff88",
                                        "color": "#1a1a1a",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                        "marginRight": "10px",
                                    },
                                ),
                                html.Button(
                                    "Cancel",
                                    id="cancel-clone-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#ff4444",
                                        "border": "1px solid #ff4444",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Span(
                                    id="clone-status",
                                    style={"marginLeft": "15px", "color": "#e0e0e0", "fontSize": "13px"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
                        )
                    ],
                    style={
                        "display": "none",
                        "padding": "12px 20px",
                        "backgroundColor": "#1a1a1a",
                        "borderBottom": "1px solid #00ff88",
                    },
                ),
                # Delete map confirmation panel (hidden by default)
                html.Div(
                    id="delete-panel",
                    children=[
                        html.Div(
                            [
                                html.Span(
                                    "X DESTRUCTIVE: Delete this floorplan? ",
                                    style={"color": "#ff4444", "fontWeight": "bold", "marginRight": "10px"},
                                ),
                                html.Span(
                                    id="delete-map-name-display",
                                    children=f"Map: {map_data.get('name', 'Unknown')}",
                                    style={"color": "#ffaa00", "marginRight": "20px"},
                                ),
                                html.Button(
                                    "YES - DELETE MAP",
                                    id="confirm-delete-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#ff4444",
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                        "marginRight": "10px",
                                    },
                                ),
                                html.Button(
                                    "Cancel",
                                    id="cancel-delete-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00ff88",
                                        "border": "1px solid #00ff88",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Span(
                                    id="delete-status",
                                    style={"marginLeft": "15px", "color": "#e0e0e0", "fontSize": "13px"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
                        )
                    ],
                    style={
                        "display": "none",
                        "padding": "12px 20px",
                        "backgroundColor": "#330000",
                        "borderBottom": "2px solid #ff4444",
                    },
                ),
                html.Div(
                    [
                        # Map container - responsive
                        html.Div(
                            [
                                dcc.Graph(
                                    id="map-display",
                                    figure=fig,
                                    config={
                                        "displayModeBar": True,
                                        "displaylogo": False,
                                        "modeBarButtonsToAdd": [
                                            "drawline",
                                            "drawopenpath",
                                            "drawclosedpath",
                                            "drawcircle",
                                            "drawrect",
                                            "eraseshape",
                                        ],
                                        "scrollZoom": True,
                                        "editable": True,
                                        "edits": {"shapePosition": True, "annotationPosition": True},
                                        "toImageButtonOptions": {
                                            "format": "png",
                                            "filename": f"map_{map_data.get('name', 'export')}",
                                            "height": 1080,
                                            "width": 1920,
                                            "scale": 2,
                                        },
                                    },
                                    style={"height": "100%", "width": "100%"},
                                )
                            ],
                            className="map-container",
                        ),
                        # Sidebar
                        html.Div(
                            [
                                html.H3("Layer Controls"),
                                html.H4(
                                    "Infrastructure",
                                    style={
                                        "fontSize": "13px",
                                        "color": "#667eea",
                                        "marginTop": "10px",
                                        "marginBottom": "5px",
                                    },
                                ),
                                dcc.Checklist(
                                    id="layer-toggle",
                                    options=[
                                        {"label": " [W] Walls", "value": "walls"},
                                        {"label": " [M] Wayfinding", "value": "wayfinding"},
                                        {"label": " [Z] Location Zones", "value": "zones"},
                                        {"label": " [P] Proximity Zones", "value": "proximity_zones"},
                                        {"label": " [V] Validation Paths", "value": "validation"},
                                        {"label": " [R] RF Diagnostics Heatmap", "value": "rf_heatmap"},
                                        {"label": " [O] Map Origin", "value": "origin"},
                                    ],
                                    value=["walls", "wayfinding", "zones", "validation"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Beacons & Positioning",
                                    style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"},
                                ),
                                dcc.Checklist(
                                    id="beacon-toggle",
                                    options=[
                                        {"label": " [vB] Virtual Beacons", "value": "vbeacons"},
                                        {"label": " [C] vBeacon Coverage", "value": "vbeacon_coverage"},
                                        {"label": " [3P] 3rd Party Beacons", "value": "ble_beacons"},
                                    ],
                                    value=["vbeacons", "ble_beacons"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Clients", style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"}
                                ),
                                dcc.Checklist(
                                    id="client-toggle",
                                    options=[
                                        {"label": " [Wi] WiFi Clients", "value": "wifi_clients"},
                                        {"label": " [Wr] Wired Clients", "value": "wired_clients"},
                                        {"label": " [Ex] Excluded Clients", "value": "excluded_clients"},
                                        {"label": " [AP] Show Associated AP", "value": "show_client_ap"},
                                    ],
                                    value=["wifi_clients", "wired_clients", "show_client_ap"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Devices", style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"}
                                ),
                                dcc.Checklist(
                                    id="device-toggle",
                                    options=[
                                        {"label": " [AP] Access Points", "value": "aps"},
                                        {"label": " [SW] Switches", "value": "switches"},
                                        {"label": " [GW] Gateways", "value": "gateways"},
                                        {"label": " [MS] Mesh Associations", "value": "mesh_links"},
                                    ],
                                    value=["aps", "switches", "gateways"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Filters", style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"}
                                ),
                                dcc.Checklist(
                                    id="filter-toggle",
                                    options=[
                                        {"label": " [HI] Hide Inactive Items", "value": "hide_inactive"},
                                    ],
                                    value=[],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.Hr(),
                                html.H3("Drawing Tools"),
                                html.Details(
                                    [
                                        html.Summary(
                                            "How to use",
                                            style={
                                                "fontSize": "12px",
                                                "color": "#00bfff",
                                                "cursor": "pointer",
                                                "marginBottom": "8px",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "1. Select a Drawing Mode below",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#aaa",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "2. Use toolbar above map to draw shape",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#aaa",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "3. Click 'Save Last Shape to Mist'",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#aaa",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "Zones: Draw rectangle for coverage areas",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#00bfff",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "Walls: Draw line for RF attenuation",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#ffa500",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "Paths: Draw line for validation routes",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#ff00ff",
                                                        "margin": "4px 0 8px 10px",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "backgroundColor": "#2a2a2a",
                                                "padding": "8px",
                                                "borderRadius": "4px",
                                                "marginBottom": "10px",
                                            },
                                        ),
                                    ],
                                    open=False,
                                ),
                                # Drawing mode selector
                                html.Div(
                                    [
                                        html.Label(
                                            "Drawing Mode:",
                                            style={"fontSize": "12px", "color": "#888", "marginBottom": "4px"},
                                        ),
                                        dcc.Dropdown(
                                            id="drawing-mode-dropdown",
                                            options=[
                                                {"label": "Validation Path (magenta)", "value": "path"},
                                                {"label": "Zone Rectangle (cyan)", "value": "zone"},
                                                {"label": "Wall Segment (orange)", "value": "wall"},
                                                {"label": "Measurement Only", "value": "measure"},
                                            ],
                                            value="measure",
                                            clearable=False,
                                            style={"marginBottom": "10px", "color": "#e0e0e0"},
                                            className="dark-dropdown",
                                        ),
                                    ],
                                    style={"marginBottom": "10px"},
                                ),
                                # Zone name input (shown when zone mode selected)
                                html.Div(
                                    [
                                        dcc.Input(
                                            id="zone-name-input",
                                            type="text",
                                            placeholder="Zone name (required)",
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "marginBottom": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#e0e0e0",
                                                "border": "1px solid #00bfff",
                                                "borderRadius": "4px",
                                            },
                                        ),
                                    ],
                                    id="zone-name-container",
                                    style={"display": "none"},
                                ),
                                # Action buttons
                                html.Div(
                                    [
                                        html.Button(
                                            "[SAVE] Save Last Shape to Mist",
                                            id="save-shape-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "8px",
                                                "padding": "10px",
                                                "backgroundColor": "#28a745",
                                                "color": "white",
                                                "border": "none",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "13px",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.Button(
                                            "[CLR] Clear All Drawings",
                                            id="clear-drawings-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "8px",
                                                "padding": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ffc107",
                                                "border": "1px solid #ffc107",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "13px",
                                            },
                                        ),
                                    ]
                                ),
                                html.Hr(style={"margin": "10px 0"}),
                                # Delete from Mist section
                                html.P(
                                    "Delete from Mist API:",
                                    style={"fontSize": "12px", "color": "#ff6666", "marginBottom": "8px"},
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            "Delete Validation Paths",
                                            id="delete-paths-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff4444",
                                                "border": "1px solid #ff4444",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                        html.Button(
                                            "Delete Wayfinding Paths",
                                            id="delete-wayfinding-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff8844",
                                                "border": "1px solid #ff8844",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                        html.Button(
                                            "Delete All Walls",
                                            id="delete-walls-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff4444",
                                                "border": "1px solid #ff4444",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                        html.Button(
                                            "Delete All Zones",
                                            id="delete-zones-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff66ff",
                                                "border": "1px solid #ff66ff",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                    ]
                                ),
                                html.Div(
                                    id="drawing-tool-status",
                                    style={
                                        "fontSize": "11px",
                                        "color": "#a0a0ff",
                                        "marginTop": "8px",
                                        "minHeight": "40px",
                                    },
                                ),
                                html.Hr(),
                                html.H3("Measurement Tools"),
                                html.P("Use the toolbar above the map:", style={"fontSize": "12px", "color": "#888"}),
                                html.P(
                                    "- Draw Line - Measure distances",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.P(
                                    "- Draw Path - Create routes",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.P(
                                    "- Draw Circle - Mark areas",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.P(
                                    "- Erase - Remove drawings",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.Hr(),
                                html.H3("Set Scale"),
                                html.P("1. Draw a line of known length", style={"fontSize": "11px", "color": "#888"}),
                                html.P("2. Enter actual length below", style={"fontSize": "11px", "color": "#888"}),
                                html.Div(
                                    [
                                        dcc.Input(
                                            id="scale-length-input",
                                            type="number",
                                            placeholder="Length in meters",
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "marginBottom": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#e0e0e0",
                                                "border": "1px solid #667eea",
                                                "borderRadius": "4px",
                                            },
                                        ),
                                        html.Button(
                                            "Set Scale from Last Line",
                                            id="set-scale-button",
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "backgroundColor": "#667eea",
                                                "color": "white",
                                                "border": "none",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.Div(
                                            id="scale-status",
                                            style={"marginTop": "8px", "fontSize": "11px", "color": "#a0a0ff"},
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.H3("Set Origin"),
                                html.P(
                                    "Click map to set coordinate origin", style={"fontSize": "11px", "color": "#888"}
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            "Enable Origin Setting Mode",
                                            id="origin-mode-button",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "marginBottom": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "white",
                                                "border": "1px solid #667eea",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.Div(
                                            id="origin-status",
                                            children=[
                                                html.P(
                                                    f"Current: ({map_data.get('origin_x', 0)}, "
                                                    f"{map_data.get('origin_y', 0)})",
                                                    style={"fontSize": "11px", "color": "#888", "margin": "4px 0"},
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.H3("Location Zones"),
                                html.Div(
                                    [
                                        (
                                            dcc.Checklist(
                                                id="zone-toggle",
                                                options=[
                                                    {
                                                        "label": f" {zone.get('name', f'Zone {i + 1}')}",
                                                        "value": zone.get("id", f"zone_{i}"),
                                                    }
                                                    for i, zone in enumerate(zones)
                                                ],
                                                value=[zone.get("id", f"zone_{i}") for i, zone in enumerate(zones)],
                                                labelStyle={
                                                    "display": "block",
                                                    "margin": "8px 0",
                                                    "fontSize": "13px",
                                                    "color": "#e0e0e0",
                                                },
                                                style={"marginBottom": "15px"},
                                            )
                                            if zones
                                            else html.P(
                                                "No zones on this map",
                                                style={"color": "#888", "fontSize": "12px", "fontStyle": "italic"},
                                            )
                                        ),
                                        html.Div(
                                            id="selected-zone-info",
                                            children=[
                                                html.P(
                                                    "Click a zone for details",
                                                    style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"},
                                                )
                                            ],
                                            style={
                                                "padding": "10px",
                                                "backgroundColor": "#3d3d3d",
                                                "borderRadius": "4px",
                                                "marginTop": "10px",
                                            },
                                        ),
                                        (
                                            html.Div(
                                                [
                                                    html.Button(
                                                        "[EDIT] Edit Zone",
                                                        id="edit-zone-btn",
                                                        n_clicks=0,
                                                        style={
                                                            "width": "48%",
                                                            "marginRight": "4%",
                                                            "padding": "6px",
                                                            "backgroundColor": "#667eea",
                                                            "color": "white",
                                                            "border": "none",
                                                            "borderRadius": "4px",
                                                            "cursor": "pointer",
                                                            "fontSize": "12px",
                                                        },
                                                    ),
                                                    html.Button(
                                                        "[DEL] Remove Zone",
                                                        id="remove-zone-btn",
                                                        n_clicks=0,
                                                        style={
                                                            "width": "48%",
                                                            "padding": "6px",
                                                            "backgroundColor": "#ff4444",
                                                            "color": "white",
                                                            "border": "none",
                                                            "borderRadius": "4px",
                                                            "cursor": "pointer",
                                                            "fontSize": "12px",
                                                        },
                                                    ),
                                                ],
                                                style={"marginTop": "10px", "display": "flex"},
                                            )
                                            if zones
                                            else None
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.H3("Map Info"),
                                html.Div(
                                    id="map-info",
                                    children=[
                                        html.P(
                                            [
                                                html.Span("Dimensions: ", className="info-badge"),
                                                f"{map_width} x {map_height} px",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("PPM: ", className="info-badge"),
                                                f"{map_data.get('ppm', 'N/A')}",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("Orientation: ", className="info-badge"),
                                                f"{map_data.get('orientation', 0)} deg",
                                            ]
                                        ),
                                        html.P([html.Span("Devices: ", className="info-badge"), f"{len(devices)}"]),
                                        html.P([html.Span("Clients: ", className="info-badge"), f"{len(clients)}"]),
                                        html.P([html.Span("Zones: ", className="info-badge"), f"{len(zones)}"]),
                                        html.P(
                                            [
                                                html.Span("vBeacons: ", className="info-badge"),
                                                f"{len(map_data.get('vbeacons', []))}",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("BLE Beacons: ", className="info-badge"),
                                                f"{len(map_data.get('beacons', []))}",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("Validation Paths: ", className="info-badge"),
                                                f"{len(map_data.get('sitesurvey_path', []))}",
                                            ]
                                        ),
                                    ],
                                ),
                                html.Hr(),
                                html.Div(
                                    id="click-data",
                                    children=[
                                        html.H3("Device Info"),
                                        html.P(
                                            "Click a device for details", style={"color": "#888", "fontStyle": "italic"}
                                        ),
                                    ],
                                ),
                            ],
                            className="sidebar",
                        ),
                    ],
                    className="main-container",
                ),
                # Hidden stores for state management
                dcc.Store(
                    id="map-config-store",
                    data={
                        "site_id": site_id,
                        "site_name": site_name,
                        "map_id": map_id,
                        "map_name": map_data.get("name", "Unknown"),
                        "ppm": ppm,
                        "map_width": map_width,
                        "map_height": map_height,
                    },
                ),
                # Store for available maps list (for dropdown)
                dcc.Store(
                    id="available-maps-store",
                    data=[{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in all_maps],
                ),
                # Store for available sites list (for dropdown)
                dcc.Store(
                    id="available-sites-store",
                    data=[{"id": s.get("id"), "name": s.get("name", "Unnamed Site")} for s in all_sites],
                ),
                # Store for tracking selected zone ID
                dcc.Store(id="selected-zone-store", data={"zone_id": None, "zone_name": None}),
                # Store for tracking last refresh times
                dcc.Store(id="refresh-times-store", data={"client_last_refresh": 0, "coverage_last_refresh": 0}),
                # Store to trigger map list refresh (cache bust) after clone/delete operations
                dcc.Store(id="cache-bust-store", data={"trigger": 0}),
                # Interval components for live refresh (enabled by default since auto-refresh is on)
                dcc.Interval(
                    id="client-refresh-interval",
                    interval=30 * 1000,  # 30 seconds in milliseconds
                    n_intervals=0,
                    disabled=False,  # Enabled by default with auto-refresh
                ),
                dcc.Interval(
                    id="coverage-refresh-interval",
                    interval=5 * 60 * 1000,  # 5 minutes in milliseconds
                    n_intervals=0,
                    disabled=False,  # Enabled by default with auto-refresh
                ),
                # Fast interval for countdown display (1 second)
                dcc.Interval(
                    id="countdown-tick-interval",
                    interval=1000,  # 1 second
                    n_intervals=0,
                    disabled=False,  # Enabled by default with auto-refresh
                ),
                # Location component for URL-based map switching
                dcc.Location(id="url-location", refresh=True),
                # Hidden div for map switch trigger
                html.Div(id="map-switch-trigger", style={"display": "none"}),
            ],
            style={"height": "100vh", "display": "flex", "flexDirection": "column"},
        )

        # Clientside callback for map switching - triggers page reload with new map_id in URL
        app.clientside_callback(
            """
            function(selected_map_id, config) {
                var current_map_id = config ? config.map_id : null;
                if (!selected_map_id || selected_map_id === current_map_id) {
                    return window.dash_clientside.no_update;
                }

                // Check if URL already has this map_id - if so, don't redirect (prevents loop)
                var urlParams = new URLSearchParams(window.location.search);
                var url_map_id = urlParams.get('map_id');
                if (url_map_id === selected_map_id) {
                    console.log('Map switch: URL already has map_id=' + selected_map_id + ', skipping redirect');
                    return window.dash_clientside.no_update;
                }

                // Redirect to URL with map_id parameter (preserve site_id if present)
                var site_id = urlParams.get('site_id') || (config ? config.site_id : null);
                var new_url = '/?map_id=' + selected_map_id;
                if (site_id) {
                    new_url += '&site_id=' + site_id;
                }
                console.log('Map switch: redirecting to map_id=' + selected_map_id);
                window.location.href = new_url;
                return '';
            }
            """,
            Output("map-switch-trigger", "children"),
            [Input("map-selector-dropdown", "value")],
            [State("map-config-store", "data")],
            prevent_initial_call=True,
        )

        # Clientside callback to reload page after clone/delete to get fresh map data
        app.clientside_callback(
            """
            function(cache_bust_data) {
                if (!cache_bust_data || !cache_bust_data.trigger) {
                    return window.dash_clientside.no_update;
                }
                // Check if this trigger was already processed (stored in sessionStorage)
                var lastTrigger = parseInt(sessionStorage.getItem('lastCacheBustTrigger') || '0');
                var currentTrigger = cache_bust_data.trigger;

                // Only reload if trigger is NEW (greater than last processed)
                if (currentTrigger > lastTrigger) {
                    console.log('Cache bust: Reloading page to refresh map data '
                        + '(trigger=' + currentTrigger + ', last=' + lastTrigger + ')');
                    // Store this trigger as processed before reloading
                    sessionStorage.setItem('lastCacheBustTrigger', currentTrigger.toString());
                    // Small delay to allow status message to display briefly
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output("map-switch-trigger", "children", allow_duplicate=True),
            [Input("cache-bust-store", "data")],
            prevent_initial_call=True,
        )

        # Store reference to API session for site switching callbacks
        api_session_for_site_switch = self.apisession

        # Server-side callback to handle site switching from dropdown selection
        # This fetches new site data without requiring a page reload
        @app.callback(
            [
                Output("map-selector-dropdown", "options"),
                Output("map-selector-dropdown", "value", allow_duplicate=True),
                Output("available-maps-store", "data", allow_duplicate=True),
                Output("map-config-store", "data", allow_duplicate=True),
                Output("map-display", "figure", allow_duplicate=True),
            ],
            [Input("site-selector-dropdown", "value")],
            [State("map-config-store", "data"), State("available-sites-store", "data"), State("map-display", "figure")],
            prevent_initial_call=True,
        )
        def handle_site_switch_from_dropdown(selected_site_id, config, available_sites, current_fig):
            """Handle site switching when user selects a new site from dropdown - no page reload needed."""
            # EXTENSIVE DEBUGGING
            print(f"\n{'=' * 60}")
            print("[DEBUG] handle_site_switch_from_dropdown TRIGGERED")
            print(f"[DEBUG] selected_site_id: {selected_site_id}")
            print(f"[DEBUG] config: {config}")
            print(f"[DEBUG] available_sites count: {len(available_sites) if available_sites else 0}")
            print(f"{'=' * 60}\n")
            logging.info(f"[SITE-SWITCH] Callback triggered with site_id={selected_site_id}")

            if not selected_site_id:
                print("[DEBUG] No selected_site_id, returning no_update")
                logging.warning("[SITE-SWITCH] No selected_site_id provided")
                return no_update, no_update, no_update, no_update, no_update

            current_site_id = config.get("site_id") if config else None
            print(f"[DEBUG] current_site_id from config: {current_site_id}")

            # If same site selected, no update needed
            if selected_site_id == current_site_id:
                print(f"[DEBUG] Same site selected ({selected_site_id}), returning no_update")
                logging.debug(f"[SITE-SWITCH] Same site selected ({selected_site_id}), no update needed")
                return no_update, no_update, no_update, no_update, no_update

            # Get site name from available sites
            site_name = next(
                (s.get("name", "Unknown") for s in available_sites if s.get("id") == selected_site_id), "Unknown"
            )
            print(f"[DEBUG] Switching to site: {site_name} ({selected_site_id})")
            logging.info(f"[SITE-SWITCH] Switching to site {site_name} ({selected_site_id})")

            try:
                # Fetch maps for the new site
                print(f"[DEBUG] Fetching maps for site {selected_site_id}...")
                maps_response = mistapi.api.v1.sites.maps.listSiteMaps(
                    api_session_for_site_switch, site_id=selected_site_id
                )
                print(f"[DEBUG] Maps API response status: {maps_response.status_code}")

                if maps_response.status_code != 200:
                    print(f"[DEBUG] ERROR: Failed to fetch maps - HTTP {maps_response.status_code}")
                    logging.error(
                        f"[SITE-SWITCH] Failed to fetch maps for site "
                        f"{selected_site_id} - HTTP {maps_response.status_code}"
                    )
                    return no_update, no_update, no_update, no_update, no_update

                new_maps = maps_response.data if maps_response.data else []
                print(f"[DEBUG] Found {len(new_maps)} maps for site {site_name}")
                logging.info(f"[SITE-SWITCH] Found {len(new_maps)} maps for site {site_name}")

                if not new_maps:
                    print("[DEBUG] No maps found, returning empty figure")
                    logging.warning(f"[SITE-SWITCH] No maps found for site {selected_site_id}")
                    # Return empty dropdown options and clear the figure
                    empty_fig = go.Figure()
                    empty_fig.update_layout(
                        title=f"No maps found for site: {site_name}",
                        paper_bgcolor="#1e1e1e",
                        plot_bgcolor="#1e1e1e",
                        font=dict(color="#e0e0e0"),
                    )
                    updated_config = config.copy() if config else {}
                    updated_config["site_id"] = selected_site_id
                    updated_config["site_name"] = site_name
                    updated_config["map_id"] = None
                    updated_config["map_name"] = None
                    print("[DEBUG] Returning: empty options, None value, empty store, updated config, empty figure")
                    return [], None, [], updated_config, empty_fig

                # Build new dropdown options
                new_map_options = [{"label": m.get("name", "Unnamed"), "value": m.get("id")} for m in new_maps]
                new_maps_store = [{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in new_maps]
                print(f"[DEBUG] Built {len(new_map_options)} dropdown options")

                # Select first map
                first_map = new_maps[0]
                selected_map_id = first_map.get("id")
                map_name = first_map.get("name", "Unnamed")
                print(f"[DEBUG] Selected first map: {map_name} ({selected_map_id})")

                # Update config with new site info
                updated_config = config.copy() if config else {}
                updated_config["site_id"] = selected_site_id
                updated_config["site_name"] = site_name
                updated_config["map_id"] = selected_map_id
                updated_config["map_name"] = map_name

                # Fetch and build the new map figure
                # Get map details including image URL
                map_data = first_map
                ppm = map_data.get("ppm", 1.0)
                map_width = map_data.get("width", 1000)
                map_height = map_data.get("height", 1000)
                updated_config["ppm"] = ppm
                updated_config["map_width"] = map_width
                updated_config["map_height"] = map_height

                # Create new figure with the map image
                new_fig = go.Figure()

                # Add map image as background
                if "url" in map_data:
                    new_fig.add_layout_image(
                        source=map_data["url"],
                        xref="x",
                        yref="y",
                        x=0,
                        y=map_height,
                        sizex=map_width,
                        sizey=map_height,
                        sizing="stretch",
                        opacity=1.0,
                        layer="below",
                    )

                # Fetch devices for this map
                try:
                    devices_response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                        api_session_for_site_switch, site_id=selected_site_id, limit=1000
                    )
                    if devices_response.status_code == 200:
                        all_devices = devices_response.data or []
                        devices = [d for d in all_devices if d.get("map_id") == selected_map_id]
                    else:
                        devices = []
                except Exception:
                    devices = []

                # Add device markers to figure
                for device in devices:
                    device_x = device.get("x", 0)
                    device_y = device.get("y", 0)
                    device_name = device.get("name", "Unknown")
                    device_type = device.get("type", "ap")
                    device_status = device.get("status", "unknown")

                    # Color based on status
                    if device_status == "connected":
                        marker_color = "#00ff00"
                    elif device_status == "disconnected":
                        marker_color = "#ff0000"
                    else:
                        marker_color = "#ffaa00"

                    # Symbol based on type
                    if device_type == "switch":
                        marker_symbol = "square"
                    elif device_type == "gateway":
                        marker_symbol = "diamond"
                    else:
                        marker_symbol = "circle"

                    new_fig.add_trace(
                        go.Scatter(
                            x=[device_x],
                            y=[device_y],
                            mode="markers+text",
                            marker=dict(
                                size=12, color=marker_color, symbol=marker_symbol, line=dict(color="white", width=1)
                            ),
                            text=[device_name],
                            textposition="top center",
                            textfont=dict(size=10, color="#e0e0e0"),
                            name=device_name,
                            showlegend=False,
                            hovertemplate=(
                                f"<b>{device_name}</b><br>Type: {device_type}<br>Status: {device_status}<extra></extra>"
                            ),
                        )
                    )

                # Configure figure layout
                new_fig.update_layout(
                    title=dict(text=f"{site_name} - {map_name}", font=dict(color="#e0e0e0", size=16), x=0.5),
                    paper_bgcolor="#1e1e1e",
                    plot_bgcolor="#1e1e1e",
                    xaxis=dict(
                        range=[0, map_width],
                        showgrid=False,
                        zeroline=False,
                        showticklabels=False,
                        scaleanchor="y",
                        scaleratio=1,
                    ),
                    yaxis=dict(range=[0, map_height], showgrid=False, zeroline=False, showticklabels=False),
                    margin=dict(l=0, r=0, t=40, b=0),
                    dragmode="pan",
                )

                print("[DEBUG] SUCCESS! Returning new data:")
                print(f"[DEBUG]   - map_options: {len(new_map_options)} options")
                print(f"[DEBUG]   - selected_map_id: {selected_map_id}")
                print(f"[DEBUG]   - maps_store: {len(new_maps_store)} maps")
                print(f"[DEBUG]   - updated_config site: {updated_config.get('site_name')}")
                print(f"[DEBUG]   - new_fig has {len(new_fig.data)} traces")  # type: ignore[arg-type]
                logging.info(f"[SITE-SWITCH] Successfully loaded map {map_name} with {len(devices)} devices")
                return new_map_options, selected_map_id, new_maps_store, updated_config, new_fig

            except Exception as site_switch_error:
                print(f"[DEBUG] EXCEPTION in site switch: {site_switch_error}")
                import traceback

                traceback.print_exc()
                logging.error(f"[SITE-SWITCH] Error: {site_switch_error}", exc_info=True)
                return no_update, no_update, no_update, no_update, no_update

        # Keep URL-based callback for handling direct URL access with site_id parameter
        @app.callback(
            [Output("site-selector-dropdown", "value")],
            [Input("url-location", "search")],
            [State("map-config-store", "data"), State("available-sites-store", "data")],
            prevent_initial_call="initial_duplicate",
        )
        def handle_site_from_url(url_search, config, available_sites):
            """Handle site selection when URL contains site_id parameter (for bookmarks/links)."""
            import urllib.parse

            if not url_search:
                return [no_update]

            params = urllib.parse.parse_qs(url_search.lstrip("?"))
            url_site_id = params.get("site_id", [None])[0]

            if not url_site_id:
                return [no_update]

            current_site_id = config.get("site_id") if config else None
            if url_site_id == current_site_id:
                return [no_update]

            # Verify site exists
            valid_site_ids = [s.get("id") for s in available_sites] if available_sites else []
            if url_site_id not in valid_site_ids:
                logging.warning(f"URL site switch: Invalid site_id {url_site_id}")
                return [no_update]

            # Return the site_id to update dropdown, which will trigger handle_site_switch_from_dropdown
            logging.info(f"URL site switch: Setting dropdown to site {url_site_id}")
            return [url_site_id]

        # Callback to sync dropdown value with URL on page load (runs BEFORE clientside callback)
        @app.callback(
            Output("map-selector-dropdown", "value"),
            [Input("url-location", "search")],
            [State("available-maps-store", "data"), State("map-selector-dropdown", "value")],
            prevent_initial_call=False,  # Must run on initial load
        )
        def sync_dropdown_with_url(url_search, available_maps, current_dropdown_value):
            """Sync dropdown selection with URL parameter on page load."""
            import urllib.parse

            if not url_search:
                return no_update

            # Parse URL query parameters
            params = urllib.parse.parse_qs(url_search.lstrip("?"))
            url_map_id = params.get("map_id", [None])[0]

            if not url_map_id:
                return no_update

            # If dropdown already shows the correct map, no update needed
            if url_map_id == current_dropdown_value:
                return no_update

            # Verify the requested map exists in available maps
            valid_map_ids = [m.get("id") for m in available_maps] if available_maps else []
            if url_map_id not in valid_map_ids:
                logging.warning(f"URL dropdown sync: Invalid map_id {url_map_id}")
                return no_update

            logging.debug(f"URL dropdown sync: Setting dropdown to {url_map_id}")
            return url_map_id

        # Callback to handle URL-based map loading on page load
        @app.callback(
            [
                Output("map-display", "figure", allow_duplicate=True),
                Output("map-config-store", "data", allow_duplicate=True),
            ],
            [Input("url-location", "search")],
            [
                State("map-config-store", "data"),
                State("map-display", "figure"),
                State("available-maps-store", "data"),
                State("map-selector-dropdown", "value"),
            ],
            prevent_initial_call="initial_duplicate",
        )
        def handle_url_map_switch(url_search, config, current_fig, available_maps, _dropdown_value):
            """Handle map switching when URL contains map_id parameter."""
            import urllib.parse

            if not url_search:
                return no_update, no_update

            # Parse URL query parameters
            params = urllib.parse.parse_qs(url_search.lstrip("?"))
            url_map_id = params.get("map_id", [None])[0]

            if not url_map_id:
                return no_update, no_update

            current_map_id = config.get("map_id")

            # If URL map_id matches current config map, no action needed
            if url_map_id == current_map_id:
                logging.debug(f"URL map switch: URL map_id {url_map_id} matches config, no switch needed")
                return no_update, no_update

            # ALWAYS fetch fresh map list from API to avoid stale cache issues after clone/delete
            # This bypasses the available_maps store which may be outdated
            site_id_local = config.get("site_id")
            if not site_id_local:
                logging.warning("URL map switch: site_id not available in config")
                return no_update, no_update

            try:
                # Fetch fresh map list from API
                fresh_maps_response = mistapi.api.v1.sites.maps.listSiteMaps(api_session_ref, site_id=site_id_local)
                if fresh_maps_response.status_code == 200:
                    fresh_maps = fresh_maps_response.data if fresh_maps_response.data else []
                    valid_map_ids = [m.get("id") for m in fresh_maps]
                else:
                    # Fallback to store if API call fails
                    logging.warning("URL map switch: Could not fetch fresh maps, using store")
                    valid_map_ids = [m.get("id") for m in available_maps]
            except Exception as fetch_err:
                logging.warning(f"URL map switch: Error fetching fresh maps: {fetch_err}")
                valid_map_ids = [m.get("id") for m in available_maps]

            if url_map_id not in valid_map_ids:
                logging.warning(f"URL map switch: Invalid map_id {url_map_id}")
                return no_update, no_update

            logging.info(f"URL map switch: Loading map {url_map_id} (current: {current_map_id})")

            try:
                # Fetch the new map data (site_id_local already set above)
                map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session_ref, site_id_local, url_map_id)

                if map_response.status_code != 200:
                    logging.error(f"URL map switch: Failed to fetch map - HTTP {map_response.status_code}")
                    return no_update, no_update

                new_map_data = map_response.data
                new_map_name = new_map_data.get("name", "Unnamed")
                new_map_width = new_map_data.get("width", 1000)
                new_map_height = new_map_data.get("height", 1000)
                new_ppm = new_map_data.get("ppm") or 10  # Use 10 if ppm is 0 or None

                logging.info(
                    f"URL map switch: Loaded map '{new_map_name}' ({new_map_width}x{new_map_height}, ppm={new_ppm})"
                )

                # Fetch devices for new map
                devices_response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                    api_session_ref, site_id=site_id_local, limit=1000
                )
                new_devices = []
                if devices_response.status_code == 200:
                    all_devices = mistapi.get_all(response=devices_response, mist_session=api_session_ref)
                    new_devices = [d for d in all_devices if d.get("map_id") == url_map_id]

                # Fetch zones for new map
                zones_response = mistapi.api.v1.sites.zones.listSiteZones(api_session_ref, site_id=site_id_local)
                new_zones = []
                if zones_response.status_code == 200:
                    all_zones = mistapi.get_all(response=zones_response, mist_session=api_session_ref)
                    new_zones = [z for z in all_zones if z.get("map_id") == url_map_id]

                # Fetch clients for new map
                clients_response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
                    api_session_ref, site_id=site_id_local, limit=1000
                )
                new_clients = []
                if clients_response.status_code == 200:
                    all_clients = mistapi.get_all(response=clients_response, mist_session=api_session_ref)
                    new_clients = [c for c in all_clients if c.get("map_id") == url_map_id and c.get("x") is not None]

                logging.info(
                    f"URL map switch: Found {len(new_devices)} devices, "
                    f"{len(new_zones)} zones, {len(new_clients)} clients"
                )

                # Build new figure with plotly
                import plotly.graph_objects as go

                new_fig = go.Figure()

                # Add map image
                if "url" in new_map_data:
                    new_fig.add_layout_image(
                        source=new_map_data["url"],
                        x=0,
                        y=0,
                        sizex=new_map_width,
                        sizey=new_map_height,
                        xref="x",
                        yref="y",
                        sizing="stretch",
                        layer="below",
                    )

                # Add walls
                wall_path = new_map_data.get("wall_path", {})
                if "nodes" in wall_path:
                    node_lookup = {}
                    for node in wall_path["nodes"]:
                        node_name = node.get("name", "")
                        pos = node.get("position", {})
                        if node_name and pos:
                            node_lookup[node_name] = pos

                    for node in wall_path["nodes"]:
                        node_pos = node.get("position", {})
                        edges = node.get("edges", {})
                        for edge_name in edges.keys():
                            if edge_name in node_lookup:
                                target_pos = node_lookup[edge_name]
                                new_fig.add_trace(
                                    go.Scatter(
                                        x=[node_pos.get("x", 0), target_pos.get("x", 0)],
                                        y=[node_pos.get("y", 0), target_pos.get("y", 0)],
                                        mode="lines",
                                        name="Walls",
                                        line=dict(color="#ff3333", width=4),
                                        showlegend=False,
                                        hoverinfo="skip",
                                    )
                                )

                # Add wayfinding paths
                wf_path = new_map_data.get("wayfinding_path", {})
                if "nodes" in wf_path:
                    wf_node_lookup = {}
                    for node in wf_path["nodes"]:
                        node_name = node.get("name", "")
                        pos = node.get("position", {})
                        if node_name and pos:
                            wf_node_lookup[node_name] = pos

                    for node in wf_path["nodes"]:
                        node_pos = node.get("position", {})
                        edges = node.get("edges", {})
                        for edge_name in edges.keys():
                            if edge_name in wf_node_lookup:
                                target_pos = wf_node_lookup[edge_name]
                                new_fig.add_trace(
                                    go.Scatter(
                                        x=[node_pos.get("x", 0), target_pos.get("x", 0)],
                                        y=[node_pos.get("y", 0), target_pos.get("y", 0)],
                                        mode="lines+markers",
                                        name="Wayfinding",
                                        line=dict(color="#4488ff", width=3, dash="dash"),
                                        marker=dict(size=8, color="#4488ff"),
                                        visible=True,
                                        showlegend=False,
                                        hoverinfo="skip",
                                    )
                                )

                # Add zones with varied colors (matching original)
                zone_colors = [
                    ("rgba(255,165,0,0.3)", "#ffa500"),  # Orange
                    ("rgba(0,255,255,0.3)", "#00ffff"),  # Cyan
                    ("rgba(255,0,255,0.3)", "#ff00ff"),  # Magenta
                    ("rgba(255,255,0,0.3)", "#ffff00"),  # Yellow
                    ("rgba(0,255,0,0.3)", "#00ff00"),  # Green
                    ("rgba(128,0,255,0.3)", "#8000ff"),  # Purple
                    ("rgba(255,0,0,0.3)", "#ff0000"),  # Red
                    ("rgba(0,128,255,0.3)", "#0080ff"),  # Blue
                ]
                for idx, zone in enumerate(new_zones):
                    vertices = zone.get("vertices", [])
                    if len(vertices) >= 3:
                        zone_x = [v.get("x", 0) for v in vertices] + [vertices[0].get("x", 0)]
                        zone_y = [v.get("y", 0) for v in vertices] + [vertices[0].get("y", 0)]
                        fill_color, border_color = zone_colors[idx % len(zone_colors)]
                        zone_name = zone.get("name", f"Zone {idx + 1}")
                        new_fig.add_trace(
                            go.Scatter(
                                x=zone_x,
                                y=zone_y,
                                mode="lines",
                                fill="toself",
                                fillcolor=fill_color,
                                line=dict(color=border_color, width=2),
                                name=f"Zone: {zone_name}",
                                showlegend=True,
                                visible=True,
                            )
                        )
                        # Add zone label annotation
                        center_x = sum(v.get("x", 0) for v in vertices) / len(vertices)
                        center_y = sum(v.get("y", 0) for v in vertices) / len(vertices)
                        new_fig.add_annotation(
                            x=center_x,
                            y=center_y,
                            text=f"<b>{zone_name}</b>",
                            showarrow=False,
                            font=dict(size=10, color="white", family="Arial Black"),
                            bgcolor=(
                                border_color.replace(")", ",0.8)").replace("rgb", "rgba")
                                if "rgb" in border_color
                                else border_color
                            ),
                            bordercolor="white",
                            borderwidth=1,
                            borderpad=3,
                            xanchor="center",
                            yanchor="middle",
                            name=f"Zone: {zone_name} Label",
                        )

                # Add validation paths if present
                val_paths = new_map_data.get("validation_paths", [])
                for val_path in val_paths:
                    path_name = val_path.get("name", "Validation Path")
                    path_coords = val_path.get("nodes", [])
                    if len(path_coords) >= 2:
                        path_x = [p.get("x", 0) for p in path_coords]
                        path_y = [p.get("y", 0) for p in path_coords]
                        new_fig.add_trace(
                            go.Scatter(
                                x=path_x,
                                y=path_y,
                                mode="lines+markers",
                                name=f"Validation: {path_name}",
                                line=dict(color="#00ff88", width=3, dash="dot"),
                                marker=dict(size=10, color="#00ff88", symbol="circle"),
                                visible=True,
                                showlegend=True,
                            )
                        )

                # Add devices (APs, Switches, Gateways) with status-based colors
                # Device type configurations matching original styling
                device_type_config = {
                    "ap": {
                        "symbol": "triangle-up",
                        "name": "Access Points",
                        "size": 20,
                        "colors": {
                            "connected": "#00ff00",  # Bright green
                            "disconnected": "#ff0000",  # Bright red
                            "upgrading": "#ff8800",  # Orange/amber
                        },
                    },
                    "switch": {
                        "symbol": "square",
                        "name": "Switches",
                        "size": 18,
                        "colors": {
                            "connected": "#00ccff",  # Cyan
                            "disconnected": "#ff0000",  # Bright red
                            "upgrading": "#ff8800",  # Orange/amber
                        },
                    },
                    "gateway": {
                        "symbol": "diamond",
                        "name": "Gateways",
                        "size": 20,
                        "colors": {
                            "connected": "#ff00ff",  # Magenta
                            "disconnected": "#ff0000",  # Bright red
                            "upgrading": "#ff8800",  # Orange/amber
                        },
                    },
                }

                # Group devices by type
                device_types = {"ap": [], "switch": [], "gateway": []}
                for device in new_devices:
                    device_type = device.get("type", "ap")
                    if device.get("x") is not None and device.get("y") is not None:
                        if device_type in device_types:
                            device_types[device_type].append(device)

                # Add traces for each device type
                for device_type, type_cfg in device_type_config.items():
                    type_devices = device_types[device_type]
                    if type_devices:
                        x_coords = [d["x"] for d in type_devices]
                        y_coords = [d["y"] for d in type_devices]
                        names = [d.get("name", d.get("mac", "Unknown")) for d in type_devices]

                        # Determine status and color for each device
                        colors = []
                        hover_texts = []
                        for device in type_devices:
                            status = device.get("status", "disconnected")
                            if device.get("upgrade_status") or device.get("fwupdate", {}).get("progress") is not None:
                                device_status = "upgrading"
                            elif status == "connected":
                                device_status = "connected"
                            else:
                                device_status = "disconnected"
                            colors.append(type_cfg["colors"][device_status])

                            # Build hover text
                            text = f"<b>{device.get('name', 'Unnamed')}</b><br>"
                            text += f"Type: {device.get('type', 'N/A')}<br>"
                            text += f"Model: {device.get('model', 'N/A')}<br>"
                            text += f"MAC: {device.get('mac', 'N/A')}<br>"
                            text += f"Status: <b>{device_status.upper()}</b>"
                            hover_texts.append(text)

                        # Add device markers
                        new_fig.add_trace(
                            go.Scatter(
                                x=x_coords,
                                y=y_coords,
                                mode="markers",
                                name=type_cfg["name"],
                                marker=dict(
                                    symbol=type_cfg["symbol"],
                                    size=type_cfg["size"],
                                    color=colors,
                                    line=dict(color="white", width=2),
                                    opacity=0.9,
                                ),
                                hovertext=hover_texts,
                                hoverinfo="text",
                                visible=True,
                                showlegend=True,
                            )
                        )

                        # Add device name labels
                        for _, (x, y, name, device_color) in enumerate(
                            zip(x_coords, y_coords, names, colors, strict=True)
                        ):
                            new_fig.add_annotation(
                                x=x,
                                y=y - 15,
                                text=f"<b>{name}</b>",
                                showarrow=False,
                                font=dict(size=11, color="white", family="Arial Black"),
                                bgcolor="rgba(0,0,0,0.85)",
                                bordercolor=device_color,
                                borderwidth=2,
                                borderpad=3,
                                xanchor="center",
                                yanchor="bottom",
                                name=f"{type_cfg['name']} Label",
                            )

                        # Add device orientation crosshairs
                        import math

                        for _, (x, y, device, device_color) in enumerate(
                            zip(x_coords, y_coords, type_devices, colors, strict=True)
                        ):
                            orientation = device.get("orientation", 0)
                            crosshair_size = 40

                            # Horizontal line
                            new_fig.add_trace(
                                go.Scatter(
                                    x=[x - crosshair_size, x + crosshair_size],
                                    y=[y, y],
                                    mode="lines",
                                    line=dict(color=device_color, width=3),
                                    name=f"{type_cfg['name']} Orientation",
                                    showlegend=False,
                                    hoverinfo="skip",
                                )
                            )

                            # Vertical line
                            new_fig.add_trace(
                                go.Scatter(
                                    x=[x, x],
                                    y=[y - crosshair_size, y + crosshair_size],
                                    mode="lines",
                                    line=dict(color=device_color, width=3),
                                    name=f"{type_cfg['name']} Orientation",
                                    showlegend=False,
                                    hoverinfo="skip",
                                )
                            )

                            # Directional dot showing orientation
                            dot_distance = 50
                            math_angle = 90 - orientation
                            rad = math.radians(math_angle)
                            dot_x = x + dot_distance * math.cos(rad)
                            dot_y = y - dot_distance * math.sin(rad)

                            new_fig.add_trace(
                                go.Scatter(
                                    x=[dot_x],
                                    y=[dot_y],
                                    mode="markers",
                                    marker=dict(
                                        size=12, color=device_color, symbol="circle", line=dict(color="black", width=2)
                                    ),
                                    name=f"{type_cfg['name']} Orientation",
                                    showlegend=False,
                                    hoverinfo="skip",
                                )
                            )

                # Add virtual beacons (vBeacons)
                vbeacons = new_map_data.get("vbeacons", [])
                if vbeacons:
                    beacon_x, beacon_y, beacon_hover = [], [], []
                    for beacon in vbeacons:
                        x = beacon.get("x")
                        y = beacon.get("y")
                        if x is not None and y is not None:
                            beacon_x.append(x)
                            beacon_y.append(y)
                            hover = "<b>vBeacon</b><br>"
                            hover += f"Name: {beacon.get('name', 'N/A')}<br>"
                            hover += f"UUID: {beacon.get('uuid', 'N/A')}<br>"
                            hover += f"Major: {beacon.get('major', 'N/A')}<br>"
                            hover += f"Minor: {beacon.get('minor', 'N/A')}<br>"
                            hover += f"Power: {beacon.get('power', 'N/A')} dBm"
                            beacon_hover.append(hover)

                    if beacon_x:
                        new_fig.add_trace(
                            go.Scatter(
                                x=beacon_x,
                                y=beacon_y,
                                mode="markers",
                                name="Virtual Beacons",
                                marker=dict(
                                    symbol="diamond",
                                    size=14,
                                    color="#00ffff",
                                    line=dict(color="white", width=2),
                                    opacity=0.9,
                                ),
                                hovertext=beacon_hover,
                                hoverinfo="text",
                                visible=True,
                                showlegend=True,
                            )
                        )

                # Add BLE beacons
                ble_beacons = new_map_data.get("beacons", [])
                if ble_beacons:
                    ble_x, ble_y, ble_hover = [], [], []
                    for beacon in ble_beacons:
                        x = beacon.get("x")
                        y = beacon.get("y")
                        if x is not None and y is not None:
                            ble_x.append(x)
                            ble_y.append(y)
                            hover = "<b>BLE Beacon</b><br>"
                            hover += f"Name: {beacon.get('name', 'N/A')}<br>"
                            hover += f"MAC: {beacon.get('mac', 'N/A')}<br>"
                            hover += f"Type: {beacon.get('type', 'N/A')}"
                            ble_hover.append(hover)

                    if ble_x:
                        new_fig.add_trace(
                            go.Scatter(
                                x=ble_x,
                                y=ble_y,
                                mode="markers",
                                name="BLE Beacons",
                                marker=dict(
                                    symbol="hexagon",
                                    size=12,
                                    color="#ff69b4",
                                    line=dict(color="white", width=2),
                                    opacity=0.9,
                                ),
                                hovertext=ble_hover,
                                hoverinfo="text",
                                visible=True,
                                showlegend=True,
                            )
                        )

                # Add clients
                client_x, client_y, client_hover, client_names = [], [], [], []
                for client in new_clients:
                    x = client.get("x")
                    y = client.get("y")
                    if x is not None and y is not None:
                        client_x.append(x)
                        client_y.append(y)

                        # Use hostname or MAC for label
                        client_mac = client.get("mac", "unknown")
                        hostname = client.get("hostname", "")
                        label = hostname if hostname else client_mac[-8:]
                        client_names.append(label)

                        # Build hover text with client details
                        hover = "<b>Client</b><br>"
                        hover += f"MAC: {client.get('mac', 'N/A')}<br>"
                        hover += f"Hostname: {client.get('hostname', 'N/A')}<br>"
                        hover += f"SSID: {client.get('ssid', 'N/A')}<br>"
                        hover += f"AP: {client.get('ap_name', 'N/A')}<br>"
                        hover += f"Band: {client.get('band', 'N/A')}<br>"
                        hover += f"Signal: {client.get('rssi', 'N/A')} dBm<br>"
                        hover += f"Position: ({x}, {y})"
                        client_hover.append(hover)

                if client_x:
                    # Add client markers with proper styling
                    new_fig.add_trace(
                        go.Scatter(
                            x=client_x,
                            y=client_y,
                            mode="markers",
                            name="Clients",
                            marker=dict(
                                symbol="circle",
                                size=12,
                                color="#00ff00",  # Bright green
                                line=dict(color="white", width=2),
                                opacity=0.9,
                            ),
                            hovertext=client_hover,
                            hoverinfo="text",
                            visible=True,
                            showlegend=True,
                        )
                    )

                    # Add client name labels with shadow effect using annotations
                    for _, (x, y, name) in enumerate(zip(client_x, client_y, client_names, strict=True)):
                        new_fig.add_annotation(
                            x=x,
                            y=y - 10,  # Position above marker
                            text=f"<b>{name}</b>",
                            showarrow=False,
                            font=dict(size=9, color="white", family="Arial"),
                            bgcolor="rgba(0,128,0,0.9)",
                            bordercolor="white",
                            borderwidth=1,
                            borderpad=2,
                            xanchor="center",
                            yanchor="bottom",
                            name="Clients Label",  # For toggle control
                        )

                # Add map origin marker
                origin = new_map_data.get("origin", {}) or {}
                origin_x = origin.get("x", 0)
                origin_y = origin.get("y", 0)
                new_fig.add_trace(
                    go.Scatter(
                        x=[origin_x],
                        y=[origin_y],
                        mode="markers+text",
                        name="Map Origin",
                        marker=dict(symbol="x", size=20, color="yellow", line=dict(width=3, color="black")),
                        text=["Origin"],
                        textposition="top center",
                        textfont=dict(color="yellow", size=10),
                        visible=False,  # Hidden by default, toggle to show
                        showlegend=True,
                    )
                )

                # Fetch and add RF coverage heatmap using raw API endpoint
                try:
                    site_id_for_coverage = config.get("site_id")
                    if site_id_for_coverage:
                        coverage_url = f"/api/v1/sites/{site_id_for_coverage}/location/coverage"
                        coverage_params = {
                            "resolution": "fine",
                            "duration": "1d",
                            "map_id": url_map_id,
                            "type": "client",
                            "from_apollo": "true",
                        }
                        logging.info(f"URL map switch: Fetching RF coverage for map {url_map_id}")
                        coverage_response = api_session_ref.mist_get(coverage_url, query=coverage_params)

                        if coverage_response.status_code == 200:
                            coverage_data = coverage_response.data
                            # Check for error response structure
                            if isinstance(coverage_data, dict) and "exception" in coverage_data:
                                logging.warning(
                                    f"URL map switch: RF Coverage backend error - "
                                    f"{str(coverage_data.get('exception', ''))[:200]}"
                                )
                                coverage_data = None

                            if coverage_data:
                                results = coverage_data.get("results", [])
                                result_def = coverage_data.get("result_def", [])
                                logging.info(f"URL map switch: RF coverage API returned {len(results)} grid points")
                                if results and result_def:
                                    # Find indices for data fields from result_def
                                    try:
                                        x_idx = result_def.index("x")
                                        y_idx = result_def.index("y")
                                        max_rssi_idx = result_def.index("max_rssi")
                                    except ValueError as idx_error:
                                        logging.warning(
                                            f"URL map switch: Coverage data missing expected fields "
                                            f"in result_def: {idx_error}"
                                        )
                                        x_idx, y_idx, max_rssi_idx = 0, 1, 4  # Fallback indices

                                    # Build grid data - results is list of lists, not list of dicts
                                    grid_data = {}
                                    for item in results:
                                        if not isinstance(item, (list, tuple)) or len(item) <= max(
                                            x_idx, y_idx, max_rssi_idx
                                        ):
                                            continue
                                        x_m = item[x_idx]
                                        y_m = item[y_idx]
                                        max_rssi = item[max_rssi_idx]
                                        if x_m is None or y_m is None or max_rssi is None:
                                            continue
                                        pixel_x = x_m * new_ppm
                                        pixel_y = y_m * new_ppm
                                        grid_data[(pixel_x, pixel_y)] = max_rssi

                                    if grid_data:
                                        all_rssi = list(grid_data.values())
                                        min_rssi = min(all_rssi)
                                        max_rssi_val = max(all_rssi)

                                        unique_x = sorted(set(x for x, y in grid_data.keys()))
                                        unique_y = sorted(set(y for x, y in grid_data.keys()))

                                        z_matrix = []
                                        for y_val in unique_y:
                                            row = [grid_data.get((x_val, y_val), None) for x_val in unique_x]
                                            z_matrix.append(row)

                                        colorscale = [
                                            [0.0, "rgb(0, 0, 255)"],
                                            [0.33, "rgb(0, 255, 0)"],
                                            [0.50, "rgb(255, 255, 0)"],
                                            [0.67, "rgb(255, 165, 0)"],
                                            [1.0, "rgb(255, 0, 0)"],
                                        ]

                                        new_fig.add_trace(
                                            go.Heatmap(
                                                x=unique_x,
                                                y=unique_y,
                                                z=z_matrix,
                                                colorscale=colorscale,
                                                zmin=min_rssi,
                                                zmax=max_rssi_val,
                                                opacity=0.5,
                                                name="RF Coverage",
                                                visible=False,  # Hidden by default
                                                showscale=True,
                                                colorbar=dict(
                                                    title=dict(
                                                        text="RSSI (dBm)",
                                                        side="right",
                                                        font=dict(size=12, color="white"),
                                                    ),
                                                    thickness=20,
                                                    len=0.5,
                                                    y=0.95,
                                                    yanchor="top",
                                                    tickfont=dict(size=10, color="white"),
                                                ),
                                                connectgaps=True,
                                                zsmooth="best",
                                            )
                                        )
                                        logging.info(
                                            f"URL map switch: Added RF coverage heatmap with "
                                            f"{len(grid_data)} cells, RSSI range {min_rssi} to {max_rssi_val} dBm"
                                        )
                                    else:
                                        logging.warning(
                                            f"URL map switch: RF coverage - no valid grid data "
                                            f"after processing {len(results)} points"
                                        )
                                else:
                                    logging.info(
                                        "URL map switch: No RF coverage data available for this map (empty results)"
                                    )
                        else:
                            logging.warning(
                                f"URL map switch: RF coverage API returned HTTP {coverage_response.status_code}"
                            )
                    else:
                        logging.warning("URL map switch: Cannot fetch RF coverage - site_id is None")
                except Exception as rf_error:
                    logging.warning(f"URL map switch: Could not load RF coverage - {rf_error}", exc_info=True)

                # Update layout
                new_fig.update_layout(
                    title=dict(text=f"Map: {new_map_name}", font=dict(color="white")),
                    xaxis=dict(
                        range=[0, new_map_width],
                        showgrid=False,
                        zeroline=False,
                        scaleanchor="y",
                        scaleratio=1,
                        constrain="domain",
                    ),
                    yaxis=dict(range=[new_map_height, 0], showgrid=False, zeroline=False, constrain="domain"),
                    plot_bgcolor="#1a1a1a",
                    paper_bgcolor="#1a1a1a",
                    font=dict(color="#e0e0e0"),
                    showlegend=True,
                    legend=dict(bgcolor="rgba(0,0,0,0.7)", font=dict(color="white")),
                    margin=dict(l=50, r=50, t=50, b=50),
                )

                # Update config - preserve site_id from original config
                new_config = config.copy()
                new_config["map_id"] = url_map_id
                new_config["map_name"] = new_map_name
                new_config["ppm"] = new_ppm
                new_config["map_width"] = new_map_width
                new_config["map_height"] = new_map_height
                # site_id stays the same since we're switching maps within the same site

                logging.info(f"URL map switch: Successfully switched to map '{new_map_name}'")
                logging.debug(
                    f"URL map switch: Returning new_config with "
                    f"site_id={new_config.get('site_id')}, map_id={new_config.get('map_id')}"
                )

                return new_fig, new_config

            except Exception as e:
                logging.error(f"URL map switch: Error loading map - {e}", exc_info=True)
                return no_update, no_update

        # Callback for layer toggle
        @app.callback(
            Output("map-display", "figure"),
            [
                Input("layer-toggle", "value"),
                Input("beacon-toggle", "value"),
                Input("client-toggle", "value"),
                Input("device-toggle", "value"),
                Input("filter-toggle", "value"),
            ],
            State("map-display", "figure"),
        )
        def toggle_layers(infra_layers, beacon_layers, client_layers, device_layers, filter_layers, current_fig):
            # Combine all layer selections
            all_layers = (
                (infra_layers or [])
                + (beacon_layers or [])
                + (client_layers or [])
                + (device_layers or [])
                + (filter_layers or [])
            )

            # Toggle traces (markers, lines, shapes)
            for trace in current_fig["data"]:
                trace_name = trace.get("name", "").lower()

                # Infrastructure
                if "wall" in trace_name:
                    trace["visible"] = "walls" in all_layers
                elif "wayfinding" in trace_name:
                    trace["visible"] = "wayfinding" in all_layers
                elif "zone" in trace_name:
                    trace["visible"] = "zones" in all_layers
                elif "validation" in trace_name:
                    trace["visible"] = "validation" in all_layers
                elif "rf coverage" in trace_name:
                    trace["visible"] = "rf_heatmap" in all_layers
                elif "map origin" in trace_name:
                    trace["visible"] = "origin" in all_layers

                # Beacons
                elif "vbeacon" in trace_name or "virtual beacon" in trace_name:
                    trace["visible"] = "vbeacons" in all_layers
                elif "ble beacon" in trace_name or trace_name.startswith("beacon "):
                    trace["visible"] = "ble_beacons" in all_layers

                # Clients (with WiFi/Wired filtering)
                elif "wifi client" in trace_name:
                    trace["visible"] = "wifi_clients" in all_layers
                elif "wired client" in trace_name:
                    trace["visible"] = "wired_clients" in all_layers
                elif "client" in trace_name:  # Generic clients (fallback)
                    trace["visible"] = "wifi_clients" in all_layers or "wired_clients" in all_layers
                elif "client-ap link" in trace_name:
                    trace["visible"] = "show_client_ap" in all_layers

                # Mesh links
                elif "mesh link" in trace_name:
                    trace["visible"] = "mesh_links" in all_layers

                # Beacon coverage
                elif "vbeacon coverage" in trace_name:
                    trace["visible"] = "vbeacon_coverage" in all_layers

                # Devices and their orientation indicators
                elif "ap" in trace_name or "access point" in trace_name:
                    trace["visible"] = "aps" in all_layers
                elif "switch" in trace_name:
                    trace["visible"] = "switches" in all_layers
                elif "gateway" in trace_name:
                    trace["visible"] = "gateways" in all_layers

            # Toggle annotations (text labels)
            for annotation in current_fig.get("layout", {}).get("annotations", []):
                annotation_name = annotation.get("name", "").lower()

                # Zone labels
                if "zone label" in annotation_name:
                    annotation["visible"] = "zones" in all_layers

                # Device labels
                elif "access points label" in annotation_name:
                    annotation["visible"] = "aps" in all_layers
                elif "switches label" in annotation_name:
                    annotation["visible"] = "switches" in all_layers
                elif "gateways label" in annotation_name:
                    annotation["visible"] = "gateways" in all_layers

                # Client labels
                elif "wifi clients label" in annotation_name:
                    annotation["visible"] = "wifi_clients" in all_layers
                elif "wired clients label" in annotation_name:
                    annotation["visible"] = "wired_clients" in all_layers
                elif "clients label" in annotation_name:  # Generic clients (fallback)
                    annotation["visible"] = "wifi_clients" in all_layers or "wired_clients" in all_layers

                # Beacon labels
                elif "virtual beacons label" in annotation_name:
                    annotation["visible"] = "vbeacons" in all_layers
                elif "ble beacons label" in annotation_name:
                    annotation["visible"] = "ble_beacons" in all_layers

            return current_fig

        # Callback for click events - enhanced device details display
        @app.callback(Output("click-data", "children"), Input("map-display", "clickData"))
        def display_click_data(clickData):
            if clickData is None:
                return [
                    html.H3("Device Info"),
                    html.P("Click a device for details", style={"color": "#888", "fontStyle": "italic"}),
                ]

            point = clickData["points"][0]
            hover_text = point.get("hovertext", "")

            # Parse hover text to extract device info
            details = []
            if hover_text:
                lines = hover_text.split("<br>")
                for line in lines:
                    if line.strip():
                        details.append(
                            html.P(
                                line.replace("<b>", "").replace("</b>", ""),
                                className="device-detail" if "Type:" in line else None,
                            )
                        )

            return [html.H3("Device Details"), html.Div(details if details else [html.P("No device data available")])]

        # Callback to add multi-unit labels to drawn shapes
        @app.callback(
            Output("map-display", "figure", allow_duplicate=True),
            Input("map-display", "relayoutData"),
            State("map-display", "figure"),
            prevent_initial_call=True,
        )
        def update_shape_labels(relayoutData, current_fig):
            """Add multi-unit measurement labels to drawn shapes."""
            if not relayoutData:
                return current_fig

            # Get current PPM from figure metadata (may have been updated by user)
            current_ppm = current_fig.get("layout", {}).get("meta", {}).get("ppm", ppm)

            # Check if a new shape was added
            shapes = current_fig.get("layout", {}).get("shapes", [])
            if shapes and len(shapes) > 0:
                # Get the last shape (newly drawn)
                for _, shape in enumerate(shapes):
                    if shape.get("type") == "line":
                        # Calculate length in pixels
                        x0, y0 = shape.get("x0", 0), shape.get("y0", 0)
                        x1, y1 = shape.get("x1", 0), shape.get("y1", 0)
                        length_px = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5

                        # Convert to meters and feet using current PPM
                        length_m = length_px / current_ppm if current_ppm > 0 else 0
                        length_ft = length_m * 3.28084

                        # Create annotation with multi-unit label
                        annotation = dict(
                            x=(x0 + x1) / 2,
                            y=(y0 + y1) / 2,
                            text=f"<b>{length_px:.1f} px</b><br>{length_ft:.2f} ft<br>{length_m:.2f} m",
                            showarrow=False,
                            font=dict(size=12, color="cyan", family="Arial Black"),
                            bgcolor="rgba(0,0,0,0.7)",
                            bordercolor="cyan",
                            borderwidth=2,
                            borderpad=4,
                        )

                        # Add to annotations
                        if "annotations" not in current_fig["layout"]:
                            current_fig["layout"]["annotations"] = []
                        current_fig["layout"]["annotations"].append(annotation)

            return current_fig

        # Callback to set scale from user input
        @app.callback(
            [Output("scale-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("set-scale-button", "n_clicks"),
            [State("scale-length-input", "value"), State("map-display", "figure")],
            prevent_initial_call=True,
        )
        def set_scale(n_clicks, actual_length_m, current_fig):
            """Calculate and update PPM based on drawn line and known length."""
            if not n_clicks or not actual_length_m or actual_length_m <= 0:
                return "[!] Please enter a valid length in meters", current_fig

            # Find the last line shape
            shapes = current_fig.get("layout", {}).get("shapes", [])
            last_line = None
            for shape in reversed(shapes):
                if shape.get("type") == "line":
                    last_line = shape
                    break

            if not last_line:
                return "[!] Please draw a line first using the ruler tool", current_fig

            # Calculate line length in pixels
            x0, y0 = last_line.get("x0", 0), last_line.get("y0", 0)
            x1, y1 = last_line.get("x1", 0), last_line.get("y1", 0)
            length_px = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5

            # Calculate new PPM
            new_ppm = length_px / actual_length_m

            # Update PPM in figure metadata
            if "meta" not in current_fig["layout"]:
                current_fig["layout"]["meta"] = {}
            current_fig["layout"]["meta"]["ppm"] = new_ppm

            # Update all existing measurement annotations with new PPM
            if "annotations" in current_fig["layout"]:
                for ann_idx, annotation in enumerate(current_fig["layout"]["annotations"]):
                    # Check if this is a measurement annotation (has px/ft/m format)
                    if "px" in annotation.get("text", ""):
                        # Find corresponding shape
                        for _, shape in enumerate(shapes):
                            if shape.get("type") == "line":
                                sx0, sy0 = shape.get("x0", 0), shape.get("y0", 0)
                                sx1, sy1 = shape.get("x1", 0), shape.get("y1", 0)
                                shape_px = ((sx1 - sx0) ** 2 + (sy1 - sy0) ** 2) ** 0.5
                                shape_m = shape_px / new_ppm
                                shape_ft = shape_m * 3.28084

                                # Update annotation text
                                annotation_text = f"<b>{shape_px:.1f} px</b><br>{shape_ft:.2f} ft<br>{shape_m:.2f} m"
                                current_fig["layout"]["annotations"][ann_idx]["text"] = annotation_text
                                break

            status_msg = f"[OK] Scale set! New PPM: {new_ppm:.2f} ({actual_length_m:.2f}m = {length_px:.1f}px)"
            logging.info(f"Map scale updated: PPM {ppm} -> {new_ppm:.2f} (user calibration: {actual_length_m}m)")

            return status_msg, current_fig

        # Callback to handle origin setting mode
        @app.callback(
            Output("origin-mode-button", "style"),
            Input("origin-mode-button", "n_clicks"),
            State("origin-mode-button", "style"),
            prevent_initial_call=True,
        )
        def toggle_origin_mode(n_clicks, current_style):
            """Toggle origin setting mode on/off with visual feedback."""
            if n_clicks % 2 == 1:  # Odd clicks = mode active
                current_style["backgroundColor"] = "#667eea"
                current_style["border"] = "2px solid #00bfff"
                return current_style
            else:  # Even clicks = mode inactive
                current_style["backgroundColor"] = "#3d3d3d"
                current_style["border"] = "1px solid #667eea"
                return current_style

        # Callback to set origin from map click
        @app.callback(
            [Output("origin-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("map-display", "clickData"),
            [State("origin-mode-button", "n_clicks"), State("map-display", "figure")],
            prevent_initial_call=True,
        )
        def set_origin_from_click(clickData, mode_clicks, current_fig):
            """Set origin point when map is clicked in origin-setting mode."""
            # Check if origin mode is active (odd number of clicks)
            if not mode_clicks or mode_clicks % 2 == 0:
                # Mode not active - return current status
                current_origin_x = current_fig.get("layout", {}).get("meta", {}).get("origin_x", 0)
                current_origin_y = current_fig.get("layout", {}).get("meta", {}).get("origin_y", 0)
                return [
                    html.P(
                        f"Current: ({current_origin_x}, {current_origin_y})",
                        style={"fontSize": "11px", "color": "#888", "margin": "4px 0"},
                    )
                ], current_fig

            if not clickData:
                return [
                    html.P("Click map to set origin", style={"fontSize": "11px", "color": "#ff8800", "margin": "4px 0"})
                ], current_fig

            # Get clicked coordinates
            point = clickData["points"][0]
            new_origin_x = point["x"]
            new_origin_y = point["y"]

            # Update origin in figure metadata
            if "meta" not in current_fig["layout"]:
                current_fig["layout"]["meta"] = {}
            current_fig["layout"]["meta"]["origin_x"] = new_origin_x
            current_fig["layout"]["meta"]["origin_y"] = new_origin_y

            # Find and update origin crosshair traces
            crosshair_size = 40
            for trace in current_fig["data"]:
                if trace.get("name") == "Origin":
                    # Update horizontal line
                    trace["x"] = [new_origin_x - crosshair_size, new_origin_x + crosshair_size]
                    trace["y"] = [new_origin_y, new_origin_y]
                    trace["hovertext"] = f"Origin: ({new_origin_x:.1f}, {new_origin_y:.1f})"
                elif trace.get("name") == "Origin Point":
                    # Update center dot
                    trace["x"] = [new_origin_x]
                    trace["y"] = [new_origin_y]
                    trace["hovertext"] = f"Origin: ({new_origin_x:.1f}, {new_origin_y:.1f})"
                elif "hovertext" in trace and "Origin:" in str(trace.get("hovertext", "")):
                    # Update vertical line (no name but has Origin hovertext)
                    if trace.get("mode") == "lines" and not trace.get("showlegend"):
                        trace["x"] = [new_origin_x, new_origin_x]
                        trace["y"] = [new_origin_y - crosshair_size, new_origin_y + crosshair_size]
                        trace["hovertext"] = f"Origin: ({new_origin_x:.1f}, {new_origin_y:.1f})"

            status = [
                html.P(
                    f"[OK] Origin set: ({new_origin_x:.1f}, {new_origin_y:.1f})",
                    style={"fontSize": "11px", "color": "#00ff00", "margin": "4px 0"},
                ),
                html.P(
                    "Click button again to exit mode", style={"fontSize": "10px", "color": "#888", "margin": "4px 0"}
                ),
            ]

            logging.info(f"Map origin updated to ({new_origin_x:.1f}, {new_origin_y:.1f})")
            return status, current_fig

        # Callback to show/hide zone name input based on drawing mode
        @app.callback(
            Output("zone-name-container", "style"), Input("drawing-mode-dropdown", "value"), prevent_initial_call=True
        )
        def toggle_zone_name_input(mode):
            """Show zone name input only when zone mode is selected."""
            if mode == "zone":
                return {"display": "block", "marginBottom": "10px"}
            return {"display": "none"}

        # Callback to handle shape saving to Mist API
        @app.callback(
            [Output("drawing-tool-status", "children"), Output("cache-bust-store", "data", allow_duplicate=True)],
            [
                Input("save-shape-btn", "n_clicks"),
                Input("clear-drawings-btn", "n_clicks"),
                Input("delete-paths-btn", "n_clicks"),
                Input("delete-wayfinding-btn", "n_clicks"),
                Input("delete-walls-btn", "n_clicks"),
                Input("delete-zones-btn", "n_clicks"),
            ],
            [
                State("drawing-mode-dropdown", "value"),
                State("zone-name-input", "value"),
                State("map-display", "figure"),
                State("map-config-store", "data"),
                State("cache-bust-store", "data"),
            ],
            prevent_initial_call=True,
        )
        def handle_drawing_tools(
            _save_clicks,
            _clear_clicks,
            del_path_clicks,
            _del_wayfinding_clicks,
            del_wall_clicks,
            _del_zone_clicks,
            drawing_mode,
            zone_name,
            current_fig,
            config,
            cache_bust_data,
        ):
            """Handle drawing tool actions - save shapes to Mist or delete from Mist."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return "", no_update

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            logging.info(
                f"Drawing tools callback triggered: button_id={button_id}, "
                f"del_path_clicks={del_path_clicks}, del_wall_clicks={del_wall_clicks}"
            )

            # Get config values
            config_site_id = config.get("site_id") if config else site_id
            config_map_id = config.get("map_id") if config else map_id
            config_ppm = config.get("ppm", ppm) if config else ppm

            # Helper to increment cache-bust trigger for forcing map reload
            current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0

            if button_id == "clear-drawings-btn":
                # This just clears local drawings, not Mist data
                msg = "Use the eraser tool in the toolbar to clear drawings from the map"
                logging.info("Drawing tool: Clear local drawings requested")
                return html.Span(msg, style={"color": "#ffc107"}), no_update

            elif button_id == "save-shape-btn":
                # Get shapes from figure
                shapes = current_fig.get("layout", {}).get("shapes", [])
                if not shapes:
                    return (
                        html.Span("No shapes drawn. Use toolbar to draw first.", style={"color": "#ff6666"}),
                        no_update,
                    )

                # Get the last shape
                last_shape = shapes[-1]
                shape_type = last_shape.get("type", "unknown")

                try:
                    if drawing_mode == "zone":
                        # Save as zone via zones API
                        if not zone_name:
                            return html.Span("Please enter a zone name first", style={"color": "#ff6666"}), no_update

                        if shape_type == "rect":
                            # Convert rectangle to vertices (4 corners)
                            x0 = last_shape.get("x0", 0) / config_ppm  # Convert pixels to meters
                            y0 = last_shape.get("y0", 0) / config_ppm
                            x1 = last_shape.get("x1", 0) / config_ppm
                            y1 = last_shape.get("y1", 0) / config_ppm

                            vertices = [{"x": x0, "y": y0}, {"x": x1, "y": y0}, {"x": x1, "y": y1}, {"x": x0, "y": y1}]

                            zone_data = {"name": zone_name, "map_id": config_map_id, "vertices": vertices}

                            # Call Mist API to create zone
                            response = mistapi.api.v1.sites.zones.createSiteZone(
                                api_session_ref, config_site_id, zone_data
                            )

                            if hasattr(response, "status_code") and response.status_code in [200, 201]:
                                logging.info(f"Drawing tool: Zone '{zone_name}' created successfully")
                                return html.Span(
                                    f"Zone '{zone_name}' saved to Mist!",
                                    style={"color": "#28a745", "fontWeight": "bold"},
                                ), {"trigger": current_trigger + 1}
                            else:
                                error_msg = getattr(response, "text", str(response))
                                logging.error(f"Drawing tool: Failed to create zone - {error_msg}")
                                return (
                                    html.Span(f"Failed to save zone: {error_msg[:50]}", style={"color": "#ff4444"}),
                                    no_update,
                                )
                        else:
                            return (
                                html.Span(
                                    "Zones require rectangle shapes. Use Draw Rectangle tool.",
                                    style={"color": "#ff6666"},
                                ),
                                no_update,
                            )

                    elif drawing_mode == "wall":
                        # Save wall path via updateSiteMap
                        # NOTE: wall_path uses PIXEL coordinates matching the map image, NOT meters
                        if shape_type == "line":
                            # Coordinates from Plotly are already in pixels - do NOT divide by PPM
                            x0 = last_shape.get("x0", 0)
                            y0 = last_shape.get("y0", 0)
                            x1 = last_shape.get("x1", 0)
                            y1 = last_shape.get("y1", 0)

                            logging.info(
                                f"Drawing tool: Saving wall segment from "
                                f"({x0:.1f}, {y0:.1f}) to ({x1:.1f}, {y1:.1f}) pixels"
                            )

                            # Get existing map data first
                            map_response = mistapi.api.v1.sites.maps.getSiteMap(
                                api_session_ref, config_site_id, config_map_id
                            )
                            existing_wall_path = {}
                            if hasattr(map_response, "data"):
                                existing_wall_path = map_response.data.get("wall_path", {})

                            # Add new wall segment to existing nodes
                            existing_nodes = existing_wall_path.get("nodes", [])
                            node_count = len(existing_nodes)
                            new_nodes = [
                                {
                                    "name": f"W{node_count}",
                                    "position": {"x": x0, "y": y0},
                                    "edges": {f"W{node_count + 1}": "wall"},
                                },
                                {"name": f"W{node_count + 1}", "position": {"x": x1, "y": y1}, "edges": {}},
                            ]
                            existing_nodes.extend(new_nodes)

                            wall_path_data = {
                                "coordinate": existing_wall_path.get("coordinate", "actual"),
                                "nodes": existing_nodes,
                            }

                            update_data = {"wall_path": wall_path_data}

                            response = mistapi.api.v1.sites.maps.updateSiteMap(
                                api_session_ref, config_site_id, config_map_id, update_data
                            )

                            if hasattr(response, "status_code") and response.status_code == 200:
                                logging.info("Drawing tool: Wall segment added successfully")
                                return html.Span(
                                    "Wall segment saved to Mist!", style={"color": "#28a745", "fontWeight": "bold"}
                                ), {"trigger": current_trigger + 1}
                            else:
                                error_msg = getattr(response, "text", str(response))
                                logging.error(f"Drawing tool: Failed to save wall - {error_msg}")
                                return (
                                    html.Span(f"Failed to save wall: {error_msg[:50]}", style={"color": "#ff4444"}),
                                    no_update,
                                )
                        else:
                            return (
                                html.Span("Walls require line shapes. Use Draw Line tool.", style={"color": "#ff6666"}),
                                no_update,
                            )

                    elif drawing_mode == "path":
                        # Save sitesurvey path via updateSiteMap
                        if shape_type == "path":
                            # Path shapes have 'path' attribute with SVG path data
                            # This is complex - for now show guidance
                            return (
                                html.Span(
                                    "Path saving requires SVG parsing. Use Mist Portal for complex paths.",
                                    style={"color": "#ff8800"},
                                ),
                                no_update,
                            )
                        elif shape_type == "line":
                            x0 = last_shape.get("x0", 0) / config_ppm
                            y0 = last_shape.get("y0", 0) / config_ppm
                            x1 = last_shape.get("x1", 0) / config_ppm
                            y1 = last_shape.get("y1", 0) / config_ppm

                            # Get existing map data
                            map_response = mistapi.api.v1.sites.maps.getSiteMap(
                                api_session_ref, config_site_id, config_map_id
                            )
                            existing_paths = []
                            if hasattr(map_response, "data"):
                                existing_paths = map_response.data.get("sitesurvey_path", [])

                            # Create new path
                            import uuid

                            new_path = {
                                "id": str(uuid.uuid4()),
                                "name": f"Path_{len(existing_paths) + 1}",
                                "coordinate": "actual",
                                "nodes": [
                                    {"name": "P0", "position": {"x": x0, "y": y0}, "edges": {"P1": "path"}},
                                    {"name": "P1", "position": {"x": x1, "y": y1}, "edges": {}},
                                ],
                            }
                            existing_paths.append(new_path)

                            update_data = {"sitesurvey_path": existing_paths}

                            response = mistapi.api.v1.sites.maps.updateSiteMap(
                                api_session_ref, config_site_id, config_map_id, update_data
                            )

                            if hasattr(response, "status_code") and response.status_code == 200:
                                logging.info("Drawing tool: Validation path added successfully")
                                return html.Span(
                                    "Validation path saved to Mist!", style={"color": "#28a745", "fontWeight": "bold"}
                                ), {"trigger": current_trigger + 1}
                            else:
                                error_msg = getattr(response, "text", str(response))
                                logging.error(f"Drawing tool: Failed to save path - {error_msg}")
                                return (
                                    html.Span(f"Failed to save path: {error_msg[:50]}", style={"color": "#ff4444"}),
                                    no_update,
                                )
                        else:
                            return (
                                html.Span("Paths require line shapes. Use Draw Line tool.", style={"color": "#ff6666"}),
                                no_update,
                            )

                    else:  # measure mode
                        return (
                            html.Span("Measurement mode - shapes not saved to Mist", style={"color": "#888"}),
                            no_update,
                        )

                except Exception as save_error:
                    logging.error(f"Drawing tool: Error saving shape - {save_error}", exc_info=True)
                    return html.Span(f"Error: {str(save_error)[:50]}", style={"color": "#ff4444"}), no_update

            elif button_id == "delete-paths-btn":
                logging.info(
                    f"Drawing tool: Delete paths button clicked - site_id={config_site_id}, map_id={config_map_id}"
                )
                try:
                    # Clear all sitesurvey_path via updateSiteMap
                    update_data = {"sitesurvey_path": []}
                    logging.info(f"Drawing tool: Calling updateSiteMap with {update_data}")
                    response = mistapi.api.v1.sites.maps.updateSiteMap(
                        api_session_ref, config_site_id, config_map_id, update_data
                    )
                    logging.info(
                        f"Drawing tool: updateSiteMap response status_code={getattr(response, 'status_code', 'N/A')}"
                    )

                    if hasattr(response, "status_code") and response.status_code == 200:
                        logging.info(f"Drawing tool: All validation paths deleted from map {config_map_id}")
                        return html.Span(
                            "All validation paths deleted - click Refresh to reload map", style={"color": "#28a745"}
                        ), {"trigger": current_trigger + 1}
                    else:
                        error_msg = getattr(response, "text", str(response))
                        logging.error(f"Drawing tool: Delete paths failed - {error_msg}")
                        return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
                except Exception as del_error:
                    logging.error(f"Drawing tool: Error deleting paths - {del_error}", exc_info=True)
                    return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

            elif button_id == "delete-wayfinding-btn":
                logging.info(
                    f"Drawing tool: Delete wayfinding button clicked - site_id={config_site_id}, map_id={config_map_id}"
                )
                try:
                    # Clear all wayfinding_path via updateSiteMap
                    update_data = {"wayfinding_path": {"coordinate": "actual", "nodes": []}}
                    logging.info(f"Drawing tool: Calling updateSiteMap with {update_data}")
                    response = mistapi.api.v1.sites.maps.updateSiteMap(
                        api_session_ref, config_site_id, config_map_id, update_data
                    )
                    logging.info(
                        f"Drawing tool: updateSiteMap response status_code={getattr(response, 'status_code', 'N/A')}"
                    )

                    if hasattr(response, "status_code") and response.status_code == 200:
                        logging.info(f"Drawing tool: All wayfinding paths deleted from map {config_map_id}")
                        return html.Span(
                            "All wayfinding paths deleted - click Refresh to reload map", style={"color": "#28a745"}
                        ), {"trigger": current_trigger + 1}
                    else:
                        error_msg = getattr(response, "text", str(response))
                        logging.error(f"Drawing tool: Delete wayfinding failed - {error_msg}")
                        return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
                except Exception as del_error:
                    logging.error(f"Drawing tool: Error deleting wayfinding - {del_error}", exc_info=True)
                    return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

            elif button_id == "delete-walls-btn":
                try:
                    # Clear wall_path via updateSiteMap
                    update_data = {"wall_path": {"coordinate": "actual", "nodes": []}}
                    response = mistapi.api.v1.sites.maps.updateSiteMap(
                        api_session_ref, config_site_id, config_map_id, update_data
                    )

                    if hasattr(response, "status_code") and response.status_code == 200:
                        logging.info(f"Drawing tool: All walls deleted from map {config_map_id}")
                        return html.Span(
                            "All walls deleted - click Refresh to reload map", style={"color": "#28a745"}
                        ), {"trigger": current_trigger + 1}
                    else:
                        error_msg = getattr(response, "text", str(response))
                        return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
                except Exception as del_error:
                    logging.error(f"Drawing tool: Error deleting walls - {del_error}")
                    return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

            elif button_id == "delete-zones-btn":
                logging.info(
                    f"Drawing tool: Delete all zones button clicked - site_id={config_site_id}, map_id={config_map_id}"
                )
                try:
                    # First, get all zones for the site
                    zones_response = mistapi.api.v1.sites.zones.listSiteZones(api_session_ref, config_site_id)

                    if not hasattr(zones_response, "status_code") or zones_response.status_code != 200:
                        return html.Span("Failed to fetch zones list", style={"color": "#ff4444"}), no_update

                    all_zones = zones_response.data if hasattr(zones_response, "data") else []

                    # Filter to only zones on this map
                    map_zones = [z for z in all_zones if z.get("map_id") == config_map_id]

                    if not map_zones:
                        return html.Span("No zones found on this map", style={"color": "#ffc107"}), no_update

                    logging.warning(f"Drawing tool: Deleting {len(map_zones)} zones from map {config_map_id}")

                    deleted_count = 0
                    failed_count = 0

                    for zone in map_zones:
                        zone_id = zone.get("id")
                        zone_name = zone.get("name", "Unknown")
                        try:
                            del_response = mistapi.api.v1.sites.zones.deleteSiteZone(
                                api_session_ref, config_site_id, zone_id
                            )
                            if hasattr(del_response, "status_code") and del_response.status_code in [200, 204]:
                                deleted_count += 1
                                logging.info(f"Drawing tool: Deleted zone '{zone_name}'")
                            else:
                                failed_count += 1
                                logging.error(f"Drawing tool: Failed to delete zone '{zone_name}'")
                        except Exception as zone_err:
                            failed_count += 1
                            logging.error(f"Drawing tool: Error deleting zone '{zone_name}': {zone_err}")

                    if failed_count == 0:
                        return html.Span(
                            f"Deleted {deleted_count} zones - click Refresh to reload map", style={"color": "#28a745"}
                        ), {"trigger": current_trigger + 1}
                    else:
                        return html.Span(
                            f"Deleted {deleted_count}, failed {failed_count} zones", style={"color": "#ffc107"}
                        ), {"trigger": current_trigger + 1}

                except Exception as del_error:
                    logging.error(f"Drawing tool: Error deleting zones - {del_error}", exc_info=True)
                    return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

            return "", no_update

        # Callback to handle utilities button actions
        @app.callback(
            Output("utilities-status", "children"),
            [
                Input("auto-zone-btn", "n_clicks"),
                Input("change-image-btn", "n_clicks"),
                Input("remove-image-btn", "n_clicks"),
                Input("rename-btn", "n_clicks"),
            ],
            prevent_initial_call=True,
        )
        def handle_utilities(_auto_zone_clicks, _change_clicks, _remove_clicks, _rename_clicks):
            """Handle utilities button clicks."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return ""

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "auto-zone-btn":
                msg = (
                    "Robot Auto-Zone: AI-powered zone detection"
                    " - analyzes walls and creates location zones automatically"
                )
                logging.info(f"Utilities: Auto-Zone requested for map {map_id}")
                return html.Span(msg, style={"color": "#667eea", "fontWeight": "bold"})

            elif button_id == "change-image-btn":
                msg = "! Change Image: Use Mist API updateSiteMapImage - feature requires file upload"
                logging.info(f"Utilities: Change Image requested for map {map_id}")
                return html.Span(msg, style={"color": "#ff8800"})

            elif button_id == "remove-image-btn":
                msg = "! Remove Image: Use Mist API deleteSiteMapImage - DESTRUCTIVE operation"
                logging.warning(f"Utilities: Remove Image requested for map {map_id}")
                return html.Span(msg, style={"color": "#ff4444"})

            elif button_id == "rename-btn":
                msg = "! Rename: Use Mist API updateSiteMap with new name - requires text input"
                logging.info(f"Utilities: Rename requested for map {map_id}")
                return html.Span(msg, style={"color": "#ff8800"})

            return ""

        # Callback to show/hide delete confirmation panel and update map name
        @app.callback(
            [Output("delete-panel", "style"), Output("delete-map-name-display", "children")],
            [
                Input("delete-btn", "n_clicks"),
                Input("cancel-delete-btn", "n_clicks"),
                Input("confirm-delete-btn", "n_clicks"),
            ],
            [State("delete-panel", "style"), State("map-config-store", "data")],
            prevent_initial_call=True,
        )
        def toggle_delete_panel(_delete_clicks, _cancel_clicks, confirm_clicks, current_style, config):
            """Show or hide the delete confirmation panel and update map name."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return current_style, no_update

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # Get current map name from config store
            current_map_name = config.get("map_name", "Unknown") if config else "Unknown"

            if button_id == "delete-btn":
                # Show the delete confirmation panel with CURRENT map name
                logging.warning(
                    f"Delete panel opened for map '{current_map_name}' "
                    f"(ID: {config.get('map_id') if config else 'unknown'})"
                )
                return (
                    {
                        "display": "block",
                        "padding": "12px 20px",
                        "backgroundColor": "#330000",
                        "borderBottom": "2px solid #ff4444",
                    },
                    f"Map: {current_map_name}",
                )
            elif button_id in ["cancel-delete-btn", "confirm-delete-btn"]:
                # Hide the panel
                return (
                    {
                        "display": "none",
                        "padding": "12px 20px",
                        "backgroundColor": "#330000",
                        "borderBottom": "2px solid #ff4444",
                    },
                    no_update,
                )

            return current_style, no_update

        # Callback to execute map deletion
        @app.callback(
            [Output("delete-status", "children"), Output("cache-bust-store", "data", allow_duplicate=True)],
            Input("confirm-delete-btn", "n_clicks"),
            [State("cache-bust-store", "data"), State("map-config-store", "data")],
            prevent_initial_call=True,
        )
        def execute_delete_map(confirm_clicks, cache_bust_data, config):
            """Actually delete the map via Mist API - creates backup first."""
            current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0

            if not confirm_clicks:
                return "", no_update

            # CRITICAL: Use config store for current map, not closure variable
            config_site_id = config.get("site_id") if config else site_id
            config_map_id = config.get("map_id") if config else map_id
            config_map_name = config.get("map_name", "Unknown") if config else "Unknown"

            try:
                # SAFETY: Backup map geometry before deletion
                logging.info(f"Creating safety backup before deleting map '{config_map_name}'")
                backup_path = self._backup_map_geometry(
                    api_session=api_session_ref,
                    site_id=config_site_id,
                    map_id=config_map_id,
                    map_name=config_map_name,
                    backup_reason="pre_delete",
                )
                if backup_path:
                    logging.info(f"Pre-delete backup saved: {backup_path}")
                else:
                    logging.warning("Pre-delete backup failed - proceeding with deletion anyway")

                logging.warning(
                    f"DESTRUCTIVE: Deleting map '{config_map_name}' (ID: {config_map_id}) from site {config_site_id}"
                )

                # Call the Mist API to delete the map - use config values!
                delete_response = mistapi.api.v1.sites.maps.deleteSiteMap(
                    api_session_ref, site_id=config_site_id, map_id=config_map_id
                )

                if delete_response.status_code in [200, 204]:
                    logging.info(f"Map '{config_map_name}' (ID: {config_map_id}) deleted successfully")
                    # Increment cache bust trigger to refresh map dropdown
                    new_cache_bust = {"trigger": current_trigger + 1}
                    return (
                        html.Span(
                            f"Map '{config_map_name}' deleted! Close this browser tab.",
                            style={"color": "#00ff88", "fontWeight": "bold"},
                        ),
                        new_cache_bust,
                    )
                else:
                    logging.error(f"Map deletion failed: HTTP {delete_response.status_code}")
                    return (
                        html.Span(f"Delete failed: HTTP {delete_response.status_code}", style={"color": "#ff4444"}),
                        no_update,
                    )

            except Exception as delete_error:
                logging.error(f"Error deleting map: {delete_error}", exc_info=True)
                return html.Span(f"Error: {str(delete_error)[:50]}", style={"color": "#ff4444"}), no_update

        # Callback to show/hide clone panel
        @app.callback(
            Output("clone-panel", "style"),
            [
                Input("clone-btn", "n_clicks"),
                Input("cancel-clone-btn", "n_clicks"),
                Input("execute-clone-btn", "n_clicks"),
            ],
            [State("clone-panel", "style")],
            prevent_initial_call=True,
        )
        def toggle_clone_panel(_clone_clicks, _cancel_clicks, _execute_clicks, current_style):
            """Show or hide the clone input panel."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return current_style

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "clone-btn":
                # Show the panel
                logging.info(f"Clone panel opened for map {map_id}")
                return {
                    "display": "block",
                    "padding": "12px 20px",
                    "backgroundColor": "#1a1a1a",
                    "borderBottom": "1px solid #00ff88",
                }
            elif button_id in ["cancel-clone-btn", "execute-clone-btn"]:
                # Hide the panel
                return {
                    "display": "none",
                    "padding": "12px 20px",
                    "backgroundColor": "#1a1a1a",
                    "borderBottom": "1px solid #00ff88",
                }

            return current_style

        # Callback to handle zone-specific toggles
        @app.callback(
            Output("map-display", "figure", allow_duplicate=True),
            Input("zone-toggle", "value"),
            State("map-display", "figure"),
            prevent_initial_call=True,
        )
        def toggle_individual_zones(selected_zone_ids, current_fig):
            """Show/hide individual zones based on checklist."""
            if not zones:
                return current_fig

            # Create set of selected IDs for fast lookup
            selected_set = set(selected_zone_ids) if selected_zone_ids else set()

            # Update visibility for each zone trace
            for trace in current_fig["data"]:
                trace_name = trace.get("name", "")
                if trace_name.startswith("Zone:"):
                    # Extract zone name from trace name
                    zone_name = trace_name.replace("Zone: ", "")
                    # Find matching zone
                    for i, zone in enumerate(zones):
                        if zone.get("name") == zone_name:
                            zone_id = zone.get("id", f"zone_{i}")
                            trace["visible"] = zone_id in selected_set
                            break

            return current_fig

        # Callback for zone edit/remove buttons and zone selection
        @app.callback(
            [Output("selected-zone-info", "children"), Output("selected-zone-store", "data")],
            [
                Input("edit-zone-btn", "n_clicks"),
                Input("remove-zone-btn", "n_clicks"),
                Input("map-display", "clickData"),
            ],
            [State("selected-zone-store", "data")],
            prevent_initial_call=True,
        )
        def handle_zone_actions(_edit_clicks, _remove_clicks, clickData, selected_zone_data):
            """Handle zone edit/remove and display selected zone info."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return html.P(
                    "Click a zone for details", style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"}
                ), selected_zone_data or {"zone_id": None, "zone_name": None}

            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            current_zone = selected_zone_data or {"zone_id": None, "zone_name": None}

            if trigger_id == "edit-zone-btn":
                if current_zone.get("zone_id"):
                    logging.info(
                        f"Zone management: Edit zone {current_zone.get('zone_name')} requested for map {map_id}"
                    )
                    return (
                        html.Div(
                            [
                                html.P(
                                    f"Pencil Edit Zone: {current_zone.get('zone_name', 'Unknown')}",
                                    style={"fontSize": "11px", "color": "#667eea", "fontWeight": "bold"},
                                ),
                                html.P(
                                    "Use Mist Dashboard to modify zone shape",
                                    style={"fontSize": "10px", "color": "#888"},
                                ),
                            ]
                        ),
                        current_zone,
                    )
                else:
                    return (
                        html.Div(
                            [
                                html.P(
                                    "! Select a zone first",
                                    style={"fontSize": "11px", "color": "#ffaa00", "fontWeight": "bold"},
                                ),
                                html.P(
                                    "Click on a zone in the map to select it",
                                    style={"fontSize": "10px", "color": "#888"},
                                ),
                            ]
                        ),
                        current_zone,
                    )

            elif trigger_id == "remove-zone-btn":
                if current_zone.get("zone_id"):
                    zone_id = current_zone.get("zone_id")
                    zone_name = current_zone.get("zone_name", "Unknown")
                    logging.warning(f"Zone management: Deleting zone {zone_name} (ID: {zone_id}) from site {site_id}")

                    try:
                        # Call Mist API to delete the zone
                        delete_response = mistapi.api.v1.sites.zones.deleteSiteZone(
                            api_session_ref, site_id=site_id, zone_id=zone_id
                        )

                        if delete_response.status_code in [200, 204]:
                            logging.info(f"Zone {zone_name} deleted successfully")
                            return html.Div(
                                [
                                    html.P(
                                        f"[OK] Zone deleted: {zone_name}",
                                        style={"fontSize": "11px", "color": "#00ff88", "fontWeight": "bold"},
                                    ),
                                    html.P(
                                        "Refresh the page to update view", style={"fontSize": "10px", "color": "#888"}
                                    ),
                                ]
                            ), {"zone_id": None, "zone_name": None}
                        else:
                            logging.error(f"Zone deletion failed: HTTP {delete_response.status_code}")
                            return (
                                html.Div(
                                    [
                                        html.P(
                                            f"X Delete failed: HTTP {delete_response.status_code}",
                                            style={"fontSize": "11px", "color": "#ff4444", "fontWeight": "bold"},
                                        ),
                                        html.P(
                                            "Check permissions and try again",
                                            style={"fontSize": "10px", "color": "#888"},
                                        ),
                                    ]
                                ),
                                current_zone,
                            )

                    except Exception as del_error:
                        logging.error(f"Error deleting zone: {del_error}", exc_info=True)
                        return (
                            html.Div(
                                [
                                    html.P(
                                        f"X Error: {str(del_error)[:40]}",
                                        style={"fontSize": "11px", "color": "#ff4444", "fontWeight": "bold"},
                                    )
                                ]
                            ),
                            current_zone,
                        )
                else:
                    return (
                        html.Div(
                            [
                                html.P(
                                    "! Select a zone first",
                                    style={"fontSize": "11px", "color": "#ffaa00", "fontWeight": "bold"},
                                ),
                                html.P(
                                    "Click on a zone in the map to select it",
                                    style={"fontSize": "10px", "color": "#888"},
                                ),
                            ]
                        ),
                        current_zone,
                    )

            elif trigger_id == "map-display" and clickData:
                # Check if clicked on a zone
                point = clickData["points"][0]
                hover_text = point.get("hovertext", "")

                if "Zone:" in hover_text:
                    zone_name = hover_text.split("Zone: ")[1] if "Zone: " in hover_text else "Unknown"
                    # Find the zone ID
                    zone_id = None
                    for zone in zones:
                        if zone.get("name") == zone_name:
                            zone_id = zone.get("id")
                            break

                    return html.Div(
                        [
                            html.P(
                                f">> Selected: {zone_name}",
                                style={
                                    "fontSize": "12px",
                                    "color": "#00ff00",
                                    "fontWeight": "bold",
                                    "marginBottom": "5px",
                                },
                            ),
                            html.P(
                                f"ID: {zone_id[:8] if zone_id else 'Unknown'}...",
                                style={"fontSize": "10px", "color": "#888"},
                            ),
                        ]
                    ), {"zone_id": zone_id, "zone_name": zone_name}

            return (
                html.P("Click a zone for details", style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"}),
                current_zone,
            )

        # Callback to toggle auto-refresh intervals on/off
        @app.callback(
            [
                Output("client-refresh-interval", "disabled"),
                Output("coverage-refresh-interval", "disabled"),
                Output("countdown-tick-interval", "disabled"),
                Output("refresh-times-store", "data"),
                Output("countdown-display", "children"),
            ],
            [Input("auto-refresh-toggle", "value")],
            prevent_initial_call=True,
        )
        def toggle_auto_refresh(toggle_value):
            """Enable or disable auto-refresh intervals based on checkbox."""
            import time

            is_enabled = "enabled" in (toggle_value or [])
            current_time = time.time()

            if is_enabled:
                logging.info("Live data refresh: Auto-refresh ENABLED by user")
                # Initialize refresh times to now so countdown starts fresh
                refresh_data = {"client_last_refresh": current_time, "coverage_last_refresh": current_time}
                countdown_text = "Clients: 30s | RF: 5:00"
            else:
                logging.info("Live data refresh: Auto-refresh DISABLED by user")
                refresh_data = {"client_last_refresh": 0, "coverage_last_refresh": 0}
                countdown_text = "Auto-refresh: Off"

            # Return disabled=False when enabled, disabled=True when disabled
            return (not is_enabled, not is_enabled, not is_enabled, refresh_data, countdown_text)

        # Callback to update countdown display every second
        @app.callback(
            Output("countdown-display", "children", allow_duplicate=True),
            [Input("countdown-tick-interval", "n_intervals")],
            [State("refresh-times-store", "data"), State("auto-refresh-toggle", "value")],
            prevent_initial_call=True,
        )
        def update_countdown_display(n_intervals, refresh_times, toggle_value):
            """Update the countdown display every second."""
            import time

            if not refresh_times or "enabled" not in (toggle_value or []):
                return "Auto-refresh: Off"

            current_time = time.time()

            # Calculate time until next client refresh (30 seconds)
            client_elapsed = current_time - refresh_times.get("client_last_refresh", current_time)
            client_remaining = max(0, 30 - int(client_elapsed) % 30)

            # Calculate time until next coverage refresh (5 minutes = 300 seconds)
            coverage_elapsed = current_time - refresh_times.get("coverage_last_refresh", current_time)
            coverage_remaining = max(0, 300 - int(coverage_elapsed) % 300)
            coverage_mins = coverage_remaining // 60
            coverage_secs = coverage_remaining % 60

            return f"Clients: {client_remaining}s | RF: {coverage_mins}:{coverage_secs:02d}"

        # Store reference to API session for refresh callbacks
        api_session_ref = self.apisession

        # Callback to execute clone operation
        @app.callback(
            [Output("clone-status", "children"), Output("cache-bust-store", "data", allow_duplicate=True)],
            [Input("execute-clone-btn", "n_clicks")],
            [State("clone-name-input", "value"), State("map-config-store", "data"), State("cache-bust-store", "data")],
            prevent_initial_call=True,
        )
        def execute_clone_operation(n_clicks, new_name, config, cache_bust_data):
            """Clone the current map with all properties, image, and zones."""
            import os
            import tempfile

            import requests

            current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0

            if not n_clicks:
                return "", no_update

            if not new_name or not new_name.strip():
                return html.Span("! Please enter a name for the cloned map", style={"color": "#ff4444"}), no_update

            new_name = new_name.strip()
            site_id_local = config.get("site_id")
            source_map_id = config.get("map_id")

            if not site_id_local or not source_map_id:
                return html.Span("! Missing site or map configuration", style={"color": "#ff4444"}), no_update

            logging.info(f"Clone operation started - source: {source_map_id}, new name: {new_name}")

            try:
                # SAFETY: Backup source map geometry before cloning
                source_map_name = config.get("map_name", "Unknown")
                logging.info(f"Creating backup of source map '{source_map_name}' before cloning")
                backup_path = self._backup_map_geometry(
                    api_session=api_session_ref,
                    site_id=site_id_local,
                    map_id=source_map_id,
                    map_name=source_map_name,
                    backup_reason="pre_clone",
                )
                if backup_path:
                    logging.info(f"Pre-clone backup saved: {backup_path}")

                # Step 1: Fetch source map details
                source_response = mistapi.api.v1.sites.maps.getSiteMap(
                    api_session_ref, site_id=site_id_local, map_id=source_map_id
                )

                if source_response.status_code != 200:
                    logging.error(f"Clone failed: Could not fetch source map - HTTP {source_response.status_code}")
                    return (
                        html.Span(
                            f"! Failed to fetch source map: HTTP {source_response.status_code}",
                            style={"color": "#ff4444"},
                        ),
                        no_update,
                    )

                source_map = source_response.data

                # Step 2: Build clone payload with ALL properties
                clone_payload = {"name": new_name, "type": source_map.get("type", "image")}

                # Copy dimensional properties (critical for scaling)
                for prop in ["width", "height", "height_m", "ppm", "orientation"]:
                    if prop in source_map:
                        clone_payload[prop] = source_map[prop]

                # Copy location data
                for prop in ["latlng", "latlng_br", "origin_x", "origin_y"]:
                    if prop in source_map:
                        clone_payload[prop] = source_map[prop]

                # Copy wayfinding and wall paths
                for prop in ["wayfinding", "wayfinding_path", "wall_path", "sitesurvey_path"]:
                    if prop in source_map:
                        clone_payload[prop] = source_map[prop]

                # Copy other settings
                for prop in ["occupancy_limit", "locked", "view"]:
                    if prop in source_map:
                        clone_payload[prop] = source_map[prop]

                logging.debug(f"Clone payload prepared with {len(clone_payload)} properties")

                # Step 3: Download image if present
                image_temp_path = None
                if "url" in source_map:
                    try:
                        image_url = source_map["url"]
                        file_ext = ".png"
                        if "." in image_url:
                            url_ext = image_url.rsplit(".", 1)[-1].split("?")[0]
                            if url_ext.lower() in ["png", "jpg", "jpeg", "gif", "svg"]:
                                file_ext = f".{url_ext.lower()}"

                        temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)
                        os.close(temp_fd)

                        response = requests.get(image_url, timeout=60)
                        if response.status_code == 200:
                            with open(image_temp_path, "wb") as f:
                                f.write(response.content)
                            logging.info(f"Downloaded source map image ({len(response.content) / 1024:.1f} KB)")
                        else:
                            logging.warning(f"Failed to download image: HTTP {response.status_code}")
                            if image_temp_path and os.path.exists(image_temp_path):
                                os.remove(image_temp_path)
                            image_temp_path = None
                    except Exception as img_err:
                        logging.error(f"Error downloading image: {img_err}")
                        if image_temp_path and os.path.exists(image_temp_path):
                            os.remove(image_temp_path)
                        image_temp_path = None

                # Step 4: Create the cloned map
                clone_response = mistapi.api.v1.sites.maps.createSiteMap(
                    api_session_ref, site_id=site_id_local, body=clone_payload
                )

                if clone_response.status_code not in [200, 201]:
                    logging.error(f"Clone failed: Could not create map - HTTP {clone_response.status_code}")
                    if image_temp_path and os.path.exists(image_temp_path):
                        os.remove(image_temp_path)
                    return (
                        html.Span(
                            f"! Failed to create cloned map: HTTP {clone_response.status_code}",
                            style={"color": "#ff4444"},
                        ),
                        no_update,
                    )

                cloned_map = clone_response.data
                cloned_map_id = cloned_map.get("id")
                logging.info(f"Cloned map created: {cloned_map_id}")

                # Step 5: Upload image to cloned map
                image_uploaded = False
                if image_temp_path and os.path.exists(image_temp_path):
                    try:
                        upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(
                            api_session_ref, site_id=site_id_local, map_id=cloned_map_id, file=image_temp_path
                        )
                        if upload_response.status_code in [200, 201]:
                            image_uploaded = True
                            logging.info(f"Image uploaded to cloned map {cloned_map_id}")
                        else:
                            logging.warning(f"Image upload failed: HTTP {upload_response.status_code}")
                    except Exception as upload_err:
                        logging.error(f"Error uploading image: {upload_err}")
                    finally:
                        if os.path.exists(image_temp_path):
                            os.remove(image_temp_path)

                # Step 6: Clone zones associated with source map
                zones_cloned = 0
                zones_failed = 0
                try:
                    zones_response = mistapi.api.v1.sites.zones.listSiteZones(api_session_ref, site_id=site_id_local)

                    if zones_response.status_code == 200:
                        source_zones = [z for z in zones_response.data if z.get("map_id") == source_map_id]

                        for zone in source_zones:
                            try:
                                zone_payload = {
                                    "name": zone.get("name", "Unnamed Zone"),
                                    "map_id": cloned_map_id,
                                    "vertices": zone.get("vertices", []),
                                }
                                if "type" in zone:
                                    zone_payload["type"] = zone["type"]
                                if "z" in zone:
                                    zone_payload["z"] = zone["z"]

                                zone_response = mistapi.api.v1.sites.zones.createSiteZone(
                                    api_session_ref, site_id=site_id_local, body=zone_payload
                                )

                                if zone_response.status_code in [200, 201]:
                                    zones_cloned += 1
                                else:
                                    zones_failed += 1
                            except Exception:
                                zones_failed += 1
                except Exception as zone_err:
                    logging.error(f"Zone cloning error: {zone_err}")

                # Build success message
                result_parts = [f"Map '{new_name}' created successfully!"]
                if image_uploaded:
                    result_parts.append("Image: uploaded")
                if zones_cloned > 0:
                    result_parts.append(f"Zones: {zones_cloned} cloned")

                logging.info(
                    f"Clone complete: {new_name} (ID: {cloned_map_id}), image={image_uploaded}, zones={zones_cloned}"
                )
                # Increment cache bust trigger to refresh map dropdown
                new_cache_bust = {"trigger": current_trigger + 1}
                return (
                    html.Span(" | ".join(result_parts), style={"color": "#00ff88", "fontWeight": "bold"}),
                    new_cache_bust,
                )

            except Exception as e:
                logging.error(f"Clone operation failed: {e}", exc_info=True)
                return html.Span(f"! Clone failed: {str(e)}", style={"color": "#ff4444"}), no_update

        # Callback to refresh map dropdown after clone/delete operations or page load (cache bust)
        @app.callback(
            [Output("map-selector-dropdown", "options"), Output("available-maps-store", "data")],
            [
                Input("cache-bust-store", "data"),
                Input("manual-refresh-btn", "n_clicks"),
                Input("url-location", "search"),
            ],
            [State("map-config-store", "data")],
            prevent_initial_call=False,  # Run on initial load to get fresh data
        )
        def refresh_map_dropdown(cache_bust_data, _manual_clicks, url_search, config):
            """Fetch fresh map list from API after clone/delete, manual refresh, or page load."""
            site_id_local = config.get("site_id") if config else None

            if not site_id_local:
                logging.warning("Cannot refresh map dropdown: site_id not available")
                return no_update, no_update

            try:
                # Determine trigger for logging
                ctx = dash.callback_context
                trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "initial_load"
                logging.info(f"Refreshing map dropdown list (trigger: {trigger_id})")

                # Fetch fresh map list from API
                maps_response = mistapi.api.v1.sites.maps.listSiteMaps(api_session_ref, site_id=site_id_local)

                if maps_response.status_code != 200:
                    logging.warning(f"Failed to refresh map list: HTTP {maps_response.status_code}")
                    return no_update, no_update

                fresh_maps = maps_response.data if maps_response.data else []
                logging.info(f"Map dropdown refreshed: {len(fresh_maps)} maps found")

                # Build new dropdown options
                new_options = [{"label": m.get("name", "Unnamed"), "value": m.get("id")} for m in fresh_maps]
                # Build new available maps store data
                new_store_data = [{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in fresh_maps]

                return new_options, new_store_data

            except Exception as refresh_error:
                logging.error(f"Error refreshing map dropdown: {refresh_error}", exc_info=True)
                return no_update, no_update

        # Callback for client position refresh (every 30 seconds when enabled)
        @app.callback(
            [
                Output("map-display", "figure", allow_duplicate=True),
                Output("refresh-times-store", "data", allow_duplicate=True),
            ],
            [Input("client-refresh-interval", "n_intervals"), Input("manual-refresh-btn", "n_clicks")],
            [
                State("map-config-store", "data"),
                State("map-display", "figure"),
                State("client-toggle", "value"),
                State("refresh-times-store", "data"),
            ],
            prevent_initial_call=True,
        )
        def refresh_client_positions(n_intervals, _manual_clicks, config, current_fig, client_layers, refresh_times):
            """Refresh client positions from Mist API."""
            import time

            ctx = dash.callback_context
            if not ctx.triggered:
                return no_update, no_update

            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # Skip if manual refresh button was clicked but clients not shown
            if trigger_id == "manual-refresh-btn":
                logging.info("Live data refresh: Manual refresh requested")

            # Update refresh time
            current_time = time.time()
            updated_refresh_times = refresh_times.copy() if refresh_times else {}
            updated_refresh_times["client_last_refresh"] = current_time

            try:
                site_id_local = config.get("site_id") if config else None
                map_id_local = config.get("map_id") if config else None

                # Validate site_id before making API call
                if not site_id_local:
                    logging.warning(f"Live data refresh: site_id is None, skipping refresh. Config: {config}")
                    return no_update, updated_refresh_times

                if not map_id_local:
                    logging.warning("Live data refresh: map_id is None, skipping refresh")
                    return no_update, updated_refresh_times

                logging.info(
                    f"Live data refresh: Fetching client positions for map {map_id_local} (site: {site_id_local})"
                )

                # Fetch fresh client data from API
                clients_response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
                    api_session_ref, site_id=site_id_local, limit=1000
                )

                if clients_response.status_code != 200:
                    logging.warning(f"Live data refresh: Failed to fetch clients - HTTP {clients_response.status_code}")
                    return no_update, updated_refresh_times

                # Get all clients and filter for this map
                all_clients = mistapi.get_all(response=clients_response, mist_session=api_session_ref)
                fresh_clients = [
                    c
                    for c in all_clients
                    if c.get("map_id") == map_id_local and c.get("x") is not None and c.get("y") is not None
                ]

                logging.info(
                    f"Live data refresh: Found {len(fresh_clients)} clients on map (total: {len(all_clients)})"
                )

                # Update client traces in the figure
                wifi_client_x = []
                wifi_client_y = []
                wifi_client_hover = []
                wifi_client_names = []
                wired_client_x = []
                wired_client_y = []
                wired_client_hover = []
                wired_client_names = []

                for client in fresh_clients:
                    # API returns x,y already in pixels (not meters) - do NOT multiply by PPM
                    client_x_px = client.get("x")
                    client_y_px = client.get("y")

                    if client_x_px is None or client_y_px is None:
                        continue

                    # Build hover text
                    hostname = client.get("hostname", "")
                    client_mac = client.get("mac", "Unknown")
                    client_name = hostname if hostname else client_mac[-8:]
                    client_ip = client.get("ip", "N/A")
                    rssi = client.get("rssi", "N/A")
                    ssid = client.get("ssid", "N/A")

                    hover_text = (
                        f"<b>Client</b><br>MAC: {client_mac}<br>"
                        f"Hostname: {hostname or 'N/A'}<br>IP: {client_ip}<br>"
                        f"SSID: {ssid}<br>RSSI: {rssi} dBm<br>"
                        f"Position: ({client_x_px}, {client_y_px})"
                    )

                    # Separate WiFi vs Wired clients
                    if client.get("wired", False):
                        wired_client_x.append(client_x_px)
                        wired_client_y.append(client_y_px)
                        wired_client_hover.append(hover_text)
                        wired_client_names.append(client_name)
                    else:
                        wifi_client_x.append(client_x_px)
                        wifi_client_y.append(client_y_px)
                        wifi_client_hover.append(hover_text)
                        wifi_client_names.append(client_name)

                # Update traces in figure
                # Note: The trace is named 'Clients' (singular), so we match on 'clients' lowercase
                trace_updated = False
                for trace in current_fig["data"]:
                    trace_name = trace.get("name", "").lower()

                    # Match 'Clients' trace (WiFi clients) - excludes 'wired client' and link traces
                    if trace_name == "clients" or ("wifi client" in trace_name and "link" not in trace_name):
                        trace["x"] = wifi_client_x
                        trace["y"] = wifi_client_y
                        trace["hovertext"] = wifi_client_hover
                        # Keep visible - don't change visibility based on toggle during refresh
                        trace_updated = True
                        logging.info(
                            f"Live data refresh: Updated WiFi clients trace with "
                            f"{len(wifi_client_x)} clients, coords sample: "
                            f"{wifi_client_x[:3] if wifi_client_x else 'empty'}"
                        )

                    elif "wired client" in trace_name and "link" not in trace_name:
                        trace["x"] = wired_client_x
                        trace["y"] = wired_client_y
                        trace["hovertext"] = wired_client_hover
                        # Keep visible - don't change visibility based on toggle during refresh
                        logging.info(
                            f"Live data refresh: Updated Wired clients trace with {len(wired_client_x)} clients"
                        )

                if not trace_updated:
                    logging.warning(
                        f"Live data refresh: Could not find 'Clients' trace to update. "
                        f"Available traces: {[t.get('name', 'unnamed') for t in current_fig['data']]}"
                    )

                # Update client label annotations
                # Client labels are annotations with 'Clients Label' in the name attribute
                # We need to update their positions to match new client positions
                if "layout" in current_fig and "annotations" in current_fig["layout"]:
                    # Remove old client label annotations
                    new_annotations = [
                        ann for ann in current_fig["layout"]["annotations"] if ann.get("name") != "Clients Label"
                    ]

                    # Add new client label annotations for WiFi clients
                    for _, (x, y, name) in enumerate(zip(wifi_client_x, wifi_client_y, wifi_client_names, strict=True)):
                        new_annotations.append(
                            {
                                "x": x,
                                "y": y - 10,  # Position below marker
                                "text": f"<b>{name}</b>",
                                "showarrow": False,
                                "font": {"size": 9, "color": "white", "family": "Arial"},
                                "bgcolor": "rgba(0,128,0,0.9)",
                                "bordercolor": "white",
                                "borderwidth": 1,
                                "borderpad": 2,
                                "xanchor": "center",
                                "yanchor": "bottom",
                                "name": "Clients Label",
                            }
                        )

                    current_fig["layout"]["annotations"] = new_annotations
                    logging.info(f"Live data refresh: Updated {len(wifi_client_names)} client label annotations")

                # Also refresh zones from Mist API
                try:
                    zones_response = mistapi.api.v1.sites.zones.listSiteZones(api_session_ref, site_id=site_id_local)
                    if zones_response.status_code == 200:
                        all_zones = mistapi.get_all(response=zones_response, mist_session=api_session_ref)
                        zones_on_map = [z for z in all_zones if z.get("map_id") == map_id_local]
                        logging.info(f"Live data refresh: Found {len(zones_on_map)} zones on map")

                        # Update zone traces - find and update zone rectangles
                        # Zones are drawn as filled rectangles, typically named 'Zones' or with zone names
                        # For now, just log that zones were refreshed
                        # Full zone update would require removing old zone traces and adding new ones
                except Exception as zone_refresh_error:
                    logging.warning(f"Live data refresh: Error refreshing zones: {zone_refresh_error}")

                # Refresh walls from map data
                try:
                    map_response = mistapi.api.v1.sites.maps.getSiteMap(
                        api_session_ref, site_id=site_id_local, map_id=map_id_local
                    )
                    if map_response.status_code == 200:
                        map_data_fresh = map_response.data
                        wall_path = map_data_fresh.get("wall_path", {})
                        wall_nodes = wall_path.get("nodes", [])
                        logging.info(f"Live data refresh: Map has {len(wall_nodes)} wall nodes")

                        # Update wall traces if wall_path changed
                        # Build node lookup for wall segments
                        if wall_nodes:
                            node_lookup = {}
                            for node in wall_nodes:
                                node_name = node.get("name", "")
                                pos = node.get("position", {})
                                if node_name and pos:
                                    node_lookup[node_name] = pos

                            # Find and update wall traces
                            for trace in current_fig["data"]:
                                trace_name = trace.get("name", "").lower()
                                if trace_name == "walls":
                                    # Clear existing and rebuild - complex due to multiple segments
                                    # For simplicity, walls will be refreshed on page reload
                                    pass
                except Exception as wall_refresh_error:
                    logging.warning(f"Live data refresh: Error refreshing walls: {wall_refresh_error}")

                # Update the map-info section with new client count
                timestamp = datetime.now().strftime("%H:%M:%S")
                logging.info(
                    f"Live data refresh: Client positions updated at {timestamp} "
                    f"- WiFi: {len(wifi_client_x)}, Wired: {len(wired_client_x)}"
                )

                return current_fig, updated_refresh_times

            except Exception as refresh_error:
                logging.error(f"Live data refresh: Error refreshing clients: {refresh_error}", exc_info=True)
                return no_update, updated_refresh_times

        # Callback for RF coverage refresh (every 5 minutes when enabled)
        @app.callback(
            [
                Output("map-display", "figure", allow_duplicate=True),
                Output("refresh-times-store", "data", allow_duplicate=True),
            ],
            [Input("coverage-refresh-interval", "n_intervals")],
            [
                State("map-config-store", "data"),
                State("map-display", "figure"),
                State("layer-toggle", "value"),
                State("refresh-times-store", "data"),
            ],
            prevent_initial_call=True,
        )
        def refresh_rf_coverage(n_intervals, config, current_fig, layer_values, refresh_times):
            """Refresh RF coverage heatmap from Mist API."""
            import time

            if n_intervals == 0:
                return no_update, no_update

            # Update refresh time
            current_time = time.time()
            updated_refresh_times = refresh_times.copy() if refresh_times else {}
            updated_refresh_times["coverage_last_refresh"] = current_time

            try:
                site_id_local = config.get("site_id") if config else None
                map_id_local = config.get("map_id") if config else None
                ppm_local = config.get("ppm", 10) if config else 10

                # Validate site_id before making API call
                if not site_id_local:
                    logging.warning(f"Live data refresh: RF coverage - site_id is None, skipping. Config: {config}")
                    return no_update, updated_refresh_times

                if not map_id_local:
                    logging.warning("Live data refresh: RF coverage - map_id is None, skipping")
                    return no_update, updated_refresh_times

                logging.info(
                    f"Live data refresh: Fetching RF coverage data for map {map_id_local} (site: {site_id_local})"
                )

                # Fetch fresh coverage data from API
                coverage_url = f"/api/v1/sites/{site_id_local}/location/coverage"
                coverage_params = {
                    "resolution": "fine",
                    "duration": "1d",
                    "map_id": map_id_local,
                    "type": "client",
                    "from_apollo": "true",
                }

                coverage_response = api_session_ref.mist_get(coverage_url, query=coverage_params)

                if coverage_response.status_code != 200:
                    logging.warning(
                        f"Live data refresh: Failed to fetch RF coverage - HTTP {coverage_response.status_code}"
                    )
                    return no_update, updated_refresh_times

                coverage_data = coverage_response.data

                # Check for error response
                if isinstance(coverage_data, dict) and "exception" in coverage_data:
                    logging.warning("Live data refresh: Coverage API returned error")
                    return no_update, updated_refresh_times

                # Coverage API returns result_def (field names) + results (list of lists)
                result_def = coverage_data.get("result_def", [])
                results = coverage_data.get("results", [])
                if not results or not result_def:
                    logging.info("Live data refresh: No coverage data available")
                    return no_update, updated_refresh_times

                logging.info(f"Live data refresh: Processing {len(results)} coverage grid points")

                # Get field indices from result_def
                try:
                    x_idx = result_def.index("x")
                    y_idx = result_def.index("y")
                    # Try max_rssi first, fall back to avg_rssi
                    if "max_rssi" in result_def:
                        rssi_idx = result_def.index("max_rssi")
                    elif "avg_rssi" in result_def:
                        rssi_idx = result_def.index("avg_rssi")
                    else:
                        rssi_idx = -1
                except ValueError as index_error:
                    logging.warning(f"Live data refresh: Missing expected fields in result_def: {index_error}")
                    return no_update, updated_refresh_times

                # Build grid data for Heatmap (requires 2D z-matrix, not flat array)
                grid_data = {}  # (x_meters, y_meters) -> rssi

                for point in results:
                    x_meters = point[x_idx] if x_idx < len(point) else 0
                    y_meters = point[y_idx] if y_idx < len(point) else 0
                    rssi_val = point[rssi_idx] if rssi_idx >= 0 and rssi_idx < len(point) else -100
                    grid_data[(x_meters, y_meters)] = rssi_val

                if not grid_data:
                    logging.info("Live data refresh: No coverage grid data to visualize")
                    return no_update, updated_refresh_times

                # Get unique sorted x and y values (in meters, then convert to pixels)
                unique_x_m = sorted(set(k[0] for k in grid_data.keys()))
                unique_y_m = sorted(set(k[1] for k in grid_data.keys()))

                # Convert to pixel coordinates for Heatmap
                unique_x = [x_m * ppm_local for x_m in unique_x_m]
                unique_y = [y_m * ppm_local for y_m in unique_y_m]

                # Build z-matrix for Heatmap (rows=y, cols=x)
                z_matrix = []
                for y_m in unique_y_m:
                    row = []
                    for x_m in unique_x_m:
                        rssi = grid_data.get((x_m, y_m), None)
                        row.append(rssi)
                    z_matrix.append(row)

                # Get min/max for color scale
                all_rssi = [v for v in grid_data.values() if v is not None]
                min_rssi = min(all_rssi) if all_rssi else -100
                max_rssi = max(all_rssi) if all_rssi else -30

                # Update the RF coverage trace (Heatmap uses x, y, z - not marker)
                for trace in current_fig["data"]:
                    trace_name = trace.get("name", "").lower()

                    if "rf coverage" in trace_name:
                        trace["x"] = unique_x
                        trace["y"] = unique_y
                        trace["z"] = z_matrix
                        trace["zmin"] = min_rssi
                        trace["zmax"] = max_rssi
                        trace["visible"] = "rf_heatmap" in (layer_values or [])
                        logging.debug(f"Live data refresh: Updated RF coverage heatmap with {len(grid_data)} cells")
                        break

                timestamp = datetime.now().strftime("%H:%M:%S")
                logging.info(f"Live data refresh: RF coverage updated at {timestamp} - {len(results)} points")

                return current_fig, updated_refresh_times

            except Exception as refresh_error:
                logging.error(f"Live data refresh: Error refreshing RF coverage: {refresh_error}", exc_info=True)
                return no_update, updated_refresh_times

        # Determine host binding - use 0.0.0.0 in containers for external access
        dash_host = "127.0.0.1"
        if is_running_in_container():
            dash_host = "0.0.0.0"  # nosec B104 — container must bind all interfaces
        # Use port 8050 by default (matches container EXPOSE and compose.yml)
        dash_port = int(os.getenv("DASH_PORT", "8050"))

        print("\nStarting Dash server...")
        if is_running_in_container():
            print(f"! Map viewer available at http://<container-ip>:{dash_port}")
            print(f"! Access from host: http://localhost:{dash_port} (if port is mapped)")
        else:
            print("! Map viewer will open in your default browser")
        print("! Press Ctrl+C to stop the server\n")

        logging.info(f"Starting Dash server on http://{dash_host}:{dash_port}")

        # Open browser automatically (skip in container - no display)
        if not is_running_in_container():
            import threading
            import time
            import webbrowser

            def open_browser():
                """Wait for server to start, then open browser."""
                time.sleep(1.5)  # Wait for Dash server to initialize
                webbrowser.open(f"http://127.0.0.1:{dash_port}")
                logging.debug(f"Browser opened to http://127.0.0.1:{dash_port}")

            # Start browser opening in background thread
            threading.Thread(target=open_browser, daemon=True).start()

        try:
            # Check if --debug flag was passed via CLI args
            debug_mode = getattr(globals().get("args"), "debug", False)
            logging.info(f"Starting Dash server with debug_mode={debug_mode}")
            # Dash 3.x uses app.run() instead of app.run_server()
            app.run(
                host=dash_host,
                port=dash_port,
                debug=debug_mode,
                use_reloader=False,  # Disable reloader to prevent double-execution
                threaded=True,
            )
        except KeyboardInterrupt:
            print("\n\nMap viewer stopped by user")
            logging.info("Interactive map viewer stopped by user (Ctrl+C)")
        except Exception as e:
            logging.error(f"Error running Dash server: {e}", exc_info=True)
            print(f"\n! Error running map viewer: {e}")

    def _launch_flask_viewer(
        self, initial_site_id: str, initial_map_id: str, all_sites: list[dict], all_maps: list[dict]
    ):
        """Launch interactive Flask-based map viewer (simpler alternative to Dash).

        This viewer uses Flask for server-side rendering and Plotly.js for client-side
        map display. Site/map switching is handled via JavaScript fetch() calls to
        Flask API endpoints, which is more reliable than Dash callbacks.

        Args:
            initial_site_id: Site ID to load initially
            initial_map_id: Map ID to load initially
            all_sites: List of all sites in the organization
            all_maps: List of maps for the initial site
        """
        import json as json_module
        import threading
        import webbrowser

        from flask import Flask, jsonify, render_template_string

        logging.info(f"_launch_flask_viewer: Starting Flask viewer for site {initial_site_id}, map {initial_map_id}")

        flask_app = Flask(__name__)
        flask_app.config["JSON_SORT_KEYS"] = False

        # Store reference to API session for use in routes
        api_session = self.apisession

        # HTML template with embedded Plotly.js
        HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MistHelper Map Viewer</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            padding: 15px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            margin-right: 30px;
        }
        .dropdown-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dropdown-group label {
            font-size: 14px;
            color: rgba(255,255,255,0.8);
        }
        select {
            padding: 8px 12px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
            background-color: rgba(255,255,255,0.9);
            color: #333;
            min-width: 200px;
            cursor: pointer;
        }
        select:focus { outline: 2px solid #667eea; }
        .status {
            margin-left: auto;
            font-size: 13px;
            color: rgba(255,255,255,0.7);
        }
        .loading {
            color: #ffd700;
            font-weight: bold;
        }
        .main-content {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
        #map-container {
            flex: 1;
            padding: 10px;
        }
        #map-display {
            width: 100%;
            height: 100%;
            background-color: #2d2d2d;
            border-radius: 8px;
        }
        .sidebar {
            width: 280px;
            background-color: #2d2d2d;
            padding: 20px;
            overflow-y: auto;
            border-left: 1px solid #444;
        }
        .sidebar h3 {
            color: #a0a0ff;
            font-size: 14px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #444;
        }
        .info-item {
            margin: 8px 0;
            font-size: 13px;
            color: #b0b0b0;
        }
        .info-item strong { color: #e0e0e0; }
        .layer-toggle {
            margin: 6px 0;
        }
        .layer-toggle label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 13px;
            padding: 4px 0;
        }
        .layer-toggle input[type="checkbox"] {
            width: 16px;
            height: 16px;
        }
        .refresh-btn {
            margin-top: 15px;
            width: 100%;
            padding: 10px;
            background-color: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: bold;
        }
        .refresh-btn:hover { background-color: #5a6fd6; }
        .refresh-btn:disabled { background-color: #555; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MistHelper Map Viewer</h1>
        <div class="dropdown-group">
            <label for="site-select">Site:</label>
            <select id="site-select"></select>
        </div>
        <div class="dropdown-group">
            <label for="map-select">Map:</label>
            <select id="map-select"></select>
        </div>
        <div class="status" id="status-display">Ready</div>
    </div>

    <div class="main-content">
        <div id="map-container">
            <div id="map-display"></div>
        </div>
        <div class="sidebar">
            <h3>Map Information</h3>
            <div id="map-info">
                <div class="info-item"><strong>Site:</strong> <span id="info-site">-</span></div>
                <div class="info-item"><strong>Map:</strong> <span id="info-map">-</span></div>
                <div class="info-item"><strong>Dimensions:</strong> <span id="info-dims">-</span></div>
                <div class="info-item"><strong>Access Points:</strong> <span id="info-aps">-</span></div>
                <div class="info-item"><strong>Switches:</strong> <span id="info-switches">-</span></div>
                <div class="info-item"><strong>Gateways:</strong> <span id="info-gateways">-</span></div>
                <div class="info-item"><strong>Zones:</strong> <span id="info-zones">-</span></div>
                <div class="info-item"><strong>WiFi Clients:</strong> <span id="info-wifi-clients">-</span></div>
                <div class="info-item"><strong>Unconnected:</strong> <span id="info-unconnected">-</span></div>
                <div class="info-item"><strong>App Clients:</strong> <span id="info-sdk">-</span></div>
                <div class="info-item"><strong>BLE Devices:</strong> <span id="info-ble">-</span></div>
                <div class="info-item"><strong>Assets:</strong> <span id="info-assets">-</span></div>
            </div>

            <h3 style="margin-top: 20px;">Layer Controls</h3>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-aps" checked> Access Points</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-switches" checked> Switches</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-gateways" checked> Gateways</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-zones" checked> Zones</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-wifi-clients" checked> WiFi Clients (Connected)</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-unconnected-clients" checked>
                    WiFi Clients (Unconnected)</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-ble-devices" checked> Bluetooth Devices</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-assets" checked> Assets</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-sdk-clients" checked> App Clients (Marvis)</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-walls" checked> Walls</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-wayfinding" checked> Wayfinding Paths</label>
            </div>

            <h3 style="margin-top: 20px;">Coverage Heatmaps</h3>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-wifi-coverage"> WiFi RF Coverage</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-ble-coverage"> BLE Coverage</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-app-coverage"> App Coverage</label>
            </div>

            <h3 style="margin-top: 20px;">Legend</h3>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 0; height: 0;
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 14px solid #00cc00;
                    margin-right: 8px;"></span>
                Device (Connected)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 0; height: 0;
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 14px solid #ff8c00;
                    margin-right: 8px;"></span>
                Device (Transitional)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 0; height: 0;
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 14px solid #ff4444;
                    margin-right: 8px;"></span>
                Device (Offline)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #9966ff; border-radius: 50%;
                    margin-right: 8px;"></span>
                WiFi Client (Connected)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #888888; border-radius: 50%;
                    margin-right: 8px;"></span>
                WiFi Client (Unconnected)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #66ccff; border-radius: 50%;
                    margin-right: 8px;"></span>
                App Client (Marvis)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #003366; border-radius: 50%;
                    margin-right: 8px;"></span>
                Bluetooth Device
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #00cc00; border-radius: 50%;
                    margin-right: 8px;"></span>
                Asset
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 16px; height: 3px;
                    background-color: #ff0000;
                    margin-right: 8px;"></span>
                Wall
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 16px; height: 3px;
                    background-color: #00bfff; border-style: dashed;
                    margin-right: 8px;"></span>
                Wayfinding
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 16px; height: 12px;
                    background-color: rgba(255,165,0,0.5);
                    border: 2px dashed orange;
                    margin-right: 8px;"></span>
                Zone
            </div>

            <button class="refresh-btn" id="refresh-btn" onclick="refreshCurrentMap()">
                Refresh Data
            </button>
        </div>
    </div>

    <script>
        // State
        let currentSiteId = '{{ initial_site_id }}';
        let currentMapId = '{{ initial_map_id }}';
        let allSites = {{ all_sites_json | safe }};
        let currentMaps = {{ all_maps_json | safe }};
        let currentFigure = null;
        let currentMapData = null;  // Store current map data for re-rendering

        // Layer visibility state
        let layerVisibility = {
            aps: true,
            switches: true,
            gateways: true,
            zones: true,
            wifiClients: true,
            unconnectedClients: true,
            bleDevices: true,
            assets: true,
            sdkClients: true,
            walls: true,
            wayfinding: true,
            wifiCoverage: false,
            bleCoverage: false,
            appCoverage: false
        };

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            populateSiteDropdown();
            populateMapDropdown();
            loadMapData(currentSiteId, currentMapId);

            // Event listeners
            document.getElementById('site-select').addEventListener('change', handleSiteChange);
            document.getElementById('map-select').addEventListener('change', handleMapChange);

            // Layer toggle listeners
            document.getElementById('toggle-aps').addEventListener('change', function() {
                layerVisibility.aps = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-switches').addEventListener('change', function() {
                layerVisibility.switches = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-gateways').addEventListener('change', function() {
                layerVisibility.gateways = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-zones').addEventListener('change', function() {
                layerVisibility.zones = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-wifi-clients').addEventListener('change', function() {
                layerVisibility.wifiClients = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-unconnected-clients').addEventListener('change', function() {
                layerVisibility.unconnectedClients = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-ble-devices').addEventListener('change', function() {
                layerVisibility.bleDevices = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-assets').addEventListener('change', function() {
                layerVisibility.assets = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-sdk-clients').addEventListener('change', function() {
                layerVisibility.sdkClients = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-walls').addEventListener('change', function() {
                layerVisibility.walls = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-wayfinding').addEventListener('change', function() {
                layerVisibility.wayfinding = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-wifi-coverage').addEventListener('change', function() {
                layerVisibility.wifiCoverage = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-ble-coverage').addEventListener('change', function() {
                layerVisibility.bleCoverage = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-app-coverage').addEventListener('change', function() {
                layerVisibility.appCoverage = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
        });

        function setStatus(message, isLoading = false) {
            const statusEl = document.getElementById('status-display');
            statusEl.textContent = message;
            statusEl.className = isLoading ? 'status loading' : 'status';
        }

        function populateSiteDropdown() {
            const select = document.getElementById('site-select');
            select.innerHTML = '';
            allSites.forEach(site => {
                const option = document.createElement('option');
                option.value = site.id;
                option.textContent = site.name;
                if (site.id === currentSiteId) option.selected = true;
                select.appendChild(option);
            });
        }

        function populateMapDropdown() {
            const select = document.getElementById('map-select');
            select.innerHTML = '';
            currentMaps.forEach(map => {
                const option = document.createElement('option');
                option.value = map.id;
                option.textContent = map.name;
                if (map.id === currentMapId) option.selected = true;
                select.appendChild(option);
            });
        }

        async function handleSiteChange(event) {
            const newSiteId = event.target.value;
            if (newSiteId === currentSiteId) return;

            setStatus('Loading site...', true);
            console.log('[Site Change] Switching to site:', newSiteId);

            try {
                // Fetch maps for new site
                const response = await fetch('/api/site/' + newSiteId + '/maps');
                if (!response.ok) throw new Error('Failed to fetch maps');

                const data = await response.json();
                currentSiteId = newSiteId;
                currentMaps = data.maps;

                // Update map dropdown
                populateMapDropdown();

                // Load first map if available
                if (currentMaps.length > 0) {
                    currentMapId = currentMaps[0].id;
                    document.getElementById('map-select').value = currentMapId;
                    await loadMapData(currentSiteId, currentMapId);
                } else {
                    currentMapId = null;
                    showEmptyMap('No maps found for this site');
                }

                setStatus('Ready');
            } catch (error) {
                console.error('Error switching site:', error);
                setStatus('Error: ' + error.message);
            }
        }

        async function handleMapChange(event) {
            const newMapId = event.target.value;
            if (newMapId === currentMapId) return;

            currentMapId = newMapId;
            await loadMapData(currentSiteId, currentMapId);
        }

        async function loadMapData(siteId, mapId) {
            if (!siteId || !mapId) {
                showEmptyMap('No map selected');
                return;
            }

            setStatus('Loading map...', true);
            console.log('[Load Map] Fetching data for site:', siteId, 'map:', mapId);

            try {
                const response = await fetch('/api/map/' + siteId + '/' + mapId);
                if (!response.ok) throw new Error('Failed to fetch map data');

                const data = await response.json();
                console.log('[Load Map] Received data:', data);

                // Update info panel
                updateInfoPanel(data);

                // Render Plotly figure
                renderMap(data);

                setStatus('Ready');
            } catch (error) {
                console.error('Error loading map:', error);
                setStatus('Error: ' + error.message);
                showEmptyMap('Error loading map');
            }
        }

        function updateInfoPanel(data) {
            document.getElementById('info-site').textContent = data.site_name || '-';
            document.getElementById('info-map').textContent = data.map_name || '-';
            document.getElementById('info-dims').textContent = data.width + ' x ' + data.height + ' px';
            document.getElementById('info-aps').textContent = data.ap_count || 0;
            document.getElementById('info-switches').textContent = data.switch_count || 0;
            document.getElementById('info-gateways').textContent = data.gateway_count || 0;
            document.getElementById('info-zones').textContent = data.zone_count || 0;
            document.getElementById('info-wifi-clients').textContent = data.wifi_client_count || 0;
            document.getElementById('info-unconnected').textContent = data.unconnected_client_count || 0;
            document.getElementById('info-sdk').textContent = data.sdk_client_count || 0;
            document.getElementById('info-ble').textContent = data.ble_device_count || 0;
            document.getElementById('info-assets').textContent = data.asset_count || 0;
        }

        function renderMap(data) {
            // Store data for re-rendering when toggling layers
            currentMapData = data;

            const traces = [];

            // Add walls traces (render first so they're behind other elements)
            // Walls are line segments: each has x1,y1 -> x2,y2
            if (layerVisibility.walls && data.walls && data.walls.length > 0) {
                console.log('Rendering ' + data.walls.length + ' wall segments');
                let wallX = [];
                let wallY = [];
                for (let i = 0; i < data.walls.length; i++) {
                    const segment = data.walls[i];
                    // Add line segment with null separator
                    wallX.push(segment.x1, segment.x2, null);
                    wallY.push(segment.y1, segment.y2, null);
                }
                if (wallX.length > 0) {
                    traces.push({
                        x: wallX,
                        y: wallY,
                        mode: 'lines',
                        type: 'scatter',
                        name: 'Walls',
                        line: { color: '#ff8c00', width: 6 },
                        hoverinfo: 'name'
                    });
                }
            }

            // Add wayfinding paths - line segments with x1,y1 -> x2,y2
            if (layerVisibility.wayfinding && data.wayfinding && data.wayfinding.length > 0) {
                console.log('Rendering ' + data.wayfinding.length + ' wayfinding segments');
                let pathX = [];
                let pathY = [];
                for (let i = 0; i < data.wayfinding.length; i++) {
                    const segment = data.wayfinding[i];
                    // Add line segment with null separator
                    pathX.push(segment.x1, segment.x2, null);
                    pathY.push(segment.y1, segment.y2, null);
                }
                if (pathX.length > 0) {
                    traces.push({
                        x: pathX,
                        y: pathY,
                        mode: 'lines',
                        type: 'scatter',
                        name: 'Wayfinding',
                        line: { color: '#0066ff', width: 5, dash: 'dash' },
                        hoverinfo: 'name'
                    });
                }
            }

            // Add zones (with labels) - dynamic rainbow colors based on zone count
            if (layerVisibility.zones && data.zones && data.zones.length > 0) {
                // Generate unique colors by evenly subdividing the rainbow (HSL hue 0-360)
                function hslToRgba(h, s, l, a) {
                    const c = (1 - Math.abs(2 * l - 1)) * s;
                    const x = c * (1 - Math.abs((h / 60) % 2 - 1));
                    const m = l - c / 2;
                    let r, g, b;
                    if (h < 60) { r = c; g = x; b = 0; }
                    else if (h < 120) { r = x; g = c; b = 0; }
                    else if (h < 180) { r = 0; g = c; b = x; }
                    else if (h < 240) { r = 0; g = x; b = c; }
                    else if (h < 300) { r = x; g = 0; b = c; }
                    else { r = c; g = 0; b = x; }
                    return `rgba(${Math.round((r + m) * 255)},` +
                        `${Math.round((g + m) * 255)},` +
                        `${Math.round((b + m) * 255)},${a})`;
                }

                const zoneCount = data.zones.length;
                // Golden angle (137.508 degrees) ensures maximum color separation between adjacent zones
                const goldenAngle = 137.508;

                data.zones.forEach((zone, idx) => {
                    if (zone.vertices && zone.vertices.length >= 3) {
                        const zoneX = zone.vertices.map(v => v.x);
                        const zoneY = zone.vertices.map(v => v.y);
                        zoneX.push(zoneX[0]);  // Close polygon
                        zoneY.push(zoneY[0]);

                        // Use golden angle for maximum color separation between sequential zones
                        const hue = (idx * goldenAngle) % 360;
                        const fillColor = hslToRgba(hue, 0.7, 0.6, 0.25);
                        const lineColor = hslToRgba(hue, 0.9, 0.4, 1.0);

                        // Add solid border first (underneath) for overlap visibility
                        traces.push({
                            x: zoneX,
                            y: zoneY,
                            mode: 'lines',
                            type: 'scatter',
                            name: '',
                            showlegend: false,
                            line: { color: lineColor, width: 5 },
                            hoverinfo: 'skip'
                        });

                        // Add filled zone with thinner dashed border on top
                        traces.push({
                            x: zoneX,
                            y: zoneY,
                            mode: 'lines',
                            type: 'scatter',
                            name: zone.name || 'Zone ' + (idx + 1),
                            fill: 'toself',
                            fillcolor: fillColor,
                            line: { color: 'rgba(255,255,255,0.8)', width: 2, dash: 'dot' },
                            hovertemplate: '<b>' + (zone.name || 'Zone') + '</b><extra></extra>'
                        });

                        // Add zone label at centroid
                        const centroidX = zoneX.slice(0, -1).reduce((a, b) => a + b, 0) / (zoneX.length - 1);
                        const centroidY = zoneY.slice(0, -1).reduce((a, b) => a + b, 0) / (zoneY.length - 1);

                        traces.push({
                            x: [centroidX],
                            y: [centroidY],
                            mode: 'markers+text',
                            type: 'scatter',
                            text: [zone.name || 'Zone'],
                            textfont: { size: 16, color: '#1a1a1a', family: 'Arial Black' },
                            textposition: 'middle center',
                            marker: { size: 40, color: 'rgba(255,255,255,0.85)', symbol: 'square' },
                            showlegend: false,
                            hoverinfo: 'skip'
                        });
                    }
                });
            }

            // Helper function for device status-based coloring
            function getDeviceColor(status, connectedColor) {
                const transitionalStatuses = ['restart', 'upgrading', 'reboot_required', 'provisioning'];
                const offlineStatuses = ['disconnected', 'offline'];
                const statusLower = (status || '').toLowerCase();
                if (transitionalStatuses.includes(statusLower)) return '#ff8c00';  // Orange
                if (offlineStatuses.includes(statusLower)) return '#ff4444';  // Red
                return connectedColor;
            }

            // Add Access Points trace (green triangles)
            if (layerVisibility.aps && data.devices && data.devices.length > 0) {
                const aps = data.devices.filter(d => d.type === 'ap' || !d.type);
                if (aps.length > 0) {
                    const apTrace = {
                        x: aps.map(d => d.x),
                        y: aps.map(d => d.y),
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Access Points',
                        text: aps.map(d => d.name),
                        textposition: 'top center',
                        textfont: { size: 14, color: '#1a1a1a', family: 'Arial Bold' },
                        marker: {
                            size: 22,
                            color: aps.map(d => getDeviceColor(d.status, '#00cc00')),
                            symbol: 'triangle-up',
                            angle: aps.map(d => d.orientation || 0),
                            line: { color: '#000000', width: 2 }
                        },
                        hovertemplate: '<b>%{text}</b><br>Type: AP<br>'
                            + 'Status: %{customdata[0]}<br>MAC: %{customdata[1]}<br>'
                            + 'Orientation: %{customdata[2]}deg<extra></extra>',
                        customdata: aps.map(d => [d.status, d.mac, d.orientation || 0])
                    };
                    traces.push(apTrace);
                }
            }

            // Add Switches trace (cyan squares)
            if (layerVisibility.switches && data.devices && data.devices.length > 0) {
                const switches = data.devices.filter(d => d.type === 'switch');
                if (switches.length > 0) {
                    const switchTrace = {
                        x: switches.map(d => d.x),
                        y: switches.map(d => d.y),
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Switches',
                        text: switches.map(d => d.name),
                        textposition: 'top center',
                        textfont: { size: 14, color: '#1a1a1a', family: 'Arial Bold' },
                        marker: {
                            size: 22,
                            color: switches.map(d => getDeviceColor(d.status, '#00ccff')),
                            symbol: 'square',
                            line: { color: '#000000', width: 2 }
                        },
                        hovertemplate: '<b>%{text}</b><br>Type: Switch<br>'
                            + 'Status: %{customdata[0]}<br>MAC: %{customdata[1]}'
                            + '<extra></extra>',
                        customdata: switches.map(d => [d.status, d.mac])
                    };
                    traces.push(switchTrace);
                }
            }

            // Add Gateways trace (purple diamonds)
            if (layerVisibility.gateways && data.devices && data.devices.length > 0) {
                const gateways = data.devices.filter(d => d.type === 'gateway');
                if (gateways.length > 0) {
                    const gatewayTrace = {
                        x: gateways.map(d => d.x),
                        y: gateways.map(d => d.y),
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Gateways',
                        text: gateways.map(d => d.name),
                        textposition: 'top center',
                        textfont: { size: 14, color: '#1a1a1a', family: 'Arial Bold' },
                        marker: {
                            size: 22,
                            color: gateways.map(d => getDeviceColor(d.status, '#cc66ff')),
                            symbol: 'diamond',
                            line: { color: '#000000', width: 2 }
                        },
                        hovertemplate: '<b>%{text}</b><br>Type: Gateway<br>'
                            + 'Status: %{customdata[0]}<br>MAC: %{customdata[1]}'
                            + '<extra></extra>',
                        customdata: gateways.map(d => [d.status, d.mac])
                    };
                    traces.push(gatewayTrace);
                }
            }

            // Add WiFi clients trace (connected - purple)
            if (layerVisibility.wifiClients && data.wifi_clients && data.wifi_clients.length > 0) {
                const wifiClientTrace = {
                    x: data.wifi_clients.map(c => c.x),
                    y: data.wifi_clients.map(c => c.y),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'WiFi Clients',
                    text: data.wifi_clients.map(c => c.name || ''),
                    textposition: 'top center',
                    textfont: { size: 11, color: '#1a1a1a', family: 'Arial' },
                    marker: {
                        size: 14,
                        color: '#9966ff',
                        symbol: 'circle',
                        line: { color: '#4400aa', width: 1 }
                    },
                    hovertemplate: '<b>WiFi Client</b><br>'
                        + 'Name: %{customdata[0]}<br>MAC: %{customdata[1]}<br>'
                        + 'SSID: %{customdata[2]}<extra></extra>',
                    customdata: data.wifi_clients.map(c => [c.name || '-', c.mac || 'Unknown', c.ssid || '-'])
                };
                traces.push(wifiClientTrace);
            }

            // Add unconnected WiFi clients trace (grey)
            if (layerVisibility.unconnectedClients && data.unconnected_clients && data.unconnected_clients.length > 0) {
                const unconnectedTrace = {
                    x: data.unconnected_clients.map(c => c.x),
                    y: data.unconnected_clients.map(c => c.y),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Unconnected Clients',
                    marker: {
                        size: 8,
                        color: '#888888',
                        symbol: 'circle',
                        line: { color: '#444444', width: 1 }
                    },
                    hovertemplate: '<b>Unconnected Client</b><br>'
                        + 'MAC: %{customdata[0]}<br>'
                        + 'Manufacturer: %{customdata[1]}<extra></extra>',
                    customdata: data.unconnected_clients.map(c => [c.mac || 'Unknown', c.manufacture || '-'])
                };
                traces.push(unconnectedTrace);
            }

            // Add BLE/Bluetooth devices trace (dark blue)
            if (layerVisibility.bleDevices && data.ble_devices && data.ble_devices.length > 0) {
                const bleTrace = {
                    x: data.ble_devices.map(d => d.x),
                    y: data.ble_devices.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Bluetooth Devices',
                    marker: {
                        size: 10,
                        color: '#003366',
                        symbol: 'circle',
                        line: { color: '#001a33', width: 1 }
                    },
                    hovertemplate: '<b>BLE Device</b><br>MAC: %{customdata[0]}<extra></extra>',
                    customdata: data.ble_devices.map(d => [d.mac || 'Unknown'])
                };
                traces.push(bleTrace);
            }

            // Add assets trace (green) with name labels
            if (layerVisibility.assets && data.assets && data.assets.length > 0) {
                const assetTrace = {
                    x: data.assets.map(a => a.x),
                    y: data.assets.map(a => a.y),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'Assets',
                    text: data.assets.map(a => a.name || ''),
                    textposition: 'top center',
                    textfont: { size: 12, color: '#1a1a1a', family: 'Arial Bold' },
                    marker: {
                        size: 12,
                        color: '#00cc00',
                        symbol: 'diamond',
                        line: { color: '#006600', width: 1 }
                    },
                    hovertemplate: '<b>Asset</b><br>Name: %{customdata[0]}<br>MAC: %{customdata[1]}<extra></extra>',
                    customdata: data.assets.map(a => [a.name || 'Unknown', a.mac || '-'])
                };
                traces.push(assetTrace);
            }

            // Add SDK/Marvis clients trace (light blue)
            if (layerVisibility.sdkClients && data.sdk_clients && data.sdk_clients.length > 0) {
                const sdkClientTrace = {
                    x: data.sdk_clients.map(c => c.x),
                    y: data.sdk_clients.map(c => c.y),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'App Clients',
                    text: data.sdk_clients.map(c => c.name || ''),
                    textposition: 'top center',
                    textfont: { size: 11, color: '#1a1a1a', family: 'Arial' },
                    marker: {
                        size: 14,
                        color: '#66ccff',
                        symbol: 'circle',
                        line: { color: '#0077cc', width: 1 }
                    },
                    hovertemplate: '<b>App Client</b><br>'
                        + 'Name: %{customdata[0]}<br>'
                        + 'UUID: %{customdata[1]}<extra></extra>',
                    customdata: data.sdk_clients.map(c => [c.name || '-', c.uuid || '-'])
                };
                traces.push(sdkClientTrace);
            }

            // Coverage heatmap traces (rendered below device markers for visibility)
            // Helper function to create coverage heatmap trace
            function createCoverageHeatmap(coverageData, layerName, colorscale) {
                if (!coverageData || coverageData.length === 0) return null;

                // Group coverage data into a grid for heatmap visualization
                const x_values = coverageData.map(p => p.x);
                const y_values = coverageData.map(p => p.y);
                const rssi_values = coverageData.map(p => p.rssi);

                // Create scatter plot with color-coded markers for coverage visualization
                // Using scatter instead of heatmap for better performance with sparse data
                return {
                    x: x_values,
                    y: y_values,
                    mode: 'markers',
                    type: 'scatter',
                    name: layerName,
                    marker: {
                        size: 8,
                        color: rssi_values,
                        colorscale: colorscale,
                        cmin: -90,
                        cmax: -30,
                        opacity: 0.6,
                        showscale: false
                    },
                    hovertemplate: '<b>' + layerName + '</b><br>'
                        + 'RSSI: %{marker.color:.0f} dBm<br>'
                        + 'X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>',
                    visible: true
                };
            }

            // WiFi coverage heatmap
            if (layerVisibility.wifiCoverage && data.wifi_coverage && data.wifi_coverage.length > 0) {
                const wifiHeatmap = createCoverageHeatmap(
                    data.wifi_coverage,
                    'WiFi Coverage',
                    [[0, '#0000ff'], [0.25, '#00ffff'], [0.5, '#00ff00'], [0.75, '#ffff00'], [1, '#ff0000']]
                );
                if (wifiHeatmap) {
                    traces.unshift(wifiHeatmap);  // Add at beginning so it renders below other elements
                }
            }

            // BLE coverage heatmap
            if (layerVisibility.bleCoverage && data.ble_coverage && data.ble_coverage.length > 0) {
                const bleHeatmap = createCoverageHeatmap(
                    data.ble_coverage,
                    'BLE Coverage',
                    [[0, '#4b0082'], [0.25, '#8a2be2'], [0.5, '#ba55d3'], [0.75, '#da70d6'], [1, '#ff69b4']]
                );
                if (bleHeatmap) {
                    traces.unshift(bleHeatmap);
                }
            }

            // App coverage heatmap
            if (layerVisibility.appCoverage && data.app_coverage && data.app_coverage.length > 0) {
                const appHeatmap = createCoverageHeatmap(
                    data.app_coverage,
                    'App Coverage',
                    [[0, '#006400'], [0.25, '#228b22'], [0.5, '#32cd32'], [0.75, '#7cfc00'], [1, '#adff2f']]
                );
                if (appHeatmap) {
                    traces.unshift(appHeatmap);
                }
            }

            const layout = {
                title: {
                    text: data.map_name || 'Map',
                    font: { color: '#e0e0e0', size: 16 }
                },
                images: data.image_url ? [{
                    source: data.image_url,
                    xref: 'x',
                    yref: 'y',
                    x: 0,
                    y: 0,
                    sizex: data.width,
                    sizey: data.height,
                    sizing: 'stretch',
                    layer: 'below'
                }] : [],
                xaxis: {
                    range: [-20, data.width + 20],
                    showgrid: false,
                    zeroline: false,
                    color: '#888'
                },
                yaxis: {
                    range: [data.height + 20, -20],  // Inverted for top-left origin
                    showgrid: false,
                    zeroline: false,
                    scaleanchor: 'x',
                    scaleratio: 1,
                    color: '#888'
                },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#2d2d2d',
                showlegend: true,
                legend: {
                    x: 0.02,
                    y: 0.98,
                    bgcolor: 'rgba(45,45,45,0.9)',
                    bordercolor: '#667eea',
                    font: { color: '#e0e0e0' }
                },
                margin: { l: 50, r: 20, t: 50, b: 30 },
                dragmode: 'pan'
            };

            const config = {
                displayModeBar: true,
                displaylogo: false,
                scrollZoom: true,
                modeBarButtonsToAdd: ['drawline', 'eraseshape'],
                toImageButtonOptions: { format: 'png', filename: 'map_export' }
            };

            Plotly.react('map-display', traces, layout, config);
            currentFigure = { traces, layout };
        }

        function showEmptyMap(message) {
            const layout = {
                title: { text: message, font: { color: '#888', size: 16 } },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#2d2d2d',
                xaxis: { visible: false },
                yaxis: { visible: false }
            };
            Plotly.react('map-display', [], layout, {});
        }

        async function refreshCurrentMap() {
            const btn = document.getElementById('refresh-btn');
            btn.disabled = true;
            btn.textContent = 'Refreshing...';

            await loadMapData(currentSiteId, currentMapId);

            btn.disabled = false;
            btn.textContent = 'Refresh Data';
        }
    </script>
</body>
</html>
        """

        @flask_app.route("/")
        def index():
            """Serve the main viewer page."""
            # Prepare sites JSON (sorted by name)
            sites_sorted = sorted(all_sites, key=lambda x: x.get("name", "").lower())
            sites_json = json_module.dumps(
                [{"id": s.get("id"), "name": s.get("name", "Unnamed")} for s in sites_sorted]
            )

            # Prepare maps JSON
            maps_json = json_module.dumps([{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in all_maps])

            return render_template_string(
                HTML_TEMPLATE,
                initial_site_id=initial_site_id,
                initial_map_id=initial_map_id,
                all_sites_json=sites_json,
                all_maps_json=maps_json,
            )

        @flask_app.route("/api/site/<site_id>/maps")
        def get_site_maps(site_id):
            """API endpoint to get maps for a site."""
            logging.info(f"[Flask API] Fetching maps for site {site_id}")
            try:
                maps_response = mistapi.api.v1.sites.maps.listSiteMaps(api_session, site_id=site_id)
                if maps_response.status_code == 200 and maps_response.data:
                    maps = [{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in maps_response.data]
                    return jsonify({"maps": maps})
                else:
                    return jsonify({"maps": []})
            except Exception as e:
                logging.error(f"Error fetching maps: {e}")
                return jsonify({"error": str(e), "maps": []}), 500

        @flask_app.route("/api/map-image/<site_id>/<map_id>")
        def get_map_image(site_id, map_id):
            """Proxy endpoint to serve map images with authentication."""
            logging.info(f"[Flask API] Fetching map image for site {site_id}, map {map_id}")
            try:
                # Get the map to find the image URL
                map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)

                if map_response.status_code != 200:
                    return "Map not found", 404

                image_url = map_response.data.get("url", "")
                if not image_url:
                    return "No image URL", 404

                # Fetch the image with authentication
                import requests as req_lib

                headers = {
                    "Authorization": f"Token {api_session._api_token}" if hasattr(api_session, "_api_token") else ""
                }

                # Try to get the image - Mist URLs may be direct or require auth
                image_response = req_lib.get(image_url, headers=headers, timeout=30)

                if image_response.status_code == 200:
                    content_type = image_response.headers.get("Content-Type", "image/png")
                    from flask import Response

                    return Response(image_response.content, mimetype=content_type)
                else:
                    logging.warning(f"Failed to fetch image: {image_response.status_code}")
                    return f"Image fetch failed: {image_response.status_code}", 404

            except Exception as e:
                logging.error(f"Error fetching map image: {e}")
                return str(e), 500

        @flask_app.route("/api/map/<site_id>/<map_id>")
        def get_map_data(site_id, map_id):
            """API endpoint to get full map data including devices, zones, clients."""
            logging.info(f"[Flask API] Fetching map data for site {site_id}, map {map_id}")
            try:
                # Get site name
                site_name = "Unknown"
                for site in all_sites:
                    if site.get("id") == site_id:
                        site_name = site.get("name", "Unknown")
                        break

                # Fetch map details
                map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)

                if map_response.status_code != 200:
                    return jsonify({"error": "Map not found"}), 404

                map_data = map_response.data
                map_name = map_data.get("name", "Unnamed")
                map_width = map_data.get("width", 1000)
                map_height = map_data.get("height", 1000)
                ppm = map_data.get("ppm", 1.0)  # Pixels per meter for coverage grid alignment
                # Use our proxy endpoint for the image (browser can't auth to Mist directly)
                original_url = map_data.get("url", "")
                image_url = f"/api/map-image/{site_id}/{map_id}" if original_url else ""

                # Extract walls from map data - it's a graph with nodes and edges
                walls = []
                wall_data = map_data.get("wall_path", {})
                if wall_data:
                    logging.debug(f"[Flask API] Raw wall_path data: {wall_data}")
                    nodes = wall_data.get("nodes", [])
                    if nodes:
                        # Build a lookup of nodes by name
                        node_lookup = {}
                        for node in nodes:
                            node_name = node.get("name", "")
                            position = node.get("position", {})
                            if position:
                                node_lookup[node_name] = {"x": position.get("x", 0), "y": position.get("y", 0)}

                        # Convert edges to line segments
                        for node in nodes:
                            node_name = node.get("name", "")
                            position = node.get("position", {})
                            edges = node.get("edges", {})
                            if position and edges:
                                start_x = position.get("x", 0)
                                start_y = position.get("y", 0)
                                for edge_name in edges.keys():
                                    if edge_name in node_lookup:
                                        end_pos = node_lookup[edge_name]
                                        # Add line segment (from current node to connected node)
                                        walls.append(
                                            {"x1": start_x, "y1": start_y, "x2": end_pos["x"], "y2": end_pos["y"]}
                                        )
                        logging.info(f"[Flask API] Extracted {len(walls)} wall segments from {len(nodes)} nodes")

                # Extract wayfinding paths from map data - same structure as walls
                wayfinding = []
                wayfinding_data = map_data.get("wayfinding_path", {})
                if wayfinding_data:
                    logging.debug(f"[Flask API] Raw wayfinding_path data: {wayfinding_data}")
                    nodes = wayfinding_data.get("nodes", [])
                    if nodes:
                        # Build a lookup of nodes by name
                        node_lookup = {}
                        for node in nodes:
                            node_name = node.get("name", "")
                            position = node.get("position", {})
                            if position:
                                node_lookup[node_name] = {"x": position.get("x", 0), "y": position.get("y", 0)}

                        # Convert edges to line segments
                        for node in nodes:
                            node_name = node.get("name", "")
                            position = node.get("position", {})
                            edges = node.get("edges", {})
                            if position and edges:
                                start_x = position.get("x", 0)
                                start_y = position.get("y", 0)
                                for edge_name in edges.keys():
                                    if edge_name in node_lookup:
                                        end_pos = node_lookup[edge_name]
                                        wayfinding.append(
                                            {"x1": start_x, "y1": start_y, "x2": end_pos["x"], "y2": end_pos["y"]}
                                        )
                        logging.info(
                            f"[Flask API] Extracted {len(wayfinding)} wayfinding segments from {len(nodes)} nodes"
                        )

                # Fetch devices (type='all' includes APs, switches, and gateways)
                devices = []
                try:
                    devices_response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                        api_session, site_id=site_id, type="all", limit=1000
                    )
                    if devices_response.status_code == 200 and devices_response.data:
                        for d in devices_response.data:
                            if d.get("map_id") == map_id and d.get("x") is not None:
                                devices.append(
                                    {
                                        "x": d.get("x"),
                                        "y": d.get("y"),
                                        "name": d.get("name", d.get("mac", "Unknown")),
                                        "type": d.get("type", "ap"),
                                        "status": d.get("status", "unknown"),
                                        "mac": d.get("mac", ""),
                                        "orientation": d.get("orientation", 0),
                                    }
                                )
                except Exception as e:
                    logging.warning(f"Error fetching devices: {e}")

                # Fetch zones
                zones = []
                try:
                    zones_response = mistapi.api.v1.sites.zones.listSiteZones(api_session, site_id=site_id)
                    if zones_response.status_code == 200 and zones_response.data:
                        for z in zones_response.data:
                            if z.get("map_id") == map_id:
                                zones.append({"name": z.get("name", "Zone"), "vertices": z.get("vertices", [])})
                except Exception as e:
                    logging.warning(f"Error fetching zones: {e}")

                # Fetch connected WiFi clients (purple)
                wifi_clients = []
                try:
                    clients_response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
                        api_session, site_id=site_id
                    )
                    if clients_response.status_code == 200 and clients_response.data:
                        for c in clients_response.data:
                            if c.get("map_id") == map_id and c.get("x") is not None:
                                wifi_clients.append(
                                    {
                                        "x": c.get("x"),
                                        "y": c.get("y"),
                                        "mac": c.get("mac", "Unknown"),
                                        "ssid": c.get("ssid", "-"),
                                        "name": c.get("hostname", "") or c.get("name", ""),
                                    }
                                )
                except Exception as e:
                    logging.warning(f"Error fetching WiFi clients: {e}")

                # Fetch unconnected WiFi clients (grey)
                unconnected_clients = []
                try:
                    # Unconnected client stats require map_id in the API call
                    unconnected_response = mistapi.api.v1.sites.stats.listSiteUnconnectedClientStats(
                        api_session, site_id=site_id, map_id=map_id
                    )
                    if unconnected_response.status_code == 200 and unconnected_response.data:
                        for c in unconnected_response.data:
                            if c.get("x") is not None:
                                unconnected_clients.append(
                                    {
                                        "x": c.get("x"),
                                        "y": c.get("y"),
                                        "mac": c.get("mac", "Unknown"),
                                        "manufacture": c.get("manufacture", "-"),
                                    }
                                )
                except Exception as e:
                    logging.warning(f"Error fetching unconnected clients: {e}")

                # Fetch BLE/Bluetooth discovered assets (blue)
                ble_devices = []
                try:
                    ble_response = mistapi.api.v1.sites.stats.listSiteDiscoveredAssets(api_session, site_id=site_id)
                    if ble_response.status_code == 200 and ble_response.data:
                        for d in ble_response.data:
                            if d.get("map_id") == map_id and d.get("x") is not None:
                                ble_devices.append({"x": d.get("x"), "y": d.get("y"), "mac": d.get("mac", "Unknown")})
                except Exception as e:
                    logging.warning(f"Error fetching BLE devices: {e}")

                # Fetch named assets (green)
                assets = []
                try:
                    assets_response = mistapi.api.v1.sites.stats.listSiteAssetsStats(api_session, site_id=site_id)
                    if assets_response.status_code == 200 and assets_response.data:
                        for a in assets_response.data:
                            if a.get("map_id") == map_id and a.get("x") is not None:
                                assets.append(
                                    {
                                        "x": a.get("x"),
                                        "y": a.get("y"),
                                        "name": a.get("name", "Asset"),
                                        "mac": a.get("mac", "-"),
                                    }
                                )
                except Exception as e:
                    logging.warning(f"Error fetching assets: {e}")

                # Fetch SDK/Marvis clients (light blue) - these use the Mist SDK for indoor location
                sdk_clients = []
                try:
                    sdk_response = mistapi.api.v1.sites.stats.getSiteSdkStatsByMap(
                        api_session, site_id=site_id, map_id=map_id
                    )
                    if sdk_response.status_code == 200 and sdk_response.data:
                        for c in sdk_response.data:
                            if c.get("x") is not None:
                                sdk_clients.append(
                                    {
                                        "x": c.get("x"),
                                        "y": c.get("y"),
                                        "name": c.get("name", ""),
                                        "uuid": c.get("uuid", "-"),
                                    }
                                )
                except Exception as e:
                    logging.warning(f"Error fetching SDK clients: {e}")

                # Fetch RF coverage data for WiFi, BLE, and App (SDK) clients
                # Coverage API: /api/v1/sites/{site_id}/location/coverage
                # Types: 'client' (WiFi), 'asset' (BLE), 'sdkclient' (App)
                def fetch_coverage(coverage_type, ppm_value):
                    """Fetch coverage heatmap data for a specific type and convert to pixels."""
                    try:
                        coverage_url = f"/api/v1/sites/{site_id}/location/coverage"
                        coverage_params = {
                            "resolution": "fine",
                            "duration": "1d",
                            "map_id": map_id,
                            "type": coverage_type,
                            "from_apollo": "true",
                        }
                        logging.info(f"[Flask API] Fetching {coverage_type} coverage for map {map_id}")
                        coverage_response = api_session.mist_get(coverage_url, query=coverage_params)

                        if coverage_response.status_code == 200:
                            coverage_data = coverage_response.data
                            # Check for error response
                            if isinstance(coverage_data, dict) and "exception" in coverage_data:
                                logging.warning(f"[Flask API] {coverage_type} coverage API error")
                                return None

                            results = coverage_data.get("results", [])
                            result_def = coverage_data.get("result_def", [])
                            if results and result_def:
                                # Get field indices
                                try:
                                    x_idx = result_def.index("x")
                                    y_idx = result_def.index("y")
                                    if "max_rssi" in result_def:
                                        rssi_idx = result_def.index("max_rssi")
                                    elif "avg_rssi" in result_def:
                                        rssi_idx = result_def.index("avg_rssi")
                                    else:
                                        rssi_idx = -1
                                except ValueError:
                                    x_idx, y_idx, rssi_idx = 0, 1, 4

                                # Build grid data - results is list of lists
                                # Coverage API returns x, y in meters - convert to pixels using ppm
                                grid_points = []
                                for item in results:
                                    if len(item) > max(x_idx, y_idx, rssi_idx):
                                        x_m = item[x_idx]
                                        y_m = item[y_idx]
                                        rssi = item[rssi_idx] if rssi_idx >= 0 else -80
                                        if x_m is not None and y_m is not None and rssi is not None:
                                            # Convert meters to pixels
                                            x_px = x_m * ppm_value
                                            y_px = y_m * ppm_value
                                            grid_points.append({"x": x_px, "y": y_px, "rssi": rssi})

                                logging.info(
                                    f"[Flask API] {coverage_type} coverage: "
                                    f"{len(grid_points)} grid points (ppm={ppm_value})"
                                )
                                return grid_points
                        return None
                    except Exception as e:
                        logging.warning(f"Error fetching {coverage_type} coverage: {e}")
                        return None

                wifi_coverage = fetch_coverage("client", ppm) if ppm else []
                ble_coverage = fetch_coverage("asset", ppm) if ppm else []
                app_coverage = fetch_coverage("sdkclient", ppm) if ppm else []

                # Ensure coverage lists are not None
                wifi_coverage = wifi_coverage or []
                ble_coverage = ble_coverage or []
                app_coverage = app_coverage or []

                # Count devices by type
                ap_count = len([d for d in devices if d.get("type") == "ap" or not d.get("type")])
                switch_count = len([d for d in devices if d.get("type") == "switch"])
                gateway_count = len([d for d in devices if d.get("type") == "gateway"])

                return jsonify(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "map_id": map_id,
                        "map_name": map_name,
                        "width": map_width,
                        "height": map_height,
                        "image_url": image_url,
                        "ppm": ppm,
                        "devices": devices,
                        "device_count": len(devices),
                        "ap_count": ap_count,
                        "switch_count": switch_count,
                        "gateway_count": gateway_count,
                        "zones": zones,
                        "zone_count": len(zones),
                        "wifi_clients": wifi_clients,
                        "wifi_client_count": len(wifi_clients),
                        "unconnected_clients": unconnected_clients,
                        "unconnected_client_count": len(unconnected_clients),
                        "ble_devices": ble_devices,
                        "ble_device_count": len(ble_devices),
                        "assets": assets,
                        "asset_count": len(assets),
                        "sdk_clients": sdk_clients,
                        "sdk_client_count": len(sdk_clients),
                        "walls": walls,
                        "wall_count": len(walls),
                        "wayfinding": wayfinding,
                        "wayfinding_count": len(wayfinding),
                        "wifi_coverage": wifi_coverage,
                        "ble_coverage": ble_coverage,
                        "app_coverage": app_coverage,
                    }
                )

            except Exception as e:
                logging.error(f"Error fetching map data: {e}", exc_info=True)
                return jsonify({"error": str(e)}), 500

        # Determine host and port
        flask_host = "127.0.0.1"
        flask_port = 8050

        if is_running_in_container():
            flask_host = "0.0.0.0"  # nosec B104 — container must bind all interfaces
            logging.debug("Container detected: binding Flask to 0.0.0.0")

        print("\n" + "-" * 80)
        print("LAUNCHING FLASK MAP VIEWER")
        print("-" * 80)
        print(f"! Server URL: http://{flask_host}:{flask_port}")
        print("! Features:")
        print("!   - Site and map switching via dropdowns")
        print("!   - Device, zone, and client visualization")
        print("!   - Pan and zoom controls")
        print("!   - Refresh button for live data")
        print("! Press Ctrl+C to stop server")
        print("-" * 80)

        # Open browser after short delay
        def open_browser():
            import time

            time.sleep(1.5)
            webbrowser.open(f"http://127.0.0.1:{flask_port}")

        if not is_running_in_container():
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()

        # Run Flask server
        try:
            logging.info(f"Starting Flask server on http://{flask_host}:{flask_port}")
            flask_app.run(host=flask_host, port=flask_port, debug=False, threaded=True, use_reloader=False)
        except KeyboardInterrupt:
            print("\n\nFlask map viewer stopped by user")
            logging.info("Flask map viewer stopped by user (Ctrl+C)")
        except Exception as e:
            logging.error(f"Error running Flask server: {e}", exc_info=True)
            print(f"\n! Error running map viewer: {e}")

    def _create_static_plotly_map(self, map_data, devices):
        """Create static Plotly HTML map when Dash is not available."""
        import os
        import tempfile
        import webbrowser

        import plotly.graph_objects as go

        print("\n! Creating static HTML map...")

        # Similar to _launch_plotly_viewer but save to HTML file
        fig = go.Figure()

        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)

        if "url" in map_data:
            fig.add_layout_image(
                source=map_data["url"],
                x=0,
                y=map_height,
                sizex=map_width,
                sizey=map_height,
                xref="x",
                yref="y",
                sizing="stretch",
                layer="below",
            )

        # Add devices (simplified version)
        if devices:
            x_coords = [d.get("x", 0) for d in devices if "x" in d]
            y_coords = [map_height - d.get("y", 0) for d in devices if "y" in d]
            names = [d.get("name", d.get("mac", "Unknown")) for d in devices if "x" in d]

            fig.add_trace(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="markers+text",
                    name="Devices",
                    marker=dict(size=10, color="green"),
                    text=names,
                    textposition="top center",
                )
            )

        fig.update_layout(
            title=f"Map: {map_data.get('name', 'Unnamed')}",
            xaxis=dict(range=[0, map_width]),
            yaxis=dict(range=[0, map_height], scaleanchor="x", scaleratio=1),
            height=800,
        )

        # Save to temp HTML file
        temp_html = os.path.join(tempfile.gettempdir(), f"mist_map_{map_data.get('id', 'unknown')[:8]}.html")
        logging.debug(f"Saving static map to: {temp_html}")
        fig.write_html(temp_html)

        print(f"\n! Map saved to: {temp_html}")
        print("! Opening in browser...")
        logging.info(f"Static HTML map created: {temp_html}")
        webbrowser.open(f"file://{temp_html}")
        logging.debug("Browser launched with static map")

    def _launch_matplotlib_viewer(self, map_data, devices):
        """Fallback matplotlib viewer (view-only)."""
        logging.info("_launch_matplotlib_viewer called - basic fallback mode")
        from math import cos, radians, sin

        import matplotlib.pyplot as plt

        print("\n! Using matplotlib viewer (view-only, no interactivity)")
        logging.debug("Creating matplotlib figure for basic visualization")

        fig, ax = plt.subplots(figsize=(12, 10))

        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)

        ax.set_xlim(0, map_width)
        ax.set_ylim(0, map_height)
        ax.set_aspect("equal")
        ax.set_title(f"Map: {map_data.get('name', 'Unnamed')}")
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")

        # Plot devices
        for device in devices:
            if "x" not in device or "y" not in device:
                continue

            x, y = device["x"], device["y"]
            device_type = device.get("type", "unknown")
            name = device.get("name", device.get("mac", "Unknown"))
            orientation = device.get("orientation", 0)

            # Color by type
            color = {"ap": "green", "switch": "orange", "gateway": "purple"}.get(device_type, "gray")

            # Plot device
            ax.plot(
                x,
                y,
                marker="o",
                markersize=10,
                color=color,
                label=device_type if device_type not in ax.get_legend_handles_labels()[1] else "",
            )
            ax.text(x, y + 20, name, fontsize=8, ha="center")

            # Add orientation arrow
            if orientation != 0:
                arrow_length = 30
                dx = arrow_length * cos(radians(orientation))
                dy = arrow_length * sin(radians(orientation))
                ax.arrow(x, y, dx, dy, head_width=10, head_length=10, fc=color, ec=color, alpha=0.7)

        ax.legend()
        ax.grid(True, alpha=0.3)

        print("\n! Displaying map... Close window to return to menu")
        logging.info("Displaying matplotlib figure (blocking until window closed)")
        plt.show()
        logging.info("Matplotlib map viewer closed by user")

    def launch_viewer_standalone(self, requested_site_id: str = None, requested_map_id: str = None):
        """Launch the interactive map viewer directly without CLI site selection.

        This method is designed for standalone usage (e.g., maps_manager.py --viewer)
        where the user wants to skip the CLI menu and select sites/maps directly
        in the web browser interface via searchable dropdowns.

        Uses the full-featured viewer with all layers, controls, and sidebar.
        Site/map selection is handled in-browser via URL parameters.

        Args:
            requested_site_id: Optional site ID to load initially (from URL parameter)
            requested_map_id: Optional map ID to load initially (from URL parameter)
        """
        logging.info("launch_viewer_standalone: Starting web-first viewer mode")

        # Fetch all sites upfront
        print("\n" + "=" * 70)
        print("  MAPS MANAGER - Standalone Web Viewer")
        print("  Select a site and map from the browser interface")
        print("=" * 70)

        print("\n  Loading sites...")
        all_sites = self._fetch_sites()
        if not all_sites:
            print("\n  [!] No sites found in organization")
            return

        sites_sorted = sorted(all_sites, key=lambda x: x.get("name", "").lower())
        print(f"  Found {len(sites_sorted)} sites")

        # Use requested site_id if provided and valid, otherwise look for default test site, then first site
        valid_site_ids = {s.get("id"): s for s in sites_sorted}
        default_test_site_name = "CAS0123G"  # Default test site with walls/wayfinding configured

        if requested_site_id and requested_site_id in valid_site_ids:
            target_site = valid_site_ids[requested_site_id]
            target_site_id = requested_site_id
            target_site_name = target_site.get("name", "Unknown")
            logging.info(f"launch_viewer_standalone: Using requested site {target_site_name}")
        else:
            # Look for default test site by name first
            target_site = next((s for s in sites_sorted if s.get("name", "") == default_test_site_name), None)
            if target_site:
                target_site_id = target_site.get("id")
                target_site_name = target_site.get("name", "Unknown")
                logging.info(f"launch_viewer_standalone: Using default test site {target_site_name}")
            else:
                # Fall back to first site
                target_site = sites_sorted[0]
                target_site_id = target_site.get("id")
                target_site_name = target_site.get("name", "Unknown")

        print(f"  Loading maps for site: {target_site_name}...")

        # Fetch maps for target site
        try:
            maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=target_site_id)
            if maps_response.status_code == 200 and maps_response.data:
                all_maps = maps_response.data
            else:
                all_maps = []
        except Exception as maps_error:
            logging.error(f"Error fetching maps: {maps_error}")
            all_maps = []

        if not all_maps:
            print(f"\n  [!] No maps found for site {target_site_name}")
            print("  Launching viewer anyway - select a different site in browser")
            # Create placeholder state for initial load
            devices = []
            zones = []
            clients = []
            map_id = None
        else:
            # Use requested map_id if provided and valid, otherwise use first map
            valid_map_ids = {m.get("id"): m for m in all_maps}
            if requested_map_id and requested_map_id in valid_map_ids:
                target_map = valid_map_ids[requested_map_id]
                map_id = requested_map_id
                logging.info(f"launch_viewer_standalone: Using requested map {target_map.get('name')}")
            else:
                target_map = all_maps[0]
                map_id = target_map.get("id")

            print(f"  Loading map: {target_map.get('name', 'Unnamed')}...")

            # Fetch devices for this map (type='all' includes APs, switches, and gateways)
            try:
                devices_response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                    self.apisession, site_id=target_site_id, type="all", limit=1000
                )
                if devices_response.status_code == 200:
                    all_devices = devices_response.data or []
                    devices = [d for d in all_devices if d.get("map_id") == map_id]
                else:
                    devices = []
            except Exception:
                devices = []

            # Fetch zones for this site
            try:
                zones_response = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=target_site_id)
                if zones_response.status_code == 200:
                    all_zones = zones_response.data or []
                    zones = [z for z in all_zones if z.get("map_id") == map_id]
                else:
                    zones = []
            except Exception:
                zones = []

            # Fetch clients for this map
            try:
                clients_response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
                    self.apisession, site_id=target_site_id
                )
                if clients_response.status_code == 200:
                    all_clients = clients_response.data or []
                    clients = [c for c in all_clients if c.get("map_id") == map_id]
                else:
                    clients = []
            except Exception:
                clients = []

            print(f"  Found {len(devices)} devices, {len(zones)} zones, {len(clients)} clients")

        # Launch the Flask-based viewer (simpler and more reliable than Dash)
        self._launch_flask_viewer(
            initial_site_id=target_site_id, initial_map_id=map_id, all_sites=sites_sorted, all_maps=all_maps
        )


# ============================================================================
# STANDALONE ENTRY POINT
# ============================================================================


def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MapsManager - Interactive Map Viewer for Mist Networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python maps_manager.py                    # Launch interactive viewer (default)
    python maps_manager.py --menu             # Show menu for non-viewer operations
    python maps_manager.py --org <ORG_ID>     # Use specific org ID
        """,
    )
    parser.add_argument("--menu", action="store_true", help="Show operations menu instead of launching viewer directly")
    parser.add_argument("--org", type=str, default=None, help="Organization ID to use (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test", action="store_true", help="Run systematic test of safe, non-destructive operations")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join("data", "maps_manager.log"), encoding="utf-8"),
        ],
    )

    # Check dependencies
    if not DASH_AVAILABLE or not PLOTLY_AVAILABLE:
        print("ERROR: This module requires dash and plotly packages.")
        print("Install with: pip install dash plotly")
        sys.exit(1)

    if not mistapi:
        print("ERROR: This module requires the mistapi package.")
        print("Install with: pip install mistapi")
        sys.exit(1)

    # Initialize API session
    try:
        # Try to load from environment or .env file
        env_file = ".env"
        if os.path.exists(env_file):
            apisession = mistapi.APISession(env_file=env_file)
        else:
            print("No .env file found. Please provide Mist API credentials.")
            host = input("Mist API Host [api.mist.com]: ").strip() or "api.mist.com"
            token = input("API Token: ").strip()
            apisession = mistapi.APISession(host=host, token=token)

        apisession.login()

    except Exception as e:
        print(f"ERROR: Failed to initialize API session: {e}")
        sys.exit(1)

    # Get org_id
    org_id = args.org
    if not org_id:
        # Try to get from environment variable first
        org_id = os.getenv("org_id") or os.getenv("ORG_ID") or os.getenv("MIST_ORG_ID")

    if not org_id:
        # Try to get from session
        try:
            self_info = mistapi.api.v1.self.self.getSelf(apisession)
            if hasattr(self_info, "data") and self_info.data:
                privileges = self_info.data.get("privileges", [])
                orgs = [p.get("org_id") for p in privileges if p.get("scope") == "org" and p.get("org_id")]
                if len(orgs) == 1:
                    org_id = orgs[0]
                elif len(orgs) > 1:
                    # In test mode, use first org automatically
                    if args.test:
                        org_id = orgs[0]
                        print(f"Test mode: Using first available org: {org_id}")
                    else:
                        print("\nAvailable Organizations:")
                        for idx, oid in enumerate(orgs, 1):
                            print(f"  {idx}. {oid}")
                        choice = input("Select organization number: ").strip()
                        try:
                            org_id = orgs[int(choice) - 1]
                        except (ValueError, IndexError):
                            print("Invalid selection")
                            sys.exit(1)
        except Exception as e:
            logger.warning(f"Could not auto-detect org_id: {e}")

    if not org_id:
        if args.test:
            print("ERROR: Organization ID required for test mode. Set org_id in .env or use --org flag")
            sys.exit(1)
        org_id = input("Organization ID: ").strip()

    if not org_id:
        print("ERROR: Organization ID is required")
        sys.exit(1)

    # Create and run MapsManager
    maps_manager = MapsManager(apisession, org_id)

    if args.test:
        # Run systematic test mode
        success = maps_manager.run_systematic_test()
        sys.exit(0 if success else 1)
    elif args.menu:
        # Show operations menu
        maps_manager.run_interactive_menu()
    else:
        # Launch interactive viewer directly
        maps_manager.launch_viewer_standalone()


if __name__ == "__main__":
    main()
