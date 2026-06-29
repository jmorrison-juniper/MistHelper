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

    def _print_shared_version_summary(self) -> None:  # Show the pre-selected shared MSP versions for this org.
        """Print shared firmware versions reused during MSP mode."""
        print(
            f"\n  Using pre-selected firmware versions ({len(self.custom_versions)} models):"
        )  # Announce shared version reuse.
        for model, version in sorted(self.custom_versions.items()):  # Walk each model/version pair in order.
            print(f"    {model}: {version}")  # Print the model/version pair for operator visibility.

    def _prepare_msp_versions(self) -> bool:  # Resolve firmware versions for one org in MSP mode.
        """Load shared versions or auto-select per-model versions for MSP mode."""
        if self.shared_versions:  # Shared versions were pre-selected earlier in the MSP workflow.
            self.custom_versions = self.shared_versions.copy()  # Copy shared versions so per-org runs stay isolated.
            self._print_shared_version_summary()  # Show the reused shared versions before applying them.
            return True  # Version preparation succeeded using shared selections.
        if (
            not self._step3_fetch_available_versions()
        ):  # Shared versions absent, so fetch this org's available versions.
            return False  # Abort version preparation when the fetch fails.
        return self._auto_select_versions()  # Auto-pick stable versions for this org's models.

    def run_msp_mode(self) -> tuple[bool, int]:  # Run the MSP bulk all-sites configuration flow.
        """Execute configuration workflow for MSP mode (all sites)."""
        logging.debug("Entering run_msp_mode() for org: %s", self.org_name)  # Trace entry for the MSP flow.

        if not self._step1_fetch_sites():  # Fetch the org's sites first.
            return (False, 0)  # Abort with zero configured on fetch failure.

        self.selected_sites = self.all_sites.copy()  # MSP mode auto-selects every site.
        print(f"  + Auto-selected ALL {len(self.selected_sites)} site(s)")

        if not self._prepare_msp_versions():  # Resolve shared or auto-selected firmware versions for this org.
            return (False, 0)  # Abort when no firmware versions could be prepared.

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

    def _extract_site_auto_upgrade(
        self, response: Any
    ) -> dict[str, Any]:  # Pull the auto-upgrade block from site settings.
        """Extract the auto_upgrade settings block from a site-settings response."""
        if not response or not hasattr(response, "data"):  # Response missing or malformed.
            return {}  # Return empty settings when nothing usable exists.
        payload = response.data  # Read the raw response payload.
        if not isinstance(payload, dict):  # Payload must be a dict for settings access.
            return {}  # Return empty settings for non-dict payloads.
        auto_upgrade = payload.get("auto_upgrade", {})  # Pull the nested auto_upgrade block.
        if not isinstance(auto_upgrade, dict):  # auto_upgrade must be a dict to be useful.
            return {}  # Return empty settings for malformed auto_upgrade blocks.
        return auto_upgrade  # Return the validated auto-upgrade settings.

    def _apply_current_site_schedule(
        self, auto_upgrade: dict[str, Any]
    ) -> None:  # Pre-load current schedule fields from site settings.
        """Apply existing schedule values from an auto-upgrade settings block."""
        day_of_week = auto_upgrade.get("day_of_week")  # Read the existing day-of-week value.
        if day_of_week:  # Only write back truthy day values.
            self.schedule["day_of_week"] = day_of_week  # Pre-fill the schedule day for the operator.
        time_of_day = auto_upgrade.get("time_of_day")  # Read the existing time-of-day value.
        if time_of_day:  # Only write back truthy time values.
            self.schedule["time_of_day"] = time_of_day  # Pre-fill the schedule time for the operator.

    def _print_current_site_settings_summary(self) -> None:  # Summarize any pre-existing model selections for a site.
        """Print summary of existing per-model auto-upgrade selections."""
        if not self.current_site_versions:  # Nothing configured means nothing to summarize.
            return  # Exit quietly when no current versions exist.
        count = len(self.current_site_versions)  # Count configured models for the summary.
        print(f"  + Current auto-upgrade settings found ({count} model(s) configured)")  # Confirm discovered config.

    def _fetch_site_auto_upgrade_block(
        self, site_id: str
    ) -> dict[str, Any]:  # Fetch and normalize one site's auto-upgrade settings block.
        """Fetch the raw auto-upgrade settings block for one site."""
        import mistapi.api.v1.sites.setting as sites_setting_api  # Import the site-settings API lazily.

        response = sites_setting_api.getSiteSettings(
            self.apisession, site_id
        )  # Fetch the site's settings payload from Mist.
        auto_upgrade = self._extract_site_auto_upgrade(
            response
        )  # Extract the validated auto-upgrade block from the API payload.
        return auto_upgrade  # Return the normalized auto-upgrade block for downstream processing.

    def _store_current_site_versions(
        self, auto_upgrade: dict[str, Any]
    ) -> None:  # Persist current per-model versions from a site's auto-upgrade block.
        """Store the current site's custom version selections when present."""
        custom_versions = auto_upgrade.get(
            "custom_versions", {}
        )  # Read the existing custom version mapping from the site settings.
        self.current_site_versions = (
            custom_versions if isinstance(custom_versions, dict) else {}
        )  # Keep only dict-shaped custom version data to avoid malformed payloads.

    def _fetch_current_site_settings(self, site_id: str) -> None:  # Read a site's existing auto-upgrade settings.
        """Fetch current auto-upgrade settings for a single site."""
        try:
            auto_upgrade = self._fetch_site_auto_upgrade_block(
                site_id
            )  # Fetch and normalize the site's auto-upgrade settings block in one step.
            if not auto_upgrade:  # No auto-upgrade configured yet.
                return  # Nothing to pre-fill.
            self._store_current_site_versions(
                auto_upgrade
            )  # Persist current per-model version overrides from the site settings block.
            self._apply_current_site_schedule(auto_upgrade)  # Pre-fill schedule values for the current site.
            self._print_current_site_settings_summary()  # Tell the operator what existing config was discovered.
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

    def _resolve_selected_sites(
        self, indices: list[int]
    ) -> list[dict[str, Any]]:  # Resolve requested indices to in-range site records.
        """Resolve validated indices into a list of selected site dicts."""
        selected_sites: list[dict[str, Any]] = []  # Start with an empty selection list.
        for idx in indices:  # Walk each requested 1-based index.
            if 1 <= idx <= len(self.all_sites):  # Keep only indices that point at an actual site.
                selected_sites.append(self.all_sites[idx - 1])  # Add the referenced site to the result list.
        return selected_sites  # Return every resolved site in request order.

    def _print_selected_site_preview(self) -> None:  # Show a short preview of the chosen site list.
        """Print a preview of selected sites for operator confirmation."""
        print(f"  + Selected {len(self.selected_sites)} site(s):")  # Confirm the final selection count.
        for site in self.selected_sites[:5]:  # Preview only the first few sites to keep output readable.
            print(f"      - {site.get('name')}")  # Print each previewed site name.
        if len(self.selected_sites) > 5:  # More sites exist beyond the preview window.
            print(f"      ... and {len(self.selected_sites) - 5} more")  # Report the number of additional sites.

    def _apply_site_indices(self, indices: list[int]) -> bool:  # Resolve index list to selected sites.
        """Apply indices to select sites."""
        self.selected_sites = self._resolve_selected_sites(
            indices
        )  # Resolve the requested indices into actual site records.
        if not self.selected_sites:  # No valid sites resolved.
            print("  X No valid sites selected")  # Tell the operator.
            return False  # Abort selection.
        self._print_selected_site_preview()  # Show the operator a short preview of the resolved sites.
        return True  # Selection succeeded.

    # ------------------------------------------------------------------
    # Step 3: Fetch available versions
    # ------------------------------------------------------------------

    def _can_fetch_available_versions(self) -> bool:  # Validate state required for firmware-version fetch.
        """Return True when API session and org id are available for version fetch."""
        if self.apisession is None or self.org_id is None:  # Session or org context missing prevents the API query.
            print("  X API session or org_id not initialized")  # Tell the operator the fetch cannot proceed yet.
            return False  # Abort step 3 when required context is missing.
        return True  # Required API context exists.

    def _populate_available_versions(self) -> bool:  # Fetch versions and build the per-model map.
        """Fetch available versions and build the model-version map."""
        self.available_versions = (
            self._fetch_available_ap_versions()
        )  # Fetch the organization's available AP firmware versions from Mist.
        if self.available_versions is None:  # None means the API helper could not produce a usable payload.
            print("  X Failed to fetch available versions")  # Tell the operator the fetch failed.
            return False  # Abort step 3 because no usable versions are available.
        self._build_model_version_map()  # Rebuild the model->versions map from the fetched payload.
        print(
            f"  + Found firmware for {len(self.model_version_map)} AP model(s)"
        )  # Confirm the number of AP models with available firmware.
        return True  # Step 3 data preparation succeeded.

    def _step3_fetch_available_versions(self) -> bool:  # Step 3: fetch available AP firmware versions.
        """Fetch available firmware versions."""
        print("\n" + "-" * 70)  # Section divider.
        print("  STEP 3: Available Firmware Versions")  # Step header.
        print("-" * 70)  # Section divider.
        print("  Fetching available AP firmware versions...")  # Tell the operator we are fetching.

        if not self._can_fetch_available_versions():  # Missing session or org context blocks firmware-version fetch.
            return False  # Abort step 3 until required API context exists.

        try:
            return (
                self._populate_available_versions()
            )  # Fetch versions and build the model-version map in one focused helper.
        except Exception as exc:  # Version fetch failed.
            print(f"  X Error fetching firmware versions: {exc}")  # Tell the operator the error.
            logging.error("SiteAutoUpgradeConfigurator: Failed to fetch versions: %s", exc)  # Log the failure.
            return False  # Abort step 3.

    def _fetch_available_ap_versions(
        self,
    ) -> list[Any] | None:  # Query Mist for available AP firmware versions for this org.
        """Fetch available AP firmware versions for the current organization."""
        import mistapi.api.v1.orgs.devices as org_devices_api  # Import the org-devices API lazily.

        response = org_devices_api.listOrgAvailableDeviceVersions(
            self.apisession, self.org_id, type="ap"
        )  # Fetch AP firmware versions.
        if not response or not hasattr(response, "data"):  # Response missing or malformed.
            return None  # Signal fetch failure to the caller.
        if not isinstance(response.data, list):  # Non-list payload cannot be iterated as version records.
            return []  # Return an empty version list for unexpected payload types.
        return response.data  # Return the validated list payload.

    def _extract_model_version_record(
        self, version_info: Any
    ) -> tuple[str, dict[str, Any]] | None:  # Validate one version record for model mapping.
        """Validate one available-version record for model grouping."""
        if not isinstance(version_info, dict):  # Only dict records can contain model/version metadata.
            return None  # Skip malformed entries.
        model = version_info.get("model")  # Read the model identifier from the record.
        version = version_info.get("version")  # Read the version string from the record.
        if not model or not version:  # Both model and version are required for mapping.
            return None  # Skip incomplete records.
        return (str(model), version_info)  # Return the normalized model key with the original record.

    def _build_model_version_map(self) -> None:  # Group available versions by AP model.
        """Build model -> versions map from available versions."""
        self.model_version_map = {}  # Rebuild the map from scratch for each fetch.
        for version_info in self.available_versions:  # Walk each version record.
            record = self._extract_model_version_record(version_info)  # Validate and normalize the version record.
            if not record:  # Skip malformed or incomplete records.
                continue  # Continue to the next record.
            model, normalized_record = record  # Unpack the model key and original version record.
            self.model_version_map.setdefault(model, []).append(
                normalized_record
            )  # Append the record to the model's list.

    # ------------------------------------------------------------------
    # Step 4: Select versions
    # ------------------------------------------------------------------

    def _seed_current_versions_for_step4(self) -> None:  # Pre-load existing versions into the working selection map.
        """Seed step-4 custom versions from current site settings when applicable."""
        if (
            self.is_single_site and self.current_site_versions
        ):  # Single-site mode can reuse the site's existing custom versions.
            self.custom_versions = (
                self.current_site_versions.copy()
            )  # Start selection from the current site configuration to support Enter-to-keep behavior.

    def _select_family_versions(
        self, model_families: dict[str, list[str]]
    ) -> bool:  # Walk each model family and collect version selections.
        """Prompt for version selection across every model family."""
        for family, models in sorted(model_families.items()):  # Walk each AP model family in stable display order.
            if not self._select_family_version(
                family, models
            ):  # Abort immediately if the operator cancels a family prompt.
                return False  # Signal step-4 cancellation to the caller.
        return True  # All model families were processed successfully.

    def _finalize_step4_selection(self) -> bool:  # Validate that step 4 produced at least one version selection.
        """Validate and report the final result of step-4 version selection."""
        if not self.custom_versions:  # Empty custom-version map means no AP models were selected for auto-upgrade.
            print("\n  X No versions selected")  # Tell the operator they must select at least one model version.
            return False  # Abort step 4 because nothing would be configured.
        print(f"\n  + Configured {len(self.custom_versions)} model(s)")  # Confirm the number of configured AP models.
        return True  # Step 4 completed with at least one selected model.

    def _step4_select_versions(self) -> bool:  # Step 4: choose firmware versions per model.
        """Select firmware version per AP model."""
        _print_step4_header(self.is_single_site, self.current_site_versions)  # Print the step-4 header.
        self._seed_current_versions_for_step4()  # Pre-load current site versions so Enter can keep existing selections.
        model_families = _group_models_by_family(self.model_version_map)  # Group AP models into families.
        if not self._select_family_versions(
            model_families
        ):  # Prompt through each family until completion or cancellation.
            return False  # Abort step 4 when the operator cancels a family prompt.
        return self._finalize_step4_selection()  # Validate and report the final set of configured model versions.

    def _select_family_version(
        self, family: str, models: list[str]
    ) -> bool:  # Prompt for and apply one family's version choice.
        """Run version-selection flow for one AP model family."""
        sorted_versions = _get_family_versions(
            self.model_version_map, models
        )  # Collect versions available across this family.
        if not sorted_versions:  # Families without versions do not need operator input.
            return True  # Continue with the next family.
        current_version = _get_current_family_version(
            self.is_single_site, self.current_site_versions, models
        )  # Resolve the current family version.
        _display_family_versions(
            family, models, sorted_versions, current_version
        )  # Show numbered version choices to the operator.
        try:
            choice = self.safe_input_fn(
                f"  Select version (1-{len(sorted_versions)}): ", "auto_upgrade_config"
            ).strip()  # Read the operator's choice safely.
        except SystemExit:  # Operator aborted at the prompt.
            return False  # Abort step 4 entirely.
        _apply_family_selection(  # Apply the chosen selection to the shared custom_versions dict.
            choice,  # Pass the raw operator input for interpretation.
            self.custom_versions,  # Mutate the accumulated model->version map in place.
            FamilySelectionContext(
                family=family,
                models=models,
                sorted_versions=sorted_versions,
                current_version=current_version,
                model_version_map=self.model_version_map,
            ),  # Bundle per-family prompt context.
        )
        return True  # This family was handled successfully.

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


