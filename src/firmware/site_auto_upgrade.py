"""Site auto-upgrade configuration for Mist AP firmware.

Configures auto-upgrade settings at the site level to schedule AP firmware
upgrades during maintenance windows. Supports single-org and MSP multi-org
workflows with dry-run capability.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines

from __future__ import annotations

import logging
from typing import Any

from src.dataclasses.family_selection_context import (  # Issue #433 Phase B: 5-field bundle for family selection.
    FamilySelectionContext,
)
from src.dataclasses.site_auto_upgrade_deps import (  # Issue #433 Phase B: bundles DI params (5-Item Rule).
    SiteAutoUpgradeCoreDeps,
    SiteAutoUpgradeMspDeps,
)

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

    def __init__(  # Reduced to 2 params via SiteAutoUpgradeCoreDeps (5-Item Rule).
        self,
        org_id: str,
        deps: SiteAutoUpgradeCoreDeps,
    ) -> None:
        """Initialize the configurator.

        Issue #433 Phase B: signature reduced from 6 params to 2 via the
        SiteAutoUpgradeCoreDeps dataclass.

        Args:
            org_id: Mist organization ID.
            deps: Bundle of injected dependencies (apisession, safe_input_fn,
                fetch_sites_fn, check_stop_fn, dry_run).
        """
        self.org_id = org_id  # Org id for every API call this configurator makes.
        self.apisession = deps.apisession  # Authenticated mistapi session.
        self.safe_input_fn = deps.safe_input_fn  # Prompt helper with EOF + interrupt safety.
        self.fetch_sites_fn = deps.fetch_sites_fn  # Callable returning all sites for an org.
        self.check_stop_fn = deps.check_stop_fn  # Predicate that signals operator stop request.
        self.dry_run = deps.dry_run  # When True, skip API mutations; only print planned changes.
        self.all_sites: list[dict[str, Any]] = []  # All sites in the org, populated by step 1.
        self.selected_sites: list[dict[str, Any]] = []  # Sites the operator chose to configure.
        self.available_versions: list[Any] = []  # Firmware versions available for the org's AP models.
        self.model_version_map: dict[str, list[Any]] = {}  # Per-model list of available versions.
        self.custom_versions: dict[str, str] = {}  # Operator-chosen version per model.
        self.schedule: dict[str, Any] = {}  # Maintenance-window schedule settings.
        self.current_site_versions: dict[str, str] = {}  # Currently-configured version per site.
        self.is_single_site = False  # True when configuring exactly one site.
        self.msp_all_sites_mode = False  # True in MSP all-sites bulk mode.
        self.org_name = ""  # Human-readable org name for logs/prompts.
        self.shared_versions: dict[str, str] | None = None  # Versions shared across MSP orgs (None until set).
        logging.debug(  # Action-log post-init state.
            "SiteAutoUpgradeConfigurator initialized: org_id=%s, dry_run=%s", org_id, deps.dry_run
        )

    # ------------------------------------------------------------------
    # Static entry point
    # ------------------------------------------------------------------

    @staticmethod
    def execute(  # noqa: PLR0913, STRUCT-PARAMS  # External entrypoint signature kept stable for MistHelper.py callers; deps dataclass refactor would break public API.
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
        logging.debug("Entering SiteAutoUpgradeConfigurator.execute()")  # Action-log entry.
        logging.info("Starting Site Auto-Upgrade Configuration workflow")  # Action-log start.

        if dry_run:  # When the operator chose dry-run, advertise it loudly so they aren't surprised.
            logging.info("DRY-RUN MODE enabled - no API calls will be made")

        # Issue #433 Phase B: bundle the 5 always-needed DI params into one dataclass so the
        # downstream entry points (_handle_msp_mode, _run_single_org) stay within the 5-Item Rule.
        core_deps = SiteAutoUpgradeCoreDeps(  # Bundle DI params into the core deps dataclass.
            apisession=apisession,
            safe_input_fn=safe_input_fn,
            fetch_sites_fn=fetch_sites_fn,
            check_stop_fn=check_stop_fn,
            dry_run=dry_run,
        )

        if msp_privileges and len(msp_privileges) > 0:  # MSP-licensed account: offer the multi-org workflow.
            msp_deps = SiteAutoUpgradeMspDeps(  # MSP-only extras bundled separately.
                select_msps_fn=select_msps_fn,
                select_orgs_fn=select_orgs_fn,
            )
            _handle_msp_mode(core_deps, msp_deps, get_org_id_fn)  # 3 params: core + MSP extras + single-org fallback.
            return  # MSP mode handles the rest of the workflow internally.

        _run_single_org(core_deps, get_org_id_fn)  # Non-MSP account: jump straight to single-org workflow.

    # ------------------------------------------------------------------
    # MSP mode helpers
    # ------------------------------------------------------------------

    def run_msp_mode(self) -> tuple[bool, int]:  # Run the MSP bulk all-sites configuration flow.
        """Execute configuration workflow for MSP mode (all sites)."""
        logging.debug("Entering run_msp_mode() for org: %s", self.org_name)  # Trace entry for the MSP flow.

        if not self._step1_fetch_sites():  # Fetch the org's sites first.
            return (False, 0)  # Abort with zero configured on fetch failure.

        self.selected_sites = self.all_sites.copy()  # MSP mode auto-selects every site.
        print(f"  + Auto-selected ALL {len(self.selected_sites)} site(s)")

        if self.shared_versions:  # Versions were pre-chosen for the MSP run.
            self.custom_versions = self.shared_versions.copy()  # Reuse the shared version map.
            print(f"\n  Using pre-selected firmware versions ({len(self.custom_versions)} models):")
            for model, version in sorted(self.custom_versions.items()):  # List each model/version pair in order.
                print(f"    {model}: {version}")  # Print the pair.
        else:
            if not self._step3_fetch_available_versions():  # Otherwise fetch available versions for this org.
                return (False, 0)  # Abort on version-fetch failure.
            if not self._auto_select_versions():  # Auto-pick a version per model.
                return (False, 0)  # Abort if no versions could be selected.

        success, count = self._apply_auto_upgrade_config()  # Apply the auto-upgrade config to all sites.
        logging.info("MSP mode complete for %s: success=%s, sites=%s", self.org_name, success, count)
        return (success, count)  # Return success flag and configured-site count.

    def _auto_select_versions(self) -> bool:  # Auto-pick the most stable version per model.
        """Auto-select firmware versions (latest stable for each model)."""
        logging.debug("Entering _auto_select_versions()")  # Trace entry for auto-selection.
        if not self.model_version_map:  # No model->version data available.
            print("  X No firmware versions available")  # Tell the operator nothing can be selected.
            return False  # Abort auto-selection.

        print("\n  Auto-selecting firmware versions:")  # Header for the selection list.
        for model, versions in self.model_version_map.items():  # Walk each model's version list.
            if not versions:  # Skip models with no versions.
                continue  # Continue to the next model.
            selected = _pick_stable_version(versions)  # Choose the stable release for this model.
            self.custom_versions[model] = selected  # Record the chosen version.
            print(f"    {model}: {self.custom_versions[model]}")  # Show the model's selected version.

        logging.info("Auto-selected versions for %s model(s)", len(self.custom_versions))
        return bool(self.custom_versions)  # Succeed only if at least one version was chosen.

    def _apply_auto_upgrade_config(self) -> tuple[bool, int]:  # Push the auto-upgrade settings to the selected sites.
        """Apply auto-upgrade configuration to all selected sites."""
        logging.debug("Entering _apply_auto_upgrade_config()")  # Trace entry for the apply step.
        if not self.selected_sites:  # No sites selected to configure.
            return (False, 0)  # Abort with zero configured.

        auto_upgrade_settings = {  # Build the auto-upgrade settings payload.
            "enabled": True,
            "version": "custom",
            "day_of_week": self.schedule.get("day_of_week", "any"),
            "time_of_day": self.schedule.get("time_of_day", "02:00"),
            "custom_versions": self.custom_versions,
        }

        label = "DRY-RUN: Would apply" if self.dry_run else "Applying"  # Label reflects dry-run vs real apply.
        print(f"\n  {label} auto-upgrade to {len(self.selected_sites)} site(s)...")

        success_count, fail_count = _apply_settings_to_sites(  # Apply settings to every selected site.
            sites=self.selected_sites,
            settings={"auto_upgrade": auto_upgrade_settings},
            apisession=self.apisession,
            check_stop_fn=self.check_stop_fn,
            dry_run=self.dry_run,
        )

        if self.dry_run:  # Dry-run reports what it would do.
            print(f"  + Would configure: {success_count} site(s)")  # Show the would-configure count.
        else:
            print(f"  + Configured: {success_count} site(s)")  # Show the configured count.
        if fail_count > 0:  # Some sites failed to configure.
            print(f"  X Failed: {fail_count} site(s)")  # Show the failure count.

        return (fail_count == 0, success_count)  # Success only when nothing failed.

    # ------------------------------------------------------------------
    # Interactive workflow (single-org mode)
    # ------------------------------------------------------------------

    def run(self) -> None:  # Run the interactive single-org configuration flow.
        """Execute the interactive configuration workflow."""
        logging.debug("Entering run() for org_id=%s", self.org_id)  # Trace entry for the interactive flow.
        _print_intro_header(self.dry_run)  # Print the intro/warning header.

        if not self._step1_fetch_sites():  # Fetch the org's sites first.
            return  # Abort if no sites could be fetched.
        if not self._step2_select_sites():  # Run step 2: site selection.
            return  # Abort the flow if selection failed.
        if not self._step3_fetch_available_versions():  # Run step 3: fetch available versions.
            return  # Abort if version fetch failed.
        if not self._step4_select_versions():  # Run step 4: version selection.
            return  # Abort if version selection failed.
        self._step5_configure_schedule()  # Run step 5: configure the schedule.
        self._step6_confirm_and_apply()  # Run step 6: confirm and apply.

    # ------------------------------------------------------------------
    # Step 1: Fetch sites
    # ------------------------------------------------------------------

    def _step1_fetch_sites(self) -> bool:  # Step 1: load the org's sites.
        """Fetch all sites in the organization."""
        print("-" * 70)  # Section divider.
        print("  STEP 1: Loading Sites")  # Step header.
        print("-" * 70)  # Section divider.

        try:
            self.all_sites = self.fetch_sites_fn(self.org_id)  # Fetch sites via the injected callable.
            if not self.all_sites:  # No sites returned.
                print("  X No sites found in organization")  # Tell the operator.
                return False  # Abort step 1.
            self.all_sites.sort(key=lambda s: s.get("name", "").lower())  # Sort sites by name for stable display.
            print(f"  + Found {len(self.all_sites)} site(s)")  # Confirm the site count.
            return True  # Step 1 succeeded.
        except Exception as exc:  # Fetch failed.
            print(f"  X Error fetching sites: {exc}")  # Tell the operator the error.
            logging.error("SiteAutoUpgradeConfigurator: Failed to fetch sites: %s", exc)  # Log the fetch failure.
            return False  # Abort step 1.

    # ------------------------------------------------------------------
    # Step 2: Select sites
    # ------------------------------------------------------------------

    def _step2_select_sites(self) -> bool:  # Step 2: choose which sites to configure.
        """Allow user to select sites with flexible options."""
        print("\n" + "-" * 70)  # Section divider.
        print("  STEP 2: Site Selection")  # Step header.
        print("-" * 70)  # Section divider.
        print("\n  Selection Options:")  # Options header.
        print("    [A] All sites in organization")  # All-sites option.
        print("    [S] Single site (interactive selection)")  # Single-site option.
        print("    [L] List view - select by index numbers\n")  # List-select option.

        try:
            choice = self.safe_input_fn("  Selection mode (A/S/L): ", "auto_upgrade_config").strip().upper()
        except SystemExit:  # Operator aborted at the prompt.
            return False  # Abort step 2.

        if choice == "S":  # Single-site mode chosen.
            return self._select_single_site()  # Delegate to single-site selection.
        if choice == "L":  # List mode chosen.
            return self._select_from_list()  # Delegate to list selection.
        return self._select_all_sites()  # Default to selecting all sites.

    def _select_all_sites(self) -> bool:  # Select every site in the org.
        """Select all sites."""
        self.selected_sites = self.all_sites.copy()  # Copy all sites as the selection.
        print(f"  + Selected ALL {len(self.selected_sites)} site(s)")  # Confirm the count.
        return True  # Selection succeeded.

    def _select_single_site(self) -> bool:  # Select exactly one site interactively.
        """Interactive single site selection."""
        _display_site_list(self.all_sites)  # Show the site list.
        try:
            selection = (  # Read the site index safely.
                self.safe_input_fn("  Enter site number (or 'q' to cancel): ", "auto_upgrade_config").strip().lower()
            )
        except SystemExit:  # Operator aborted at the prompt.
            return False  # Abort selection.

        if selection == "q":  # Operator quit.
            return False  # Abort selection.
        if not selection.isdigit():  # Non-numeric input.
            print("  Invalid input")  # Tell the operator.
            return False  # Abort selection.

        idx = int(selection) - 1  # Convert to a 0-based index.
        if not 0 <= idx < len(self.all_sites):  # Index out of range.
            print("  Invalid selection")  # Tell the operator.
            return False  # Abort selection.

        self.selected_sites = [self.all_sites[idx]]  # Select the single chosen site.
        self.is_single_site = True  # Mark single-site mode.
        print(f"  + Selected: {self.all_sites[idx].get('name')}")  # Confirm the chosen site.
        self._fetch_current_site_settings(self.all_sites[idx]["id"])  # Pull current settings for that site.
        return True  # Selection succeeded.

    def _fetch_current_site_settings(self, site_id: str) -> None:  # Read a site's existing auto-upgrade settings.
        """Fetch current auto-upgrade settings for a single site."""
        try:
            import mistapi.api.v1.sites.setting as sites_setting_api  # Import the site-settings API lazily.

            response = sites_setting_api.getSiteSettings(self.apisession, site_id)  # Fetch the site settings.
            if not response or not hasattr(response, "data") or not response.data:  # No usable settings payload.
                return  # Nothing to read.
            settings = response.data if isinstance(response.data, dict) else {}  # Use the dict payload or empty.
            auto_upgrade = settings.get("auto_upgrade", {})  # Read any existing auto_upgrade block.
            if not auto_upgrade:  # No auto-upgrade configured yet.
                return  # Nothing to pre-fill.
            self.current_site_versions = auto_upgrade.get("custom_versions", {})
            if auto_upgrade.get("day_of_week"):  # Existing schedule day present.
                self.schedule["day_of_week"] = auto_upgrade["day_of_week"]  # Pre-fill the schedule day.
            if auto_upgrade.get("time_of_day"):  # Existing schedule time present.
                self.schedule["time_of_day"] = auto_upgrade["time_of_day"]  # Pre-fill the schedule time.
            if self.current_site_versions:  # Found existing version config.
                count = len(self.current_site_versions)  # Count configured models.
                print(f"  + Current auto-upgrade settings found ({count} model(s) configured)")  # Tell the operator.
        except Exception as exc:  # Settings read failed.
            logging.debug("Could not fetch current site settings: %s", exc)  # Trace the (non-fatal) failure.

    def _select_from_list(self) -> bool:  # Select multiple sites by index list.
        """Display numbered list and allow index/range selection."""
        _display_site_list(self.all_sites)  # Show the site list.
        _display_selection_instructions()  # Show the selection instructions.

        try:
            selection = self.safe_input_fn("  Selection: ", "auto_upgrade_config").strip()
        except SystemExit:  # Operator aborted at the prompt.
            return False  # Abort selection.

        if not selection:  # Empty input.
            print("  No selection made")  # Tell the operator.
            return False  # Abort selection.

        indices = _parse_index_selection(selection)  # Parse the index expression.
        if not indices:  # No valid indices parsed.
            print("  X Invalid selection format")  # Tell the operator.
            return False  # Abort selection.

        return self._apply_site_indices(indices)  # Apply the parsed indices.

    def _apply_site_indices(self, indices: list[int]) -> bool:  # Resolve index list to selected sites.
        """Apply indices to select sites."""
        for idx in indices:  # Walk each requested index.
            if 1 <= idx <= len(self.all_sites):  # Keep only in-range indices.
                self.selected_sites.append(self.all_sites[idx - 1])  # Add the 1-based-indexed site.

        if not self.selected_sites:  # No valid sites resolved.
            print("  X No valid sites selected")  # Tell the operator.
            return False  # Abort selection.

        print(f"  + Selected {len(self.selected_sites)} site(s):")  # Confirm the selection count.
        for site in self.selected_sites[:5]:  # Preview the first few sites.
            print(f"      - {site.get('name')}")  # Print each previewed site.
        if len(self.selected_sites) > 5:  # More sites than previewed.
            print(f"      ... and {len(self.selected_sites) - 5} more")  # Note the remainder.
        return True  # Selection succeeded.

    # ------------------------------------------------------------------
    # Step 3: Fetch available versions
    # ------------------------------------------------------------------

    def _step3_fetch_available_versions(self) -> bool:  # Step 3: fetch available AP firmware versions.
        """Fetch available firmware versions."""
        print("\n" + "-" * 70)  # Section divider.
        print("  STEP 3: Available Firmware Versions")  # Step header.
        print("-" * 70)  # Section divider.
        print("  Fetching available AP firmware versions...")  # Tell the operator we are fetching.

        if self.apisession is None or self.org_id is None:  # Session or org not initialized.
            print("  X API session or org_id not initialized")  # Tell the operator.
            return False  # Abort step 3.

        try:
            import mistapi.api.v1.orgs.devices as org_devices_api  # Import the org-devices API lazily.

            response = org_devices_api.listOrgAvailableDeviceVersions(self.apisession, self.org_id, type="ap")
            if not response or not hasattr(response, "data"):  # No usable response.
                print("  X Failed to fetch available versions")  # Tell the operator.
                return False  # Abort step 3.

            self.available_versions = response.data if isinstance(response.data, list) else []
            self._build_model_version_map()  # Build the per-model version map.
            print(f"  + Found firmware for {len(self.model_version_map)} AP model(s)")  # Confirm model count.
            return True  # Step 3 succeeded.
        except Exception as exc:  # Version fetch failed.
            print(f"  X Error fetching firmware versions: {exc}")  # Tell the operator the error.
            logging.error("SiteAutoUpgradeConfigurator: Failed to fetch versions: %s", exc)  # Log the failure.
            return False  # Abort step 3.

    def _build_model_version_map(self) -> None:  # Group available versions by AP model.
        """Build model -> versions map from available versions."""
        for version_info in self.available_versions:  # Walk each version record.
            if not isinstance(version_info, dict):  # Skip malformed records.
                continue  # Continue to the next record.
            model = version_info.get("model")  # Read the model name.
            version = version_info.get("version")  # Read the version string.
            if model and version:  # Only map records with both.
                if model not in self.model_version_map:  # First version for this model.
                    self.model_version_map[model] = []  # Start the model's list.
                self.model_version_map[model].append(version_info)  # Append the version record.

    # ------------------------------------------------------------------
    # Step 4: Select versions
    # ------------------------------------------------------------------

    def _step4_select_versions(self) -> bool:  # Step 4: choose firmware versions per model.
        """Select firmware version per AP model."""
        _print_step4_header(self.is_single_site, self.current_site_versions)  # Print the step-4 header.
        if self.is_single_site and self.current_site_versions:  # Single-site with existing versions.
            self.custom_versions = self.current_site_versions.copy()  # Pre-fill from current site versions.

        model_families = _group_models_by_family(self.model_version_map)  # Group AP models into families.

        for family, models in sorted(model_families.items()):  # Walk each family in order.
            sorted_versions = _get_family_versions(self.model_version_map, models)
            if not sorted_versions:  # Skip families with no versions.
                continue  # Continue to the next family.

            current_version = _get_current_family_version(  # Resolve the family's current version.
                self.is_single_site,
                self.current_site_versions,
                models,
            )
            _display_family_versions(family, models, sorted_versions, current_version)

            try:
                choice = self.safe_input_fn(  # Read the operator's choice safely.
                    f"  Select version (1-{len(sorted_versions)}): ",
                    "auto_upgrade_config",
                ).strip()
            except SystemExit:  # Operator aborted at the prompt.
                return False  # Abort step 4.

            _apply_family_selection(
                choice,
                self.custom_versions,
                FamilySelectionContext(  # Issue #433 Phase B: 5-field bundle for the prompt inputs.
                    family=family,
                    models=models,
                    sorted_versions=sorted_versions,
                    current_version=current_version,
                    model_version_map=self.model_version_map,
                ),
            )

        if not self.custom_versions:  # No versions were selected.
            print("\n  X No versions selected")  # Tell the operator.
            return False  # Abort step 4.

        print(f"\n  + Configured {len(self.custom_versions)} model(s)")  # Confirm the configured model count.
        return True  # Step 4 succeeded.

    # ------------------------------------------------------------------
    # Step 5: Configure schedule
    # ------------------------------------------------------------------

    def _step5_configure_schedule(self) -> None:  # Step 5: configure the upgrade schedule.
        """Configure upgrade schedule."""
        print("\n" + "-" * 70)  # Section divider.
        print("  STEP 5: Schedule Configuration (Optional)")  # Step header.
        print("-" * 70)  # Section divider.
        print("\n  Configure when auto-upgrades should occur.\n")  # Explain the step.

        self.schedule["day_of_week"] = _prompt_day_of_week(self.safe_input_fn)  # Prompt and store the day-of-week.
        self.schedule["time_of_day"] = (
            _prompt_time_of_day(  # Issue #433 Phase B: was self._parse_time_input; canonical helper inlined.
                self.safe_input_fn,
                parse_time_input,
            )
        )

        day_display = self.schedule.get("day_of_week", "daily")  # Resolve the day for display.
        if day_display == "any":  # Normalize 'any' to 'daily'.
            day_display = "daily"  # Use the friendly label.
        time_display = self.schedule.get("time_of_day", "any time")  # Resolve the time for display.
        if time_display == "any":  # Normalize 'any' to 'any time'.
            time_display = "any time"  # Use the friendly label.
        print(f"  + Schedule: {day_display} at {time_display}")  # Show the chosen schedule.

    # Issue #433 Phase B: _parse_time_input static method removed (ARCH-DELEGATE).
    # The 1-line forwarder to module-level parse_time_input is replaced by direct
    # callers using parse_time_input() at the call site; see L486 in this file.

    # ------------------------------------------------------------------
    # Step 6: Confirm and apply
    # ------------------------------------------------------------------

    def _step6_confirm_and_apply(self) -> None:  # Step 6: confirm then apply the config.
        """Confirm settings and apply to selected sites."""
        print("\n" + "-" * 70)  # Section divider.
        print("  STEP 6: Confirm and Apply")  # Step header.
        print("-" * 70 + "\n")  # Section divider.

        _display_step6_summary(  # Show the pre-apply summary.
            self.selected_sites,
            self.custom_versions,
            self.schedule,
        )

        if not self.dry_run:  # Real run requires confirmation.
            try:
                confirm = self.safe_input_fn("  Apply these settings? (y/N): ", "auto_upgrade_config").strip().lower()
            except SystemExit:  # Operator aborted at the prompt.
                return  # Abort the apply.
            if confirm not in ("y", "yes"):  # Operator declined.
                print("  Cancelled.")  # Tell the operator.
                return  # Abort the apply.

        auto_upgrade = _build_auto_upgrade_payload(self.custom_versions, self.schedule)
        settings = {"auto_upgrade": auto_upgrade}  # Wrap it in the settings object.

        label = "DRY-RUN: Simulating" if self.dry_run else "Applying"  # Label reflects dry-run vs real apply.
        print(f"\n  {label} configuration...")  # Announce the apply.

        successful, failed = _apply_settings_to_sites(  # Apply settings to all selected sites.
            sites=self.selected_sites,
            settings=settings,
            apisession=self.apisession,
            check_stop_fn=self.check_stop_fn,
            dry_run=self.dry_run,
        )

        _print_final_summary(successful, failed, self.dry_run)  # Print the final success/failure summary.


# ======================================================================
# Module-level helper functions (reduce class CC)
# ======================================================================


def _handle_msp_mode(  # Dispatch single-org vs MSP multi-org mode.
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
    get_org_id_fn: GetOrgIdFn,
) -> None:
    """Handle MSP privilege detection and mode selection.

    Issue #433 Phase B: signature reduced from 9 params to 3 via the
    SiteAutoUpgradeCoreDeps + SiteAutoUpgradeMspDeps dataclasses.
    """
    logging.debug("Entering _handle_msp_mode")  # Action-log entry.
    print("\n" + "=" * 70)  # Visual banner -- ASCII only per logging standards.
    print("  SITE AUTO-UPGRADE CONFIGURATION")  # Header.
    print("=" * 70 + "\n")  # Divider.
    if core.dry_run:  # Dry-run banner only when relevant so non-dry runs aren't cluttered.
        print("  >> DRY-RUN MODE: No actual changes will be made <<\n")  # Warn dry-run is active.
    print("  MSP privileges detected. Select operation mode:\n")  # Explain MSP options.
    print("    [1] Single Organization - configure auto-upgrade for current org")  # Single-org option.
    print("    [2] MSP Multi-Org - configure ALL sites across multiple orgs\n")  # MSP multi-org option.

    try:
        mode = core.safe_input_fn("  Select mode (1-2) [1]: ", "msp_mode_select").strip() or "1"
    except SystemExit:  # safe_input raises SystemExit on container/SSH EOF -- bail cleanly.
        return  # Operator aborted.

    if mode == "2":  # Operator chose multi-org MSP workflow.
        logging.info("User selected MSP Multi-Org mode")  # Action-log the operator's choice.
        _execute_msp_mode(core, msp)  # 2-param dispatcher (dataclass + MSP-extras dataclass).
        return  # MSP mode owns the rest of the workflow.

    _run_single_org(core, get_org_id_fn)  # Fall back to single-org workflow with 2 params.


def _run_single_org(  # Run the single-org configuration path.
    core: SiteAutoUpgradeCoreDeps,
    get_org_id_fn: GetOrgIdFn,
) -> None:
    """Run single-org configuration workflow.

    Issue #433 Phase B: signature reduced from 6 params to 2 via the
    SiteAutoUpgradeCoreDeps dataclass.
    """
    logging.debug("Entering _run_single_org")  # Action-log entry.
    org_id = get_org_id_fn()  # Prompt operator (or read cache) for the target org id.
    if not org_id:  # No org id means the operator cancelled or no orgs are available.
        print("  X No organization selected")  # No org selected.
        return  # Bail out cleanly -- nothing to do.
    configurator = SiteAutoUpgradeConfigurator(  # Build the per-org workflow class (issue #433: deps via dataclass).
        org_id=org_id,
        deps=core,
    )
    configurator.run()  # Run the 6-step interactive workflow inside the configurator.


def _msp_select_entities(  # Select MSPs then their orgs.
    select_msps_fn: SelectMspsFn,
    select_orgs_fn: SelectOrgsFromMspFn,
) -> list[dict[str, Any]] | None:
    """Select MSPs and organizations for MSP mode.

    Returns:
        List of selected orgs, or None if selection cancelled.
    """
    print("\n" + "-" * 70)  # Section divider.
    print("  STEP 1: MSP Selection")  # Step header.
    print("-" * 70 + "\n")  # Section divider.
    selected_msps = select_msps_fn()  # Prompt for MSP selection.
    if not selected_msps:  # No MSPs chosen.
        print("  No MSPs selected. Returning.")  # Tell the operator.
        return None  # Abort entity selection.

    print("\n" + "-" * 70)  # Section divider.
    print("  STEP 2: Organization Selection")  # Step header.
    print("-" * 70 + "\n")  # Section divider.
    selected_orgs = select_orgs_fn(selected_msps)  # Prompt for org selection within the MSPs.
    if not selected_orgs:  # No orgs chosen.
        print("  No organizations selected. Returning.")  # Tell the operator.
        return None  # Abort entity selection.

    print(f"\n  Selected {len(selected_orgs)} organization(s)")  # Confirm the org count.
    result: list[dict[str, Any]] = list(selected_orgs)  # Materialize the selected orgs list.
    return result  # Return the selected orgs.


def _msp_get_firmware_config(  # Pick shared firmware versions for MSP orgs.
    apisession: Any,
    selected_orgs: list[dict[str, Any]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Prompt user for firmware version selection in MSP mode.

    Returns:
        Dict of model->version mappings, or None if cancelled.
        Empty dict means auto-detect.
    """
    print("\n" + "-" * 70)  # Section divider.
    print("  STEP 3: Firmware Version Configuration")  # Step header.
    print("-" * 70 + "\n")  # Section divider.
    print("  How to select firmware versions?\n")  # Explain the choice.
    print("    [1] Auto-detect latest stable per model for each org")  # Auto-detect option.
    print("    [2] Manually select firmware versions (from reference org)\n")  # Manual-select option.

    try:
        fw_choice = (  # Read the firmware-source choice.
            safe_input_fn(
                "  Selection (1-2) [1]: ",
                "msp_firmware",
            ).strip()
            or "1"
        )
    except SystemExit:  # Operator aborted at the prompt.
        return None  # Abort.

    if fw_choice != "2" or not selected_orgs:  # Not manual, or no orgs.
        return {}  # Use empty shared versions (auto per org).

    return _get_shared_firmware_versions(  # Pick shared versions from a reference org.
        apisession,
        selected_orgs[0],
        safe_input_fn,
    )


