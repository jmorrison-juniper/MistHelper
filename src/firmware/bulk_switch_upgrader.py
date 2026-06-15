"""Bulk switch firmware upgrade operations for Mist organizations.

Executes firmware upgrades on switches across selected sites with safety
checks, multiple upgrade strategies, and comprehensive progress tracking.

Extracted from MistHelper.py for maintainability.
"""


from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from typing import Any

from MistHelper import mistapi, safe_input

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
SafeInputFn = type[None]  # Placeholder, redefined below


class BulkSwitchFirmwareUpgrader:
    """Execute firmware upgrades on switches across selected sites.

    Supports multiple upgrade strategies (big_bang, serial, canary) with
    comprehensive progress tracking, firmware caching, and model
    compatibility validation.

    NETWORK IMPACT WARNING:
    - Switch reboots will disrupt network connectivity
    - Plan maintenance windows for production environments
    - Verify backup connectivity paths before execution
    """

    # Cache settings
    CACHE_FILE = os.path.join("data", "cached_org_devices_versions_switch.csv")
    CACHE_FRESHNESS_HOURS = 24

    def __init__(
        self,
        org_id: str,
        apisession: Any,
        safe_input_fn: Any,
        sites_override: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the switch firmware upgrader.

        Args:
            org_id: Organization ID.
            apisession: Authenticated Mist API session.
            safe_input_fn: Callable for safe user input collection.
            sites_override: Optional site list for template-based upgrades.
        """
        self.org_id = org_id
        self.apisession = apisession
        self.safe_input_fn = safe_input_fn
        self.sites_override = sites_override
        self.logger = logging.getLogger(__name__)

        # State variables initialized during execution
        self.org_name: str = ""
        self.selected_sites: list[dict[str, Any]] = []
        self.switch_models: set[str] = set()
        self.current_firmware_versions: set[str] = set()
        self.available_versions: list[str] = []
        self.compatible_versions: dict[str, set[str]] = {}
        self.target_version: str = ""

        # Upgrade parameters
        self.upgrade_strategy: str = ""
        self.force_upgrade: bool = False
        self.auto_reboot: bool = True
        self.take_snapshot: bool = True

        # Results tracking
        self.upgrade_results: dict[str, Any] = {}

    # --------------------------------------------------------------------- #
    # Public entry point
    # --------------------------------------------------------------------- #

    def execute(self) -> dict[str, Any]:
        """Orchestrate the complete upgrade workflow.

        Returns:
            Dict with upgrade operation results and status information.
        """
        self.logger.debug(
            "Starting bulk switch firmware upgrade - org_id: %s",
            self.org_id,
        )

        if not self._validate_organization():
            return {"error": "Organization validation failed"}

        site_result = self._select_sites()
        if site_result:
            return site_result

        if not self._configure_upgrade_parameters():
            return {"cancelled": True}

        firmware_result = self._discover_and_select_firmware()
        if firmware_result:
            return firmware_result

        if not self._confirm_upgrade():
            return {"cancelled": True}

        return self._execute_upgrades()

    # --------------------------------------------------------------------- #
    # Step 1: Organization Validation
    # --------------------------------------------------------------------- #

    def _validate_organization(self) -> bool:
        """Validate organization access and retrieve org name."""
        import mistapi

        print("\n-> Validating organization access...")
        try:
            org_info = mistapi.api.v1.orgs.orgs.getOrg(self.apisession, self.org_id)
            if org_info.status_code != 200:
                print(f"X  Error accessing organization: {org_info.status_code}")
                self.logger.error(
                    "Failed to access organization %s: %s",
                    self.org_id,
                    org_info.status_code,
                )
                return False

            self.org_name = org_info.data.get("name", "Unknown")
            print(f"!? Organization: {self.org_name}")
            self.logger.debug("Organization validated: %s", self.org_name)
            return True

        except Exception as exc:
            print(f"X  Error validating organization: {exc}")
            self.logger.error("Organization validation failed: %s", exc)
            return False

    # --------------------------------------------------------------------- #
    # Step 2: Site Selection
    # --------------------------------------------------------------------- #

    def _select_sites(self) -> dict[str, Any] | None:
        """Select sites for upgrade.

        Returns:
            ``None`` on success, error dict on failure.
        """
        if self.sites_override:
            return self._use_override_sites()
        return self._interactive_site_selection()

    def _use_override_sites(self) -> dict[str, Any] | None:
        """Use provided site list from template-based upgrade."""
        self.selected_sites = self.sites_override if self.sites_override else []
        print(f"-> Using provided site list: {len(self.selected_sites)} sites")
        return None

    def _interactive_site_selection(self) -> dict[str, Any] | None:
        """Interactive site selection with discovery."""
        import mistapi

        print("\n-> Discovering available sites...")
        try:
            sites_response = mistapi.api.v1.orgs.sites.listOrgSites(self.apisession, self.org_id)
            if sites_response.status_code != 200:
                print(f"X  Error retrieving sites: {sites_response.status_code}")
                return {"error": "Failed to retrieve sites"}

            all_sites = sites_response.data
            print(f"!? Found {len(all_sites)} total sites")
            return self._prompt_site_selection(all_sites)

        except Exception as exc:
            print(f"X  Error during site discovery: {exc}")
            self.logger.error("Site discovery failed: %s", exc)
            return {"error": f"Site discovery error: {exc}"}

    def _prompt_site_selection(self, all_sites: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Display site list and get user selection."""
        self._display_site_list(all_sites)

        print("\nSite selection options:")
        print("A. All sites")
        print("S. Select specific sites")
        print("C. Cancel operation")

        site_choice = input("\nEnter your choice (A/S/C): ").strip().upper()

        if site_choice == "C":
            print("-> Operation cancelled by user")
            return {"cancelled": True}
        if site_choice == "A":
            self.selected_sites = all_sites
            print(f"-> Selected all {len(self.selected_sites)} sites")
        elif site_choice == "S":
            return self._parse_specific_sites(all_sites)
        else:
            print("X  Invalid selection")
            return {"error": "Invalid selection"}

        if not self.selected_sites:
            print("X  No sites selected")
            return {"error": "No sites selected"}

        return None

    @staticmethod
    def _display_site_list(sites: list[dict[str, Any]]) -> None:
        """Display numbered list of available sites."""
        print("\nAvailable sites:")
        for index, site in enumerate(sites, 1):
            site_name = site.get("name", "Unnamed")
            site_id = site.get("id", "Unknown")
            print(f"{index:3}. {site_name} (ID: {site_id})")

    def _parse_specific_sites(self, all_sites: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Parse user input for specific site selection."""
        print("\nEnter site numbers (comma-separated) or ranges (e.g., 1-5):")
        site_input = input("Sites: ").strip()

        try:
            self.selected_sites = []
            for part in site_input.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    for device_index in range(start - 1, end):
                        if 0 <= device_index < len(all_sites):
                            self.selected_sites.append(all_sites[device_index])
                else:
                    index = int(part) - 1
                    if 0 <= index < len(all_sites):
                        self.selected_sites.append(all_sites[index])

            print(f"-> Selected {len(self.selected_sites)} sites")

            if not self.selected_sites:
                print("X  No valid sites selected")
                return {"error": "No valid sites selected"}

            return None

        except Exception as exc:
            print(f"X  Invalid site selection: {exc}")
            return {"error": "Invalid site selection"}

    # --------------------------------------------------------------------- #
    # Step 3: Upgrade Parameters Configuration
    # --------------------------------------------------------------------- #

    def _configure_upgrade_parameters(self) -> bool:
        """Configure all upgrade parameters interactively."""
        print(f"\n{'=' * 60}")
        print("SWITCH FIRMWARE UPGRADE PARAMETER CONFIGURATION")
        print(f"{'=' * 60}")

        self._select_strategy()
        self._select_force_option()
        self._select_reboot_option()
        self._select_snapshot_option()

        return True

    def _select_strategy(self) -> None:
        """Select upgrade strategy (big_bang, serial, canary)."""
        print("\nUpgrade Strategy Options:")
        print("1. big_bang    - Upgrade all switches simultaneously (fastest)")
        print("2. serial      - Upgrade switches one by one (safest)")
        print("3. canary      - Test subset first, then upgrade remaining")

        while True:
            strategy_choice = input("\nSelect upgrade strategy (1-3): ").strip()
            if strategy_choice == "1":
                self.upgrade_strategy = "big_bang"
                break
            if strategy_choice == "2":
                self.upgrade_strategy = "serial"
                break
            if strategy_choice == "3":
                self.upgrade_strategy = "canary"
                break
            print("X  Please enter 1, 2, or 3")

        print(f"-> Selected strategy: {self.upgrade_strategy}")

    def _select_force_option(self) -> None:
        """Select force upgrade option."""
        print("\nForce Upgrade Options:")
        print("1. Yes - Force upgrade even if same version (recommended for testing)")
        print("2. No  - Skip devices already on target version (recommended for production)")

        while True:
            force_choice = input("\nForce upgrade? (1-2): ").strip()
            if force_choice == "1":
                self.force_upgrade = True
                break
            if force_choice == "2":
                self.force_upgrade = False
                break
            print("X  Please enter 1 or 2")

        label = "Yes" if self.force_upgrade else "No"
        print(f"-> Force upgrade: {label}")

    def _select_reboot_option(self) -> None:
        """Select auto-reboot option."""
        print("\nReboot Options:")
        print("1. Yes - Reboot after upgrade (required for switches - recommended)")
        print("2. No  - No reboot (not recommended for switches)")

        while True:
            reboot_choice = input("\nReboot after upgrade? (1-2): ").strip()
            if reboot_choice == "1":
                self.auto_reboot = True
                break
            if reboot_choice == "2":
                self.auto_reboot = False
                print("!? WARNING: Switches typically require reboot to complete firmware upgrade")
                break
            print("X  Please enter 1 or 2")

        label = "Yes" if self.auto_reboot else "No"
        print(f"-> Auto reboot: {label}")

    def _select_snapshot_option(self) -> None:
        """Select recovery snapshot option (Junos specific)."""
        print("\nRecovery Snapshot Options (Junos devices only):")
        print("1. Yes - Take recovery snapshot after device reboots (recommended for Junos)")
        print("2. No  - Skip recovery snapshot (faster but no post-upgrade backup)")

        while True:
            snapshot_choice = input("\nTake recovery snapshot after reboot? (1-2): ").strip()
            if snapshot_choice == "1":
                self.take_snapshot = True
                break
            if snapshot_choice == "2":
                self.take_snapshot = False
                break
            print("X  Please enter 1 or 2")

        label = "Yes" if self.take_snapshot else "No"
        print(f"-> Recovery snapshot after reboot: {label}")

    # --------------------------------------------------------------------- #
    # Step 4: Firmware Discovery and Selection
    # --------------------------------------------------------------------- #

    def _discover_and_select_firmware(self) -> dict[str, Any] | None:
        """Discover available firmware and get user selection.

        Returns:
            ``None`` on success, error dict on failure.
        """
        print(f"\n{'=' * 60}")
        print("FIRMWARE VERSION SELECTION")
        print(f"{'=' * 60}")

        if not self._fetch_switch_inventory():
            return {"error": "Failed to retrieve switch inventory"}

        firmware_data = self._load_firmware_data()
        if not firmware_data:
            return {"error": "No firmware data available"}

        self._process_firmware_data(firmware_data)
        return self._get_version_selection()

    def _fetch_switch_inventory(self) -> bool:
        """Fetch switch inventory to determine current firmware and models."""
        import mistapi

        print("\n-> Discovering available switch firmware versions...")
        try:
            switches_response = mistapi.api.v1.orgs.inventory.getOrgInventory(
                self.apisession, self.org_id, type="switch"
            )

            if switches_response.status_code != 200:
                print(f"X  Error retrieving switch inventory: {switches_response.status_code}")
                return False

            switches = switches_response.data
            if not switches:
                print("X  No switches found in organization")
                return False

            print(f"!? Found {len(switches)} switches")

            for switch in switches:
                if switch.get("version"):
                    self.current_firmware_versions.add(switch.get("version"))
                if switch.get("model"):
                    self.switch_models.add(switch.get("model"))

            print(f"-> Switch models found: {', '.join(sorted(self.switch_models))}")
            print(f"-> Current firmware versions: {', '.join(sorted(self.current_firmware_versions))}")

            if not self.switch_models:
                print("!? WARNING: No switch models detected - firmware filtering may not work properly")
                self.logger.warning("No switch models found in inventory")

            return True

        except Exception as exc:
            print(f"X  Error fetching switch inventory: {exc}")
            self.logger.error("Switch inventory fetch failed: %s", exc)
            return False

    # --------------------------------------------------------------------- #
    # Firmware data loading (cache / API)
    # --------------------------------------------------------------------- #

    def _load_firmware_data(self) -> list[dict[str, Any]]:
        """Load firmware data from cache or API."""
        print("\n-> Checking for cached firmware versions...")
        cached_data = self._load_from_cache()
        if cached_data:
            return cached_data
        return self._fetch_firmware_from_api()

    def _load_from_cache(self) -> list[dict[str, Any]] | None:
        """Load firmware data from cache file if fresh."""
        if not os.path.exists(self.CACHE_FILE):
            print("-> No cache file found, will query API")
            self.logger.info("No cached firmware data found")
            return None

        try:
            file_age_hours = (datetime.now().timestamp() - os.path.getmtime(self.CACHE_FILE)) / 3600

            if file_age_hours >= self.CACHE_FRESHNESS_HOURS:
                print(f"-> Cache file exists but is stale ({file_age_hours:.1f} hours old)")
                self.logger.info("Cache file stale, will refresh from API")
                return None

            file_size = os.path.getsize(self.CACHE_FILE)
            if file_size == 0:
                print("-> Cache file exists but is empty, will query API")
                self.logger.info("Cache file is empty, will refresh from API")
                return None

            print(f"!? Found fresh cached firmware data ({file_age_hours:.1f} hours old)")
            self.logger.info(
                "Using cached firmware data (age: %.1f hours)",
                file_age_hours,
            )
            return self._read_cache_file()

        except Exception as cache_error:
            self.logger.warning("Error reading cache file: %s", cache_error)
            print("-> Cache file unreadable, will query API")
            return None

    def _read_cache_file(self) -> list[dict[str, Any]]:
        """Read and parse cache file contents."""
        firmware_data: list[dict[str, Any]] = []
        with open(self.CACHE_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                firmware_entry: dict[str, Any] = {
                    "version": row["version"],
                    "model": row["model"],
                    "record_id": (int(row["record_id"]) if row.get("record_id") else None),
                    "record_size": (int(row["record_size"]) if row.get("record_size") else None),
                    "record_md5": row.get("record_md5", ""),
                    "_short": row.get("_short", ""),
                }
                firmware_data.append(firmware_entry)

        if firmware_data:
            self.logger.info(
                "Loaded %d firmware entries from cache",
                len(firmware_data),
            )

        return firmware_data

    def _fetch_firmware_from_api(self) -> list[dict[str, Any]]:
        """Fetch firmware versions from Mist API."""
        import mistapi

        print("-> Querying available firmware versions from Mist API...")
        try:
            self.logger.debug("Calling listOrgAvailableDeviceVersions API for switch firmware")
            versions_response = mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions(
                self.apisession, self.org_id, type="switch"
            )

            if not (versions_response and hasattr(versions_response, "data") and versions_response.data):
                self.logger.warning("API returned empty or invalid firmware data")
                print("X  No firmware data returned from API")
                return []

            firmware_data: list[dict[str, Any]] = versions_response.data
            self.logger.debug(
                "API returned %d firmware entries",
                len(firmware_data),
            )

            self._save_to_cache(firmware_data)
            return firmware_data

        except Exception as api_error:
            self.logger.error(
                "Failed to query switch firmware versions: %s",
                api_error,
            )
            print(f"X  Error querying firmware versions: {api_error}")
            return []

    def _save_to_cache(self, firmware_data: list[dict[str, Any]]) -> None:
        """Save firmware data to cache file."""
        try:
            os.makedirs("data", exist_ok=True)
            fieldnames = [
                "version",
                "model",
                "record_id",
                "record_size",
                "record_md5",
                "_short",
            ]
            with open(
                self.CACHE_FILE,
                "w",
                newline="",
                encoding="utf-8",
            ) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for entry in firmware_data:
                    if isinstance(entry, dict):
                        cache_row = {
                            "version": entry.get("version", ""),
                            "model": entry.get("model", ""),
                            "record_id": entry.get("record_id", ""),
                            "record_size": entry.get("record_size", ""),
                            "record_md5": entry.get("record_md5", ""),
                            "_short": entry.get("_short", ""),
                        }
                        writer.writerow(cache_row)

            print(f"!? Cached {len(firmware_data)} firmware entries to {self.CACHE_FILE}")
            self.logger.info(
                "Saved %d firmware entries to cache",
                len(firmware_data),
            )

        except Exception as save_error:
            self.logger.warning("Failed to save firmware cache: %s", save_error)
            print(f"!? Warning: Could not cache firmware data: {save_error}")

    # --------------------------------------------------------------------- #
    # Firmware data processing
    # --------------------------------------------------------------------- #

    def _process_firmware_data(self, firmware_data: list[dict[str, Any]]) -> None:
        """Process firmware data for model compatibility filtering."""
        print(f"-> Processing {len(firmware_data)} firmware entries...")

        raw_versions: list[str] = []
        for firmware_entry in firmware_data:
            if not isinstance(firmware_entry, dict):
                continue

            version = firmware_entry.get("version")
            firmware_model = firmware_entry.get("model")

            if version and firmware_model and firmware_model in self.switch_models:
                if version not in self.compatible_versions:
                    self.compatible_versions[version] = set()
                self.compatible_versions[version].add(firmware_model)
                raw_versions.append(version)
                self.logger.debug(
                    "Firmware %s compatible with model: %s",
                    version,
                    firmware_model,
                )

        unique_versions = list(set(raw_versions))
        self.available_versions = sorted(
            unique_versions,
            key=self._version_sort_key,
            reverse=True,
        )

        self.logger.info(
            "Filtered %d compatible versions from %d entries",
            len(self.available_versions),
            len(firmware_data),
        )

    @staticmethod
    def _version_sort_key(
        version_string: str,
    ) -> list[int | str]:
        """Create sort key for proper version number ordering."""
        try:
            normalized = version_string.replace("-S", ".").replace("R", ".")
            parts: list[int | str] = []
            for part in normalized.split("."):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(part.lower())
            return parts
        except Exception:
            return [version_string.lower()]

    # --------------------------------------------------------------------- #
    # Version selection
    # --------------------------------------------------------------------- #

    def _get_version_selection(self) -> dict[str, Any] | None:
        """Get user's firmware version selection."""
        if not self.available_versions:
            return self._handle_no_versions()

        print(f"!? Found {len(self.available_versions)} compatible firmware versions")
        self._display_version_table()
        return self._prompt_version_selection()

    def _handle_no_versions(self) -> dict[str, Any] | None:
        """Handle case when no compatible versions found."""
        if self.switch_models:
            print(f"X  No compatible firmware versions found for: {', '.join(sorted(self.switch_models))}")
        else:
            print("X  No switch firmware versions available from API")

        print("\nFallback Option:")
        print("You can still proceed by manually specifying a firmware version.")
        print("!? WARNING: Manual entry bypasses model compatibility checks!")

        fallback_choice = input("\nProceed with manual firmware entry? (y/N): ").strip().lower()
        if fallback_choice not in ["y", "yes"]:
            print("-> Operation cancelled")
            return {"error": "No compatible firmware versions and manual entry declined"}

        return self._get_manual_version_entry()

    def _get_manual_version_entry(self) -> dict[str, Any] | None:
        """Get manually entered firmware version."""
        print("\nManual firmware version entry:")
        print(f"Switch models in organization: {', '.join(sorted(self.switch_models))}")
        print("Examples: 23.4R2.21, 22.4R3.25, 21.4R3.15, 20.4R3.8")

        while True:
            manual_version = input("Enter firmware version: ").strip()
            if manual_version:
                self.target_version = manual_version
                print(f"!? Using manually specified firmware version: {self.target_version}")
                print("   Model compatibility has NOT been verified!")
                self.logger.warning(
                    "Using manually specified firmware %s",
                    self.target_version,
                )
                return None
            print("X  Firmware version is required")

    def _display_version_table(self) -> None:
        """Display available firmware versions in formatted table."""
        print("\nAvailable firmware versions (filtered by device model compatibility):")
        print("Index | Version      | Compatible Models                | Notes")
        print("------|--------------|----------------------------------|------")

        for idx, version in enumerate(self.available_versions, 1):
            notes = self._get_version_notes(version, idx)
            models_str = self._format_compatible_models(version)
            print(f"{idx:5} | {version:12} | {models_str:32} | {notes}")

    def _get_version_notes(self, version: str, index: int) -> str:
        """Get notes string for a firmware version."""
        if version in self.current_firmware_versions:
            return "(Currently installed)"
        if index == 1:
            return "(Latest/Recommended)"
        return ""

    def _format_compatible_models(self, version: str) -> str:
        """Format compatible models string for display."""
        version_models = sorted(self.compatible_versions.get(version, []))
        models_str = ", ".join(version_models) if version_models else "Unknown"
        if len(models_str) > 32:
            models_str = models_str[:29] + "..."
        return models_str

    def _prompt_version_selection(self) -> dict[str, Any] | None:
        """Prompt user to select firmware version by index."""
        while True:
            try:
                count = len(self.available_versions)
                print(f"\nSelect firmware version by index (1-{count}):")
                selection = input("Enter index number: ").strip()

                if not selection:
                    print("X  Selection required")
                    continue

                selection_idx = int(selection) - 1

                if 0 <= selection_idx < count:
                    self.target_version = self.available_versions[selection_idx]
                    print(f"-> Selected firmware version: {self.target_version}")
                    return None
                print(f"X  Invalid selection. Enter a number between 1 and {count}")

            except ValueError:
                print("X  Invalid input. Please enter a number")
            except KeyboardInterrupt:
                print("\n-> Operation cancelled by user")
                return {"cancelled": True}

    # --------------------------------------------------------------------- #
    # Step 5: Upgrade Confirmation
    # --------------------------------------------------------------------- #

    def _confirm_upgrade(self) -> bool:
        """Display configuration summary and get user confirmation."""
        self._display_config_summary()
        self._display_warnings()

        print("\nTo proceed with switch firmware upgrade, type: UPGRADE SWITCHES")
        confirmation = self.safe_input_fn(
            "Confirmation: ",
            "",
            True,
            "switch firmware upgrade confirmation",
        )

        if confirmation is None or confirmation != "UPGRADE SWITCHES":
            print("-> Operation cancelled - incorrect confirmation")
            self.logger.info("Switch firmware upgrade cancelled by user")
            return False

        return True

    def _display_config_summary(self) -> None:
        """Display upgrade configuration summary."""
        print(f"\n{'=' * 60}")
        print("UPGRADE CONFIGURATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Organization: {self.org_name}")
        print(f"Sites to upgrade: {len(self.selected_sites)}")
        print(f"Target firmware: {self.target_version}")
        print(f"Upgrade strategy: {self.upgrade_strategy}")
        force_label = "Yes" if self.force_upgrade else "No"
        print(f"Force upgrade: {force_label}")
        reboot_label = "Yes" if self.auto_reboot else "No"
        print(f"Auto reboot: {reboot_label}")
        snapshot_label = "Yes" if self.take_snapshot else "No"
        print(f"Recovery snapshot after reboot: {snapshot_label}")

    @staticmethod
    def _display_warnings() -> None:
        """Display critical warnings before upgrade."""
        print("\n!? CRITICAL WARNING !?")
        print("Switch firmware upgrades will cause network disruption!")
        print("- Switches will reboot and be offline during upgrade")
        print("- Plan appropriate maintenance windows")
        print("- Ensure backup connectivity if needed")
        print("- Monitor upgrade progress closely")

    # --------------------------------------------------------------------- #
    # Step 6: Execute Upgrades
    # --------------------------------------------------------------------- #

    def _execute_upgrades(self) -> dict[str, Any]:
        """Execute firmware upgrades across all selected sites."""
        print(f"\n{'=' * 60}")
        print("EXECUTING SWITCH FIRMWARE UPGRADE")
        print(f"{'=' * 60}")

        self._initialize_results()
        self.logger.info(
            "Starting switch firmware upgrade: %s",
            self.upgrade_results["operation_id"],
        )

        try:
            for site_index, site_info in enumerate(self.selected_sites, 1):
                self._process_site(site_index, site_info)

            self._finalize_results()
            return self.upgrade_results

        except Exception as exc:
            return self._handle_critical_error(exc)

    def _initialize_results(self) -> None:
        """Initialize results tracking structure."""
        self.upgrade_results = {
            "operation_id": f"switch_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_version": self.target_version,
            "strategy": self.upgrade_strategy,
            "force": self.force_upgrade,
            "reboot": self.auto_reboot,
            "snapshot": self.take_snapshot,
            "sites_processed": 0,
            "sites_successful": 0,
            "sites_failed": 0,
            "site_results": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        }

    def _process_site(self, site_index: int, site_info: dict[str, Any]) -> None:
        """Process firmware upgrade for a single site."""
        site_id = site_info.get("id", "")
        site_name = site_info.get("name", "Unknown Site")

        if not site_id:
            self.logger.error("Site has no ID: %s", site_name)
            self.upgrade_results["sites_failed"] += 1
            return

        total = len(self.selected_sites)
        print(f"\n-> Processing site {site_index}/{total}: {site_name}")
        self.logger.debug("Processing site: %s (%s)", site_name, site_id)

        try:
            site_switches = self._get_site_switches(site_id, site_name)
            if site_switches is None:
                return

            if not site_switches:
                self._record_no_switches(site_id, site_name)
                return

            print(f"  -> Found {len(site_switches)} switches")
            self._execute_site_upgrade(site_id, site_name, site_switches)

        except Exception as exc:
            self._record_site_error(site_id, site_name, str(exc))

        self.upgrade_results["sites_processed"] += 1

    def _get_site_switches(self, site_id: str, site_name: str) -> list[dict[str, Any]] | None:
        """Get switches for a specific site."""
        import mistapi

        site_devices_response = mistapi.api.v1.sites.devices.listSiteDevices(self.apisession, site_id, type="switch")

        if site_devices_response.status_code != 200:
            print(f"  X  Error retrieving devices: {site_devices_response.status_code}")
            self.upgrade_results["sites_failed"] += 1
            self.upgrade_results["site_results"].append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "status": "failed",
                    "error": f"Device retrieval failed: {site_devices_response.status_code}",
                }
            )
            return None

        return [d for d in site_devices_response.data if d.get("type") == "switch"]

    def _record_no_switches(self, site_id: str, site_name: str) -> None:
        """Record result when no switches found in site."""
        print("  -> No switches found in site")
        self.upgrade_results["sites_processed"] += 1
        self.upgrade_results["site_results"].append(
            {
                "site_id": site_id,
                "site_name": site_name,
                "status": "skipped",
                "switches_count": 0,
                "reason": "No switches found",
            }
        )

    def _execute_site_upgrade(
        self,
        site_id: str,
        site_name: str,
        switches: list[dict[str, Any]],
    ) -> None:
        """Execute firmware upgrade for switches in a site."""
        import mistapi

        switch_device_ids: list[str] = [str(s.get("id")) for s in switches if s.get("id")]

        if not switch_device_ids:
            self.logger.error(
                "No valid switch device IDs found for site %s",
                site_name,
            )
            self.upgrade_results["sites_failed"] += 1
            self.upgrade_results["site_results"].append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "status": "failed",
                    "reason": "No valid switch device IDs",
                }
            )
            return

        upgrade_request = self._build_upgrade_request(switch_device_ids)

        print("  -> Initiating firmware upgrade...")
        self.logger.debug(
            "Upgrade request for site %s: %s",
            site_name,
            upgrade_request,
        )

        upgrade_response = mistapi.api.v1.sites.devices.upgradeSiteDevices(
            self.apisession, site_id, body=upgrade_request
        )

        self._record_upgrade_result(site_id, site_name, switches, upgrade_response)

    def _build_upgrade_request(self, device_ids: list[str]) -> dict[str, Any]:
        """Build the upgrade request payload."""
        return {
            "version": self.target_version,
            "strategy": self.upgrade_strategy,
            "force": self.force_upgrade,
            "reboot": self.auto_reboot,
            "snapshot": self.take_snapshot,
            "device_ids": device_ids,
        }

    def _record_upgrade_result(
        self,
        site_id: str,
        site_name: str,
        switches: list[dict[str, Any]],
        response: Any,
    ) -> None:
        """Record the result of an upgrade attempt."""
        if response.status_code in [200, 202]:
            print("  !? Upgrade initiated successfully")
            self.upgrade_results["sites_successful"] += 1
            self.upgrade_results["site_results"].append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "status": "initiated",
                    "switches_count": len(switches),
                    "target_version": self.target_version,
                    "strategy": self.upgrade_strategy,
                    "response_code": response.status_code,
                }
            )
            self.logger.info(
                "Switch firmware upgrade initiated for site: %s",
                site_name,
            )
        else:
            print(f"  X  Upgrade failed: HTTP {response.status_code}")
            self.upgrade_results["sites_failed"] += 1
            self.upgrade_results["site_results"].append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "status": "failed",
                    "switches_count": len(switches),
                    "error": f"API error: {response.status_code}",
                    "response": (response.data if hasattr(response, "data") else None),
                }
            )
            self.logger.error(
                "Switch firmware upgrade failed for site %s: %s",
                site_name,
                response.status_code,
            )

    def _record_site_error(self, site_id: str, site_name: str, error: str) -> None:
        """Record an error that occurred while processing a site."""
        print(f"  X  Error processing site: {error}")
        self.upgrade_results["sites_failed"] += 1
        self.upgrade_results["site_results"].append(
            {
                "site_id": site_id,
                "site_name": site_name,
                "status": "error",
                "error": error,
            }
        )
        self.logger.error(
            "Exception processing site %s: %s",
            site_name,
            error,
        )

    def _finalize_results(self) -> None:
        """Finalize results and display summary."""
        self.upgrade_results["end_time"] = datetime.now().isoformat()
        self._display_results_summary()

    def _display_results_summary(self) -> None:
        """Display the final upgrade results summary."""
        print(f"\n{'=' * 60}")
        print("SWITCH FIRMWARE UPGRADE SUMMARY")
        print(f"{'=' * 60}")
        results = self.upgrade_results
        print(f"Operation ID: {results['operation_id']}")
        print(f"Sites processed: {results['sites_processed']}")
        print(f"Sites successful: {results['sites_successful']}")
        print(f"Sites failed: {results['sites_failed']}")
        print(f"Target firmware: {self.target_version}")
        print(f"Strategy: {self.upgrade_strategy}")

        self._display_failure_details()

        print("\nUpgrade operations have been initiated.")
        print("Monitor progress through Mist dashboard or API.")
        print("Check individual switch status for completion.")

        self.logger.info(
            "Switch firmware upgrade operation completed: %s",
            results["operation_id"],
        )

    def _display_failure_details(self) -> None:
        """Display details of any failed sites."""
        failed = self.upgrade_results["sites_failed"]
        if failed > 0:
            print(f"\n!? {failed} sites encountered errors:")
            for result in self.upgrade_results["site_results"]:
                if result["status"] in ["failed", "error"]:
                    error_msg = result.get("error", "Unknown error")
                    print(f"  - {result['site_name']}: {error_msg}")

    def _handle_critical_error(self, error: Exception) -> dict[str, Any]:
        """Handle critical error during upgrade execution."""
        error_msg = f"Critical error in switch firmware upgrade: {error}"
        print(f"\nX  {error_msg}")
        self.logger.error(error_msg)

        self.upgrade_results["end_time"] = datetime.now().isoformat()
        self.upgrade_results["error"] = str(error)

        return self.upgrade_results