def _msp_dependencies_ready(msp: SiteAutoUpgradeMspDeps) -> bool:  # Validate MSP-only dependency injection helpers.
    """Return True when both MSP selection callables are available."""
    return bool(msp.select_msps_fn and msp.select_orgs_fn)  # Require both MSP selection helpers to proceed.


def _select_msp_orgs_and_versions(  # Select target orgs and shared versions for MSP mode.
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
) -> tuple[list[dict[str, Any]], dict[str, str] | None] | None:
    """Resolve selected organizations and optional shared versions for MSP mode."""
    selected_orgs = _msp_select_entities(msp.select_msps_fn, msp.select_orgs_fn)  # Step 1 + 2: select MSPs and orgs.
    if not selected_orgs:  # Operator cancelled or selected nothing.
        return None  # Signal cancellation to the caller.
    shared_versions = _msp_get_firmware_config(
        core.apisession, selected_orgs, core.safe_input_fn
    )  # Step 3: choose shared versions.
    if shared_versions is None:  # None means the operator aborted the firmware-selection prompt.
        return None  # Signal cancellation to the caller.
    return (
        selected_orgs,
        shared_versions if shared_versions else None,
    )  # Return resolved orgs with optional shared versions.


def _execute_msp_mode(  # Execute the MSP multi-org flow.
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
) -> None:
    """Execute MSP multi-organization auto-upgrade configuration.

    Issue #433 Phase B: signature reduced from 7 params to 2 via the
    SiteAutoUpgradeCoreDeps + SiteAutoUpgradeMspDeps dataclasses.
    """
    logging.debug("Entering _execute_msp_mode")  # Action-log entry.

    if not _msp_dependencies_ready(msp):  # MSP DI is optional at call boundary; guard here.
        print("  X MSP functions not available")  # MSP helper callables missing.
        return  # Bail out -- caller did not wire in MSP selection functions.

    selection = _select_msp_orgs_and_versions(core, msp)  # Run target-org and shared-version selection.
    if not selection:  # Operator cancelled one of the MSP selection prompts.
        return  # Cleanly exit -- nothing to apply.
    selected_orgs, shared_versions = selection  # Unpack the selected orgs and optional shared versions.

    shared_schedule = _prompt_msp_shared_schedule(
        core.safe_input_fn
    )  # Prompt once for the shared MSP upgrade schedule after org/version selection succeeds.
    if shared_schedule is None:  # Operator cancelled the shared schedule prompt.
        return  # Cleanly exit -- nothing to apply.

    _msp_confirm_and_apply(  # Step 6: confirm + apply across every org (4-param signature).
        core,
        selected_orgs,
        shared_schedule,
        shared_versions if shared_versions else None,
    )


