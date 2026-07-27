"""Bulk switch firmware upgrade operations for Mist organizations.

Executes firmware upgrades on switches across selected sites with safety
checks, multiple upgrade strategies, and comprehensive progress tracking.
Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines

from __future__ import annotations  # WHY: enable PEP 604 union types on Python 3.9+.

import csv  # WHY: needed for CSV read/write of firmware cache.
import logging  # WHY: structured logging of upgrade workflow steps.
import os  # WHY: filesystem checks and path joining for cache file.
from datetime import datetime  # WHY: timestamps for operation IDs and freshness checks.
from typing import Any  # WHY: Mist API returns loosely typed dicts.

# ---------------------------------------------------------------------------
# Module-level constants (magic values extracted for clarity/testability)
# ---------------------------------------------------------------------------
STRATEGY_BIG_BANG = "big_bang"  # WHY: simultaneous upgrade of every switch.
STRATEGY_SERIAL = "serial"  # WHY: sequential per-switch upgrade for safety.
STRATEGY_CANARY = "canary"  # WHY: test-subset-first rollout strategy.
CONFIRM_PHRASE = "UPGRADE SWITCHES"  # WHY: exact phrase required to arm destructive action.
HTTP_OK = 200  # WHY: standard HTTP success code for GET responses.
HTTP_ACCEPTED = 202  # WHY: async job accepted by Mist upgrade API.
SECONDS_PER_HOUR = 3600  # WHY: divisor when computing cache file age in hours.
MODEL_STR_MAX = 32  # WHY: fixed-width column budget for compatible-models cell.
MODEL_STR_TRUNC = 29  # WHY: leave room for ellipsis in truncated models cell.
ELLIPSIS = "..."  # WHY: suffix appended to truncated model listings.
CACHE_DIR = "data"  # WHY: relative directory that holds cached firmware CSV.
CACHE_FILENAME = "cached_org_devices_versions_switch.csv"  # WHY: fixed cache filename.
YES_ANSWERS = ("y", "yes")  # WHY: canonical affirmatives for manual entry prompt.
VALID_CHOICES_A_S_C = ("A", "S", "C")  # WHY: allowed inputs for site scope selection.
STATUS_UPGRADE_OK = (HTTP_OK, HTTP_ACCEPTED)  # WHY: acceptable upgrade API responses.


class BulkSwitchFirmwareUpgrader:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Execute firmware upgrades on switches across selected sites.

    Supports multiple upgrade strategies (big_bang, serial, canary) with
    comprehensive progress tracking, firmware caching, and model
    compatibility validation.

    NETWORK IMPACT WARNING:
    - Switch reboots will disrupt network connectivity
    - Plan maintenance windows for production environments
    - Verify backup connectivity paths before execution
    """

    # WHY: relative path so tests can override. Kept as class attr for compatibility.
    CACHE_FILE = os.path.join(CACHE_DIR, CACHE_FILENAME)
    CACHE_FRESHNESS_HOURS = 24  # WHY: reuse cached firmware list if newer than one day.

    def __init__(
        self,
        org_id: str,
        apisession: Any,
        safe_input_fn: Any,
        sites_override: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the switch firmware upgrader."""
        self.org_id = org_id  # WHY: Mist organization identifier used by every API call.
        self.apisession = apisession  # WHY: authenticated Mist API session dependency.
        self.safe_input_fn = safe_input_fn  # WHY: injected EOF-safe input collector.
        self.sites_override = sites_override  # WHY: caller-supplied sites for template mode.
        self.logger = logging.getLogger(__name__)  # WHY: per-module logger for traceability.
        self._init_org_state()  # WHY: seed organization-level attributes for later fill.
        self._init_inventory_state()  # WHY: seed inventory attributes populated during discovery.
        self._init_upgrade_params()  # WHY: seed upgrade-parameter attributes with defaults.
        self.upgrade_results: dict[str, Any] = {}  # WHY: aggregate result container for callers.

    def _init_org_state(self) -> None:
        """Seed organization-scope attributes to safe defaults."""
        self.org_name: str = ""  # WHY: populated after successful validation.
        self.selected_sites: list[dict[str, Any]] = []  # WHY: filled by site-selection step.

    def _init_inventory_state(self) -> None:
        """Seed inventory-related attributes populated during discovery."""
        self.switch_models: set[str] = set()  # WHY: distinct switch models present in inventory.
        self.current_firmware_versions: set[str] = set()  # WHY: firmware versions already running.
        self.available_versions: list[str] = []  # WHY: candidate firmware versions after filter.
        self.compatible_versions: dict[str, set[str]] = {}  # WHY: version -> compatible models map.
        self.target_version: str = ""  # WHY: user-selected firmware version target.

    def _init_upgrade_params(self) -> None:
        """Seed upgrade-parameter attributes with default choices."""
        self.upgrade_strategy: str = ""  # WHY: rollout style selected by operator.
        self.force_upgrade: bool = False  # WHY: default matches production safe path.
        self.auto_reboot: bool = True  # WHY: reboot needed for switch firmware to activate.
        self.take_snapshot: bool = True  # WHY: recovery snapshot on Junos is default best-practice.

    # --------------------------------------------------------------------- #
    # Public entry point
    # --------------------------------------------------------------------- #

    def execute(self) -> dict[str, Any]:
        """Orchestrate the complete upgrade workflow."""
        self.logger.debug(  # WHY: mark workflow start for post-mortem log review.
            "Starting bulk switch firmware upgrade - org_id: %s",
            self.org_id,
        )
        if not self._validate_organization():  # WHY: abort early on org access failure.
            return {"error": "Organization validation failed"}  # WHY: caller-friendly error dict.
        site_result = self._select_sites()  # WHY: attempt site scoping (interactive or override).
        if site_result:  # WHY: non-None means selection step returned an early exit/error.
            return site_result  # WHY: propagate selection outcome to caller.
        return self._run_post_site_workflow()  # WHY: complete parameter/firmware/exec stages.

    def _run_post_site_workflow(self) -> dict[str, Any]:
        """Run the workflow stages that follow site selection."""
        if not self._configure_upgrade_parameters():  # WHY: bail on cancellation of params dialog.
            return {"cancelled": True}  # WHY: signal user cancellation to caller.
        firmware_result = self._discover_and_select_firmware()  # WHY: inventory + version choice.
        if firmware_result:  # WHY: any non-None value indicates firmware step short-circuited.
            return firmware_result  # WHY: propagate firmware step outcome.
        if not self._confirm_upgrade():  # WHY: enforce explicit high-risk confirmation phrase.
            return {"cancelled": True}  # WHY: user declined the destructive action.
        return self._execute_upgrades()  # WHY: dispatch the actual upgrade jobs.

    # --------------------------------------------------------------------- #
    # Step 1: Organization Validation
    # --------------------------------------------------------------------- #

    def _validate_organization(self) -> bool:
        """Validate organization access and retrieve org name."""
        import mistapi  # pylint: disable=import-outside-toplevel

        print("\n-> Validating organization access...")  # WHY: keep operator aware of progress.
        try:  # WHY: guard against network / auth failures from mistapi.
            org_info = mistapi.api.v1.orgs.orgs.getOrg(self.apisession, self.org_id)  # WHY: fetch org record.
            return self._process_org_response(org_info)  # WHY: split branching into helper for CC.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"X  Error validating organization: {exc}")  # WHY: surface exception to console.
            self.logger.error("Organization validation failed: %s", exc)  # WHY: log root cause.
            return False  # WHY: failed validation blocks the workflow.

    def _process_org_response(self, org_info: Any) -> bool:
        """Interpret the org lookup response and record the org name."""
        if org_info.status_code != HTTP_OK:  # WHY: only 200 indicates a valid org record.
            print(f"X  Error accessing organization: {org_info.status_code}")  # WHY: user-visible.
            self.logger.error(  # WHY: log HTTP status for debugging.
                "Failed to access organization %s: %s",
                self.org_id,
                org_info.status_code,
            )
            return False  # WHY: cannot proceed without a valid org.
        self.org_name = org_info.data.get("name", "Unknown")  # WHY: display friendly org name.
        print(f"!? Organization: {self.org_name}")  # WHY: confirm discovered org to operator.
        self.logger.debug("Organization validated: %s", self.org_name)  # WHY: trace success.
        return True  # WHY: green-light the next workflow step.

    # --------------------------------------------------------------------- #
    # Step 2: Site Selection
    # --------------------------------------------------------------------- #

    def _select_sites(self) -> dict[str, Any] | None:
        """Select sites for upgrade via override or interactive picker."""
        if self.sites_override:  # WHY: template-driven callers pre-supply the site set.
            return self._use_override_sites()  # WHY: skip interactive discovery.
        return self._interactive_site_selection()  # WHY: fall back to discover + prompt.

    def _use_override_sites(self) -> dict[str, Any] | None:
        """Use provided site list from template-based upgrade."""
        self.selected_sites = self.sites_override if self.sites_override else []  # WHY: mypy narrow.
        print(f"-> Using provided site list: {len(self.selected_sites)} sites")  # WHY: operator note.
        return None  # pylint: disable=useless-return  # WHY: contract returns None on success.

    def _interactive_site_selection(self) -> dict[str, Any] | None:
        """Interactive site selection with discovery."""
        import mistapi  # pylint: disable=import-outside-toplevel

        print("\n-> Discovering available sites...")  # WHY: cue operator that API call is starting.
        try:  # WHY: shield against transient API failures.
            sites_response = mistapi.api.v1.orgs.sites.listOrgSites(
                self.apisession, self.org_id
            )  # WHY: fetch all sites.
            if sites_response.status_code != HTTP_OK:  # WHY: any non-200 halts selection.
                print(f"X  Error retrieving sites: {sites_response.status_code}")  # WHY: user-facing.
                return {"error": "Failed to retrieve sites"}  # WHY: structured error for caller.
            all_sites = sites_response.data  # WHY: API returns raw list of site dicts.
            print(f"!? Found {len(all_sites)} total sites")  # WHY: give operator scope preview.
            return self._prompt_site_selection(all_sites)  # WHY: delegate menu handling.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"X  Error during site discovery: {exc}")  # WHY: surface failure to console.
            self.logger.error("Site discovery failed: %s", exc)  # WHY: trace for debugging.
            return {"error": f"Site discovery error: {exc}"}  # WHY: caller sees precise error.

    def _prompt_site_selection(self, all_sites: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Display site list and get user selection."""
        self._display_site_list(all_sites)  # WHY: show numbered options before prompting.
        site_choice = self._read_site_menu_choice()  # WHY: get validated menu letter from user.
        result = self._apply_site_menu_choice(site_choice, all_sites)  # WHY: dispatch by choice.
        if result is not None:  # WHY: propagate cancel/error result if dispatch produced one.
            return result  # WHY: caller expects short-circuit on error/cancel.
        if not self.selected_sites:  # WHY: reject empty selections.
            print("X  No sites selected")  # WHY: operator feedback.
            return {"error": "No sites selected"}  # WHY: structured error result.
        return None  # WHY: success path returns None per contract.

    def _read_site_menu_choice(self) -> str:
        """Prompt the site scope menu and return the normalized upper letter."""
        # WHY: single-line prompt with uppercase normalization for switch handling.
        raw_choice = self.safe_input_fn(
            "\nEnter your choice (A/S/C): ", context="bulk_switch_scope"
        )  # WHY: safe prompt.
        return str(raw_choice).upper()  # WHY: coerce to str for typing then normalize case.

    def _apply_site_menu_choice(
        self,
        site_choice: str,
        all_sites: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Apply the menu choice to `selected_sites` or return an early result."""
        if site_choice == "C":  # WHY: cancellation path.
            print("-> Operation cancelled by user")  # WHY: acknowledge cancel to user.
            return {"cancelled": True}  # WHY: signal cancel to caller.
        if site_choice == "A":  # WHY: select-all path.
            self.selected_sites = all_sites  # WHY: no filtering needed.
            print(f"-> Selected all {len(self.selected_sites)} sites")  # WHY: confirmation.
            return None  # WHY: continue with populated selection.
        if site_choice == "S":  # WHY: prompt for specific site numbers/ranges.
            return self._parse_specific_sites(all_sites)  # WHY: delegate parsing.
        print("X  Invalid selection")  # WHY: unknown option feedback.
        return {"error": "Invalid selection"}  # WHY: caller sees explicit error.

    @staticmethod
    def _display_site_list(sites: list[dict[str, Any]]) -> None:
        """Display numbered list of available sites."""
        print("\nAvailable sites:")  # WHY: header row above list.
        for index, site in enumerate(sites, 1):  # WHY: 1-based numbering matches menu prompt.
            site_name = site.get("name", "Unnamed")  # WHY: guard missing name field.
            site_id = site.get("id", "Unknown")  # WHY: guard missing id field.
            print(f"{index:3}. {site_name} (ID: {site_id})")  # WHY: aligned table for readability.

    def _parse_specific_sites(self, all_sites: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Parse user input for specific site selection."""
        print("\nEnter site numbers (comma-separated) or ranges (e.g., 1-5):")  # WHY: user hint.
        # WHY: EOF-safe site-list entry via injected input helper.
        site_input = self.safe_input_fn("Sites: ", context="bulk_switch_site_list")
        try:  # WHY: any parse error must degrade gracefully.
            self.selected_sites = self._resolve_site_tokens(site_input, all_sites)  # WHY: pure helper.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"X  Invalid site selection: {exc}")  # WHY: user sees exact parse failure.
            return {"error": "Invalid site selection"}  # WHY: caller-visible error.
        print(f"-> Selected {len(self.selected_sites)} sites")  # WHY: echo selection count.
        if not self.selected_sites:  # WHY: reject empty parse result.
            print("X  No valid sites selected")  # WHY: user feedback.
            return {"error": "No valid sites selected"}  # WHY: caller-visible error.
        return None  # WHY: success path returns None.

    def _resolve_site_tokens(
        self,
        site_input: str,
        all_sites: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert comma-separated tokens into a concrete site list."""
        selected: list[dict[str, Any]] = []  # WHY: accumulator for parsed selections.
        for raw_token in site_input.split(","):  # WHY: comma separates independent tokens.
            token = raw_token.strip()  # WHY: tolerate spaces around commas.
            self._append_token_sites(token, all_sites, selected)  # WHY: single-token dispatch.
        return selected  # WHY: caller assigns to selected_sites.

    def _append_token_sites(
        self,
        token: str,
        all_sites: list[dict[str, Any]],
        selected: list[dict[str, Any]],
    ) -> None:
        """Append the sites referenced by a single token (range or index)."""
        if "-" in token:  # WHY: token like '1-5' is a range.
            self._append_range(token, all_sites, selected)  # WHY: delegate range handling.
            return  # WHY: single-responsibility exit.
        self._append_single(token, all_sites, selected)  # WHY: otherwise treat as single index.

    @staticmethod
    def _append_range(
        token: str,
        all_sites: list[dict[str, Any]],
        selected: list[dict[str, Any]],
    ) -> None:
        """Append sites for a 1-based inclusive range token like '3-7'."""
        start, end = map(int, token.split("-"))  # WHY: raise ValueError on non-numeric to caller.
        for device_index in range(start - 1, end):  # WHY: convert 1-based to 0-based slice.
            if 0 <= device_index < len(all_sites):  # WHY: silently skip out-of-range endpoints.
                selected.append(all_sites[device_index])  # WHY: accumulate the site dict.

    @staticmethod
    def _append_single(
        token: str,
        all_sites: list[dict[str, Any]],
        selected: list[dict[str, Any]],
    ) -> None:
        """Append the site referenced by a single 1-based index token."""
        index = int(token) - 1  # WHY: convert user-facing 1-based index to 0-based.
        if 0 <= index < len(all_sites):  # WHY: silently drop indices that do not exist.
            selected.append(all_sites[index])  # WHY: accumulate site dict.

    # --------------------------------------------------------------------- #
    # Step 3: Upgrade Parameters Configuration
    # --------------------------------------------------------------------- #

    def _configure_upgrade_parameters(self) -> bool:
        """Configure all upgrade parameters interactively."""
        print(f"\n{'=' * 60}")  # WHY: visual separator prior to parameter menus.
        print("SWITCH FIRMWARE UPGRADE PARAMETER CONFIGURATION")  # WHY: section header.
        print(f"{'=' * 60}")  # WHY: bottom border to match top.
        self._select_strategy()  # WHY: chooses rollout style.
        self._select_force_option()  # WHY: choose whether to bypass same-version check.
        self._select_reboot_option()  # WHY: reboot decision affects activation.
        self._select_snapshot_option()  # WHY: Junos snapshot preference.
        return True  # WHY: contract signals successful parameter capture.

    def _select_strategy(self) -> None:
        """Select upgrade strategy (big_bang, serial, canary)."""
        print("\nUpgrade Strategy Options:")  # WHY: menu heading.
        print("1. big_bang    - Upgrade all switches simultaneously (fastest)")  # WHY: option 1.
        print("2. serial      - Upgrade switches one by one (safest)")  # WHY: option 2.
        print("3. canary      - Test subset first, then upgrade remaining")  # WHY: option 3.
        while True:  # WHY: reprompt until a valid choice is entered.
            # WHY: EOF-safe strategy prompt through injected input helper.
            strategy_choice = self.safe_input_fn("\nSelect upgrade strategy (1-3): ", context="bulk_switch_strategy")
            resolved = self._resolve_strategy_choice(strategy_choice)  # WHY: single-branch mapping.
            if resolved is not None:  # WHY: None means invalid. Loop again.
                self.upgrade_strategy = resolved  # WHY: commit valid strategy.
                break  # WHY: exit prompt loop.
            print("X  Please enter 1, 2, or 3")  # WHY: invalid input feedback.
        print(f"-> Selected strategy: {self.upgrade_strategy}")  # WHY: echo selection.

    @staticmethod
    def _resolve_strategy_choice(strategy_choice: str) -> str | None:
        """Return the strategy constant for a menu selection, or None if invalid."""
        # WHY: dict lookup keeps CC low and is easy to extend later.
        mapping = {"1": STRATEGY_BIG_BANG, "2": STRATEGY_SERIAL, "3": STRATEGY_CANARY}
        return mapping.get(strategy_choice)  # WHY: None signals invalid input.

    def _select_force_option(self) -> None:
        """Select force upgrade option."""
        print("\nForce Upgrade Options:")  # WHY: menu heading.
        print("1. Yes - Force upgrade even if same version (recommended for testing)")  # WHY: option 1.
        print("2. No  - Skip devices already on target version (recommended for production)")  # WHY: option 2.
        while True:  # WHY: reprompt loop.
            # WHY: EOF-safe boolean-style prompt via injected helper.
            force_choice = self.safe_input_fn("\nForce upgrade? (1-2): ", context="bulk_switch_force")
            if force_choice in ("1", "2"):  # WHY: only two acceptable inputs.
                self.force_upgrade = force_choice == "1"  # WHY: map '1' to True, '2' to False.
                break  # WHY: exit prompt loop.
            print("X  Please enter 1 or 2")  # WHY: invalid input feedback.
        label = "Yes" if self.force_upgrade else "No"  # WHY: human-readable summary.
        print(f"-> Force upgrade: {label}")  # WHY: echo selection.

    def _select_reboot_option(self) -> None:
        """Select auto-reboot option."""
        print("\nReboot Options:")  # WHY: menu heading.
        print("1. Yes - Reboot after upgrade (required for switches - recommended)")  # WHY: option 1.
        print("2. No  - No reboot (not recommended for switches)")  # WHY: option 2.
        while True:  # WHY: reprompt loop.
            reboot_choice = self.safe_input_fn(
                "\nReboot after upgrade? (1-2): ", context="bulk_switch_reboot"
            )  # WHY: prompt.
            if reboot_choice in ("1", "2"):  # WHY: constrain to menu options.
                self.auto_reboot = reboot_choice == "1"  # WHY: True for reboot, False otherwise.
                if not self.auto_reboot:  # WHY: emphasize danger of no-reboot mode.
                    print("!? WARNING: Switches typically require reboot to complete firmware upgrade")
                break  # WHY: exit prompt loop.
            print("X  Please enter 1 or 2")  # WHY: invalid input feedback.
        label = "Yes" if self.auto_reboot else "No"  # WHY: echo helper.
        print(f"-> Auto reboot: {label}")  # WHY: echo selection.

    def _select_snapshot_option(self) -> None:
        """Select recovery snapshot option (Junos specific)."""
        print("\nRecovery Snapshot Options (Junos devices only):")  # WHY: menu heading.
        print("1. Yes - Take recovery snapshot after device reboots (recommended for Junos)")  # WHY: option 1.
        print("2. No  - Skip recovery snapshot (faster but no post-upgrade backup)")  # WHY: option 2.
        while True:  # WHY: reprompt loop.
            snapshot_choice = self.safe_input_fn(  # WHY: EOF-safe injected prompt helper.
                "\nTake recovery snapshot after reboot? (1-2): ",
                context="bulk_switch_snap",
            )
            if snapshot_choice in ("1", "2"):  # WHY: menu constraint.
                self.take_snapshot = snapshot_choice == "1"  # WHY: True for snapshot, False otherwise.
                break  # WHY: exit prompt loop.
            print("X  Please enter 1 or 2")  # WHY: invalid input feedback.
        label = "Yes" if self.take_snapshot else "No"  # WHY: echo helper.
        print(f"-> Recovery snapshot after reboot: {label}")  # WHY: echo selection.

    # --------------------------------------------------------------------- #
    # Step 4: Firmware Discovery and Selection
    # --------------------------------------------------------------------- #

    def _discover_and_select_firmware(self) -> dict[str, Any] | None:
        """Discover available firmware and get user selection."""
        print(f"\n{'=' * 60}")  # WHY: visual separator before firmware section.
        print("FIRMWARE VERSION SELECTION")  # WHY: section header.
        print(f"{'=' * 60}")  # WHY: closing border.
        if not self._fetch_switch_inventory():  # WHY: inventory drives model compatibility filter.
            return {"error": "Failed to retrieve switch inventory"}  # WHY: caller-visible error.
        firmware_data = self._load_firmware_data()  # WHY: cached or live firmware list.
        if not firmware_data:  # WHY: nothing to select from.
            return {"error": "No firmware data available"}  # WHY: caller-visible error.
        self._process_firmware_data(firmware_data)  # WHY: filter and sort into available_versions.
        return self._get_version_selection()  # WHY: prompt user for version choice.

    def _fetch_switch_inventory(self) -> bool:
        """Fetch switch inventory to determine current firmware and models."""
        print("\n-> Discovering available switch firmware versions...")  # WHY: progress cue.
        try:  # WHY: guard against transient inventory API failures.
            switches = self._call_inventory_api()  # WHY: fetch inventory list from Mist.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"X  Error fetching switch inventory: {exc}")  # WHY: user-visible failure.
            self.logger.error("Switch inventory fetch failed: %s", exc)  # WHY: log root cause.
            return False  # WHY: cannot proceed without inventory.
        if switches is None:  # WHY: None signals API-level failure with printed reason.
            return False  # WHY: propagate failure upward.
        if not switches:  # WHY: empty inventory means nothing to upgrade.
            print("X  No switches found in organization")  # WHY: user-visible outcome.
            return False  # WHY: block workflow.
        print(f"!? Found {len(switches)} switches")  # WHY: confirm switch count discovered.
        self._populate_inventory_state(switches)  # WHY: fill model / version sets.
        self._report_inventory_findings()  # WHY: echo findings and warn if models missing.
        return True  # WHY: inventory step succeeded.

    def _call_inventory_api(self) -> list[dict[str, Any]] | None:
        """Call the org inventory API and return the switch list or None on HTTP error."""
        import mistapi  # pylint: disable=import-outside-toplevel

        switches_response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: fetch switches only.
            self.apisession,
            self.org_id,
            type="switch",
        )
        if switches_response.status_code != HTTP_OK:  # WHY: only 200 responses are usable.
            print(f"X  Error retrieving switch inventory: {switches_response.status_code}")  # WHY: user note.
            return None  # WHY: caller distinguishes None (HTTP error) from [] (empty inv).
        return list(switches_response.data)  # WHY: return list of switch dicts.

    def _populate_inventory_state(self, switches: list[dict[str, Any]]) -> None:
        """Populate switch_models and current_firmware_versions from inventory."""
        for switch in switches:  # WHY: single pass over inventory.
            version = switch.get("version")  # WHY: extract version once for narrowing.
            if version:  # WHY: skip entries lacking a version field.
                self.current_firmware_versions.add(str(version))  # WHY: accumulate versions as str.
            model = switch.get("model")  # WHY: extract model once for narrowing.
            if model:  # WHY: skip entries lacking a model field.
                self.switch_models.add(str(model))  # WHY: accumulate distinct models as str.

    def _report_inventory_findings(self) -> None:
        """Echo discovered models/versions and warn when models missing."""
        print(f"-> Switch models found: {', '.join(sorted(self.switch_models))}")  # WHY: echo models.
        # WHY: echo currently-running firmware versions for context.
        print(f"-> Current firmware versions: {', '.join(sorted(self.current_firmware_versions))}")
        if not self.switch_models:  # WHY: missing models degrades compatibility filter.
            print("!? WARNING: No switch models detected - firmware filtering may not work properly")
            self.logger.warning("No switch models found in inventory")  # WHY: keep an audit trail.

    # --------------------------------------------------------------------- #
    # Firmware data loading (cache / API)
    # --------------------------------------------------------------------- #

    def _load_firmware_data(self) -> list[dict[str, Any]]:
        """Load firmware data from cache or API."""
        print("\n-> Checking for cached firmware versions...")  # WHY: progress cue.
        cached_data = self._load_from_cache()  # WHY: prefer fresh cache to avoid API load.
        if cached_data:  # WHY: fresh cache returns list. Stale/missing returns None.
            return cached_data  # WHY: short-circuit with cached firmware list.
        return self._fetch_firmware_from_api()  # WHY: fall back to live API.

    def _load_from_cache(self) -> list[dict[str, Any]] | None:
        """Load firmware data from cache file if fresh."""
        if not os.path.exists(self.CACHE_FILE):  # WHY: no cache file means nothing to load.
            print("-> No cache file found, will query API")  # WHY: user note.
            self.logger.info("No cached firmware data found")  # WHY: audit log.
            return None  # WHY: signal caller to hit API.
        try:  # WHY: any IO error must fall back to API.
            return self._maybe_read_cache()  # WHY: encapsulate freshness+size checks.
        except Exception as cache_error:  # pylint: disable=broad-exception-caught
            self.logger.warning("Error reading cache file: %s", cache_error)  # WHY: audit failure.
            print("-> Cache file unreadable, will query API")  # WHY: user note.
            return None  # WHY: signal fallback to API.

    def _maybe_read_cache(self) -> list[dict[str, Any]] | None:
        """Return cache contents if the file is fresh and non-empty."""
        # WHY: age in hours drives freshness comparison against configured window.
        file_age_hours = (datetime.now().timestamp() - os.path.getmtime(self.CACHE_FILE)) / SECONDS_PER_HOUR
        if file_age_hours >= self.CACHE_FRESHNESS_HOURS:  # WHY: skip stale cache.
            print(f"-> Cache file exists but is stale ({file_age_hours:.1f} hours old)")  # WHY: user note.
            self.logger.info("Cache file stale, will refresh from API")  # WHY: audit.
            return None  # WHY: signal API refresh.
        if os.path.getsize(self.CACHE_FILE) == 0:  # WHY: empty file is unusable.
            print("-> Cache file exists but is empty, will query API")  # WHY: user note.
            self.logger.info("Cache file is empty, will refresh from API")  # WHY: audit.
            return None  # WHY: signal API refresh.
        print(f"!? Found fresh cached firmware data ({file_age_hours:.1f} hours old)")  # WHY: user note.
        self.logger.info("Using cached firmware data (age: %.1f hours)", file_age_hours)  # WHY: audit.
        return self._read_cache_file()  # WHY: parse and return CSV rows.

    def _read_cache_file(self) -> list[dict[str, Any]]:
        """Read and parse cache file contents."""
        firmware_data: list[dict[str, Any]] = []  # WHY: accumulator for row dicts.
        with open(self.CACHE_FILE, newline="", encoding="utf-8") as csvfile:  # WHY: safe csv open.
            reader = csv.DictReader(csvfile)  # WHY: rely on header row for field names.
            for row in reader:  # WHY: linear scan of CSV rows.
                firmware_data.append(self._row_to_firmware(row))  # WHY: normalize each row.
        if firmware_data:  # WHY: only log when rows exist.
            self.logger.info("Loaded %d firmware entries from cache", len(firmware_data))  # WHY: audit.
        return firmware_data  # WHY: return normalized list to caller.

    @staticmethod
    def _row_to_firmware(row: dict[str, Any]) -> dict[str, Any]:
        """Convert one CSV row into a firmware entry dict."""
        return {  # WHY: consistent schema across cache/API sources.
            "version": row["version"],  # WHY: version string is mandatory.
            "model": row["model"],  # WHY: model string is mandatory.
            "record_id": int(row["record_id"]) if row.get("record_id") else None,  # WHY: optional int.
            "record_size": int(row["record_size"]) if row.get("record_size") else None,  # WHY: optional int.
            "record_md5": row.get("record_md5", ""),  # WHY: optional integrity hash.
            "_short": row.get("_short", ""),  # WHY: optional short label from Mist.
        }

    def _fetch_firmware_from_api(self) -> list[dict[str, Any]]:
        """Fetch firmware versions from Mist API."""
        import mistapi  # pylint: disable=import-outside-toplevel

        print("-> Querying available firmware versions from Mist API...")  # WHY: progress cue.
        try:  # WHY: guard against API failures.
            self.logger.debug("Calling listOrgAvailableDeviceVersions API for switch firmware")  # WHY: audit.
            versions_response = mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions(  # WHY: live query.
                self.apisession,
                self.org_id,
                type="switch",
            )
            return self._handle_firmware_response(versions_response)  # WHY: interpret result.
        except Exception as api_error:  # pylint: disable=broad-exception-caught
            self.logger.error("Failed to query switch firmware versions: %s", api_error)  # WHY: audit.
            print(f"X  Error querying firmware versions: {api_error}")  # WHY: user-visible.
            return []  # WHY: empty list halts the workflow gracefully.

    def _handle_firmware_response(self, versions_response: Any) -> list[dict[str, Any]]:
        """Validate the firmware response and persist a cache copy on success."""
        if not (versions_response and hasattr(versions_response, "data") and versions_response.data):
            self.logger.warning("API returned empty or invalid firmware data")  # WHY: audit gap.
            print("X  No firmware data returned from API")  # WHY: user-visible failure.
            return []  # WHY: caller treats empty as failure.
        firmware_data: list[dict[str, Any]] = versions_response.data  # WHY: capture usable rows.
        self.logger.debug("API returned %d firmware entries", len(firmware_data))  # WHY: audit count.
        self._save_to_cache(firmware_data)  # WHY: memoize for future runs.
        return firmware_data  # WHY: hand rows to caller.

    def _save_to_cache(self, firmware_data: list[dict[str, Any]]) -> None:
        """Save firmware data to cache file."""
        try:  # WHY: any file-system failure must not abort the workflow.
            os.makedirs(CACHE_DIR, exist_ok=True)  # WHY: ensure output directory exists.
            self._write_cache_rows(firmware_data)  # WHY: perform actual file write.
            print(f"!? Cached {len(firmware_data)} firmware entries to {self.CACHE_FILE}")  # WHY: user note.
            self.logger.info("Saved %d firmware entries to cache", len(firmware_data))  # WHY: audit.
        except Exception as save_error:  # pylint: disable=broad-exception-caught
            self.logger.warning("Failed to save firmware cache: %s", save_error)  # WHY: audit.
            print(f"!? Warning: Could not cache firmware data: {save_error}")  # WHY: user note.

    def _write_cache_rows(self, firmware_data: list[dict[str, Any]]) -> None:
        """Write the firmware entries as CSV rows to the cache file."""
        fieldnames = [  # WHY: schema mirrors _row_to_firmware for symmetry.
            "version",
            "model",
            "record_id",
            "record_size",
            "record_md5",
            "_short",
        ]
        with open(self.CACHE_FILE, "w", newline="", encoding="utf-8") as csvfile:  # WHY: safe open.
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)  # WHY: header-driven writer.
            writer.writeheader()  # WHY: emit column names first.
            for entry in firmware_data:  # WHY: iterate rows in stable order.
                if isinstance(entry, dict):  # WHY: skip malformed non-dict entries.
                    writer.writerow(self._firmware_to_row(entry))  # WHY: serialize single row.

    @staticmethod
    def _firmware_to_row(entry: dict[str, Any]) -> dict[str, Any]:
        """Convert a firmware entry into a row dict for CSV output."""
        return {  # WHY: default empty strings avoid None serialization surprises.
            "version": entry.get("version", ""),
            "model": entry.get("model", ""),
            "record_id": entry.get("record_id", ""),
            "record_size": entry.get("record_size", ""),
            "record_md5": entry.get("record_md5", ""),
            "_short": entry.get("_short", ""),
        }

    # --------------------------------------------------------------------- #
    # Firmware data processing
    # --------------------------------------------------------------------- #

    def _process_firmware_data(self, firmware_data: list[dict[str, Any]]) -> None:
        """Process firmware data for model compatibility filtering."""
        print(f"-> Processing {len(firmware_data)} firmware entries...")  # WHY: progress cue.
        raw_versions: list[str] = []  # WHY: buffer of matching versions before dedup.
        for firmware_entry in firmware_data:  # WHY: linear scan.
            self._absorb_firmware_entry(firmware_entry, raw_versions)  # WHY: per-entry logic.
        self._finalize_available_versions(raw_versions, len(firmware_data))  # WHY: dedup + sort.

    def _absorb_firmware_entry(
        self,
        firmware_entry: dict[str, Any],
        raw_versions: list[str],
    ) -> None:
        """Record a single firmware entry if it targets a known switch model."""
        if not isinstance(firmware_entry, dict):  # WHY: guard against non-dict rows.
            return  # WHY: skip malformed rows silently.
        version = firmware_entry.get("version")  # WHY: version is required for accounting.
        firmware_model = firmware_entry.get("model")  # WHY: model gates compatibility.
        if not (version and firmware_model and firmware_model in self.switch_models):
            return  # WHY: skip entries not matching organizational models.
        self.compatible_versions.setdefault(version, set()).add(firmware_model)  # WHY: record mapping.
        raw_versions.append(version)  # WHY: buffer for later dedup+sort.
        self.logger.debug(  # WHY: audit compatibility record.
            "Firmware %s compatible with model: %s",
            version,
            firmware_model,
        )

    def _finalize_available_versions(self, raw_versions: list[str], total: int) -> None:
        """Deduplicate, sort, and record the final available_versions list."""
        unique_versions = list(set(raw_versions))  # WHY: collapse duplicates.
        self.available_versions = sorted(  # WHY: newest first for menu ordering.
            unique_versions,
            key=self._version_sort_key,
            reverse=True,
        )
        self.logger.info(  # WHY: audit filter result.
            "Filtered %d compatible versions from %d entries",
            len(self.available_versions),
            total,
        )

    @staticmethod
    def _version_sort_key(
        version_string: str,
    ) -> list[int | str]:
        """Create sort key for proper version number ordering."""
        try:  # WHY: fall back to raw string on parse failure.
            normalized = version_string.replace("-S", ".").replace("R", ".")  # WHY: canonicalize separators.
            parts: list[int | str] = []  # WHY: mixed int/str parts for natural sort.
            for part in normalized.split("."):  # WHY: split into ordered components.
                try:  # WHY: try numeric conversion for correct ordering.
                    parts.append(int(part))  # WHY: numeric components sort numerically.
                except ValueError:  # WHY: non-numeric tokens fall back to string.
                    parts.append(part.lower())  # WHY: lowercase for case-insensitive compare.
            return parts  # WHY: sort key ready.
        except Exception:  # pylint: disable=broad-exception-caught
            return [version_string.lower()]  # WHY: fallback stable ordering.

    # --------------------------------------------------------------------- #
    # Version selection
    # --------------------------------------------------------------------- #

    def _get_version_selection(self) -> dict[str, Any] | None:
        """Get user's firmware version selection."""
        if not self.available_versions:  # WHY: fall back to manual entry when nothing filtered.
            return self._handle_no_versions()  # WHY: delegate to manual path.
        print(f"!? Found {len(self.available_versions)} compatible firmware versions")  # WHY: summary.
        self._display_version_table()  # WHY: show numbered options.
        return self._prompt_version_selection()  # WHY: capture user selection.

    def _handle_no_versions(self) -> dict[str, Any] | None:
        """Handle case when no compatible versions found."""
        if self.switch_models:  # WHY: distinguish 'no matches' vs 'no versions returned at all'.
            # WHY: report which models had no matching firmware.
            print(f"X  No compatible firmware versions found for: {', '.join(sorted(self.switch_models))}")
        else:
            print("X  No switch firmware versions available from API")  # WHY: nothing available at all.
        print("\nFallback Option:")  # WHY: describe manual override path.
        print("You can still proceed by manually specifying a firmware version.")  # WHY: option text.
        print("!? WARNING: Manual entry bypasses model compatibility checks!")  # WHY: risk banner.
        # WHY: single-line manual-entry consent prompt.
        fallback_choice = self.safe_input_fn(
            "\nProceed with manual firmware entry? (y/N): ",
            context="bulk_switch_manual",
        ).lower()
        if fallback_choice not in YES_ANSWERS:  # WHY: any non-affirmative cancels the workflow.
            print("-> Operation cancelled")  # WHY: user note.
            return {"error": "No compatible firmware versions and manual entry declined"}  # WHY: caller sees reason.
        return self._get_manual_version_entry()  # WHY: proceed with manual prompt.

    def _get_manual_version_entry(self) -> dict[str, Any] | None:
        """Get manually entered firmware version."""
        print("\nManual firmware version entry:")  # WHY: user prompt.
        print(f"Switch models in organization: {', '.join(sorted(self.switch_models))}")  # WHY: help.
        print("Examples: 23.4R2.21, 22.4R3.25, 21.4R3.15, 20.4R3.8")  # WHY: format hint.
        while True:  # WHY: reprompt until non-empty version supplied.
            manual_version = self.safe_input_fn(
                "Enter firmware version: ", context="bulk_switch_manual_ver"
            )  # WHY: prompt.
            if manual_version:  # WHY: reject empty entry.
                self.target_version = manual_version  # WHY: commit user value.
                print(f"!? Using manually specified firmware version: {self.target_version}")  # WHY: echo.
                print("   Model compatibility has NOT been verified!")  # WHY: risk reminder.
                self.logger.warning("Using manually specified firmware %s", self.target_version)  # WHY: audit.
                return None  # WHY: success path.
            print("X  Firmware version is required")  # WHY: user feedback.

    def _display_version_table(self) -> None:
        """Display available firmware versions in formatted table."""
        print("\nAvailable firmware versions (filtered by device model compatibility):")  # WHY: header.
        print("Index | Version      | Compatible Models                | Notes")  # WHY: column labels.
        print("------|--------------|----------------------------------|------")  # WHY: separator row.
        for idx, version in enumerate(self.available_versions, 1):  # WHY: 1-based numbering.
            notes = self._get_version_notes(version, idx)  # WHY: label current / recommended.
            models_str = self._format_compatible_models(version)  # WHY: truncated model string.
            print(f"{idx:5} | {version:12} | {models_str:32} | {notes}")  # WHY: aligned table row.

    def _get_version_notes(self, version: str, index: int) -> str:
        """Get notes string for a firmware version."""
        if version in self.current_firmware_versions:  # WHY: annotate currently deployed versions.
            return "(Currently installed)"  # WHY: user hint.
        if index == 1:  # WHY: newest sorted first, so label it recommended.
            return "(Latest/Recommended)"  # WHY: user hint.
        return ""  # WHY: no note otherwise.

    def _format_compatible_models(self, version: str) -> str:
        """Format compatible models string for display."""
        version_models = sorted(self.compatible_versions.get(version, []))  # WHY: stable order.
        models_str = ", ".join(version_models) if version_models else "Unknown"  # WHY: default label.
        if len(models_str) > MODEL_STR_MAX:  # WHY: enforce column width.
            models_str = models_str[:MODEL_STR_TRUNC] + ELLIPSIS  # WHY: truncate + mark truncation.
        return models_str  # WHY: caller renders directly.

    def _prompt_version_selection(self) -> dict[str, Any] | None:
        """Prompt user to select firmware version by index."""
        while True:  # WHY: reprompt until a valid index is chosen or workflow is cancelled.
            result = self._version_prompt_iteration()  # WHY: single iteration encapsulates branching.
            if result is not None:  # WHY: non-None means either success or cancel.
                return result if result else None  # WHY: empty dict -> None on success.

    def _version_prompt_iteration(self) -> dict[str, Any] | None:
        """Run one iteration of the version prompt loop. Return dict or None to reloop."""
        count = len(self.available_versions)  # WHY: recomputed each loop for clarity.
        try:  # WHY: numeric parse must not crash the loop.
            print(f"\nSelect firmware version by index (1-{count}):")  # WHY: instruction.
            selection = self.safe_input_fn("Enter index number: ", context="bulk_switch_index")  # WHY: prompt.
        except KeyboardInterrupt:  # WHY: ctrl-c during prompt cancels workflow.
            print("\n-> Operation cancelled by user")  # WHY: user note.
            return {"cancelled": True}  # WHY: caller sees explicit cancel signal.
        if not selection:  # WHY: empty input triggers reprompt.
            print("X  Selection required")  # WHY: user feedback.
            return None  # WHY: sentinel to keep loop running.
        return self._apply_version_choice(selection, count)  # WHY: convert index to selection.

    def _apply_version_choice(self, selection: str, count: int) -> dict[str, Any] | None:
        """Apply the numeric selection or emit a reprompt on invalid input."""
        try:  # WHY: guard numeric conversion.
            selection_idx = int(selection) - 1  # WHY: convert 1-based to 0-based index.
        except ValueError:  # WHY: non-numeric input reprompts.
            print("X  Invalid input. Please enter a number")  # WHY: user feedback.
            return None  # WHY: sentinel keeps outer loop running.
        if 0 <= selection_idx < count:  # WHY: bounds check.
            self.target_version = self.available_versions[selection_idx]  # WHY: commit choice.
            print(f"-> Selected firmware version: {self.target_version}")  # WHY: echo choice.
            return {}  # WHY: empty dict signals success without payload.
        print(f"X  Invalid selection. Enter a number between 1 and {count}")  # WHY: user feedback.
        return None  # WHY: sentinel keeps outer loop running.

    # --------------------------------------------------------------------- #
    # Step 5: Upgrade Confirmation
    # --------------------------------------------------------------------- #

    def _confirm_upgrade(self) -> bool:
        """Display configuration summary and get user confirmation."""
        self._display_config_summary()  # WHY: recap all selected parameters.
        self._display_warnings()  # WHY: emphasize network-impacting risks.
        print(f"\nTo proceed with switch firmware upgrade, type: {CONFIRM_PHRASE}")  # WHY: instruction.
        confirmation = self.safe_input_fn(  # WHY: use positional signature required by legacy callers.
            "Confirmation: ",
            "",
            True,
            "switch firmware upgrade confirmation",
        )
        if confirmation is None or confirmation != CONFIRM_PHRASE:  # WHY: strict phrase match.
            print("-> Operation cancelled - incorrect confirmation")  # WHY: user note.
            self.logger.info("Switch firmware upgrade cancelled by user")  # WHY: audit cancel.
            return False  # WHY: abort workflow.
        return True  # WHY: proceed with upgrade execution.

    def _display_config_summary(self) -> None:
        """Display upgrade configuration summary."""
        print(f"\n{'=' * 60}")  # WHY: visual separator.
        print("UPGRADE CONFIGURATION SUMMARY")  # WHY: section header.
        print(f"{'=' * 60}")  # WHY: closing border.
        print(f"Organization: {self.org_name}")  # WHY: recap org.
        print(f"Sites to upgrade: {len(self.selected_sites)}")  # WHY: recap scope.
        print(f"Target firmware: {self.target_version}")  # WHY: recap version.
        print(f"Upgrade strategy: {self.upgrade_strategy}")  # WHY: recap strategy.
        force_label = "Yes" if self.force_upgrade else "No"  # WHY: format bool.
        print(f"Force upgrade: {force_label}")  # WHY: recap force flag.
        reboot_label = "Yes" if self.auto_reboot else "No"  # WHY: format bool.
        print(f"Auto reboot: {reboot_label}")  # WHY: recap reboot flag.
        snapshot_label = "Yes" if self.take_snapshot else "No"  # WHY: format bool.
        print(f"Recovery snapshot after reboot: {snapshot_label}")  # WHY: recap snapshot flag.

    @staticmethod
    def _display_warnings() -> None:
        """Display critical warnings before upgrade."""
        print("\n!? CRITICAL WARNING !?")  # WHY: attention banner.
        print("Switch firmware upgrades will cause network disruption!")  # WHY: warn user.
        print("- Switches will reboot and be offline during upgrade")  # WHY: consequence.
        print("- Plan appropriate maintenance windows")  # WHY: mitigation advice.
        print("- Ensure backup connectivity if needed")  # WHY: mitigation advice.
        print("- Monitor upgrade progress closely")  # WHY: post-run guidance.

    # --------------------------------------------------------------------- #
    # Step 6: Execute Upgrades
    # --------------------------------------------------------------------- #

    def _execute_upgrades(self) -> dict[str, Any]:
        """Execute firmware upgrades across all selected sites."""
        print(f"\n{'=' * 60}")  # WHY: visual separator.
        print("EXECUTING SWITCH FIRMWARE UPGRADE")  # WHY: section header.
        print(f"{'=' * 60}")  # WHY: closing border.
        self._initialize_results()  # WHY: seed results container.
        self.logger.info(  # WHY: audit start-of-operation.
            "Starting switch firmware upgrade: %s",
            self.upgrade_results["operation_id"],
        )
        try:  # WHY: catch-all in case an unexpected error escapes site processing.
            for site_index, site_info in enumerate(self.selected_sites, 1):  # WHY: 1-based site count.
                self._process_site(site_index, site_info)  # WHY: per-site orchestration.
            self._finalize_results()  # WHY: stamp end-time and summary.
            return self.upgrade_results  # WHY: caller sees aggregate results.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return self._handle_critical_error(exc)  # WHY: surface as structured error dict.

    def _initialize_results(self) -> None:
        """Initialize results tracking structure."""
        self.upgrade_results = {  # WHY: canonical shape expected by consumers/tests.
            "operation_id": f"switch_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # WHY: unique per-run id.
            "target_version": self.target_version,  # WHY: recap target.
            "strategy": self.upgrade_strategy,  # WHY: recap strategy.
            "force": self.force_upgrade,  # WHY: recap force flag.
            "reboot": self.auto_reboot,  # WHY: recap reboot flag.
            "snapshot": self.take_snapshot,  # WHY: recap snapshot flag.
            "sites_processed": 0,  # WHY: counter for processed sites.
            "sites_successful": 0,  # WHY: counter for successful sites.
            "sites_failed": 0,  # WHY: counter for failed sites.
            "site_results": [],  # WHY: per-site detail records.
            "start_time": datetime.now().isoformat(),  # WHY: audit start timestamp.
            "end_time": None,  # WHY: filled by _finalize_results.
        }

    def _process_site(self, site_index: int, site_info: dict[str, Any]) -> None:
        """Process firmware upgrade for a single site."""
        site_id = site_info.get("id", "")  # WHY: falsy id blocks processing.
        site_name = site_info.get("name", "Unknown Site")  # WHY: display-friendly fallback.
        if not site_id:  # WHY: cannot upgrade without an ID.
            self.logger.error("Site has no ID: %s", site_name)  # WHY: audit skip.
            self.upgrade_results["sites_failed"] += 1  # WHY: count as failure.
            return  # WHY: nothing more to do for this site.
        self._log_site_progress(site_index, site_name, site_id)  # WHY: echo progress.
        try:  # WHY: contain per-site errors so other sites still run.
            self._run_site_upgrade(site_id, site_name)  # WHY: perform actual work.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._record_site_error(site_id, site_name, str(exc))  # WHY: record exception per site.
        self.upgrade_results["sites_processed"] += 1  # WHY: count regardless of outcome.

    def _log_site_progress(self, site_index: int, site_name: str, site_id: str) -> None:
        """Emit a progress line and debug audit for site processing."""
        total = len(self.selected_sites)  # WHY: display total for user context.
        print(f"\n-> Processing site {site_index}/{total}: {site_name}")  # WHY: progress line.
        self.logger.debug("Processing site: %s (%s)", site_name, site_id)  # WHY: audit trace.

    def _run_site_upgrade(self, site_id: str, site_name: str) -> None:
        """Fetch switches for a site and dispatch the upgrade if any exist."""
        site_switches = self._get_site_switches(site_id, site_name)  # WHY: fetch switch list.
        if site_switches is None:  # WHY: None signals API error already recorded.
            return  # WHY: nothing more to do.
        if not site_switches:  # WHY: empty means no switches to upgrade.
            self._record_no_switches(site_id, site_name)  # WHY: record skipped result.
            return  # WHY: skip execution.
        print(f"  -> Found {len(site_switches)} switches")  # WHY: echo count.
        self._execute_site_upgrade(site_id, site_name, site_switches)  # WHY: perform upgrade.

    def _get_site_switches(self, site_id: str, site_name: str) -> list[dict[str, Any]] | None:
        """Get switches for a specific site."""
        import mistapi  # pylint: disable=import-outside-toplevel

        # WHY: query devices scoped to switch type only.
        site_devices_response = mistapi.api.v1.sites.devices.listSiteDevices(self.apisession, site_id, type="switch")
        if site_devices_response.status_code != HTTP_OK:  # WHY: any non-200 aborts this site.
            print(f"  X  Error retrieving devices: {site_devices_response.status_code}")  # WHY: user note.
            self.upgrade_results["sites_failed"] += 1  # WHY: count as failure.
            self.upgrade_results["site_results"].append(  # WHY: record detailed error.
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "status": "failed",
                    "error": f"Device retrieval failed: {site_devices_response.status_code}",
                }
            )
            return None  # WHY: caller distinguishes None (error) from [] (empty).
        return [d for d in site_devices_response.data if d.get("type") == "switch"]  # WHY: filter to switches.

    def _record_no_switches(self, site_id: str, site_name: str) -> None:
        """Record result when no switches found in site."""
        print("  -> No switches found in site")  # WHY: user note.
        self.upgrade_results["sites_processed"] += 1  # WHY: increment processed counter.
        self.upgrade_results["site_results"].append(  # WHY: capture skipped outcome.
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
        switch_device_ids: list[str] = [str(s.get("id")) for s in switches if s.get("id")]  # WHY: filter valid ids.
        if not switch_device_ids:  # WHY: nothing to upgrade if all ids are missing.
            self._record_missing_ids(site_id, site_name)  # WHY: log + record failure.
            return  # WHY: skip API call.
        upgrade_request = self._build_upgrade_request(switch_device_ids)  # WHY: assemble payload.
        print("  -> Initiating firmware upgrade...")  # WHY: user progress cue.
        self.logger.debug(  # WHY: audit request payload for troubleshooting.
            "Upgrade request for site %s: %s",
            site_name,
            upgrade_request,
        )
        upgrade_response = self._call_upgrade_api(site_id, upgrade_request)  # WHY: hit Mist upgrade endpoint.
        self._record_upgrade_result(site_id, site_name, switches, upgrade_response)  # WHY: record outcome.

    def _record_missing_ids(self, site_id: str, site_name: str) -> None:
        """Record failure when switches carry no usable device ids."""
        self.logger.error("No valid switch device IDs found for site %s", site_name)  # WHY: audit.
        self.upgrade_results["sites_failed"] += 1  # WHY: count failure.
        self.upgrade_results["site_results"].append(  # WHY: capture detail.
            {
                "site_id": site_id,
                "site_name": site_name,
                "status": "failed",
                "reason": "No valid switch device IDs",
            }
        )

    def _call_upgrade_api(self, site_id: str, upgrade_request: dict[str, Any]) -> Any:
        """Invoke the Mist upgrade API for the site with the built payload."""
        import mistapi  # pylint: disable=import-outside-toplevel

        return mistapi.api.v1.sites.devices.upgradeSiteDevices(  # WHY: single call site for mocking.
            self.apisession,
            site_id,
            body=upgrade_request,
        )

    def _build_upgrade_request(self, device_ids: list[str]) -> dict[str, Any]:
        """Build the upgrade request payload."""
        return {  # WHY: exact payload shape expected by Mist upgradeSiteDevices.
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
        if response.status_code in STATUS_UPGRADE_OK:  # WHY: 200/202 both indicate acceptance.
            self._record_upgrade_success(site_id, site_name, switches, response)  # WHY: success detail.
            return  # WHY: skip failure branch.
        self._record_upgrade_failure(site_id, site_name, switches, response)  # WHY: failure detail.

    def _record_upgrade_success(
        self,
        site_id: str,
        site_name: str,
        switches: list[dict[str, Any]],
        response: Any,
    ) -> None:
        """Record a successful upgrade initiation for a site."""
        print("  !? Upgrade initiated successfully")  # WHY: user note.
        self.upgrade_results["sites_successful"] += 1  # WHY: increment success counter.
        self.upgrade_results["site_results"].append(  # WHY: append detailed record.
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
        self.logger.info(  # WHY: audit success.
            "Switch firmware upgrade initiated for site: %s",
            site_name,
        )

    def _record_upgrade_failure(
        self,
        site_id: str,
        site_name: str,
        switches: list[dict[str, Any]],
        response: Any,
    ) -> None:
        """Record a failed upgrade initiation for a site."""
        print(f"  X  Upgrade failed: HTTP {response.status_code}")  # WHY: user note.
        self.upgrade_results["sites_failed"] += 1  # WHY: increment failure counter.
        self.upgrade_results["site_results"].append(  # WHY: append detailed record.
            {
                "site_id": site_id,
                "site_name": site_name,
                "status": "failed",
                "switches_count": len(switches),
                "error": f"API error: {response.status_code}",
                "response": response.data if hasattr(response, "data") else None,
            }
        )
        self.logger.error(  # WHY: audit failure.
            "Switch firmware upgrade failed for site %s: %s",
            site_name,
            response.status_code,
        )

    def _record_site_error(self, site_id: str, site_name: str, error: str) -> None:
        """Record an error that occurred while processing a site."""
        print(f"  X  Error processing site: {error}")  # WHY: user note.
        self.upgrade_results["sites_failed"] += 1  # WHY: count failure.
        self.upgrade_results["site_results"].append(  # WHY: append detailed record.
            {
                "site_id": site_id,
                "site_name": site_name,
                "status": "error",
                "error": error,
            }
        )
        self.logger.error(  # WHY: audit exception.
            "Exception processing site %s: %s",
            site_name,
            error,
        )

    def _finalize_results(self) -> None:
        """Finalize results and display summary."""
        self.upgrade_results["end_time"] = datetime.now().isoformat()  # WHY: stamp completion time.
        self._display_results_summary()  # WHY: emit final report to console.

    def _display_results_summary(self) -> None:
        """Display the final upgrade results summary."""
        print(f"\n{'=' * 60}")  # WHY: visual separator.
        print("SWITCH FIRMWARE UPGRADE SUMMARY")  # WHY: section header.
        print(f"{'=' * 60}")  # WHY: closing border.
        results = self.upgrade_results  # WHY: local alias for concise formatting.
        print(f"Operation ID: {results['operation_id']}")  # WHY: unique run id.
        print(f"Sites processed: {results['sites_processed']}")  # WHY: total sites.
        print(f"Sites successful: {results['sites_successful']}")  # WHY: successes.
        print(f"Sites failed: {results['sites_failed']}")  # WHY: failures.
        print(f"Target firmware: {self.target_version}")  # WHY: recap target.
        print(f"Strategy: {self.upgrade_strategy}")  # WHY: recap strategy.
        self._display_failure_details()  # WHY: append per-site failure detail.
        print("\nUpgrade operations have been initiated.")  # WHY: user note.
        print("Monitor progress through Mist dashboard or API.")  # WHY: user hint.
        print("Check individual switch status for completion.")  # WHY: user hint.
        self.logger.info(  # WHY: audit completion.
            "Switch firmware upgrade operation completed: %s",
            results["operation_id"],
        )

    def _display_failure_details(self) -> None:
        """Display details of any failed sites."""
        failed = self.upgrade_results["sites_failed"]  # WHY: local for readability.
        if failed <= 0:  # WHY: skip section when no failures occurred.
            return  # WHY: nothing to render.
        print(f"\n!? {failed} sites encountered errors:")  # WHY: section heading.
        for result in self.upgrade_results["site_results"]:  # WHY: scan for failed/error entries.
            if result["status"] in ("failed", "error"):  # WHY: skip skipped/initiated.
                error_msg = result.get("error", "Unknown error")  # WHY: fallback message.
                print(f"  - {result['site_name']}: {error_msg}")  # WHY: per-site failure line.

    def _handle_critical_error(self, error: Exception) -> dict[str, Any]:
        """Handle critical error during upgrade execution."""
        error_msg = f"Critical error in switch firmware upgrade: {error}"  # WHY: uniform prefix.
        print(f"\nX  {error_msg}")  # WHY: user-visible failure.
        self.logger.error(error_msg)  # WHY: audit failure.
        self.upgrade_results["end_time"] = datetime.now().isoformat()  # WHY: stamp completion.
        self.upgrade_results["error"] = str(error)  # WHY: expose error to caller.
        return self.upgrade_results  # WHY: caller sees partial results.