def bulk_upgrade_switch_firmware_by_site_impl(org_id, sites_to_upgrade_override=None):
    """
    DESTRUCTIVE: Execute firmware upgrades on switches across selected sites.

    This function performs bulk firmware upgrades on network switches with comprehensive
    safety checks and detailed progress tracking. Supports multiple upgrade strategies
    including big bang, canary testing, and rolling upgrade modes.

    SECURITY: This operation will reboot network switches and may cause network disruption.
    All switches in target sites will be affected. Use with extreme caution in production.

    Args:
        org_id: Organization ID
        sites_to_upgrade_override: Optional list of site dictionaries for template-based upgrades

    Returns:
        dict: Upgrade operation results and status information
        canary_percentage (int): Percentage of devices for canary testing
        rrm_rollout_percentage (int): Percentage per wave for rolling upgrades
        delay_between_canary_and_rrm (int): Minutes between canary and rollout phases
        delay_between_rrm_waves (int): Minutes between rolling upgrade waves
        csv_export_path (str): Path for exporting upgrade operation details

    Returns:
        dict: Comprehensive upgrade operation results with success/failure tracking

    Raises:
        Exception: On critical API failures or validation errors

    NETWORK IMPACT WARNING:
    - Switch reboots will disrupt network connectivity
    - Plan maintenance windows for production environments
    - Verify backup connectivity paths before execution
    - Monitor upgrade progress closely for rapid intervention
    """
    # Set up logging for this function
    logger = logging.getLogger(__name__)
    logger.debug(f"Starting bulk switch firmware upgrade - org_id: {org_id}")

    # Get organization information
    print("\n-> Validating organization access...")
    try:
        org_info = mistapi.api.v1.orgs.orgs.getOrg(apisession, org_id)
        if org_info.status_code != 200:
            print(f"X  Error accessing organization: {org_info.status_code}")
            logger.error(f"Failed to access organization {org_id}: {org_info.status_code}")
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
            sites_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
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

            site_choice = input("\nEnter your choice (A/S/C): ").strip().upper()

            if site_choice == "C":
                print("-> Operation cancelled by user")
                return {"cancelled": True}
            elif site_choice == "A":
                selected_sites = all_sites
                print(f"-> Selected all {len(selected_sites)} sites")
            elif site_choice == "S":
                selected_sites = []
                print("\nEnter site numbers (comma-separated) or ranges (e.g., 1-5):")
                site_input = input("Sites: ").strip()

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

    # Switch firmware upgrade parameter selection
    print(f"\n{'='*60}")
    print("SWITCH FIRMWARE UPGRADE PARAMETER CONFIGURATION")
    print(f"{'='*60}")

    # Strategy selection
    print("\nUpgrade Strategy Options:")
    print("1. big_bang    - Upgrade all switches simultaneously (fastest)")
    print("2. serial      - Upgrade switches one by one (safest)")
    print("3. canary      - Test subset first, then upgrade remaining")

    while True:
        strategy_choice = input("\nSelect upgrade strategy (1-3): ").strip()
        if strategy_choice == "1":
            upgrade_strategy = "big_bang"
            break
        elif strategy_choice == "2":
            upgrade_strategy = "serial"
            break
        elif strategy_choice == "3":
            upgrade_strategy = "canary"
            break
        else:
            print("X  Please enter 1, 2, or 3")

    print(f"-> Selected strategy: {upgrade_strategy}")

    # Force upgrade selection
    print("\nForce Upgrade Options:")
    print("1. Yes - Force upgrade even if same version (recommended for testing)")
    print("2. No  - Skip devices already on target version (recommended for production)")

    while True:
        force_choice = input("\nForce upgrade? (1-2): ").strip()
        if force_choice == "1":
            force_upgrade = True
            break
        elif force_choice == "2":
            force_upgrade = False
            break
        else:
            print("X  Please enter 1 or 2")

    print(f"-> Force upgrade: {'Yes' if force_upgrade else 'No'}")

    # Reboot selection
    print("\nReboot Options:")
    print("1. Yes - Reboot after upgrade (required for switches - recommended)")
    print("2. No  - No reboot (not recommended for switches)")

    while True:
        reboot_choice = input("\nReboot after upgrade? (1-2): ").strip()
        if reboot_choice == "1":
            auto_reboot = True
            break
        elif reboot_choice == "2":
            auto_reboot = False
            print("!? WARNING: Switches typically require reboot to complete firmware upgrade")
            break
        else:
            print("X  Please enter 1 or 2")

    print(f"-> Auto reboot: {'Yes' if auto_reboot else 'No'}")

    # Recovery snapshot selection (Junos specific)
    print("\nRecovery Snapshot Options (Junos devices only):")
    print("1. Yes - Take recovery snapshot after device reboots (recommended for Junos)")
    print("2. No  - Skip recovery snapshot (faster but no post-upgrade backup)")

    while True:
        snapshot_choice = input("\nTake recovery snapshot after reboot? (1-2): ").strip()
        if snapshot_choice == "1":
            take_snapshot = True
            break
        elif snapshot_choice == "2":
            take_snapshot = False
            break
        else:
            print("X  Please enter 1 or 2")

    print(f"-> Recovery snapshot after reboot: {'Yes' if take_snapshot else 'No'}")

    # Firmware version selection
    print(f"\n{'='*60}")
    print("FIRMWARE VERSION SELECTION")
    print(f"{'='*60}")

    # Get available firmware versions for switches
    print("\n-> Discovering available switch firmware versions...")
    try:
        # Get switch inventory to determine current firmware and models
        switches_response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, type="switch")

        if switches_response.status_code != 200:
            print(f"X  Error retrieving switch inventory: {switches_response.status_code}")
            return {"error": "Failed to retrieve switch inventory"}

        switches = switches_response.data
        if not switches:
            print("X  No switches found in organization")
            return {"error": "No switches found"}

        print(f"!? Found {len(switches)} switches")

        # Extract unique current firmware versions and models
        current_firmware_versions = set()
        switch_models = set()
        for switch in switches:
            if switch.get("version"):
                current_firmware_versions.add(switch.get("version"))
            if switch.get("model"):
                switch_models.add(switch.get("model"))

        print(f"-> Switch models found: {', '.join(sorted(switch_models))}")
        print(f"-> Current firmware versions: {', '.join(sorted(current_firmware_versions))}")

        if not switch_models:
            print("!? WARNING: No switch models detected - firmware filtering may not work properly")
            logger.warning("No switch models found in inventory - firmware compatibility checking disabled")

        # Check for cached firmware data first, then query API if needed
        print("\n-> Checking for cached firmware versions...")
        available_versions = []
        compatible_versions = {}  # Initialize here for scope
        firmware_data = []

        # Define cache file path and freshness threshold
        # Name reflects API endpoint: /orgs/{org_id}/devices/versions?type=switch
        cache_file = os.path.join("data", "cached_org_devices_versions_switch.csv")
        cache_freshness_hours = 24  # Cache is fresh for 24 hours
        use_cached_data = False

        # Check if cache file exists and is fresh
        if os.path.exists(cache_file):
            try:
                file_age_hours = (datetime.now().timestamp() - os.path.getmtime(cache_file)) / 3600
                if file_age_hours < cache_freshness_hours:
                    # Check if file has content before using it
                    file_size = os.path.getsize(cache_file)
                    if file_size == 0:
                        print(f"-> Cache file exists but is empty, will query API")
                        logger.info("Cache file is empty, will refresh from API")
                    else:
                        print(f"!? Found fresh cached firmware data ({file_age_hours:.1f} hours old)")
                        logger.info(f"Using cached firmware data from {cache_file} (age: {file_age_hours:.1f} hours)")

                        # Read cached data and validate content
                        with open(cache_file, "r", newline="", encoding="utf-8") as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                # Convert CSV row back to API format
                                firmware_entry = {
                                    "version": row["version"],
                                    "model": row["model"],
                                    "record_id": int(row.get("record_id", 0)) if row.get("record_id") else None,
                                    "record_size": int(row.get("record_size", 0)) if row.get("record_size") else None,
                                    "record_md5": row.get("record_md5", ""),
                                    "_short": row.get("_short", ""),
                                }
                                firmware_data.append(firmware_entry)

                        # Validate that we actually loaded data
                        if firmware_data:
                            use_cached_data = True
                            logger.info(f"Loaded {len(firmware_data)} firmware entries from cache")
                        else:
                            print(f"-> Cache file has no valid data rows, will query API")
                            logger.info("Cache file exists but contains no valid data, will refresh from API")
                else:
                    print(
                        f"-> Cache file exists but is stale ({file_age_hours:.1f} hours old, threshold: {cache_freshness_hours}h)"
                    )
                    logger.info(f"Cache file stale, will refresh from API")
            except Exception as cache_error:
                logger.warning(f"Error reading cache file: {cache_error}")
                print("-> Cache file unreadable, will query API")
        else:
            print("-> No cache file found, will query API")
            logger.info("No cached firmware data found")

        # Query API if cache not used
        if not use_cached_data:
            print("-> Querying available firmware versions from Mist API...")
            try:
                # Use the proper listOrgAvailableDeviceVersions API with type=switch parameter
                logger.debug("Calling listOrgAvailableDeviceVersions API for switch firmware")
                versions_response = mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions(
                    apisession, org_id, type="switch"
                )

                if versions_response and hasattr(versions_response, "data") and versions_response.data:
                    firmware_data = versions_response.data
                    logger.debug(f"API returned {len(firmware_data)} firmware entries for switches")

                    # Save fresh API data to cache file
                    try:
                        os.makedirs("data", exist_ok=True)  # Ensure data directory exists
                        with open(cache_file, "w", newline="", encoding="utf-8") as csvfile:
                            fieldnames = ["version", "model", "record_id", "record_size", "record_md5", "_short"]
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()

                            for entry in firmware_data:
                                if isinstance(entry, dict):
                                    # Write relevant fields to cache
                                    cache_row = {
                                        "version": entry.get("version", ""),
                                        "model": entry.get("model", ""),
                                        "record_id": entry.get("record_id", ""),
                                        "record_size": entry.get("record_size", ""),
                                        "record_md5": entry.get("record_md5", ""),
                                        "_short": entry.get("_short", ""),
                                    }
                                    writer.writerow(cache_row)

                        print(f"!? Cached {len(firmware_data)} firmware entries to {cache_file}")
                        logger.info(f"Saved {len(firmware_data)} firmware entries to cache file")

                    except Exception as save_error:
                        logger.warning(f"Failed to save firmware cache: {save_error}")
                        print(f"!? Warning: Could not cache firmware data: {save_error}")

                else:
                    logger.warning("API returned empty or invalid firmware data")
                    raise Exception("No firmware data returned from API")

            except Exception as api_error:
                logger.error(f"Failed to query switch firmware versions from API: {api_error}")
                print(f"X  Error querying firmware versions: {api_error}")
                print("   Cannot proceed without current firmware version list.")
                return {"error": f"API firmware query failed: {api_error}"}

        # Process firmware data (works for both cached and fresh API data)
        if firmware_data:
            print(f"-> Processing {len(firmware_data)} firmware entries...")

            # Filter firmware versions by device model compatibility
            for firmware_entry in firmware_data:
                if isinstance(firmware_entry, dict):
                    # Get version number and model - API returns individual model per entry
                    version = firmware_entry.get("version")
                    firmware_model = firmware_entry.get("model")  # Single model, not array

                    if version and firmware_model:
                        # Check if this firmware model is compatible with any of our switch models
                        if firmware_model in switch_models:
                            if version not in compatible_versions:
                                compatible_versions[version] = set()
                            compatible_versions[version].add(firmware_model)
                            available_versions.append(version)

                            logger.debug(
                                f"Firmware version {version} compatible with organization model: {firmware_model}"
                            )
                        else:
                            logger.debug(
                                f"Firmware version {version} NOT compatible - available for: {firmware_model}, organization has: {sorted(switch_models)}"
                            )

            # Remove duplicates and sort versions (newest first)
            unique_versions = list(set(available_versions))

            def version_sort_key(version_string):
                """
                Create sort key for proper version number ordering.
                Handles Juniper version formats like: 24.4R2.23, 24.4R1-S2.12, 23.4R3.11
                """
                try:
                    # Remove common prefixes and suffixes, normalize separators
                    normalized = version_string.replace("-S", ".").replace("R", ".")
                    # Split into parts and convert numbers to integers for proper numeric sorting
                    parts = []
                    for part in normalized.split("."):
                        # Try to convert to int, fall back to string comparison
                        try:
                            parts.append(int(part))
                        except ValueError:
                            # Keep as string for non-numeric parts, but ensure consistent ordering
                            parts.append(part.lower())
                    return parts
                except Exception:
                    # Fallback to string sorting if parsing fails
                    return [version_string.lower()]

            available_versions = sorted(unique_versions, key=version_sort_key, reverse=True)

            # Count firmware entries by model for debugging
            model_counts = {}
            vjunos_versions = []
            ex4100_versions = []
            for entry in firmware_data:
                if isinstance(entry, dict):
                    model = entry.get("model", "Unknown")
                    version = entry.get("version")
                    model_counts[model] = model_counts.get(model, 0) + 1
                    if model == "VJUNOS" and version:
                        vjunos_versions.append(version)
                    elif model == "EX4100-F-12P" and version:
                        ex4100_versions.append(version)

            logger.debug(f"Firmware model distribution in data:")
            for model in sorted(switch_models):
                count = model_counts.get(model, 0)
                logger.debug(f"  {model}: {count} firmware entries")

            if vjunos_versions:
                logger.debug(f"Sample VJUNOS versions found: {sorted(set(vjunos_versions))[:5]}")
            else:
                logger.debug("No VJUNOS firmware entries found in data")

            # Log compatibility summary
            logger.info(
                f"Successfully filtered {len(available_versions)} compatible switch firmware versions from {len(firmware_data)} total entries"
            )
            if compatible_versions:
                logger.debug("Firmware compatibility summary:")
                for version in available_versions[:5]:  # Log top 5 versions
                    models_list = sorted(compatible_versions.get(version, []))
                    logger.debug(f"  {version}: {models_list}")
            else:
                logger.warning("No compatible firmware versions found for organization switch models")
        else:
            logger.error("No firmware data available for processing")
            print("X  No firmware data available")
            return {"error": "No firmware data available"}

        # Validate we have compatible firmware versions
        if not available_versions:
            if switch_models:
                error_msg = (
                    f"No compatible firmware versions found for switch models: {', '.join(sorted(switch_models))}"
                )
                print(f"X  {error_msg}")
                print("   This may indicate:")
                print("   - Switch models are not supported by current firmware releases")
                print("   - API data may be incomplete or outdated")
                print("   - Switch models may need manual firmware specification")
            else:
                error_msg = "No switch firmware versions available from API"
                print(f"X  {error_msg}")

            logger.error(error_msg)

            # Offer manual firmware version entry as fallback
            print(f"\nFallback Option:")
            print("You can still proceed by manually specifying a firmware version.")
            print("!? WARNING: Manual entry bypasses model compatibility checks!")
            print("Ensure the firmware version you enter is compatible with your switch models.")

            fallback_choice = input("\nProceed with manual firmware entry? (y/N): ").strip().lower()
            if fallback_choice not in ["y", "yes"]:
                print("-> Operation cancelled")
                return {"error": "No compatible firmware versions and manual entry declined"}

            # Manual firmware entry
            print("\nManual firmware version entry:")
            print(f"Switch models in organization: {', '.join(sorted(switch_models))}")
            print("Examples: 23.4R2.21, 22.4R3.25, 21.4R3.15, 20.4R3.8")

            while True:
                manual_version = input("Enter firmware version: ").strip()
                if manual_version:
                    target_version = manual_version
                    print(f"!? Using manually specified firmware version: {target_version}")
                    print("   Model compatibility has NOT been verified!")
                    logger.warning(
                        f"Using manually specified firmware {target_version} - compatibility not verified for models: {sorted(switch_models)}"
                    )
                    break
                else:
                    print("X  Firmware version is required")

            # Skip the normal selection process
            available_versions = [target_version]

        if available_versions:
            print(f"!? Found {len(available_versions)} compatible firmware versions")

            # Present firmware versions as indexed list with model compatibility
            print("\nAvailable firmware versions (filtered by device model compatibility):")
            print("Index | Version      | Compatible Models                | Notes")
            print("------|--------------|----------------------------------|------")

            for idx, version in enumerate(available_versions, 1):
                notes = ""
                if version in current_firmware_versions:
                    notes = "(Currently installed)"
                elif idx == 1:
                    notes = "(Latest/Recommended)"

                # Show which models this version is compatible with
                version_models = sorted(compatible_versions.get(version, []))
                models_str = ", ".join(version_models) if version_models else "Unknown"
                if len(models_str) > 32:  # Truncate if too long
                    models_str = models_str[:29] + "..."

                print(f"{idx:5} | {version:12} | {models_str:32} | {notes}")

            # Get user selection
            while True:
                try:
                    print(f"\nSelect firmware version by index (1-{len(available_versions)}):")
                    selection = input("Enter index number: ").strip()

                    if not selection:
                        print("X  Selection required")
                        continue

                    selection_idx = int(selection) - 1  # Convert to 0-based index

                    if 0 <= selection_idx < len(available_versions):
                        target_version = available_versions[selection_idx]
                        print(f"-> Selected firmware version: {target_version}")
                        break
                    else:
                        print(f"X  Invalid selection. Please enter a number between 1 and {len(available_versions)}")

                except ValueError:
                    print("X  Invalid input. Please enter a number")
                except KeyboardInterrupt:
                    print("\n-> Operation cancelled by user")
                    return {"cancelled": True}
        else:
            # Fallback to manual entry if no versions found
            print("-> No firmware versions available from API, using manual entry")
            print("\nPlease enter target firmware version manually:")
            print("Examples: 23.4R2.21, 22.4R3.25, 21.4R3.15, 20.4R3.8")

            target_version = input("Target firmware version: ").strip()
            if not target_version:
                print("X  Firmware version is required")
                return {"error": "No firmware version specified"}

        print(f"-> Target firmware version: {target_version}")

    except Exception as e:
        print(f"X  Error during firmware discovery: {str(e)}")
        logger.error(f"Firmware discovery failed: {str(e)}")
        return {"error": f"Firmware discovery error: {str(e)}"}

    # Configuration summary and confirmation
    print(f"\n{'='*60}")
    print("UPGRADE CONFIGURATION SUMMARY")
    print(f"{'='*60}")
    print(f"Organization: {org_name}")
    print(f"Sites to upgrade: {len(selected_sites)}")
    print(f"Target firmware: {target_version}")
    print(f"Upgrade strategy: {upgrade_strategy}")
    print(f"Force upgrade: {'Yes' if force_upgrade else 'No'}")
    print(f"Auto reboot: {'Yes' if auto_reboot else 'No'}")
    print(f"Recovery snapshot after reboot: {'Yes' if take_snapshot else 'No'}")

    print(f"\n!? CRITICAL WARNING !?")
    print("Switch firmware upgrades will cause network disruption!")
    print("- Switches will reboot and be offline during upgrade")
    print("- Plan appropriate maintenance windows")
    print("- Ensure backup connectivity if needed")
    print("- Monitor upgrade progress closely")

    print(f"\nTo proceed with switch firmware upgrade, type: UPGRADE SWITCHES")
    confirmation = safe_input("Confirmation: ", "", True, "switch firmware upgrade confirmation")

    if confirmation is None or confirmation != "UPGRADE SWITCHES":
        print("-> Operation cancelled - incorrect confirmation")
        logger.info("Switch firmware upgrade cancelled by user")
        return {"cancelled": True}

    # Execute upgrade operation
    print(f"\n{'='*60}")
    print("EXECUTING SWITCH FIRMWARE UPGRADE")
    print(f"{'='*60}")

    # Initialize results tracking
    upgrade_results = {
        "operation_id": f"switch_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "target_version": target_version,
        "strategy": upgrade_strategy,
        "force": force_upgrade,
        "reboot": auto_reboot,
        "snapshot": take_snapshot,
        "sites_processed": 0,
        "sites_successful": 0,
        "sites_failed": 0,
        "site_results": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None,
    }

    logger.info(f"Starting switch firmware upgrade: {upgrade_results['operation_id']}")

    try:
        # Process each site for switch firmware upgrade
        for site_index, site_info in enumerate(selected_sites, 1):
            site_id = site_info.get("id")
            site_name = site_info.get("name", "Unknown Site")

            print(f"\n-> Processing site {site_index}/{len(selected_sites)}: {site_name}")
            logger.debug(f"Processing site: {site_name} ({site_id})")

            try:
                # Get switches for this site
                site_devices_response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="switch")

                if site_devices_response.status_code != 200:
                    print(f"  X  Error retrieving devices: {site_devices_response.status_code}")
                    upgrade_results["sites_failed"] += 1
                    upgrade_results["site_results"].append(
                        {
                            "site_id": site_id,
                            "site_name": site_name,
                            "status": "failed",
                            "error": f"Device retrieval failed: {site_devices_response.status_code}",
                        }
                    )
                    continue

                site_switches = [d for d in site_devices_response.data if d.get("type") == "switch"]

                if not site_switches:
                    print(f"  -> No switches found in site")
                    upgrade_results["sites_processed"] += 1
                    upgrade_results["site_results"].append(
                        {
                            "site_id": site_id,
                            "site_name": site_name,
                            "status": "skipped",
                            "switches_count": 0,
                            "reason": "No switches found",
                        }
                    )
                    continue

                print(f"  -> Found {len(site_switches)} switches")

                # Extract switch device IDs for targeted upgrade
                switch_device_ids = [switch.get("id") for switch in site_switches if switch.get("id")]

                if not switch_device_ids:
                    logger.error(f"No valid switch device IDs found for site {site_name}")
                    upgrade_results["sites_failed"] += 1
                    upgrade_results["site_results"].append(
                        {
                            "site_id": site_id,
                            "site_name": site_name,
                            "status": "failed",
                            "reason": "No valid switch device IDs",
                        }
                    )
                    continue

                logger.debug(f"Switch device IDs for upgrade: {switch_device_ids}")

                # Prepare upgrade request with device IDs to target only switches
                upgrade_request = {
                    "version": target_version,
                    "strategy": upgrade_strategy,
                    "force": force_upgrade,
                    "reboot": auto_reboot,
                    "snapshot": take_snapshot,
                    "device_ids": switch_device_ids,  # Target only the switch devices
                }

                print(f"  -> Initiating firmware upgrade...")
                logger.debug(f"Upgrade request for site {site_name}: {upgrade_request}")

                # Execute upgrade via Mist API
                upgrade_response = mistapi.api.v1.sites.devices.upgradeSiteDevices(
                    apisession, site_id, body=upgrade_request
                )

                if upgrade_response.status_code in [200, 202]:
                    print(f"  !? Upgrade initiated successfully")
                    upgrade_results["sites_successful"] += 1
                    upgrade_results["site_results"].append(
                        {
                            "site_id": site_id,
                            "site_name": site_name,
                            "status": "initiated",
                            "switches_count": len(site_switches),
                            "target_version": target_version,
                            "strategy": upgrade_strategy,
                            "response_code": upgrade_response.status_code,
                        }
                    )
                    logger.info(f"Switch firmware upgrade initiated for site: {site_name}")

                else:
                    print(f"  X  Upgrade failed: HTTP {upgrade_response.status_code}")
                    upgrade_results["sites_failed"] += 1
                    upgrade_results["site_results"].append(
                        {
                            "site_id": site_id,
                            "site_name": site_name,
                            "status": "failed",
                            "switches_count": len(site_switches),
                            "error": f"API error: {upgrade_response.status_code}",
                            "response": upgrade_response.data if hasattr(upgrade_response, "data") else None,
                        }
                    )
                    logger.error(f"Switch firmware upgrade failed for site {site_name}: {upgrade_response.status_code}")

            except Exception as e:
                print(f"  X  Error processing site: {str(e)}")
                upgrade_results["sites_failed"] += 1
                upgrade_results["site_results"].append(
                    {"site_id": site_id, "site_name": site_name, "status": "error", "error": str(e)}
                )
                logger.error(f"Exception processing site {site_name}: {str(e)}")

            upgrade_results["sites_processed"] += 1

        # Finalize results
        upgrade_results["end_time"] = datetime.now().isoformat()

        print(f"\n{'='*60}")
        print("SWITCH FIRMWARE UPGRADE SUMMARY")
        print(f"{'='*60}")
        print(f"Operation ID: {upgrade_results['operation_id']}")
        print(f"Sites processed: {upgrade_results['sites_processed']}")
        print(f"Sites successful: {upgrade_results['sites_successful']}")
        print(f"Sites failed: {upgrade_results['sites_failed']}")
        print(f"Target firmware: {target_version}")
        print(f"Strategy: {upgrade_strategy}")

        if upgrade_results["sites_failed"] > 0:
            print(f"\n!? {upgrade_results['sites_failed']} sites encountered errors:")
            for result in upgrade_results["site_results"]:
                if result["status"] in ["failed", "error"]:
                    print(f"  - {result['site_name']}: {result.get('error', 'Unknown error')}")

        print(f"\nUpgrade operations have been initiated.")
        print(f"Monitor progress through Mist dashboard or API.")
        print(f"Check individual switch status for completion.")

        logger.info(f"Switch firmware upgrade operation completed: {upgrade_results['operation_id']}")
        return upgrade_results

    except Exception as e:
        error_msg = f"Critical error in switch firmware upgrade: {str(e)}"
        print(f"\nX  {error_msg}")
        logger.error(error_msg)

        upgrade_results["end_time"] = datetime.now().isoformat()
        upgrade_results["error"] = str(e)

        return upgrade_results