def _msp_confirm_and_apply(  # Confirm then apply across MSP orgs.
    core: SiteAutoUpgradeCoreDeps,
    selected_orgs: list[dict[str, Any]],
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
) -> None:
    """Display summary, confirm, and apply MSP configuration.

    Issue #433 Phase B: signature reduced from 8 params to 4 via the
    SiteAutoUpgradeCoreDeps dataclass.
    """
    logging.debug("Entering _msp_confirm_and_apply")  # Action-log entry.
    _display_msp_pre_apply_summary(  # Show operator the planned changes before they pull the trigger.
        shared_schedule,
        shared_versions,
        selected_orgs,
    )

    try:
        final_confirm = (  # Read the Y/n confirmation; defaults to Y on bare Enter for the common case.
            core.safe_input_fn(
                "  Apply this configuration? (Y/n): ",
                "msp_final_confirm",
            )
            .strip()
            .lower()
        )
    except SystemExit:  # safe_input raises SystemExit on container/SSH EOF -- bail cleanly.
        return  # Operator aborted.

    if final_confirm in ["n", "no"]:  # Explicit no -> abort without making changes.
        print("  Cancelled.")  # Operator declined.
        return  # Abort the apply.

    print("\n" + "-" * 70)  # Visual step separator -- ASCII only per logging standards.
    print("  STEP 6: Applying Configuration")  # Step header.
    print("-" * 70)  # Section divider.

    all_results = _apply_to_all_orgs(core, selected_orgs, shared_schedule, shared_versions)  # 4-param.
    _print_msp_summary(all_results, core.dry_run)  # Final results table for the operator.


