"""Bulk AP firmware upgrade operations for Mist organizations.

Manages the complete workflow for upgrading AP firmware across one or more
sites: site selection, AP discovery, firmware version analysis, advanced
upgrade configuration, execution, and tracking.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import csv
import importlib
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any


class BulkAPFirmwareUpgrader:  # pylint: disable=too-many-instance-attributes
    """Bulk AP Firmware Upgrade Manager.

    Manages the complete workflow for upgrading AP firmware across one or
    more sites:
    - Site selection (override, file-based, or interactive)
    - AP discovery and grouping by model
    - Firmware version analysis and selection
    - Cross-model compatibility analysis
    - Advanced upgrade configuration (strategies, P2P, scheduling)
    - Upgrade execution and tracking
    - Auto-upgrade configuration

    NETWORK IMPACT WARNING:
    - APs will REBOOT during firmware upgrades
    - Wi-Fi connectivity will be TEMPORARILY LOST
    - Upgrades take 5-15 minutes per device
    """

    def __init__(
        self,
        org_id: str,
        apisession: Any,
        *,
        sites_override: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
        safe_input_fn: Any = None,
        check_stop_fn: Any = None,
        fetch_sites_fn: Any = None,
        get_csv_path_fn: Any = None,
        check_firmware_status_fn: Any = None,
        get_org_id_fn: Any = None,
    ) -> None:
        """Initialize the bulk AP firmware upgrader.

        Args:
            org_id: Mist organization ID.
            apisession: Authenticated mistapi session.
            sites_override: Pre-selected sites list to skip interactive selection.
            dry_run: If True, simulate upgrades without making API calls.
            safe_input_fn: Callable for safe user input (prompt, context) -> str.
            check_stop_fn: Callable to check for stop signal () -> bool.
            fetch_sites_fn: Callable to fetch all sites (org_id) -> list.
            get_csv_path_fn: Callable to get CSV path (filename) -> str.
            check_firmware_status_fn: Callable to check firmware status.
            get_org_id_fn: Callable to get or prompt for org_id.
        """
        self.org_id = org_id
        self.apisession = apisession
        self.sites_override = sites_override
        self.dry_run = dry_run
        self._input_fn = safe_input_fn or input
        self._check_stop_fn = check_stop_fn
        self._fetch_sites_fn = fetch_sites_fn
        self._get_csv_path_fn = get_csv_path_fn
        self._check_firmware_status_fn = check_firmware_status_fn
        self._get_org_id_fn = get_org_id_fn

        # Site context
        self.sites_to_upgrade: list[dict[str, Any]] = []
        self.all_sites_aps: dict[str, Any] = {}

        # AP data
        self.all_aps: list[dict[str, Any]] = []
        self.aps_by_model: dict[str, list[dict[str, Any]]] = {}
        self.ap_versions: dict[str, str] = {}

        # Firmware data
        self.available_versions: list[Any] = []
        self.model_version_ranges: dict[str, list[str]] = {}

        # Upgrade plan
        self.upgrade_plan: dict[str, dict[str, Any]] = {}
        self.skipped_already_at_target: int = 0
        self.upgrade_config: dict[str, Any] = {}
        self.upgrade_ids: list[str] = []

        # Results tracking
        self.results: list[dict[str, Any]] = []
        self.successful_upgrades: int = 0
        self.failed_upgrades: int = 0

    def execute(self) -> None:
        """Execute the bulk AP firmware upgrade workflow."""
        logging.info("Starting advanced bulk AP firmware upgrade by site...")
        logging.debug("BulkAPFirmwareUpgrader.execute() initiated")
        logging.debug(f"Using org_id: {self.org_id}")

        if self.dry_run:
            print("\n  >> DRY-RUN MODE: No actual upgrades will be performed <<")
            logging.info("DRY-RUN MODE enabled - no API calls will be made")

        try:
            if not self._step1_determine_sites():
                return
            if not self._step2_discover_aps():
                return
            if not self._step3_fetch_firmware_stats():
                return
            if not self._step4_fetch_available_firmware():
                return
            if not self._step5_select_firmware_versions():
                return
            if not self._step6_configure_upgrade():
                return
            if not self._step7_confirm_upgrade():
                return
            self._step8_execute_upgrades()
            self._step9_configure_auto_upgrade()
            self._step10_offer_status_check()
            self._step11_write_results()
        except KeyboardInterrupt:
            print("\n Operation cancelled by user.")
            logging.info("Bulk AP firmware upgrade cancelled by user interrupt")

    # =========================================================================
    # STEP 1: SITE SELECTION
    # =========================================================================

    def _step1_determine_sites(self) -> bool:
        """Determine which sites to upgrade."""
        if self.sites_override:
            return self._use_override_sites()
        return self._determine_sites_interactive()

    def _use_override_sites(self) -> bool:
        """Use pre-selected sites from override."""
        self.sites_to_upgrade = self.sites_override or []
        site_names = ", ".join(s.get("name", "?") for s in self.sites_to_upgrade)
        print(f"\n  Using pre-selected sites: {site_names}")
        logging.info(f"Using {len(self.sites_to_upgrade)} override sites")
        return bool(self.sites_to_upgrade)

    def _determine_sites_interactive(self) -> bool:
        """Determine sites from file or interactive selection."""
        csv_path = self._resolve_csv_path()
        if csv_path and os.path.exists(csv_path):
            return self._load_sites_from_file(csv_path)
        return self._select_site_interactively()

    def _resolve_csv_path(self) -> str | None:
        """Resolve path to APUpgradeSiteList.CSV."""
        if self._get_csv_path_fn:
            result: str | None = self._get_csv_path_fn("APUpgradeSiteList.CSV")
            return result
        default = os.path.join("data", "APUpgradeSiteList.CSV")
        return default if os.path.exists(default) else None

    def _load_sites_from_file(self, csv_path: str) -> bool:
        """Load site names from CSV and resolve to site IDs."""
        print(f"\n  Found site list file: {csv_path}")
        site_names = self._read_site_names_from_file(csv_path)
        if not site_names:
            print(" No site names found in file.")
            return False

        print(f"  Read {len(site_names)} site name(s) from file")
        all_sites = self._fetch_org_sites_for_lookup()
        if not all_sites:
            return False

        return self._resolve_site_names(site_names, all_sites)

    def _read_site_names_from_file(self, csv_path: str) -> list[str]:
        """Read site names from CSV file."""
        site_names = []
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():
                        site_names.append(row[0].strip())
        except Exception as error:
            print(f" Error reading site list: {error}")
            logging.error(f"Failed to read site list from {csv_path}: {error}")
        return site_names

    def _fetch_org_sites_for_lookup(self) -> list[dict[str, Any]]:
        """Fetch all org sites for name-to-ID lookup."""
        if self._fetch_sites_fn:
            sites_result: list[dict[str, Any]] = list(self._fetch_sites_fn(self.org_id))
            return sites_result
        try:
            import mistapi

            response = mistapi.api.v1.orgs.sites.listOrgSites(self.apisession, self.org_id)
            all_sites: list[dict[str, Any]] = list(mistapi.get_all(response=response, mist_session=self.apisession))
            return all_sites
        except Exception as error:
            print(f" Failed to fetch org sites: {error}")
            logging.error(f"Failed to fetch sites for org {self.org_id}: {error}")
            return []

    def _resolve_site_names(self, site_names: list[str], all_sites: list[dict[str, Any]]) -> bool:
        """Resolve site names to site dicts."""
        site_lookup = {s.get("name", "").lower(): s for s in all_sites}
        resolved = []
        missing = []

        for name in site_names:
            site = site_lookup.get(name.lower())
            if site:
                resolved.append(site)
            else:
                missing.append(name)

        if missing:
            self._report_missing_sites(missing)

        self.sites_to_upgrade = resolved
        if resolved:
            print(f"  Resolved {len(resolved)} site(s) for upgrade")
        return bool(resolved)

    def _report_missing_sites(self, missing: list[str]) -> None:
        """Report sites that could not be resolved."""
        print(f"\n  Warning: {len(missing)} site(s) not found:")
        for name in missing[:10]:
            print(f"    - {name}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")

    def _select_site_interactively(self) -> bool:
        """Interactive site selection."""
        all_sites = self._fetch_org_sites_for_lookup()
        if not all_sites:
            print(" No sites found in organization.")
            return False

        print("\n  Site Selection:")
        print("   [1] All sites in organization")
        print("   [2] Select specific sites")

        try:
            choice = self._input_fn("Select option (1-2): ").strip()
        except (EOFError, KeyboardInterrupt):
            return False

        if choice == "1":
            return self._select_all_sites(all_sites)
        return self._select_multiple_sites(all_sites)

    def _select_all_sites(self, all_sites: list[dict[str, Any]]) -> bool:
        """Select all sites in organization."""
        self.sites_to_upgrade = all_sites
        print(f"  Selected all {len(all_sites)} sites")
        return True

    def _select_multiple_sites(self, all_sites: list[dict[str, Any]]) -> bool:
        """Interactive multi-site selection."""
        print("\n  Available Sites:")
        for idx, site in enumerate(all_sites, 1):
            print(f"   [{idx}] {site.get('name', 'Unknown')}")

        print("\n  Enter site numbers (comma-separated, e.g., 1,3,5):")
        try:
            selection = self._input_fn("Selection: ").strip()
        except (EOFError, KeyboardInterrupt):
            return False

        indices = self._parse_index_input(selection, len(all_sites))
        if not indices:
            print(" No valid sites selected.")
            return False

        self.sites_to_upgrade = [all_sites[i] for i in indices]
        names = ", ".join(s.get("name", "?") for s in self.sites_to_upgrade)
        print(f"  Selected {len(self.sites_to_upgrade)} site(s): {names}")
        return True

    def _parse_index_input(self, text: str, max_count: int) -> list[int]:  # noqa: C901
        """Parse comma-separated index input."""
        indices = []
        for part in text.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = part.split("-", 1)
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1
                    for i in range(start_idx, min(end_idx + 1, max_count)):
                        if 0 <= i < max_count and i not in indices:
                            indices.append(i)
                except ValueError:
                    continue
            elif part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < max_count and idx not in indices:
                    indices.append(idx)
        return indices

    # =========================================================================
    # STEP 2: AP DISCOVERY
    # =========================================================================

    def _step2_discover_aps(self) -> bool:
        """Discover APs across selected sites."""
        print("\n  Discovering APs across selected sites...")
        import mistapi

        for site_info in self.sites_to_upgrade:
            self._fetch_aps_for_site(site_info, mistapi)

        self._display_ap_discovery_summary()

        if not self.all_aps:
            print(" No APs found at any selected site.")
            return False
        return True

    def _fetch_aps_for_site(self, site_info: dict[str, Any], mistapi: Any) -> None:
        """Fetch APs for a single site."""
        site_id = site_info["id"]
        site_name = site_info["name"]
        try:
            print(f"   Fetching APs at site '{site_name}'...")
            response = mistapi.api.v1.sites.devices.listSiteDevices(self.apisession, site_id, type="ap")
            site_aps = mistapi.get_all(response=response, mist_session=self.apisession)

            if site_aps:
                for ap in site_aps:
                    ap["_site_id"] = site_id
                    ap["_site_name"] = site_name
                self.all_aps.extend(site_aps)
                self.all_sites_aps[site_id] = {
                    "name": site_name,
                    "aps": site_aps,
                    "count": len(site_aps),
                }
                print(f"      Found {len(site_aps)} APs at '{site_name}'")
            else:
                self.all_sites_aps[site_id] = {
                    "name": site_name,
                    "aps": [],
                    "count": 0,
                }
                print(f"      No APs found at site '{site_name}'")
        except Exception as error:
            self.all_sites_aps[site_id] = {
                "name": site_name,
                "aps": [],
                "count": 0,
                "error": str(error),
            }
            print(f"      Failed to fetch APs for site '{site_name}': {error}")

    def _display_ap_discovery_summary(self) -> None:
        """Display AP discovery summary with per-site model breakdown."""
        total_aps = len(self.all_aps)
        sites_with_aps = len([s for s in self.all_sites_aps.values() if s["count"] > 0])

        print("\n  AP Discovery Summary:")
        print(f"   Total APs found: {total_aps}")
        print(f"   Sites with APs: {sites_with_aps}/{len(self.sites_to_upgrade)}")

        print("\n  Per-Site Breakdown:")
        print("  " + "-" * 70)
        for site_data in self.all_sites_aps.values():
            self._print_site_ap_breakdown(site_data)
        print("  " + "-" * 70)

    def _print_site_ap_breakdown(self, site_data: dict[str, Any]) -> None:
        """Print AP breakdown for a single site."""
        site_name = site_data["name"]
        ap_count = site_data["count"]

        if "error" in site_data:
            print(f"   {site_name}: ERROR - {site_data['error']}")
        elif ap_count == 0:
            print(f"   {site_name}: No APs (will be skipped)")
        else:
            model_counts: dict[str, int] = {}
            for ap in site_data.get("aps", []):
                model = ap.get("model", "Unknown")
                model_counts[model] = model_counts.get(model, 0) + 1
            model_summary = ", ".join(f"{m}:{c}" for m, c in sorted(model_counts.items()))
            print(f"   {site_name}: {ap_count} APs ({model_summary})")

    # =========================================================================
    # STEP 3: FIRMWARE STATS COLLECTION
    # =========================================================================

    def _step3_fetch_firmware_stats(self) -> bool:
        """Fetch firmware stats and group APs by model."""
        print("\n  Getting current firmware versions from device statistics...")

        stats_lookup = self._fetch_all_ap_stats()
        self._process_aps_with_stats(stats_lookup)
        self._display_model_summary()
        return True

    def _fetch_all_ap_stats(self) -> dict[str, Any]:
        """Fetch device stats for all sites."""
        stats_lookup: dict[str, Any] = {}
        for site_id, site_data in self.all_sites_aps.items():
            if site_data["count"] == 0:
                continue
            site_stats = self._fetch_site_ap_stats(site_id, site_data["name"])
            stats_lookup.update(site_stats)
        return stats_lookup

    def _fetch_site_ap_stats(self, site_id: str, site_name: str) -> dict[str, Any]:
        """Fetch AP stats for a single site."""
        import mistapi

        lookup: dict[str, Any] = {}
        try:
            print(f"   Fetching device statistics for APs at '{site_name}'...")
            stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                self.apisession, site_id, type="ap", limit=1000
            )
            site_stats = mistapi.get_all(response=stats_resp, mist_session=self.apisession)
            if site_stats:
                for stats in site_stats:
                    device_id = stats.get("id") or stats.get("device_id") or stats.get("mac")
                    if device_id:
                        lookup[device_id] = stats
        except Exception as error:
            logging.error(f"Failed to fetch stats for site {site_name}: {error}")
        return lookup

    def _process_aps_with_stats(self, stats_lookup: dict[str, Any]) -> None:
        """Process APs and extract version information."""
        for ap in self.all_aps:
            model = ap.get("model", "Unknown")
            device_id: str = str(ap.get("id", ""))

            if model not in self.aps_by_model:
                self.aps_by_model[model] = []
            self.aps_by_model[model].append(ap)

            version = self._get_ap_version(ap, stats_lookup)
            self.ap_versions[device_id] = version

    def _get_ap_version(self, ap: dict[str, Any], stats_lookup: dict[str, Any]) -> str:
        """Get firmware version for an AP."""
        device_id: str = str(ap.get("id", ""))
        device_mac: str = str(ap.get("mac", ""))

        for key in [device_id, device_mac]:
            if key and key in stats_lookup:
                stats = stats_lookup[key]
                if isinstance(stats, dict):
                    version: str = str(stats.get("version", "Unknown"))
                    return version
        return "Unknown"

    def _display_model_summary(self) -> None:
        """Display summary of AP models found."""
        print(f"\n  AP Models found across {len(self.sites_to_upgrade)} site(s):")
        for model, devices in self.aps_by_model.items():
            versions = set(self.ap_versions.get(str(d.get("id", "")), "Unknown") for d in devices)
            versions_text = ", ".join(sorted(versions, reverse=True)) if "Unknown" not in versions else "Unknown"
            print(f"   !? {model}: {len(devices)} devices" f" (Current versions: {versions_text})")

    # =========================================================================
    # STEP 4: AVAILABLE FIRMWARE VERSIONS
    # =========================================================================

    def _step4_fetch_available_firmware(self) -> bool:
        """Fetch available firmware versions from API."""
        import mistapi

        print("\n  Fetching available firmware versions...")
        try:
            response = mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions(self.apisession, self.org_id)
            self.available_versions = response.data
            self._build_model_version_ranges()
            return True
        except Exception as error:
            print(f"! Failed to fetch available firmware versions: {error}")
            return False

    def _build_model_version_ranges(self) -> None:
        """Build model-to-versions mapping."""
        if not self.available_versions:
            return
        for version_info in self.available_versions:
            if not isinstance(version_info, dict):
                continue
            models = version_info.get("models", [])
            model = version_info.get("model")
            version = version_info.get("version", "Unknown")

            target_models = models if models else ([model] if model else [])
            for m in target_models:
                if m:
                    if m not in self.model_version_ranges:
                        self.model_version_ranges[m] = []
                    self.model_version_ranges[m].append(version)

    # =========================================================================
    # STEP 5: FIRMWARE VERSION SELECTION
    # =========================================================================

    def _step5_select_firmware_versions(self) -> bool:
        """Let user select firmware version for each model."""
        print("\n  Firmware Version Selection:")
        print("=" * 60)

        self._display_current_version_summary()
        self._display_compatibility_analysis()

        for model, devices in self.aps_by_model.items():
            self._select_version_for_model(model, devices)

        if not self.upgrade_plan:
            print(" No firmware upgrades selected. Exiting.")
            return False

        return self._validate_upgrade_plan()

    def _display_current_version_summary(self) -> None:
        """Display current firmware status summary."""
        print("! Current Firmware Status Summary:")
        all_versions: dict[str, list[str]] = {}
        for model, devices in self.aps_by_model.items():
            for device in devices:
                version = self.ap_versions.get(str(device.get("id", "")), "Unknown")
                if version not in all_versions:
                    all_versions[version] = []
                all_versions[version].append(f"{device.get('name', 'Unnamed')} ({model})")

        for version, device_list in sorted(all_versions.items(), reverse=True):
            print(f"   Version {version}: {len(device_list)} devices")

    def _display_compatibility_analysis(self) -> None:
        """Display cross-model compatibility analysis."""
        site_models = set(self.aps_by_model.keys())
        matching = site_models.intersection(set(self.model_version_ranges.keys()))

        if len(matching) <= 1:
            return

        print("\n  Version Compatibility Analysis:")
        universal = self._find_universal_versions(matching)
        if universal:
            print("   UNIVERSAL versions (compatible with ALL models):")
            print(f"      {', '.join(sorted(universal, reverse=True)[:5])}")

    def _find_universal_versions(self, models: set[str]) -> list[str]:
        """Find versions compatible with all models."""
        all_versions: set[str] = set()
        for model in models:
            if model in self.model_version_ranges:
                all_versions.update(self.model_version_ranges[model])

        return [v for v in all_versions if all(v in self.model_version_ranges.get(m, []) for m in models)]

    def _select_version_for_model(self, model: str, devices: list[dict[str, Any]]) -> bool:
        """Select firmware version for a specific model."""
        model_versions = self._get_versions_for_model(model)
        if not model_versions:
            print(f"!  No firmware versions found for model '{model}' - skipping")
            return False

        print(f"\n  Model: {model} ({len(devices)} devices)")
        self._display_model_versions(model, model_versions)
        return self._get_user_version_selection(model, devices, model_versions)

    def _get_versions_for_model(self, model: str) -> list[dict[str, Any]]:
        """Get deduplicated, sorted versions for a model."""
        raw_versions = []
        for v in self.available_versions:
            if isinstance(v, dict):
                models = v.get("models", [])
                single = v.get("model")
                if model in models or single == model:
                    raw_versions.append(v)

        version_dict: dict[str, dict[str, Any]] = {}
        for v in raw_versions:
            num = v.get("version", "Unknown")
            if num not in version_dict:
                version_dict[num] = v

        versions = list(version_dict.values())
        try:
            versions.sort(
                key=lambda x: tuple(map(int, x.get("version", "0").split("."))),
                reverse=True,
            )
        except ValueError:
            versions.sort(key=lambda x: x.get("version", ""), reverse=True)
        return versions

    def _display_model_versions(self, model: str, versions: list[dict[str, Any]]) -> None:
        """Display available versions for a model."""
        current = set(self.ap_versions.get(str(d.get("id", "")), "Unknown") for d in self.aps_by_model[model])
        print(f"   Current versions: {', '.join(sorted(current, reverse=True))}")
        print(f"   Available versions ({len(versions)} found):")

        for idx, v in enumerate(versions):
            num = v.get("version", "Unknown")
            indicators = []
            if v.get("recommended"):
                indicators.append("RECOMMENDED")
            if num in current:
                indicators.append("CURRENT")
            ind_text = f" [{', '.join(indicators)}]" if indicators else ""
            print(f"      [{idx}] {num}{ind_text}")

    def _get_user_version_selection(
        self,
        model: str,
        devices: list[dict[str, Any]],
        versions: list[dict[str, Any]],
    ) -> bool:
        """Get user's version selection for a model."""
        while True:
            try:
                user_input = (
                    self._input_fn(f"Select version for {model} (0-{len(versions) - 1}, 's' to skip): ").strip().lower()
                )
                if user_input == "s":
                    print(f"!  Skipping firmware upgrade for {model}")
                    return False

                idx = int(user_input)
                if 0 <= idx < len(versions):
                    return self._apply_version_selection(model, devices, versions[idx])
                print("! Invalid selection.")
            except ValueError:
                print(" Invalid input.")
            except KeyboardInterrupt:
                return False

    def _apply_version_selection(
        self,
        model: str,
        devices: list[dict[str, Any]],
        selected: dict[str, Any],
    ) -> bool:
        """Apply a version selection, filtering already-upgraded devices."""
        target_version = selected.get("version")
        needing_upgrade = []
        already_at_target = []

        for device in devices:
            device_id: str = str(device.get("id", ""))
            current = self.ap_versions.get(device_id, "Unknown")
            if current == target_version:
                already_at_target.append(device)
            else:
                needing_upgrade.append(device)

        if already_at_target:
            print(f"   -> Skipping {len(already_at_target)} device(s)" f" already at {target_version}")
            self.skipped_already_at_target += len(already_at_target)

        if not needing_upgrade:
            print(f"!  All {len(devices)} {model} devices already at" f" {target_version} - nothing to upgrade")
            return False

        self.upgrade_plan[model] = {
            "version": target_version,
            "version_info": selected,
            "devices": needing_upgrade,
        }
        print(f"! Selected version {target_version} for {model}" f" ({len(needing_upgrade)} devices need upgrade)")
        return True

    def _validate_upgrade_plan(self) -> bool:
        """Validate and display upgrade plan summary."""
        print("\n  Upgrade Plan Summary:")
        print("=" * 60)

        total = sum(len(p["devices"]) for p in self.upgrade_plan.values())
        versions = set(p["version"] for p in self.upgrade_plan.values())

        for model, plan in self.upgrade_plan.items():
            print(f"   {model}: {len(plan['devices'])} devices" f" firmware {plan['version']}")

        print(f"\n   Total: {total} devices to upgrade, {len(versions)} version(s)")
        if self.skipped_already_at_target > 0:
            print(f"   Skipped: {self.skipped_already_at_target}" " devices already at target version")

        if len(versions) > 1:
            confirm = self._input_fn("\n  Proceed with multi-version upgrade? (y/n): ").strip().lower() or "y"
            if confirm not in ["y", "yes"]:
                return False
        return True

    # =========================================================================
    # STEP 6: UPGRADE CONFIGURATION
    # =========================================================================

    def _step6_configure_upgrade(self) -> bool:
        """Configure advanced upgrade options."""
        print("\n  Advanced Upgrade Configuration:")
        print("=" * 60)

        self._select_strategy()
        self._configure_strategy_options()
        self._configure_p2p()
        self._configure_scheduling()
        self._configure_force_option()
        self._display_final_config()
        return True

    def _select_strategy(self) -> None:
        """Select separate download and reboot strategies."""
        download_strategies = {
            "1": ("big_bang", "Download all at once - no orchestration"),
            "2": ("serial", "Download one device at a time"),
            "3": ("canary", "Phased download rollout"),
        }
        reboot_strategies = {
            "1": ("big_bang", "Reboot all at once"),
            "2": ("serial", "Reboot one at a time"),
            "3": ("canary", "Phased reboot rollout"),
            "4": ("rrm", "RRM-aware reboot (AP only - minimizes Wi-Fi disruption)"),
        }

        print("\n DOWNLOAD Strategy (how firmware is distributed):")
        for key, (name, desc) in download_strategies.items():
            print(f"   [{key}] {name.upper()}: {desc}")

        download_choice = self._input_fn("Select download strategy (1-3, default=3 canary): ").strip() or "3"
        download_strategy = download_strategies.get(download_choice, download_strategies["3"])[0]
        print(f"! Selected download strategy: {download_strategy.upper()}")

        print("\n REBOOT Strategy (how devices restart after download):")
        for key, (name, desc) in reboot_strategies.items():
            print(f"   [{key}] {name.upper()}: {desc}")

        reboot_choice = self._input_fn("Select reboot strategy (1-4, default=4 rrm): ").strip() or "4"
        reboot_strategy = reboot_strategies.get(reboot_choice, reboot_strategies["4"])[0]
        print(f"! Selected reboot strategy: {reboot_strategy.upper()}")

        self.upgrade_config = {
            "download_strategy": download_strategy,
            "reboot_strategy": reboot_strategy,
            "force": False,
            "enable_p2p": True,
            "max_failure_percentage": 7,
            "start_time": None,
            "canary_phases": [1, 2, 4, 8, 16, 32, 64, 100],
            "p2p_cluster_size": 5,
            "p2p_parallelism": 100,
            "reboot": True,
        }
        print(f"\n! Final strategy: Download={download_strategy.upper()}," f" Reboot={reboot_strategy.upper()}")

    def _configure_strategy_options(self) -> None:
        """Configure strategy-specific options."""
        if self.upgrade_config["download_strategy"] == "canary":
            self._configure_canary_options()
        if self.upgrade_config["reboot_strategy"] == "rrm":
            self._configure_rrm_options()

    def _configure_canary_options(self) -> None:
        """Configure canary strategy options."""
        print("\n  Canary Strategy Configuration:")
        try:
            failure = self._input_fn("Max failure % (default=7): ").strip()
            if failure:
                self.upgrade_config["max_failure_percentage"] = int(failure)
        except ValueError:
            pass

    def _configure_rrm_options(self) -> None:
        """Configure RRM strategy options."""
        print("\n  RRM Strategy Configuration:")
        self.upgrade_config["rrm_node_order"] = "fringe_to_center"
        self.upgrade_config["rrm_first_batch_percentage"] = 2
        self.upgrade_config["rrm_max_batch_percentage"] = 10

    def _configure_p2p(self) -> None:
        """Configure P2P settings."""
        print("\n  Peer-to-Peer Configuration:")
        enable = self._input_fn("Enable P2P firmware sharing? (Y/n): ").strip().lower()
        self.upgrade_config["enable_p2p"] = enable not in ["n", "no"]
        if self.upgrade_config["enable_p2p"]:
            print(" P2P enabled")

    def _configure_scheduling(self) -> None:
        """Configure scheduling options."""
        print("\n  Scheduling Options:")
        schedule = self._input_fn("Schedule for later? (y/N): ").strip().lower()
        if schedule in ["y", "yes"]:
            self._get_scheduled_time()

    def _get_scheduled_time(self) -> None:
        """Get scheduled start time from user."""
        try:
            time_input = self._input_fn("Start time (+minutes or YYYY-MM-DD HH:MM): ").strip()
            if time_input.startswith("+"):
                minutes = int(time_input[1:])
                self.upgrade_config["start_time"] = int(time.time()) + (minutes * 60)
            else:
                dt = datetime.strptime(time_input, "%Y-%m-%d %H:%M")
                self.upgrade_config["start_time"] = int(dt.timestamp())
        except ValueError:
            print(" Invalid format, scheduling immediately")

    def _configure_force_option(self) -> None:
        """Configure force upgrade option."""
        force = self._input_fn("Force upgrade even if same version? (y/N): ").strip().lower()
        self.upgrade_config["force"] = force in ["y", "yes"]

    def _display_final_config(self) -> None:
        """Display final upgrade configuration."""
        print("\n  Final Configuration:")
        print(f"Download Strategy: {self.upgrade_config['download_strategy'].upper()}")
        print(f"Reboot Strategy: {self.upgrade_config['reboot_strategy'].upper()}")
        print(f"P2P: {self.upgrade_config['enable_p2p']}")
        print(f"Force: {self.upgrade_config['force']}")

    # =========================================================================
    # STEP 7: CONFIRMATION
    # =========================================================================

    def _step7_confirm_upgrade(self) -> bool:
        """Display warnings and get user confirmation."""
        total = sum(len(p["devices"]) for p in self.upgrade_plan.values())

        if len(self.sites_to_upgrade) > 1:
            self._display_multi_site_summary()

        self._display_upgrade_warnings()
        self._display_final_plan()
        self._display_api_call_estimate()

        return self._get_upgrade_confirmation(total)

    def _estimate_api_calls(self) -> dict[str, Any]:
        """Estimate the number of API calls required for the upgrade."""
        devices_by_site: dict[str, dict[str, Any]] = {}
        for _model, plan in self.upgrade_plan.items():
            version = plan["version"]
            for device in plan["devices"]:
                site_id = device.get("_site_id")
                site_name = device.get("_site_name", "Unknown")
                if site_id not in devices_by_site:
                    devices_by_site[site_id] = {
                        "name": site_name,
                        "versions": set(),
                        "models": set(),
                        "device_count": 0,
                    }
                devices_by_site[site_id]["versions"].add(version)
                devices_by_site[site_id]["models"].add(_model)
                devices_by_site[site_id]["device_count"] += 1

        upgrade_calls = 0
        breakdown = []
        for _site_id, site_info in devices_by_site.items():
            num_versions = len(site_info["versions"])
            calls_for_site = num_versions
            reason = "single version" if num_versions == 1 else f"{num_versions} versions"
            upgrade_calls += calls_for_site
            breakdown.append(
                {
                    "site_name": site_info["name"],
                    "devices": site_info["device_count"],
                    "calls": calls_for_site,
                    "reason": reason,
                }
            )

        auto_upgrade_calls = len(devices_by_site)
        return {
            "upgrade_calls": upgrade_calls,
            "auto_upgrade_calls": auto_upgrade_calls,
            "total_calls": upgrade_calls,
            "site_count": len(devices_by_site),
            "breakdown": breakdown,
        }

    def _display_api_call_estimate(self) -> None:
        """Display estimated API calls before confirmation."""
        estimate = self._estimate_api_calls()

        print("\n  API Call Estimate:")
        print("  " + "-" * 50)
        print(f"   Upgrade API calls: {estimate['upgrade_calls']}")
        print(f"   Sites to process: {estimate['site_count']}")

        if estimate["site_count"] > 1 or estimate["upgrade_calls"] > 1:
            print("\n   Breakdown by site:")
            for item in estimate["breakdown"][:10]:
                print(
                    f"     - {item['site_name']}: {item['calls']} call(s)"
                    f" ({item['reason']}, {item['devices']} devices)"
                )
            if len(estimate["breakdown"]) > 10:
                remaining = len(estimate["breakdown"]) - 10
                remaining_calls = sum(b["calls"] for b in estimate["breakdown"][10:])
                print(f"     ... and {remaining} more sites" f" ({remaining_calls} additional calls)")

        print("  " + "-" * 50)

        if estimate["auto_upgrade_calls"] > 0:
            print(
                f"   Note: If you configure auto-upgrade (Step 9),"
                f" add {estimate['auto_upgrade_calls']} more call(s)"
            )

    def _display_multi_site_summary(self) -> None:
        """Display comprehensive summary for multi-site upgrades."""
        print("\n  Sites with APs to Upgrade:")
        print("  " + "=" * 70)

        site_summary: dict[str, dict[str, Any]] = {}
        for model, plan in self.upgrade_plan.items():
            target_version = plan["version"]
            for device in plan["devices"]:
                site_name = device.get("_site_name", "Unknown")
                if site_name not in site_summary:
                    site_summary[site_name] = {
                        "models": {},
                        "total": 0,
                        "version": target_version,
                    }
                if model not in site_summary[site_name]["models"]:
                    site_summary[site_name]["models"][model] = 0
                site_summary[site_name]["models"][model] += 1
                site_summary[site_name]["total"] += 1

        for site_name in sorted(site_summary.keys()):
            info = site_summary[site_name]
            model_str = ", ".join(f"{m}:{c}" for m, c in sorted(info["models"].items()))
            print(f"   {site_name}: {info['total']} APs ({model_str})")

        print("  " + "=" * 70)
        total_aps = sum(s["total"] for s in site_summary.values())
        print(f"   Total: {len(site_summary)} sites, {total_aps} APs")
        if self.skipped_already_at_target > 0:
            print(f"   Skipped: {self.skipped_already_at_target}" " APs already at target version")

    def _display_upgrade_warnings(self) -> None:
        """Display critical upgrade warnings."""
        print("\n" + "??" * 50)
        if self.dry_run:
            print(" DRY-RUN MODE - NO ACTUAL CHANGES WILL BE MADE")
            print("??" * 50)
            print(" This will simulate the firmware upgrade workflow:")
        else:
            print(" CRITICAL WARNING - ADVANCED FIRMWARE UPGRADE:")
        print("!? APs will REBOOT during upgrade")
        print("!? Wi-Fi connectivity will be TEMPORARILY LOST")
        print("!? Upgrades take 5-15 minutes per device")
        print(f"!? Download Strategy:" f" {self.upgrade_config['download_strategy'].upper()}")
        print(f"!? Reboot Strategy:" f" {self.upgrade_config['reboot_strategy'].upper()}")
        print("??" * 50)

    def _display_final_plan(self) -> None:
        """Display final upgrade plan."""
        print("\n  Final Plan:")
        if len(self.sites_to_upgrade) > 1:
            print(f"   Bulk upgrade: {len(self.sites_to_upgrade)} sites")
        for model, plan in self.upgrade_plan.items():
            print(f"   {model}: {len(plan['devices'])} devices" f" firmware {plan['version']}")

    def _get_upgrade_confirmation(self, total: int) -> bool:
        """Get user confirmation for upgrade."""
        sites_count = len(set(d.get("_site_id") for p in self.upgrade_plan.values() for d in p["devices"]))

        if sites_count > 1:
            print(f"\n  Type 'UPGRADE' to confirm upgrading {total}" f" devices across {sites_count} sites:")
        else:
            print(f"\n  Type 'UPGRADE' to confirm upgrading {total} devices:")

        try:
            confirm = self._input_fn(">>> ").strip()
            if confirm != "UPGRADE":
                print(" Upgrade cancelled.")
                return False
            print(" User confirmed. Proceeding...")
            logging.info(f"User confirmed upgrade for {total} devices" f" across {sites_count} sites")
            return True
        except (KeyboardInterrupt, EOFError):
            return False

    # =========================================================================
    # STEP 8: EXECUTE UPGRADES
    # =========================================================================

    def _step8_execute_upgrades(self) -> None:
        """Execute firmware upgrades across all sites."""
        import mistapi

        print("\n  Starting firmware upgrade operations...")
        print("=" * 60)

        devices_by_site = self._organize_devices_by_site()
        sites_with_upgrades = {sid: data for sid, data in devices_by_site.items() if data["devices"]}
        skipped = len(devices_by_site) - len(sites_with_upgrades)

        if skipped > 0:
            print(f"   Skipping {skipped} site(s) with no devices needing upgrade")

        if not sites_with_upgrades:
            print("   No sites have devices needing upgrade - nothing to do")
            return

        for idx, (site_id, site_data) in enumerate(sites_with_upgrades.items(), 1):
            self._execute_site_upgrade(idx, len(sites_with_upgrades), site_id, site_data, mistapi)

    def _organize_devices_by_site(self) -> dict[str, dict[str, Any]]:
        """Organize upgrade plan devices by site."""
        devices_by_site: dict[str, dict[str, Any]] = {}
        for model, plan in self.upgrade_plan.items():
            for device in plan["devices"]:
                site_id = device.get("_site_id")
                site_name = device.get("_site_name")
                if site_id not in devices_by_site:
                    devices_by_site[site_id] = {
                        "name": site_name,
                        "devices": [],
                        "models": {},
                    }
                devices_by_site[site_id]["devices"].append(device)
                if model not in devices_by_site[site_id]["models"]:
                    devices_by_site[site_id]["models"][model] = {
                        "version": plan["version"],
                        "devices": [],
                    }
                devices_by_site[site_id]["models"][model]["devices"].append(device)
        return devices_by_site

    def _execute_site_upgrade(
        self,
        index: int,
        total: int,
        site_id: str,
        site_data: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Execute upgrade for a single site."""
        site_name = site_data["name"]
        print(f"\n   Site {index}/{total}: {site_name}" f" ({len(site_data['devices'])} devices)")

        try:
            versions = set(m["version"] for m in site_data["models"].values())
            if len(versions) == 1:
                self._execute_single_version_upgrade(site_id, site_name, site_data, mistapi)
            else:
                self._execute_multi_version_upgrade(site_id, site_name, site_data, mistapi)
            self._log_upgrade_results(site_id, site_name, site_data, "Upgrade Initiated")
        except Exception as error:
            print(f"      Failed: {error}")
            self.failed_upgrades += len(site_data["devices"])
            self._log_upgrade_results(site_id, site_name, site_data, f"ERROR: {error}")

    def _execute_single_version_upgrade(
        self,
        site_id: str,
        site_name: str,
        site_data: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Execute upgrade when all devices use same version."""
        version = list(site_data["models"].values())[0]["version"]
        device_ids = [d.get("id") for d in site_data["devices"] if d.get("id")]
        body = self._build_upgrade_body(version, device_ids)

        if self.dry_run:
            print(f"      [DRY-RUN] Would upgrade {len(device_ids)}" f" devices to {version}")
            logging.info(
                f"DRY-RUN: Would call upgradeSiteDevices for site" f" {site_name} with {len(device_ids)} devices"
            )
            self.successful_upgrades += len(site_data["devices"])
            return

        resp = mistapi.api.v1.sites.devices.upgradeSiteDevices(self.apisession, site_id, body=body)

        if hasattr(resp, "data") and resp.data and isinstance(resp.data, dict):
            upgrade_id = resp.data.get("upgrade_id")
            if upgrade_id:
                self.upgrade_ids.append(upgrade_id)
                print(f"      Upgrade initiated - ID: {upgrade_id}")

        self.successful_upgrades += len(site_data["devices"])

    def _execute_multi_version_upgrade(
        self,
        site_id: str,
        site_name: str,
        site_data: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Execute upgrade when devices use different versions."""
        print("      Multiple versions - grouping by target version...")

        devices_by_version: dict[str, dict[str, Any]] = {}
        for model, model_info in site_data["models"].items():
            version = model_info["version"]
            if version not in devices_by_version:
                devices_by_version[version] = {"devices": [], "models": []}
            devices_by_version[version]["devices"].extend(model_info["devices"])
            devices_by_version[version]["models"].append(model)

        for version, version_info in devices_by_version.items():
            self._upgrade_version_group(site_id, site_name, version, version_info, mistapi)

    def _upgrade_version_group(
        self,
        site_id: str,
        site_name: str,
        version: str,
        version_info: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Upgrade a group of devices sharing the same target version."""
        devices = version_info["devices"]
        models = version_info["models"]
        device_ids = [d.get("id") for d in devices if d.get("id")]
        models_str = ", ".join(models)
        body = self._build_upgrade_body(version, device_ids)

        if self.dry_run:
            print(f"         [DRY-RUN] {version}: Would upgrade" f" {len(devices)} devices ({models_str})")
            logging.info(
                f"DRY-RUN: Would call upgradeSiteDevices for version"
                f" {version} at {site_name} with {len(device_ids)} devices"
            )
            self.successful_upgrades += len(devices)
            return

        resp = mistapi.api.v1.sites.devices.upgradeSiteDevices(self.apisession, site_id, body=body)

        if hasattr(resp, "data") and resp.data and isinstance(resp.data, dict):
            if "upgrade_id" in resp.data:
                self.upgrade_ids.append(resp.data["upgrade_id"])

        self.successful_upgrades += len(devices)
        print(f"         + {version}: {len(devices)} devices ({models_str})")

    def _build_upgrade_body(self, version: str, device_ids: list[str | None]) -> dict[str, Any]:
        """Build upgrade API request body."""
        body: dict[str, Any] = {
            "download_strategy": self.upgrade_config["download_strategy"],
            "reboot_strategy": self.upgrade_config["reboot_strategy"],
            "force": self.upgrade_config["force"],
            "enable_p2p": self.upgrade_config["enable_p2p"],
            "max_failure_percentage": self.upgrade_config["max_failure_percentage"],
            "reboot": self.upgrade_config["reboot"],
            "version": version,
            "device_ids": device_ids,
        }
        if self.upgrade_config["enable_p2p"]:
            body["p2p_cluster_size"] = self.upgrade_config["p2p_cluster_size"]
        if self.upgrade_config["download_strategy"] == "canary" or self.upgrade_config["reboot_strategy"] == "canary":
            body["canary_phases"] = self.upgrade_config["canary_phases"]
        if self.upgrade_config["reboot_strategy"] == "rrm":
            for key in [
                "rrm_node_order",
                "rrm_first_batch_percentage",
                "rrm_max_batch_percentage",
            ]:
                if key in self.upgrade_config:
                    body[key] = self.upgrade_config[key]
        if self.upgrade_config.get("start_time"):
            body["start_time"] = self.upgrade_config["start_time"]
        return body

    def _log_upgrade_results(
        self,
        site_id: str,
        site_name: str,
        site_data: dict[str, Any],
        status: str,
    ) -> None:
        """Log upgrade results for each device."""
        effective_status = f"DRY-RUN: {status}" if self.dry_run else status

        for device in site_data["devices"]:
            target = self._get_device_target_version(device)
            self.results.append(
                {
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Device ID": device.get("id", "Unknown"),
                    "Device Name": device.get("name", "Unnamed"),
                    "Device MAC": device.get("mac", "Unknown"),
                    "Model": device.get("model", "Unknown"),
                    "Current Version": self.ap_versions.get(device.get("id"), "Unknown"),
                    "Target Version": target,
                    "Download Strategy": self.upgrade_config["download_strategy"],
                    "Reboot Strategy": self.upgrade_config["reboot_strategy"],
                    "P2P Enabled": self.upgrade_config["enable_p2p"],
                    "Max Failure %": self.upgrade_config["max_failure_percentage"],
                    "Force Upgrade": self.upgrade_config["force"],
                    "Upgrade ID": (
                        self.upgrade_ids[-1] if self.upgrade_ids else ("N/A (DRY-RUN)" if self.dry_run else "N/A")
                    ),
                    "Status": effective_status,
                    "Timestamp": datetime.now(UTC).isoformat(),
                }
            )

    def _get_device_target_version(self, device: dict[str, Any]) -> str:
        """Get target version for a device."""
        for _model, plan in self.upgrade_plan.items():
            if device in plan["devices"]:
                target: str = str(plan["version"])
                return target
        return "Unknown"

    # =========================================================================
    # STEP 9: AUTO-UPGRADE CONFIGURATION
    # =========================================================================

    def _fetch_ap_model_families(self) -> dict[str, list[str]]:
        """Fetch AP model families from the Mist const/device_models API.

        Groups AP models by their ap_type (hardware chipset/generation).
        Returns dict mapping ap_type to list of model names.
        """
        print("   Fetching AP model definitions from Mist API...")

        try:
            device_models_module = importlib.import_module("mistapi.api.v1.const.device_models")
            list_device_models = device_models_module.listDeviceModels
            response = list_device_models(self.apisession)

            all_models = getattr(response, "data", response) or []

            ap_type_to_models: dict[str, list[str]] = {}
            for model_info in all_models:
                if not isinstance(model_info, dict):
                    continue
                if model_info.get("type") != "ap":
                    continue
                model_name = model_info.get("model", "")
                ap_type = model_info.get("ap_type", "unknown")
                if not model_name:
                    continue
                if ap_type not in ap_type_to_models:
                    ap_type_to_models[ap_type] = []
                ap_type_to_models[ap_type].append(model_name)

            families = {}
            for ap_type, models in sorted(ap_type_to_models.items()):
                families[ap_type] = sorted(models)

            logging.info(
                f"Fetched {len(families)} AP families with" f" {sum(len(m) for m in families.values())} total models"
            )
            return families

        except Exception as error:
            logging.warning(f"Failed to fetch AP model families from API: {error}")
            print("   Warning: Could not fetch AP models from API")
            return {}

    def _step9_configure_auto_upgrade(self) -> None:
        """Configure site auto-upgrade settings for ALL selected sites."""
        if not self.sites_to_upgrade:
            return

        print("\n  Site Auto-Upgrade Configuration")
        print("=" * 60)
        print(f"   This will configure auto-upgrade for" f" {len(self.sites_to_upgrade)} site(s)")
        print("   Auto-upgrade ensures new APs automatically upgrade" " to target firmware")

        try:
            prompt = self._input_fn("\n  Configure site auto-upgrade? (Y/n): ").strip().lower()
            if prompt in ["n", "no"]:
                print("   Skipping auto-upgrade configuration")
                return
        except (EOFError, KeyboardInterrupt):
            return

        custom_versions = {model: plan["version"] for model, plan in self.upgrade_plan.items()}
        custom_versions = self._offer_additional_model_versions(custom_versions)
        schedule_config = self._configure_auto_upgrade_schedule()
        self._apply_auto_upgrade_to_all_sites(custom_versions, schedule_config)

    def _offer_additional_model_versions(self, custom_versions: dict[str, str]) -> dict[str, str]:
        """Offer to configure firmware versions for models not at sites."""
        print("\n  Additional Model Configuration")
        print("-" * 60)
        print(f"   Current upgrade targets: {len(custom_versions)} model(s)")
        for model, version in sorted(custom_versions.items()):
            print(f"      {model}: {version}")

        try:
            add_more = self._input_fn("\n  Add firmware versions for other AP models? (y/N): ").strip().lower()
            if add_more not in ["y", "yes"]:
                return custom_versions
        except (EOFError, KeyboardInterrupt):
            return custom_versions

        ap_families = self._fetch_ap_model_families()
        if not ap_families:
            print("   Could not fetch AP model families from API")
            return custom_versions

        print("\n  AP Model Families (select by family to set ONE version" " for all models in that family):")
        print("-" * 60)

        family_list = list(ap_families.items())
        for idx, (ap_type, models) in enumerate(family_list, 1):
            models_str = ", ".join(models)
            print(f"   [{idx}] {ap_type}: {models_str}")

        print("\n  Options:")
        print("   - Enter family numbers (e.g., '1,3,5')" " - you will select ONE version per family")
        print("   - Enter 'all' to configure all AP model families")
        print("   - Press Enter to skip")

        try:
            selection = self._input_fn("\n  Selection: ").strip()
            if not selection:
                return custom_versions
        except (EOFError, KeyboardInterrupt):
            return custom_versions

        selected_families = self._parse_family_selection(selection, family_list)
        if not selected_families:
            print("   No families selected")
            return custom_versions

        return self._select_versions_by_family(custom_versions, selected_families)

    def _parse_family_selection(self, selection: str, family_list: list[tuple[str, list[str]]]) -> dict[str, list[str]]:
        """Parse user selection into dict of {ap_type: [models]}."""
        if selection.lower() == "all":
            return dict(family_list)

        selected: dict[str, list[str]] = {}
        parts = [p.strip() for p in selection.split(",")]
        for part in parts:
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(family_list):
                    ap_type, models = family_list[idx]
                    selected[ap_type] = models
        return selected

    def _select_versions_by_family(
        self,
        custom_versions: dict[str, str],
        selected_families: dict[str, list[str]],
    ) -> dict[str, str]:
        """Select ONE firmware version per family."""
        print("\n  Selecting firmware versions by family")
        print("  (One version selection applies to ALL models in each family)")
        print("-" * 60)

        for ap_type, models in selected_families.items():
            new_models = [m for m in models if m not in custom_versions]
            self._select_version_for_family(ap_type, new_models, custom_versions)

        return custom_versions

    def _select_version_for_family(
        self,
        ap_type: str,
        new_models: list[str],
        custom_versions: dict[str, str],
    ) -> None:
        """Prompt user to select a firmware version for one AP family."""
        if not new_models:
            print(f"\n   {ap_type}: All models already configured - skipping")
            return

        print(f"\n   Family: {ap_type}")
        print(f"   Models: {', '.join(new_models)}")

        universal = self._find_universal_versions_for_models(set(new_models))
        if not universal:
            print(f"   ! No universal version found for all models" f" in {ap_type}")
            return

        sorted_versions = sorted(universal, key=self._version_sort_key, reverse=True)[:10]

        print(f"   Available versions" f" (compatible with ALL {len(new_models)} models):")
        for idx, version in enumerate(sorted_versions, 1):
            print(f"      [{idx}] {version}")

        self._apply_family_version_choice(ap_type, new_models, sorted_versions, custom_versions)

    def _apply_family_version_choice(
        self,
        ap_type: str,
        new_models: list[str],
        sorted_versions: list[str],
        custom_versions: dict[str, str],
    ) -> None:
        """Handle user input for family version selection."""
        try:
            choice = (
                self._input_fn(f"\n   Select version for {ap_type}" f" (1-{len(sorted_versions)}), 's' to skip: ")
                .strip()
                .lower()
            )
            if choice == "s":
                print(f"   Skipped {ap_type}")
                return
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(sorted_versions):
                    selected_version = sorted_versions[idx]
                    for model in new_models:
                        custom_versions[model] = selected_version
                    print(f"   -> Applied {selected_version}" f" to: {', '.join(new_models)}")
        except (EOFError, KeyboardInterrupt, ValueError):
            pass

    def _find_universal_versions_for_models(self, models: set[str]) -> list[str]:
        """Find firmware versions compatible with all specified models."""
        version_to_compatible: dict[str, set[str]] = {}

        for version_info in self.available_versions:
            if not isinstance(version_info, dict):
                continue
            version = version_info.get("version", "")
            if not version:
                continue

            entry_models = set(version_info.get("models", []))
            if version_info.get("model"):
                entry_models.add(version_info.get("model"))

            if version not in version_to_compatible:
                version_to_compatible[version] = set()
            version_to_compatible[version].update(entry_models)

        return list({v for v, compatible in version_to_compatible.items() if models.issubset(compatible)})

    def _version_sort_key(self, version_string: str) -> list[int | str]:
        """Create sort key for semantic version ordering."""
        try:
            parts: list[int | str] = []
            for part in version_string.split("."):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(part.lower())
            return parts
        except Exception:
            return [version_string.lower()]

    def _configure_auto_upgrade_schedule(self) -> dict[str, str]:
        """Configure auto-upgrade scheduling options."""
        schedule: dict[str, str] = {}

        print("\n  Auto-Upgrade Scheduling")
        print("-" * 60)
        print("   Configure when auto-upgrades should occur")

        days = ["any", "mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        print("\n  Day of week options:")
        print("   [0] any (default)")
        for idx, day in enumerate(days[1:], 1):
            print(f"   [{idx}] {day}")

        try:
            day_choice = self._input_fn("\n  Select day (0-7, default=0 any): ").strip() or "0"
            if day_choice.isdigit() and 0 <= int(day_choice) < len(days):
                schedule["day_of_week"] = days[int(day_choice)]
            else:
                schedule["day_of_week"] = "any"
        except (EOFError, KeyboardInterrupt, ValueError):
            schedule["day_of_week"] = "any"

        print("\n  Time of day (24-hour format HH:MM, or 'any'):")
        print("   Examples: 02:00 (2 AM), 14:00 (2 PM), any")

        try:
            time_input = self._input_fn("   Enter time (default=any): ").strip() or "any"
            if time_input.lower() == "any":
                schedule["time_of_day"] = "any"
            elif ":" in time_input:
                schedule["time_of_day"] = time_input
            else:
                schedule["time_of_day"] = "any"
        except (EOFError, KeyboardInterrupt):
            schedule["time_of_day"] = "any"

        return schedule

    def _apply_auto_upgrade_to_all_sites(self, custom_versions: dict[str, str], schedule: dict[str, str]) -> None:
        """Apply auto-upgrade configuration to ALL selected sites."""
        import mistapi

        print(f"\n  Applying Auto-Upgrade to" f" {len(self.sites_to_upgrade)} Site(s)")
        print("=" * 60)

        settings = {"auto_upgrade": self._build_auto_upgrade_settings(custom_versions, schedule)}

        successful, failed = self._apply_settings_to_sites(settings, mistapi)

        self._print_auto_upgrade_summary(successful, failed, custom_versions, schedule)

    def _build_auto_upgrade_settings(self, custom_versions: dict[str, str], schedule: dict[str, str]) -> dict[str, Any]:
        """Build auto-upgrade settings payload."""
        auto_upgrade: dict[str, Any] = {
            "enabled": True,
            "version": "custom",
            "custom_versions": custom_versions,
        }

        if schedule.get("day_of_week") and schedule["day_of_week"] != "any":
            auto_upgrade["day_of_week"] = schedule["day_of_week"]
        if schedule.get("time_of_day") and schedule["time_of_day"] != "any":
            auto_upgrade["time_of_day"] = schedule["time_of_day"]

        return auto_upgrade

    def _apply_settings_to_sites(self, settings: dict[str, Any], mistapi: Any) -> tuple[int, int]:
        """Apply settings to each site, returning (successful, failed) counts."""
        successful = 0
        failed = 0

        for site in self.sites_to_upgrade:
            if self._check_stop_fn and self._check_stop_fn():
                break
            site_id = site["id"]
            site_name = site["name"]

            try:
                mistapi.api.v1.sites.setting.updateSiteSettings(self.apisession, site_id, body=settings)
                print(f"   [OK] {site_name}")
                successful += 1
            except Exception as error:
                print(f"   [FAIL] {site_name}: {error}")
                logging.error(f"Failed to configure auto-upgrade for site" f" {site_name}: {error}")
                failed += 1

        return successful, failed

    def _print_auto_upgrade_summary(
        self,
        successful: int,
        failed: int,
        custom_versions: dict[str, str],
        schedule: dict[str, str],
    ) -> None:
        """Print auto-upgrade configuration summary."""
        print("\n  Auto-Upgrade Configuration Complete:")
        print(f"   Successful: {successful} site(s)")
        if failed > 0:
            print(f"   Failed: {failed} site(s)")
        print(f"   Models configured: {len(custom_versions)}")
        for model, version in sorted(custom_versions.items()):
            print(f"      {model}: {version}")
        if schedule.get("day_of_week") != "any" or schedule.get("time_of_day") != "any":
            print(f"   Schedule: {schedule.get('day_of_week', 'any')}" f" at {schedule.get('time_of_day', 'any')}")

    # =========================================================================
    # STEP 10: STATUS CHECK
    # =========================================================================

    def _step10_offer_status_check(self) -> None:
        """Offer to check upgrade status."""
        if self.successful_upgrades == 0:
            return

        print("\n Firmware upgrades initiated successfully!")
        print(f"   {self.successful_upgrades} upgrades started")

        self._save_upgrade_tracking()

        print("\n Reminder: Monitor progress using menu option 60")
        try:
            check = self._input_fn("\n Check upgrade status now? (y/n): ").strip().lower()
            if check in ["y", "yes"] and self._check_firmware_status_fn:
                self._check_firmware_status_fn()
        except (EOFError, KeyboardInterrupt):
            pass

    def _save_upgrade_tracking(self) -> None:
        """Save upgrade IDs for tracking."""
        if not self.upgrade_ids:
            return
        try:
            tracking_file = "ActiveUpgrades.json"
            tracking_data = []
            if os.path.exists(tracking_file):
                with open(tracking_file, encoding="utf-8") as f:
                    tracking_data = json.load(f)

            for upgrade_id in self.upgrade_ids:
                tracking_data.append(
                    {
                        "upgrade_id": upgrade_id,
                        "org_id": self.org_id,
                        "download_strategy": self.upgrade_config.get("download_strategy", ""),
                        "reboot_strategy": self.upgrade_config.get("reboot_strategy", ""),
                        "timestamp": datetime.now(UTC).isoformat(),
                        "status": "initiated",
                    }
                )

            with open(tracking_file, "w", encoding="utf-8") as f:
                json.dump(tracking_data, f, indent=2)
        except Exception as error:
            logging.warning(f"Failed to save tracking: {error}")

    # =========================================================================
    # STEP 11: WRITE RESULTS
    # =========================================================================

    def _step11_write_results(self) -> None:
        """Write upgrade results to CSV."""
        if not self.results:
            return

        site_name = self.sites_to_upgrade[0]["name"] if self.sites_to_upgrade else "Unknown"
        dry_run_suffix = "_DRYRUN" if self.dry_run else ""
        filename = os.path.join(
            "data",
            f"AdvancedAPFirmwareUpgrade_{site_name.replace(' ', '_')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f"{dry_run_suffix}.csv",
        )

        try:
            fieldnames = [
                "Site ID",
                "Site Name",
                "Device ID",
                "Device Name",
                "Device MAC",
                "Model",
                "Current Version",
                "Target Version",
                "Download Strategy",
                "Reboot Strategy",
                "P2P Enabled",
                "Max Failure %",
                "Force Upgrade",
                "Upgrade ID",
                "Status",
                "Timestamp",
            ]

            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)

            if self.dry_run:
                print("\n  DRY-RUN Complete - No actual upgrades performed!")
                print(f"   Would have upgraded:" f" {self.successful_upgrades} devices")
            else:
                print("\n  Advanced Firmware Upgrade Completed!")
                print(f"   Successful: {self.successful_upgrades}")
                print(f"   Failed: {self.failed_upgrades}")
            print(f"   Results: {filename}")
            logging.info(f"Upgrade results written to {filename}")
        except Exception as error:
            print(f"! Failed to write results: {error}")
