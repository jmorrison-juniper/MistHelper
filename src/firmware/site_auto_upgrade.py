"""Site auto-upgrade configuration for Mist AP firmware.

Configures auto-upgrade settings at the site level to schedule AP firmware
upgrades during maintenance windows. Supports single-org and MSP multi-org
workflows with dry-run capability.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import logging
from typing import Any

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
SafeInputFn = Any  # Callable[[str, str], str]
FetchSitesFn = Any  # Callable[[str], list[dict]]
GetOrgIdFn = Any  # Callable[[], str | None]
CheckStopFn = Any  # Callable[[], bool]
SelectMspsFn = Any  # Callable[..., Any]
SelectOrgsFromMspFn = Any  # Callable[..., Any]


class SiteAutoUpgradeConfigurator:  # pylint: disable=too-many-instance-attributes
    """Configure AP auto-upgrade settings at site level.

    Sets auto_upgrade configuration in site settings so that:
    - New APs automatically upgrade to the specified firmware
    - Existing APs upgrade during scheduled maintenance windows

    NETWORK IMPACT WARNING:
    - While auto-upgrade itself does not initiate immediate upgrades,
      scheduled upgrades WILL cause AP reboots during maintenance windows
    """

    def __init__(
        self,
        org_id: str,
        apisession: Any,
        safe_input_fn: SafeInputFn,
        fetch_sites_fn: FetchSitesFn,
        check_stop_fn: CheckStopFn,
        dry_run: bool = False,
    ) -> None:
        """Initialize the configurator.

        Args:
            org_id: Mist organization ID.
            apisession: Authenticated mistapi session.
            safe_input_fn: Function for safe user input (prompt, context) -> str.
            fetch_sites_fn: Function to fetch all sites for an org (org_id) -> list.
            check_stop_fn: Function to check for stop signal () -> bool.
            dry_run: If True, skip actual API calls.
        """
        self.org_id = org_id
        self.apisession = apisession
        self.safe_input_fn = safe_input_fn
        self.fetch_sites_fn = fetch_sites_fn
        self.check_stop_fn = check_stop_fn
        self.dry_run = dry_run
        self.all_sites: list[dict[str, Any]] = []
        self.selected_sites: list[dict[str, Any]] = []
        self.available_versions: list[Any] = []
        self.model_version_map: dict[str, list[Any]] = {}
        self.custom_versions: dict[str, str] = {}
        self.schedule: dict[str, Any] = {}
        self.current_site_versions: dict[str, str] = {}
        self.is_single_site = False
        self.msp_all_sites_mode = False
        self.org_name = ""
        self.shared_versions: dict[str, str] | None = None
        logging.debug("SiteAutoUpgradeConfigurator initialized: org_id=%s, dry_run=%s", org_id, dry_run)

    # ------------------------------------------------------------------
    # Static entry point
    # ------------------------------------------------------------------

    @staticmethod
    def execute(
        apisession: Any,
        msp_privileges: list[Any],
        safe_input_fn: SafeInputFn,
        get_org_id_fn: GetOrgIdFn,
        fetch_sites_fn: FetchSitesFn,
        check_stop_fn: CheckStopFn,
        dry_run: bool = False,
        select_msps_fn: SelectMspsFn | None = None,
        select_orgs_fn: SelectOrgsFromMspFn | None = None,
    ) -> None:
        """Entry point for menu system - checks MSP privileges.

        Args:
            apisession: Authenticated mistapi session.
            msp_privileges: List of MSP privileges (may be empty).
            safe_input_fn: Function for safe user input.
            get_org_id_fn: Function to get or prompt for org_id.
            fetch_sites_fn: Function to fetch all sites for an org.
            check_stop_fn: Function to check for stop signal.
            dry_run: If True, skip actual API calls.
            select_msps_fn: Function to select MSPs (for MSP mode).
            select_orgs_fn: Function to select orgs from MSP (for MSP mode).
        """
        logging.debug("Entering SiteAutoUpgradeConfigurator.execute()")
        logging.info("Starting Site Auto-Upgrade Configuration workflow")

        if dry_run:
            logging.info("DRY-RUN MODE enabled - no API calls will be made")

        if msp_privileges and len(msp_privileges) > 0:
            _handle_msp_mode(
                apisession=apisession,
                msp_privileges=msp_privileges,
                safe_input_fn=safe_input_fn,
                get_org_id_fn=get_org_id_fn,
                fetch_sites_fn=fetch_sites_fn,
                check_stop_fn=check_stop_fn,
                dry_run=dry_run,
                select_msps_fn=select_msps_fn,
                select_orgs_fn=select_orgs_fn,
            )
            return

        _run_single_org(
            apisession=apisession,
            safe_input_fn=safe_input_fn,
            get_org_id_fn=get_org_id_fn,
            fetch_sites_fn=fetch_sites_fn,
            check_stop_fn=check_stop_fn,
            dry_run=dry_run,
        )

    # ------------------------------------------------------------------
    # MSP mode helpers
    # ------------------------------------------------------------------

    def run_msp_mode(self) -> tuple[bool, int]:
        """Execute configuration workflow for MSP mode (all sites)."""
        logging.debug("Entering run_msp_mode() for org: %s", self.org_name)

        if not self._step1_fetch_sites():
            return (False, 0)

        self.selected_sites = self.all_sites.copy()
        print(f"  + Auto-selected ALL {len(self.selected_sites)} site(s)")

        if self.shared_versions:
            self.custom_versions = self.shared_versions.copy()
            print(f"\n  Using pre-selected firmware versions ({len(self.custom_versions)} models):")
            for model, version in sorted(self.custom_versions.items()):
                print(f"    {model}: {version}")
        else:
            if not self._step3_fetch_available_versions():
                return (False, 0)
            if not self._auto_select_versions():
                return (False, 0)

        success, count = self._apply_auto_upgrade_config()
        logging.info("MSP mode complete for %s: success=%s, sites=%s", self.org_name, success, count)
        return (success, count)

    def _auto_select_versions(self) -> bool:
        """Auto-select firmware versions (latest stable for each model)."""
        logging.debug("Entering _auto_select_versions()")
        if not self.model_version_map:
            print("  X No firmware versions available")
            return False

        print("\n  Auto-selecting firmware versions:")
        for model, versions in self.model_version_map.items():
            if not versions:
                continue
            selected = _pick_stable_version(versions)
            self.custom_versions[model] = selected
            print(f"    {model}: {self.custom_versions[model]}")

        logging.info("Auto-selected versions for %s model(s)", len(self.custom_versions))
        return bool(self.custom_versions)

    def _apply_auto_upgrade_config(self) -> tuple[bool, int]:
        """Apply auto-upgrade configuration to all selected sites."""
        logging.debug("Entering _apply_auto_upgrade_config()")
        if not self.selected_sites:
            return (False, 0)

        auto_upgrade_settings = {
            "enabled": True,
            "version": "custom",
            "day_of_week": self.schedule.get("day_of_week", "any"),
            "time_of_day": self.schedule.get("time_of_day", "02:00"),
            "custom_versions": self.custom_versions,
        }

        label = "DRY-RUN: Would apply" if self.dry_run else "Applying"
        print(f"\n  {label} auto-upgrade to {len(self.selected_sites)} site(s)...")

        success_count, fail_count = _apply_settings_to_sites(
            sites=self.selected_sites,
            settings={"auto_upgrade": auto_upgrade_settings},
            apisession=self.apisession,
            check_stop_fn=self.check_stop_fn,
            dry_run=self.dry_run,
        )

        if self.dry_run:
            print(f"  + Would configure: {success_count} site(s)")
        else:
            print(f"  + Configured: {success_count} site(s)")
        if fail_count > 0:
            print(f"  X Failed: {fail_count} site(s)")

        return (fail_count == 0, success_count)

    # ------------------------------------------------------------------
    # Interactive workflow (single-org mode)
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Execute the interactive configuration workflow."""
        logging.debug("Entering run() for org_id=%s", self.org_id)
        _print_intro_header(self.dry_run)

        if not self._step1_fetch_sites():
            return
        if not self._step2_select_sites():
            return
        if not self._step3_fetch_available_versions():
            return
        if not self._step4_select_versions():
            return
        self._step5_configure_schedule()
        self._step6_confirm_and_apply()

    # ------------------------------------------------------------------
    # Step 1: Fetch sites
    # ------------------------------------------------------------------

    def _step1_fetch_sites(self) -> bool:
        """Fetch all sites in the organization."""
        print("-" * 70)
        print("  STEP 1: Loading Sites")
        print("-" * 70)

        try:
            self.all_sites = self.fetch_sites_fn(self.org_id)
            if not self.all_sites:
                print("  X No sites found in organization")
                return False
            self.all_sites.sort(key=lambda s: s.get("name", "").lower())
            print(f"  + Found {len(self.all_sites)} site(s)")
            return True
        except Exception as exc:
            print(f"  X Error fetching sites: {exc}")
            logging.error("SiteAutoUpgradeConfigurator: Failed to fetch sites: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Step 2: Select sites
    # ------------------------------------------------------------------

    def _step2_select_sites(self) -> bool:
        """Allow user to select sites with flexible options."""
        print("\n" + "-" * 70)
        print("  STEP 2: Site Selection")
        print("-" * 70)
        print("\n  Selection Options:")
        print("    [A] All sites in organization")
        print("    [S] Single site (interactive selection)")
        print("    [L] List view - select by index numbers\n")

        try:
            choice = self.safe_input_fn("  Selection mode (A/S/L): ", "auto_upgrade_config").strip().upper()
        except SystemExit:
            return False

        if choice == "S":
            return self._select_single_site()
        if choice == "L":
            return self._select_from_list()
        return self._select_all_sites()

    def _select_all_sites(self) -> bool:
        """Select all sites."""
        self.selected_sites = self.all_sites.copy()
        print(f"  + Selected ALL {len(self.selected_sites)} site(s)")
        return True

    def _select_single_site(self) -> bool:
        """Interactive single site selection."""
        _display_site_list(self.all_sites)
        try:
            selection = (
                self.safe_input_fn("  Enter site number (or 'q' to cancel): ", "auto_upgrade_config").strip().lower()
            )
        except SystemExit:
            return False

        if selection == "q":
            return False
        if not selection.isdigit():
            print("  Invalid input")
            return False

        idx = int(selection) - 1
        if not 0 <= idx < len(self.all_sites):
            print("  Invalid selection")
            return False

        self.selected_sites = [self.all_sites[idx]]
        self.is_single_site = True
        print(f"  + Selected: {self.all_sites[idx].get('name')}")
        self._fetch_current_site_settings(self.all_sites[idx]["id"])
        return True

    def _fetch_current_site_settings(self, site_id: str) -> None:
        """Fetch current auto-upgrade settings for a single site."""
        try:
            import mistapi.api.v1.sites.setting as sites_setting_api

            response = sites_setting_api.getSiteSettings(self.apisession, site_id)
            if not response or not hasattr(response, "data") or not response.data:
                return
            settings = response.data if isinstance(response.data, dict) else {}
            auto_upgrade = settings.get("auto_upgrade", {})
            if not auto_upgrade:
                return
            self.current_site_versions = auto_upgrade.get("custom_versions", {})
            if auto_upgrade.get("day_of_week"):
                self.schedule["day_of_week"] = auto_upgrade["day_of_week"]
            if auto_upgrade.get("time_of_day"):
                self.schedule["time_of_day"] = auto_upgrade["time_of_day"]
            if self.current_site_versions:
                count = len(self.current_site_versions)
                print(f"  + Current auto-upgrade settings found ({count} model(s) configured)")
        except Exception as exc:
            logging.debug("Could not fetch current site settings: %s", exc)

    def _select_from_list(self) -> bool:
        """Display numbered list and allow index/range selection."""
        _display_site_list(self.all_sites)
        _display_selection_instructions()

        try:
            selection = self.safe_input_fn("  Selection: ", "auto_upgrade_config").strip()
        except SystemExit:
            return False

        if not selection:
            print("  No selection made")
            return False

        indices = _parse_index_selection(selection)
        if not indices:
            print("  X Invalid selection format")
            return False

        return self._apply_site_indices(indices)

    def _apply_site_indices(self, indices: list[int]) -> bool:
        """Apply indices to select sites."""
        for idx in indices:
            if 1 <= idx <= len(self.all_sites):
                self.selected_sites.append(self.all_sites[idx - 1])

        if not self.selected_sites:
            print("  X No valid sites selected")
            return False

        print(f"  + Selected {len(self.selected_sites)} site(s):")
        for site in self.selected_sites[:5]:
            print(f"      - {site.get('name')}")
        if len(self.selected_sites) > 5:
            print(f"      ... and {len(self.selected_sites) - 5} more")
        return True

    # ------------------------------------------------------------------
    # Step 3: Fetch available versions
    # ------------------------------------------------------------------

    def _step3_fetch_available_versions(self) -> bool:
        """Fetch available firmware versions."""
        print("\n" + "-" * 70)
        print("  STEP 3: Available Firmware Versions")
        print("-" * 70)
        print("  Fetching available AP firmware versions...")

        if self.apisession is None or self.org_id is None:
            print("  X API session or org_id not initialized")
            return False

        try:
            import mistapi.api.v1.orgs.devices as org_devices_api

            response = org_devices_api.listOrgAvailableDeviceVersions(self.apisession, self.org_id, type="ap")
            if not response or not hasattr(response, "data"):
                print("  X Failed to fetch available versions")
                return False

            self.available_versions = response.data if isinstance(response.data, list) else []
            self._build_model_version_map()
            print(f"  + Found firmware for {len(self.model_version_map)} AP model(s)")
            return True
        except Exception as exc:
            print(f"  X Error fetching firmware versions: {exc}")
            logging.error("SiteAutoUpgradeConfigurator: Failed to fetch versions: %s", exc)
            return False

    def _build_model_version_map(self) -> None:
        """Build model -> versions map from available versions."""
        for version_info in self.available_versions:
            if not isinstance(version_info, dict):
                continue
            model = version_info.get("model")
            version = version_info.get("version")
            if model and version:
                if model not in self.model_version_map:
                    self.model_version_map[model] = []
                self.model_version_map[model].append(version_info)

    # ------------------------------------------------------------------
    # Step 4: Select versions
    # ------------------------------------------------------------------

    def _step4_select_versions(self) -> bool:
        """Select firmware version per AP model."""
        _print_step4_header(self.is_single_site, self.current_site_versions)
        if self.is_single_site and self.current_site_versions:
            self.custom_versions = self.current_site_versions.copy()

        model_families = _group_models_by_family(self.model_version_map)

        for family, models in sorted(model_families.items()):
            sorted_versions = _get_family_versions(self.model_version_map, models)
            if not sorted_versions:
                continue

            current_version = _get_current_family_version(
                self.is_single_site,
                self.current_site_versions,
                models,
            )
            _display_family_versions(family, models, sorted_versions, current_version)

            try:
                choice = self.safe_input_fn(
                    f"  Select version (1-{len(sorted_versions)}): ",
                    "auto_upgrade_config",
                ).strip()
            except SystemExit:
                return False

            _apply_family_selection(
                choice,
                family,
                models,
                sorted_versions,
                current_version,
                self.model_version_map,
                self.custom_versions,
            )

        if not self.custom_versions:
            print("\n  X No versions selected")
            return False

        print(f"\n  + Configured {len(self.custom_versions)} model(s)")
        return True

    # ------------------------------------------------------------------
    # Step 5: Configure schedule
    # ------------------------------------------------------------------

    def _step5_configure_schedule(self) -> None:
        """Configure upgrade schedule."""
        print("\n" + "-" * 70)
        print("  STEP 5: Schedule Configuration (Optional)")
        print("-" * 70)
        print("\n  Configure when auto-upgrades should occur.\n")

        self.schedule["day_of_week"] = _prompt_day_of_week(self.safe_input_fn)
        self.schedule["time_of_day"] = _prompt_time_of_day(
            self.safe_input_fn,
            self._parse_time_input,
        )

        day_display = self.schedule.get("day_of_week", "daily")
        if day_display == "any":
            day_display = "daily"
        time_display = self.schedule.get("time_of_day", "any time")
        if time_display == "any":
            time_display = "any time"
        print(f"  + Schedule: {day_display} at {time_display}")

    @staticmethod
    def _parse_time_input(time_input: str) -> str:
        """Parse various time formats to HH:MM for the API.

        Accepts: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM, etc.
        Returns: HH:MM format string, or 'any' for any time.
        """
        return parse_time_input(time_input)

    # ------------------------------------------------------------------
    # Step 6: Confirm and apply
    # ------------------------------------------------------------------

    def _step6_confirm_and_apply(self) -> None:
        """Confirm settings and apply to selected sites."""
        print("\n" + "-" * 70)
        print("  STEP 6: Confirm and Apply")
        print("-" * 70 + "\n")

        _display_step6_summary(
            self.selected_sites,
            self.custom_versions,
            self.schedule,
        )

        if not self.dry_run:
            try:
                confirm = self.safe_input_fn("  Apply these settings? (y/N): ", "auto_upgrade_config").strip().lower()
            except SystemExit:
                return
            if confirm not in ("y", "yes"):
                print("  Cancelled.")
                return

        auto_upgrade = _build_auto_upgrade_payload(self.custom_versions, self.schedule)
        settings = {"auto_upgrade": auto_upgrade}

        label = "DRY-RUN: Simulating" if self.dry_run else "Applying"
        print(f"\n  {label} configuration...")

        successful, failed = _apply_settings_to_sites(
            sites=self.selected_sites,
            settings=settings,
            apisession=self.apisession,
            check_stop_fn=self.check_stop_fn,
            dry_run=self.dry_run,
        )

        _print_final_summary(successful, failed, self.dry_run)


# ======================================================================
# Module-level helper functions (reduce class CC)
# ======================================================================


def _handle_msp_mode(
    apisession: Any,
    msp_privileges: list[Any],
    safe_input_fn: SafeInputFn,
    get_org_id_fn: GetOrgIdFn,
    fetch_sites_fn: FetchSitesFn,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
    select_msps_fn: SelectMspsFn | None,
    select_orgs_fn: SelectOrgsFromMspFn | None,
) -> None:
    """Handle MSP privilege detection and mode selection."""
    logging.debug("MSP privileges detected: %s MSP(s)", len(msp_privileges))
    print("\n" + "=" * 70)
    print("  SITE AUTO-UPGRADE CONFIGURATION")
    print("=" * 70 + "\n")
    if dry_run:
        print("  >> DRY-RUN MODE: No actual changes will be made <<\n")
    print("  MSP privileges detected. Select operation mode:\n")
    print("    [1] Single Organization - configure auto-upgrade for current org")
    print("    [2] MSP Multi-Org - configure ALL sites across multiple orgs\n")

    try:
        mode = safe_input_fn("  Select mode (1-2) [1]: ", "msp_mode_select").strip() or "1"
    except SystemExit:
        return

    if mode == "2":
        logging.info("User selected MSP Multi-Org mode")
        _execute_msp_mode(
            apisession=apisession,
            safe_input_fn=safe_input_fn,
            fetch_sites_fn=fetch_sites_fn,
            check_stop_fn=check_stop_fn,
            dry_run=dry_run,
            select_msps_fn=select_msps_fn,
            select_orgs_fn=select_orgs_fn,
        )
        return

    _run_single_org(
        apisession=apisession,
        safe_input_fn=safe_input_fn,
        get_org_id_fn=get_org_id_fn,
        fetch_sites_fn=fetch_sites_fn,
        check_stop_fn=check_stop_fn,
        dry_run=dry_run,
    )


def _run_single_org(
    apisession: Any,
    safe_input_fn: SafeInputFn,
    get_org_id_fn: GetOrgIdFn,
    fetch_sites_fn: FetchSitesFn,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
) -> None:
    """Run single-org configuration workflow."""
    org_id = get_org_id_fn()
    if not org_id:
        print("  X No organization selected")
        return
    configurator = SiteAutoUpgradeConfigurator(
        org_id=org_id,
        apisession=apisession,
        safe_input_fn=safe_input_fn,
        fetch_sites_fn=fetch_sites_fn,
        check_stop_fn=check_stop_fn,
        dry_run=dry_run,
    )
    configurator.run()


def _msp_select_entities(
    select_msps_fn: SelectMspsFn,
    select_orgs_fn: SelectOrgsFromMspFn,
) -> list[dict[str, Any]] | None:
    """Select MSPs and organizations for MSP mode.

    Returns:
        List of selected orgs, or None if selection cancelled.
    """
    print("\n" + "-" * 70)
    print("  STEP 1: MSP Selection")
    print("-" * 70 + "\n")
    selected_msps = select_msps_fn()
    if not selected_msps:
        print("  No MSPs selected. Returning.")
        return None

    print("\n" + "-" * 70)
    print("  STEP 2: Organization Selection")
    print("-" * 70 + "\n")
    selected_orgs = select_orgs_fn(selected_msps)
    if not selected_orgs:
        print("  No organizations selected. Returning.")
        return None

    print(f"\n  Selected {len(selected_orgs)} organization(s)")
    result: list[dict[str, Any]] = list(selected_orgs)
    return result


def _msp_get_firmware_config(
    apisession: Any,
    selected_orgs: list[dict[str, Any]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Prompt user for firmware version selection in MSP mode.

    Returns:
        Dict of model->version mappings, or None if cancelled.
        Empty dict means auto-detect.
    """
    print("\n" + "-" * 70)
    print("  STEP 3: Firmware Version Configuration")
    print("-" * 70 + "\n")
    print("  How to select firmware versions?\n")
    print("    [1] Auto-detect latest stable per model for each org")
    print("    [2] Manually select firmware versions (from reference org)\n")

    try:
        fw_choice = (
            safe_input_fn(
                "  Selection (1-2) [1]: ",
                "msp_firmware",
            ).strip()
            or "1"
        )
    except SystemExit:
        return None

    if fw_choice != "2" or not selected_orgs:
        return {}

    return _get_shared_firmware_versions(
        apisession,
        selected_orgs[0],
        safe_input_fn,
    )


def _msp_confirm_and_apply(
    selected_orgs: list[dict[str, Any]],
    apisession: Any,
    safe_input_fn: SafeInputFn,
    fetch_sites_fn: FetchSitesFn,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
) -> None:
    """Display summary, confirm, and apply MSP configuration."""
    _display_msp_pre_apply_summary(
        shared_schedule,
        shared_versions,
        selected_orgs,
    )

    try:
        final_confirm = (
            safe_input_fn(
                "  Apply this configuration? (Y/n): ",
                "msp_final_confirm",
            )
            .strip()
            .lower()
        )
    except SystemExit:
        return

    if final_confirm in ["n", "no"]:
        print("  Cancelled.")
        return

    print("\n" + "-" * 70)
    print("  STEP 6: Applying Configuration")
    print("-" * 70)

    all_results = _apply_to_all_orgs(
        selected_orgs=selected_orgs,
        apisession=apisession,
        safe_input_fn=safe_input_fn,
        fetch_sites_fn=fetch_sites_fn,
        check_stop_fn=check_stop_fn,
        dry_run=dry_run,
        shared_schedule=shared_schedule,
        shared_versions=shared_versions,
    )
    _print_msp_summary(all_results, dry_run)


def _execute_msp_mode(
    apisession: Any,
    safe_input_fn: SafeInputFn,
    fetch_sites_fn: FetchSitesFn,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
    select_msps_fn: SelectMspsFn | None,
    select_orgs_fn: SelectOrgsFromMspFn | None,
) -> None:
    """Execute MSP multi-organization auto-upgrade configuration."""
    logging.debug("Entering _execute_msp_mode()")

    if not select_msps_fn or not select_orgs_fn:
        print("  X MSP functions not available")
        return

    selected_orgs = _msp_select_entities(select_msps_fn, select_orgs_fn)
    if not selected_orgs:
        return

    shared_versions = _msp_get_firmware_config(
        apisession,
        selected_orgs,
        safe_input_fn,
    )
    if shared_versions is None:
        return

    print("\n" + "-" * 70)
    print("  STEP 4: Schedule Configuration")
    print("-" * 70 + "\n")
    shared_schedule = _get_shared_schedule(safe_input_fn)
    if shared_schedule is None:
        return

    _msp_confirm_and_apply(
        selected_orgs,
        apisession,
        safe_input_fn,
        fetch_sites_fn,
        check_stop_fn,
        dry_run,
        shared_schedule,
        shared_versions if shared_versions else None,
    )


def _apply_to_all_orgs(
    selected_orgs: list[dict[str, Any]],
    apisession: Any,
    safe_input_fn: SafeInputFn,
    fetch_sites_fn: FetchSitesFn,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
    shared_schedule: dict[str, Any],
    shared_versions: dict[str, str] | None,
) -> list[dict[str, Any]]:
    """Apply configuration to all selected organizations."""
    all_results: list[dict[str, Any]] = []
    for idx, org_info in enumerate(selected_orgs, start=1):
        org_id = org_info["id"]
        org_name = org_info["name"]

        print(f"\n{'=' * 70}")
        print(f"  ORGANIZATION {idx}/{len(selected_orgs)}: {org_name}")
        print("=" * 70)

        configurator = SiteAutoUpgradeConfigurator(
            org_id=org_id,
            apisession=apisession,
            safe_input_fn=safe_input_fn,
            fetch_sites_fn=fetch_sites_fn,
            check_stop_fn=check_stop_fn,
            dry_run=dry_run,
        )
        configurator.msp_all_sites_mode = True
        configurator.org_name = org_name
        configurator.schedule = shared_schedule.copy()
        configurator.shared_versions = shared_versions

        success, site_count = configurator.run_msp_mode()
        all_results.append(
            {
                "org_id": org_id,
                "org_name": org_name,
                "success": success,
                "sites_configured": site_count,
            }
        )

    return all_results


# ======================================================================
# Pure helper functions
# ======================================================================


def _print_intro_header(dry_run: bool) -> None:
    """Print introduction header for the configuration workflow."""
    print("\n" + "=" * 70)
    print("  SITE AUTO-UPGRADE CONFIGURATION")
    print("=" * 70 + "\n")
    if dry_run:
        print("  >> DRY-RUN MODE: No actual changes will be made <<\n")
    print("  This tool configures auto-upgrade settings for sites WITHOUT")
    print("  initiating immediate upgrades. Auto-upgrade ensures:")
    print("    - New APs automatically upgrade to target firmware")
    print("    - Scheduled upgrades during maintenance windows\n")


def _display_site_list(all_sites: list[dict[str, Any]]) -> None:
    """Display numbered list of all sites."""
    print(f"\n  All Sites ({len(all_sites)} total):")
    print("-" * 70)
    for idx, site in enumerate(all_sites, 1):
        print(f"    [{idx:>3}] {site.get('name', 'Unknown')}")
    print("")


def _display_selection_instructions() -> None:
    """Display selection format instructions."""
    print("  Enter selection:")
    print("    - Single: 5")
    print("    - Multiple: 1,3,5,7")
    print("    - Range: 1-10")
    print("    - Combined: 1-5,8,12-15\n")


def _parse_index_selection(selection: str) -> list[int]:
    """Parse index selection string into sorted list of integers."""
    indices: set[int] = set()
    parts = selection.replace(" ", "").split(",")

    for part in parts:
        if "-" in part:
            try:
                range_parts = part.split("-")
                if len(range_parts) == 2:
                    start = int(range_parts[0])
                    end = int(range_parts[1])
                    indices.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                indices.add(int(part))
            except ValueError:
                continue

    return sorted(indices)


def _group_models_by_family(
    model_version_map: dict[str, list[Any]],
) -> dict[str, list[str]]:
    """Group models by family prefix (AP41, AP43, etc.)."""
    model_families: dict[str, list[str]] = {}
    for model in sorted(model_version_map.keys()):
        family = model.rstrip("EP")
        if family not in model_families:
            model_families[family] = []
        model_families[family].append(model)
    return model_families


def _get_family_versions(
    model_version_map: dict[str, list[Any]],
    models: list[str],
) -> list[str]:
    """Get sorted versions for a model family."""
    family_versions: set[str] = set()
    for model in models:
        for entry in model_version_map.get(model, []):
            if isinstance(entry, dict):
                version = entry.get("version")
            else:
                version = entry
            if version:
                family_versions.add(str(version))
    return sorted(family_versions, reverse=True)


def _get_current_family_version(
    is_single_site: bool,
    current_site_versions: dict[str, str],
    models: list[str],
) -> str | None:
    """Get current version for a model family if in single-site mode."""
    if not is_single_site:
        return None
    for model in models:
        if model in current_site_versions:
            return current_site_versions[model]
    return None


def _display_family_versions(
    family: str,
    models: list[str],
    sorted_versions: list[str],
    current_version: str | None,
) -> None:
    """Display version options for a model family."""
    print(f"\n  {family} family ({', '.join(models)}):")
    for idx, version in enumerate(sorted_versions, 1):
        marker = " <-- current" if version == current_version else ""
        print(f"    [{idx:>2}] {version}{marker}")
    if current_version:
        print(f"    [Enter] Keep current: {current_version}")
    else:
        print("    [Enter] Skip")


def _apply_family_selection(
    choice: str,
    family: str,
    models: list[str],
    sorted_versions: list[str],
    current_version: str | None,
    model_version_map: dict[str, list[Any]],
    custom_versions: dict[str, str],
) -> None:
    """Apply user's version selection for a model family."""
    if choice and choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(sorted_versions):
            selected = sorted_versions[idx]
            for model in models:
                model_versions = _extract_version_strings(
                    model_version_map.get(model, []),
                )
                if selected in model_versions:
                    custom_versions[model] = selected
            print(f"    + Set {family} models to {selected}")
    elif not choice and current_version:
        print(f"    + Keeping {family} models at {current_version}")
    elif not choice:
        print(f"    - Skipped {family} family")


def _extract_version_strings(entries: list[Any]) -> list[str]:
    """Extract version strings from a list of version entries."""
    result: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            ver = entry.get("version")
        else:
            ver = entry
        if ver:
            result.append(str(ver))
    return result


def _print_step4_header(
    is_single_site: bool,
    current_site_versions: dict[str, str],
) -> None:
    """Print step 4 header and instructions."""
    print("\n" + "-" * 70)
    print("  STEP 4: Firmware Version Selection")
    print("-" * 70 + "\n")
    print("  Select firmware version for each AP model family.")
    if is_single_site and current_site_versions:
        print("  Press Enter to keep current version, or select a new one.")
        print(f"  (Pre-loaded {len(current_site_versions)} existing model configurations)")
    else:
        print("  Press Enter to skip a model (won't be included in auto-upgrade).")
    print("")


def _pick_stable_version(versions: list[Any]) -> str:
    """Pick the latest stable version from a list of version entries."""
    stable = [v for v in versions if isinstance(v, dict) and v.get("tag") == "stable"]
    if stable:
        return str(stable[0].get("version", ""))
    if versions:
        first = versions[0]
        if isinstance(first, dict):
            return str(first.get("version", ""))
        return str(first)
    return ""


def _prompt_day_of_week(safe_input_fn: SafeInputFn) -> str:
    """Prompt for day of week selection."""
    print("  Day of week options:")
    print("    [1] Daily (any day)  [2] Sunday   [3] Monday")
    print("    [4] Tuesday          [5] Wednesday [6] Thursday")
    print("    [7] Friday           [8] Saturday")

    day_map = {
        "1": "any",
        "2": "sun",
        "3": "mon",
        "4": "tue",
        "5": "wed",
        "6": "thu",
        "7": "fri",
        "8": "sat",
    }
    try:
        choice = safe_input_fn("  Day of week (1-8, default=1 for daily): ", "auto_upgrade_config").strip()
    except SystemExit:
        choice = "1"
    return day_map.get(choice, "any")


def _prompt_time_of_day(
    safe_input_fn: SafeInputFn,
    parse_fn: Any,
) -> str:
    """Prompt for time of day selection."""
    print("\n  Time of day for upgrades:")
    print("    Examples: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM")
    print("    Leave blank for any time")
    try:
        time_input = safe_input_fn("  Time: ", "auto_upgrade_config").strip()
    except SystemExit:
        time_input = ""
    result: str = parse_fn(time_input)
    return result


def parse_time_input(time_input: str) -> str:
    """Parse various time formats to HH:MM for the API.

    Accepts: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM, etc.
    Returns: HH:MM format string, or 'any' for any time.
    """
    if not time_input:
        return "any"

    time_upper = time_input.upper().strip()
    is_pm = "PM" in time_upper
    is_am = "AM" in time_upper
    time_clean = time_upper.replace("AM", "").replace("PM", "").strip()

    hour, minute = _parse_hour_minute(time_clean)
    if hour < 0:
        return "any"

    hour = _apply_ampm(hour, is_am, is_pm)

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return "any"

    return f"{hour:02d}:{minute:02d}"


def _parse_hour_minute(time_clean: str) -> tuple[int, int]:
    """Parse hour and minute from cleaned time string."""
    if ":" in time_clean:
        parts = time_clean.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return (hour, minute)
        except ValueError:
            return (-1, 0)
    try:
        return (int(time_clean), 0)
    except ValueError:
        return (-1, 0)


def _apply_ampm(hour: int, is_am: bool, is_pm: bool) -> int:
    """Apply AM/PM conversion to hour value."""
    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0
    return hour


def _display_step6_summary(
    selected_sites: list[dict[str, Any]],
    custom_versions: dict[str, str],
    schedule: dict[str, Any],
) -> None:
    """Display configuration summary for step 6."""
    day_display = schedule.get("day_of_week") or "daily"
    time_display = schedule.get("time_of_day") or "any time"
    print("  Summary:")
    print(f"    Sites: {len(selected_sites)}")
    print(f"    Models configured: {len(custom_versions)}")
    for model, version in sorted(custom_versions.items()):
        print(f"      {model}: {version}")
    print(f"    Schedule: {day_display} at {time_display}\n")


def _build_auto_upgrade_payload(
    custom_versions: dict[str, str],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    """Build the auto-upgrade configuration payload."""
    return {
        "enabled": True,
        "version": "custom",
        "custom_versions": custom_versions,
        "day_of_week": schedule.get("day_of_week", "any"),
        "time_of_day": schedule.get("time_of_day", "any"),
    }


def _apply_settings_to_sites(
    sites: list[dict[str, Any]],
    settings: dict[str, Any],
    apisession: Any,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
) -> tuple[int, int]:
    """Apply settings to sites. Returns (successful, failed) counts."""
    successful = 0
    failed = 0
    for site in sites:
        if check_stop_fn():
            break
        site_id = site.get("id")
        site_name = site.get("name", "Unknown")
        if not site_id:
            failed += 1
            continue
        try:
            if dry_run:
                print(f"    [DRY-RUN] {site_name}")
            else:
                import mistapi.api.v1.sites.setting as sites_setting_api

                sites_setting_api.updateSiteSettings(
                    apisession,
                    site_id,
                    body=settings,
                )
                print(f"    [OK] {site_name}")
            successful += 1
        except Exception as exc:
            print(f"    [FAIL] {site_name}: {exc}")
            logging.error("Failed to configure auto-upgrade for site %s: %s", site_name, exc)
            failed += 1
    return (successful, failed)


def _print_final_summary(
    successful: int,
    failed: int,
    dry_run: bool,
) -> None:
    """Print final summary after applying configuration."""
    print("\n" + "=" * 70)
    print(f"  {'DRY-RUN COMPLETE' if dry_run else 'CONFIGURATION COMPLETE'}")
    print("=" * 70)
    if dry_run:
        print(f"    Would configure: {successful} site(s)")
    else:
        print(f"    Successful: {successful} site(s)")
    if failed > 0:
        print(f"    Failed: {failed} site(s)")
    if dry_run:
        print("\n  >> To apply changes, run without --dry-run flag")
    print("")


def _compute_msp_totals(
    results: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Compute total orgs, successful orgs, and total sites from results."""
    total_orgs = len(results)
    successful_orgs = sum(1 for r in results if r["success"])
    total_sites = sum(r["sites_configured"] for r in results)
    return total_orgs, successful_orgs, total_sites


def _print_msp_failed_orgs(results: list[dict[str, Any]]) -> None:
    """Print list of failed organizations from MSP results."""
    print("  Failed organizations:")
    for result in results:
        if not result["success"]:
            print(f"    - {result['org_name']}")
    print("")


def _print_msp_summary(
    results: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Print summary of MSP multi-org auto-upgrade configuration."""
    print("\n" + "=" * 70)
    label = "MSP MULTI-ORG AUTO-UPGRADE SUMMARY"
    if dry_run:
        label += " (DRY-RUN)"
    print(f"  {label}")
    print("=" * 70 + "\n")

    if dry_run:
        print("  >> DRY-RUN MODE: No actual changes were made <<\n")

    total_orgs, successful_orgs, total_sites = _compute_msp_totals(results)

    print(f"  Organizations processed: {total_orgs}")
    if dry_run:
        print(f"  Would configure: {successful_orgs} org(s)")
        print(f"  Total sites WOULD be configured: {total_sites}")
    else:
        print(f"  Successful: {successful_orgs}")
        print(f"  Total sites configured: {total_sites}")
    print("")

    if successful_orgs < total_orgs:
        _print_msp_failed_orgs(results)

    if dry_run:
        print("  >> To apply changes, run without --dry-run flag")
    else:
        print("  Configuration complete.")


def _get_shared_schedule(
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Get shared schedule settings for MSP mode."""
    print("  Schedule Configuration:")
    print("    When should auto-upgrades occur?\n")
    print("    Day of week:")
    print("      [1] any - Any day")
    print("      [2] mon, tue, wed, thu, fri, sat, sun\n")

    try:
        day_input = (
            safe_input_fn(
                "  Day of week [any]: ",
                "msp_schedule",
            )
            .strip()
            .lower()
            or "any"
        )
    except SystemExit:
        return None

    day_map = {
        "1": "any",
        "2": "mon",
        "3": "tue",
        "4": "wed",
        "5": "thu",
        "6": "fri",
        "7": "sat",
        "8": "sun",
        "any": "any",
        "mon": "mon",
        "tue": "tue",
        "wed": "wed",
        "thu": "thu",
        "fri": "fri",
        "sat": "sat",
        "sun": "sun",
    }
    day_of_week = day_map.get(day_input, "any")

    print(f"    + Day: {day_of_week}\n")
    print("    Time of day (HH:MM in site's local timezone, or 'any'):")

    try:
        time_input = (
            safe_input_fn(
                "  Time of day [02:00]: ",
                "msp_schedule",
            ).strip()
            or "02:00"
        )
    except SystemExit:
        return None

    time_of_day = time_input if time_input.lower() != "any" else "any"
    print(f"    + Time: {time_of_day}")

    return {"day_of_week": day_of_week, "time_of_day": time_of_day}


def _get_shared_firmware_versions(
    apisession: Any,
    reference_org: dict[str, Any],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Fetch firmware versions from a reference org and let user select.

    Returns:
        Dict mapping model to selected version, None if cancelled,
        empty dict if no selection.
    """
    org_id = reference_org.get("id")
    org_name = reference_org.get("name", "Unknown")

    if not org_id or apisession is None:
        print("  X Missing organization ID or API session")
        return {}

    org_id_str: str = str(org_id)
    print(f"\n  Fetching available firmware versions from: {org_name}")

    try:
        import mistapi.api.v1.orgs.devices as org_devices_api

        response = org_devices_api.listOrgAvailableDeviceVersions(
            apisession,
            org_id_str,
            type="ap",
        )
        if not response or not hasattr(response, "data"):
            print("  X Failed to fetch available firmware versions")
            return {}

        available_versions = response.data if isinstance(response.data, list) else []
    except Exception as error:
        print(f"  X Error fetching firmware versions: {error}")
        return {}

    model_version_map = _build_version_map_from_list(available_versions)
    if not model_version_map:
        print("  X No AP firmware versions found")
        return {}

    print(f"  + Found firmware for {len(model_version_map)} AP model(s)")
    model_families = _group_models_for_msp(model_version_map)

    return _select_versions_interactively(
        model_families,
        model_version_map,
        safe_input_fn,
    )


def _build_version_map_from_list(
    available_versions: list[Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build model -> versions map from API response."""
    result: dict[str, list[dict[str, Any]]] = {}
    for entry in available_versions:
        if not isinstance(entry, dict):
            continue
        model = entry.get("model")
        version = entry.get("version")
        tag = entry.get("tag", "")
        if model and version:
            if model not in result:
                result[model] = []
            result[model].append({"version": version, "tag": tag})
    return result


def _group_models_for_msp(
    model_version_map: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    """Group models by family for MSP firmware selection."""
    model_families: dict[str, list[str]] = {}
    for model in sorted(model_version_map.keys()):
        family = model.rstrip("EP")
        if family not in model_families:
            model_families[family] = []
        model_families[family].append(model)
    return model_families


def _collect_family_versions(
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
) -> list[tuple[str, str]]:
    """Collect and sort unique versions for a model family.

    Returns:
        Sorted list of (version, tag) tuples, newest first.
    """
    family_versions: set[tuple[str, str]] = set()
    for model in models:
        for v_info in model_version_map.get(model, []):
            family_versions.add((v_info["version"], v_info.get("tag", "")))
    return sorted(list(family_versions), key=lambda x: x[0], reverse=True)


def _display_msp_family_versions(
    family: str,
    models: list[str],
    sorted_versions: list[tuple[str, str]],
) -> None:
    """Display available firmware versions for a model family."""
    print(f"\n  {family} family ({', '.join(models)}):")
    for idx, (version, tag) in enumerate(sorted_versions, 1):
        tag_display = f" [{tag}]" if tag else ""
        print(f"    [{idx:>2}] {version}{tag_display}")
    print("    [Enter] Skip this family")


def _apply_version_to_models(
    selected_version: str,
    family: str,
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
    custom_versions: dict[str, str],
) -> None:
    """Apply a selected version to all compatible models in a family."""
    for model in models:
        model_versions = [v["version"] for v in model_version_map.get(model, [])]
        if selected_version in model_versions:
            custom_versions[model] = selected_version
    print(f"    + Set {family} family to {selected_version}")


def _select_versions_interactively(
    model_families: dict[str, list[str]],
    model_version_map: dict[str, list[dict[str, Any]]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Interactively select firmware versions per model family."""
    print("\n  Select firmware version for each AP model family.")
    print("  Press Enter to skip a family (won't be configured).")
    print("  Enter 'q' to cancel selection.")

    custom_versions: dict[str, str] = {}

    for family, models in sorted(model_families.items()):
        sorted_versions = _collect_family_versions(models, model_version_map)
        if not sorted_versions:
            continue

        _display_msp_family_versions(family, models, sorted_versions)

        try:
            choice = safe_input_fn(
                f"  Select version (1-{len(sorted_versions)}): ",
                "msp_firmware_select",
            ).strip()
        except SystemExit:
            return None

        if choice.lower() == "q":
            return None

        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sorted_versions):
                _apply_version_to_models(
                    sorted_versions[idx][0],
                    family,
                    models,
                    model_version_map,
                    custom_versions,
                )
            else:
                print(f"    - Invalid selection, skipped {family}")
        else:
            print(f"    - Skipped {family} family")

    return custom_versions


def _display_msp_pre_apply_summary(
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
    selected_orgs: list[dict[str, Any]],
) -> None:
    """Display summary before MSP configuration application."""
    print("\n  Configuration to apply:")
    print(f"    - Day of week: {shared_schedule.get('day_of_week', 'any')}.")
    time_display = shared_schedule.get("time_of_day", "02:00")
    print(f"    - Time of day: {time_display} (site's local timezone)")
    if shared_versions:
        print(f"    - Firmware: Manually selected ({len(shared_versions)} models)")
        for model, version in sorted(shared_versions.items()):
            print(f"        {model}: {version}")
    else:
        print("    - Firmware: Latest stable per model (auto-detected)")
    print(f"    - Organizations: {len(selected_orgs)}\n")