def _execute_msp_mode(  # Execute the MSP multi-org flow.
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
) -> None:
    """Execute MSP multi-organization auto-upgrade configuration.

    Issue #433 Phase B: signature reduced from 7 params to 2 via the
    SiteAutoUpgradeCoreDeps + SiteAutoUpgradeMspDeps dataclasses.
    """
    logging.debug("Entering _execute_msp_mode")  # Action-log entry.

    if not msp.select_msps_fn or not msp.select_orgs_fn:  # MSP DI is optional at call boundary; guard here.
        print("  X MSP functions not available")  # MSP helper callables missing.
        return  # Bail out -- caller did not wire in MSP selection functions.

    selected_orgs = _msp_select_entities(msp.select_msps_fn, msp.select_orgs_fn)  # Step 1 + 2: pick MSPs and orgs.
    if not selected_orgs:  # Operator cancelled the selection.
        return  # Cleanly exit -- nothing to apply.

    shared_versions = _msp_get_firmware_config(  # Step 3: pick firmware versions to apply across all orgs.
        core.apisession,
        selected_orgs,
        core.safe_input_fn,
    )
    if shared_versions is None:  # None means the operator cancelled the firmware-version prompt.
        return  # Cleanly exit -- nothing to apply.

    print("\n" + "-" * 70)  # Visual step separator -- ASCII only per logging standards.
    print("  STEP 4: Schedule Configuration")  # Step header.
    print("-" * 70 + "\n")  # Section divider.
    shared_schedule = _get_shared_schedule(core.safe_input_fn)  # Step 4 + 5: pick day/time for all orgs.
    if shared_schedule is None:  # Operator cancelled the schedule prompt.
        return  # Cleanly exit -- nothing to apply.

    _msp_confirm_and_apply(  # Step 6: confirm + apply across every org (4-param signature).
        core,
        selected_orgs,
        shared_schedule,
        shared_versions if shared_versions else None,
    )


