"""Site auto-upgrade configuration for Mist AP firmware.

Configures auto-upgrade settings at the site level to schedule AP firmware
upgrades during maintenance windows. Supports single-org and MSP multi-org
workflows with dry-run capability.

Extracted from MistHelper.py for maintainability.
"""

from __future__ import annotations  # WHY: PEP 604 union syntax and forward refs.

import logging  # WHY: structured action-log info/debug lines per project standards.
from dataclasses import dataclass  # WHY: frozen slots kw_only config record.
from typing import Any  # WHY: duck-typed DI callables and mistapi session.

from src.dataclasses.family_selection_context import (  # WHY: 5-field bundle for family selection.
    FamilySelectionContext,
)
from src.dataclasses.site_auto_upgrade_deps import (  # WHY: bundles DI params (5-Item Rule).
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


@dataclass(frozen=True, slots=True, kw_only=True)
class SiteAutoUpgradeConfig:
    """Immutable configuration record for SiteAutoUpgradeConfigurator.

    Frozen slots kw_only dataclass mirroring the pattern used by
    org_ap_upgrader (spec 1006). Wraps the 6 always-needed inputs so that
    the configurator constructor accepts a single object instead of
    positional params, satisfying the 5-Item Rule.
    """

    org_id: str  # WHY: Mist organization UUID used for every API call.
    apisession: Any  # WHY: authenticated mistapi session (may be None. Helpers degrade).
    safe_input_fn: SafeInputFn  # WHY: EOF-safe interactive input helper.
    fetch_sites_fn: FetchSitesFn  # WHY: returns the org's sites.
    check_stop_fn: CheckStopFn  # WHY: cooperative stop-signal predicate.
    dry_run: bool = False  # WHY: when True, suppress API mutations. Print-only mode.

    def __post_init__(self) -> None:
        """Permissive validation - only reject clearly-wrong types.

        Raises:
            TypeError: If org_id is not a string, or dry_run is not a boolean
        """
        if not isinstance(self.org_id, str):  # WHY: catch obvious misuse. An assert vanishes under -O.
            raise TypeError("org_id must be str")  # WHY: name the field and the expected type.
        if not isinstance(self.dry_run, bool):  # WHY: catch obvious misuse. An assert vanishes under -O.
            raise TypeError("dry_run must be bool")  # WHY: name the field and the expected type.


@dataclass(frozen=True, slots=True, kw_only=True)
class _MspOrgApplyContext:
    """Bundle of per-org apply-loop context (5-Item Rule)."""

    core: SiteAutoUpgradeCoreDeps  # WHY: DI bundle passed to per-org configurator.
    idx: int  # WHY: 1-based index of the org within the selected list.
    total: int  # WHY: total count of orgs for progress header.
    shared_schedule: dict[str, Any]  # WHY: MSP-shared upgrade schedule.
    shared_versions: dict[str, str] | None  # WHY: MSP-shared firmware map (or None to prompt per-org).


@dataclass(frozen=True, slots=True, kw_only=True)
class _MspFamilyChoiceContext:
    """Bundle for one MSP family-version choice dispatch (5-Item Rule)."""

    family: str  # WHY: family name for print messages.
    models: list[str]  # WHY: concrete model SKUs in this family.
    sorted_versions: list[tuple[str, str]]  # WHY: (version, tag) options shown to operator.
    model_version_map: dict[str, list[dict[str, Any]]]  # WHY: per-model raw API entries for validation.


def _resolve_configurator_kwargs(cfg: dict[str, Any]) -> SiteAutoUpgradeConfig:
    """Resolve constructor kwargs into a SiteAutoUpgradeConfig.

    Accepts either config=SiteAutoUpgradeConfig(...) OR legacy
    org_id=..., deps=SiteAutoUpgradeCoreDeps(...). Raises TypeError on
    any other invocation form.
    """
    if "config" in cfg:  # WHY: new form - config already resolved.
        resolved = cfg["config"]  # WHY: extract the pre-built record.
        assert isinstance(resolved, SiteAutoUpgradeConfig)  # nosec B101 - The "config" branch proved the shape.
        return resolved  # WHY: pass through unchanged.
    if "org_id" in cfg and "deps" in cfg:  # WHY: legacy form - build from deps bundle.
        deps = cfg["deps"]  # WHY: unpack the deps bundle.
        return SiteAutoUpgradeConfig(  # WHY: convert legacy form to canonical config.
            org_id=cfg["org_id"],
            apisession=deps.apisession,
            safe_input_fn=deps.safe_input_fn,
            fetch_sites_fn=deps.fetch_sites_fn,
            check_stop_fn=deps.check_stop_fn,
            dry_run=deps.dry_run,
        )
    raise TypeError(  # WHY: neither invocation form matched - reject.
        "SiteAutoUpgradeConfigurator requires either " "config=SiteAutoUpgradeConfig(...) or org_id=..., deps=..."
    )


class SiteAutoUpgradeConfigurator:
    """Configure AP auto-upgrade settings at site level.

    Sets auto_upgrade configuration in site settings so that:
    - New APs automatically upgrade to the specified firmware
    - Existing APs upgrade during scheduled maintenance windows

    NETWORK IMPACT WARNING:
    - While auto-upgrade itself does not initiate immediate upgrades,
      scheduled upgrades WILL cause AP reboots during maintenance windows
    """

    def __init__(self, **cfg: Any) -> None:
        """Initialize the configurator.

        Accepts either ``config=SiteAutoUpgradeConfig(...)`` (new form) or
        legacy ``org_id=..., deps=SiteAutoUpgradeCoreDeps(...)`` for
        byte-identical MistHelper.py + test-file compatibility.
        """
        resolved = _resolve_configurator_kwargs(cfg)  # WHY: normalize both invocation forms.
        self._apply_config_to_attributes(resolved)  # WHY: hydrate 6 DI-derived attrs.
        self._reset_workflow_state()  # WHY: seed 11 workflow-scoped attrs to defaults.
        logging.debug(  # WHY: action-log post-init state.
            "SiteAutoUpgradeConfigurator initialized: org_id=%s, dry_run=%s",
            resolved.org_id,
            resolved.dry_run,
        )

    def _apply_config_to_attributes(self, cfg: SiteAutoUpgradeConfig) -> None:
        """Copy the 6 DI-derived config fields onto self."""
        self.org_id = cfg.org_id  # WHY: org id for every API call this configurator makes.
        self.apisession = cfg.apisession  # WHY: authenticated mistapi session.
        self.safe_input_fn = cfg.safe_input_fn  # WHY: prompt helper with EOF safety.
        self.fetch_sites_fn = cfg.fetch_sites_fn  # WHY: callable returning all sites for an org.
        self.check_stop_fn = cfg.check_stop_fn  # WHY: predicate that signals operator stop.
        self.dry_run = cfg.dry_run  # WHY: True suppresses API mutations. Print-only.

    def _reset_workflow_state(self) -> None:
        """Seed the 11 workflow-scoped attributes to empty defaults."""
        self.all_sites: list[dict[str, Any]] = []  # WHY: all sites in the org.
        self.selected_sites: list[dict[str, Any]] = []  # WHY: sites operator chose to configure.
        self.available_versions: list[Any] = []  # WHY: firmware versions available for the org.
        self.model_version_map: dict[str, list[Any]] = {}  # WHY: per-model list of versions.
        self.custom_versions: dict[str, str] = {}  # WHY: operator-chosen version per model.
        self.schedule: dict[str, Any] = {}  # WHY: maintenance-window schedule settings.
        self.current_site_versions: dict[str, str] = {}  # WHY: currently-configured versions.
        self.is_single_site = False  # WHY: True when configuring exactly one site.
        self.msp_all_sites_mode = False  # WHY: True in MSP all-sites bulk mode.
        self.org_name = ""  # WHY: human-readable org name for logs/prompts.
        self.shared_versions: dict[str, str] | None = None  # WHY: MSP-shared versions.

    # ------------------------------------------------------------------
    # Static entry point
    # ------------------------------------------------------------------

    @staticmethod
    def execute(**cfg: Any) -> None:
        """Entry point for menu system - checks MSP privileges."""
        logging.info("Starting Site Auto-Upgrade Configuration workflow")  # WHY: action-log workflow start.
        if cfg.get("dry_run"):  # WHY: advertise dry-run so operator is not surprised.
            logging.info("DRY-RUN MODE enabled - no API calls will be made")  # WHY: dry-run advert log.
        core_deps = SiteAutoUpgradeCoreDeps(  # WHY: bundle 5 always-needed DI params.
            apisession=cfg["apisession"],
            safe_input_fn=cfg["safe_input_fn"],
            fetch_sites_fn=cfg["fetch_sites_fn"],
            check_stop_fn=cfg["check_stop_fn"],
            dry_run=cfg.get("dry_run", False),
        )
        msp_deps = SiteAutoUpgradeMspDeps(  # WHY: bundle 2 MSP-only extras.
            select_msps_fn=cfg.get("select_msps_fn"),
            select_orgs_fn=cfg.get("select_orgs_fn"),
        )
        SiteAutoUpgradeConfigurator._dispatch_mode(  # WHY: delegate MSP-vs-single-org decision to helper.
            core_deps, msp_deps, cfg.get("msp_privileges") or [], cfg["get_org_id_fn"]
        )
        logging.debug("Exiting SiteAutoUpgradeConfigurator.execute()")  # WHY: trace exit for observability.

    @staticmethod
    def _dispatch_mode(
        core_deps: SiteAutoUpgradeCoreDeps,
        msp_deps: SiteAutoUpgradeMspDeps,
        msp_privileges: list[Any],
        get_org_id_fn: GetOrgIdFn,
    ) -> None:
        """Route to MSP multi-org flow or single-org flow based on privileges."""
        if msp_privileges and len(msp_privileges) > 0:  # WHY: MSP-licensed account gets multi-org workflow.
            _handle_msp_mode(core_deps, msp_deps, get_org_id_fn)  # WHY: run MSP-mode dispatcher.
            return  # WHY: MSP path handles the whole workflow.
        _run_single_org(core_deps, get_org_id_fn)  # WHY: non-MSP account uses single-org workflow.

    # ------------------------------------------------------------------
    # MSP mode helpers
    # ------------------------------------------------------------------

    def run_msp_mode(self) -> tuple[bool, int]:  # WHY: run the MSP bulk all-sites configuration flow.
        """Execute configuration workflow for MSP mode (all sites)."""
        logging.debug("Entering run_msp_mode() for org: %s", self.org_name)  # WHY: trace entry.
        if not self._step1_fetch_sites():  # WHY: sites are required for every downstream step.
            return (False, 0)  # WHY: abort with zero configured on fetch failure.
        self.selected_sites = self.all_sites.copy()  # WHY: MSP mode auto-selects every site.
        print(f"  + Auto-selected ALL {len(self.selected_sites)} site(s)")  # WHY: confirm auto-selection.
        if not self._msp_ensure_versions():  # WHY: either use pre-shared versions or fetch+auto-pick.
            return (False, 0)  # WHY: abort if versions cannot be resolved.
        success, count = self._apply_auto_upgrade_config()  # WHY: apply the auto-upgrade config to all sites.
        logging.info(  # WHY: action-log the outcome for later audit.
            "MSP mode complete for %s: success=%s, sites=%s", self.org_name, success, count
        )
        return (success, count)  # WHY: propagate success flag and configured-site count.

    def _msp_ensure_versions(self) -> bool:
        """Ensure custom_versions is populated for the MSP run."""
        if self.shared_versions:  # WHY: versions pre-chosen at the MSP level - reuse them.
            self.custom_versions = self.shared_versions.copy()  # WHY: copy shared map into per-org state.
            print(  # WHY: show operator we skipped the per-org selection.
                f"\n  Using pre-selected firmware versions ({len(self.custom_versions)} models):"
            )
            for model, version in sorted(self.custom_versions.items()):  # WHY: list each pair for audit.
                print(f"    {model}: {version}")  # WHY: print model/version pair.
            return True  # WHY: version state ready.
        if not self._step3_fetch_available_versions():  # WHY: fetch available versions for this org.
            return False  # WHY: abort if fetch failed.
        return self._auto_select_versions()  # WHY: auto-pick a version per model.

    def _auto_select_versions(self) -> bool:  # WHY: auto-pick the most stable version per model.
        """Auto-select firmware versions (latest stable for each model)."""
        logging.debug("Entering _auto_select_versions()")  # WHY: trace entry.
        if not self.model_version_map:  # WHY: no model->version data means we cannot select anything.
            print("  X No firmware versions available")  # WHY: tell operator nothing can be selected.
            return False  # WHY: abort auto-selection.
        print("\n  Auto-selecting firmware versions:")  # WHY: header for the selection list.
        for model, versions in self.model_version_map.items():  # WHY: walk each model's version list.
            if not versions:  # WHY: skip models with no versions.
                continue  # WHY: continue to next model.
            selected = _pick_stable_version(versions)  # WHY: choose the stable release for this model.
            self.custom_versions[model] = selected  # WHY: record the chosen version.
            print(f"    {model}: {self.custom_versions[model]}")  # WHY: show selected version.
        logging.info(  # WHY: action-log the auto-selection outcome.
            "Auto-selected versions for %s model(s)", len(self.custom_versions)
        )
        return bool(self.custom_versions)  # WHY: succeed only if at least one version was chosen.

    def _apply_auto_upgrade_config(self) -> tuple[bool, int]:
        """Apply auto-upgrade configuration to all selected sites."""
        logging.debug("Entering _apply_auto_upgrade_config()")  # WHY: trace entry.
        if not self.selected_sites:  # WHY: no sites means nothing to configure.
            return (False, 0)  # WHY: abort with zero configured.
        settings = self._build_auto_upgrade_settings()  # WHY: build the auto-upgrade payload.
        label = "DRY-RUN: Would apply" if self.dry_run else "Applying"  # WHY: label reflects dry-run vs real apply.
        print(  # WHY: announce the apply step to the operator.
            f"\n  {label} auto-upgrade to {len(self.selected_sites)} site(s)..."
        )
        success_count, fail_count = _apply_settings_to_sites(  # WHY: push settings to every site.
            sites=self.selected_sites,
            settings={"auto_upgrade": settings},
            apisession=self.apisession,
            check_stop_fn=self.check_stop_fn,
            dry_run=self.dry_run,
        )
        self._report_apply_outcome(success_count, fail_count)  # WHY: print operator-visible summary.
        return (fail_count == 0, success_count)  # WHY: success only when nothing failed.

    def _build_auto_upgrade_settings(self) -> dict[str, Any]:
        """Assemble the auto_upgrade payload for the site settings API."""
        return {  # WHY: return a fresh dict. Mist API expects these keys verbatim.
            "enabled": True,  # WHY: enable auto-upgrade at the site.
            "version": "custom",  # WHY: 'custom' selects per-model version overrides.
            "day_of_week": self.schedule.get("day_of_week", "any"),  # WHY: default 'any' means daily.
            "time_of_day": self.schedule.get("time_of_day", "02:00"),  # WHY: default 02:00 low-traffic window.
            "custom_versions": self.custom_versions,  # WHY: operator-chosen version per model.
        }

    def _report_apply_outcome(self, success_count: int, fail_count: int) -> None:
        """Print operator-visible summary of the apply outcome."""
        if self.dry_run:  # WHY: dry-run reports what it would do.
            print(f"  + Would configure: {success_count} site(s)")  # WHY: show would-configure count.
        else:  # WHY: real run reports actual counts.
            print(f"  + Configured: {success_count} site(s)")  # WHY: show configured count.
        if fail_count > 0:  # WHY: only report failures when non-zero.
            print(f"  X Failed: {fail_count} site(s)")  # WHY: show failure count.

    # ------------------------------------------------------------------
    # Interactive workflow (single-org mode)
    # ------------------------------------------------------------------

    def run(self) -> None:  # WHY: run the interactive single-org configuration flow.
        """Execute the interactive configuration workflow."""
        logging.debug("Entering run() for org_id=%s", self.org_id)  # WHY: trace entry.
        _print_intro_header(self.dry_run)  # WHY: print the intro/warning header.
        if not self._step1_fetch_sites():  # WHY: sites are required for every downstream step.
            return  # WHY: abort if no sites could be fetched.
        if not self._step2_select_sites():  # WHY: abort if operator did not select any sites.
            return  # WHY: abort the flow if selection failed.
        if not self._step3_fetch_available_versions():  # WHY: version data required for step 4.
            return  # WHY: abort if version fetch failed.
        if not self._step4_select_versions():  # WHY: abort if operator selected no versions.
            return  # WHY: abort if version selection failed.
        self._step5_configure_schedule()  # WHY: configure the maintenance-window schedule.
        self._step6_confirm_and_apply()  # WHY: final confirmation + apply.

    # ------------------------------------------------------------------
    # Step 1: Fetch sites
    # ------------------------------------------------------------------

    def _step1_fetch_sites(self) -> bool:  # WHY: step 1 loads the org's sites.
        """Fetch all sites in the organization."""
        print("-" * 70)  # WHY: visual section divider.
        print("  STEP 1: Loading Sites")  # WHY: step header.
        print("-" * 70)  # WHY: visual section divider.
        try:
            self.all_sites = self.fetch_sites_fn(self.org_id)  # WHY: fetch sites via injected callable.
            if not self.all_sites:  # WHY: no sites returned means nothing to configure.
                print("  X No sites found in organization")  # WHY: tell operator.
                return False  # WHY: abort step 1.
            self.all_sites.sort(key=lambda s: s.get("name", "").lower())  # WHY: stable alpha ordering.
            print(f"  + Found {len(self.all_sites)} site(s)")  # WHY: confirm the site count.
            return True  # WHY: step 1 succeeded.
        except Exception as exc:  # WHY: fetch may raise any mistapi error - treat as failure.
            print(f"  X Error fetching sites: {exc}")  # WHY: tell operator the error.
            logging.error(  # WHY: action-log the fetch failure.
                "SiteAutoUpgradeConfigurator: Failed to fetch sites: %s", exc
            )
            return False  # WHY: abort step 1.

    # ------------------------------------------------------------------
    # Step 2: Select sites
    # ------------------------------------------------------------------

    def _step2_select_sites(self) -> bool:  # WHY: step 2 asks operator which sites to configure.
        """Allow user to select sites with flexible options."""
        print("\n" + "-" * 70)  # WHY: visual section divider.
        print("  STEP 2: Site Selection")  # WHY: step header.
        print("-" * 70)  # WHY: visual section divider.
        print("\n  Selection Options:")  # WHY: options header.
        print("    [A] All sites in organization")  # WHY: all-sites option.
        print("    [S] Single site (interactive selection)")  # WHY: single-site option.
        print("    [L] List view - select by index numbers\n")  # WHY: list-select option.
        try:
            choice = (
                self.safe_input_fn(  # WHY: read choice via EOF-safe prompt helper.
                    "  Selection mode (A/S/L): ", "auto_upgrade_config"
                )
                .strip()
                .upper()
            )
        except SystemExit:  # WHY: safe_input raises SystemExit on EOF - bail cleanly.
            return False  # WHY: abort step 2.
        if choice == "S":  # WHY: single-site mode.
            return self._select_single_site()  # WHY: delegate to single-site selector.
        if choice == "L":  # WHY: list mode.
            return self._select_from_list()  # WHY: delegate to list selector.
        return self._select_all_sites()  # WHY: default to selecting all sites.

    def _select_all_sites(self) -> bool:  # WHY: select every site in the org.
        """Select all sites."""
        self.selected_sites = self.all_sites.copy()  # WHY: copy all sites as the selection.
        print(f"  + Selected ALL {len(self.selected_sites)} site(s)")  # WHY: confirm count.
        return True  # WHY: selection succeeded.

    def _select_single_site(self) -> bool:  # WHY: pick one site interactively.
        """Interactive single site selection."""
        _display_site_list(self.all_sites)  # WHY: show the site list.
        idx = self._prompt_single_site_index()  # WHY: read the operator's chosen index.
        if idx is None:  # WHY: operator quit or gave invalid input.
            return False  # WHY: abort selection.
        return self._apply_single_site_choice(idx)  # WHY: apply the chosen index.

    def _read_single_site_input(self) -> str | None:
        """Read the raw operator input for a single-site selection."""
        try:
            raw = self.safe_input_fn(  # WHY: read the site number via EOF-safe prompt.
                "  Enter site number (or 'q' to cancel): ", "auto_upgrade_config"
            )
            return str(raw).strip().lower()  # WHY: coerce injected callable's Any return to str.
        except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
            return None  # WHY: abort selection.

    def _prompt_single_site_index(self) -> int | None:
        """Prompt operator for a single-site index. Return 0-based idx or None."""
        selection = self._read_single_site_input()  # WHY: fetch raw input via EOF-safe helper.
        if selection is None or selection == "q":  # WHY: EOF or explicit quit.
            return None  # WHY: abort selection silently.
        if not selection.isdigit():  # WHY: non-digits are invalid.
            print("  Invalid input")  # WHY: tell operator.
            return None  # WHY: abort selection.
        idx = int(selection) - 1  # WHY: display is 1-based. Convert to 0-based index.
        if not 0 <= idx < len(self.all_sites):  # WHY: guard against out-of-range indices.
            print("  Invalid selection")  # WHY: tell operator.
            return None  # WHY: abort selection.
        return idx  # WHY: valid 0-based index.

    def _apply_single_site_choice(self, idx: int) -> bool:
        """Commit a single-site selection at the given 0-based index."""
        self.selected_sites = [self.all_sites[idx]]  # WHY: select exactly one site.
        self.is_single_site = True  # WHY: enable single-site pre-fill behaviour.
        print(f"  + Selected: {self.all_sites[idx].get('name')}")  # WHY: confirm the chosen site.
        self._fetch_current_site_settings(self.all_sites[idx]["id"])  # WHY: pre-fill from existing config.
        return True  # WHY: selection succeeded.

    def _fetch_current_site_settings(self, site_id: str) -> None:
        """Fetch current auto-upgrade settings for a single site (pre-fill)."""
        auto_upgrade = self._read_site_settings_payload(site_id)  # WHY: extract auto_upgrade block from API.
        if not auto_upgrade:  # WHY: nothing to pre-fill if the block is empty.
            return  # WHY: leave workflow state untouched.
        self._ingest_auto_upgrade_block(auto_upgrade)  # WHY: hydrate current_site_versions + schedule.

    def _response_has_data(self, response: Any) -> bool:
        """Return True when a mistapi response carries usable data."""
        return bool(response and hasattr(response, "data") and response.data)  # WHY: single-guard payload check.

    def _extract_auto_upgrade_from_response(self, response: Any) -> dict[str, Any]:
        """Pull the auto_upgrade sub-object from a mistapi settings response."""
        if not self._response_has_data(response):  # WHY: guard empty payload via helper.
            return {}  # WHY: nothing to read.
        settings = response.data if isinstance(response.data, dict) else {}  # WHY: only dict is usable.
        block = settings.get("auto_upgrade", {})  # WHY: read the auto_upgrade sub-object.
        return block if isinstance(block, dict) else {}  # WHY: normalize non-dict to empty.

    def _read_site_settings_payload(self, site_id: str) -> dict[str, Any]:
        """Read the auto_upgrade block from the site settings API."""
        try:
            import mistapi.api.v1.sites.setting as sites_setting_api  # WHY: lazy import to avoid cycles.

            response = sites_setting_api.getSiteSettings(self.apisession, site_id)  # WHY: fetch the site settings.
            return self._extract_auto_upgrade_from_response(response)  # WHY: extract block via helper.
        except Exception as exc:  # WHY: settings read may raise mistapi errors - non-fatal.
            logging.debug("Could not fetch current site settings: %s", exc)  # WHY: trace and continue.
            return {}  # WHY: pre-fill best-effort. Empty on failure.

    def _ingest_auto_upgrade_block(self, auto_upgrade: dict[str, Any]) -> None:
        """Hydrate current_site_versions and schedule from an auto_upgrade block."""
        self.current_site_versions = auto_upgrade.get("custom_versions", {})  # WHY: pre-fill version map.
        if auto_upgrade.get("day_of_week"):  # WHY: preserve existing schedule day if present.
            self.schedule["day_of_week"] = auto_upgrade["day_of_week"]  # WHY: pre-fill schedule day.
        if auto_upgrade.get("time_of_day"):  # WHY: preserve existing schedule time if present.
            self.schedule["time_of_day"] = auto_upgrade["time_of_day"]  # WHY: pre-fill schedule time.
        if self.current_site_versions:  # WHY: only report when we found something.
            count = len(self.current_site_versions)  # WHY: count configured models.
            print(  # WHY: tell operator about the pre-fill.
                f"  + Current auto-upgrade settings found ({count} model(s) configured)"
            )

    def _select_from_list(self) -> bool:  # WHY: select multiple sites via index expression.
        """Display numbered list and allow index/range selection."""
        _display_site_list(self.all_sites)  # WHY: show the site list.
        _display_selection_instructions()  # WHY: show the selection format instructions.
        try:
            selection = self.safe_input_fn(  # WHY: read the index expression.
                "  Selection: ", "auto_upgrade_config"
            ).strip()
        except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
            return False  # WHY: abort selection.
        if not selection:  # WHY: empty input is a bail-out.
            print("  No selection made")  # WHY: tell operator.
            return False  # WHY: abort selection.
        indices = _parse_index_selection(selection)  # WHY: parse expression into a sorted index list.
        if not indices:  # WHY: expression was malformed.
            print("  X Invalid selection format")  # WHY: tell operator.
            return False  # WHY: abort selection.
        return self._apply_site_indices(indices)  # WHY: apply the parsed indices.

    def _apply_site_indices(self, indices: list[int]) -> bool:  # WHY: resolve indices to sites.
        """Apply indices to select sites."""
        self._collect_valid_site_choices(indices)  # WHY: append in-range sites to selected_sites.
        if not self.selected_sites:  # WHY: no valid sites resolved from the input.
            print("  X No valid sites selected")  # WHY: tell operator.
            return False  # WHY: abort selection.
        self._report_selected_sites()  # WHY: preview the operator's selection.
        return True  # WHY: selection succeeded.

    def _collect_valid_site_choices(self, indices: list[int]) -> None:
        """Append in-range 1-based indices to selected_sites."""
        for idx in indices:  # WHY: walk each requested index.
            if 1 <= idx <= len(self.all_sites):  # WHY: keep only in-range indices.
                self.selected_sites.append(self.all_sites[idx - 1])  # WHY: 1-based to 0-based index.

    def _report_selected_sites(self) -> None:
        """Print the selection count and a preview of the first sites."""
        print(f"  + Selected {len(self.selected_sites)} site(s):")  # WHY: confirm selection count.
        for site in self.selected_sites[:5]:  # WHY: preview only the first few sites.
            print(f"      - {site.get('name')}")  # WHY: print each previewed site.
        if len(self.selected_sites) > 5:  # WHY: note remaining sites past preview limit.
            print(f"      ... and {len(self.selected_sites) - 5} more")  # WHY: note the remainder.

    # ------------------------------------------------------------------
    # Step 3: Fetch available versions
    # ------------------------------------------------------------------

    def _step3_fetch_available_versions(self) -> bool:  # WHY: step 3 loads AP firmware versions.
        """Fetch available firmware versions."""
        print("\n" + "-" * 70)  # WHY: visual section divider.
        print("  STEP 3: Available Firmware Versions")  # WHY: step header.
        print("-" * 70)  # WHY: visual section divider.
        print("  Fetching available AP firmware versions...")  # WHY: tell operator we are fetching.
        if self.apisession is None or self.org_id is None:  # WHY: cannot call API without session+org.
            print("  X API session or org_id not initialized")  # WHY: tell operator.
            return False  # WHY: abort step 3.
        payload = self._fetch_available_versions_payload()  # WHY: fetch the list from the API.
        if payload is None:  # WHY: None means the call failed.
            return False  # WHY: abort step 3.
        return self._ingest_available_versions_payload(payload)  # WHY: build model->versions map.

    def _fetch_available_versions_payload(self) -> list[Any] | None:
        """Call the org-devices API and return the list payload (or None)."""
        try:
            import mistapi.api.v1.orgs.devices as org_devices_api  # WHY: lazy import to avoid cycles.

            response = org_devices_api.listOrgAvailableDeviceVersions(  # WHY: list AP firmware versions.
                self.apisession, self.org_id, type="ap"
            )
            if not response or not hasattr(response, "data"):  # WHY: guard empty response.
                print("  X Failed to fetch available versions")  # WHY: tell operator.
                return None  # WHY: signal failure.
            return response.data if isinstance(response.data, list) else []  # WHY: normalize list payload.
        except Exception as exc:  # WHY: fetch may raise mistapi errors - treat as failure.
            print(f"  X Error fetching firmware versions: {exc}")  # WHY: tell operator.
            logging.error(  # WHY: action-log the fetch failure.
                "SiteAutoUpgradeConfigurator: Failed to fetch versions: %s", exc
            )
            return None  # WHY: signal failure.

    def _ingest_available_versions_payload(self, payload: list[Any]) -> bool:
        """Hydrate available_versions and model_version_map from a payload."""
        self.available_versions = payload  # WHY: store raw payload for later reference.
        self._build_model_version_map()  # WHY: build the per-model version map.
        print(  # WHY: confirm model count to operator.
            f"  + Found firmware for {len(self.model_version_map)} AP model(s)"
        )
        return True  # WHY: step 3 succeeded.

    def _build_model_version_map(self) -> None:  # WHY: group available versions by AP model.
        """Build model -> versions map from available versions."""
        for version_info in self.available_versions:  # WHY: walk each version record.
            if not _is_valid_version_entry(version_info):  # WHY: skip malformed records.
                continue  # WHY: continue to next record.
            model = version_info.get("model")  # WHY: pull the model name.
            self.model_version_map.setdefault(model, []).append(version_info)  # WHY: append the record.

    # ------------------------------------------------------------------
    # Step 4: Select versions
    # ------------------------------------------------------------------

    def _step4_select_versions(self) -> bool:  # WHY: step 4 selects firmware versions per model.
        """Select firmware version per AP model."""
        _print_step4_header(self.is_single_site, self.current_site_versions)  # WHY: print step header.
        self._prefill_current_site_versions()  # WHY: seed custom_versions with existing config if any.
        model_families = _group_models_by_family(self.model_version_map)  # WHY: group AP models by family.
        if not self._process_family_selection_loop(model_families):  # WHY: iterate families for selection.
            return False  # WHY: operator aborted mid-loop.
        if not self.custom_versions:  # WHY: nothing selected means nothing to configure.
            print("\n  X No versions selected")  # WHY: tell operator.
            return False  # WHY: abort step 4.
        print(f"\n  + Configured {len(self.custom_versions)} model(s)")  # WHY: confirm configured count.
        return True  # WHY: step 4 succeeded.

    def _prefill_current_site_versions(self) -> None:
        """Pre-fill custom_versions from a single site's existing settings."""
        if self.is_single_site and self.current_site_versions:  # WHY: only single-site mode has current versions.
            self.custom_versions = self.current_site_versions.copy()  # WHY: pre-fill from current settings.

    def _process_family_selection_loop(self, model_families: dict[str, list[str]]) -> bool:
        """Iterate each family, prompt operator, and apply their selection."""
        for family, models in sorted(model_families.items()):  # WHY: walk each family in stable order.
            if not self._prompt_and_apply_family(family, models):  # WHY: delegate per-family flow.
                return False  # WHY: operator aborted at this family.
        return True  # WHY: loop completed without operator abort.

    def _read_family_choice(self, num_versions: int) -> str | None:
        """Prompt for a numeric family choice. None on EOF."""
        try:
            raw = self.safe_input_fn(  # WHY: read the operator's numeric choice.
                f"  Select version (1-{num_versions}): ", "auto_upgrade_config"
            )
            return str(raw).strip()  # WHY: coerce injected callable's Any return to str.
        except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
            return None  # WHY: signal abort via None.

    def _prompt_and_apply_family(self, family: str, models: list[str]) -> bool:
        """Prompt the operator for one family and apply the selection."""
        sorted_versions = _get_family_versions(self.model_version_map, models)  # WHY: family versions.
        if not sorted_versions:  # WHY: skip families with no versions.
            return True  # WHY: nothing to prompt. Treat as success.
        current_version = _get_current_family_version(  # WHY: resolve family's current version.
            self.is_single_site, self.current_site_versions, models
        )
        _display_family_versions(family, models, sorted_versions, current_version)  # WHY: show choices.
        choice = self._read_family_choice(len(sorted_versions))  # WHY: read choice via helper.
        if choice is None:  # WHY: EOF-abort from safe_input.
            return False  # WHY: abort the outer loop.
        _apply_family_selection(  # WHY: commit the operator's family-level choice.
            choice,
            self.custom_versions,
            FamilySelectionContext(  # WHY: 5-field bundle satisfies the 5-Item Rule.
                family=family,
                models=models,
                sorted_versions=sorted_versions,
                current_version=current_version,
                model_version_map=self.model_version_map,
            ),
        )
        return True  # WHY: family processed successfully.

    # ------------------------------------------------------------------
    # Step 5: Configure schedule
    # ------------------------------------------------------------------

    def _step5_configure_schedule(self) -> None:  # WHY: step 5 configures the maintenance-window schedule.
        """Configure upgrade schedule."""
        print("\n" + "-" * 70)  # WHY: visual section divider.
        print("  STEP 5: Schedule Configuration (Optional)")  # WHY: step header.
        print("-" * 70)  # WHY: visual section divider.
        print("\n  Configure when auto-upgrades should occur.\n")  # WHY: explain the step to operator.
        self.schedule["day_of_week"] = _prompt_day_of_week(self.safe_input_fn)  # WHY: prompt for day.
        self.schedule["time_of_day"] = _prompt_time_of_day(  # WHY: prompt for time-of-day.
            self.safe_input_fn, parse_time_input
        )
        day_display = self.schedule.get("day_of_week", "daily")  # WHY: resolve day for display.
        if day_display == "any":  # WHY: normalize 'any' to friendly 'daily' label.
            day_display = "daily"  # WHY: friendlier display.
        time_display = self.schedule.get("time_of_day", "any time")  # WHY: resolve time for display.
        if time_display == "any":  # WHY: normalize 'any' to friendly label.
            time_display = "any time"  # WHY: friendlier display.
        print(f"  + Schedule: {day_display} at {time_display}")  # WHY: show chosen schedule.

    # ------------------------------------------------------------------
    # Step 6: Confirm and apply
    # ------------------------------------------------------------------

    def _step6_confirm_and_apply(self) -> None:  # WHY: step 6 confirms then applies the config.
        """Confirm settings and apply to selected sites."""
        print("\n" + "-" * 70)  # WHY: visual section divider.
        print("  STEP 6: Confirm and Apply")  # WHY: step header.
        print("-" * 70 + "\n")  # WHY: visual section divider.
        _display_step6_summary(  # WHY: show operator the pre-apply summary.
            self.selected_sites, self.custom_versions, self.schedule
        )
        if not self._prompt_step6_confirm():  # WHY: read Y/N confirmation (skipped for dry-run).
            return  # WHY: operator declined - abort apply.
        self._apply_step6_settings()  # WHY: build payload and push to sites.

    def _prompt_step6_confirm(self) -> bool:
        """Return True when the operator confirms (dry-run auto-confirms)."""
        if self.dry_run:  # WHY: dry-run bypasses confirmation entirely.
            return True  # WHY: allow apply loop to run for reporting.
        try:
            confirm = (
                self.safe_input_fn(  # WHY: read Y/N via EOF-safe prompt.
                    "  Apply these settings? (y/N): ", "auto_upgrade_config"
                )
                .strip()
                .lower()
            )
        except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
            return False  # WHY: abort apply.
        if confirm not in ("y", "yes"):  # WHY: default N. Only explicit yes proceeds.
            print("  Cancelled.")  # WHY: tell operator we bailed.
            return False  # WHY: abort apply.
        return True  # WHY: operator confirmed.

    def _apply_step6_settings(self) -> None:
        """Build the auto_upgrade payload and push it to every selected site."""
        auto_upgrade = _build_auto_upgrade_payload(  # WHY: canonical payload builder.
            self.custom_versions, self.schedule
        )
        settings = {"auto_upgrade": auto_upgrade}  # WHY: wrap in the site-settings object.
        label = "DRY-RUN: Simulating" if self.dry_run else "Applying"  # WHY: label reflects mode.
        print(f"\n  {label} configuration...")  # WHY: announce the apply step.
        successful, failed = _apply_settings_to_sites(  # WHY: push settings to every selected site.
            sites=self.selected_sites,
            settings=settings,
            apisession=self.apisession,
            check_stop_fn=self.check_stop_fn,
            dry_run=self.dry_run,
        )
        _print_final_summary(successful, failed, self.dry_run)  # WHY: print success/failure summary.


# ======================================================================
# Module-level helper functions (reduce class CC)
# ======================================================================


def _handle_msp_mode(  # WHY: dispatch single-org vs MSP multi-org mode.
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
    get_org_id_fn: GetOrgIdFn,
) -> None:
    """Handle MSP privilege detection and mode selection."""
    logging.debug("Entering _handle_msp_mode")  # WHY: action-log entry.
    _print_msp_mode_banner(core.dry_run)  # WHY: print header + optional dry-run warning.
    try:
        mode = (
            core.safe_input_fn(  # WHY: read the mode choice via EOF-safe prompt.
                "  Select mode (1-2) [1]: ", "msp_mode_select"
            ).strip()
            or "1"
        )
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF - bail cleanly.
        return  # WHY: operator aborted.
    _dispatch_msp_mode_choice(mode, core, msp, get_org_id_fn)  # WHY: run chosen mode.


def _print_msp_mode_banner(dry_run: bool) -> None:
    """Print the MSP-mode intro banner and options list."""
    print("\n" + "=" * 70)  # WHY: visual banner - ASCII only per logging standards.
    print("  SITE AUTO-UPGRADE CONFIGURATION")  # WHY: title header.
    print("=" * 70 + "\n")  # WHY: divider.
    if dry_run:  # WHY: only advertise dry-run when active.
        print("  >> DRY-RUN MODE: No actual changes will be made <<\n")  # WHY: warn active dry-run.
    print("  MSP privileges detected. Select operation mode:\n")  # WHY: explain MSP options.
    print("    [1] Single Organization - configure auto-upgrade for current org")  # WHY: opt 1.
    print("    [2] MSP Multi-Org - configure ALL sites across multiple orgs\n")  # WHY: opt 2.


def _dispatch_msp_mode_choice(
    mode: str,
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
    get_org_id_fn: GetOrgIdFn,
) -> None:
    """Route the operator's mode choice to the correct workflow."""
    if mode == "2":  # WHY: operator chose the multi-org MSP workflow.
        logging.info("User selected MSP Multi-Org mode")  # WHY: action-log the operator's choice.
        _execute_msp_mode(core, msp)  # WHY: run the MSP multi-org flow.
        return  # WHY: MSP mode owns the rest of the workflow.
    _run_single_org(core, get_org_id_fn)  # WHY: fall back to single-org flow.


def _run_single_org(  # WHY: run the single-org configuration path.
    core: SiteAutoUpgradeCoreDeps,
    get_org_id_fn: GetOrgIdFn,
) -> None:
    """Run single-org configuration workflow."""
    logging.debug("Entering _run_single_org")  # WHY: action-log entry.
    org_id = get_org_id_fn()  # WHY: prompt operator (or read cache) for the target org id.
    if not org_id:  # WHY: no org id means the operator cancelled or nothing is available.
        print("  X No organization selected")  # WHY: tell operator.
        return  # WHY: bail cleanly.
    configurator = SiteAutoUpgradeConfigurator(org_id=org_id, deps=core)  # WHY: build the per-org workflow class.
    configurator.run()  # WHY: run the 6-step interactive workflow.


def _msp_select_entities(  # WHY: select MSPs then their orgs.
    select_msps_fn: SelectMspsFn,
    select_orgs_fn: SelectOrgsFromMspFn,
) -> list[dict[str, Any]] | None:
    """Select MSPs and organizations for MSP mode."""
    selected_msps = _select_msps_or_bail(select_msps_fn)  # WHY: step 1 - select MSPs (or bail).
    if selected_msps is None:  # WHY: None signals operator cancelled.
        return None  # WHY: abort entity selection.
    selected_orgs = _select_orgs_or_bail(select_orgs_fn, selected_msps)  # WHY: step 2 - select orgs.
    if selected_orgs is None:  # WHY: None signals operator cancelled.
        return None  # WHY: abort entity selection.
    print(f"\n  Selected {len(selected_orgs)} organization(s)")  # WHY: confirm org count.
    return list(selected_orgs)  # WHY: materialize the selected orgs list.


def _select_msps_or_bail(select_msps_fn: SelectMspsFn) -> list[Any] | None:
    """Run the MSP selection prompt. Return None on empty selection."""
    print("\n" + "-" * 70)  # WHY: visual section divider.
    print("  STEP 1: MSP Selection")  # WHY: step header.
    print("-" * 70 + "\n")  # WHY: visual section divider.
    selected_msps = select_msps_fn()  # WHY: prompt for MSP selection via injected callable.
    if not selected_msps:  # WHY: no MSPs chosen means abort.
        print("  No MSPs selected. Returning.")  # WHY: tell operator.
        return None  # WHY: signal abort.
    result: list[Any] = list(selected_msps)  # WHY: materialize the selection list.
    return result  # WHY: return the selected MSPs.


def _select_orgs_or_bail(select_orgs_fn: SelectOrgsFromMspFn, selected_msps: list[Any]) -> list[dict[str, Any]] | None:
    """Run the org selection prompt within the chosen MSPs. None on empty."""
    print("\n" + "-" * 70)  # WHY: visual section divider.
    print("  STEP 2: Organization Selection")  # WHY: step header.
    print("-" * 70 + "\n")  # WHY: visual section divider.
    selected_orgs = select_orgs_fn(selected_msps)  # WHY: prompt for org selection within MSPs.
    if not selected_orgs:  # WHY: no orgs chosen means abort.
        print("  No organizations selected. Returning.")  # WHY: tell operator.
        return None  # WHY: signal abort.
    result: list[dict[str, Any]] = list(selected_orgs)  # WHY: materialize the selection list.
    return result  # WHY: return the selected orgs.


def _msp_get_firmware_config(  # WHY: pick shared firmware versions for MSP orgs.
    apisession: Any,
    selected_orgs: list[dict[str, Any]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Prompt user for firmware version selection in MSP mode."""
    fw_choice = _prompt_msp_firmware_source_choice(safe_input_fn)  # WHY: choose auto vs manual.
    if fw_choice is None:  # WHY: operator aborted at the prompt.
        return None  # WHY: signal abort.
    if fw_choice != "2" or not selected_orgs:  # WHY: not manual (or no orgs) means auto-detect.
        return {}  # WHY: empty dict = auto-detect per org.
    return _get_shared_firmware_versions(  # WHY: manual - pick shared versions from reference org.
        apisession, selected_orgs[0], safe_input_fn
    )


def _prompt_msp_firmware_source_choice(safe_input_fn: SafeInputFn) -> str | None:
    """Prompt operator to choose auto-detect vs manual firmware selection."""
    print("\n" + "-" * 70)  # WHY: visual section divider.
    print("  STEP 3: Firmware Version Configuration")  # WHY: step header.
    print("-" * 70 + "\n")  # WHY: visual section divider.
    print("  How to select firmware versions?\n")  # WHY: explain the choice.
    print("    [1] Auto-detect latest stable per model for each org")  # WHY: opt 1.
    print("    [2] Manually select firmware versions (from reference org)\n")  # WHY: opt 2.
    try:
        return (
            safe_input_fn(  # WHY: read the firmware-source choice via EOF-safe prompt.
                "  Selection (1-2) [1]: ", "msp_firmware"
            ).strip()
            or "1"
        )
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        return None  # WHY: signal abort.


def _msp_confirm_and_apply(  # WHY: confirm then apply across MSP orgs.
    core: SiteAutoUpgradeCoreDeps,
    selected_orgs: list[dict[str, Any]],
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
) -> None:
    """Display summary, confirm, and apply MSP configuration."""
    logging.debug("Entering _msp_confirm_and_apply")  # WHY: action-log entry.
    _display_msp_pre_apply_summary(  # WHY: show planned changes before firing.
        shared_schedule, shared_versions, selected_orgs
    )
    if not _prompt_msp_final_confirm(core.safe_input_fn):  # WHY: gate on Y/n confirmation.
        return  # WHY: operator declined or aborted.
    _apply_msp_config(core, selected_orgs, shared_schedule, shared_versions)  # WHY: run apply step.


def _prompt_msp_final_confirm(safe_input_fn: SafeInputFn) -> bool:
    """Read Y/n confirmation for MSP apply. Default Y on bare Enter."""
    try:
        final_confirm = (
            safe_input_fn(  # WHY: read the Y/n via EOF-safe prompt.
                "  Apply this configuration? (Y/n): ", "msp_final_confirm"
            )
            .strip()
            .lower()
        )
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        return False  # WHY: abort apply.
    if final_confirm in ["n", "no"]:  # WHY: explicit no aborts.
        print("  Cancelled.")  # WHY: tell operator we bailed.
        return False  # WHY: abort apply.
    return True  # WHY: default Y or explicit yes proceeds.


def _apply_msp_config(
    core: SiteAutoUpgradeCoreDeps,
    selected_orgs: list[dict[str, Any]],
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
) -> None:
    """Print step-6 header, apply across every org, then print summary."""
    print("\n" + "-" * 70)  # WHY: visual step separator.
    print("  STEP 6: Applying Configuration")  # WHY: step header.
    print("-" * 70)  # WHY: visual section divider.
    logging.info(  # WHY: action-log the apply step across orgs.
        "Applying MSP config across %d org(s)", len(selected_orgs)
    )
    all_results = _apply_to_all_orgs(  # WHY: run the per-org configurator.
        core, selected_orgs, shared_schedule, shared_versions
    )
    logging.debug("Completed MSP apply across %d org(s)", len(all_results))  # WHY: trace completion.
    _print_msp_summary(all_results, core.dry_run)  # WHY: final results table for operator.


def _execute_msp_mode(  # WHY: execute the MSP multi-org flow.
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
) -> None:
    """Execute MSP multi-organization auto-upgrade configuration."""
    logging.debug("Entering _execute_msp_mode")  # WHY: action-log entry.
    if not msp.select_msps_fn or not msp.select_orgs_fn:  # WHY: MSP DI is optional at boundary.
        print("  X MSP functions not available")  # WHY: tell operator.
        return  # WHY: bail out - MSP callables missing.
    result = _msp_gather_config(core, msp)  # WHY: collect orgs + versions + schedule.
    if result is None:  # WHY: None means operator cancelled at some prompt.
        return  # WHY: bail cleanly - nothing to apply.
    selected_orgs, shared_versions, shared_schedule = result  # WHY: unpack the gathered config.
    _msp_confirm_and_apply(  # WHY: step 6 - confirm + apply across every org.
        core,
        selected_orgs,
        shared_schedule,
        shared_versions if shared_versions else None,
    )


_MspGatherResult = tuple[
    list[dict[str, Any]],
    dict[str, str] | None,
    dict[str, str],
]  # WHY: aliases the MSP gather return shape to keep the function under 25 lines.


def _msp_gather_config(
    core: SiteAutoUpgradeCoreDeps,
    msp: SiteAutoUpgradeMspDeps,
) -> _MspGatherResult | None:
    """Gather MSPs+orgs, shared versions, and shared schedule (or None)."""
    selected_orgs = _msp_select_entities(msp.select_msps_fn, msp.select_orgs_fn)  # WHY: steps 1+2 - pick MSPs and orgs.
    if not selected_orgs:  # WHY: operator cancelled selection.
        return None  # WHY: cleanly exit - nothing to apply.
    shared_versions = _msp_get_firmware_config(  # WHY: step 3 - pick firmware source.
        core.apisession, selected_orgs, core.safe_input_fn
    )
    if shared_versions is None:  # WHY: None means the operator cancelled the version prompt.
        return None  # WHY: cleanly exit - nothing to apply.
    shared_schedule = _msp_prompt_shared_schedule(core.safe_input_fn)  # WHY: steps 4+5 - schedule.
    if shared_schedule is None:  # WHY: operator cancelled schedule prompt.
        return None  # WHY: cleanly exit - nothing to apply.
    return (selected_orgs, shared_versions, shared_schedule)  # WHY: return the gathered config.


def _msp_prompt_shared_schedule(safe_input_fn: SafeInputFn) -> dict[str, Any] | None:
    """Print the schedule step header and prompt for the shared schedule."""
    print("\n" + "-" * 70)  # WHY: visual step separator.
    print("  STEP 4: Schedule Configuration")  # WHY: step header.
    print("-" * 70 + "\n")  # WHY: visual section divider.
    return _get_shared_schedule(safe_input_fn)  # WHY: read the shared schedule via the module helper.


def _apply_to_all_orgs(  # WHY: apply shared config to every selected org.
    core: SiteAutoUpgradeCoreDeps,
    selected_orgs: list[dict[str, Any]],
    shared_schedule: dict[str, Any],
    shared_versions: dict[str, str] | None,
) -> list[dict[str, Any]]:
    """Apply configuration to all selected organizations."""
    logging.debug("Entering _apply_to_all_orgs for %d org(s)", len(selected_orgs))  # WHY: action-log entry.
    all_results: list[dict[str, Any]] = []  # WHY: accumulate one result dict per org.
    total = len(selected_orgs)  # WHY: cache count for header printing.
    for idx, org_info in enumerate(selected_orgs, start=1):  # WHY: 1-based for operator-visible progress.
        ctx = _MspOrgApplyContext(  # WHY: bundle per-org context to satisfy 5-Item Rule.
            core=core,
            idx=idx,
            total=total,
            shared_schedule=shared_schedule,
            shared_versions=shared_versions,
        )
        result = _configure_single_msp_org(org_info, ctx)  # WHY: run the per-org configuration.
        all_results.append(result)  # WHY: record the org's result.
    return all_results  # WHY: return all per-org results.


def _configure_single_msp_org(
    org_info: dict[str, Any],
    ctx: _MspOrgApplyContext,
) -> dict[str, Any]:
    """Run the auto-upgrade configurator for a single MSP-selected org."""
    org_id = org_info["id"]  # WHY: pull org id for the configurator + log lines.
    org_name = org_info["name"]  # WHY: pull org name for operator-visible logs.
    print(f"\n{'=' * 70}")  # WHY: visual per-org separator.
    print(f"  ORGANIZATION {ctx.idx}/{ctx.total}: {org_name}")  # WHY: per-org progress header.
    print("=" * 70)  # WHY: visual divider.
    configurator = SiteAutoUpgradeConfigurator(org_id=org_id, deps=ctx.core)  # WHY: build the per-org workflow class.
    configurator.msp_all_sites_mode = True  # WHY: skip site-selection prompt in MSP mode.
    configurator.org_name = org_name  # WHY: set org name on the configurator for logs.
    configurator.schedule = ctx.shared_schedule.copy()  # WHY: copy shared schedule per org.
    configurator.shared_versions = ctx.shared_versions  # WHY: attach shared versions per org.
    success, site_count = configurator.run_msp_mode()  # WHY: run per-org MSP configuration.
    return {  # WHY: record the org's outcome.
        "org_id": org_id,
        "org_name": org_name,
        "success": success,
        "sites_configured": site_count,
    }


# ======================================================================
# Pure helper functions
# ======================================================================


def _print_intro_header(dry_run: bool) -> None:  # WHY: print intro/warning header.
    """Print introduction header for the configuration workflow."""
    print("\n" + "=" * 70)  # WHY: visual divider.
    print("  SITE AUTO-UPGRADE CONFIGURATION")  # WHY: title.
    print("=" * 70 + "\n")  # WHY: visual divider.
    if dry_run:  # WHY: dry-run banner only when relevant.
        print("  >> DRY-RUN MODE: No actual changes will be made <<\n")  # WHY: warn no changes.
    print("  This tool configures auto-upgrade settings for sites WITHOUT")  # WHY: explain tool.
    print("  initiating immediate upgrades. Auto-upgrade ensures:")  # WHY: explain auto-upgrade.
    print("    - New APs automatically upgrade to target firmware")  # WHY: bullet.
    print("    - Scheduled upgrades during maintenance windows\n")  # WHY: bullet.


def _display_site_list(all_sites: list[dict[str, Any]]) -> None:  # WHY: display numbered site list.
    """Display numbered list of all sites."""
    print(f"\n  All Sites ({len(all_sites)} total):")  # WHY: list header with count.
    print("-" * 70)  # WHY: visual divider.
    for idx, site in enumerate(all_sites, 1):  # WHY: 1-based enumeration for operator readability.
        print(f"    [{idx:>3}] {site.get('name', 'Unknown')}")  # WHY: print each site.
    print("")  # WHY: trailing spacer.


def _display_selection_instructions() -> None:  # WHY: show index-selection instructions.
    """Display selection format instructions."""
    print("  Enter selection:")  # WHY: instructions header.
    print("    - Single: 5")  # WHY: single example.
    print("    - Multiple: 1,3,5,7")  # WHY: multiple example.
    print("    - Range: 1-10")  # WHY: range example.
    print("    - Combined: 1-5,8,12-15\n")  # WHY: combined example.


def _parse_index_selection(selection: str) -> list[int]:  # WHY: parse index expression.
    """Parse index selection string into sorted list of integers."""
    indices: set[int] = set()  # WHY: collect distinct indices.
    parts = selection.replace(" ", "").split(",")  # WHY: comma-split with whitespace stripped.
    for part in parts:  # WHY: walk each comma-separated part.
        if "-" in part:  # WHY: hyphen means a range expression.
            _parse_range_part(part, indices)  # WHY: delegate range parsing.
        else:
            _parse_single_part(part, indices)  # WHY: delegate single-index parsing.
    return sorted(indices)  # WHY: return sorted distinct indices.


def _parse_range_part(part: str, indices: set[int]) -> None:
    """Parse a 'start-end' range and add inclusive integers to the set."""
    try:
        range_parts = part.split("-")  # WHY: split the range into start+end tokens.
        if len(range_parts) == 2:  # WHY: only well-formed pairs are valid.
            start = int(range_parts[0])  # WHY: parse start index.
            end = int(range_parts[1])  # WHY: parse end index.
            indices.update(range(start, end + 1))  # WHY: add the inclusive range.
    except ValueError:  # WHY: non-numeric range - skip.
        return  # WHY: silently ignore malformed parts.


def _parse_single_part(part: str, indices: set[int]) -> None:
    """Parse a single integer token and add it to the set."""
    try:
        indices.add(int(part))  # WHY: add the single index.
    except ValueError:  # WHY: non-numeric single index - skip.
        return  # WHY: silently ignore malformed parts.


def _group_models_by_family(  # WHY: group AP models into families.
    model_version_map: dict[str, list[Any]],
) -> dict[str, list[str]]:
    """Group models by family prefix (AP41, AP43, and so on)."""
    model_families: dict[str, list[str]] = {}  # WHY: family -> member-models map.
    for model in sorted(model_version_map.keys()):  # WHY: sorted order for stable output.
        family = model.rstrip("EP")  # WHY: strip E/P suffixes to get the family.
        model_families.setdefault(family, []).append(model)  # WHY: append model to its family.
    return model_families  # WHY: return the family map.


def _get_family_versions(  # WHY: collect sorted versions across a family.
    model_version_map: dict[str, list[Any]],
    models: list[str],
) -> list[str]:
    """Get sorted versions for a model family."""
    family_versions: set[str] = set()  # WHY: distinct version strings.
    for model in models:  # WHY: walk each family model.
        for entry in model_version_map.get(model, []):  # WHY: walk that model's version entries.
            version = entry.get("version") if isinstance(entry, dict) else entry  # WHY: normalize.
            if version:  # WHY: only keep truthy versions.
                family_versions.add(str(version))  # WHY: add the version string.
    return sorted(family_versions, reverse=True)  # WHY: return newest-first versions.


def _get_current_family_version(  # WHY: resolve a family's current version.
    is_single_site: bool,
    current_site_versions: dict[str, str],
    models: list[str],
) -> str | None:
    """Get current version for a model family if in single-site mode."""
    if not is_single_site:  # WHY: only single-site has a current version.
        return None  # WHY: no current version otherwise.
    for model in models:  # WHY: walk the family's models.
        if model in current_site_versions:  # WHY: model has a configured version.
            return current_site_versions[model]  # WHY: return it.
    return None  # WHY: no current version found.


def _display_family_versions(  # WHY: display a family's version choices.
    family: str,
    models: list[str],
    sorted_versions: list[str],
    current_version: str | None,
) -> None:
    """Display version options for a model family."""
    print(f"\n  {family} family ({', '.join(models)}):")  # WHY: family header with members.
    for idx, version in enumerate(sorted_versions, 1):  # WHY: 1-based enumeration.
        marker = " <-- current" if version == current_version else ""  # WHY: mark current version.
        print(f"    [{idx:>2}] {version}{marker}")  # WHY: print numbered version.
    if current_version:  # WHY: a current version exists.
        print(f"    [Enter] Keep current: {current_version}")  # WHY: offer to keep on Enter.
    else:
        print("    [Enter] Skip")  # WHY: offer to skip on Enter.


def _apply_family_selection(  # WHY: apply the operator's family selection.
    choice: str,
    custom_versions: dict[str, str],
    ctx: FamilySelectionContext,
) -> None:
    """Apply user's version selection for a model family."""
    logging.debug(  # WHY: action-log entry with family context.
        "Entering _apply_family_selection for family %s", ctx.family
    )
    if choice and choice.isdigit():  # WHY: numeric choice picks a specific version.
        _apply_family_numeric_choice(choice, custom_versions, ctx)  # WHY: delegate numeric branch.
        return  # WHY: numeric branch handled.
    _apply_family_default_choice(ctx)  # WHY: bare Enter branch.


def _apply_family_numeric_choice(
    choice: str,
    custom_versions: dict[str, str],
    ctx: FamilySelectionContext,
) -> None:
    """Apply a numeric family-version choice across all family models."""
    idx = int(choice) - 1  # WHY: translate 1-based display to 0-based list index.
    if not 0 <= idx < len(ctx.sorted_versions):  # WHY: guard against off-by-one.
        return  # WHY: out-of-range - silently ignore.
    selected = ctx.sorted_versions[idx]  # WHY: pull the chosen version string.
    for model in ctx.models:  # WHY: apply the same version to every model in the family.
        model_versions = _extract_version_strings(  # WHY: check the model's actual version list.
            ctx.model_version_map.get(model, [])
        )
        if selected in model_versions:  # WHY: only set when version exists for this model.
            custom_versions[model] = selected  # WHY: record the selection.
    print(f"    + Set {ctx.family} models to {selected}")  # WHY: confirm to operator.


def _apply_family_default_choice(
    ctx: FamilySelectionContext,
) -> None:
    """Handle bare-Enter choice (keep current or skip family)."""
    if ctx.current_version:  # WHY: Enter + current version -> keep it.
        print(f"    + Keeping {ctx.family} models at {ctx.current_version}")  # WHY: confirm.
        return  # WHY: keep-current branch done.
    print(f"    - Skipped {ctx.family} family")  # WHY: Enter + no current version -> skip.


def _extract_version_strings(entries: list[Any]) -> list[str]:  # WHY: extract version strings.
    """Extract version strings from a list of version entries."""
    result: list[str] = []  # WHY: collected version strings.
    for entry in entries:  # WHY: walk each entry.
        ver = entry.get("version") if isinstance(entry, dict) else entry  # WHY: normalize.
        if ver:  # WHY: only keep truthy versions.
            result.append(str(ver))  # WHY: add the version string.
    return result  # WHY: return the strings.


def _print_step4_header(  # WHY: print step-4 header.
    is_single_site: bool,
    current_site_versions: dict[str, str],
) -> None:
    """Print step 4 header and instructions."""
    print("\n" + "-" * 70)  # WHY: visual section divider.
    print("  STEP 4: Firmware Version Selection")  # WHY: step header.
    print("-" * 70 + "\n")  # WHY: visual section divider.
    print("  Select firmware version for each AP model family.")  # WHY: explain per-family selection.
    if is_single_site and current_site_versions:  # WHY: single-site with existing config.
        print("  Press Enter to keep current version, or select a new one.")  # WHY: Enter-keeps-current.
        print(f"  (Pre-loaded {len(current_site_versions)} existing model configurations)")  # WHY: pre-fill count.
    else:
        print("  Press Enter to skip a model (won't be included in auto-upgrade).")  # WHY: Enter-skips.
    print("")  # WHY: spacer.


def _pick_stable_version(versions: list[Any]) -> str:  # WHY: pick the most stable version.
    """Pick the latest stable version from a list of version entries."""
    stable_version = _first_stable_or_none(versions)  # WHY: prefer stable-tagged first.
    if stable_version is not None:  # WHY: found one - return it immediately.
        return stable_version  # WHY: return the stable version string.
    return _first_any_version(versions)  # WHY: fall back to any version.


def _first_stable_or_none(versions: list[Any]) -> str | None:
    """Return the first stable-tagged version string, or None."""
    for entry in versions:  # WHY: walk each entry.
        if isinstance(entry, dict) and entry.get("tag") == "stable":  # WHY: match stable-tagged entries.
            return str(entry.get("version", ""))  # WHY: return the stable version string.
    return None  # WHY: no stable version found.


def _first_any_version(versions: list[Any]) -> str:
    """Return the first version string from a list of entries, or empty."""
    if not versions:  # WHY: empty list means no versions.
        return ""  # WHY: no versions - empty string.
    first = versions[0]  # WHY: take the first entry.
    if isinstance(first, dict):  # WHY: dict-shaped entry.
        return str(first.get("version", ""))  # WHY: return its version field.
    return str(first)  # WHY: entry is already a version string.


def _prompt_day_of_week(safe_input_fn: SafeInputFn) -> str:  # WHY: prompt for upgrade day.
    """Prompt for day of week selection."""
    print("  Day of week options:")  # WHY: options header.
    print("    [1] Daily (any day)  [2] Sunday   [3] Monday")  # WHY: Daily/Sun/Mon row.
    print("    [4] Tuesday          [5] Wednesday [6] Thursday")  # WHY: Tue/Wed/Thu row.
    print("    [7] Friday           [8] Saturday")  # WHY: Fri/Sat row.
    day_map = {  # WHY: choice -> day-name map.
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
        choice = safe_input_fn(  # WHY: read the day choice via EOF-safe prompt.
            "  Day of week (1-8, default=1 for daily): ", "auto_upgrade_config"
        ).strip()
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        choice = "1"  # WHY: default to daily.
    return day_map.get(choice, "any")  # WHY: resolve choice to a day (default any).


def _prompt_time_of_day(  # WHY: prompt for upgrade time-of-day.
    safe_input_fn: SafeInputFn,
    parse_fn: Any,
) -> str:
    """Prompt for time of day selection."""
    print("\n  Time of day for upgrades:")  # WHY: explain the time prompt.
    print("    Examples: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM")  # WHY: show accepted formats.
    print("    Leave blank for any time")  # WHY: blank means any time.
    try:
        time_input = safe_input_fn("  Time: ", "auto_upgrade_config").strip()  # WHY: read the time input.
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        time_input = ""  # WHY: default to blank.
    result: str = parse_fn(time_input)  # WHY: parse the time via the injected parser.
    return result  # WHY: return the parsed time.


def _is_valid_hhmm(hour: int, minute: int) -> bool:
    """Return True when hour/minute fall within the valid HH:MM range."""
    return 0 <= hour <= 23 and 0 <= minute <= 59  # WHY: single boolean guard for HH:MM range.


def parse_time_input(time_input: str) -> str:  # WHY: parse a free-form time string.
    """Parse various time formats to HH:MM for the API.

    Accepts: 02:00, 2:00, 14:00, 2AM, 2PM, 02:00AM, and so on
    Returns: HH:MM format string, or 'any' for any time.
    """
    if not time_input:  # WHY: empty input maps to 'any'.
        return "any"  # WHY: default.
    is_pm, is_am, time_clean = _parse_time_markers(time_input)  # WHY: strip and detect AM/PM.
    hour, minute = _parse_hour_minute(time_clean)  # WHY: parse hour and minute.
    if hour < 0:  # WHY: negative hour signals a parse failure.
        return "any"  # WHY: return 'any' on parse failure.
    hour = _apply_ampm(hour, is_am, is_pm)  # WHY: apply AM/PM to 24h.
    if not _is_valid_hhmm(hour, minute):  # WHY: guard out-of-range HH:MM.
        return "any"  # WHY: return 'any' on out-of-range.
    return f"{hour:02d}:{minute:02d}"  # WHY: return zero-padded HH:MM.


def _parse_time_markers(time_input: str) -> tuple[bool, bool, str]:
    """Detect AM/PM markers and return (is_pm, is_am, cleaned) tuple."""
    time_upper = time_input.upper().strip()  # WHY: normalize case + whitespace.
    is_pm = "PM" in time_upper  # WHY: detect PM marker.
    is_am = "AM" in time_upper  # WHY: detect AM marker.
    time_clean = time_upper.replace("AM", "").replace("PM", "").strip()  # WHY: strip AM/PM.
    return (is_pm, is_am, time_clean)  # WHY: return the detection tuple.


def _parse_hour_minute(time_clean: str) -> tuple[int, int]:  # WHY: parse hour/minute.
    """Parse hour and minute from cleaned time string."""
    if ":" in time_clean:  # WHY: colon means explicit minute.
        parts = time_clean.split(":")  # WHY: split hour and minute.
        try:
            hour = int(parts[0])  # WHY: parse hour.
            minute = int(parts[1]) if len(parts) > 1 else 0  # WHY: parse minute (default 0).
            return (hour, minute)  # WHY: return the pair.
        except ValueError:  # WHY: non-numeric time.
            return (-1, 0)  # WHY: signal parse failure.
    try:
        return (int(time_clean), 0)  # WHY: hour-only input.
    except ValueError:  # WHY: non-numeric hour.
        return (-1, 0)  # WHY: signal parse failure.


def _apply_ampm(hour: int, is_am: bool, is_pm: bool) -> int:  # WHY: 12h -> 24h using AM/PM.
    """Apply AM/PM conversion to hour value."""
    if is_pm and hour < 12:  # WHY: PM and not noon shifts into afternoon.
        hour += 12  # WHY: shift into afternoon.
    elif is_am and hour == 12:  # WHY: 12 AM is midnight.
        hour = 0  # WHY: map 12 AM to hour 0.
    return hour  # WHY: return the 24h hour.


def _display_step6_summary(  # WHY: print step-6 pre-apply summary.
    selected_sites: list[dict[str, Any]],
    custom_versions: dict[str, str],
    schedule: dict[str, Any],
) -> None:
    """Display configuration summary for step 6."""
    day_display = schedule.get("day_of_week") or "daily"  # WHY: resolve the display day.
    time_display = schedule.get("time_of_day") or "any time"  # WHY: resolve the display time.
    print("  Summary:")  # WHY: summary header.
    print(f"    Sites: {len(selected_sites)}")  # WHY: show site count.
    print(f"    Models configured: {len(custom_versions)}")  # WHY: show model count.
    for model, version in sorted(custom_versions.items()):  # WHY: list each model/version.
        print(f"      {model}: {version}")  # WHY: print the pair.
    print(f"    Schedule: {day_display} at {time_display}\n")  # WHY: show the schedule.


def _build_auto_upgrade_payload(  # WHY: build the auto_upgrade settings payload.
    custom_versions: dict[str, str],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    """Build the auto-upgrade configuration payload."""
    return {  # WHY: return the Mist auto_upgrade object.
        "enabled": True,  # WHY: enable auto-upgrade at the site.
        "version": "custom",  # WHY: 'custom' selects per-model overrides.
        "custom_versions": custom_versions,  # WHY: per-model chosen versions.
        "day_of_week": schedule.get("day_of_week", "any"),  # WHY: default any = daily.
        "time_of_day": schedule.get("time_of_day", "any"),  # WHY: default any time.
    }


def _apply_settings_to_sites(  # WHY: apply settings to each site, counting results.
    sites: list[dict[str, Any]],
    settings: dict[str, Any],
    apisession: Any,
    check_stop_fn: CheckStopFn,
    dry_run: bool,
) -> tuple[int, int]:
    """Apply settings to sites. Returns (successful, failed) counts."""
    successful = 0  # WHY: success counter.
    failed = 0  # WHY: failure counter.
    for site in sites:  # WHY: walk each site.
        if check_stop_fn():  # WHY: honor a stop request.
            break  # WHY: stop processing sites.
        ok = _apply_settings_to_single_site(site, settings, apisession, dry_run)  # WHY: delegate.
        if ok:  # WHY: success path.
            successful += 1  # WHY: count success.
        else:
            failed += 1  # WHY: count failure.
    return (successful, failed)  # WHY: return counts.


def _apply_settings_to_single_site(
    site: dict[str, Any],
    settings: dict[str, Any],
    apisession: Any,
    dry_run: bool,
) -> bool:
    """Apply settings to one site. Returns True on success, False on failure."""
    site_id = site.get("id")  # WHY: read the site id.
    site_name = site.get("name", "Unknown")  # WHY: read the site name for logs.
    if not site_id:  # WHY: missing site id means we cannot call the API.
        return False  # WHY: count as a failure.
    try:
        _perform_site_settings_update(site_name, site_id, settings, apisession, dry_run)  # WHY: do work.
        return True  # WHY: success (dry-run or real).
    except Exception as exc:  # WHY: apply may raise mistapi errors - treat as failure.
        print(f"    [FAIL] {site_name}: {exc}")  # WHY: report the failure.
        logging.error(  # WHY: action-log the failure.
            "Failed to configure auto-upgrade for site %s: %s", site_name, exc
        )
        return False  # WHY: count as failure.


def _perform_site_settings_update(
    site_name: str,
    site_id: str,
    settings: dict[str, Any],
    apisession: Any,
    dry_run: bool,
) -> None:
    """Perform the actual dry-run print or the mistapi settings update."""
    if dry_run:  # WHY: dry-run reports what it would do.
        print(f"    [DRY-RUN] {site_name}")  # WHY: report the would-apply.
        return  # WHY: no mutation in dry-run.
    logging.info("Updating auto-upgrade settings for site %s", site_name)  # WHY: action-log before the API mutation.
    import mistapi.api.v1.sites.setting as sites_setting_api  # WHY: lazy import.

    sites_setting_api.updateSiteSettings(apisession, site_id, body=settings)  # WHY: push the updated settings.
    logging.debug("Updated auto-upgrade settings for site %s", site_name)  # WHY: action-log after the API mutation.
    print(f"    [OK] {site_name}")  # WHY: report success.


def _print_final_summary(  # WHY: print the final single-org summary.
    successful: int,
    failed: int,
    dry_run: bool,
) -> None:
    """Print final summary after applying configuration."""
    print("\n" + "=" * 70)  # WHY: visual divider.
    print(f"  {'DRY-RUN COMPLETE' if dry_run else 'CONFIGURATION COMPLETE'}")  # WHY: title.
    print("=" * 70)  # WHY: visual divider.
    if dry_run:  # WHY: dry-run reports what it would do.
        print(f"    Would configure: {successful} site(s)")  # WHY: show would-configure count.
    else:
        print(f"    Successful: {successful} site(s)")  # WHY: show successful count.
    if failed > 0:  # WHY: only report failures when non-zero.
        print(f"    Failed: {failed} site(s)")  # WHY: show failed count.
    if dry_run:  # WHY: dry-run path tells operator how to apply.
        print("\n  >> To apply changes, run without --dry-run flag")  # WHY: apply hint.
    print("")  # WHY: spacer.


def _compute_msp_totals(  # WHY: compute MSP roll-up totals.
    results: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Compute total orgs, successful orgs, and total sites from results."""
    total_orgs = len(results)  # WHY: count orgs processed.
    successful_orgs = sum(1 for r in results if r["success"])  # WHY: count successful orgs.
    total_sites = sum(r["sites_configured"] for r in results)  # WHY: sum configured sites.
    return total_orgs, successful_orgs, total_sites  # WHY: return the totals.


def _print_msp_failed_orgs(results: list[dict[str, Any]]) -> None:  # WHY: list failed MSP orgs.
    """Print list of failed organizations from MSP results."""
    print("  Failed organizations:")  # WHY: failed-orgs header.
    for result in results:  # WHY: walk each result.
        if not result["success"]:  # WHY: only list failed orgs.
            print(f"    - {result['org_name']}")  # WHY: print the org name.
    print("")  # WHY: spacer.


def _print_msp_summary(  # WHY: print the MSP multi-org summary.
    results: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Print summary of MSP multi-org auto-upgrade configuration."""
    _print_msp_summary_header(dry_run)  # WHY: title + optional dry-run notice.
    total_orgs, successful_orgs, total_sites = _compute_msp_totals(results)  # WHY: roll-up totals.
    _print_msp_summary_totals(total_orgs, successful_orgs, total_sites, dry_run)  # WHY: print the totals block.
    if successful_orgs < total_orgs:  # WHY: some orgs failed - list them.
        _print_msp_failed_orgs(results)  # WHY: list the failed orgs.
    if dry_run:  # WHY: dry-run path tells operator how to apply.
        print("  >> To apply changes, run without --dry-run flag")  # WHY: apply hint.
    else:
        print("  Configuration complete.")  # WHY: report completion.


def _print_msp_summary_header(dry_run: bool) -> None:
    """Print the MSP summary banner + optional dry-run notice."""
    print("\n" + "=" * 70)  # WHY: visual divider.
    label = "MSP MULTI-ORG AUTO-UPGRADE SUMMARY"  # WHY: summary title.
    if dry_run:  # WHY: annotate dry-run in the title.
        label += " (DRY-RUN)"  # WHY: dry-run annotation.
    print(f"  {label}")  # WHY: print the title.
    print("=" * 70 + "\n")  # WHY: visual divider.
    if dry_run:  # WHY: warn dry-run made no changes.
        print("  >> DRY-RUN MODE: No actual changes were made <<\n")  # WHY: warn no changes.


def _print_msp_summary_totals(total_orgs: int, successful_orgs: int, total_sites: int, dry_run: bool) -> None:
    """Print the totals block of the MSP summary."""
    print(f"  Organizations processed: {total_orgs}")  # WHY: show orgs processed.
    if dry_run:  # WHY: dry-run reports would-configure counts.
        print(f"  Would configure: {successful_orgs} org(s)")  # WHY: would-configure orgs.
        print(f"  Total sites WOULD be configured: {total_sites}")  # WHY: would-configure sites.
    else:
        print(f"  Successful: {successful_orgs}")  # WHY: show successful orgs.
        print(f"  Total sites configured: {total_sites}")  # WHY: show configured sites.
    print("")  # WHY: spacer.


def _get_shared_schedule(  # WHY: prompt for shared MSP schedule.
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Get shared schedule settings for MSP mode."""
    day_of_week = _prompt_msp_day_of_week(safe_input_fn)  # WHY: prompt for day.
    if day_of_week is None:  # WHY: None means operator aborted at the prompt.
        return None  # WHY: abort with no schedule.
    print(f"    + Day: {day_of_week}\n")  # WHY: confirm the chosen day.
    time_of_day = _prompt_msp_time_of_day(safe_input_fn)  # WHY: prompt for time.
    if time_of_day is None:  # WHY: None means operator aborted at the prompt.
        return None  # WHY: abort with no schedule.
    print(f"    + Time: {time_of_day}")  # WHY: confirm the chosen time.
    return {"day_of_week": day_of_week, "time_of_day": time_of_day}  # WHY: return schedule.


_MSP_DAY_MAP: dict[str, str] = {  # WHY: input -> day-name map (numeric and named accepted).
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


def _print_msp_day_of_week_prompt() -> None:
    """Print the day-of-week prompt banner."""
    print("  Schedule Configuration:")  # WHY: schedule header.
    print("    When should auto-upgrades occur?\n")  # WHY: explain the prompt.
    print("    Day of week:")  # WHY: day-of-week header.
    print("      [1] any - Any day")  # WHY: any-day option.
    print("      [2] mon, tue, wed, thu, fri, sat, sun\n")  # WHY: weekday options.


def _prompt_msp_day_of_week(safe_input_fn: SafeInputFn) -> str | None:
    """Prompt operator for the shared MSP day-of-week (or None on abort)."""
    _print_msp_day_of_week_prompt()  # WHY: emit the banner via helper.
    try:
        day_input = (
            safe_input_fn("  Day of week [any]: ", "msp_schedule")  # WHY: read the day input via EOF-safe prompt.
            .strip()
            .lower()
            or "any"
        )
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        return None  # WHY: abort schedule.
    return _MSP_DAY_MAP.get(day_input, "any")  # WHY: resolve day via module-level map (default any).


def _prompt_msp_time_of_day(safe_input_fn: SafeInputFn) -> str | None:
    """Prompt operator for the shared MSP time-of-day (or None on abort)."""
    print("    Time of day (HH:MM in site's local timezone, or 'any'):")  # WHY: prompt intro.
    try:
        time_input = (
            safe_input_fn(  # WHY: read the time input via EOF-safe prompt.
                "  Time of day [02:00]: ", "msp_schedule"
            ).strip()
            or "02:00"
        )
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        return None  # WHY: abort schedule.
    return time_input if time_input.lower() != "any" else "any"  # WHY: normalize 'any' time.


def _get_shared_firmware_versions(  # WHY: pick shared versions from a reference org.
    apisession: Any,
    reference_org: dict[str, Any],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Fetch firmware versions from a reference org and let user select."""
    model_version_map = _fetch_reference_org_versions(apisession, reference_org)  # WHY: fetch versions.
    if model_version_map is None:  # WHY: None means the fetch failed.
        return {}  # WHY: empty dict = fall back to auto-detect.
    return _shared_versions_from_map(model_version_map, safe_input_fn)  # WHY: interactive select.


def _fetch_reference_org_versions(
    apisession: Any,
    reference_org: dict[str, Any],
) -> dict[str, list[dict[str, Any]]] | None:
    """Fetch and map versions from a reference org (None on any failure)."""
    org_id = reference_org.get("id")  # WHY: read the reference org id.
    org_name = reference_org.get("name", "Unknown")  # WHY: read the reference org name.
    if not org_id or apisession is None:  # WHY: guard missing prerequisites.
        print("  X Missing organization ID or API session")  # WHY: tell operator.
        return None  # WHY: signal failure.
    print(f"\n  Fetching available firmware versions from: {org_name}")  # WHY: announce fetch source.
    available_versions = _fetch_reference_org_version_list(apisession, str(org_id))  # WHY: API call.
    if available_versions is None:  # WHY: fetch failed (already logged).
        return None  # WHY: propagate failure.
    model_version_map = _build_version_map_from_list(available_versions)  # WHY: build map.
    if not model_version_map:  # WHY: no versions mapped.
        print("  X No AP firmware versions found")  # WHY: tell operator.
        return None  # WHY: signal failure.
    print(f"  + Found firmware for {len(model_version_map)} AP model(s)")  # WHY: confirm count.
    return model_version_map  # WHY: return the mapped versions.


def _fetch_reference_org_version_list(
    apisession: Any,
    org_id: str,
) -> list[Any] | None:
    """Call the mistapi listOrgAvailableDeviceVersions API. None on any failure."""
    try:
        import mistapi.api.v1.orgs.devices as org_devices_api  # WHY: lazy import.

        response = org_devices_api.listOrgAvailableDeviceVersions(  # WHY: list AP versions.
            apisession, org_id, type="ap"
        )
    except Exception as error:  # WHY: fetch may raise mistapi errors - treat as failure.
        print(f"  X Error fetching firmware versions: {error}")  # WHY: tell operator.
        return None  # WHY: signal failure.
    if not response or not hasattr(response, "data"):  # WHY: guard empty response.
        print("  X Failed to fetch available firmware versions")  # WHY: tell operator.
        return None  # WHY: signal failure.
    return response.data if isinstance(response.data, list) else []  # WHY: normalize to list.


def _shared_versions_from_map(
    model_version_map: dict[str, list[dict[str, Any]]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Group the model_version_map into families and prompt interactively."""
    model_families = _group_models_for_msp(model_version_map)  # WHY: group models into families.
    return _select_versions_interactively(  # WHY: interactive per-family selection.
        model_families, model_version_map, safe_input_fn
    )


def _build_version_map_from_list(  # WHY: build a model->versions map from a list.
    available_versions: list[Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build model -> versions map from API response."""
    result: dict[str, list[dict[str, Any]]] = {}  # WHY: result map.
    for entry in available_versions:  # WHY: walk each version record.
        if not _is_valid_version_entry(entry):  # WHY: skip malformed records.
            continue  # WHY: continue to next.
        model = entry.get("model")  # WHY: pull the model.
        tag = entry.get("tag", "")  # WHY: pull the release tag.
        result.setdefault(model, []).append(  # WHY: append the version+tag record.
            {"version": entry.get("version"), "tag": tag}
        )
    return result  # WHY: return the map.


def _is_valid_version_entry(entry: Any) -> bool:
    """Predicate - True when the entry is a dict with both model and version."""
    if not isinstance(entry, dict):  # WHY: skip non-dict entries.
        return False  # WHY: malformed record.
    return bool(entry.get("model") and entry.get("version"))  # WHY: require both fields.


def _group_models_for_msp(  # WHY: group MSP models into families.
    model_version_map: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    """Group models by family for MSP firmware selection."""
    model_families: dict[str, list[str]] = {}  # WHY: family -> models map.
    for model in sorted(model_version_map.keys()):  # WHY: sorted order for stable output.
        family = model.rstrip("EP")  # WHY: strip E/P suffixes to get the family.
        model_families.setdefault(family, []).append(model)  # WHY: append model to family.
    return model_families  # WHY: return the family map.


def _collect_family_versions(  # WHY: collect a family's distinct versions+tags.
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
) -> list[tuple[str, str]]:
    """Collect and sort unique versions for a model family."""
    family_versions: set[tuple[str, str]] = set()  # WHY: distinct (version, tag) pairs.
    for model in models:  # WHY: walk the family's models.
        for v_info in model_version_map.get(model, []):  # WHY: walk each model's versions.
            family_versions.add((v_info["version"], v_info.get("tag", "")))  # WHY: record the version and tag.
    return sorted(list(family_versions), key=lambda x: x[0], reverse=True)  # WHY: newest-first.


def _display_msp_family_versions(  # WHY: display an MSP family's version choices.
    family: str,
    models: list[str],
    sorted_versions: list[tuple[str, str]],
) -> None:
    """Display available firmware versions for a model family."""
    print(f"\n  {family} family ({', '.join(models)}):")  # WHY: family header with members.
    for idx, (version, tag) in enumerate(sorted_versions, 1):  # WHY: 1-based enumeration.
        tag_display = f" [{tag}]" if tag else ""  # WHY: show release tag if present.
        print(f"    [{idx:>2}] {version}{tag_display}")  # WHY: print the numbered version.
    print("    [Enter] Skip this family")  # WHY: offer to skip on Enter.


def _apply_version_to_models(  # WHY: apply chosen version to a family's models.
    selected_version: str,
    family: str,
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
    custom_versions: dict[str, str],
) -> None:
    """Apply a selected version to all compatible models in a family."""
    for model in models:  # WHY: walk the family's models.
        model_versions = [  # WHY: extract per-model version strings for compatibility check.
            v["version"] for v in model_version_map.get(model, [])
        ]
        if selected_version in model_versions:  # WHY: version is valid for this model.
            custom_versions[model] = selected_version  # WHY: record the model's version.
    print(f"    + Set {family} family to {selected_version}")  # WHY: confirm selection.


def _process_family_choice(  # WHY: per-family prompt-and-apply used by interactive loop.
    family: str,
    models: list[str],
    model_version_map: dict[str, list[dict[str, Any]]],
    safe_input_fn: SafeInputFn,
    custom_versions: dict[str, str],
) -> bool:
    """Prompt for and apply a single family's version choice. Returns False on cancel."""
    sorted_versions = _collect_family_versions(models, model_version_map)  # WHY: collect versions.
    if not sorted_versions:  # WHY: skip families with no versions.
        return True  # WHY: continue outer loop.
    _display_msp_family_versions(family, models, sorted_versions)  # WHY: show choices.
    choice = _prompt_family_version_choice(safe_input_fn, len(sorted_versions))  # WHY: read choice.
    if choice is None:  # WHY: operator cancelled ('q' or EOF).
        return False  # WHY: signal cancel to caller.
    family_ctx = _MspFamilyChoiceContext(  # WHY: bundle context to stay under 5-param limit.
        family=family,
        models=models,
        sorted_versions=sorted_versions,
        model_version_map=model_version_map,
    )
    _dispatch_family_choice(choice, family_ctx, custom_versions)  # WHY: commit operator's choice.
    return True  # WHY: successful family handling.


def _select_versions_interactively(  # WHY: interactively select versions per family.
    model_families: dict[str, list[str]],
    model_version_map: dict[str, list[dict[str, Any]]],
    safe_input_fn: SafeInputFn,
) -> dict[str, str] | None:
    """Interactively select firmware versions per model family."""
    print("\n  Select firmware version for each AP model family.")  # WHY: explain selection.
    print("  Press Enter to skip a family (won't be configured).")  # WHY: Enter skips.
    print("  Enter 'q' to cancel selection.")  # WHY: 'q' cancels.
    custom_versions: dict[str, str] = {}  # WHY: operator-chosen versions.
    for family, models in sorted(model_families.items()):  # WHY: walk families in order.
        if not _process_family_choice(  # WHY: delegate per-family handling.
            family, models, model_version_map, safe_input_fn, custom_versions
        ):
            return None  # WHY: abort selection on cancel signal.
    return custom_versions  # WHY: return the selected versions.


def _prompt_family_version_choice(safe_input_fn: SafeInputFn, num_versions: int) -> str | None:
    """Prompt for a family version choice. None on 'q' or EOF."""
    try:
        raw = safe_input_fn(  # WHY: read the numeric choice via EOF-safe prompt.
            f"  Select version (1-{num_versions}): ", "msp_firmware_select"
        )
        choice = str(raw).strip()  # WHY: coerce Any return of injected fn to str.
    except SystemExit:  # WHY: safe_input raises SystemExit on EOF.
        return None  # WHY: abort selection.
    if choice.lower() == "q":  # WHY: 'q' cancels the whole selection.
        return None  # WHY: signal cancel.
    return choice  # WHY: return the raw choice string.


def _dispatch_family_choice(
    choice: str,
    ctx: _MspFamilyChoiceContext,
    custom_versions: dict[str, str],
) -> None:
    """Interpret a family version choice and apply it (or skip on empty)."""
    if not (choice and choice.isdigit()):  # WHY: empty or non-numeric means skip family.
        print(f"    - Skipped {ctx.family} family")  # WHY: tell operator we skipped.
        return  # WHY: skip this family.
    idx = int(choice) - 1  # WHY: 1-based display to 0-based list index.
    if not 0 <= idx < len(ctx.sorted_versions):  # WHY: guard against out-of-range indices.
        print(f"    - Invalid selection, skipped {ctx.family}")  # WHY: out-of-range - skip family.
        return  # WHY: skip family on invalid selection.
    _apply_version_to_models(  # WHY: apply the chosen version to every model in the family.
        ctx.sorted_versions[idx][0], ctx.family, ctx.models, ctx.model_version_map, custom_versions
    )


def _display_msp_pre_apply_summary(  # WHY: print MSP pre-apply summary.
    shared_schedule: dict[str, str],
    shared_versions: dict[str, str] | None,
    selected_orgs: list[dict[str, Any]],
) -> None:
    """Display summary before MSP configuration application."""
    print("\n  Configuration to apply:")  # WHY: summary header.
    print(f"    - Day of week: {shared_schedule.get('day_of_week', 'any')}.")  # WHY: show day.
    time_display = shared_schedule.get("time_of_day", "02:00")  # WHY: resolve display time.
    print(f"    - Time of day: {time_display} (site's local timezone)")  # WHY: show time.
    if shared_versions:  # WHY: manually-selected versions present.
        print(f"    - Firmware: Manually selected ({len(shared_versions)} models)")  # WHY: show manual-selection count.
        for model, version in sorted(shared_versions.items()):  # WHY: list each pair.
            print(f"        {model}: {version}")  # WHY: print the pair.
    else:
        print("    - Firmware: Latest stable per model (auto-detected)")  # WHY: auto-detect note.
    print(f"    - Organizations: {len(selected_orgs)}\n")  # WHY: show org count.
