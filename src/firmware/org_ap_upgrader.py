"""Org-level AP firmware upgrade operations for Mist organizations.

Uses the upgradeOrgDevices API (POST /api/v1/orgs/{org_id}/devices/upgrade)
for massive efficiency improvements when upgrading APs across many sites.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import importlib
import logging
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any


class OrgLevelAPFirmwareUpgrader:  # pylint: disable=too-many-instance-attributes
    """Org-Level AP Firmware Upgrade Manager.

    Uses the org-level upgrade API for efficiency:
    - Site-level API: 1 call per site per unique version
    - Org-level API: 1 call per unique version per org

    Features:
    - MSP multi-organization support
    - Org-level upgrade across all_sites or selected site_ids
    - Model-filtered upgrades using the 'models' parameter
    - Full support for upgrade strategies (big_bang, canary, rrm, serial)
    - Dry-run mode for safe validation

    NETWORK IMPACT WARNING:
    - APs will REBOOT during firmware upgrades
    - Wi-Fi connectivity will be TEMPORARILY LOST
    - Upgrades take 5-15 minutes per device
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        org_id: str,
        apisession: Any,
        *,
        dry_run: bool = False,
        safe_input_fn: Any = None,
        check_stop_fn: Any = None,
        get_org_id_fn: Any = None,
        fetch_sites_fn: Any = None,
        write_results_fn: Any = None,
        is_debug_fn: Any = None,
        msp_privileges: list[Any] | None = None,
        selected_msp: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the org-level AP firmware upgrader.

        Args:
            org_id: Mist organization ID.
            apisession: Authenticated mistapi session.
            dry_run: If True, simulate upgrades without making API calls.
            safe_input_fn: Callable for safe user input (prompt, context) -> str.
            check_stop_fn: Callable to check for stop signal () -> bool.
            get_org_id_fn: Callable to get or prompt for org_id () -> str | None.
            fetch_sites_fn: Callable to fetch all sites (org_id) -> list.
            write_results_fn: Callable to write results to file.
            is_debug_fn: Callable to check debug mode () -> bool.
            msp_privileges: List of MSP privilege dicts.
            selected_msp: Currently selected MSP dict.
        """
        self.org_id = org_id
        self.apisession = apisession
        self.dry_run = dry_run
        self._input_fn = safe_input_fn or (lambda prompt, _context="": input(prompt))
        self._check_stop_fn = check_stop_fn
        self._get_org_id_fn = get_org_id_fn
        self._fetch_sites_fn = fetch_sites_fn
        self._write_results_fn = write_results_fn
        self._is_debug_fn = is_debug_fn or (lambda: False)
        self._msp_privileges = msp_privileges or []
        self._selected_msp = selected_msp

        self._init_selection_state()
        self._init_device_state()
        self._init_results_state()

    def _init_selection_state(self) -> None:
        """Initialize site selection state."""
        self.target_all_sites: bool = True
        self.selected_site_ids: list[Any] = []
        self.selected_sites: list[Any] = []

    def _init_device_state(self) -> None:
        """Initialize device and firmware state."""
        self.all_aps: list[Any] = []
        self.aps_by_model: dict[str, list[Any]] = {}
        self.ap_versions: dict[str, str] = {}
        self.available_versions: list[Any] = []
        self.model_version_ranges: dict[str, list[str]] = {}
        self.upgrade_plan: dict[str, dict[str, Any]] = {}
        self.skipped_already_at_target: int = 0
        self.upgrade_config: dict[str, Any] = {}

    def _init_results_state(self) -> None:
        """Initialize results tracking state."""
        self.results: list[dict[str, Any]] = []
        self.successful_api_calls: int = 0
        self.failed_api_calls: int = 0
        self.total_devices_upgraded: int = 0

    # =========================================================================
    # ENTRY POINTS
    # =========================================================================

    def run(self) -> None:
        """Entry point that detects MSP privileges and branches accordingly."""
        logging.debug("Entering OrgLevelAPFirmwareUpgrader.run()")
        logging.info("OrgLevelAPFirmwareUpgrader workflow started, dry_run=%s", self.dry_run)

        if self._msp_privileges and len(self._msp_privileges) > 0:
            logging.debug("MSP privileges detected: %s MSP(s)", len(self._msp_privileges))
            mode = self._prompt_msp_mode()
            if mode is None:
                return
            if mode == "2":
                logging.info("User selected MSP Multi-Org mode")
                self._execute_msp_mode()
                return

        logging.info("Using single-org mode")
        org_id = self._resolve_org_id()
        if not org_id:
            print("  X No organization selected")
            logging.warning("No organization selected")
            return

        logging.info("Single-org mode: org_id=%s", org_id)
        self.org_id = org_id
        self.execute()

    def _prompt_msp_mode(self) -> str | None:
        """Prompt user to select MSP vs single-org mode."""
        print("")
        print("=" * 70)
        print("  ORG-LEVEL AP FIRMWARE UPGRADE")
        print("=" * 70)
        print("")
        print("  MSP privileges detected. Select operation mode:")
        print("")
        print("    [1] Single Organization - upgrade APs in current org")
        print("    [2] MSP Multi-Org - select orgs from your MSP(s)")
        print("")

        try:
            return self._input_fn("  Select mode (1-2) [1]: ", "msp_mode_select").strip() or "1"
        except SystemExit:
            logging.debug("SystemExit during mode selection")
            return None

    def _resolve_org_id(self) -> str | None:
        """Resolve org ID via the injected function."""
        if self._get_org_id_fn:
            result: str | None = self._get_org_id_fn()
            return result
        return self.org_id if self.org_id else None

    # =========================================================================
    # MSP MULTI-ORG MODE
    # =========================================================================

    def _execute_msp_mode(self) -> None:  # noqa: PLR0915
        """Execute MSP multi-organization upgrade mode."""
        logging.debug("Entering _execute_msp_mode(), dry_run=%s", self.dry_run)
        logging.info("Starting MSP Multi-Org AP firmware upgrade workflow")
        self._print_msp_mode_header()

        selected_msps = self._select_msps()
        if not selected_msps:
            print("  X Cancelled - no MSP selected")
            logging.warning("MSP selection cancelled")
            return

        logging.info("User selected %s MSP(s)", len(selected_msps))

        selected_orgs = self._collect_orgs_from_msps(selected_msps)
        if not selected_orgs:
            print("  X Cancelled - no organizations selected")
            logging.warning("Organization selection cancelled")
            return

        logging.info("User selected %s organization(s) for upgrade", len(selected_orgs))

        if not self._confirm_msp_orgs(selected_orgs):
            return

        all_results = self._execute_org_upgrades(selected_orgs)
        logging.info("MSP multi-org upgrade completed: %s organizations processed", len(all_results))
        self._print_msp_summary(all_results, self.dry_run)

    def _print_msp_mode_header(self) -> None:
        """Print MSP mode header banner."""
        print("")
        print("=" * 70)
        print("  MSP MULTI-ORG AP FIRMWARE UPGRADE")
        print("=" * 70)
        print("")
        print(f"  Your account has access to {len(self._msp_privileges)} MSP(s).")
        print("  This workflow will guide you through selecting MSPs and organizations,")
        print("  then execute firmware upgrades across all selected organizations.")

        if self.dry_run:
            print("")
            print("  >> DRY-RUN MODE: No actual upgrades will be performed <<")
            logging.debug("Dry-run mode enabled")

    def _collect_orgs_from_msps(self, selected_msps: list[Any]) -> list[Any]:
        """Collect orgs from each selected MSP."""
        selected_orgs: list[Any] = []
        for msp in selected_msps:
            orgs = self._select_orgs_from_msp(msp)
            if orgs:
                selected_orgs.extend(orgs)
        return selected_orgs

    def _confirm_msp_orgs(self, selected_orgs: list[Any]) -> bool:
        """Confirm selected orgs before proceeding."""
        print("")
        print("-" * 70)
        print("  STEP 3: Confirmation")
        print("-" * 70)
        print("")
        print(f"  Ready to upgrade firmware across {len(selected_orgs)} organization(s):")
        print("")
        for idx, org in enumerate(selected_orgs, start=1):
            print(f"    {idx:>3}. {org.get('name', 'Unknown')}")
        print("")
        print("  Each organization will be processed sequentially.")
        print("  You will configure upgrade settings for each organization.")
        print("")

        try:
            confirm = self._input_fn("  Proceed with these organizations? (Y/n): ", "msp_confirm").strip().lower()
        except SystemExit:
            logging.debug("SystemExit during MSP confirmation")
            return False

        if confirm in ["n", "no"]:
            print("  Cancelled.")
            logging.warning("User declined MSP multi-org confirmation")
            return False

        print("")
        print(f"  + Confirmed - proceeding with {len(selected_orgs)} organization(s)")
        logging.info("User confirmed MSP multi-org upgrade for %s organization(s)", len(selected_orgs))
        return True

    def _execute_org_upgrades(self, selected_orgs: list[Any]) -> list[dict[str, Any]]:
        """Execute upgrade for each selected org."""
        all_results: list[dict[str, Any]] = []
        for idx, org_info in enumerate(selected_orgs, start=1):
            org_id = org_info["id"]
            org_name = org_info["name"]

            print("")
            print("=" * 70)
            print(f"  ORGANIZATION {idx}/{len(selected_orgs)}: {org_name}")
            print("=" * 70)

            logging.info("Processing organization %s/%s: %s", idx, len(selected_orgs), org_name)
            upgrader = OrgLevelAPFirmwareUpgrader(
                org_id,
                self.apisession,
                dry_run=self.dry_run,
                safe_input_fn=self._input_fn,
                check_stop_fn=self._check_stop_fn,
                get_org_id_fn=self._get_org_id_fn,
                fetch_sites_fn=self._fetch_sites_fn,
                write_results_fn=self._write_results_fn,
                is_debug_fn=self._is_debug_fn,
            )
            upgrader.execute()
            all_results.append(
                {
                    "org_id": org_id,
                    "org_name": org_name,
                    "success": upgrader.successful_api_calls,
                    "failed": upgrader.failed_api_calls,
                    "devices": upgrader.total_devices_upgraded,
                }
            )
            logging.debug(
                "Organization %s: success=%s, failed=%s, devices=%s",
                org_name,
                upgrader.successful_api_calls,
                upgrader.failed_api_calls,
                upgrader.total_devices_upgraded,
            )
        return all_results

    # =========================================================================
    # MSP / ORG SELECTION
    # =========================================================================

    def _select_msps(self) -> list[Any]:  # noqa: C901, PLR0912, PLR0915
        """Select MSPs for upgrade."""
        logging.debug("Entering _select_msps()")
        print("")
        print("-" * 70)
        print("  STEP 1: MSP Selection")
        print("-" * 70)
        print("")
        print(f"  Your account has access to {len(self._msp_privileges)} MSP(s).")
        print("  Select which MSP(s) to operate on.")
        print("")

        if len(self._msp_privileges) == 1:
            msp_name = self._msp_privileges[0].get("msp_name", "Unknown")
            print(f"  Only one MSP available: {msp_name}")
            print(f"  + Auto-selected: {msp_name}")
            logging.info("Auto-selected single MSP: %s", msp_name)
            return list(self._msp_privileges)

        default_idx = self._find_selected_msp_index()
        self._display_msp_list(default_idx)

        return self._collect_msp_selection(default_idx)

    def _find_selected_msp_index(self) -> int | None:
        """Find index of currently selected MSP."""
        if not self._selected_msp:
            return None
        for idx, msp in enumerate(self._msp_privileges):
            if msp.get("msp_id") == self._selected_msp.get("msp_id"):
                return idx + 1
        return None

    def _display_msp_list(self, default_idx: int | None) -> None:
        """Display available MSPs."""
        print("  Available MSPs:")
        print("")
        for idx, msp in enumerate(self._msp_privileges, start=1):
            current_marker = " <-- currently selected" if default_idx == idx else ""
            print(
                f"    [{idx:>2}] {msp.get('msp_name', 'Unknown')} "
                f"(role: {msp.get('role', 'unknown')}){current_marker}"
            )
        print("")
        print("  Selection Options:")
        print("    - Single MSP: Enter number (e.g., '1')")
        print("    - Multiple MSPs: Comma-separated (e.g., '1,3,5')")
        print("    - Range: Dash or 'through' (e.g., '1-3' or '1 through 3')")
        print("    - ALL MSPs: Enter 'all'")
        print("    - Cancel: Enter 'q'")
        print("")

    def _collect_msp_selection(self, default_idx: int | None) -> list[Any]:
        """Collect MSP selection from user."""
        if default_idx:
            prompt = f"  Select MSP(s) [Enter for current selection {default_idx}]: "
        else:
            prompt = "  Select MSP(s): "

        try:
            selection = self._input_fn(prompt, "msp_select").strip().lower()
        except SystemExit:
            return []

        if selection == "" and default_idx and self._selected_msp is not None:
            return self._use_default_msp()
        if selection in ["q", ""]:
            print("  Cancelled.")
            logging.info("MSP selection cancelled")
            return []
        if selection == "all":
            return self._select_all_msps()

        return self._select_msps_by_indices(selection)

    def _use_default_msp(self) -> list[Any]:
        """Return the currently selected MSP as a list."""
        msp = self._selected_msp or {}
        print(f"  + Using current MSP: {msp.get('msp_name', 'Unknown')}")
        logging.debug("Using default MSP: %s", msp.get("msp_name"))
        return [self._selected_msp]

    def _select_all_msps(self) -> list[Any]:
        """Select all available MSPs."""
        print("")
        print(f"  + Selected ALL {len(self._msp_privileges)} MSP(s):")
        for msp in self._msp_privileges:
            print(f"      - {msp.get('msp_name', 'Unknown')}")
        logging.info("User selected ALL %s MSP(s)", len(self._msp_privileges))
        return list(self._msp_privileges)

    def _select_msps_by_indices(self, selection: str) -> list[Any]:
        """Select MSPs by parsed index selection."""
        indices = self._parse_selection(selection, len(self._msp_privileges))
        if not indices:
            print("  X Invalid selection")
            logging.warning("Invalid MSP selection: %s", selection)
            return []

        selected = [self._msp_privileges[i] for i in indices]
        print("")
        print(f"  + Selected {len(selected)} MSP(s):")
        for msp in selected:
            print(f"      - {msp.get('msp_name', 'Unknown')}")
        logging.info("User selected %s MSP(s)", len(selected))
        return selected

    def _select_orgs_from_msp(self, msp: dict[str, Any]) -> list[Any]:  # noqa: C901, PLR0915
        """Select organizations from a specific MSP."""
        logging.debug("Entering _select_orgs_from_msp() for MSP: %s", msp.get("msp_name"))

        msp_id = msp["msp_id"]
        msp_name = msp.get("msp_name", "Unknown")

        print("")
        print("-" * 70)
        print(f"  STEP 2: Organization Selection for MSP: {msp_name}")
        print("-" * 70)
        print("")
        print(f"  Fetching organizations from {msp_name}...")

        if self.apisession is None:
            print("  X API session not initialized")
            logging.error("API session not initialized for org fetch")
            return []

        try:
            orgs = self._fetch_msp_orgs(msp_id, msp_name)
            if not orgs:
                return []

            self._display_org_list(orgs, msp_name)
            return self._collect_org_selection(orgs, msp_name)

        except Exception as error:
            print(f"  X Error fetching organizations: {error}")
            logging.error("Failed to fetch orgs from MSP %s: %s", msp_name, error)
            return []

    def _fetch_msp_orgs(self, msp_id: str, msp_name: str) -> list[Any]:
        """Fetch organizations from an MSP."""
        msp_orgs_api = importlib.import_module("mistapi.api.v1.msps.orgs")
        logging.debug("Calling listMspOrgs for msp_id=%s", msp_id)
        response = msp_orgs_api.listMspOrgs(self.apisession, msp_id)

        if not response or not hasattr(response, "data"):
            print(f"  X Failed to fetch organizations from {msp_name}")
            logging.warning("Failed to fetch organizations from MSP %s", msp_name)
            return []

        orgs = response.data if isinstance(response.data, list) else [response.data] if response.data else []
        if not orgs:
            print(f"  X No organizations found under {msp_name}")
            logging.warning("No organizations found under MSP %s", msp_name)
            return []

        orgs = sorted(orgs, key=lambda x: x.get("name", "").lower())
        print(f"  + Found {len(orgs)} organization(s) under {msp_name}")
        logging.info("Found %s organizations under MSP %s", len(orgs), msp_name)
        return orgs

    def _display_org_list(self, orgs: list[Any], msp_name: str) -> None:
        """Display numbered organization list."""
        print("")
        print("  Organizations:")
        print("")
        for idx, org in enumerate(orgs, start=1):
            print(f"    [{idx:>3}] {org.get('name', 'Unknown')}")
        print("")
        print("  Selection Options:")
        print("    - Single org: Enter number (e.g., '1')")
        print("    - Multiple orgs: Comma-separated (e.g., '1,3,5')")
        print("    - Range: Dash or 'through' (e.g., '1-10' or '1 through 10')")
        print("    - ALL orgs under this MSP: Enter 'all'")
        print("    - Skip this MSP: Enter 'q'")
        print("")

    def _collect_org_selection(self, orgs: list[Any], msp_name: str) -> list[Any]:
        """Collect org selection from user."""
        try:
            selection = self._input_fn("  Select organization(s): ", "org_select").strip().lower()
        except SystemExit:
            logging.debug("SystemExit during org selection")
            return []

        logging.debug("User selection input: '%s'", selection)

        if selection in ["q", ""]:
            print(f"  Skipping {msp_name}")
            logging.info("User skipped MSP %s", msp_name)
            return []
        if selection == "all":
            print("")
            print(f"  + Selected ALL {len(orgs)} organization(s) under {msp_name}:")
            for org in orgs:
                print(f"      - {org.get('name', 'Unknown')}")
            logging.info("User selected ALL %s organizations from MSP %s", len(orgs), msp_name)
            return orgs

        indices = self._parse_selection(selection, len(orgs))
        if not indices:
            print("  X Invalid selection, skipping this MSP")
            logging.warning("Invalid org selection '%s' for MSP %s", selection, msp_name)
            return []

        selected = [orgs[i] for i in indices]
        print("")
        print(f"  + Selected {len(selected)} organization(s) from {msp_name}:")
        for org in selected:
            print(f"      - {org.get('name', 'Unknown')}")
        logging.info("User selected %s organization(s) from MSP %s", len(selected), msp_name)
        return selected

    # =========================================================================
    # SELECTION PARSING UTILITIES
    # =========================================================================

    @staticmethod
    def _parse_selection(selection: str, max_items: int) -> list[int]:
        """Parse selection string into list of indices."""
        indices: list[int] = []
        parts = selection.replace(",", " ").split()

        for part in parts:
            indices.extend(OrgLevelAPFirmwareUpgrader._parse_selection_part(part, max_items))

        through_indices = OrgLevelAPFirmwareUpgrader._parse_through_range(selection, max_items)
        if through_indices:
            indices = through_indices

        return sorted(set(indices))

    @staticmethod
    def _parse_selection_part(part: str, max_items: int) -> list[int]:
        """Parse a single selection part (number or range)."""
        if "-" in part and not part.startswith("-"):
            try:
                start, end = part.split("-", 1)
                start_idx, end_idx = int(start) - 1, int(end) - 1
                if 0 <= start_idx <= end_idx < max_items:
                    return list(range(start_idx, end_idx + 1))
            except ValueError:
                pass
            return []
        if "through" in part.lower():
            return []
        try:
            idx = int(part) - 1
            if 0 <= idx < max_items:
                return [idx]
        except ValueError:
            pass
        return []

    @staticmethod
    def _parse_through_range(selection: str, max_items: int) -> list[int]:
        """Parse 'X through Y' range from selection string."""
        through_match = re.search(r"(\d+)\s*through\s*(\d+)", selection, re.IGNORECASE)
        if not through_match:
            return []
        try:
            start_idx = int(through_match.group(1)) - 1
            end_idx = int(through_match.group(2)) - 1
            if 0 <= start_idx <= end_idx < max_items:
                return list(range(start_idx, end_idx + 1))
        except ValueError:
            pass
        return []

    @staticmethod
    def _print_msp_summary(results: list[dict[str, Any]], dry_run: bool) -> None:
        """Print summary of MSP multi-org upgrade."""
        print("")
        print("=" * 70)
        print("  MSP MULTI-ORG UPGRADE SUMMARY")
        print("=" * 70)

        if dry_run:
            print("  >> DRY-RUN MODE - No actual changes made <<")

        total_success = sum(r["success"] for r in results)
        total_failed = sum(r["failed"] for r in results)
        total_devices = sum(r["devices"] for r in results)

        print(f"\n  Organizations: {len(results)}")
        print(f"  API Calls: {total_success} success, {total_failed} failed")
        print(f"  Devices: {total_devices}")

        print("\n  Per-Org Breakdown:")
        for result in results:
            status = "OK" if result["failed"] == 0 else "PARTIAL"
            print(f"    {result['org_name']}: {result['devices']} devices ({status})")

    # =========================================================================
    # MAIN EXECUTE WORKFLOW
    # =========================================================================

    def execute(self) -> None:
        """Execute the org-level AP firmware upgrade workflow."""
        logging.info("Starting org-level AP firmware upgrade...")
        logging.debug("OrgLevelAPFirmwareUpgrader.execute() initiated")
        logging.debug("Using org_id: %s", self.org_id)

        self._print_execute_header()

        try:
            if not self._step1_select_site_scope():
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
            if not self._step7_confirm_and_execute():
                return
            self._step8_write_results()
        except KeyboardInterrupt:
            print("\n Operation cancelled by user.")
            logging.info("Org-level AP firmware upgrade cancelled by user interrupt")

    def _print_execute_header(self) -> None:
        """Print execute workflow header."""
        print("")
        print("=" * 70)
        print("  ORG-LEVEL AP FIRMWARE UPGRADE (Efficient Multi-Site)")
        print("=" * 70)
        print("")
        print("  This operation uses the org-level upgrade API for efficiency:")
        print("    - 1 API call per unique version (vs 1 per site per version)")
        print("    - Supports all sites or selected sites per org")
        print("    - Same upgrade strategies as site-level (big_bang, canary, etc.)")

        if self.dry_run:
            print("")
            print("  >> DRY-RUN MODE: No actual upgrades will be performed <<")
            logging.info("DRY-RUN MODE enabled - no API calls will be made")

    # =========================================================================
    # STEP 1: SITE SCOPE SELECTION
    # =========================================================================

    def _step1_select_site_scope(self) -> bool:
        """Select whether to upgrade all sites or specific sites."""
        logging.debug("Entering _step1_select_site_scope()")
        print("")
        print("-" * 70)
        print("  STEP 1: Site Scope Selection")
        print("-" * 70)
        print("")
        print("  Select scope for this organization:")
        print("   [1] All sites - upgrade APs across ALL sites in this org")
        print("   [2] Select sites - choose specific sites to include")
        print("")

        try:
            choice = self._input_fn("  Select scope (1 or 2): ", "org_scope_select").strip()
        except SystemExit:
            logging.debug("SystemExit during site scope selection")
            return False

        logging.debug("Site scope selection: %s", choice)

        if choice == "1":
            self.target_all_sites = True
            self.selected_site_ids = []
            print("  + Targeting ALL sites in organization")
            logging.info("Org-level upgrade: targeting all sites")
            return True
        if choice == "2":
            return self._select_specific_sites()
        print("  X Invalid selection")
        logging.warning("Invalid site scope selection")
        return False

    def _select_specific_sites(self) -> bool:
        """Allow user to select specific sites for upgrade."""
        print("")
        print("  Fetching sites from organization...")

        sites_data = self._fetch_sorted_sites()
        if not sites_data:
            return False

        self._display_site_list(sites_data)
        return self._collect_site_selection(sites_data)

    def _fetch_sorted_sites(self) -> list[Any] | None:
        """Fetch and sort sites by name."""
        try:
            if self._fetch_sites_fn:
                sites_data = self._fetch_sites_fn(self.org_id)
            else:
                return None
            if not sites_data:
                print("  X No sites found in organization")
                return None
            return sorted(sites_data, key=lambda s: s.get("name", "").lower())
        except Exception as error:
            print(f"  X Error fetching sites: {error}")
            logging.error("Failed to fetch sites for org-level upgrade: %s", error)
            return None

    def _display_site_list(self, sites_data: list[Any]) -> None:
        """Display numbered site list."""
        print(f"  Found {len(sites_data)} site(s):")
        print("")
        for idx, site in enumerate(sites_data, start=1):
            print(f"    {idx:>4}. {site.get('name', 'Unknown')}")
        print("")
        print("  Selection: single '1', multiple '1,3,5', range '1-3', 'all', or 'q'")
        print("")

    def _collect_site_selection(self, sites_data: list[Any]) -> bool:
        """Collect and process site selection from user."""
        try:
            selection = self._input_fn("  Select site(s): ", "site_multi_select").strip().lower()
        except SystemExit:
            return False

        if selection in ["q", ""]:
            return False

        if selection == "all":
            self.target_all_sites = True
            self.selected_site_ids = []
            print("  + Targeting ALL sites")
            return True

        return self._apply_site_selection(sites_data, selection)

    def _apply_site_selection(self, sites_data: list[Any], selection: str) -> bool:
        """Apply parsed site selection."""
        selected_indices = self._parse_selection_input(selection, len(sites_data))
        if not selected_indices:
            print("  X Invalid selection")
            return False

        self.target_all_sites = False
        self.selected_sites = [sites_data[idx] for idx in selected_indices]
        self.selected_site_ids = [site["id"] for site in self.selected_sites]
        print(f"  + Selected {len(self.selected_site_ids)} site(s)")
        return True

    def _parse_selection_input(self, selection: str, max_items: int) -> list[int]:
        """Parse selection input with support for ranges and multiple selections."""
        return self._parse_selection(selection, max_items)

    # =========================================================================
    # STEP 2: DEVICE DISCOVERY
    # =========================================================================

    def _step2_discover_aps(self) -> bool:
        """Discover APs from selected scope."""
        logging.debug("Entering _step2_discover_aps()")
        print("")
        print("-" * 70)
        print("  STEP 2: Device Discovery")
        print("-" * 70)

        if self.target_all_sites:
            print("  Fetching all APs from organization...")
            logging.debug("Fetching APs from all sites in organization")
            return self._fetch_org_aps()
        print(f"  Fetching APs from {len(self.selected_site_ids)} selected site(s)...")
        logging.debug("Fetching APs from %s selected sites", len(self.selected_site_ids))
        return self._fetch_selected_sites_aps()

    def _fetch_org_aps(self) -> bool:
        """Fetch all APs from the organization with full pagination."""
        logging.debug("Entering _fetch_org_aps()")
        if self.apisession is None or self.org_id is None:
            print("  X API session or org_id not initialized")
            logging.error("API session or org_id not initialized for AP fetch")
            return False

        try:
            devices_data = self._get_org_inventory()
            if not devices_data:
                print("  X Failed to retrieve devices")
                logging.warning("No device data returned from org inventory")
                return False

            self.all_aps = self._filter_ap_devices(devices_data)
            if not self.all_aps:
                print("  X No access points found in organization")
                logging.warning("No APs found in organization")
                return False

            logging.info("Discovered %s APs in organization", len(self.all_aps))
            return self._organize_aps_by_model()
        except Exception as error:
            print(f"  X Error fetching devices: {error}")
            logging.error("Failed to fetch org devices: %s", error)
            return False

    def _get_org_inventory(self) -> list[Any]:
        """Retrieve org inventory with pagination."""
        if self.apisession is None:
            print("  X API session not initialized")
            return []
        import mistapi

        org_inventory_api = importlib.import_module("mistapi.api.v1.orgs.inventory")
        response = org_inventory_api.getOrgInventory(self.apisession, self.org_id, type="ap", limit=1000)

        if not response or not hasattr(response, "data"):
            return []

        devices_data = mistapi.get_all(response=response, mist_session=self.apisession)
        if not isinstance(devices_data, list):
            return [devices_data] if devices_data else []
        return devices_data

    @staticmethod
    def _filter_ap_devices(devices_data: list[Any]) -> list[Any]:
        """Filter list to only AP devices."""
        return [d for d in devices_data if d.get("type") == "ap" or d.get("model", "").startswith("AP")]

    def _fetch_selected_sites_aps(self) -> bool:
        """Fetch APs from selected sites only."""
        try:
            self.all_aps = self._collect_aps_from_sites()

            if not self.all_aps:
                print("  X No access points found in selected sites")
                return False

            return self._organize_aps_by_model()

        except Exception as error:
            print(f"  X Error fetching devices: {error}")
            logging.error("Failed to fetch site devices: %s", error)
            return False

    def _collect_aps_from_sites(self) -> list[Any]:
        """Collect APs from each selected site."""
        all_aps: list[Any] = []
        for site in self.selected_sites:
            if self._check_stop_fn and self._check_stop_fn():
                break
            site_aps = self._fetch_site_aps(site["id"], site.get("name", "Unknown"))
            all_aps.extend(site_aps)
        return all_aps

    def _fetch_site_aps(self, site_id: str, site_name: str) -> list[Any]:
        """Fetch APs from a single site."""
        print(f"    Fetching APs from {site_name}...")

        import mistapi.api.v1.sites.devices

        response = mistapi.api.v1.sites.devices.listSiteDevices(self.apisession, site_id, type="ap")
        if not response or not hasattr(response, "data") or not response.data:
            return []

        site_aps = response.data if isinstance(response.data, list) else [response.data]
        for ap in site_aps:
            ap["_site_id"] = site_id
            ap["_site_name"] = site_name
        return site_aps

    def _organize_aps_by_model(self) -> bool:
        """Organize discovered APs by model."""
        for ap in self.all_aps:
            model = ap.get("model", "Unknown")
            if model not in self.aps_by_model:
                self.aps_by_model[model] = []
            self.aps_by_model[model].append(ap)

        print(f"  + Found {len(self.all_aps)} AP(s) across {len(self.aps_by_model)} model(s)")
        for model, aps in sorted(self.aps_by_model.items()):
            print(f"      {model}: {len(aps)} device(s)")

        return True

    # =========================================================================
    # STEP 3: FIRMWARE STATS
    # =========================================================================

    def _step3_fetch_firmware_stats(self) -> bool:
        """Fetch current firmware versions for all discovered APs."""
        logging.debug("Entering _step3_fetch_firmware_stats()")
        self._print_step3_header()

        if self.apisession is None or self.org_id is None:
            print("  X API session or org_id not initialized")
            logging.error("API session or org_id not initialized for firmware stats")
            return False

        try:
            self._populate_ap_versions()
            logging.info("Retrieved firmware versions for %s devices", len(self.ap_versions))
            self._display_version_distribution()
            return True
        except Exception as error:
            print(f"  X Error fetching firmware stats: {error}")
            logging.error("Failed to fetch firmware stats: %s", error)
            return False

    def _print_step3_header(self) -> None:
        """Print Step 3 header."""
        print("")
        print("-" * 70)
        print("  STEP 3: Current Firmware Versions")
        print("-" * 70)
        print("  Fetching device firmware versions...")

    def _populate_ap_versions(self) -> None:
        """Populate ap_versions dict from org stats API."""
        if self.apisession is None:
            return
        import mistapi

        org_stats_api = importlib.import_module("mistapi.api.v1.orgs.stats")
        response = org_stats_api.listOrgDevicesStats(self.apisession, self.org_id, type="ap", limit=1000)

        if not response or not hasattr(response, "data"):
            return

        stats_data = mistapi.get_all(response=response, mist_session=self.apisession)
        if not isinstance(stats_data, list):
            stats_data = [stats_data] if stats_data else []

        for stat in stats_data:
            mac = stat.get("mac")
            if mac:
                self.ap_versions[mac] = stat.get("version") or "Unknown"

    def _display_version_distribution(self) -> None:
        """Display firmware version distribution."""
        version_counts = self._count_versions_by_mac()
        unknown_devices = self._get_unknown_firmware_devices()

        print("  + Current firmware distribution:")
        for version, count in sorted(version_counts.items(), key=lambda x: x[0] or "", reverse=True):
            if version == "Unknown" and unknown_devices:
                device_names = [d.get("name", d.get("mac", "unnamed")) for d in unknown_devices[:5]]
                names_str = ", ".join(device_names)
                if len(unknown_devices) > 5:
                    names_str += f" +{len(unknown_devices) - 5} more"
                print(f"      {version}: {count} device(s) - likely offline ({names_str})")
            else:
                print(f"      {version}: {count} device(s)")

    def _get_unknown_firmware_devices(self) -> list[Any]:
        """Get devices with unknown firmware."""
        unknown: list[Any] = []
        for ap in self.all_aps:
            version = self.ap_versions.get(ap.get("mac"))
            if not version or version == "Unknown":
                unknown.append(ap)
        return unknown

    def _count_versions_by_mac(self) -> dict[str, int]:
        """Count devices by version using MAC address lookup."""
        version_counts: dict[str, int] = {}
        for ap in self.all_aps:
            version = self.ap_versions.get(ap.get("mac")) or "Unknown"
            version_counts[version] = version_counts.get(version, 0) + 1
        return version_counts

    # =========================================================================
    # STEP 4: AVAILABLE FIRMWARE
    # =========================================================================

    def _step4_fetch_available_firmware(self) -> bool:
        """Fetch available firmware versions for each model."""
        logging.debug("Entering _step4_fetch_available_firmware()")
        self._print_step4_header()

        if self.apisession is None or self.org_id is None:
            print("  X API session or org_id not initialized")
            logging.error("API session or org_id not initialized for firmware fetch")
            return False

        try:
            if not self._load_available_versions():
                print("  X Failed to retrieve available firmware versions")
                logging.warning("Failed to load available firmware versions")
                return False

            logging.debug("Loaded %s firmware version entries", len(self.available_versions))
            self._build_model_version_mapping()
            return self._display_version_summary()

        except Exception as error:
            print(f"  X Error fetching available firmware: {error}")
            logging.error("Failed to fetch available firmware: %s", error)
            return False

    def _print_step4_header(self) -> None:
        """Print Step 4 header."""
        print("")
        print("-" * 70)
        print("  STEP 4: Available Firmware Versions")
        print("-" * 70)
        print("  Fetching available firmware for each model...")

    def _load_available_versions(self) -> bool:
        """Load available firmware versions from API."""
        if self.apisession is None:
            print("  X API session not initialized")
            return False
        org_devices_api = importlib.import_module("mistapi.api.v1.orgs.devices")
        response = org_devices_api.listOrgAvailableDeviceVersions(self.apisession, self.org_id, type="ap")

        if not response or not hasattr(response, "data"):
            return False

        self.available_versions = response.data if isinstance(response.data, list) else []
        return True

    def _build_model_version_mapping(self) -> None:
        """Build model-to-versions mapping from available_versions."""
        for version_info in self.available_versions:
            if not isinstance(version_info, dict):
                continue
            model = version_info.get("model")
            version = version_info.get("version")
            if model and version:
                if model not in self.model_version_ranges:
                    self.model_version_ranges[model] = []
                self.model_version_ranges[model].append(version)

    def _display_version_summary(self) -> bool:
        """Display version summary for discovered models."""
        models_found = 0
        for model in self.aps_by_model:
            if model in self.model_version_ranges:
                models_found += 1
                print(f"    {model}: {len(self.model_version_ranges[model])} version(s) available")
            else:
                print(f"    {model}: No firmware versions found")

        if models_found == 0:
            print("  X No firmware versions available for discovered models")
            return False

        print(f"  + Loaded firmware data for {models_found} model(s)")
        return True

    # =========================================================================
    # STEP 5: VERSION SELECTION
    # =========================================================================

    def _step5_select_firmware_versions(self) -> bool:
        """Let user select firmware version for each model."""
        logging.debug("Entering _step5_select_firmware_versions()")
        print("")
        print("-" * 70)
        print("  STEP 5: Firmware Version Selection")
        print("-" * 70)

        model_selections = self._collect_model_selections()

        if not model_selections:
            print("\n  X No upgrades selected")
            logging.warning("No firmware versions selected by user")
            return False

        logging.info("User selected firmware for %s model(s)", len(model_selections))
        self._organize_by_version(model_selections)
        return True

    def _collect_model_selections(self) -> dict[str, Any]:
        """Collect firmware version selections for each model."""
        model_selections: dict[str, Any] = {}

        for model, devices in sorted(self.aps_by_model.items()):
            selection = self._process_single_model(model, devices)
            if selection is None:
                return {}
            if selection:
                model_selections[model] = selection

        return model_selections

    def _process_single_model(self, model: str, devices: list[Any]) -> dict[str, Any] | None:
        """Process version selection for a single model."""
        model_versions = self._get_versions_for_model(model)
        if not model_versions:
            print(f"  ! No firmware versions found for {model} - skipping")
            return {}

        current_versions = set(self.ap_versions.get(d.get("mac"), "Unknown") for d in devices)
        self._display_model_options(model, devices, model_versions, current_versions)

        user_input = self._get_version_selection_input(model_versions)
        if user_input is None:
            return None
        if user_input == "s":
            print(f"    Skipping {model}")
            return {}

        return self._apply_version_selection(model, devices, model_versions, user_input)

    def _display_model_options(
        self,
        model: str,
        devices: list[Any],
        model_versions: list[Any],
        current_versions: set[str],
    ) -> None:
        """Display available firmware versions for a model."""
        print(f"\n  Model: {model} ({len(devices)} devices)")
        self._print_current_versions(devices, current_versions)
        print("    Available versions:")
        self._print_version_list(model_versions, current_versions)

    def _print_current_versions(self, devices: list[Any], current_versions: set[str]) -> None:
        """Print current version info including offline devices."""
        if "Unknown" not in current_versions:
            print(f"    Current: {', '.join(sorted(current_versions, reverse=True))}")
            return

        unknown_devs = [d for d in devices if self.ap_versions.get(d.get("mac"), "Unknown") == "Unknown"]
        known_versions = sorted([v for v in current_versions if v != "Unknown"], reverse=True)
        offline_names = ", ".join([d.get("name", d.get("mac", "unnamed")[:8]) for d in unknown_devs[:3]])
        if len(unknown_devs) > 3:
            offline_names += f" +{len(unknown_devs) - 3} more"
        if known_versions:
            print(f"    Current: {', '.join(known_versions)}")
        print(f"    Offline ({len(unknown_devs)}): {offline_names}")

    @staticmethod
    def _print_version_list(model_versions: list[Any], current_versions: set[str]) -> None:
        """Print numbered list of available firmware versions."""
        for idx, version_info in enumerate(model_versions):
            version_num = version_info.get("version", "Unknown")
            indicators: list[str] = []
            if version_info.get("recommended"):
                indicators.append("RECOMMENDED")
            if version_num in current_versions:
                indicators.append("CURRENT")
            ind_text = f" [{', '.join(indicators)}]" if indicators else ""
            print(f"      [{idx}] {version_num}{ind_text}")

    def _get_version_selection_input(self, model_versions: list[Any]) -> str | None:
        """Get user input for version selection."""
        try:
            return (
                self._input_fn(
                    f"    Select version (0-{len(model_versions) - 1}, 's' to skip): ",
                    "version_select",
                )
                .strip()
                .lower()
            )
        except SystemExit:
            return None

    def _apply_version_selection(
        self,
        model: str,
        devices: list[Any],
        model_versions: list[Any],
        user_input: str,
    ) -> dict[str, Any]:
        """Apply user's version selection for a model."""
        try:
            idx = int(user_input)
            if not (0 <= idx < len(model_versions)):
                print("    Invalid input - skipping model")
                return {}
        except ValueError:
            print("    Invalid input - skipping model")
            return {}

        selected = model_versions[idx]
        target_version = selected.get("version")

        devices_needing = [d for d in devices if self.ap_versions.get(d.get("mac")) != target_version]
        if not devices_needing:
            print(f"    All {model} devices already at {target_version}")
            return {}

        skipped = len(devices) - len(devices_needing)
        if skipped:
            print(f"    Skipping {skipped} device(s) already at target")
            self.skipped_already_at_target += skipped

        print(f"    + Selected {target_version} for {len(devices_needing)} device(s)")
        return {"version": target_version, "devices": devices_needing}

    def _get_versions_for_model(self, model: str) -> list[Any]:
        """Get sorted versions for a model."""
        versions: list[Any] = []
        for version_entry in self.available_versions:
            if isinstance(version_entry, dict):
                models = version_entry.get("models", [])
                single = version_entry.get("model")
                if model in models or single == model:
                    versions.append(version_entry)

        seen: set[str] = set()
        unique: list[Any] = []
        for version_entry in versions:
            num = version_entry.get("version")
            if num and num not in seen:
                seen.add(num)
                unique.append(version_entry)

        try:
            unique.sort(key=lambda x: tuple(map(int, x.get("version", "0").split("."))), reverse=True)
        except ValueError:
            unique.sort(key=lambda x: x.get("version", ""), reverse=True)

        return unique

    def _organize_by_version(self, model_selections: dict[str, Any]) -> None:
        """Reorganize selections by version for org-level API."""
        for model, data in model_selections.items():
            version = data["version"]
            device_ids = [d.get("id") for d in data["devices"] if d.get("id")]

            if version not in self.upgrade_plan:
                self.upgrade_plan[version] = {"models": [], "device_ids": []}

            self.upgrade_plan[version]["models"].append(model)
            self.upgrade_plan[version]["device_ids"].extend(device_ids)

        print("\n  Upgrade Plan Summary (grouped by version):")
        for version, data in sorted(self.upgrade_plan.items()):
            models_str = ", ".join(data["models"])
            print(f"    {version}: {len(data['device_ids'])} device(s) ({models_str})")

        print("\n  API Efficiency:")
        print(f"    - Org-level calls needed: {len(self.upgrade_plan)}")
        if not self.target_all_sites:
            site_count = len(self.selected_site_ids)
            site_level_calls = site_count * len(self.upgrade_plan)
            print(f"    - Site-level would need: ~{site_level_calls} calls")
            print(f"    - Savings: {site_level_calls - len(self.upgrade_plan)} fewer API calls")

    # =========================================================================
    # STEP 6: UPGRADE CONFIGURATION
    # =========================================================================

    def _step6_configure_upgrade(self) -> bool:
        """Configure upgrade parameters."""
        logging.debug("Entering _step6_configure_upgrade()")
        self._print_step6_header()

        if not self._configure_download_strategy():
            logging.info("Download strategy configuration cancelled")
            return False
        if not self._configure_reboot_strategy():
            logging.info("Reboot strategy configuration cancelled")
            return False
        if not self._configure_scheduling():
            logging.info("Scheduling configuration cancelled")
            return False
        if not self._configure_p2p():
            logging.info("P2P configuration cancelled")
            return False

        if not self._apply_default_settings():
            return False
        self._display_configuration()
        logging.info("Upgrade configuration complete: %s", self.upgrade_config)
        return True

    def _print_step6_header(self) -> None:
        """Print Step 6 header."""
        print("")
        print("-" * 70)
        print("  STEP 6: Upgrade Configuration")
        print("-" * 70)

    def _configure_download_strategy(self) -> bool:
        """Configure download strategy."""
        print("\n  Download Strategy:")
        print("    [1] big_bang - Download to all devices simultaneously")
        print("    [2] serial - Download to one device at a time")
        print("    [3] canary - Download in phases")

        try:
            choice = self._input_fn("  Select (1-3) [1]: ", "dl_strategy").strip() or "1"
        except SystemExit:
            return False

        strategies = {"1": "big_bang", "2": "serial", "3": "canary"}
        self.upgrade_config["download_strategy"] = strategies.get(choice, "big_bang")
        return True

    def _configure_reboot_strategy(self) -> bool:
        """Configure reboot strategy."""
        print("\n  Reboot Strategy:")
        print("    [1] big_bang - Reboot all devices simultaneously")
        print("    [2] serial - Reboot one device at a time")
        print("    [3] rrm - RF-aware sequential reboot")
        print("    [4] canary - Reboot in phases")

        try:
            choice = self._input_fn("  Select (1-4) [1]: ", "rb_strategy").strip() or "1"
        except SystemExit:
            return False

        strategies = {"1": "big_bang", "2": "serial", "3": "rrm", "4": "canary"}
        self.upgrade_config["reboot_strategy"] = strategies.get(choice, "big_bang")
        return True

    def _parse_relative_offset(self, offset_str: str) -> timedelta | None:
        """Parse relative time offset like 'in 15 minutes', '+3h', '2 days'."""
        offset_str = offset_str.strip().lower()

        if offset_str.startswith("in "):
            offset_str = offset_str[3:].strip()
        elif offset_str.startswith("+"):
            offset_str = offset_str[1:].strip()

        patterns = [
            (r"^(\d+)\s*m(?:in(?:ute)?s?)?$", "minutes"),
            (r"^(\d+)\s*h(?:(?:ou)?rs?)?$", "hours"),
            (r"^(\d+)\s*d(?:ays?)?$", "days"),
        ]

        for pattern, unit in patterns:
            match = re.match(pattern, offset_str)
            if match:
                value = int(match.group(1))
                if unit == "minutes":
                    return timedelta(minutes=value)
                if unit == "hours":
                    return timedelta(hours=value)
                if unit == "days":
                    return timedelta(days=value)

        return None

    def _parse_time_input(
        self,
        time_str: str,
        base_datetime: datetime | None = None,
        is_for_reboot: bool = False,
    ) -> str | None:
        """Parse time input to ISO 8601 format."""
        if not time_str or time_str.lower() in ["now", "immediate", ""]:
            return None

        time_str = time_str.strip()
        use_site_local = self.upgrade_config.get("use_site_local_time", False)

        relative_result = self._try_parse_relative(time_str, base_datetime, is_for_reboot, use_site_local)
        if relative_result is not None:
            return relative_result if relative_result != "" else None

        after_result = self._try_parse_after(time_str, base_datetime, is_for_reboot, use_site_local)
        if after_result is not None:
            return after_result if after_result != "" else None

        return self._parse_absolute_time(time_str, use_site_local)

    def _try_parse_relative(
        self,
        time_str: str,
        base_datetime: datetime | None,
        is_for_reboot: bool,
        use_site_local: bool,
    ) -> str | None:
        """Try parsing as relative offset. Returns None if not relative, '' to signal no result."""
        relative_offset = self._parse_relative_offset(time_str)
        if not relative_offset:
            return None
        if use_site_local and is_for_reboot:
            print("    ! Relative times not supported for reboot in site-local mode. Use HH:MM format.")
            return ""
        target_dt = (base_datetime or datetime.now(UTC)) + relative_offset
        return target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _try_parse_after(
        self,
        time_str: str,
        base_datetime: datetime | None,
        is_for_reboot: bool,
        use_site_local: bool,
    ) -> str | None:
        """Try parsing 'X after' format. Returns None if not matching, '' for no result."""
        if "after" not in time_str.lower():
            return None
        if use_site_local and is_for_reboot:
            print("    ! Relative times not supported for reboot in site-local mode. Use HH:MM format.")
            return ""
        after_idx = time_str.lower().find("after")
        time_portion = time_str[:after_idx].strip()
        relative_offset = self._parse_relative_offset(time_portion)
        if relative_offset and base_datetime:
            target_dt = base_datetime + relative_offset
            return target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return ""

    def _parse_absolute_time(self, time_str: str, use_site_local: bool) -> str | None:
        """Parse absolute HH:MM time input."""
        is_utc = time_str.upper().endswith(" UTC")
        if is_utc:
            time_str = time_str[:-4].strip()

        try:
            time_parts = time_str.split(":")
            if len(time_parts) != 2:
                return None
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return None

            if use_site_local:
                return self._format_site_local_time(hour, minute)
            return self._format_utc_time(hour, minute, is_utc)
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _format_site_local_time(hour: int, minute: int) -> str:
        """Format time for site-local scheduling."""
        now = datetime.now()
        target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_dt <= now:
            target_dt += timedelta(days=1)
        return target_dt.strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _format_utc_time(hour: int, minute: int, is_utc: bool) -> str:
        """Format time for UTC scheduling."""
        if is_utc:
            now = datetime.now(UTC)
            target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += timedelta(days=1)
            return target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        now_utc = datetime.now(UTC)
        local_now = datetime.now()
        target_local = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_local <= local_now:
            target_local += timedelta(days=1)
        utc_offset = now_utc.replace(tzinfo=None) - local_now
        target_utc = target_local + utc_offset
        return target_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _parse_download_datetime(self, time_str: str) -> datetime | None:
        """Parse download time as datetime for reboot offset calculation."""
        if not time_str or time_str.lower() in ["now", "immediate", ""]:
            return None

        time_str = time_str.strip()

        relative_offset = self._parse_relative_offset(time_str)
        if relative_offset:
            return datetime.now(UTC) + relative_offset

        return self._parse_download_absolute(time_str)

    def _parse_download_absolute(self, time_str: str) -> datetime | None:
        """Parse absolute time string into datetime for download scheduling."""
        is_utc = time_str.upper().endswith(" UTC")
        if is_utc:
            time_str = time_str[:-4].strip()

        try:
            time_parts = time_str.split(":")
            if len(time_parts) != 2:
                return None
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return None

            if is_utc:
                return self._resolve_utc_datetime(hour, minute)
            return self._resolve_local_to_utc_datetime(hour, minute)
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _resolve_utc_datetime(hour: int, minute: int) -> datetime:
        """Resolve hour:minute in UTC to next occurrence."""
        now = datetime.now(UTC)
        target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_dt <= now:
            target_dt += timedelta(days=1)
        return target_dt

    @staticmethod
    def _resolve_local_to_utc_datetime(hour: int, minute: int) -> datetime:
        """Resolve local hour:minute to UTC datetime."""
        now_utc = datetime.now(UTC)
        local_now = datetime.now()
        target_local = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_local <= local_now:
            target_local += timedelta(days=1)
        offset = now_utc.replace(tzinfo=None) - local_now
        return target_local + offset

    def _configure_scheduling(self) -> bool:
        """Configure download and reboot scheduling."""
        if not self._configure_time_mode():
            return False
        if not self._configure_download_schedule():
            return False
        return self._configure_reboot_schedule()

    def _configure_time_mode(self) -> bool:
        """Prompt for UTC vs site-local time mode."""
        print("\n  Time Zone Mode:")
        print("    [1] Global (UTC) - All sites upgrade at the same instant")
        print("    [2] Site-Local - Each site upgrades at that time in its timezone")
        print("        Example: '21:00' site-local = 9pm Eastern, 9pm Pacific, 9pm Central, etc.")

        try:
            mode_input = self._input_fn("  Select time mode (1-2) [1]: ", "time_mode").strip() or "1"
        except SystemExit:
            return False

        self.upgrade_config["use_site_local_time"] = mode_input == "2"
        if self.upgrade_config["use_site_local_time"]:
            print("    + Using site-local time (rolling upgrade across timezones)")
        else:
            print("    + Using global UTC time (all sites at same instant)")
        return True

    def _configure_download_schedule(self) -> bool:
        """Prompt for download start time."""
        self._print_download_time_help()

        try:
            download_input = self._input_fn("  Download start time [now]: ", "sched_download").strip()
        except SystemExit:
            return False

        self.upgrade_config["start_datetime"] = self._parse_time_input(download_input, is_for_reboot=False)
        self.upgrade_config["_download_dt"] = self._parse_download_datetime(download_input)
        self._print_download_confirmation()
        return True

    def _print_download_time_help(self) -> None:
        """Print download scheduling help text."""
        print("\n  Download Scheduling:")
        if self.upgrade_config.get("use_site_local_time"):
            print("    Absolute: 'HH:MM' (24-hour, site-local)")
            print("    Relative: 'in 15 minutes', '+3h', '+2m' (converts to UTC)")
            print("    Note: Relative times start download immediately across all sites;")
            print("          HH:MM schedules download at that time in each site's timezone")
        else:
            print("    Absolute: '21:30' (your local) or '19:45 UTC'")
            print("    Relative: 'in 15 minutes', 'in 3 hours', 'in 2 days', '+3h'")
        print("    Immediate: blank or 'now'")

    def _print_download_confirmation(self) -> None:
        """Print download time confirmation."""
        start_dt = self.upgrade_config.get("start_datetime")
        if start_dt:
            is_utc = start_dt.endswith("Z")
            use_site_local = self.upgrade_config.get("use_site_local_time", False)
            if is_utc and use_site_local:
                print(f"    + Download scheduled: {start_dt} (UTC - immediate start)")
            else:
                time_suffix = " (site-local)" if use_site_local else " (UTC)"
                print(f"    + Download scheduled: {start_dt}{time_suffix}")
        else:
            print("    + Download: immediate")

    def _configure_reboot_schedule(self) -> bool:
        """Prompt for reboot start time."""
        self._print_reboot_time_help()

        try:
            reboot_input = self._input_fn("  Reboot start time [immediate]: ", "sched_reboot").strip()
        except SystemExit:
            return False

        download_dt = self.upgrade_config.pop("_download_dt", None)
        parsed_reboot = self._parse_time_input(reboot_input, base_datetime=download_dt, is_for_reboot=True)
        self.upgrade_config["reboot_datetime"] = parsed_reboot if parsed_reboot else None

        if self.upgrade_config["reboot_datetime"]:
            time_suffix = " (site-local)" if self.upgrade_config.get("use_site_local_time") else " (UTC)"
            print(f"    + Reboot scheduled: {self.upgrade_config['reboot_datetime']}{time_suffix}")
        else:
            print("    + Reboot: immediate (after download completes)")

        return True

    def _print_reboot_time_help(self) -> None:
        """Print reboot scheduling help text."""
        print("\n    Reboot time options:")
        if self.upgrade_config.get("use_site_local_time"):
            print("      Time format: 'HH:MM' (24-hour, site-local)")
            print("      Example: '02:00' = 2am at each site's local time")
        else:
            print("      Absolute: '21:30', '19:45 UTC'")
            if self.upgrade_config.get("start_datetime"):
                print("      Relative to download: '+4h', '4 hours after', 'in 6 hours'")
        print("      Immediate (after download): blank or 'now'")

    def _apply_default_settings(self) -> bool:  # noqa: PLR0912
        """Apply default upgrade settings with optional user prompts."""
        uses_canary = (
            self.upgrade_config.get("download_strategy") == "canary"
            or self.upgrade_config.get("reboot_strategy") == "canary"
        )

        if uses_canary:
            if not self._configure_canary_phases():
                return False

        if not self._configure_failure_threshold():
            return False

        self.upgrade_config["force"] = False
        return True

    def _configure_canary_phases(self) -> bool:
        """Configure canary phase percentages."""
        print("\n  Canary Configuration:")
        print("    Canary phases define what percentage of devices to upgrade in each wave.")
        print("    Example: '1,2,4,8,16,32,64,100' means 1%, then 2%, then 4%, etc.")
        try:
            phases_input = self._input_fn(
                "  Canary phases (comma-separated) [1,2,4,8,16,32,64,100]: ", "canary_phases"
            ).strip()
        except SystemExit:
            return False

        if phases_input:
            try:
                phases = [int(p.strip()) for p in phases_input.split(",") if p.strip()]
                if phases and all(0 < p <= 100 for p in phases):
                    self.upgrade_config["canary_phases"] = phases
                else:
                    print("    ! Invalid phases, using default [1,2,4,8,16,32,64,100]")
                    self.upgrade_config["canary_phases"] = [1, 2, 4, 8, 16, 32, 64, 100]
            except ValueError:
                print("    ! Invalid input, using default [1,2,4,8,16,32,64,100]")
                self.upgrade_config["canary_phases"] = [1, 2, 4, 8, 16, 32, 64, 100]
        else:
            self.upgrade_config["canary_phases"] = [1, 2, 4, 8, 16, 32, 64, 100]
        return True

    def _configure_failure_threshold(self) -> bool:
        """Configure max failure percentage."""
        print("\n  Failure Threshold:")
        print("    Maximum percentage of devices that can fail before aborting upgrade.")
        try:
            failure_input = self._input_fn("  Max failure percentage [7]: ", "max_failure").strip()
        except SystemExit:
            return False

        if failure_input:
            try:
                failure_pct = int(failure_input)
                if 0 <= failure_pct <= 100:
                    self.upgrade_config["max_failure_percentage"] = failure_pct
                else:
                    print("    ! Invalid percentage, using default 7%")
                    self.upgrade_config["max_failure_percentage"] = 7
            except ValueError:
                print("    ! Invalid input, using default 7%")
                self.upgrade_config["max_failure_percentage"] = 7
        else:
            self.upgrade_config["max_failure_percentage"] = 7
        return True

    def _configure_p2p(self) -> bool:  # noqa: C901, PLR0912
        """Configure peer-to-peer firmware distribution settings."""
        print("\n  Peer-to-Peer Configuration:")
        print("    P2P allows APs to share firmware with nearby APs to reduce bandwidth.")
        try:
            p2p_input = self._input_fn("  Enable P2P firmware sharing? (Y/n) [Y]: ", "p2p_enable").strip().lower()
        except SystemExit:
            return False

        self.upgrade_config["enable_p2p"] = p2p_input not in ["n", "no"]

        if self.upgrade_config["enable_p2p"]:
            print("    + P2P enabled")
            if not self._configure_p2p_cluster_size():
                return False
            if not self._configure_p2p_parallelism():
                return False
        else:
            print("    + P2P disabled")
            self.upgrade_config["p2p_cluster_size"] = 5
            self.upgrade_config["p2p_parallelism"] = 100

        return True

    def _configure_p2p_cluster_size(self) -> bool:
        """Configure P2P cluster size."""
        try:
            cluster_input = self._input_fn("  P2P cluster size (APs per cluster) [5]: ", "p2p_cluster").strip()
        except SystemExit:
            return False

        if cluster_input:
            try:
                cluster_size = int(cluster_input)
                if 1 <= cluster_size <= 100:
                    self.upgrade_config["p2p_cluster_size"] = cluster_size
                else:
                    print("    ! Invalid size, using default 5")
                    self.upgrade_config["p2p_cluster_size"] = 5
            except ValueError:
                print("    ! Invalid input, using default 5")
                self.upgrade_config["p2p_cluster_size"] = 5
        else:
            self.upgrade_config["p2p_cluster_size"] = 5
        return True

    def _configure_p2p_parallelism(self) -> bool:
        """Configure P2P parallelism."""
        try:
            parallel_input = self._input_fn(
                "  P2P parallelism (simultaneous site batches) [100]: ", "p2p_parallelism"
            ).strip()
        except SystemExit:
            return False

        if parallel_input:
            try:
                parallelism = int(parallel_input)
                if 1 <= parallelism <= 500:
                    self.upgrade_config["p2p_parallelism"] = parallelism
                else:
                    print("    ! Invalid value, using default 100")
                    self.upgrade_config["p2p_parallelism"] = 100
            except ValueError:
                print("    ! Invalid input, using default 100")
                self.upgrade_config["p2p_parallelism"] = 100
        else:
            self.upgrade_config["p2p_parallelism"] = 100
        return True

    def _display_configuration(self) -> None:
        """Display configured upgrade settings."""
        print("\n  + Configuration:")
        print(f"      Download Strategy: {self.upgrade_config['download_strategy']}")
        print(f"      Reboot Strategy: {self.upgrade_config['reboot_strategy']}")

        use_site_local = self.upgrade_config.get("use_site_local_time", False)
        time_mode = "Site-Local" if use_site_local else "Global (UTC)"
        print(f"      Time Mode: {time_mode}")

        start_dt = self.upgrade_config.get("start_datetime")
        reboot_dt = self.upgrade_config.get("reboot_datetime")
        print(f"      Download Time: {start_dt if start_dt else 'Immediate'}")
        print(f"      Reboot Time: {reboot_dt if reboot_dt else ('Same as download' if start_dt else 'Immediate')}")
        print(f"      Max Failure: {self.upgrade_config['max_failure_percentage']}%")
        if "canary_phases" in self.upgrade_config:
            phases_str = ", ".join(str(p) for p in self.upgrade_config["canary_phases"])
            print(f"      Canary Phases: [{phases_str}]%")
        if self.upgrade_config.get("enable_p2p"):
            print(
                f"      P2P Enabled: Yes (cluster: {self.upgrade_config.get('p2p_cluster_size', 5)}, "
                f"parallel: {self.upgrade_config.get('p2p_parallelism', 100)})"
            )
        else:
            print("      P2P Enabled: No")

    # =========================================================================
    # STEP 7: CONFIRM AND EXECUTE
    # =========================================================================

    def _step7_confirm_and_execute(self) -> bool:
        """Confirm upgrade plan and execute."""
        logging.debug("Entering _step7_confirm_and_execute()")
        self._print_step7_header()
        self._display_upgrade_summary()
        self._display_version_breakdown()

        if self.dry_run:
            print("\n  >> DRY-RUN: Simulating execution <<")
            logging.debug("Executing dry-run simulation")
            return self._execute_dry_run()

        return self._confirm_and_execute_live()

    def _print_step7_header(self) -> None:
        """Print Step 7 header."""
        print("")
        print("-" * 70)
        print("  STEP 7: Confirm and Execute")
        print("-" * 70)

    def _display_upgrade_summary(self) -> None:
        """Display upgrade summary statistics."""
        total_devices = sum(len(d["device_ids"]) for d in self.upgrade_plan.values())
        total_calls = len(self.upgrade_plan)

        print("\n  Summary:")
        print(f"    - Organization: {self.org_id[:8]}...")
        scope = "All sites" if self.target_all_sites else f"{len(self.selected_site_ids)} selected site(s)"
        print(f"    - Site Scope: {scope}")
        print(f"    - Total Devices: {total_devices}")
        print(f"    - API Calls: {total_calls}")

    def _display_version_breakdown(self) -> None:
        """Display upgrades by version."""
        print("\n  Upgrades by Version:")
        for version, data in sorted(self.upgrade_plan.items()):
            models_str = ", ".join(data["models"])
            print(f"    {version}: {len(data['device_ids'])} device(s) ({models_str})")

    def _confirm_and_execute_live(self) -> bool:
        """Confirm and execute live upgrade."""
        logging.debug("Entering _confirm_and_execute_live()")
        self._print_destructive_warning()

        try:
            confirm = self._input_fn("  Type 'UPGRADE' to proceed: ", "upgrade_confirm").strip()
        except SystemExit:
            logging.debug("SystemExit during upgrade confirmation")
            return False

        logging.debug("User confirmation input: '%s'", confirm)

        if confirm != "UPGRADE":
            print("  X Upgrade cancelled")
            logging.warning("User cancelled upgrade - confirmation failed")
            return False

        logging.info("User confirmed upgrade - executing")
        return self._execute_upgrades()

    @staticmethod
    def _print_destructive_warning() -> None:
        """Print destructive operation warning banner."""
        print("")
        print("  " + "!" * 60)
        print("  !  WARNING: DESTRUCTIVE OPERATION - FIRMWARE UPGRADE  !")
        print("  " + "!" * 60)
        print("")

    def _execute_dry_run(self) -> bool:
        """Execute dry-run simulation."""
        print("")
        for version, data in sorted(self.upgrade_plan.items()):
            self._print_dry_run_entry(version, data)
            self._record_dry_run_results(version, data)

        print("")
        print("  DRY-RUN Complete:")
        print(f"    - API Calls (simulated): {self.successful_api_calls}")
        print(f"    - Devices (simulated): {self.total_devices_upgraded}")
        return True

    def _print_dry_run_entry(self, version: str, data: dict[str, Any]) -> None:
        """Print a single dry-run upgrade entry."""
        models_str = ", ".join(data["models"])
        scope = "all_sites=true" if self.target_all_sites else f"{len(self.selected_site_ids)} site_ids"
        use_site_local = self.upgrade_config.get("use_site_local_time", False)
        start_dt = self.upgrade_config.get("start_datetime")
        reboot_dt = self.upgrade_config.get("reboot_datetime")

        print("  [DRY-RUN] Would call upgradeOrgDevices:")
        print(f"      Version: {version}")
        print(f"      Models: {models_str}")
        print(f"      Devices: {len(data['device_ids'])}")
        print(f"      Site Scope: {scope}")
        print(f"      Time Mode: {'Site-Local' if use_site_local else 'Global (UTC)'}")
        print(f"      Download Time: {start_dt or 'Immediate'}")
        print(f"      Reboot Time: {reboot_dt or ('Same as download' if start_dt else 'Immediate')}")
        self._print_dry_run_extras()

    def _print_dry_run_extras(self) -> None:
        """Print optional dry-run config details (canary, P2P)."""
        if "canary_phases" in self.upgrade_config:
            phases_str = ", ".join(str(p) for p in self.upgrade_config["canary_phases"])
            print(f"      Canary Phases: [{phases_str}]%")
        if self.upgrade_config.get("enable_p2p"):
            print(
                f"      P2P: Enabled (cluster: {self.upgrade_config.get('p2p_cluster_size', 5)}, "
                f"parallel: {self.upgrade_config.get('p2p_parallelism', 100)})"
            )

    def _record_dry_run_results(self, version: str, data: dict[str, Any]) -> None:
        """Record dry-run results for a version."""
        self.successful_api_calls += 1
        self.total_devices_upgraded += len(data["device_ids"])
        for device_id in data["device_ids"]:
            self.results.append(
                {
                    "org_id": self.org_id,
                    "version": version,
                    "device_id": device_id,
                    "status": "DRY-RUN: Would upgrade",
                }
            )

    def _execute_upgrades(self) -> bool:  # noqa: C901, PLR0912
        """Execute actual org-level upgrades."""
        logging.debug("Entering _execute_upgrades()")
        logging.info("Executing org-level AP firmware upgrades")
        print("\n  Executing org-level upgrades...")

        if self.apisession is None or self.org_id is None:
            print("  X API session or org_id not initialized")
            logging.error("API session or org_id not initialized for upgrade execution")
            return False

        org_devices_api = importlib.import_module("mistapi.api.v1.orgs.devices")

        for version, data in sorted(self.upgrade_plan.items()):
            self._execute_single_version_upgrade(version, data, org_devices_api)

        print("")
        print("  Execution Complete:")
        print(f"    - Successful API Calls: {self.successful_api_calls}")
        print(f"    - Failed API Calls: {self.failed_api_calls}")
        print(f"    - Total Devices: {self.total_devices_upgraded}")
        logging.info(
            "Org-level upgrade execution complete: successful=%s, failed=%s, total_devices=%s",
            self.successful_api_calls,
            self.failed_api_calls,
            self.total_devices_upgraded,
        )
        return True

    def _execute_single_version_upgrade(
        self,
        version: str,
        data: dict[str, Any],
        org_devices_api: Any,
    ) -> None:
        """Execute upgrade for a single version."""
        models_str = ", ".join(data["models"])
        print(f"\n  Upgrading to {version} ({models_str})...")
        logging.info("Processing upgrade to version %s for models: %s", version, models_str)

        body = self._build_upgrade_body(version, data)

        logging.debug("Upgrade API body: %s", body)
        if self._is_debug_fn():
            print(f"    API Body: {body}")

        try:
            response = org_devices_api.upgradeOrgDevices(self.apisession, self.org_id, body=body)
            self._process_upgrade_response(response, version, data)
        except Exception as exc:
            print(f"    X Error: {exc}")
            logging.error("Org-level upgrade failed for version %s: %s", version, exc)
            self.failed_api_calls += 1

    def _build_upgrade_body(self, version: str, data: dict[str, Any]) -> dict[str, Any]:
        """Build the API request body for an upgrade."""
        body: dict[str, Any] = {
            "versions": [{"firmware_type": "ap", "version": version}],
            "models": [[m] for m in data["models"]],
            "strategy": self.upgrade_config["reboot_strategy"],
            "download_strategy": self.upgrade_config["download_strategy"],
            "max_failure_percentage": self.upgrade_config["max_failure_percentage"],
        }

        if self.upgrade_config.get("start_datetime"):
            body["start_datetime"] = self.upgrade_config["start_datetime"]
        if self.upgrade_config.get("reboot_datetime"):
            body["reboot_datetime"] = self.upgrade_config["reboot_datetime"]

        if self.target_all_sites:
            body["all_sites"] = True
        else:
            body["site_ids"] = self.selected_site_ids

        if "canary_phases" in self.upgrade_config:
            body["canary_phases"] = self.upgrade_config["canary_phases"]

        if self.upgrade_config.get("enable_p2p"):
            body["enable_p2p"] = True
            body["p2p_cluster_size"] = self.upgrade_config.get("p2p_cluster_size", 5)
            body["p2p_parallelism"] = self.upgrade_config.get("p2p_parallelism", 100)

        return body

    def _process_upgrade_response(
        self,
        response: Any,
        version: str,
        data: dict[str, Any],
    ) -> None:
        """Process the response from an upgrade API call."""
        if response and hasattr(response, "data"):
            upgrade_id = response.data.get("id") if isinstance(response.data, dict) else None
            print(f"    + Upgrade initiated - ID: {upgrade_id or 'N/A'}")
            self.successful_api_calls += 1
            self.total_devices_upgraded += len(data["device_ids"])

            for device_id in data["device_ids"]:
                self.results.append(
                    {
                        "org_id": self.org_id,
                        "version": version,
                        "device_id": device_id,
                        "upgrade_id": upgrade_id,
                        "status": "Initiated",
                    }
                )
        else:
            print("    X Failed - no response data")
            self.failed_api_calls += 1

    # =========================================================================
    # STEP 8: WRITE RESULTS
    # =========================================================================

    def _step8_write_results(self) -> None:
        """Write upgrade results to file."""
        logging.debug("Entering _step8_write_results()")
        if not self.results:
            logging.debug("No results to write")
            return

        filename = os.path.join("data", "org_level_ap_upgrade_results.csv")
        try:
            if self._write_results_fn:
                self._write_results_fn(self.results, filename, api_function_name="orgLevelAPFirmwareUpgrade")
            print(f"\n  Results written to: {filename}")
            logging.info("Upgrade results written to: %s", filename)
        except Exception as exc:
            print(f"  X Failed to write results: {exc}")
            logging.error("Failed to write upgrade results: %s", exc)