def _apply_to_all_orgs(  # Apply shared config to every selected org.
    core: SiteAutoUpgradeCoreDeps,
    selected_orgs: list[dict[str, Any]],
    shared_schedule: dict[str, Any],
    shared_versions: dict[str, str] | None,
) -> list[dict[str, Any]]:
    """Apply configuration to all selected organizations.

    Issue #433 Phase B: signature reduced from 8 params to 4 via the
    SiteAutoUpgradeCoreDeps dataclass.
    """
    logging.debug("Entering _apply_to_all_orgs for %d org(s)", len(selected_orgs))  # Action-log entry.
    all_results: list[dict[str, Any]] = []  # Accumulate one result dict per org.
    for idx, org_info in enumerate(selected_orgs, start=1):  # 1-based index for human-readable progress.
        org_id = org_info["id"]  # Pull the org id for the configurator + log lines.
        org_name = org_info["name"]  # Pull the org name purely for operator-visible logs.

        print(f"\n{'=' * 70}")  # Visual per-org separator -- ASCII only per logging standards.
        print(f"  ORGANIZATION {idx}/{len(selected_orgs)}: {org_name}")  # Per-org progress header.
        print("=" * 70)  # Divider.

        configurator = (
            SiteAutoUpgradeConfigurator(  # Build the per-org workflow class (issue #433: deps via dataclass).
                org_id=org_id,
                deps=core,
            )
        )
        configurator.msp_all_sites_mode = True  # Skip the site-selection prompt in MSP mode.
        configurator.org_name = org_name  # Set the org name on the configurator.
        configurator.schedule = shared_schedule.copy()  # Copy the shared schedule.
        configurator.shared_versions = shared_versions  # Attach the shared versions.

        success, site_count = configurator.run_msp_mode()  # Run the per-org MSP configuration.
        all_results.append(  # Record the org's result.
            {
                "org_id": org_id,
                "org_name": org_name,
                "success": success,
                "sites_configured": site_count,
            }
        )

    return all_results  # Return all per-org results.


