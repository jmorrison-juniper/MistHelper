"""
FirmwareManager - Firmware upgrade status checking and execution.

Manages firmware upgrades for APs, switches, and SSR devices across
Mist organization sites.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import csv
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

# Type aliases for injected dependencies
SafeInputFn = Callable[..., str]
SelectSiteFn = Callable[..., Any]
CheckCacheFn = Callable[..., Any]
GetCsvPathFn = Callable[[str], str]
GeneratorFn = Callable[..., Any]

# ── Module-level stubs for globals declared in method bodies ──────────────────
# Methods use 'global <name>' to read/write these at runtime.
# apisession and org_id are set per-instance in __init__.
# msp_privileges and PROGRESS_EMITTER are sourced from the main module in __init__.
msp_privileges: list[Any] = []
apisession: Any = None
org_id: str = ""
PROGRESS_EMITTER: Any = None


try:
    import mistapi
except ImportError:  # pragma: no cover
    mistapi = None  # type: ignore[assignment]


class FirmwareManager:
    """
    Advanced Firmware Management System for Mist Access Points

    This class provides comprehensive firmware upgrade capabilities including:
    1. Firmware status monitoring and reporting
    2. Site-based bulk firmware upgrades
    3. Gateway template-based firmware upgrades
    4. Automatic site auto-upgrade configuration
    5. Multi-strategy upgrade orchestration (big_bang, canary, rrm, serial)
    6. Progress monitoring and audit logging

    Follows NASA/JPL coding standards for safety-critical operations with:
    - Comprehensive validation and error handling
    - Explicit user confirmation for destructive operations
    - Complete audit trails and logging
    - Rollback and recovery capabilities
    """

    def __init__(  # type: ignore[no-untyped-def]
        self,
        apisession: Any,
        org_id: str,
        safe_input_fn: SafeInputFn | None = None,
        select_site_fn: SelectSiteFn | None = None,
        check_cache_fn: CheckCacheFn | None = None,
        get_csv_path_fn: GetCsvPathFn | None = None,
        gateway_templates_fn: GeneratorFn | None = None,
        sites_fn: GeneratorFn | None = None,
    ) -> None:
        """
        Initialize FirmwareManager with API session and organization context.

        Args:
            apisession: Authenticated Mist API session
            org_id: Organization ID for operations
            safe_input_fn: Callable for safe user input
            select_site_fn: Callable for interactive site selection
            check_cache_fn: Callable for cache-checked CSV generation
            get_csv_path_fn: Callable for CSV path resolution
            gateway_templates_fn: Callable for gateway templates generation
            sites_fn: Callable for sites generation
        """
        import sys as _sys

        self.apisession = apisession
        self.org_id = org_id
        self._safe_input_fn: SafeInputFn = safe_input_fn or input
        self._select_site_fn = select_site_fn
        self._check_cache_fn = check_cache_fn
        self._get_csv_path_fn = get_csv_path_fn
        self._gateway_templates_fn = gateway_templates_fn
        self._sites_fn = sites_fn

        # Populate module-level globals used by methods with 'global' declarations
        _mod = _sys.modules[__name__]
        _mod.apisession = apisession  # type: ignore[attr-defined]
        _mod.org_id = org_id  # type: ignore[attr-defined]
        _main = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
        if _main is not None:
            _mod.msp_privileges = getattr(_main, "msp_privileges", [])  # type: ignore[attr-defined]
            _mod.PROGRESS_EMITTER = getattr(_main, "PROGRESS_EMITTER", None)  # type: ignore[attr-defined]

        logging.info(f"FirmwareManager initialized for org_id: {org_id}")

    def _is_firmware_downgrade(self, current_version, target_version):  # type: ignore[no-untyped-def]  # noqa: C901
        """
        Check if the target version is a downgrade from the current version.

        This method performs a basic version comparison to detect potential downgrades.
        SSR firmware versions typically follow patterns like: 6.3.4-7.r2, 6.3.5-37.sts

        Args:
            current_version (str): Current firmware version
            target_version (str): Target firmware version

        Returns:
            bool: True if target_version appears to be older than current_version
        """
        try:
            # Handle empty versions
            if not current_version or not target_version:
                return False

            # Extract major.minor.patch from versions like "6.3.4-7.r2" or "6.3.5-37.sts"
            current_parts = current_version.split("-")[0].split(".")
            target_parts = target_version.split("-")[0].split(".")

            # Pad shorter version to same length
            max_len = max(len(current_parts), len(target_parts))
            while len(current_parts) < max_len:
                current_parts.append("0")
            while len(target_parts) < max_len:
                target_parts.append("0")

            # Compare version parts numerically
            for current_part, target_part in zip(current_parts, target_parts, strict=False):
                try:
                    current_num = int(current_part)
                    target_num = int(target_part)

                    if target_num < current_num:
                        return True  # Downgrade detected
                    elif target_num > current_num:
                        return False  # Upgrade
                    # If equal, continue to next part
                except ValueError:
                    # Non-numeric parts, fall back to string comparison
                    if target_part < current_part:
                        return True
                    elif target_part > current_part:
                        return False

            # Versions are equal
            return False

        except Exception as e:
            logging.warning(f"Could not compare versions {current_version} vs {target_version}: {e}")
            # If we can't compare, err on the side of caution and allow the upgrade
            return False

    def check_firmware_upgrade_status(self, scope_choice=None, site_filter=None):  # type: ignore[no-untyped-def]
        """
        Check current firmware upgrade status across the organization.

        This method provides comprehensive upgrade status monitoring with:
        1. Device-level firmware status from device statistics (fwupdate field)
        2. Site-level upgrade operations and history
        3. Organization-wide upgrade tracking
        4. Current version vs. available version comparison
        5. Upgrade progress monitoring for active operations
        6. Failed upgrade identification and retry status
        7. Bulk status export to CSV for analysis
        8. Interactive site/device filtering options

        Args:
            scope_choice: Optional pre-selected scope (1-4)
            site_filter: Optional pre-selected site ID

        Reports include:
        - Current firmware versions and upgrade status per device
        - Active upgrade operations with progress tracking
        - Failed upgrades with error details and retry information
        - Upgrade history and completion statistics
        - Version mismatch identification across sites
        """
        logging.info("Starting firmware upgrade status check...")
        logging.debug("FirmwareManager.check_firmware_upgrade_status() initiated")

        print(" Firmware Upgrade Status Check")
        print("=" * 60)

        # Step 1: Choose scope (organization-wide or specific site) if not provided
        if scope_choice is None:
            print("\n  Select status check scope:")
            print("   [1] Organization-wide status (all sites and devices)")
            print("   [2] Specific site status")
            print("   [3] Active upgrade operations only")
            print("   [4] Failed upgrades only")
            print("   [5] Continuous monitoring mode (auto-refresh until complete)")
            print("   [6] Org-level upgrade jobs (with P2P/scheduling details)")

            while True:
                try:
                    scope_choice = self._safe_input_fn("Select scope (1-6): ", context="firmware_manager").strip()
                    if scope_choice in ["1", "2", "3", "4", "5", "6"]:
                        logging.debug(f"User selected scope: {scope_choice}")
                        break
                    else:
                        print(" Invalid selection. Please choose 1-6.")
                        logging.debug(f"Invalid scope selection: {scope_choice}")
                except KeyboardInterrupt:
                    print("\n Operation cancelled by user.")
                    return

        if scope_choice == "2" and site_filter is None:
            # Get specific site selection
            logging.debug("User selected specific site mode")
            site_filter = self._select_site_fn()
            if not site_filter:
                print(" No site selected. Exiting.")
                logging.warning("No site selected in specific site mode")
                return
            logging.debug(f"Selected site filter: {site_filter}")

        # Handle monitoring mode (option 5)
        if scope_choice == "5":
            logging.info("Entering continuous monitoring mode")
            return self._continuous_monitoring_mode(site_filter)  # type: ignore[no-untyped-call]

        # Handle org-level upgrade jobs (option 6)
        if scope_choice == "6":
            logging.info("Fetching org-level upgrade jobs")
            return self._show_org_level_upgrade_jobs()  # type: ignore[no-untyped-call]

        # Continue with the existing implementation...
        return self._execute_status_check(scope_choice, site_filter)  # type: ignore[no-untyped-call]

    def _continuous_monitoring_mode(self, site_filter=None):  # type: ignore[no-untyped-def]
        """
        Continuous monitoring mode that auto-refreshes upgrade status until complete or cancelled.

        Features:
        - Auto-refresh every 7 seconds with full device scan each iteration
        - Clear screen between refreshes
        - Show only devices actively upgrading
        - Detects new devices that start upgrading after monitoring begins
        - Exit automatically when all upgrades complete
        - Press Ctrl+C to exit at any time

        Note: Each refresh queries ALL devices (not just initial set), so new upgrades
        started after monitoring begins will be detected and displayed.

        Args:
            site_filter: Optional site ID to filter monitoring
        """
        import os
        import platform

        print("\n  Continuous Monitoring Mode")
        print("=" * 70)
        print("   Monitoring active firmware upgrades...")
        print("   Press Ctrl+C to exit at any time")
        print("   Auto-refreshing every 7 seconds")
        print("   NOTE: Each refresh scans ALL devices for active upgrades")
        print("=" * 70)

        logging.info("Starting continuous monitoring mode with 7-second refresh interval")
        iteration = 0

        try:
            while True:
                iteration += 1

                # Clear screen for cleaner display (platform-specific)  # nosec B605 B607
                if platform.system() == "Windows":
                    os.system("cls")  # nosec B605 B607
                else:
                    os.system("clear")  # nosec B605 B607

                # Display header
                print("\n  Firmware Upgrade Monitoring - Live View")
                print("=" * 70)
                print(f"   Refresh #{iteration} | Press Ctrl+C to exit")
                print("   Scanning all devices for active upgrades...")
                print("=" * 70)

                # Execute status check for active upgrades only
                # NOTE: This queries ALL devices each time, not just initial set
                # New devices that start upgrading will be detected automatically
                result = self._execute_monitoring_check(site_filter)  # type: ignore[no-untyped-call]

                if result is None:
                    print("\n   Error fetching upgrade status. Retrying...")
                    logging.warning(f"Monitoring iteration {iteration} failed")
                elif result == 0:
                    # No active upgrades found
                    print("\n  All upgrades completed!")
                    print("   No active firmware upgrades detected.")
                    print("   Exiting monitoring mode.")
                    logging.info("Monitoring mode exiting - all upgrades complete")
                    break
                else:
                    print(f"\n   Found {result} device(s) actively upgrading")
                    print("   Next refresh in 7 seconds...")

                # Wait 7 seconds before next refresh
                time.sleep(7)

        except KeyboardInterrupt:
            print("\n\n  Monitoring mode cancelled by user.")
            logging.info("Continuous monitoring mode cancelled by user")
            return

    def _show_org_level_upgrade_jobs(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """
        Display org-level upgrade jobs with full configuration details including P2P settings.

        Calls:
        1. GET /api/v1/orgs/{org_id}/devices/upgrade - List all org upgrade jobs
        2. GET /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id} - Get details for each job

        Shows:
        - Upgrade ID, status, target version
        - P2P configuration (enable_p2p, p2p_cluster_size, p2p_parallelism)
        - Scheduling (start_time, reboot_at)
        - Strategy and canary phases
        - Progress metrics
        """
        print("\n  Org-Level Upgrade Jobs")
        print("=" * 70)

        try:
            import mistapi.api.v1.orgs.devices as org_devices_api

            # Step 1: List all org-level upgrade jobs
            print("  Fetching org-level upgrade jobs...")
            list_response = org_devices_api.listOrgDeviceUpgrades(self.apisession, self.org_id)

            if not list_response or not hasattr(list_response, "data"):
                print("  No org-level upgrade jobs found.")
                return

            upgrade_jobs = list_response.data if isinstance(list_response.data, list) else []

            if not upgrade_jobs:
                print("  No org-level upgrade jobs found.")
                return

            print(f"  Found {len(upgrade_jobs)} org-level upgrade job(s)\n")

            # Step 2: Get details for each upgrade job
            for job in upgrade_jobs:
                job_id = job.get("id") if isinstance(job, dict) else getattr(job, "id", None)
                if not job_id:
                    continue

                print(f"  Upgrade Job: {job_id}")
                print("-" * 70)

                try:
                    detail_response = org_devices_api.getOrgDeviceUpgrade(self.apisession, self.org_id, job_id)

                    if detail_response and hasattr(detail_response, "data"):
                        details = detail_response.data if isinstance(detail_response.data, dict) else {}

                        # Basic info
                        print(f"    Status: {details.get('status', 'Unknown')}")
                        print(f"    Target Version: {details.get('target_version', 'Unknown')}")
                        print(f"    Strategy: {details.get('strategy', 'Unknown')}")

                        # Scheduling
                        start_time = details.get("start_time")
                        if start_time:
                            from datetime import datetime as dt_module

                            try:
                                start_dt = dt_module.fromtimestamp(start_time)
                                print(f"    Start Time: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            except Exception:
                                print(f"    Start Time: {start_time} (epoch)")

                        reboot_at = details.get("reboot_at")
                        if reboot_at:
                            from datetime import datetime as dt_reboot

                            try:
                                reboot_dt = dt_reboot.fromtimestamp(reboot_at)
                                print(f"    Reboot Time: {reboot_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            except Exception:
                                print(f"    Reboot Time: {reboot_at} (epoch)")

                        # P2P Configuration
                        enable_p2p = details.get("enable_p2p", False)
                        print(f"    P2P Enabled: {enable_p2p}")
                        if enable_p2p:
                            p2p_cluster = details.get("p2p_cluster_size", "Not specified")
                            p2p_parallel = details.get("p2p_parallelism", "Not specified")
                            print(f"    P2P Cluster Size: {p2p_cluster}")
                            print(f"    P2P Parallelism: {p2p_parallel}")

                        # Canary phases
                        canary_phases = details.get("canary_phases")
                        if canary_phases:
                            print(f"    Canary Phases: {canary_phases}")

                        max_failure = details.get("max_failure_percentage")
                        if max_failure is not None:
                            print(f"    Max Failure %: {max_failure}")

                        # Progress
                        current_phase = details.get("current_phase")
                        if current_phase is not None:
                            print(f"    Current Phase: {current_phase}")

                        # Targets summary
                        targets = details.get("targets", {})
                        if targets:
                            total = targets.get("total", 0)
                            upgraded = len(targets.get("upgraded", []))
                            downloaded = len(targets.get("downloaded", []))
                            downloading = len(targets.get("download_requested", []))
                            print(
                                f"    Progress: {upgraded}/{total} upgraded, {downloaded} downloaded, {downloading} downloading"  # noqa: E501
                            )

                        # Site upgrades count
                        upgrades = details.get("upgrades", [])
                        if upgrades:
                            print(f"    Sites: {len(upgrades)} site upgrade(s)")

                except Exception as e:
                    print(f"    Error fetching details: {e}")
                    logging.error(f"Error fetching upgrade job {job_id}: {e}")

                print()

            print("=" * 70)
            print("  Org-level upgrade job details complete.")

        except Exception as e:
            print(f"  Error fetching org-level upgrades: {e}")
            logging.error(f"Error in _show_org_level_upgrade_jobs: {e}")

    def _execute_monitoring_check(self, site_filter=None):  # type: ignore[no-untyped-def]  # noqa: C901
        """
        Execute a single monitoring check iteration.

        This method performs a FULL fresh query of all devices on each call.
        It does NOT track specific devices from the first iteration - instead,
        it queries the API for ALL devices and checks their current upgrade status.

        This means:
        - New devices that start upgrading will be detected
        - Devices that complete will drop off automatically
        - Progress percentages are always current/live

        Returns:
            int: Number of devices actively upgrading, or None if error
        """
        try:
            # Fetch FRESH device statistics from API (not cached from previous iteration)
            all_device_stats = []

            if site_filter:
                # Query specific site for current device stats
                stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                    self.apisession, site_filter, type="all", limit=1000
                )
                site_stats = mistapi.get_all(response=stats_resp, mist_session=self.apisession)
                all_device_stats.extend(site_stats)
            else:
                # Query entire org for current device stats
                stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
                    self.apisession, self.org_id, type="all", fields="*", limit=1000
                )
                org_stats = mistapi.get_all(response=stats_resp, mist_session=self.apisession)
                all_device_stats.extend(org_stats)

            # Scan through ALL devices to find active upgrades
            active_upgrades = []

            for device_stat in all_device_stats:
                fwupdate = device_stat.get("fwupdate")
                if not fwupdate:
                    continue

                fw_status = fwupdate.get("status", "unknown")
                fw_progress = fwupdate.get("progress", 0)
                fw_timestamp = fwupdate.get("timestamp", 0)

                # Check if this is truly an active upgrade (not stale)
                is_active = fw_status in ("inprogress", "upgrading", "downloading")

                if is_active and fw_progress == 100 and fw_timestamp:
                    # Check for stale upgrade
                    try:
                        upgrade_age_hours = (time.time() - fw_timestamp) / 3600
                        if upgrade_age_hours > 1:
                            is_active = False  # Stale, skip it
                    except (ValueError, OSError, TypeError):
                        pass

                if is_active:
                    device_name = device_stat.get("name", "Unnamed")
                    device_type = device_stat.get("type", "unknown")
                    device_model = device_stat.get("model", "Unknown")

                    active_upgrades.append(
                        {
                            "name": device_name,
                            "type": device_type,
                            "model": device_model,
                            "progress": fw_progress if fw_progress is not None else 0,
                            "status": fw_status,
                        }
                    )

            # Display active upgrades table
            if active_upgrades:
                print("\n  Devices Currently Upgrading:")
                print("  " + "=" * 86)
                print(f"  {'Device Name':<25} {'Type':<10} {'Model':<15} {'Status':<12} {'Progress':<20}")
                print("  " + "-" * 86)

                for upgrade in active_upgrades:
                    import sys as _sys

                    _main_d = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
                    DisplayUtils = _main_d.DisplayUtils  # lazy import avoids circular
                    progress_bar = DisplayUtils.create_progress_bar(upgrade["progress"], bar_length=15)
                    print(
                        f"  {upgrade['name']:<25} {upgrade['type']:<10} {upgrade['model']:<15} "
                        f"{upgrade['status']:<12} {progress_bar}"
                    )

                print("  " + "=" * 86)

            return len(active_upgrades)

        except Exception as e:
            logging.error(f"Error in monitoring check: {e}", exc_info=True)
            return None

    def _upgrade_ap_firmware_by_gateway_template(self):  # type: ignore[no-untyped-def]
        """
        Advanced AP firmware upgrade organized by Gateway Template assignment.

        This method provides template-based firmware upgrades with:
        1. Interactive Gateway Template selection with site count display
        2. Automatic site discovery for selected template
        3. AP enumeration across all sites in template
        4. Model-based firmware version selection
        5. Unified upgrade execution across template sites
        6. Automatic site auto-upgrade configuration
        7. Comprehensive audit logging and progress monitoring

        Features:
        - Template selection by index or name
        - Site count and AP count display per template
        - Reuse of existing upgrade strategies and safety measures
        - Maintains all existing safety confirmations and audit trails
        """
        logging.info("Starting template-based AP firmware upgrade...")
        logging.debug("FirmwareManager._upgrade_ap_firmware_by_gateway_template() initiated")

        print(" Advanced AP Firmware Upgrade by Gateway Template")
        print("=" * 70)

        # Step 1: Ensure required CSVs are fresh
        print("\n  Preparing template and site data...")
        self._check_cache_fn("OrgGatewayTemplates.csv", self._gateway_templates_fn)
        self._check_cache_fn("SiteList.csv", self._sites_fn)

        # Step 2: Load gateway templates and build template-to-sites mapping
        template_name_to_id, template_sites_mapping = self._load_template_sites_mapping()  # type: ignore[no-untyped-call]

        if not template_name_to_id:
            print(" No gateway templates found.")
            logging.warning("No gateway templates available for upgrade")
            return

        # Step 3: Display template selection with site counts
        selected_template_id, selected_template_name = self._prompt_template_selection(  # type: ignore[no-untyped-call]
            template_name_to_id, template_sites_mapping
        )

        if not selected_template_id:
            print(" No template selected. Exiting.")
            logging.info("Template-based upgrade cancelled - no template selected")
            return

        # Step 4: Get sites for selected template
        sites_to_upgrade = template_sites_mapping.get(selected_template_id, [])

        if not sites_to_upgrade:
            print(f" No sites found using template '{selected_template_name}'.")
            logging.warning(f"No sites found for template {selected_template_name} (ID: {selected_template_id})")
            return

        print("\n  Template Selection Summary:")
        print(f"   Selected Template: {selected_template_name}")
        print(f"   Template ID: {selected_template_id}")
        print(f"   Sites in Template: {len(sites_to_upgrade)}")

        # Log site details
        logging.info(f"Template-based upgrade: '{selected_template_name}' with {len(sites_to_upgrade)} sites")
        for site_info in sites_to_upgrade:
            logging.debug(f"  Site: {site_info['name']} (ID: {site_info['id']})")

        # Step 5: Execute firmware upgrade using existing bulk upgrade logic
        # Convert sites_to_upgrade to the format expected by bulk_upgrade_ap_firmware_by_site
        return self._execute_template_based_upgrade(sites_to_upgrade, selected_template_name)  # type: ignore[no-untyped-call]

    def _ensure_template_csv_freshness(self):  # type: ignore[no-untyped-def]
        """
        Ensure that required template and site CSV files are fresh and available.

        This method generates or refreshes the CSV files needed for template-based
        operations if they don't exist or are stale.
        """
        logging.debug("Ensuring template CSV files are fresh")
        print("  Preparing template and site data...")

        # Generate required CSV files using existing export functions
        self._check_cache_fn("OrgGatewayTemplates.csv", self._gateway_templates_fn)
        self._check_cache_fn("SiteList.csv", self._sites_fn)

        logging.debug("Template CSV files ensured fresh")

    def _load_template_sites_mapping(self):  # type: ignore[no-untyped-def]
        """
        Load gateway templates and create mapping of templates to their assigned sites.

        Returns:
            tuple: (template_name_to_id dict, template_sites_mapping dict)
        """
        template_name_to_id: dict[str, str] = {}
        template_sites_mapping: dict[str, list[dict[str, Any]]] = {}  # template_id -> list of site info dicts

        try:
            # Load gateway templates
            gateway_templates_path = self._get_csv_path_fn("OrgGatewayTemplates.csv")
            with open(gateway_templates_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    tid = row.get("id", "").strip()
                    if name and tid:
                        template_name_to_id[name] = tid
                        template_sites_mapping[tid] = []  # Initialize empty list

            logging.info(f"Loaded {len(template_name_to_id)} gateway templates")

            # Load sites and map them to templates
            site_list_path = self._get_csv_path_fn("SiteList.csv")
            with open(site_list_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    gateway_template_id = row.get("gatewaytemplate_id", "").strip()
                    site_id = row.get("id", "").strip()
                    site_name = row.get("name", "").strip()

                    if gateway_template_id in template_sites_mapping and site_id and site_name:
                        template_sites_mapping[gateway_template_id].append({"id": site_id, "name": site_name})

            # Log template-to-site mapping statistics
            for template_id, sites in template_sites_mapping.items():
                template_name = next(
                    (name for name, tid in template_name_to_id.items() if tid == template_id), "Unknown"
                )
                logging.debug(f"Template '{template_name}': {len(sites)} sites")

            return template_name_to_id, template_sites_mapping

        except Exception as e:
            logging.error(f"Failed to load template-sites mapping: {e}")
            print(f"! Failed to load template and site data: {e}")
            return {}, {}

    def _prompt_template_selection(self, template_name_to_id, template_sites_mapping):  # type: ignore[no-untyped-def]
        """
        Present interactive template selection with site counts.

        Args:
            template_name_to_id: Dict mapping template names to IDs
            template_sites_mapping: Dict mapping template IDs to site lists

        Returns:
            tuple: (selected_template_id, selected_template_name) or (None, None)
        """
        print("\n  Available Gateway Templates:")
        print(f"  {'Index':<8} {'Template Name':<40} {'Sites':<8}")
        print(f"  {'-' * 8} {'-' * 40} {'-' * 8}")

        # Create indexed list of templates sorted by name
        sorted_templates = sorted(template_name_to_id.items())
        template_index_map = {}

        for idx, (template_name, template_id) in enumerate(sorted_templates, 1):
            site_count = len(template_sites_mapping.get(template_id, []))
            print(f"  [{idx:<7}] {template_name:<40} {site_count:<8}")
            template_index_map[str(idx)] = (template_id, template_name)

        print("\n  Selection Options:")
        print(f"   !? Enter index number (1-{len(sorted_templates)})")
        print("   !? Type exact template name")
        print("   !? Press Enter to cancel")

        while True:
            try:
                user_input = self._safe_input_fn("\n  Select template: ", context="firmware_manager").strip()

                if not user_input:
                    # Empty input - cancel
                    return None, None

                # Check if input is an index number
                if user_input in template_index_map:
                    template_id, template_name = template_index_map[user_input]
                    logging.debug(f"Template selected by index {user_input}: {template_name}")
                    return template_id, template_name

                # Check if input matches a template name exactly
                if user_input in template_name_to_id:
                    template_id = template_name_to_id[user_input]
                    logging.debug(f"Template selected by name: {user_input}")
                    return template_id, user_input

                # No match found
                print(
                    f"   Invalid selection. Please enter a valid index (1-{len(sorted_templates)}) or exact template name."  # noqa: E501
                )

            except KeyboardInterrupt:
                print("\n   Template selection cancelled.")
                return None, None

    def _execute_template_based_upgrade(self, sites_to_upgrade, template_name):  # type: ignore[no-untyped-def]
        """
        Execute firmware upgrade for all sites in a gateway template.

        This method reuses the existing bulk upgrade logic but with template context.

        Args:
            sites_to_upgrade: List of site info dicts with 'id' and 'name'
            template_name: Name of the selected template for logging

        Returns:
            Results of the upgrade operation
        """
        logging.info(
            f"Executing template-based firmware upgrade for template '{template_name}' with {len(sites_to_upgrade)} sites"  # noqa: E501
        )

        print("\n  Template-Based Upgrade Execution")
        print(f"  Template: {template_name}")
        print(f"  Sites to process: {len(sites_to_upgrade)}")
        print(f"  {'Site Name':<40} {'Site ID':<40}")
        print(f"  {'-' * 40} {'-' * 40}")

        for site_info in sites_to_upgrade:
            print(f"  {site_info['name']:<40} {site_info['id']:<40}")

        # Use the existing bulk upgrade functionality
        # We'll call the refactored bulk_upgrade method with our site list
        return self._bulk_upgrade_ap_firmware_by_site(sites_to_upgrade_override=sites_to_upgrade)  # type: ignore[no-untyped-call]

    def execute_firmware_upgrade_with_mode_selection(self):  # type: ignore[no-untyped-def]
        """
        Main entry point for firmware upgrades with mode selection.

        Presents user with choice between:
        1. Site-based upgrade (existing behavior)
        2. Template-based upgrade (new functionality)
        3. MSP Multi-Org upgrade (when MSP session active) - upgrade across multiple organizations

        Returns:
            Results of the selected upgrade operation
        """
        global msp_privileges

        logging.info("Starting firmware upgrade with mode selection...")
        logging.debug("FirmwareManager.execute_firmware_upgrade_with_mode_selection() initiated")
        emitter = PROGRESS_EMITTER
        if emitter:
            emitter.emit_progress_start("90", "firmware_upgrade", 1)

        print(" Advanced AP Firmware Upgrade")
        print("=" * 60)

        # Check if MSP mode is available
        msp_mode_available = bool(msp_privileges)

        # Step 1: Mode selection
        print("\n  Select upgrade mode:")
        print("   [1] By Site - Upgrade specific sites (CSV file, bulk list, or single site selection)")
        print("   [2] By Gateway Template - Upgrade all sites assigned to a selected Gateway Template")

        if msp_mode_available:
            print("   [3] MSP Multi-Org - Upgrade across multiple organizations (MSP session active)")
            valid_choices = ["1", "2", "3"]
            prompt = "\n  Select mode (1-3): "
        else:
            valid_choices = ["1", "2"]
            prompt = "\n  Select mode (1-2): "

        while True:
            try:
                mode_choice = self._safe_input_fn(prompt, context="firmware_manager").strip()
                if mode_choice == "1":
                    logging.info("User selected site-based upgrade mode")
                    print("\n  Site-based upgrade mode selected")
                    return self._bulk_upgrade_ap_firmware_by_site()  # type: ignore[no-untyped-call]
                elif mode_choice == "2":
                    logging.info("User selected template-based upgrade mode")
                    print("\n  Template-based upgrade mode selected")
                    return self._upgrade_ap_firmware_by_gateway_template()  # type: ignore[no-untyped-call]
                elif mode_choice == "3" and msp_mode_available:
                    logging.info("User selected MSP multi-org upgrade mode")
                    print("\n  MSP Multi-Organization upgrade mode selected")
                    return self._execute_msp_multi_org_upgrade()  # type: ignore[no-untyped-call]
                else:
                    print(f"   Invalid selection. Please choose {'/'.join(valid_choices)}.")
                    logging.debug(f"Invalid mode selection: {mode_choice}")
            except KeyboardInterrupt:
                print("\n\n  Firmware upgrade cancelled by user.")
                logging.info("Firmware upgrade cancelled during mode selection")
                return

    def _execute_msp_multi_org_upgrade(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0915
        """
        Execute firmware upgrade across multiple MSPs and organizations.

        This mode allows MSP administrators to:
        1. Select multiple MSPs (if multiple available)
        2. Select multiple organizations per MSP
        3. Select sites within each organization
        4. Execute upgrades sequentially with dry-run support

        Supports selection patterns:
        - Single index: "1"
        - Comma-separated: "1,3,5"
        - Range with dash: "1-5"
        - Range with 'through': "1 through 5"
        - All items: "all"

        Returns:
            Summary of upgrade results across all organizations
        """
        global msp_privileges, apisession, org_id

        # Check for dry_run mode
        dry_run = getattr(globals().get("args", None), "dry_run", False)

        print("")
        print("=" * 70)
        print("  MSP MULTI-ORGANIZATION FIRMWARE UPGRADE")
        print("=" * 70)

        if dry_run:
            print("")
            print("  >> DRY-RUN MODE ENABLED <<")
            print("  >> No actual upgrades will be performed - simulation only <<")

        print("")
        print("  WARNING: This will upgrade AP firmware across multiple organizations.")
        print("  Please review selections carefully before confirming.")
        print("")

        # Step 1: Select MSPs (supports multi-select)
        selected_msps = self._select_msps_for_upgrade()  # type: ignore[no-untyped-call]
        if not selected_msps:
            print("  Cancelled - no MSP selected")
            return

        print(f"\n  + Selected {len(selected_msps)} MSP(s)")

        # Step 2: For each MSP, select organizations and sites
        upgrade_plan = []  # List of {msp, org, sites} dicts

        for msp_info in selected_msps:
            msp_id = msp_info["msp_id"]
            msp_name = msp_info.get("msp_name", "Unknown MSP")

            print("")
            print("-" * 70)
            print(f"  MSP: {msp_name}")
            print("-" * 70)

            # Fetch and select organizations for this MSP
            selected_orgs = self._select_orgs_for_upgrade(msp_id, msp_name)  # type: ignore[no-untyped-call]
            if not selected_orgs:
                print(f"    Skipping MSP {msp_name} - no organizations selected")
                continue

            # For each org, select sites
            for org_info in selected_orgs:
                org_target_id = org_info["id"]
                org_name = org_info["name"]

                print(f"\n    Organization: {org_name}")

                # Fetch and select sites for this org
                selected_sites = self._select_sites_for_org_upgrade(org_target_id, org_name)  # type: ignore[no-untyped-call]
                if not selected_sites:
                    print(f"      Skipping org {org_name} - no sites selected")
                    continue

                upgrade_plan.append(
                    {
                        "msp_id": msp_id,
                        "msp_name": msp_name,
                        "org_id": org_target_id,
                        "org_name": org_name,
                        "sites": selected_sites,
                    }
                )

        if not upgrade_plan:
            print("\n  No upgrade targets configured. Operation cancelled.")
            return

        # Step 3: Display upgrade plan summary
        self._display_upgrade_plan_summary(upgrade_plan, dry_run)  # type: ignore[no-untyped-call]

        # Step 4: Confirm destructive operation (skip in dry-run)
        if not dry_run:
            print("")
            print("  " + "!" * 68)
            print("  !  DESTRUCTIVE OPERATION - FIRMWARE UPGRADE ACROSS MULTIPLE ORGS  !")
            print("  " + "!" * 68)
            print("")

            total_sites = sum(len(p["sites"]) for p in upgrade_plan)
            total_orgs = len(upgrade_plan)
            print("  You are about to upgrade AP firmware in:")
            print(f"    - {total_orgs} organization(s)")
            print(f"    - {total_sites} site(s) total")
            print("")

            try:
                confirm = self._safe_input_fn("  Type 'UPGRADE' to proceed: ", context="msp_firmware_upgrade").strip()
            except SystemExit:
                return

            if confirm != "UPGRADE":
                print("  X Upgrade cancelled - confirmation not received")
                logging.warning("MSP multi-org upgrade cancelled - user did not confirm")
                return
        else:
            print("\n  >> DRY-RUN: Skipping confirmation - proceeding with simulation <<")

        # Step 5: Execute upgrades
        results = self._execute_msp_upgrade_plan(upgrade_plan, dry_run)  # type: ignore[no-untyped-call]

        # Step 6: Print summary
        self._print_msp_upgrade_summary(results, dry_run)  # type: ignore[no-untyped-call]

        return results

    def _select_msps_for_upgrade(self):  # type: ignore[no-untyped-def]
        """
        Select MSPs for multi-org upgrade with support for multi-selection.

        Supports:
        - Single selection by index
        - Multiple selection via comma-separated indices
        - Range selection with dash or 'through' keyword
        - 'all' to select all MSPs

        Returns:
            List of selected MSP dicts or None if cancelled
        """
        global msp_privileges

        if not msp_privileges:
            return None

        if len(msp_privileges) == 1:
            print(f"  Single MSP available: {msp_privileges[0].get('msp_name', 'Unknown')}")
            return msp_privileges

        print("  Available MSPs:")
        print("")
        for idx, msp in enumerate(msp_privileges, start=1):
            msp_name = msp.get("msp_name", "Unknown")
            msp_role = msp.get("role", "unknown")
            print(f"    {idx:>3}. {msp_name} (role: {msp_role})")

        print("")
        print("  Selection options:")
        print("    - Single: '1'")
        print("    - Multiple: '1,3,5'")
        print("    - Range: '1-3' or '1 through 3'")
        print("    - All: 'all'")
        print("    - Cancel: 'q'")
        print("")

        try:
            selection = self._safe_input_fn("  Select MSP(s): ", context="msp_multi_select").strip().lower()
        except SystemExit:
            return None

        if selection == "q" or selection == "":
            return None

        if selection == "all":
            return msp_privileges

        # Parse selection using shared parser
        selected_indices = self._parse_selection_input(selection, len(msp_privileges))
        if not selected_indices:
            print("  X Invalid selection")
            return None

        return [msp_privileges[idx] for idx in selected_indices]

    def _select_orgs_for_upgrade(self, msp_id, msp_name):  # type: ignore[no-untyped-def]  # noqa: C901
        """
        Fetch orgs from MSP and let user select which to upgrade.

        Supports:
        - Single selection by index
        - Multiple selection via comma-separated indices
        - Range selection with dash or 'through' keyword
        - 'all' to select all organizations

        Returns:
            List of org dicts or None if cancelled
        """
        global apisession

        print(f"    Fetching organizations from MSP {msp_name}...")

        if apisession is None:
            print("    X API session not initialized")
            return None

        try:
            import mistapi.api.v1.msps.orgs as msp_orgs_api

            response = msp_orgs_api.listMspOrgs(apisession, msp_id)

            if not response or not hasattr(response, "data"):
                print("    X Failed to retrieve organizations")
                return None

            orgs_data = response.data
            if not isinstance(orgs_data, list):
                orgs_data = [orgs_data] if orgs_data else []

            if not orgs_data:
                print("    X No organizations found under this MSP")
                return None

            # Sort by name
            orgs_data = sorted(orgs_data, key=lambda x: x.get("name", "").lower())

            print(f"    Found {len(orgs_data)} organization(s):")
            print("")

            # Show all orgs with numbers
            for idx, org in enumerate(orgs_data, start=1):
                org_name = org.get("name", "Unknown")
                org_id_preview = org.get("id", "N/A")[:8]
                print(f"      {idx:>3}. {org_name} ({org_id_preview}...)")

            print("")
            print("    Selection: single '1', multiple '1,3,5', range '1-3', 'all', or 'q'")
            print("")

            try:
                selection = (
                    self._safe_input_fn("    Select organization(s): ", context="org_multi_select").strip().lower()
                )
            except SystemExit:
                return None

            if selection == "q" or selection == "":
                return None

            if selection == "all":
                return orgs_data

            # Parse selection
            selected_indices = self._parse_selection_input(selection, len(orgs_data))
            if not selected_indices:
                print("    X Invalid selection")
                return None

            return [orgs_data[idx] for idx in selected_indices]

        except Exception as e:
            print(f"    X Error fetching organizations: {e}")
            logging.error(f"Failed to fetch MSP orgs for upgrade: {e}")
            return None

    def _select_sites_for_org_upgrade(self, target_org_id, org_name):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """
        Fetch sites from org and let user select which to upgrade.

        Supports:
        - Single selection by index
        - Multiple selection via comma-separated indices
        - Range selection with dash or 'through' keyword
        - 'all' to select all sites

        Returns:
            List of site dicts or None if cancelled
        """
        global apisession

        print(f"      Fetching sites from {org_name}...")

        if apisession is None:
            print("      X API session not initialized")
            return None

        try:
            import mistapi.api.v1.orgs.sites as org_sites_api

            response = org_sites_api.listOrgSites(apisession, target_org_id)

            if not response or not hasattr(response, "data"):
                print("      X Failed to retrieve sites")
                return None

            sites_data = response.data
            if not isinstance(sites_data, list):
                sites_data = [sites_data] if sites_data else []

            if not sites_data:
                print("      X No sites found in this organization")
                return None

            # Sort by name
            sites_data = sorted(sites_data, key=lambda x: x.get("name", "").lower())

            print(f"      Found {len(sites_data)} site(s):")
            print("")

            # Show all sites with numbers (paginate if many)
            page_size = 25
            total_pages = (len(sites_data) + page_size - 1) // page_size
            current_page = 0

            while True:
                start_idx = current_page * page_size
                end_idx = min(start_idx + page_size, len(sites_data))

                for idx in range(start_idx, end_idx):
                    site = sites_data[idx]
                    site_name = site.get("name", "Unknown")
                    print(f"        {idx + 1:>4}. {site_name}")

                if total_pages > 1:
                    print(f"\n      Page {current_page + 1}/{total_pages}")
                    print("      [n]ext page, [p]rev page, or enter selection:")

                print("")
                print("      Selection: single '1', multiple '1,3,5', range '1-10', 'all', or 'q'")
                print("")

                try:
                    selection = (
                        self._safe_input_fn("      Select site(s): ", context="site_multi_select").strip().lower()
                    )
                except SystemExit:
                    return None

                if selection == "q" or selection == "":
                    return None

                if selection == "n" and current_page < total_pages - 1:
                    current_page += 1
                    continue
                elif selection == "p" and current_page > 0:
                    current_page -= 1
                    continue
                elif selection == "all":
                    return sites_data
                else:
                    # Parse selection
                    selected_indices = self._parse_selection_input(selection, len(sites_data))
                    if selected_indices:
                        return [sites_data[idx] for idx in selected_indices]
                    print("      X Invalid selection - try again")

        except Exception as e:
            print(f"      X Error fetching sites: {e}")
            logging.error(f"Failed to fetch org sites for upgrade: {e}")
            return None

    def _parse_selection_input(self, user_input: str, max_count: int) -> list:  # type: ignore[type-arg]  # noqa: C901
        """
        Parse user selection input into list of 0-based indices.

        Supports:
        - Single index: "1" -> [0]
        - Comma-separated: "1,3,5" -> [0, 2, 4]
        - Dash range: "1-5" -> [0, 1, 2, 3, 4]
        - 'through' range: "1 through 5" -> [0, 1, 2, 3, 4]
        - Mixed: "1-3, 5, 7 through 10" -> [0, 1, 2, 4, 6, 7, 8, 9]

        Note: User input is 1-based, output is 0-based indices

        Args:
            user_input: User's selection string
            max_count: Maximum number of items (for validation)

        Returns:
            List of valid 0-based indices, or empty list if invalid
        """
        selected_indices = []

        # Normalize 'through' to '-' for consistent parsing
        normalized_input = user_input.lower().replace(" through ", "-").replace("through", "-")

        parts = [part.strip() for part in normalized_input.split(",")]

        for part in parts:
            if "-" in part and not part.startswith("-"):
                # Handle range like "1-5" (1-based user input)
                try:
                    range_parts = part.split("-")
                    if len(range_parts) == 2:
                        start = int(range_parts[0].strip()) - 1  # Convert to 0-based
                        end = int(range_parts[1].strip()) - 1  # Convert to 0-based
                        if start > end:
                            start, end = end, start  # Swap if reversed
                        for idx in range(start, end + 1):
                            if 0 <= idx < max_count and idx not in selected_indices:
                                selected_indices.append(idx)
                            elif idx >= max_count:
                                print(f"      !? Index {idx + 1} out of range (max: {max_count})")
                except ValueError:
                    logging.warning(f"Invalid range format: {part}")
                    continue
            else:
                # Handle single index (1-based user input)
                try:
                    idx = int(part) - 1  # Convert to 0-based
                    if 0 <= idx < max_count and idx not in selected_indices:
                        selected_indices.append(idx)
                    elif idx >= max_count:
                        print(f"      !? Index {idx + 1} out of range (max: {max_count})")
                except ValueError:
                    logging.warning(f"Invalid index: {part}")
                    continue

        # Sort indices for consistent ordering
        selected_indices.sort()
        return selected_indices

    def _display_upgrade_plan_summary(self, upgrade_plan, dry_run):  # type: ignore[no-untyped-def]
        """Display a summary of the planned upgrades."""
        print("")
        print("=" * 70)
        print("  UPGRADE PLAN SUMMARY" + (" (DRY-RUN)" if dry_run else ""))
        print("=" * 70)
        print("")

        total_sites = 0
        msps_seen = set()

        for plan in upgrade_plan:
            msp_name = plan["msp_name"]
            org_name = plan["org_name"]
            sites = plan["sites"]
            total_sites += len(sites)
            msps_seen.add(plan["msp_id"])

            print(f"  MSP: {msp_name}")
            print(f"    Organization: {org_name}")
            print(f"    Sites ({len(sites)}):")
            for site in sites[:5]:  # Show first 5
                print(f"      - {site.get('name', 'Unknown')}")
            if len(sites) > 5:
                print(f"      ... and {len(sites) - 5} more")
            print("")

        print("-" * 70)
        print("  TOTALS:")
        print(f"    MSPs: {len(msps_seen)}")
        print(f"    Organizations: {len(upgrade_plan)}")
        print(f"    Sites: {total_sites}")
        print("-" * 70)

    def _execute_msp_upgrade_plan(self, upgrade_plan, dry_run):  # type: ignore[no-untyped-def]
        """Execute the upgrade plan across all orgs and sites."""
        global apisession, org_id

        results = []
        original_org_id = org_id
        total_items = len(upgrade_plan)

        for idx, plan in enumerate(upgrade_plan, 1):
            target_org_id = plan["org_id"]
            target_org_name = plan["org_name"]
            msp_name = plan["msp_name"]
            sites = plan["sites"]

            print("")
            print(f"  [{idx}/{total_items}] Processing: {target_org_name} (MSP: {msp_name})")
            print(f"      Organization ID: {target_org_id}")
            print(f"      Sites to upgrade: {len(sites)}")
            print("-" * 70)

            try:
                # Set the global org_id for helper functions
                org_id = target_org_id

                # Create a BulkAPFirmwareUpgrader with pre-selected sites
                sites_for_upgrader = [{"id": s["id"], "name": s.get("name", "Unknown")} for s in sites]
                import sys as _sys

                _main_msp = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
                _BulkAPUpgrader = _main_msp.BulkAPFirmwareUpgrader  # lazy import avoids circular
                upgrader = _BulkAPUpgrader(target_org_id, sites_for_upgrader, dry_run=dry_run)
                upgrader.execute()

                results.append(
                    {
                        "msp_name": msp_name,
                        "org_id": target_org_id,
                        "org_name": target_org_name,
                        "sites_count": len(sites),
                        "status": "completed",
                        "result": None,
                        "dry_run": dry_run,
                    }
                )

                logging.info(f"MSP upgrade {'simulated' if dry_run else 'completed'} for org: {target_org_name}")

            except KeyboardInterrupt:
                print(f"\n  Upgrade interrupted at organization: {target_org_name}")
                results.append(
                    {
                        "msp_name": msp_name,
                        "org_id": target_org_id,
                        "org_name": target_org_name,
                        "sites_count": len(sites),
                        "status": "interrupted",
                        "result": None,
                        "dry_run": dry_run,
                    }
                )

                try:
                    cont = (
                        self._safe_input_fn("  Continue with remaining orgs? (y/N): ", context="msp_continue")
                        .strip()
                        .lower()
                    )
                except SystemExit:
                    break

                if cont != "y":
                    print("  Stopping MSP upgrade process")
                    break

            except Exception as e:
                error_msg = str(e)
                print(f"  X Error upgrading {target_org_name}: {error_msg}")
                logging.error(f"MSP upgrade failed for org {target_org_name}: {e}")

                results.append(
                    {
                        "msp_name": msp_name,
                        "org_id": target_org_id,
                        "org_name": target_org_name,
                        "sites_count": len(sites),
                        "status": "failed",
                        "error": error_msg,
                        "dry_run": dry_run,
                    }
                )

        # Restore original org_id
        org_id = original_org_id

        return results

    def _print_msp_upgrade_summary(self, results, dry_run=False):  # type: ignore[no-untyped-def]
        """Print summary of MSP multi-org upgrade results."""
        print("")
        print("=" * 70)
        print("  MSP UPGRADE SUMMARY" + (" (DRY-RUN)" if dry_run else ""))
        print("=" * 70)
        print("")

        completed = [r for r in results if r["status"] == "completed"]
        failed = [r for r in results if r["status"] == "failed"]
        interrupted = [r for r in results if r["status"] == "interrupted"]

        total_sites = sum(r.get("sites_count", 0) for r in results)

        print(f"  Total organizations processed: {len(results)}")
        print(f"  Total sites targeted: {total_sites}")
        print(f"    + Completed: {len(completed)}")
        print(f"    X Failed: {len(failed)}")
        print(f"    ! Interrupted: {len(interrupted)}")
        print("")

        if completed:
            print("  Completed organizations:")
            for r in completed:
                status_prefix = "(DRY-RUN) " if r.get("dry_run") else ""
                print(f"    + {status_prefix}{r['org_name']} ({r.get('sites_count', 0)} sites)")

        if failed:
            print("\n  Failed organizations:")
            for r in failed:
                print(f"    X {r['org_name']}: {r.get('error', 'Unknown error')}")

        if interrupted:
            print("\n  Interrupted organizations:")
            for r in interrupted:
                print(f"    ! {r['org_name']}")

        print("")
        mode_str = "DRY-RUN " if dry_run else ""
        logging.info(
            f"MSP {mode_str}upgrade summary: {len(completed)} completed, {len(failed)} failed, {len(interrupted)} interrupted"  # noqa: E501
        )

    def _select_msp_for_upgrade(self):  # type: ignore[no-untyped-def]
        """DEPRECATED: Use _select_msps_for_upgrade() instead. Kept for compatibility."""
        msps = self._select_msps_for_upgrade()  # type: ignore[no-untyped-call]
        return msps[0] if msps and len(msps) == 1 else None

    def _bulk_upgrade_ap_firmware_by_site(self, sites_to_upgrade_override=None):  # type: ignore[no-untyped-def]
        """
        Advanced bulk upgrade AP firmware for APs at selected site(s).

        This method provides comprehensive firmware upgrade capabilities with:
        1. Bulk site mode: Reads APUpgradeSiteList.CSV for multi-site upgrades
        2. Single site mode: Interactive site selection (fallback if CSV not found)
        3. Template mode: Uses provided sites_to_upgrade_override for template-based upgrades
        4. Automatic site name-to-ID resolution via organization lookup
        5. Firmware version selection per model across all sites
        6. Advanced upgrade strategies (big_bang, canary, rrm, serial) - default: RRM
        7. P2P firmware sharing options (default: enabled)
        8. Scheduling and failure threshold controls
        9. Device filtering and selection rules
        10. Progress monitoring and rollback options
        11. Comprehensive safety measures and audit logging
        12. Per-site upgrade execution with unified reporting

        Args:
            sites_to_upgrade_override: Optional list of site dicts for template-based upgrades
                                     Format: [{'id': site_id, 'name': site_name}, ...]

        File Format for APUpgradeSiteList.CSV (headerless, one site name per line):
        Main Office
        Branch Office A
        Remote Site B

        Note: Site names must exactly match those in the Mist organization.
        """
        # Set up global session context for compatibility with existing helper functions
        global apisession
        original_apisession = apisession
        apisession = self.apisession

        try:
            return self._execute_bulk_upgrade(sites_to_upgrade_override)  # type: ignore[no-untyped-call]
        finally:
            apisession = original_apisession

    def _execute_bulk_upgrade(self, sites_to_upgrade_override):  # type: ignore[no-untyped-def]
        """Execute the bulk firmware upgrade using BulkAPFirmwareUpgrader class."""
        import sys as _sys

        _main = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
        BulkAPFirmwareUpgrader = _main.BulkAPFirmwareUpgrader  # lazy import avoids circular
        # Check for dry_run flag from global args
        dry_run = getattr(getattr(_main, "args", None), "dry_run", False)
        upgrader = BulkAPFirmwareUpgrader(self.org_id, sites_to_upgrade_override, dry_run=dry_run)
        upgrader.execute()

    def _execute_status_check(self, scope_choice, site_filter):  # type: ignore[no-untyped-def]
        """Execute the firmware status check using FirmwareUpgradeStatusChecker."""
        import sys as _sys

        _main = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
        FirmwareUpgradeStatusChecker = _main.FirmwareUpgradeStatusChecker  # lazy import avoids circular
        # Set up the implementation to use this class's session and org_id
        global apisession
        original_apisession = apisession
        apisession = self.apisession

        try:
            FirmwareUpgradeStatusChecker(scope_choice, site_filter).check()
        finally:
            apisession = original_apisession

    # ===============================================================================
    # SWITCH FIRMWARE UPGRADE METHODS
    # ===============================================================================

    def execute_switch_firmware_upgrade_with_mode_selection(self):  # type: ignore[no-untyped-def]
        """
        Main entry point for switch firmware upgrades with mode selection.

        Presents user with choice between:
        1. Site-based upgrade (individual site selection)
        2. Template-based upgrade (Gateway Template assignment - same grouping as APs)

        Returns:
            Results of the selected upgrade operation
        """
        logging.info("Starting switch firmware upgrade with mode selection...")
        logging.debug("FirmwareManager.execute_switch_firmware_upgrade_with_mode_selection() initiated")

        print(" Advanced Switch Firmware Upgrade")
        print("=" * 60)
        print("")
        print("  DESTRUCTIVE OPERATION WARNING")
        print("  ===========================")
        print("  Switch firmware upgrades will:")
        print("  X  Reboot switches during upgrade process")
        print("  X  Potentially disrupt network connectivity")
        print("  X  Affect production traffic flow")
        print("  X  Require recovery snapshots for Junos devices")
        print("")

        # Step 1: Mode selection
        print("  Select upgrade mode:")
        print("   [1] By Site - Upgrade specific sites (individual site selection)")
        print("   [2] By Gateway Template - Upgrade all sites assigned to a selected Gateway Template")

        while True:
            try:
                mode_choice = self._safe_input_fn("\n  Select mode (1-2): ", context="firmware_manager").strip()
                if mode_choice == "1":
                    logging.info("User selected site-based switch upgrade mode")
                    print("\n  Site-based switch upgrade mode selected")
                    return self._bulk_upgrade_switch_firmware_by_site()  # type: ignore[no-untyped-call]
                elif mode_choice == "2":
                    logging.info("User selected template-based switch upgrade mode")
                    print("\n  Template-based switch upgrade mode selected")
                    return self._upgrade_switch_firmware_by_gateway_template()  # type: ignore[no-untyped-call]
                else:
                    print("  Invalid selection. Please choose 1 or 2.")
                    logging.debug(f"Invalid mode selection: {mode_choice}")
            except (EOFError, KeyboardInterrupt):
                print("\n  Operation cancelled by user.")
                logging.info("Switch firmware upgrade cancelled (EOF or interrupt) - SSH/container safe exit")
                return

    def _bulk_upgrade_switch_firmware_by_site(self, sites_to_upgrade_override=None):  # type: ignore[no-untyped-def]
        """
        Advanced bulk switch firmware upgrade for switches at selected site(s).

        This method provides comprehensive switch firmware upgrade capabilities with:
        1. Bulk site mode: Interactive site selection for multi-site upgrades
        2. Single site mode: Individual site selection (fallback if override not provided)
        3. Template mode: Uses provided sites_to_upgrade_override for template-based upgrades
        4. Switch-specific upgrade parameters (reboot=True, snapshot=True for Junos)
        5. Conservative upgrade strategies optimized for network switches
        6. Enhanced safety measures for network disruption prevention
        7. Model-specific firmware version selection across sites
        8. Per-site upgrade execution with unified reporting

        Args:
            sites_to_upgrade_override: Optional list of site dictionaries for template-based upgrades

        Returns:
            Upgrade execution results and tracking information
        """
        logging.info("Starting bulk switch firmware upgrade by site...")
        logging.debug("FirmwareManager._bulk_upgrade_switch_firmware_by_site() initiated")

        import sys as _sys

        _main = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
        BulkSwitchFirmwareUpgrader = _main.BulkSwitchFirmwareUpgrader  # lazy import avoids circular
        BulkSwitchFirmwareUpgrader(self.org_id, sites_to_upgrade_override).execute()

    def _upgrade_switch_firmware_by_gateway_template(self):  # type: ignore[no-untyped-def]
        """
        Advanced switch firmware upgrade organized by Gateway Template assignment.

        This method provides template-based switch firmware upgrades with:
        1. Interactive Gateway Template selection with site count display
        2. Automatic site discovery for selected template (same logic as AP system)
        3. Switch enumeration across all sites in template
        4. Model-based firmware version selection optimized for switches
        5. Unified upgrade execution across template sites
        6. Switch-specific safety measures and network disruption warnings
        7. Comprehensive audit logging and progress monitoring

        Features:
        - Template selection by index or name (reuses AP template infrastructure)
        - Site count and switch count display per template
        - Switch-specific upgrade parameters (reboot, snapshot, conservative strategy)
        - Maintains all existing safety confirmations and audit trails
        - Enhanced network disruption warnings for production environments
        """
        logging.info("Starting template-based switch firmware upgrade...")
        logging.debug("FirmwareManager._upgrade_switch_firmware_by_gateway_template() initiated")

        print(" Advanced Switch Firmware Upgrade by Gateway Template")
        print("=" * 70)

        # Step 1: Ensure required CSVs are fresh (reuse AP template infrastructure)
        self._ensure_template_csv_freshness()  # type: ignore[no-untyped-call]

        # Step 2: Load template-to-sites mapping (same as AP system)
        template_name_to_id, template_sites_mapping = self._load_template_sites_mapping()  # type: ignore[no-untyped-call]

        if not template_sites_mapping:
            print("\n! No Gateway Templates with assigned sites found.")
            print("  Make sure sites are assigned to Gateway Templates and try again.")
            logging.warning("No Gateway Templates with site assignments found")
            return

        # Step 3: Template selection (reuse AP template selection logic)
        selected_template_id, selected_template_name = self._prompt_template_selection(  # type: ignore[no-untyped-call]
            template_name_to_id, template_sites_mapping
        )

        if not selected_template_id:
            print(" No template selected. Exiting.")
            return

        # Step 4: Get sites for selected template
        sites_to_upgrade = template_sites_mapping.get(selected_template_id, [])

        print(f"\n  Template '{selected_template_name}' includes {len(sites_to_upgrade)} sites")
        logging.info(f"Template {selected_template_name} has {len(sites_to_upgrade)} assigned sites")

        return self._execute_template_based_switch_upgrade(sites_to_upgrade, selected_template_name)  # type: ignore[no-untyped-call]

    def _execute_template_based_switch_upgrade(self, sites_to_upgrade, selected_template_name):  # type: ignore[no-untyped-def]
        """Execute the template-based switch upgrade with the existing switch implementation."""
        print(f"  Proceeding with switch firmware upgrade for template: {selected_template_name}")
        print(f"  Target sites: {len(sites_to_upgrade)}")

        # Use the switch-specific bulk upgrade implementation
        return self._bulk_upgrade_switch_firmware_by_site(sites_to_upgrade)  # type: ignore[no-untyped-call]

    # ===============================================================================
    # SSR FIRMWARE UPGRADE METHODS
    # ===============================================================================

    def execute_ssr_firmware_upgrade_with_mode_selection(self):  # type: ignore[no-untyped-def]
        """
        Main entry point for SSR firmware upgrades with mode selection.

        Presents user with choice between:
        1. Site-based upgrade (individual site selection)
        2. Template-based upgrade (Gateway Template assignment - same grouping as APs/switches)

        SECURITY: This is a DESTRUCTIVE operation that will reboot SSR devices and
        disrupt WAN/SD-WAN connectivity. Critical routing infrastructure warnings provided.

        Returns:
            Results of the selected upgrade operation
        """
        logging.warning("Menu #100 DESTRUCTIVE: SSR firmware upgrade with mode selection started")
        logging.debug("FirmwareManager.execute_ssr_firmware_upgrade_with_mode_selection() initiated")

        print(" Advanced SSR Firmware Upgrade")
        print("=" * 60)
        print("")
        print("  CRITICAL ROUTING INFRASTRUCTURE WARNING")
        print("  ======================================")
        print("  SSR firmware upgrades will:")
        print("  X  Reboot Session Smart Routers")
        print("  X  Disrupt WAN and SD-WAN connectivity")
        print("  X  Affect branch office connectivity")
        print("  X  Impact tunnel establishment and failover")
        print("  X  Require careful HA pair coordination")
        print("  X  Potentially cause extended outages")
        print("")
        print("  RECOMMENDED PRECAUTIONS:")
        print("  X  Schedule maintenance windows")
        print("  X  Verify backup connectivity paths")
        print("  X  Coordinate with network operations")
        print("  X  Monitor upgrade progress closely")
        print("")

        # Step 1: Mode selection
        print("  Select upgrade mode:")
        print("   [1] By Site - Upgrade specific sites (individual site selection)")
        print("   [2] By Gateway Template - Upgrade all sites assigned to a selected Gateway Template")

        while True:
            try:
                mode_choice = self._safe_input_fn("\n  Select mode (1-2): ", context="firmware_manager").strip()
                if mode_choice == "1":
                    logging.info("User selected site-based SSR upgrade mode")
                    print("\n  Site-based SSR upgrade mode selected")
                    return self._bulk_upgrade_ssr_firmware_by_site()  # type: ignore[no-untyped-call]
                elif mode_choice == "2":
                    logging.info("User selected template-based SSR upgrade mode")
                    print("\n  Template-based SSR upgrade mode selected")
                    return self._upgrade_ssr_firmware_by_gateway_template()  # type: ignore[no-untyped-call]
                else:
                    print("  Invalid selection. Please choose 1 or 2.")
                    logging.debug(f"Invalid mode selection: {mode_choice}")
            except (EOFError, KeyboardInterrupt):
                print("\n  Operation cancelled by user.")
                logging.info("SSR firmware upgrade cancelled (EOF or interrupt) - SSH/container safe exit")
                return

    def _bulk_upgrade_ssr_firmware_by_site(self, sites_to_upgrade_override=None):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """
        DESTRUCTIVE: Execute firmware upgrades on Session Smart Routers across selected sites.

        This function performs bulk firmware upgrades on SSR routing infrastructure with comprehensive
        safety checks and detailed progress tracking. Supports multiple upgrade strategies
        including big bang, canary testing, and rolling upgrade modes optimized for routing infrastructure.

        SECURITY: This operation will reboot Session Smart Routers and WILL cause WAN connectivity disruption.
        All SSRs in target sites will be affected. This impacts SD-WAN tunnels, branch office connectivity,
        and critical routing infrastructure. Use with extreme caution in production.

        Args:
            sites_to_upgrade_override: Optional list of site dictionaries for template-based upgrades

        Returns:
            dict: Comprehensive upgrade operation results with success/failure tracking

        Raises:
            Exception: On critical API failures or validation errors

        CRITICAL INFRASTRUCTURE WARNING:
        - SSR reboots will disrupt WAN and SD-WAN connectivity
        - Branch offices may lose connectivity during upgrades
        - SD-WAN tunnels will be re-established after reboot
        - HA pairs require coordinated failover procedures
        - Plan extended maintenance windows for production environments
        - Verify backup connectivity paths before execution
        - Monitor upgrade progress closely for rapid intervention
        """
        # Set up logging for this method
        logger = logging.getLogger(__name__)
        logger.debug(f"Starting bulk SSR firmware upgrade - org_id: {self.org_id}")

        # Get organization information
        print("\n-> Validating organization access...")
        try:
            org_info = mistapi.api.v1.orgs.orgs.getOrg(self.apisession, self.org_id)
            if org_info.status_code != 200:
                print(f"X  Error accessing organization: {org_info.status_code}")
                logger.error(f"Failed to access organization {self.org_id}: {org_info.status_code}")
                return {"error": "Organization access failed"}

            org_name = org_info.data.get("name", "Unknown")
            print(f"!? Organization: {org_name}")
            logger.debug(f"Organization validated: {org_name}")

        except Exception as e:
            print(f"X  Error validating organization: {str(e)}")
            logger.error(f"Organization validation failed: {str(e)}")
            return {"error": f"Organization validation error: {str(e)}"}

        # Site selection logic
        if sites_to_upgrade_override:
            selected_sites = sites_to_upgrade_override
            print(f"-> Using provided site list: {len(selected_sites)} sites")
        else:
            # Get available sites
            print("\n-> Discovering available sites...")
            try:
                sites_response = mistapi.api.v1.orgs.sites.listOrgSites(self.apisession, self.org_id)
                if sites_response.status_code != 200:
                    print(f"X  Error retrieving sites: {sites_response.status_code}")
                    return {"error": "Failed to retrieve sites"}

                all_sites = sites_response.data
                print(f"!? Found {len(all_sites)} total sites")

                # Present site selection to user
                print("\nAvailable sites:")
                for index, site in enumerate(all_sites, 1):
                    print(f"{index:3}. {site.get('name', 'Unnamed')} (ID: {site.get('id', 'Unknown')})")

                print("\nSite selection options:")
                print("A. All sites")
                print("S. Select specific sites")
                print("C. Cancel operation")

                site_choice = (
                    self._safe_input_fn("\nEnter your choice (A/S/C): ", context="firmware_manager").strip().upper()
                )

                if site_choice == "C":
                    print("-> Operation cancelled by user")
                    return {"cancelled": True}
                elif site_choice == "A":
                    selected_sites = all_sites
                    print(f"-> Selected all {len(selected_sites)} sites")
                elif site_choice == "S":
                    selected_sites: list[dict[str, Any]] = []  # type: ignore[no-redef]
                    print("\nEnter site numbers (comma-separated) or ranges (e.g., 1-5):")
                    site_input = self._safe_input_fn("Sites: ", context="firmware_manager").strip()

                    # Parse site selection
                    try:
                        for part in site_input.split(","):
                            part = part.strip()
                            if "-" in part:
                                start, end = map(int, part.split("-"))
                                for device_index in range(start - 1, end):
                                    if 0 <= device_index < len(all_sites):
                                        selected_sites.append(all_sites[device_index])
                            else:
                                index = int(part) - 1
                                if 0 <= index < len(all_sites):
                                    selected_sites.append(all_sites[index])

                        print(f"-> Selected {len(selected_sites)} sites")

                    except Exception as e:
                        print(f"X  Invalid site selection: {str(e)}")
                        return {"error": "Invalid site selection"}
                else:
                    print("X  Invalid selection")
                    return {"error": "Invalid selection"}

            except Exception as e:
                print(f"X  Error during site discovery: {str(e)}")
                logger.error(f"Site discovery failed: {str(e)}")
                return {"error": f"Site discovery error: {str(e)}"}

        if not selected_sites:
            print("X  No sites selected")
            return {"error": "No sites selected"}

        # SSR firmware upgrade parameter selection
        print(f"\n{'=' * 60}")
        print("SSR FIRMWARE UPGRADE PARAMETER CONFIGURATION")
        print(f"{'=' * 60}")

        # Strategy selection (conservative defaults for SSR routing infrastructure)
        print("\nUpgrade Strategy Options (optimized for routing infrastructure):")
        print("1. serial      - Upgrade SSRs one by one (safest for routing infrastructure)")
        print("2. big_bang    - Upgrade all SSRs simultaneously (higher risk)")

        while True:
            strategy_choice = self._safe_input_fn(
                "\nSelect upgrade strategy (1-2, recommend 1): ", context="firmware_manager"
            ).strip()
            if strategy_choice == "1":
                upgrade_strategy = "serial"
                break
            elif strategy_choice == "2":
                upgrade_strategy = "big_bang"
                print("!? WARNING: big_bang strategy will upgrade all SSRs simultaneously")
                print("   This may cause widespread WAN connectivity disruption")
                break
            else:
                print("X  Please enter 1 or 2")

        print(f"-> Selected strategy: {upgrade_strategy}")

        # Reboot timing selection (SSR-specific parameter)
        print("\nReboot Timing Options:")
        print("1. Automatic - Reboot immediately after firmware download (recommended)")
        print("2. Manual    - Download firmware only, manual reboot required later")

        while True:
            reboot_choice = self._safe_input_fn("\nReboot timing? (1-2): ", context="firmware_manager").strip()
            if reboot_choice == "1":
                auto_reboot = True
                break
            elif reboot_choice == "2":
                auto_reboot = False
                print("!? WARNING: SSRs require manual reboot to activate new firmware")
                print("   New firmware will not be operational until manual reboot")
                break
            else:
                print("X  Please enter 1 or 2")

        print(f"-> Auto reboot: {'Yes' if auto_reboot else 'No'}")

        # Channel selection for firmware versions
        print("\nFirmware Channel Options:")
        print("1. stable - Production-ready releases (recommended)")
        print("2. beta   - Pre-release versions for testing")
        print("3. alpha  - Development versions (not recommended for production)")

        while True:
            channel_choice = self._safe_input_fn(
                "\nSelect firmware channel (1-3): ", context="firmware_manager"
            ).strip()
            if channel_choice == "1":
                firmware_channel = "stable"
                break
            elif channel_choice == "2":
                firmware_channel = "beta"
                break
            elif channel_choice == "3":
                firmware_channel = "alpha"
                print("!? WARNING: alpha channel contains development versions")
                print("   Not recommended for production environments")
                break
            else:
                print("X  Please enter 1, 2, or 3")

        print(f"-> Firmware channel: {firmware_channel}")

        # SSR-specific firmware version selection
        print(f"\n{'=' * 60}")
        print("SSR FIRMWARE VERSION SELECTION")
        print(f"{'=' * 60}")

        # Get available firmware versions for SSRs (Session Smart Routers)
        print("\n-> Discovering available SSR firmware versions...")
        try:
            # Use the SSR-specific API to get available firmware versions
            versions_response = mistapi.api.v1.orgs.ssr.listOrgAvailableSsrVersions(
                self.apisession, self.org_id, channel=firmware_channel
            )

            if versions_response.status_code != 200:
                print(f"X  Error retrieving SSR firmware versions: {versions_response.status_code}")
                logger.error(f"Failed to retrieve SSR versions: {versions_response.status_code}")
                return {"error": "Failed to retrieve SSR firmware versions"}

            available_versions: list[dict[str, Any]] = []
            if hasattr(versions_response, "data") and versions_response.data:
                for version_obj in versions_response.data:
                    if isinstance(version_obj, dict):
                        version = version_obj.get("version")
                        package = version_obj.get("package", "SSR")
                        is_default = version_obj.get("default", False)
                        if version:
                            available_versions.append({"version": version, "package": package, "default": is_default})
                    elif isinstance(version_obj, str):
                        # Handle case where API returns just version strings
                        available_versions.append({"version": version_obj, "package": "SSR", "default": False})

            if not available_versions:
                print(f"X  No SSR firmware versions available for {firmware_channel} channel")
                print("   Please check with Juniper support for available SSR firmware versions")
                print("   Or try a different firmware channel (stable/beta/alpha)")
                return {"error": f"No SSR firmware versions available for {firmware_channel} channel"}

            print(f"!? Found {len(available_versions)} available SSR firmware versions")
            print(f"  Channel: {firmware_channel}")

            # Get SSR inventory to show current firmware versions
            print("\n-> Checking current SSR devices...")
            ssrs_response = mistapi.api.v1.orgs.inventory.getOrgInventory(self.apisession, self.org_id, type="gateway")

            current_firmware_versions = set()
            ssr_models_found = set()
            ssr_count = 0

            if ssrs_response.status_code == 200:
                # Filter for Session Smart Router models specifically
                all_gateways = ssrs_response.data
                for gateway in all_gateways:
                    gateway_model = gateway.get("model", "")
                    gateway_type = gateway.get("type", "")

                    # Check if this is an SSR by model or type
                    if gateway_type == "ssr" or "SSR" in gateway_model or "128T" in gateway_model:
                        ssr_count += 1
                        if gateway.get("version"):
                            current_firmware_versions.add(gateway.get("version"))
                        if gateway.get("model"):
                            ssr_models_found.add(gateway.get("model"))

            if ssr_count > 0:
                print(f"!? Found {ssr_count} SSR device(s) in organization")
                if ssr_models_found:
                    print(f"  Models: {', '.join(sorted(ssr_models_found))}")
                if current_firmware_versions:
                    print(f"  Current versions: {', '.join(sorted(current_firmware_versions))}")

            # Present firmware version options
            print(f"\n{'=' * 50}")
            print("AVAILABLE SSR FIRMWARE VERSIONS")
            print(f"{'=' * 50}")

            for i, version_info in enumerate(available_versions, 1):
                version = version_info["version"]
                package = version_info["package"]
                is_default = version_info["default"]

                default_marker = " (default)" if is_default else ""
                print(f"{i:2d}. {version} [{package}]{default_marker}")

            # Allow user to select firmware version
            while True:
                try:
                    choice = self._safe_input_fn(
                        f"\nSelect firmware version (1-{len(available_versions)}): ",
                        context="firmware_manager",
                    ).strip()
                    if not choice:
                        print("X  Please enter a selection")
                        continue

                    version_index = int(choice) - 1
                    if 0 <= version_index < len(available_versions):
                        selected_version = available_versions[version_index]
                        target_version = selected_version["version"]
                        break
                    else:
                        print(f"X  Please enter a number between 1 and {len(available_versions)}")
                except ValueError:
                    print("X  Please enter a valid number")

            print(f"-> Selected firmware version: {target_version}")

        except Exception as e:
            print(f"X  Error during SSR firmware discovery: {str(e)}")
            logger.error(f"SSR firmware discovery failed: {str(e)}")
            return {"error": f"SSR firmware discovery error: {str(e)}"}

        # Configuration summary and confirmation
        print(f"\n{'=' * 60}")
        print("SSR UPGRADE CONFIGURATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Organization: {org_name}")
        print(f"Sites to upgrade: {len(selected_sites)}")
        print(f"Target firmware: {target_version}")
        print(f"Firmware channel: {firmware_channel}")
        print(f"Upgrade strategy: {upgrade_strategy}")
        print(f"Auto reboot: {'Yes' if auto_reboot else 'No'}")

        print("\n!? CRITICAL ROUTING INFRASTRUCTURE WARNING !?")
        print("SSR firmware upgrades will cause WAN connectivity disruption!")
        print("- SSRs will reboot and SD-WAN tunnels will be offline during upgrade")
        print("- Branch offices may lose connectivity")
        print("- Plan extended maintenance windows")
        print("- Verify backup connectivity paths")
        print("- Coordinate with network operations team")
        print("- Monitor upgrade progress closely")

        print("\nTo proceed with SSR firmware upgrade, type: UPGRADE")
        confirmation = self._safe_input_fn("Confirmation: ", "", True, "SSR firmware upgrade confirmation")

        if confirmation is None or confirmation != "UPGRADE":
            print("-> Operation cancelled - incorrect confirmation")
            logger.info("SSR firmware upgrade cancelled by user")
            return {"cancelled": True}

        # Execute upgrade operation
        print(f"\n{'=' * 60}")
        print("EXECUTING SSR FIRMWARE UPGRADE")
        print(f"{'=' * 60}")

        # Initialize results tracking
        upgrade_results = {
            "operation_id": f"ssr_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_version": target_version,
            "strategy": upgrade_strategy,
            "channel": firmware_channel,
            "reboot": auto_reboot,
            "sites_processed": 0,
            "ssrs_upgraded": 0,
            "errors": [],
            "start_time": datetime.now().isoformat(),
            "site_results": [],
        }

        logger.info(f"Starting SSR firmware upgrade operation: {upgrade_results['operation_id']}")

        # Define SSR model patterns for device filtering
        ssr_models = ["SSR", "128T"]  # Patterns to identify SSR devices

        # Get org-level SSR inventory for validation
        print("-> Validating SSR devices from organization inventory...")
        org_ssr_inventory = {}
        try:
            ssrs_response = mistapi.api.v1.orgs.inventory.getOrgInventory(self.apisession, self.org_id, type="gateway")
            if ssrs_response.status_code == 200:
                for gateway in ssrs_response.data:
                    gateway_id = gateway.get("id")
                    gateway_model = gateway.get("model", "")
                    gateway_type = gateway.get("type", "")

                    # Check if this is an SSR by model or type
                    if gateway_type == "ssr" or "SSR" in gateway_model or "128T" in gateway_model:
                        org_ssr_inventory[gateway_id] = {
                            "model": gateway_model,
                            "type": gateway_type,
                            "version": gateway.get("version", ""),
                            "site_id": gateway.get("site_id", ""),
                        }
                print(f"!? Found {len(org_ssr_inventory)} SSR device(s) in organization inventory")
            else:
                logger.error(f"Failed to get org inventory: {ssrs_response.status_code}")
                print("X  Failed to validate SSR inventory")
        except Exception as e:
            logger.error(f"Error getting org SSR inventory: {e}")
            print(f"X  Error validating SSR inventory: {e}")

        try:
            # Process each site for SSR upgrades
            for site_index, site in enumerate(selected_sites, 1):
                site_id = site.get("id")
                site_name = site.get("name", "Unknown")

                print(f"\n[{site_index}/{len(selected_sites)}] Processing site: {site_name}")
                logger.info(f"Processing site {site_index}/{len(selected_sites)}: {site_name} (ID: {site_id})")

                site_result = {
                    "site_id": site_id,
                    "site_name": site_name,
                    "ssrs_found": 0,
                    "upgrade_initiated": False,
                    "error": None,
                }

                try:
                    # Get SSRs at this site
                    print(f"  -> Discovering SSRs at {site_name}...")
                    site_devices_response = mistapi.api.v1.sites.devices.listSiteDevices(
                        self.apisession, site_id, type="gateway"
                    )

                    if site_devices_response.status_code != 200:
                        error_msg = (
                            f"Failed to retrieve devices for site {site_name}: {site_devices_response.status_code}"
                        )
                        print(f"  X  {error_msg}")
                        site_result["error"] = error_msg
                        upgrade_results["errors"].append(error_msg)
                        continue

                    site_devices = site_devices_response.data

                    # Filter for SSRs at this site
                    site_ssrs = []
                    for device in site_devices:
                        device_model = device.get("model", "")
                        device_type = device.get("type", "")
                        device_id = device.get("id", "")

                        # Debug: Log device details
                        logger.debug(f"Device {device_id}: model='{device_model}', type='{device_type}'")

                        # Check if this is an SSR
                        if device_type == "gateway" and (
                            any(ssr_pattern in device_model for ssr_pattern in ssr_models) or "SSR" in device_model
                        ):
                            site_ssrs.append(device)
                            logger.info(
                                f"Identified SSR device: {device_id} (model: {device_model}, type: {device_type})"
                            )
                            print(f"    -> Identified SSR: {device_model} ({device_id})")
                        else:
                            logger.debug(
                                f"Skipping non-SSR device: {device_id} (model: {device_model}, type: {device_type})"
                            )

                    site_result["ssrs_found"] = len(site_ssrs)

                    if not site_ssrs:
                        print(f"  -> No SSRs found at {site_name}, skipping")
                        logger.info(f"No SSRs found at site {site_name}")
                        upgrade_results["sites_processed"] += 1
                        upgrade_results["site_results"].append(site_result)
                        continue

                    print(f"  !? Found {len(site_ssrs)} SSR(s) at {site_name}")

                    # Initiate firmware upgrade for SSRs at this site
                    ssr_device_ids = [ssr["id"] for ssr in site_ssrs]

                    # Validate device IDs against org SSR inventory and check firmware versions
                    validated_device_ids = []
                    skipped_device_ids = []
                    for device_id in ssr_device_ids:
                        if device_id in org_ssr_inventory:
                            ssr_info = org_ssr_inventory[device_id]
                            current_version = ssr_info.get("version", "")

                            # Check if device is already at target version
                            if current_version == target_version:
                                logger.info(f"Device {device_id} already at target version {target_version} - skipping")
                                print(f"    -> Device {device_id} already at version {target_version} - skipping")
                                skipped_device_ids.append(device_id)
                            else:
                                # Check for potential firmware downgrade
                                if self._is_firmware_downgrade(current_version, target_version):  # type: ignore[no-untyped-call]
                                    logger.warning(
                                        f"Device {device_id} downgrade detected: {current_version} -> {target_version} - skipping"  # noqa: E501
                                    )
                                    print(
                                        f"    ! Downgrade detected: {ssr_info['model']} ({current_version} -> {target_version}) - skipping"  # noqa: E501
                                    )
                                    skipped_device_ids.append(device_id)
                                else:
                                    validated_device_ids.append(device_id)
                                    logger.info(
                                        f"Validated SSR device: {device_id} (model: {ssr_info['model']}, current: {current_version} -> target: {target_version})"  # noqa: E501
                                    )
                                    print(
                                        f"    -> Upgrade needed: {ssr_info['model']} ({current_version} -> {target_version})"  # noqa: E501
                                    )
                        else:
                            logger.warning(f"Device {device_id} not found in org SSR inventory - skipping")
                            print(f"    !? Device {device_id} not in SSR inventory - skipping")
                            skipped_device_ids.append(device_id)

                    if not validated_device_ids:
                        if skipped_device_ids:
                            reason = "already at target version or not in SSR inventory"
                            logger.info(f"All devices at {site_name} skipped: {reason}")
                            print(f"  -> All devices at {site_name} skipped ({reason})")
                        else:
                            logger.warning(f"No validated SSR devices found at {site_name}")
                            print(f"  -> No validated SSR devices at {site_name}, skipping")
                        upgrade_results["sites_processed"] += 1
                        upgrade_results["site_results"].append(site_result)
                        continue

                    print(f"  -> Initiating firmware upgrade for {len(validated_device_ids)} SSR(s) needing upgrade...")
                    if skipped_device_ids:
                        print(
                            f"  -> Skipped {len(skipped_device_ids)} device(s) (already at target version or other issues)"  # noqa: E501
                        )
                    logger.info(
                        f"Initiating SSR firmware upgrade at {site_name} for validated devices: {validated_device_ids}"
                    )

                    # Use Mist API to upgrade SSR firmware
                    # SECURITY: SSR upgrades use org-level API with specific parameters
                    upgrade_body = {
                        "device_ids": validated_device_ids,
                        "channel": firmware_channel,
                        "version": target_version,
                        "strategy": upgrade_strategy,
                    }

                    # Add reboot timing if auto-reboot enabled
                    if auto_reboot:
                        # For auto-reboot, don't set reboot_at (use default timing)
                        # The default is start_time, which enables reboot after download
                        pass  # Let API use default reboot timing
                    else:
                        # Disable reboot if auto_reboot is False
                        upgrade_body["reboot_at"] = -1

                    # Debug: Log the upgrade request body
                    logger.info(f"SSR upgrade request body: {upgrade_body}")
                    print(
                        f"  -> Request body: channel='{firmware_channel}', version='{target_version}', strategy='{upgrade_strategy}'"  # noqa: E501
                    )
                    print(f"  -> Device IDs: {validated_device_ids}")

                    # Execute the SSR-specific upgrade API call
                    upgrade_response = mistapi.api.v1.orgs.ssr.upgradeOrgSsrs(
                        self.apisession, self.org_id, body=upgrade_body
                    )

                    if upgrade_response.status_code in [200, 202]:
                        print(f"  !? Firmware upgrade initiated for {len(validated_device_ids)} SSR(s)")
                        site_result["upgrade_initiated"] = True
                        upgrade_results["ssrs_upgraded"] += len(validated_device_ids)
                        logger.info(f"Successfully initiated SSR firmware upgrade at {site_name}")
                    else:
                        # Log response details for debugging
                        try:
                            # Try multiple ways to get response content
                            if hasattr(upgrade_response, "data") and upgrade_response.data:
                                response_text = str(upgrade_response.data)
                            elif hasattr(upgrade_response, "text") and upgrade_response.text:
                                response_text = upgrade_response.text
                            elif hasattr(upgrade_response, "content") and upgrade_response.content:
                                response_text = upgrade_response.content.decode("utf-8")
                            else:
                                response_text = f"Status: {upgrade_response.status_code}, Headers: {dict(upgrade_response.headers) if hasattr(upgrade_response, 'headers') else 'None'}"  # noqa: E501

                            # Check for specific error types
                            if "already at the requested fw version" in response_text.lower():
                                # This is informational, not a real error
                                logger.info(f"SSR upgrade skipped at {site_name}: devices already at target version")
                                print(f"  - SSRs at {site_name} already at target version {target_version}")
                                site_result["upgrade_initiated"] = False
                                site_result["skip_reason"] = "already_at_version"
                                # Don't count this as an error
                            elif "downgrade fw version not allowed" in response_text.lower():
                                # This is a validation error, not a system error
                                logger.warning(
                                    f"SSR downgrade rejected at {site_name}: API prevents firmware downgrades"
                                )
                                print(f"  ! Firmware downgrade not allowed at {site_name} - API validation failed")
                                site_result["upgrade_initiated"] = False
                                site_result["skip_reason"] = "downgrade_not_allowed"
                                # Don't count this as a critical error
                            else:
                                logger.error(f"SSR upgrade API error response: {response_text}")
                                print(f"  -> API Response: {response_text}")

                                error_msg = f"Upgrade initiation failed for {site_name}: {upgrade_response.status_code}"
                                print(f"  X  {error_msg}")
                                site_result["error"] = error_msg
                                upgrade_results["errors"].append(error_msg)
                                logger.error(
                                    f"SSR firmware upgrade failed at {site_name}: {upgrade_response.status_code}"
                                )

                        except Exception as e:
                            logger.error(f"Could not read response details: {e}")
                            print(f"  -> Could not read response: {e}")

                            error_msg = f"Upgrade initiation failed for {site_name}: {upgrade_response.status_code}"
                            print(f"  X  {error_msg}")
                            site_result["error"] = error_msg
                            upgrade_results["errors"].append(error_msg)
                            logger.error(f"SSR firmware upgrade failed at {site_name}: {upgrade_response.status_code}")

                except Exception as site_error:
                    error_msg = f"Error processing site {site_name}: {str(site_error)}"
                    print(f"  X  {error_msg}")
                    site_result["error"] = error_msg
                    upgrade_results["errors"].append(error_msg)
                    logger.error(f"Site processing error for {site_name}: {str(site_error)}")

                upgrade_results["sites_processed"] += 1
                upgrade_results["site_results"].append(site_result)

            # Operation completion
            upgrade_results["end_time"] = datetime.now().isoformat()

            print(f"\n{'=' * 60}")
            print("SSR FIRMWARE UPGRADE OPERATION COMPLETED")
            print(f"{'=' * 60}")
            print(f"Operation ID: {upgrade_results['operation_id']}")
            print(f"Sites processed: {upgrade_results['sites_processed']}")
            print(f"SSRs upgraded: {upgrade_results['ssrs_upgraded']}")
            print(f"Errors encountered: {len(upgrade_results['errors'])}")

            if upgrade_results["errors"]:
                print("\nErrors:")
                for error in upgrade_results["errors"]:
                    print(f"  - {error}")

            print("\nSSR upgrade operations have been initiated.")
            print("Monitor progress through Mist dashboard or API.")
            print("Check individual SSR status for completion and connectivity.")
            print("Verify SD-WAN tunnel re-establishment after reboots.")

            logger.info(f"SSR firmware upgrade operation completed: {upgrade_results['operation_id']}")
            return upgrade_results

        except Exception as e:
            error_msg = f"Critical error in SSR firmware upgrade: {str(e)}"
            print(f"\nX  {error_msg}")
            logger.error(error_msg)

            upgrade_results["end_time"] = datetime.now().isoformat()
            upgrade_results["error"] = str(e)

            return upgrade_results

    def _upgrade_ssr_firmware_by_gateway_template(self):  # type: ignore[no-untyped-def]
        """
        Advanced SSR firmware upgrade organized by Gateway Template assignment.

        This method provides template-based SSR firmware upgrades with:
        1. Interactive Gateway Template selection with site count display
        2. Automatic site discovery for selected template (same logic as AP/switch systems)
        3. SSR enumeration across all sites in template
        4. Model-based firmware version selection optimized for Session Smart Routers
        5. Unified upgrade execution across template sites
        6. SSR-specific safety measures and WAN connectivity disruption warnings
        7. Comprehensive audit logging and progress monitoring
        8. HA pair coordination and failover considerations

        Features:
        - Template selection by index or name (reuses AP/switch template infrastructure)
        - Site count and SSR count display per template
        - SSR-specific upgrade parameters (reboot, snapshot, conservative strategy)
        - Enhanced WAN connectivity warnings for production environments
        - Maintains all existing safety confirmations and audit trails

        SECURITY: Template-based upgrades affect multiple sites simultaneously.
        Ensure adequate maintenance windows and backup connectivity before proceeding.
        """
        logging.info("Starting template-based SSR firmware upgrade...")
        logging.debug("FirmwareManager._upgrade_ssr_firmware_by_gateway_template() initiated")

        print(" Advanced SSR Firmware Upgrade by Gateway Template")
        print("=" * 70)

        # Step 1: Ensure required CSVs are fresh (reuse AP/switch template infrastructure)
        self._ensure_template_csv_freshness()  # type: ignore[no-untyped-call]

        # Step 2: Load template-to-sites mapping (same as AP/switch systems)
        template_name_to_id, template_sites_mapping = self._load_template_sites_mapping()  # type: ignore[no-untyped-call]

        if not template_sites_mapping:
            print("\n! No Gateway Templates with assigned sites found.")
            print("  Make sure sites are assigned to Gateway Templates and try again.")
            logging.warning("No Gateway Templates with site assignments found")
            return

        # Step 3: Template selection (reuse AP/switch template selection logic)
        selected_template_id, selected_template_name = self._prompt_template_selection(  # type: ignore[no-untyped-call]
            template_name_to_id, template_sites_mapping
        )

        if not selected_template_id:
            print(" No template selected. Exiting.")
            return

        # Step 4: Get sites for selected template
        sites_to_upgrade = template_sites_mapping.get(selected_template_id, [])

        print(f"\n  Template '{selected_template_name}' includes {len(sites_to_upgrade)} sites")
        logging.info(f"Template {selected_template_name} has {len(sites_to_upgrade)} assigned sites")

        return self._execute_template_based_ssr_upgrade(sites_to_upgrade, selected_template_name)  # type: ignore[no-untyped-call]

    def _execute_template_based_ssr_upgrade(self, sites_to_upgrade, selected_template_name):  # type: ignore[no-untyped-def]
        """Execute the template-based SSR upgrade with the existing SSR implementation."""
        print(f"  Proceeding with SSR firmware upgrade for template: {selected_template_name}")
        print(f"  Target sites: {len(sites_to_upgrade)}")

        # Use the SSR-specific bulk upgrade implementation
        return self._bulk_upgrade_ssr_firmware_by_site(sites_to_upgrade)  # type: ignore[no-untyped-call]


# NOTE: check_firmware_upgrade_status_direct removed - use FirmwareManager(apisession, org_id).check_firmware_upgrade_status() directly  # noqa: E501