def _prompt_msp_shared_schedule(
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:  # Prompt for the shared MSP schedule block with step banner.
    """Prompt for shared schedule settings during MSP mode."""
    print("\n" + "-" * 70)  # Visual step separator -- ASCII only per logging standards.
    print("  STEP 4: Schedule Configuration")  # Step header.
    print("-" * 70 + "\n")  # Section divider.
    shared_schedule = _get_shared_schedule(
        safe_input_fn
    )  # Step 4 + 5: collect one shared schedule for every selected organization.
    return shared_schedule  # Return the collected shared schedule or None on cancellation.


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


def _parse_index_part(part: str) -> list[int]:  # Parse one single or range index fragment.
    """Parse one comma-delimited index fragment."""
    if "-" not in part:  # Single-number fragment.
        return _parse_single_index(part)  # Parse a single index value.
    return _parse_index_range(part)  # Parse an inclusive range fragment.


def _parse_single_index(part: str) -> list[int]:  # Parse one single index token.
    """Parse one index token into a one-item list."""
    try:
        return [int(part)]  # Return the parsed index in list form for easy set updates.
    except ValueError:  # Non-numeric single index.
        return []  # Skip malformed single-index tokens.


def _parse_index_range(part: str) -> list[int]:  # Parse one start-end range token.
    """Parse one inclusive range token into a list of indices."""
    range_parts = part.split("-")  # Split the range token into start and end parts.
    if len(range_parts) != 2:  # Malformed ranges cannot be interpreted safely.
        return []  # Skip malformed range tokens.
    try:
        start = int(range_parts[0])  # Parse the range start.
        end = int(range_parts[1])  # Parse the range end.
    except ValueError:  # Non-numeric range endpoints.
        return []  # Skip malformed range tokens.
    return list(range(start, end + 1))  # Return the inclusive range as a list of indices.


def _parse_index_selection(selection: str) -> list[int]:  # Parse an index expression into a list.
    """Parse index selection string into sorted list of integers."""
    indices: set[int] = set()  # Collect distinct indices.
    parts = selection.replace(" ", "").split(",")  # Split on commas (whitespace stripped).

    for part in parts:  # Walk each comma-separated part.
        indices.update(_parse_index_part(part))  # Merge parsed indices from this selection fragment.

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


def _handle_unselected_family_choice(
    choice: str,
    ctx: FamilySelectionContext,
) -> None:  # Report keep/skip behavior when no new family version was chosen.
    """Handle Enter-to-keep and Enter-to-skip behavior for one family."""
    if not choice and ctx.current_version:  # Bare Enter in single-site mode keeps the current configured version.
        print(
            f"    + Keeping {ctx.family} models at {ctx.current_version}"
        )  # Confirm that the current family version remains unchanged.
        return  # Family outcome handled completely.
    if not choice:  # Bare Enter with no current version means skip this family entirely.
        print(f"    - Skipped {ctx.family} family")  # Tell the operator this family will not be configured.


def _resolve_family_selected_version(
    choice: str, sorted_versions: list[str]
) -> str | None:  # Resolve numeric family choice into a version string.
    """Resolve a numeric family choice into the selected version string."""
    if not choice or not choice.isdigit():  # Only numeric non-empty choices can select a version.
        return None  # Signal that no concrete version was selected.
    idx = int(choice) - 1  # Translate the 1-based display index into a 0-based list index.
    if idx < 0 or idx >= len(sorted_versions):  # Out-of-range choices are invalid.
        return None  # Signal invalid or absent version selection.
    return sorted_versions[idx]  # Return the selected version string.


def _apply_family_version_to_models(  # Apply one selected family version to each compatible model.
    selected: str,
    custom_versions: dict[str, str],
    ctx: FamilySelectionContext,
) -> None:
    """Apply a selected family version to all models that support it."""
    for model in ctx.models:  # Walk each model in the selected family.
        model_versions = _extract_version_strings(
            ctx.model_version_map.get(model, [])
        )  # Read valid versions for this model.
        if selected in model_versions:  # Only apply versions available for the current model.
            custom_versions[model] = selected  # Record the family selection for the compatible model.


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
    selected = _resolve_family_selected_version(
        choice, ctx.sorted_versions
    )  # Resolve the chosen version from the operator input.
    if selected:  # Numeric selection resolved to a real version string.
        _apply_family_version_to_models(
            selected, custom_versions, ctx
        )  # Apply the chosen version to compatible models.
        print(f"    + Set {ctx.family} models to {selected}")  # Confirm to operator with the chosen version.
        return  # Family selection handled completely.
    _handle_unselected_family_choice(
        choice, ctx
    )  # Handle Enter-to-keep and Enter-to-skip behavior when no new version was selected.


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


def _find_first_stable_version(versions: list[Any]) -> str:  # Find first stable-tagged version string.
    """Return the first stable version string from a version list."""
    for entry in versions:  # Walk version entries in API-provided order.
        if isinstance(entry, dict) and entry.get("tag") == "stable":  # Stable-tagged dict entry found.
            return str(entry.get("version", ""))  # Return its version string immediately.
    return ""  # No stable-tagged version found.


def _version_string_from_entry(entry: Any) -> str:  # Normalize one version entry to a string.
    """Normalize a version entry to a version string."""
    if isinstance(entry, dict):  # Dict-shaped version entry.
        return str(entry.get("version", ""))  # Return the dict's version field.
    return str(entry)  # Non-dict entries are already version-like values.


def _fallback_version_string(
    versions: list[Any],
) -> str:  # Return the first available version string when no stable tag exists.
    """Return the first available version string from a version list."""
    if not versions:  # No version entries exist at all.
        return ""  # Return empty string when no versions are available.
    return _version_string_from_entry(
        versions[0]
    )  # Fall back to the first available version entry from the API payload.


def _pick_stable_version(versions: list[Any]) -> str:  # Pick the most stable version available.
    """Pick the latest stable version from a list of version entries."""
    stable_version = _find_first_stable_version(versions)  # Prefer the first stable-tagged version when available.
    if stable_version:  # Stable version found.
        return stable_version  # Return the stable version immediately.
    return _fallback_version_string(versions)  # Fall back to the first available version when no stable tag exists.


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


def _normalize_time_input_markers(
    time_input: str,
) -> tuple[str, bool, bool]:  # Normalize free-form time input and detect AM/PM markers.
    """Normalize time input text and return cleaned value plus AM/PM flags."""
    time_upper = time_input.upper().strip()  # Uppercase and trim input for easier marker detection.
    is_pm = "PM" in time_upper  # Detect whether the operator explicitly entered PM.
    is_am = "AM" in time_upper  # Detect whether the operator explicitly entered AM.
    time_clean = time_upper.replace("AM", "").replace("PM", "").strip()  # Remove AM/PM markers before numeric parsing.
    return (time_clean, is_am, is_pm)  # Return cleaned text with the detected AM/PM flags.


def _time_components_in_range(hour: int, minute: int) -> bool:  # Validate parsed hour/minute values.
    """Return True when parsed hour and minute values are within 24-hour bounds."""
    return 0 <= hour <= 23 and 0 <= minute <= 59  # Require valid 24-hour clock bounds.


def _parse_time_components(
    time_input: str,
) -> tuple[int, int] | None:  # Parse and validate hour/minute components from free-form input.
    """Parse free-form time input into validated 24-hour components."""
    time_clean, is_am, is_pm = _normalize_time_input_markers(
        time_input
    )  # Normalize casing and strip any AM/PM markers before numeric parsing.
    hour, minute = _parse_hour_minute(time_clean)  # Parse the cleaned time string into hour and minute values.
    if hour < 0:  # Negative hour signals parsing failure from the lower-level helper.
        return None  # Signal invalid time input to the caller.
    hour = _apply_ampm(hour, is_am, is_pm)  # Apply AM/PM conversion after basic numeric parsing succeeds.
    if not _time_components_in_range(hour, minute):  # Reject out-of-range hour/minute values after AM/PM conversion.
        return None  # Signal invalid time input to the caller.
    return (hour, minute)  # Return the validated 24-hour time components.


def parse_time_input(time_input: str) -> str:  # Parse a free-form time string to HH:MM.
    """Parse various time formats to HH:MM for the API.

    Accepts: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM, etc.
    Returns: HH:MM format string, or 'any' for any time.
    """
    if not time_input:  # Empty input.
        return "any"  # Return 'any'.
    parsed_time = _parse_time_components(time_input)  # Parse the operator input into validated 24-hour time components.
    if parsed_time is None:  # Invalid or unparseable time input falls back to Mist's any-time token.
        return "any"  # Return 'any' for invalid free-form time input.
    hour, minute = parsed_time  # Unpack validated 24-hour hour/minute components for formatting.
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


def _extract_site_identity(
    site: dict[str, Any],
) -> tuple[str | None, str]:  # Pull common site identity fields from a site record.
    """Extract a site's ID and display name from a site record."""
    site_id = site.get("id")  # Read the site id field.
    site_name = site.get("name", "Unknown")  # Read the site display name with fallback.
    return (site_id, site_name)  # Return the extracted site identity tuple.


def _apply_settings_to_site(  # Apply or simulate one site-settings update.
    site_id: str,
    site_name: str,
    settings: dict[str, Any],
    apisession: Any,
    dry_run: bool,
) -> bool:
    """Apply or simulate one site-settings update and return success status."""
    try:
        if dry_run:  # Dry-run path only reports the planned site update.
            print(f"    [DRY-RUN] {site_name}")  # Report the would-apply action.
            return True  # Treat dry-run reporting as success.
        import mistapi.api.v1.sites.setting as sites_setting_api  # Import the settings API lazily.

        sites_setting_api.updateSiteSettings(apisession, site_id, body=settings)  # Push the updated settings to Mist.
        print(f"    [OK] {site_name}")  # Report per-site success.
        return True  # Report successful apply.
    except Exception as exc:  # Apply failed for this site.
        print(f"    [FAIL] {site_name}: {exc}")  # Report the failure to the operator.
        logging.error("Failed to configure auto-upgrade for site %s: %s", site_name, exc)  # Log the per-site failure.
        return False  # Report failed apply.


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
        site_id, site_name = _extract_site_identity(site)  # Read the site's id and display name.
        if not site_id:  # Missing site id.
            failed += 1  # Count as a failure.
            continue  # Skip this site.
        if _apply_settings_to_site(
            site_id, site_name, settings, apisession, dry_run
        ):  # Apply or simulate config for this site.
            successful += 1  # Count the success.
            continue  # Continue to the next site after a successful apply.
        failed += 1  # Count failed apply attempts.
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


def _build_msp_summary_label(dry_run: bool) -> str:  # Build dry-run-aware MSP summary title.
    """Build summary title for MSP output."""
    label = "MSP MULTI-ORG AUTO-UPGRADE SUMMARY"  # Base summary title used for real applies.
    if dry_run:  # Dry-run summaries need explicit operator labeling.
        label += " (DRY-RUN)"  # Append dry-run annotation to the title.
    return label  # Return the final display label.


def _print_msp_totals(  # Print dry-run-aware MSP totals.
    total_orgs: int,
    successful_orgs: int,
    total_sites: int,
    dry_run: bool,
) -> None:
    """Print total organizations and sites for MSP summary output."""
    print(f"  Organizations processed: {total_orgs}")  # Show how many organizations were evaluated.
    if dry_run:  # Dry-run wording differs from real-apply wording.
        print(f"  Would configure: {successful_orgs} org(s)")  # Show would-configure organization count.
        print(f"  Total sites WOULD be configured: {total_sites}")  # Show would-configure site count.
        return  # Dry-run totals block is complete.
    print(f"  Successful: {successful_orgs}")  # Show successful organization count for real applies.
    print(f"  Total sites configured: {total_sites}")  # Show configured site count for real applies.


def _print_msp_summary(  # Print the MSP multi-org summary.
    results: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Print summary of MSP multi-org auto-upgrade configuration."""
    print("\n" + "=" * 70)  # Divider.
    print(f"  {_build_msp_summary_label(dry_run)}")  # Print dry-run-aware summary title.
    print("=" * 70 + "\n")  # Divider.

    if dry_run:  # Dry-run path.
        print("  >> DRY-RUN MODE: No actual changes were made <<\n")  # Warn no changes made.

    total_orgs, successful_orgs, total_sites = _compute_msp_totals(results)  # Compute the roll-up totals.
    _print_msp_totals(total_orgs, successful_orgs, total_sites, dry_run)  # Print dry-run-aware totals block.
    print("")  # Spacer.

    if successful_orgs < total_orgs:  # Some orgs failed.
        _print_msp_failed_orgs(results)  # List the failed orgs.

    if dry_run:  # Dry-run path.
        print("  >> To apply changes, run without --dry-run flag")  # Tell the operator how to apply.
    else:
        print("  Configuration complete.")  # Report completion.


def _prompt_shared_day_of_week(safe_input_fn: SafeInputFn) -> str | None:  # Prompt for shared MSP schedule day.
    """Prompt for shared day-of-week input and normalize it."""
    try:
        day_input = (
            safe_input_fn("  Day of week [any]: ", "msp_schedule").strip().lower() or "any"
        )  # Read operator day input with default.
    except SystemExit:  # Operator aborted the schedule prompt.
        return None  # Signal cancellation to the caller.
    return _normalize_shared_day_of_week(day_input)  # Normalize operator input into Mist day tokens.


def _normalize_shared_day_of_week(day_input: str) -> str:  # Normalize shared day input into Mist API token.
    """Normalize shared day-of-week input to a Mist-supported value."""
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
    return day_map.get(day_input, "any")  # Default unexpected values to Mist's "any" token.


def _prompt_shared_time_of_day(safe_input_fn: SafeInputFn) -> str | None:  # Prompt for shared MSP schedule time.
    """Prompt for shared time-of-day input and normalize it."""
    try:
        time_input = (
            safe_input_fn("  Time of day [02:00]: ", "msp_schedule").strip() or "02:00"
        )  # Read operator time input with default.
    except SystemExit:  # Operator aborted the schedule prompt.
        return None  # Signal cancellation to the caller.
    if time_input.lower() == "any":  # Mist accepts explicit "any" time token.
        return "any"  # Normalize any-time input.
    return time_input  # Return literal HH:MM input unchanged.


def _get_shared_schedule(  # Prompt for the shared MSP schedule.
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Get shared schedule settings for MSP mode."""
    print("  Schedule Configuration:")  # Schedule header.
    print("    When should auto-upgrades occur?\n")  # Explain the prompt.
    print("    Day of week:")  # Day-of-week header.
    print("      [1] any - Any day")  # Any-day option.
    print("      [2] mon, tue, wed, thu, fri, sat, sun\n")  # Weekday options.

    day_of_week = _prompt_shared_day_of_week(safe_input_fn)  # Prompt for the shared day-of-week value.
    if day_of_week is None:  # Operator aborted the day prompt.
        return None  # Abort with no schedule.
    print(f"    + Day: {day_of_week}\n")  # Confirm the chosen day.
    print("    Time of day (HH:MM in site's local timezone, or 'any'):")  # Time prompt explanation.

    time_of_day = _prompt_shared_time_of_day(safe_input_fn)  # Prompt for the shared time-of-day value.
    if time_of_day is None:  # Operator aborted the time prompt.
        return None  # Abort with no schedule.
    print(f"    + Time: {time_of_day}")  # Confirm the chosen time.

    return {"day_of_week": day_of_week, "time_of_day": time_of_day}  # Return the shared schedule.


def _get_reference_org_context(  # Validate reference org and normalize org display fields.
    reference_org: dict[str, Any],
    apisession: Any,
) -> tuple[str, str] | None:
    """Validate reference-org context for shared firmware selection."""
    org_id = reference_org.get("id")  # Read the reference org id from the selected org dict.
    if not org_id or apisession is None:  # Shared firmware selection requires both org id and API session.
        return None  # Signal missing context to the caller.
    org_name = reference_org.get("name", "Unknown")  # Read the reference org display name with fallback.
    return (str(org_id), org_name)  # Return normalized org id and name.


def _fetch_reference_org_versions(
    apisession: Any, org_id: str
) -> list[Any] | None:  # Fetch available AP versions for one reference org.
    """Fetch available AP firmware versions for a reference organization."""
    import mistapi.api.v1.orgs.devices as org_devices_api  # Import the org-devices API lazily.

    response = org_devices_api.listOrgAvailableDeviceVersions(
        apisession, org_id, type="ap"
    )  # Fetch AP firmware versions for the reference org.
    if not response or not hasattr(response, "data"):  # Response missing or malformed.
        return None  # Signal unusable response payload.
    if not isinstance(response.data, list):  # Non-list payload cannot be processed as version records.
        return []  # Treat unexpected payload types as an empty version set.
    return response.data  # Return the validated list payload.


def _load_reference_org_versions(
    apisession: Any, org_id_str: str
) -> list[Any] | None:  # Fetch reference-org firmware versions while handling user-visible errors.
    """Fetch reference-org firmware versions and handle fetch failures consistently."""
    try:
        available_versions = _fetch_reference_org_versions(
            apisession, org_id_str
        )  # Fetch available AP firmware versions for the chosen reference organization.
    except Exception as error:  # Network, SDK, or API exceptions are non-fatal to the overall workflow.
        print(f"  X Error fetching firmware versions: {error}")  # Tell the operator the fetch failed unexpectedly.
        return None  # Signal that the reference-org version fetch failed.
    if available_versions is None:  # None means the helper could not produce a usable response payload.
        print(
            "  X Failed to fetch available firmware versions"
        )  # Tell the operator the reference-org payload was unusable.
        return None  # Signal failure to the caller.
    return available_versions  # Return the validated reference-org version list for further processing.


def _prepare_shared_firmware_selection(
    available_versions: list[Any],
) -> (
    tuple[dict[str, list[str]], dict[str, list[dict[str, Any]]]] | None
):  # Build family-selection data from raw reference-org versions.
    """Build model-family structures for shared MSP firmware selection."""
    model_version_map = _build_version_map_from_list(
        available_versions
    )  # Build the per-model version map from the raw API payload.
    if not model_version_map:  # Empty map means no AP firmware versions were discoverable for the reference org.
        print("  X No AP firmware versions found")  # Tell the operator there is nothing to select from.
        return None  # Signal that interactive selection cannot proceed.
    print(
        f"  + Found firmware for {len(model_version_map)} AP model(s)"
    )  # Confirm the number of AP models with available firmware.
    model_families = _group_models_for_msp(
        model_version_map
    )  # Group the model-version map into AP model families for selection UX.
    return (model_families, model_version_map)  # Return the family map and raw model-version map together.


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
    org_context = _get_reference_org_context(reference_org, apisession)  # Validate the reference org and API session.
    if not org_context:  # Missing organization context or API session.
        print("  X Missing organization ID or API session")  # Tell the operator.
        return {}  # Return empty versions.
    org_id_str, org_name = org_context  # Unpack normalized org id and display name.
    print(f"\n  Fetching available firmware versions from: {org_name}")  # Announce the fetch source.
    available_versions = _load_reference_org_versions(
        apisession, org_id_str
    )  # Fetch the reference organization's firmware catalog with user-visible error handling.
    if available_versions is None:  # Reference-org fetch failed or returned no usable payload.
        return {}  # Return empty versions so MSP mode can fall back to auto-detect behavior.
    selection_data = _prepare_shared_firmware_selection(
        available_versions
    )  # Build family-selection structures from the fetched version catalog.
    if selection_data is None:  # No usable AP firmware versions existed in the reference org.
        return {}  # Return empty versions so MSP mode can fall back to auto-detect behavior.
    model_families, model_version_map = selection_data  # Unpack the prepared family-selection structures.
    return _select_versions_interactively(  # Select shared versions interactively.
        model_families,
        model_version_map,
        safe_input_fn,
    )


def _extract_version_map_entry(
    entry: Any,
) -> tuple[str, dict[str, Any]] | None:  # Normalize one API version record for MSP mapping.
    """Normalize one API version record for model->versions mapping."""
    if not isinstance(entry, dict):  # Only dict records contain model/version fields.
        return None  # Skip malformed version entries.
    model = entry.get("model")  # Read the model identifier.
    version = entry.get("version")  # Read the firmware version string.
    if not model or not version:  # Both fields are required for mapping.
        return None  # Skip incomplete version entries.
    tag = entry.get("tag", "")  # Read the release tag with empty-string fallback.
    return (str(model), {"version": version, "tag": tag})  # Return normalized model key with version payload.


def _build_version_map_from_list(  # Build a model->versions map from a list.
    available_versions: list[Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build model -> versions map from API response."""
    result: dict[str, list[dict[str, Any]]] = {}  # Result map.
    for entry in available_versions:  # Walk each version record.
        mapped_entry = _extract_version_map_entry(entry)  # Validate and normalize one version record.
        if not mapped_entry:  # Skip malformed or incomplete records.
            continue  # Continue to the next version record.
        model, version_record = mapped_entry  # Unpack the normalized model key and version payload.
        result.setdefault(model, []).append(version_record)  # Append the normalized version record for this model.
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


def _prompt_msp_family_choice(
    safe_input_fn: SafeInputFn, option_count: int
) -> str | None:  # Prompt once for one MSP family selection.
    """Prompt for one MSP family version choice."""
    try:
        return safe_input_fn(
            f"  Select version (1-{option_count}): ", "msp_firmware_select"
        ).strip()  # Read one family selection safely.
    except SystemExit:  # Operator aborted the prompt.
        return None  # Signal cancellation to the caller.


def _apply_msp_family_choice(  # Apply or skip one MSP family choice.
    choice: str,
    family: str,
    models: list[str],
    sorted_versions: list[tuple[str, str]],
    model_version_map: dict[str, list[dict[str, Any]]],
    custom_versions: dict[str, str],
) -> None:
    """Apply one MSP family selection or print the corresponding skip message."""
    selected_version = _resolve_msp_selected_version(
        choice, sorted_versions
    )  # Resolve numeric choice into a version string.
    if selected_version:  # Valid numeric selection resolved successfully.
        _apply_version_to_models(
            selected_version, family, models, model_version_map, custom_versions
        )  # Apply the chosen version to compatible models.
        return  # Family selection handled completely.
    if choice:  # Non-empty invalid input means explicit invalid selection.
        print(f"    - Invalid selection, skipped {family}")  # Report invalid selection and skip this family.
        return  # Family selection handled completely.
    print(f"    - Skipped {family} family")  # Empty input skips this family silently.


def _resolve_msp_selected_version(  # Resolve numeric MSP family choice into a version string.
    choice: str,
    sorted_versions: list[tuple[str, str]],
) -> str | None:
    """Resolve a numeric MSP family choice into a version string."""
    if not choice or not choice.isdigit():  # Only numeric non-empty choices can select a version.
        return None  # Signal absent or invalid selection.
    idx = int(choice) - 1  # Convert from 1-based display index to 0-based list index.
    if idx < 0 or idx >= len(sorted_versions):  # Guard against out-of-range selections.
        return None  # Signal invalid selection.
    return sorted_versions[idx][0]  # Return the selected version string from the tuple payload.


def _select_one_family_version(
    family: str,
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
    safe_input_fn: SafeInputFn,
    custom_versions: dict[str, str],
) -> bool | None:  # Prompt for one MSP family and apply the result.
    """Prompt for one MSP family selection and return False on cancellation."""
    sorted_versions = _collect_family_versions(
        models, model_version_map
    )  # Collect the family's distinct firmware versions in newest-first order.
    if not sorted_versions:  # Families without versions do not need operator input.
        return True  # Continue with the next family.
    _display_msp_family_versions(family, models, sorted_versions)  # Show numbered firmware choices for this family.
    choice = _prompt_msp_family_choice(
        safe_input_fn, len(sorted_versions)
    )  # Read the operator's selection for this family safely.
    if choice is None or choice.lower() == "q":  # EOF or explicit q both cancel the entire shared-selection flow.
        return None  # Signal full interactive-selection cancellation.
    _apply_msp_family_choice(
        choice, family, models, sorted_versions, model_version_map, custom_versions
    )  # Apply, skip, or reject the family's chosen version.
    return True  # This family was processed successfully.


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
        selection_result = _select_one_family_version(
            family, models, model_version_map, safe_input_fn, custom_versions
        )  # Prompt for this family and apply the operator's chosen outcome.
        if selection_result is None:  # Operator cancelled the interactive shared-version workflow.
            return None  # Abort selection for the entire MSP shared-version flow.
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