# ======================================================================
# Pure helper functions
# ======================================================================


def _print_intro_header(dry_run: bool) -> None:  # Print the intro/warning header.
    """Print introduction header for the configuration workflow."""
    print("\n" + "=" * 70)  # Divider.
    print("  SITE AUTO-UPGRADE CONFIGURATION")  # Title.
    print("=" * 70 + "\n")  # Divider.
    if dry_run:  # Dry-run active.
        print("  >> DRY-RUN MODE: No actual changes will be made <<\n")  # Warn no changes will be made.
    print("  This tool configures auto-upgrade settings for sites WITHOUT")  # Explain the tool's behavior.
    print("  initiating immediate upgrades. Auto-upgrade ensures:")  # Explain auto-upgrade.
    print("    - New APs automatically upgrade to target firmware")  # Bullet: new APs.
    print("    - Scheduled upgrades during maintenance windows\n")  # Bullet: scheduled upgrades.


def _display_site_list(all_sites: list[dict[str, Any]]) -> None:  # Display the numbered site list.
    """Display numbered list of all sites."""
    print(f"\n  All Sites ({len(all_sites)} total):")  # List header with count.
    print("-" * 70)  # Divider.
    for idx, site in enumerate(all_sites, 1):  # Enumerate sites 1-based.
        print(f"    [{idx:>3}] {site.get('name', 'Unknown')}")  # Print each site.
    print("")  # Trailing spacer.


def _display_selection_instructions() -> None:  # Show index-selection instructions.
    """Display selection format instructions."""
    print("  Enter selection:")  # Instructions header.
    print("    - Single: 5")  # Single example.
    print("    - Multiple: 1,3,5,7")  # Multiple example.
    print("    - Range: 1-10")  # Range example.
    print("    - Combined: 1-5,8,12-15\n")  # Combined example.


def _parse_index_selection(selection: str) -> list[int]:  # Parse an index expression into a list.
    """Parse index selection string into sorted list of integers."""
    indices: set[int] = set()  # Collect distinct indices.
    parts = selection.replace(" ", "").split(",")  # Split on commas (whitespace stripped).

    for part in parts:  # Walk each comma-separated part.
        if "-" in part:  # Range expression.
            try:
                range_parts = part.split("-")  # Split the range.
                if len(range_parts) == 2:  # Well-formed start-end pair.
                    start = int(range_parts[0])  # Parse the start index.
                    end = int(range_parts[1])  # Parse the end index.
                    indices.update(range(start, end + 1))  # Add the inclusive range.
            except ValueError:  # Non-numeric range.
                continue  # Skip this part.
        else:
            try:
                indices.add(int(part))  # Add a single index.
            except ValueError:  # Non-numeric single index.
                continue  # Skip this part.

    return sorted(indices)  # Return the sorted distinct indices.


def _group_models_by_family(  # Group AP models into families.
    model_version_map: dict[str, list[Any]],
) -> dict[str, list[str]]:
    """Group models by family prefix (AP41, AP43, etc.)."""
    model_families: dict[str, list[str]] = {}  # Family -> member-models map.
    for model in sorted(model_version_map.keys()):  # Walk models in sorted order.
        family = model.rstrip("EP")  # Strip E/P suffixes to get the family.
        if family not in model_families:  # First model in this family.
            model_families[family] = []  # Start the family's list.
        model_families[family].append(model)  # Add the model to its family.
    return model_families  # Return the family map.


def _get_family_versions(  # Collect sorted versions across a family.
    model_version_map: dict[str, list[Any]],
    models: list[str],
) -> list[str]:
    """Get sorted versions for a model family."""
    family_versions: set[str] = set()  # Distinct version strings.
    for model in models:  # Walk each family model.
        for entry in model_version_map.get(model, []):  # Walk that model's version entries.
            if isinstance(entry, dict):  # Dict-shaped entry.
                version = entry.get("version")  # Read the version field.
            else:
                version = entry  # Entry is already a version string.
            if version:  # Only keep truthy versions.
                family_versions.add(str(version))  # Add the version string.
    return sorted(family_versions, reverse=True)  # Return newest-first versions.


def _get_current_family_version(  # Resolve a family's current version.
    is_single_site: bool,
    current_site_versions: dict[str, str],
    models: list[str],
) -> str | None:
    """Get current version for a model family if in single-site mode."""
    if not is_single_site:  # Only single-site has a current version.
        return None  # No current version otherwise.
    for model in models:  # Walk the family's models.
        if model in current_site_versions:  # Model has a configured version.
            return current_site_versions[model]  # Return it.
    return None  # No current version found.


def _display_family_versions(  # Display a family's version choices.
    family: str,
    models: list[str],
    sorted_versions: list[str],
    current_version: str | None,
) -> None:
    """Display version options for a model family."""
    print(f"\n  {family} family ({', '.join(models)}):")  # Family header with members.
    for idx, version in enumerate(sorted_versions, 1):  # Enumerate versions 1-based.
        marker = " <-- current" if version == current_version else ""  # Mark the current version.
        print(f"    [{idx:>2}] {version}{marker}")  # Print the numbered version.
    if current_version:  # A current version exists.
        print(f"    [Enter] Keep current: {current_version}")  # Offer to keep it on Enter.
    else:
        print("    [Enter] Skip")  # Offer to skip on Enter.


def _apply_family_selection(  # Apply the operator's family selection.
    choice: str,
    custom_versions: dict[str, str],
    ctx: FamilySelectionContext,
) -> None:
    """Apply user's version selection for a model family.

    Issue #433 Phase B: signature reduced from 7 params to 3 via the
    FamilySelectionContext dataclass.
    """
    logging.debug("Entering _apply_family_selection for family %s", ctx.family)  # Action-log entry.
    if choice and choice.isdigit():  # Operator typed a number -> they picked a specific version.
        idx = int(choice) - 1  # Translate from 1-based display to 0-based list index.
        if 0 <= idx < len(ctx.sorted_versions):  # Guard the index against off-by-one mistakes.
            selected = ctx.sorted_versions[idx]  # Pull the chosen version string.
            for model in ctx.models:  # Apply the same chosen version across every model in this family.
                model_versions = _extract_version_strings(  # Pull the per-model version list to validate availability.
                    ctx.model_version_map.get(model, []),
                )
                if selected in model_versions:  # Only set when the chosen version actually exists for this model.
                    custom_versions[model] = selected  # Record the selection in the operator-mutable dict.
            print(f"    + Set {ctx.family} models to {selected}")  # Confirm to operator with the chosen version.
    elif not choice and ctx.current_version:  # Bare Enter + currently-set version -> keep current.
        print(f"    + Keeping {ctx.family} models at {ctx.current_version}")  # Keeping the current version.
    elif not choice:  # Bare Enter + no current version -> skip this family entirely.
        print(f"    - Skipped {ctx.family} family")  # Skipping the family.


def _extract_version_strings(entries: list[Any]) -> list[str]:  # Extract version strings from entries.
    """Extract version strings from a list of version entries."""
    result: list[str] = []  # Collected version strings.
    for entry in entries:  # Walk each entry.
        if isinstance(entry, dict):  # Dict-shaped entry.
            ver = entry.get("version")  # Read the version field.
        else:
            ver = entry  # Entry is already a version string.
        if ver:  # Only keep truthy versions.
            result.append(str(ver))  # Add the version string.
    return result  # Return the strings.


def _print_step4_header(  # Print the step-4 header.
    is_single_site: bool,
    current_site_versions: dict[str, str],
) -> None:
    """Print step 4 header and instructions."""
    print("\n" + "-" * 70)  # Section divider.
    print("  STEP 4: Firmware Version Selection")  # Step header.
    print("-" * 70 + "\n")  # Section divider.
    print("  Select firmware version for each AP model family.")  # Explain per-family selection.
    if is_single_site and current_site_versions:  # Single-site with existing config.
        print("  Press Enter to keep current version, or select a new one.")  # Explain Enter-keeps-current.
        print(f"  (Pre-loaded {len(current_site_versions)} existing model configurations)")
    else:
        print("  Press Enter to skip a model (won't be included in auto-upgrade).")  # Explain Enter-skips the model.
    print("")  # Spacer.


def _pick_stable_version(versions: list[Any]) -> str:  # Pick the most stable version available.
    """Pick the latest stable version from a list of version entries."""
    stable = [v for v in versions if isinstance(v, dict) and v.get("tag") == "stable"]
    if stable:  # Stable versions exist.
        return str(stable[0].get("version", ""))  # Return the first stable version.
    if versions:  # Fall back to any version.
        first = versions[0]  # Take the first entry.
        if isinstance(first, dict):  # Dict-shaped entry.
            return str(first.get("version", ""))  # Return its version field.
        return str(first)  # Return the entry as a string.
    return ""  # No versions: empty string.


def _prompt_day_of_week(safe_input_fn: SafeInputFn) -> str:  # Prompt for the upgrade day-of-week.
    """Prompt for day of week selection."""
    print("  Day of week options:")  # Options header.
    print("    [1] Daily (any day)  [2] Sunday   [3] Monday")  # Daily/Sun/Mon row.
    print("    [4] Tuesday          [5] Wednesday [6] Thursday")  # Tue/Wed/Thu row.
    print("    [7] Friday           [8] Saturday")  # Fri/Sat row.

    day_map = {  # Choice -> day-name map.
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
    except SystemExit:  # Operator aborted.
        choice = "1"  # Default to daily.
    return day_map.get(choice, "any")  # Resolve choice to a day (default any).


def _prompt_time_of_day(  # Prompt for the upgrade time-of-day.
    safe_input_fn: SafeInputFn,
    parse_fn: Any,
) -> str:
    """Prompt for time of day selection."""
    print("\n  Time of day for upgrades:")  # Explain the time prompt.
    print("    Examples: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM")  # Show accepted formats.
    print("    Leave blank for any time")  # Blank means any time.
    try:
        time_input = safe_input_fn("  Time: ", "auto_upgrade_config").strip()  # Read the time input.
    except SystemExit:  # Operator aborted.
        time_input = ""  # Default to blank.
    result: str = parse_fn(time_input)  # Parse the time via the injected parser.
    return result  # Return the parsed time.


def parse_time_input(time_input: str) -> str:  # Parse a free-form time string to HH:MM.
    """Parse various time formats to HH:MM for the API.

    Accepts: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM, etc.
    Returns: HH:MM format string, or 'any' for any time.
    """
    if not time_input:  # Empty input.
        return "any"  # Return 'any'.

    time_upper = time_input.upper().strip()  # Uppercase and trim.
    is_pm = "PM" in time_upper  # Detect PM marker.
    is_am = "AM" in time_upper  # Detect AM marker.
    time_clean = time_upper.replace("AM", "").replace("PM", "").strip()  # Strip AM/PM markers.

    hour, minute = _parse_hour_minute(time_clean)  # Parse hour and minute.
    if hour < 0:  # Unparseable hour.
        return "any"  # Return 'any'.

    hour = _apply_ampm(hour, is_am, is_pm)  # Apply AM/PM 24h conversion.

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:  # Out-of-range hour/minute.
        return "any"  # Return 'any'.

    return f"{hour:02d}:{minute:02d}"  # Return zero-padded HH:MM.


def _parse_hour_minute(time_clean: str) -> tuple[int, int]:  # Parse hour/minute from a clean string.
    """Parse hour and minute from cleaned time string."""
    if ":" in time_clean:  # Has an explicit minute.
        parts = time_clean.split(":")  # Split hour and minute.
        try:
            hour = int(parts[0])  # Parse the hour.
            minute = int(parts[1]) if len(parts) > 1 else 0  # Parse the minute (default 0).
            return (hour, minute)  # Return the pair.
        except ValueError:  # Non-numeric time.
            return (-1, 0)  # Signal a parse failure.
    try:
        return (int(time_clean), 0)  # Hour-only input.
    except ValueError:  # Non-numeric hour.
        return (-1, 0)  # Signal a parse failure.


def _apply_ampm(hour: int, is_am: bool, is_pm: bool) -> int:  # Convert a 12h hour to 24h using AM/PM.
    """Apply AM/PM conversion to hour value."""
    if is_pm and hour < 12:  # PM and not noon.
        hour += 12  # Shift into the afternoon.
    elif is_am and hour == 12:  # AM and midnight (12 AM).
        hour = 0  # Map 12 AM to hour 0.
    return hour  # Return the 24h hour.


def _display_step6_summary(  # Print the step-6 pre-apply summary.
    selected_sites: list[dict[str, Any]],
    custom_versions: dict[str, str],
    schedule: dict[str, Any],
) -> None:
    """Display configuration summary for step 6."""
    day_display = schedule.get("day_of_week") or "daily"  # Resolve the display day.
    time_display = schedule.get("time_of_day") or "any time"  # Resolve the display time.
    print("  Summary:")  # Summary header.
    print(f"    Sites: {len(selected_sites)}")  # Show the site count.
    print(f"    Models configured: {len(custom_versions)}")  # Show the model count.
    for model, version in sorted(custom_versions.items()):  # List each model/version.
        print(f"      {model}: {version}")  # Print the pair.
    print(f"    Schedule: {day_display} at {time_display}\n")  # Show the schedule.


def _build_auto_upgrade_payload(  # Build the auto_upgrade settings payload.
    custom_versions: dict[str, str],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    """Build the auto-upgrade configuration payload."""
    return {  # Return the Mist auto_upgrade object.
        "enabled": True,
        "version": "custom",
        "custom_versions": custom_versions,
        "day_of_week": schedule.get("day_of_week", "any"),
        "time_of_day": schedule.get("time_of_day", "any"),
    }


def _apply_settings_to_sites(  # Apply settings to each site, counting results.
    sites: list[dict[str, Any]],
    settings: dict[str, Any],
    apisession: Any,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
) -> tuple[int, int]:
    """Apply settings to sites. Returns (successful, failed) counts."""
    successful = 0  # Success counter.
    failed = 0  # Failure counter.
    for site in sites:  # Walk each site.
        if check_stop_fn():  # Honor a stop request.
            break  # Stop processing sites.
        site_id = site.get("id")  # Read the site id.
        site_name = site.get("name", "Unknown")  # Read the site name.
        if not site_id:  # Missing site id.
            failed += 1  # Count as a failure.
            continue  # Skip this site.
        try:
            if dry_run:  # Dry-run path.
                print(f"    [DRY-RUN] {site_name}")  # Report the would-apply.
            else:
                import mistapi.api.v1.sites.setting as sites_setting_api  # Import the settings API lazily.

                sites_setting_api.updateSiteSettings(  # Push the updated settings.
                    apisession,
                    site_id,
                    body=settings,
                )
                print(f"    [OK] {site_name}")  # Report success.
            successful += 1  # Count the success.
        except Exception as exc:  # Apply failed for this site.
            print(f"    [FAIL] {site_name}: {exc}")  # Report the failure.
            logging.error("Failed to configure auto-upgrade for site %s: %s", site_name, exc)  # Log the failure.
            failed += 1  # Count the failure.
    return (successful, failed)  # Return success/failure counts.


def _print_final_summary(  # Print the final single-org summary.
    successful: int,
    failed: int,
    dry_run: bool,
) -> None:
    """Print final summary after applying configuration."""
    print("\n" + "=" * 70)  # Divider.
    print(f"  {'DRY-RUN COMPLETE' if dry_run else 'CONFIGURATION COMPLETE'}")  # Completion title (dry-run aware).
    print("=" * 70)  # Divider.
    if dry_run:  # Dry-run path.
        print(f"    Would configure: {successful} site(s)")  # Show would-configure count.
    else:
        print(f"    Successful: {successful} site(s)")  # Show successful count.
    if failed > 0:  # Some sites failed.
        print(f"    Failed: {failed} site(s)")  # Show failed count.
    if dry_run:  # Dry-run path.
        print("\n  >> To apply changes, run without --dry-run flag")  # Tell the operator how to apply.
    print("")  # Spacer.


def _compute_msp_totals(  # Compute MSP roll-up totals.
    results: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Compute total orgs, successful orgs, and total sites from results."""
    total_orgs = len(results)  # Count orgs processed.
    successful_orgs = sum(1 for r in results if r["success"])  # Count successful orgs.
    total_sites = sum(r["sites_configured"] for r in results)  # Sum configured sites.
    return total_orgs, successful_orgs, total_sites  # Return the totals.


def _print_msp_failed_orgs(results: list[dict[str, Any]]) -> None:  # List MSP orgs that failed.
    """Print list of failed organizations from MSP results."""
    print("  Failed organizations:")  # Failed-orgs header.
    for result in results:  # Walk each result.
        if not result["success"]:  # Org failed.
            print(f"    - {result['org_name']}")  # Print the org name.
    print("")  # Spacer.


def _print_msp_summary(  # Print the MSP multi-org summary.
    results: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Print summary of MSP multi-org auto-upgrade configuration."""
    print("\n" + "=" * 70)  # Divider.
    label = "MSP MULTI-ORG AUTO-UPGRADE SUMMARY"  # Summary title.
    if dry_run:  # Dry-run path.
        label += " (DRY-RUN)"  # Annotate dry-run.
    print(f"  {label}")  # Print the title.
    print("=" * 70 + "\n")  # Divider.

    if dry_run:  # Dry-run path.
        print("  >> DRY-RUN MODE: No actual changes were made <<\n")  # Warn no changes made.

    total_orgs, successful_orgs, total_sites = _compute_msp_totals(results)  # Compute the roll-up totals.

    print(f"  Organizations processed: {total_orgs}")  # Show orgs processed.
    if dry_run:  # Dry-run path.
        print(f"  Would configure: {successful_orgs} org(s)")  # Show would-configure orgs.
        print(f"  Total sites WOULD be configured: {total_sites}")  # Show would-configure sites.
    else:
        print(f"  Successful: {successful_orgs}")  # Show successful orgs.
        print(f"  Total sites configured: {total_sites}")  # Show configured sites.
    print("")  # Spacer.

    if successful_orgs < total_orgs:  # Some orgs failed.
        _print_msp_failed_orgs(results)  # List the failed orgs.

    if dry_run:  # Dry-run path.
        print("  >> To apply changes, run without --dry-run flag")  # Tell the operator how to apply.
    else:
        print("  Configuration complete.")  # Report completion.


def _get_shared_schedule(  # Prompt for the shared MSP schedule.
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Get shared schedule settings for MSP mode."""
    print("  Schedule Configuration:")  # Schedule header.
    print("    When should auto-upgrades occur?\n")  # Explain the prompt.
    print("    Day of week:")  # Day-of-week header.
    print("      [1] any - Any day")  # Any-day option.
    print("      [2] mon, tue, wed, thu, fri, sat, sun\n")  # Weekday options.

    try:
        day_input = (  # Read the day input.
            safe_input_fn(
                "  Day of week [any]: ",
                "msp_schedule",
            )
            .strip()
            .lower()
            or "any"
        )
    except SystemExit:  # Operator aborted.
        return None  # Abort with no schedule.

    day_map = {  # Day-input -> day-name map.
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
    day_of_week = day_map.get(day_input, "any")  # Resolve the day (default any).

    print(f"    + Day: {day_of_week}\n")  # Confirm the chosen day.
    print("    Time of day (HH:MM in site's local timezone, or 'any'):")  # Time prompt explanation.

    try:
        time_input = (  # Read the time input.
            safe_input_fn(
                "  Time of day [02:00]: ",
                "msp_schedule",
            ).strip()
            or "02:00"
        )
    except SystemExit:  # Operator aborted.
        return None  # Abort with no schedule.

    time_of_day = time_input if time_input.lower() != "any" else "any"  # Normalize 'any' time.
    print(f"    + Time: {time_of_day}")  # Confirm the chosen time.

    return {"day_of_week": day_of_week, "time_of_day": time_of_day}  # Return the shared schedule.


def _get_shared_firmware_versions(  # Pick shared firmware versions from a reference org.
    apisession: Any,
    reference_org: dict[str, Any],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Fetch firmware versions from a reference org and let user select.

    Returns:
        Dict mapping model to selected version, None if cancelled,
        empty dict if no selection.
    """
    org_id = reference_org.get("id")  # Read the reference org id.
    org_name = reference_org.get("name", "Unknown")  # Read the reference org name.

    if not org_id or apisession is None:  # Missing org id or session.
        print("  X Missing organization ID or API session")  # Tell the operator.
        return {}  # Return empty versions.

    org_id_str: str = str(org_id)  # Stringify the org id.
    print(f"\n  Fetching available firmware versions from: {org_name}")  # Announce the fetch source.

    try:
        import mistapi.api.v1.orgs.devices as org_devices_api  # Import the org-devices API lazily.

        response = org_devices_api.listOrgAvailableDeviceVersions(  # List available AP firmware versions.
            apisession,
            org_id_str,
            type="ap",
        )
        if not response or not hasattr(response, "data"):  # No usable response.
            print("  X Failed to fetch available firmware versions")  # Tell the operator.
            return {}  # Return empty versions.

        available_versions = response.data if isinstance(response.data, list) else []  # Use the list payload or empty.
    except Exception as error:  # Fetch failed.
        print(f"  X Error fetching firmware versions: {error}")  # Tell the operator.
        return {}  # Return empty versions.

    model_version_map = _build_version_map_from_list(available_versions)  # Build the per-model version map.
    if not model_version_map:  # No versions mapped.
        print("  X No AP firmware versions found")  # Tell the operator.
        return {}  # Return empty versions.

    print(f"  + Found firmware for {len(model_version_map)} AP model(s)")  # Confirm model count.
    model_families = _group_models_for_msp(model_version_map)  # Group models into families.

    return _select_versions_interactively(  # Select shared versions interactively.
        model_families,
        model_version_map,
        safe_input_fn,
    )


def _build_version_map_from_list(  # Build a model->versions map from a list.
    available_versions: list[Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build model -> versions map from API response."""
    result: dict[str, list[dict[str, Any]]] = {}  # Result map.
    for entry in available_versions:  # Walk each version record.
        if not isinstance(entry, dict):  # Skip malformed records.
            continue  # Continue to the next.
        model = entry.get("model")  # Read the model.
        version = entry.get("version")  # Read the version.
        tag = entry.get("tag", "")  # Read the release tag.
        if model and version:  # Only map records with model+version.
            if model not in result:  # First version for this model.
                result[model] = []  # Start the model's list.
            result[model].append({"version": version, "tag": tag})  # Append the version+tag.
    return result  # Return the map.


def _group_models_for_msp(  # Group MSP models into families.
    model_version_map: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    """Group models by family for MSP firmware selection."""
    model_families: dict[str, list[str]] = {}  # Family -> models map.
    for model in sorted(model_version_map.keys()):  # Walk models in sorted order.
        family = model.rstrip("EP")  # Strip E/P suffixes to get the family.
        if family not in model_families:  # First model in this family.
            model_families[family] = []  # Start the family's list.
        model_families[family].append(model)  # Add the model.
    return model_families  # Return the family map.


def _collect_family_versions(  # Collect a family's distinct versions+tags.
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
) -> list[tuple[str, str]]:
    """Collect and sort unique versions for a model family.

    Returns:
        Sorted list of (version, tag) tuples, newest first.
    """
    family_versions: set[tuple[str, str]] = set()  # Distinct (version, tag) pairs.
    for model in models:  # Walk the family's models.
        for v_info in model_version_map.get(model, []):  # Walk each model's versions.
            family_versions.add((v_info["version"], v_info.get("tag", "")))  # Record the version and tag.
    return sorted(list(family_versions), key=lambda x: x[0], reverse=True)  # Return newest-first pairs.


def _display_msp_family_versions(  # Display an MSP family's version choices.
    family: str,
    models: list[str],
    sorted_versions: list[tuple[str, str]],
) -> None:
    """Display available firmware versions for a model family."""
    print(f"\n  {family} family ({', '.join(models)}):")  # Family header with members.
    for idx, (version, tag) in enumerate(sorted_versions, 1):  # Enumerate versions 1-based.
        tag_display = f" [{tag}]" if tag else ""  # Show the release tag if present.
        print(f"    [{idx:>2}] {version}{tag_display}")  # Print the numbered version.
    print("    [Enter] Skip this family")  # Offer to skip on Enter.


def _apply_version_to_models(  # Apply a chosen version to a family's models.
    selected_version: str,
    family: str,
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
    custom_versions: dict[str, str],
) -> None:
    """Apply a selected version to all compatible models in a family."""
    for model in models:  # Walk the family's models.
        model_versions = [v["version"] for v in model_version_map.get(model, [])]
        if selected_version in model_versions:  # Version is valid for this model.
            custom_versions[model] = selected_version  # Record the model's version.
    print(f"    + Set {family} family to {selected_version}")  # Confirm the family selection.


def _select_versions_interactively(  # Interactively select versions per family.
    model_families: dict[str, list[str]],
    model_version_map: dict[str, list[dict[str, Any]]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Interactively select firmware versions per model family."""
    print("\n  Select firmware version for each AP model family.")  # Explain per-family selection.
    print("  Press Enter to skip a family (won't be configured).")  # Enter skips a family.
    print("  Enter 'q' to cancel selection.")  # 'q' cancels selection.

    custom_versions: dict[str, str] = {}  # Operator-chosen versions.

    for family, models in sorted(model_families.items()):  # Walk families in order.
        sorted_versions = _collect_family_versions(models, model_version_map)  # Collect the family's versions.
        if not sorted_versions:  # Skip families with no versions.
            continue  # Continue to the next family.

        _display_msp_family_versions(family, models, sorted_versions)  # Show the family's choices.

        try:
            choice = safe_input_fn(  # Read the choice safely.
                f"  Select version (1-{len(sorted_versions)}): ",
                "msp_firmware_select",
            ).strip()
        except SystemExit:  # Operator aborted.
            return None  # Abort selection.

        if choice.lower() == "q":  # Operator cancelled.
            return None  # Abort selection.

        if choice and choice.isdigit():  # Numeric choice given.
            idx = int(choice) - 1  # Convert to a 0-based index.
            if 0 <= idx < len(sorted_versions):  # In range.
                _apply_version_to_models(  # Apply the chosen version.
                    sorted_versions[idx][0],
                    family,
                    models,
                    model_version_map,
                    custom_versions,
                )
            else:
                print(f"    - Invalid selection, skipped {family}")  # Out-of-range selection.
        else:
            print(f"    - Skipped {family} family")  # Empty choice skips the family.

    return custom_versions  # Return the selected versions.


def _display_msp_pre_apply_summary(  # Print the MSP pre-apply summary.
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
    selected_orgs: list[dict[str, Any]],
) -> None:
    """Display summary before MSP configuration application."""
    print("\n  Configuration to apply:")  # Summary header.
    print(f"    - Day of week: {shared_schedule.get('day_of_week', 'any')}.")  # Show the schedule day.
    time_display = shared_schedule.get("time_of_day", "02:00")  # Resolve the display time.
    print(f"    - Time of day: {time_display} (site's local timezone)")  # Show the schedule time.
    if shared_versions:  # Versions were manually selected.
        print(f"    - Firmware: Manually selected ({len(shared_versions)} models)")  # Show the manual selection count.
        for model, version in sorted(shared_versions.items()):  # List each model/version.
            print(f"        {model}: {version}")  # Print the pair.
    else:
        print("    - Firmware: Latest stable per model (auto-detected)")  # Auto-detected versions otherwise.
    print(f"    - Organizations: {len(selected_orgs)}\n")  # Show the org count.
