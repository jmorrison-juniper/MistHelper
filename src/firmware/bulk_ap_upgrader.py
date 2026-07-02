"""Bulk AP firmware upgrade operations for Mist organizations.

Manages the complete workflow for upgrading AP firmware across one or more
sites: site selection, AP discovery, firmware version analysis, advanced
upgrade configuration, execution, and tracking.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations  # WHY: PEP 563 lazy annotations for cheap Optional[...] usage without runtime cost

import csv  # WHY: stdlib CSV writer used to persist upgrade results table (FR-013 tracking artifact)
import importlib  # WHY: dynamic import for MistHelper globals fallback (avoid circular top-level import)
import json  # WHY: parse Mist API JSON responses and serialize tracking state
import logging  # WHY: FR-007 info-before / debug-after logging pattern used throughout module
import os  # WHY: OS-safe path operations (Constitution VI portable file paths)
import time  # WHY: unix timestamps for schedule offsets and filename discriminators
from collections.abc import Callable  # WHY: PEP 585 preferred; ruff UP035 forbids typing.Callable
from dataclasses import dataclass  # WHY: frozen dataclass replaces 10-param __init__ (FR-004 / Constitution I)
from datetime import UTC, datetime  # WHY: UTC-anchored timestamps in tracking/results filenames
from typing import Any  # WHY: type-erase mistapi session for both prod object and MagicMock test doubles


@dataclass(frozen=True, slots=True)  # WHY: frozen=True prevents mid-run mutation; slots=True stops attr drift
class BulkAPUpgraderConfig:  # WHY: class definition (see docstring)
    """Immutable configuration bundle for BulkAPFirmwareUpgrader.

    Groups every input required by the upgrader's constructor into a single
    dataclass, replacing the legacy 10-parameter __init__ signature (FR-004).
    Frozen so that once a run starts, its configuration cannot be mutated
    mid-flight (defensive against the "same config, two upgraders, one
    modifies mid-run" class of bug).
    """

    # ------------------------------------------------------------------
    # Required session inputs (no defaults so omission raises TypeError)
    # ------------------------------------------------------------------
    org_id: str  # WHY: Mist organization UUID this run targets; required by every downstream API call
    apisession: Any  # WHY: authenticated mistapi session used by every remote call; type-erased for test doubles

    # ------------------------------------------------------------------
    # Optional behavior flags
    # ------------------------------------------------------------------
    sites_override: list[dict[str, Any]] | None = None  # WHY: pre-selected sites skip interactive site prompt
    dry_run: bool = False  # WHY: dry-run gate short-circuits all mutating API calls for safe rehearsals

    # ------------------------------------------------------------------
    # Injected callables (dependency injection seams for tests + reuse)
    # ------------------------------------------------------------------
    safe_input_fn: Callable[..., str] | None = None  # WHY: injected safe_input wrapper keeps stop-signal support
    check_stop_fn: Callable[[], bool] | None = None  # WHY: polled between long steps to abort on Ctrl+C signals
    fetch_sites_fn: Callable[[str], list] | None = None  # WHY: seam over APICoreFetchUtils for tests to stub sites
    get_csv_path_fn: Callable[[str], str] | None = None  # WHY: seam over FilePathUtils for OS-safe results path
    check_firmware_status_fn: Callable[[], None] | None = None  # WHY: seam to launch post-upgrade status viewer
    get_org_id_fn: Callable[[], str] | None = None  # WHY: seam over ConfigUtils.get_cached_or_prompted_org_id


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

    def __init__(self, config: BulkAPUpgraderConfig) -> None:  # WHY: helper definition (see docstring)
        """Initialize the bulk AP firmware upgrader.

        Args:
            config: Immutable ``BulkAPUpgraderConfig`` bundle carrying every
                input the upgrader needs (org id, API session, dry-run flag,
                injected callables). Replaces the legacy 10-parameter
                signature per FR-004 / Constitution I.
        """
        logging.info("Init upgrader org_id=%s dry_run=%s", config.org_id, config.dry_run)  # WHY: info-before FR-007
        self._init_session_ctx(config)  # WHY: PCPP "Prepare" — session/DI callables live in one helper
        self._init_ap_and_site_state()  # WHY: PCPP "Prepare" — mutable AP/site containers isolated
        self._init_plan_and_results_state()  # WHY: PCPP "Prepare" — plan/result counters isolated
        logging.debug("Init complete; sites_override=%s", bool(config.sites_override))  # WHY: debug-after FR-007

    def _init_session_ctx(self, config: BulkAPUpgraderConfig) -> None:  # WHY: helper definition (see docstring)
        """Unpack the ``config`` bundle into per-instance session context.

        Assigns the org id, apisession, override list, dry-run flag, and the
        six injected callables onto ``self``. Falls back to the builtin
        ``input`` when no ``safe_input_fn`` was supplied so tests that omit
        the seam still work.
        """
        logging.debug("Init session ctx for org_id=%s", config.org_id)  # WHY: trace which config bootstraps state
        self.org_id = config.org_id  # WHY: attr so downstream helpers reuse existing self.org_id lookups
        self.apisession = config.apisession  # WHY: authenticated session reused by every remote call
        self.sites_override = config.sites_override  # WHY: pre-selected sites bypass interactive prompt
        self.dry_run = config.dry_run  # WHY: dry-run flag gates every mutating API call
        self._input_fn = config.safe_input_fn or input  # WHY: builtin input is safe fallback if no wrapper
        self._check_stop_fn = config.check_stop_fn  # WHY: stored so long steps can poll for Ctrl+C
        self._fetch_sites_fn = config.fetch_sites_fn  # WHY: seam over APICoreFetchUtils.all_sites_with_limit
        self._get_csv_path_fn = config.get_csv_path_fn  # WHY: seam over FilePathUtils.get_csv_path
        self._check_firmware_status_fn = config.check_firmware_status_fn  # WHY: seam for status viewer
        self._get_org_id_fn = config.get_org_id_fn  # WHY: seam over ConfigUtils.get_cached_or_prompted_org_id

    def _init_ap_and_site_state(self) -> None:  # WHY: helper definition (see docstring)
        """Reset the mutable AP and site containers to empty defaults.

        Every field here is populated during the discovery phase
        (steps 1-4). Initializing them empty here means callers can inspect
        state safely between construction and ``execute()``.
        """
        logging.debug("Init empty AP and site state containers")  # WHY: visible cold-start marker for fresh instance
        self.sites_to_upgrade: list[dict[str, Any]] = []  # WHY: filled by _step1_determine_sites once resolved
        self.all_sites_aps: dict[str, Any] = {}  # WHY: site_id -> AP list index used during discovery
        self.all_aps: list[dict[str, Any]] = []  # WHY: flat list of every AP across selected sites
        self.aps_by_model: dict[str, list[dict[str, Any]]] = {}  # WHY: grouping powers per-model firmware analysis
        self.ap_versions: dict[str, str] = {}  # WHY: model -> current version snapshot for plan diffing

    def _init_plan_and_results_state(self) -> None:  # WHY: helper definition (see docstring)
        """Reset the upgrade plan and execution-result tallies.

        Every field here is populated during the planning phase (steps 5-7)
        or the execution phase (steps 8-11). Initializing them empty here
        prevents attribute-error hazards for early-exit paths.
        """
        logging.debug("Init empty plan and results counters")  # WHY: cheap trace to spot cold-start of a fresh instance
        self.available_versions: list[Any] = []  # WHY: populated in step 4 from firmware inventory API
        self.model_version_ranges: dict[str, list[str]] = {}  # WHY: per-model available versions used in step 5
        self.upgrade_plan: dict[str, dict[str, Any]] = {}  # WHY: model -> {from_version, to_version, ap_ids} plan
        self.skipped_already_at_target: int = 0  # WHY: user-facing counter reported in the results summary
        self.upgrade_config: dict[str, Any] = {}  # WHY: strategy / P2P / schedule chosen in step 6
        self.upgrade_ids: list[str] = []  # WHY: mist-side upgrade IDs used by the status viewer
        self.results: list[dict[str, Any]] = []  # WHY: per-model result rows written to CSV in step 11
        self.successful_upgrades: int = 0  # WHY: user-facing tally reported in the summary banner
        self.failed_upgrades: int = 0  # WHY: user-facing tally reported in the summary banner

    def execute(self) -> None:  # WHY: helper definition (see docstring)
        """Execute the bulk AP firmware upgrade workflow.

        Delegates to four phase helpers (announce, discovery, planning,
        execution) to keep this entry point trivially small and each phase
        independently readable / testable.
        """
        logging.info("Starting advanced bulk AP firmware upgrade for org_id=%s", self.org_id)  # WHY: info-before FR-007
        try:
            self._announce_start()  # WHY: user-facing banner + dry-run notice; extracted so execute stays flat
            if not self._run_discovery_phase():  # WHY: steps 1-4 populate sites/APs/firmware; may early-exit
                return  # WHY: early exit from branch
            if not self._run_planning_phase():  # WHY: steps 5-7 build plan + confirm; may early-exit
                return  # WHY: early exit from branch
            self._run_execution_phase()  # WHY: steps 8-11 mutate Mist + persist results; terminal
        except KeyboardInterrupt:  # WHY: recover from failure
            print("\n Operation cancelled by user.")  # WHY: preserved verbatim per FR-017 observable-equivalence
            logging.info("Bulk AP firmware upgrade cancelled by user interrupt")  # WHY: audit trail for interrupt
        logging.debug("execute() finished for org_id=%s", self.org_id)  # WHY: debug-after FR-007

    def _announce_start(self) -> None:  # WHY: helper definition (see docstring)
        """Emit the workflow-start banner and dry-run notice.

        Split from ``execute`` so the entry point contains only phase
        delegation. Preserves the two legacy log lines verbatim so live logs
        remain observationally equivalent (FR-017).
        """
        logging.info("Starting advanced bulk AP firmware upgrade by site...")  # WHY: preserved verbatim per FR-017
        logging.debug("BulkAPFirmwareUpgrader.execute() initiated")  # WHY: preserved verbatim per FR-017
        logging.debug("Using org_id: %s", self.org_id)  # WHY: preserved verbatim per FR-017
        if self.dry_run:  # WHY: only surface the banner when dry-run is armed
            print("\n  >> DRY-RUN MODE: No actual upgrades will be performed <<")  # WHY: preserved verbatim per FR-017
            logging.info("DRY-RUN MODE enabled - no API calls will be made")  # WHY: preserved verbatim per FR-017

    def _run_discovery_phase(self) -> bool:  # WHY: helper definition (see docstring)
        """Run discovery steps 1-4 (sites, APs, current firmware, available firmware).

        Returns ``False`` at the first step that returns ``False`` (typically
        because the user cancelled or no APs were found). Callers should
        stop the workflow when this returns ``False``.
        """
        logging.info("Discovery phase start for org_id=%s", self.org_id)  # WHY: info-before FR-007
        if not self._step1_determine_sites():  # WHY: step 1 resolves site list (override/file/interactive)
            return False  # WHY: user cancelled site selection — nothing else to do
        if not self._step2_discover_aps():  # WHY: step 2 pulls APs across selected sites
            return False  # WHY: zero APs found — abort before firmware queries
        if not self._step3_fetch_firmware_stats():  # WHY: step 3 gathers current firmware per AP
            return False  # WHY: stats fetch failed — cannot compute a plan
        if not self._step4_fetch_available_firmware():  # WHY: step 4 lists available versions per model
            return False  # WHY: no versions returned — cannot select upgrade targets
        n_aps = len(self.all_aps)  # WHY: extracted so the debug line stays under the 120-char limit
        n_sites = len(self.sites_to_upgrade)  # WHY: extracted so the debug line stays under the 120-char limit
        logging.debug("Discovery done: %d APs %d sites", n_aps, n_sites)  # WHY: debug-after FR-007
        return True  # WHY: green-light the planning phase

    def _run_planning_phase(self) -> bool:  # WHY: helper definition (see docstring)
        """Run planning steps 5-7 (version selection, config, confirmation).

        Returns ``False`` if the user declined the final confirmation or the
        plan is empty. Otherwise returns ``True`` and leaves ``self.upgrade_plan``
        + ``self.upgrade_config`` populated for the execution phase.
        """
        logging.info("Planning phase start for org_id=%s", self.org_id)  # WHY: info-before FR-007
        if not self._step5_select_firmware_versions():  # WHY: step 5 picks target version per model
            return False  # WHY: user cancelled or no upgradeable APs
        if not self._step6_configure_upgrade():  # WHY: step 6 chooses strategy / P2P / schedule
            return False  # WHY: user cancelled config
        if not self._step7_confirm_upgrade():  # WHY: step 7 is the final "yes really do it" gate
            return False  # WHY: user declined — do not touch Mist
        logging.debug("Planning done: plan has %d model groups", len(self.upgrade_plan))  # WHY: debug-after FR-007
        return True  # WHY: green-light the execution phase

    def _run_execution_phase(self) -> None:  # WHY: helper definition (see docstring)
        """Run execution steps 8-11 (upgrades, auto-upgrade, status, results).

        No return value because this phase is terminal — after step 11 the
        run is complete regardless of individual step outcomes.
        """
        logging.info("Execution phase start for org_id=%s", self.org_id)  # WHY: info-before FR-007
        self._step8_execute_upgrades()  # WHY: step 8 fires the actual upgrade API calls (or dry-run stubs)
        self._step9_configure_auto_upgrade()  # WHY: step 9 optionally schedules auto-upgrade rollout
        self._step10_offer_status_check()  # WHY: step 10 offers the post-upgrade status viewer
        self._step11_write_results()  # WHY: step 11 persists the results CSV (last, always runs)
        ok, bad = self.successful_upgrades, self.failed_upgrades  # WHY: alias so debug line fits under 120 chars
        logging.debug("Execution done: success=%d failed=%d", ok, bad)  # WHY: debug-after FR-007

    # =========================================================================
    # STEP 1: SITE SELECTION
    # =========================================================================

    def _step1_determine_sites(self) -> bool:  # WHY: helper definition (see docstring)
        """Determine which sites to upgrade."""
        if self.sites_override:  # WHY: guard on condition
            return self._use_override_sites()  # WHY: surface computed result
        return self._determine_sites_interactive()  # WHY: surface computed result

    def _use_override_sites(self) -> bool:  # WHY: helper definition (see docstring)
        """Use pre-selected sites from override."""
        self.sites_to_upgrade = self.sites_override or []  # WHY: instance state
        site_names = ", ".join(s.get("name", "?") for s in self.sites_to_upgrade)  # WHY: capture intermediate value
        print(f"\n  Using pre-selected sites: {site_names}")  # WHY: user-facing feedback
        logging.info("Using %s override sites", len(self.sites_to_upgrade))  # WHY: info log (FR-007)
        return bool(self.sites_to_upgrade)  # WHY: surface computed result

    def _determine_sites_interactive(self) -> bool:  # WHY: helper definition (see docstring)
        """Determine sites from file or interactive selection."""
        csv_path = self._resolve_csv_path()  # WHY: capture intermediate value
        if csv_path and os.path.exists(csv_path):  # WHY: guard on condition
            return self._load_sites_from_file(csv_path)  # WHY: surface computed result
        return self._select_site_interactively()  # WHY: surface computed result

    def _resolve_csv_path(self) -> str | None:  # WHY: helper definition (see docstring)
        """Resolve path to APUpgradeSiteList.CSV."""
        if self._get_csv_path_fn:  # WHY: guard on condition
            result: str | None = self._get_csv_path_fn("APUpgradeSiteList.CSV")  # WHY: capture intermediate value
            return result  # WHY: surface computed result
        default = os.path.join("data", "APUpgradeSiteList.CSV")  # WHY: capture intermediate value
        return default if os.path.exists(default) else None  # WHY: surface computed result

    def _load_sites_from_file(self, csv_path: str) -> bool:  # WHY: helper definition (see docstring)
        """Load site names from CSV and resolve to site IDs."""
        print(f"\n  Found site list file: {csv_path}")  # WHY: user-facing feedback
        site_names = self._read_site_names_from_file(csv_path)  # WHY: capture intermediate value
        if not site_names:  # WHY: guard on condition
            print(" No site names found in file.")  # WHY: user-facing feedback
            return False  # WHY: surface computed result

        print(f"  Read {len(site_names)} site name(s) from file")  # WHY: user-facing feedback
        all_sites = self._fetch_org_sites_for_lookup()  # WHY: capture intermediate value
        if not all_sites:  # WHY: guard on condition
            return False  # WHY: surface computed result

        return self._resolve_site_names(site_names, all_sites)  # WHY: surface computed result

    def _read_site_names_from_file(self, csv_path: str) -> list[str]:  # WHY: helper definition (see docstring)
        """Read site names from CSV file."""
        site_names = []  # WHY: capture intermediate value
        try:
            with open(csv_path, encoding="utf-8") as f:  # WHY: scoped resource
                reader = csv.reader(f)  # WHY: capture intermediate value
                for row in reader:  # WHY: iterate collection
                    if row and row[0].strip():  # WHY: guard on condition
                        site_names.append(row[0].strip())  # WHY: workflow step
        except Exception as error:  # WHY: recover from failure
            print(f" Error reading site list: {error}")  # WHY: user-facing feedback
            logging.error("Failed to read site list from %s: %s", csv_path, error)  # WHY: error log
        return site_names  # WHY: surface computed result

    def _fetch_org_sites_for_lookup(self) -> list[dict[str, Any]]:  # WHY: helper definition (see docstring)
        """Fetch all org sites for name-to-ID lookup."""
        if self._fetch_sites_fn:  # WHY: guard on condition
            sites_result: list[dict[str, Any]] = list(self._fetch_sites_fn(self.org_id))  # WHY: capture intermediate...
            return sites_result  # WHY: surface computed result
        try:
            import mistapi  # WHY: required module import

            response = mistapi.api.v1.orgs.sites.listOrgSites(self.apisession, self.org_id)  # WHY: capture intermedi...
            all_sites: list[dict[str, Any]] = list(mistapi.get_all(response=response, mist_session=self.apisession))
            return all_sites  # WHY: surface computed result
        except Exception as error:  # WHY: recover from failure
            print(f" Failed to fetch org sites: {error}")  # WHY: user-facing feedback
            logging.error("Failed to fetch sites for org %s: %s", self.org_id, error)  # WHY: error log
            return []  # WHY: surface computed result

    def _resolve_site_names(self, site_names: list[str], all_sites: list[dict[str, Any]]) -> bool:
        """Resolve site names to site dicts (PCPP: partition -> report -> persist)."""
        resolved, missing = self._partition_sites_by_name(site_names, all_sites)  # WHY: split into found/missing
        if missing:  # WHY: surface unresolved names to the user
            self._report_missing_sites(missing)  # WHY: warn about names that did not match
        self.sites_to_upgrade = resolved  # WHY: persist resolved list for downstream workflow
        if resolved:  # WHY: only echo count when at least one site matched
            print(f"  Resolved {len(resolved)} site(s) for upgrade")  # WHY: user-facing feedback
        return bool(resolved)  # WHY: caller decides whether to proceed

    def _partition_sites_by_name(
        self, site_names: list[str], all_sites: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Split requested names into resolved sites and missing names."""
        site_lookup = {s.get("name", "").lower(): s for s in all_sites}  # WHY: O(1) case-insensitive lookup
        resolved: list[dict[str, Any]] = []  # WHY: found-site accumulator
        missing: list[str] = []  # WHY: unknown-name accumulator
        for name in site_names:  # WHY: iterate caller-supplied names
            site = site_lookup.get(name.lower())  # WHY: case-insensitive lookup
            (resolved if site else missing).append(site or name)  # WHY: single branch dispatch by truthiness
        return resolved, missing  # WHY: surface both partitions

    def _report_missing_sites(self, missing: list[str]) -> None:  # WHY: helper definition (see docstring)
        """Report sites that could not be resolved."""
        print(f"\n  Warning: {len(missing)} site(s) not found:")  # WHY: user-facing feedback
        for name in missing[:10]:  # WHY: iterate collection
            print(f"    - {name}")  # WHY: user-facing feedback
        if len(missing) > 10:  # WHY: guard on condition
            print(f"    ... and {len(missing) - 10} more")  # WHY: user-facing feedback

    def _select_site_interactively(self) -> bool:  # WHY: helper definition (see docstring)
        """Interactive site selection."""
        all_sites = self._fetch_org_sites_for_lookup()  # WHY: capture intermediate value
        if not all_sites:  # WHY: guard on condition
            print(" No sites found in organization.")  # WHY: user-facing feedback
            return False  # WHY: surface computed result

        print("\n  Site Selection:")  # WHY: user-facing feedback
        print("   [1] All sites in organization")  # WHY: user-facing feedback
        print("   [2] Select specific sites")  # WHY: user-facing feedback

        try:
            choice = self._input_fn("Select option (1-2): ").strip()  # WHY: capture intermediate value
        except (EOFError, KeyboardInterrupt):  # WHY: recover from failure
            return False  # WHY: surface computed result

        if choice == "1":  # WHY: guard on condition
            return self._select_all_sites(all_sites)  # WHY: surface computed result
        return self._select_multiple_sites(all_sites)  # WHY: surface computed result

    def _select_all_sites(self, all_sites: list[dict[str, Any]]) -> bool:  # WHY: helper definition (see docstring)
        """Select all sites in organization."""
        self.sites_to_upgrade = all_sites  # WHY: instance state
        print(f"  Selected all {len(all_sites)} sites")  # WHY: user-facing feedback
        return True  # WHY: surface computed result

    def _select_multiple_sites(self, all_sites: list[dict[str, Any]]) -> bool:
        """Interactive multi-site selection (PCPP: prompt -> parse -> persist)."""
        self._print_site_menu(all_sites)  # WHY: show numbered choices to user
        indices = self._read_site_indices(len(all_sites))  # WHY: parse user selection into 0-based indices
        if not indices:  # WHY: nothing valid selected -> abort with feedback
            print(" No valid sites selected.")  # WHY: user-facing feedback
            return False  # WHY: caller stops workflow
        self.sites_to_upgrade = [all_sites[i] for i in indices]  # WHY: persist selection in workflow order
        names = ", ".join(s.get("name", "?") for s in self.sites_to_upgrade)  # WHY: friendly echo string
        print(f"  Selected {len(self.sites_to_upgrade)} site(s): {names}")  # WHY: user-facing feedback
        return True  # WHY: signal success to caller

    def _print_site_menu(self, all_sites: list[dict[str, Any]]) -> None:
        """Render numbered list of sites for interactive selection."""
        print("\n  Available Sites:")  # WHY: section header
        for idx, site in enumerate(all_sites, 1):  # WHY: 1-based menu numbering
            print(f"   [{idx}] {site.get('name', 'Unknown')}")  # WHY: user-facing feedback
        print("\n  Enter site numbers (comma-separated, e.g., 1,3,5):")  # WHY: prompt guidance

    def _read_site_indices(self, max_count: int) -> list[int]:
        """Prompt for site selection; return parsed 0-based indices or empty on abort."""
        try:  # WHY: EOF/Ctrl-C during prompt should yield empty selection
            selection = self._input_fn("Selection: ").strip()  # WHY: capture raw user text
        except (EOFError, KeyboardInterrupt):  # WHY: recover from terminal interrupt
            return []  # WHY: empty indicates aborted selection
        return self._parse_index_input(selection, max_count)  # WHY: delegate tokenising to shared parser

    def _parse_index_input(self, text: str, max_count: int) -> list[int]:
        """Parse comma-separated index input into unique in-range indices (0-based)."""
        indices: list[int] = []  # WHY: accumulator preserves user-entered order
        for part in text.split(","):  # WHY: iterate over comma-delimited tokens
            self._absorb_index_token(part.strip(), max_count, indices)  # WHY: delegate per-token parse
        return indices  # WHY: surface computed result

    def _absorb_index_token(self, part: str, max_count: int, indices: list[int]) -> None:
        """Append token's indices to accumulator; silently drop malformed tokens."""
        if "-" in part:  # WHY: range token like "3-7" requires range parsing
            self._absorb_range_token(part, max_count, indices)  # WHY: delegate range branch
            return  # WHY: single-branch dispatch keeps nesting shallow
        if part.isdigit():  # WHY: single-digit token maps to a single index
            self._append_index(int(part) - 1, max_count, indices)  # WHY: delegate append with bounds+dedup

    def _absorb_range_token(self, part: str, max_count: int, indices: list[int]) -> None:
        """Parse a "a-b" token and append each in-range unique index."""
        try:  # WHY: swallow malformed range tokens per pre-refactor behavior
            start, end = part.split("-", 1)  # WHY: split once on the first hyphen
            start_idx = int(start.strip()) - 1  # WHY: convert to 0-based bound
            end_idx = int(end.strip()) - 1  # WHY: convert to 0-based inclusive bound
        except ValueError:  # WHY: recover from non-integer inputs
            return  # WHY: silently drop malformed range token
        for range_idx in range(start_idx, min(end_idx + 1, max_count)):  # WHY: clamp end to max_count
            self._append_index(range_idx, max_count, indices)  # WHY: reuse bounds+dedup logic

    def _append_index(self, idx: int, max_count: int, indices: list[int]) -> None:
        """Append idx if in [0, max_count) and not already present."""
        if 0 <= idx < max_count and idx not in indices:  # WHY: bounds + dedup guard
            indices.append(idx)  # WHY: accumulate unique parsed index in insertion order

    # =========================================================================
    # STEP 2: AP DISCOVERY
    # =========================================================================

    def _step2_discover_aps(self) -> bool:  # WHY: helper definition (see docstring)
        """Discover APs across selected sites."""
        print("\n  Discovering APs across selected sites...")  # WHY: user-facing feedback
        import mistapi  # WHY: required module import

        for site_info in self.sites_to_upgrade:  # WHY: iterate collection
            self._fetch_aps_for_site(site_info, mistapi)  # WHY: instance state

        self._display_ap_discovery_summary()  # WHY: instance state

        if not self.all_aps:  # WHY: guard on condition
            print(" No APs found at any selected site.")  # WHY: user-facing feedback
            return False  # WHY: surface computed result
        return True  # WHY: surface computed result

    def _fetch_aps_for_site(self, site_info: dict[str, Any], mistapi: Any) -> None:  # WHY: helper definition (see do...
        """Fetch APs for a single site (PCPP orchestrator)."""
        site_id = site_info["id"]  # WHY: local alias for readability across branches
        site_name = site_info["name"]  # WHY: local alias used in every log/print line
        # WHY: FR-007 info-before naming the target site for audit trail
        logging.info("Fetch APs starting site=%s site_id=%s", site_name, site_id)  # WHY: info log (FR-007)
        try:
            # WHY: PCPP Compute — one API call fetches all APs at this site
            print(f"   Fetching APs at site '{site_name}'...")  # WHY: user-facing feedback
            site_aps = self._request_site_aps(site_id, mistapi)  # WHY: capture intermediate value
            # WHY: PCPP Persist — record result in aggregate + per-site maps
            self._record_site_ap_result(site_id, site_name, site_aps)  # WHY: instance state
        except Exception as error:  # noqa: BLE001 — API errors surface any way here
            # WHY: PCPP Persist error path — record empty result + error string for tracking
            self._record_site_ap_error(site_id, site_name, error)  # WHY: instance state
        logging.debug("Fetch APs done site=%s total_all_aps=%s", site_name, len(self.all_aps))  # WHY: debug log (FR-...

    def _request_site_aps(self, site_id: str, mistapi: Any) -> list[dict[str, Any]]:  # WHY: helper definition (see d...
        """Call the Mist API and return the paginated AP list (or empty list on none)."""
        # WHY: use listSiteDevices with type=ap to filter server-side and reduce payload
        response = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: capture intermediate value
            self.apisession,
            site_id,
            type="ap",
        )
        # WHY: get_all handles pagination transparently; returns list or None on empty
        site_aps = mistapi.get_all(response=response, mist_session=self.apisession)  # WHY: capture intermediate value
        return site_aps or []  # WHY: normalise None to [] so callers can iterate safely

    def _record_site_ap_result(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        site_aps: list[dict[str, Any]],
    ) -> None:
        """Record AP fetch result for one site — populate index + print progress."""
        # WHY: annotate each AP with owning site for later per-device site lookup
        for ap in site_aps:  # WHY: iterate collection
            ap["_site_id"] = site_id  # WHY: capture intermediate value
            ap["_site_name"] = site_name  # WHY: capture intermediate value
        self.all_aps.extend(site_aps)  # WHY: build combined AP list for cross-site aggregation
        # WHY: per-site index used by summary/reporting steps
        self.all_sites_aps[site_id] = {  # WHY: instance state
            "name": site_name,
            "aps": site_aps,
            "count": len(site_aps),
        }
        # WHY: user-visible message differs by whether site had any APs at all
        if site_aps:  # WHY: guard on condition
            print(f"      Found {len(site_aps)} APs at '{site_name}'")  # WHY: user-facing feedback
        else:
            print(f"      No APs found at site '{site_name}'")  # WHY: user-facing feedback

    def _record_site_ap_error(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        error: Exception,
    ) -> None:
        """Record an error result for one site and surface it to the CLI + logs."""
        # WHY: retain zero-AP record + error string so downstream steps can flag site
        self.all_sites_aps[site_id] = {  # WHY: instance state
            "name": site_name,
            "aps": [],
            "count": 0,
            "error": str(error),
        }
        print(f"      Failed to fetch APs for site '{site_name}': {error}")  # WHY: user-facing feedback
        # WHY: log error at ERROR level so ops can grep logs for fetch failures
        logging.error("Fetch APs failed site=%s error=%s", site_name, error)  # WHY: error log

    def _display_ap_discovery_summary(self) -> None:  # WHY: helper definition (see docstring)
        """Display AP discovery summary with per-site model breakdown."""
        total_aps = len(self.all_aps)  # WHY: capture intermediate value
        sites_with_aps = len([s for s in self.all_sites_aps.values() if s["count"] > 0])  # WHY: capture intermediate...

        print("\n  AP Discovery Summary:")  # WHY: user-facing feedback
        print(f"   Total APs found: {total_aps}")  # WHY: user-facing feedback
        print(f"   Sites with APs: {sites_with_aps}/{len(self.sites_to_upgrade)}")  # WHY: user-facing feedback

        print("\n  Per-Site Breakdown:")  # WHY: user-facing feedback
        print("  " + "-" * 70)  # WHY: user-facing feedback
        for site_data in self.all_sites_aps.values():  # WHY: iterate collection
            self._print_site_ap_breakdown(site_data)  # WHY: instance state
        print("  " + "-" * 70)  # WHY: user-facing feedback

    def _print_site_ap_breakdown(self, site_data: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Print AP breakdown for a single site."""
        site_name = site_data["name"]  # WHY: capture intermediate value
        ap_count = site_data["count"]  # WHY: capture intermediate value

        if "error" in site_data:  # WHY: guard on condition
            print(f"   {site_name}: ERROR - {site_data['error']}")  # WHY: user-facing feedback
        elif ap_count == 0:  # WHY: alternate branch
            print(f"   {site_name}: No APs (will be skipped)")  # WHY: user-facing feedback
        else:
            model_counts: dict[str, int] = {}  # WHY: capture intermediate value
            for ap in site_data.get("aps", []):  # WHY: iterate collection
                model = ap.get("model", "Unknown")  # WHY: capture intermediate value
                model_counts[model] = model_counts.get(model, 0) + 1  # WHY: capture intermediate value
            model_summary = ", ".join(f"{m}:{c}" for m, c in sorted(model_counts.items()))  # WHY: capture intermedia...
            print(f"   {site_name}: {ap_count} APs ({model_summary})")  # WHY: user-facing feedback

    # =========================================================================
    # STEP 3: FIRMWARE STATS COLLECTION
    # =========================================================================

    def _step3_fetch_firmware_stats(self) -> bool:  # WHY: helper definition (see docstring)
        """Fetch firmware stats and group APs by model."""
        print("\n  Getting current firmware versions from device statistics...")  # WHY: user-facing feedback

        stats_lookup = self._fetch_all_ap_stats()  # WHY: capture intermediate value
        self._process_aps_with_stats(stats_lookup)  # WHY: instance state
        self._display_model_summary()  # WHY: instance state
        return True  # WHY: surface computed result

    def _fetch_all_ap_stats(self) -> dict[str, Any]:  # WHY: helper definition (see docstring)
        """Fetch device stats for all sites."""
        stats_lookup: dict[str, Any] = {}  # WHY: capture intermediate value
        for site_id, site_data in self.all_sites_aps.items():  # WHY: iterate collection
            if site_data["count"] == 0:  # WHY: guard on condition
                continue  # WHY: skip iteration
            site_stats = self._fetch_site_ap_stats(site_id, site_data["name"])  # WHY: capture intermediate value
            stats_lookup.update(site_stats)  # WHY: workflow step
        return stats_lookup  # WHY: surface computed result

    def _fetch_site_ap_stats(self, site_id: str, site_name: str) -> dict[str, Any]:
        """Fetch AP stats for a single site, returning a device_id-keyed lookup."""
        try:  # WHY: any network/parse failure yields empty lookup (matches pre-refactor behavior)
            site_stats = self._call_site_stats_api(site_id, site_name)  # WHY: extracted API call
        except Exception as error:  # WHY: recover from failure
            logging.error("Failed to fetch stats for site %s: %s", site_name, error)  # WHY: error log
            return {}  # WHY: empty lookup keeps outer loop resilient
        return self._index_stats_by_device_id(site_stats)  # WHY: PCPP compute the id->stats map

    def _call_site_stats_api(self, site_id: str, site_name: str) -> list[dict[str, Any]]:
        """Invoke listSiteDevicesStats via mistapi and return list of stats records."""
        import mistapi  # WHY: lazy import keeps module load cheap
        print(f"   Fetching device statistics for APs at '{site_name}'...")  # WHY: user-facing feedback
        stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(  # WHY: paginated call
            self.apisession, site_id, type="ap", limit=1000
        )
        return mistapi.get_all(response=stats_resp, mist_session=self.apisession) or []  # WHY: unify None -> []

    def _index_stats_by_device_id(self, site_stats: list[dict[str, Any]]) -> dict[str, Any]:
        """Index stats records by device_id (falling back to device_id or mac field)."""
        lookup: dict[str, Any] = {}  # WHY: accumulator keyed by device id
        for stats in site_stats:  # WHY: single pass over stats records
            device_id = stats.get("id") or stats.get("device_id") or stats.get("mac")  # WHY: pick first non-empty
            if device_id:  # WHY: skip records with no identifier
                lookup[device_id] = stats  # WHY: last-write-wins for duplicate ids
        return lookup  # WHY: surface computed result

    def _process_aps_with_stats(self, stats_lookup: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Process APs and extract version information."""
        for ap in self.all_aps:  # WHY: iterate collection
            model = ap.get("model", "Unknown")  # WHY: capture intermediate value
            device_id: str = str(ap.get("id", ""))  # WHY: capture intermediate value

            if model not in self.aps_by_model:  # WHY: guard on condition
                self.aps_by_model[model] = []  # WHY: instance state
            self.aps_by_model[model].append(ap)  # WHY: instance state

            version = self._get_ap_version(ap, stats_lookup)  # WHY: capture intermediate value
            self.ap_versions[device_id] = version  # WHY: instance state

    def _get_ap_version(self, ap: dict[str, Any], stats_lookup: dict[str, Any]) -> str:  # WHY: helper definition (se...
        """Get firmware version for an AP."""
        device_id: str = str(ap.get("id", ""))  # WHY: capture intermediate value
        device_mac: str = str(ap.get("mac", ""))  # WHY: capture intermediate value

        for key in [device_id, device_mac]:  # WHY: iterate collection
            if key and key in stats_lookup:  # WHY: guard on condition
                stats = stats_lookup[key]  # WHY: capture intermediate value
                if isinstance(stats, dict):  # WHY: guard on condition
                    version: str = str(stats.get("version", "Unknown"))  # WHY: capture intermediate value
                    return version  # WHY: surface computed result
        return "Unknown"  # WHY: surface computed result

    def _display_model_summary(self) -> None:  # WHY: helper definition (see docstring)
        """Display summary of AP models found."""
        print(f"\n  AP Models found across {len(self.sites_to_upgrade)} site(s):")  # WHY: user-facing feedback
        for model, devices in self.aps_by_model.items():  # WHY: iterate collection
            versions = set(self.ap_versions.get(str(d.get("id", "")), "Unknown") for d in devices)  # WHY: capture in...
            versions_text = ", ".join(sorted(versions, reverse=True)) if "Unknown" not in versions else "Unknown"
            print(f"   !? {model}: {len(devices)} devices" f" (Current versions: {versions_text})")  # WHY: user-faci...

    # =========================================================================
    # STEP 4: AVAILABLE FIRMWARE VERSIONS
    # =========================================================================

    def _step4_fetch_available_firmware(self) -> bool:  # WHY: helper definition (see docstring)
        """Fetch available firmware versions from API."""
        import mistapi  # WHY: required module import

        print("\n  Fetching available firmware versions...")  # WHY: user-facing feedback
        try:
            response = mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions(self.apisession, self.org_id)
            self.available_versions = response.data  # WHY: instance state
            self._build_model_version_ranges()  # WHY: instance state
            return True  # WHY: surface computed result
        except Exception as error:  # WHY: recover from failure
            print(f"! Failed to fetch available firmware versions: {error}")  # WHY: user-facing feedback
            return False  # WHY: surface computed result

    def _build_model_version_ranges(self) -> None:
        """Build model-to-versions mapping from available_versions."""
        if not self.available_versions:  # WHY: no data to seed the mapping
            return  # WHY: early exit before scan
        for version_info in self.available_versions:  # WHY: iterate available firmware records
            self._absorb_version_info(version_info)  # WHY: delegate per-record parsing

    def _absorb_version_info(self, version_info: Any) -> None:
        """Add version_info's version string to each of its models' buckets."""
        if not isinstance(version_info, dict):  # WHY: skip malformed records defensively
            return  # WHY: silently ignore non-dict entries
        version = version_info.get("version", "Unknown")  # WHY: fallback keeps entry visible
        target_models = self._extract_target_models(version_info)  # WHY: compute the model list once
        for model_name in target_models:  # WHY: descriptive loop var per CONV-NAME
            if model_name:  # WHY: guard against empty model strings
                self.model_version_ranges.setdefault(model_name, []).append(version)  # WHY: seed+extend bucket

    def _extract_target_models(self, version_info: dict[str, Any]) -> list[str]:
        """Return the list of model names a version record applies to."""
        models = version_info.get("models", [])  # WHY: preferred multi-model list
        if models:  # WHY: multi-model form takes precedence
            return list(models)  # WHY: copy to isolate caller state
        model = version_info.get("model")  # WHY: fallback single-model field
        return [model] if model else []  # WHY: wrap single into list; empty for missing

    # =========================================================================
    # STEP 5: FIRMWARE VERSION SELECTION
    # =========================================================================

    def _step5_select_firmware_versions(self) -> bool:  # WHY: helper definition (see docstring)
        """Let user select firmware version for each model."""
        print("\n  Firmware Version Selection:")  # WHY: user-facing feedback
        print("=" * 60)  # WHY: user-facing feedback

        self._display_current_version_summary()  # WHY: instance state
        self._display_compatibility_analysis()  # WHY: instance state

        for model, devices in self.aps_by_model.items():  # WHY: iterate collection
            self._select_version_for_model(model, devices)  # WHY: instance state

        if not self.upgrade_plan:  # WHY: guard on condition
            print(" No firmware upgrades selected. Exiting.")  # WHY: user-facing feedback
            return False  # WHY: surface computed result

        return self._validate_upgrade_plan()  # WHY: surface computed result

    def _display_current_version_summary(self) -> None:  # WHY: helper definition (see docstring)
        """Display current firmware status summary."""
        print("! Current Firmware Status Summary:")  # WHY: user-facing feedback
        all_versions: dict[str, list[str]] = {}  # WHY: capture intermediate value
        for model, devices in self.aps_by_model.items():  # WHY: iterate collection
            for device in devices:  # WHY: iterate collection
                version = self.ap_versions.get(str(device.get("id", "")), "Unknown")  # WHY: capture intermediate value
                if version not in all_versions:  # WHY: guard on condition
                    all_versions[version] = []  # WHY: capture intermediate value
                all_versions[version].append(f"{device.get('name', 'Unnamed')} ({model})")  # WHY: workflow step

        for version, device_list in sorted(all_versions.items(), reverse=True):  # WHY: iterate collection
            print(f"   Version {version}: {len(device_list)} devices")  # WHY: user-facing feedback

    def _display_compatibility_analysis(self) -> None:  # WHY: helper definition (see docstring)
        """Display cross-model compatibility analysis."""
        site_models = set(self.aps_by_model.keys())  # WHY: capture intermediate value
        matching = site_models.intersection(set(self.model_version_ranges.keys()))  # WHY: capture intermediate value

        if len(matching) <= 1:  # WHY: guard on condition
            return  # WHY: early exit from branch

        print("\n  Version Compatibility Analysis:")  # WHY: user-facing feedback
        universal = self._find_universal_versions(matching)  # WHY: capture intermediate value
        if universal:  # WHY: guard on condition
            print("   UNIVERSAL versions (compatible with ALL models):")  # WHY: user-facing feedback
            print(f"      {', '.join(sorted(universal, reverse=True)[:5])}")  # WHY: user-facing feedback

    def _find_universal_versions(self, models: set[str]) -> list[str]:
        """Find versions compatible with all models (compute -> filter)."""
        all_versions = self._collect_all_versions(models)  # WHY: union of every candidate version across models
        return [v for v in all_versions if self._is_universal(v, models)]  # WHY: keep only versions supporting all

    def _collect_all_versions(self, models: set[str]) -> set[str]:
        """Union of versions offered for any of the given models."""
        all_versions: set[str] = set()  # WHY: seed empty union
        for model in models:  # WHY: iterate caller-supplied model set
            all_versions.update(self.model_version_ranges.get(model, []))  # WHY: safe update against missing models
        return all_versions  # WHY: surface computed result

    def _is_universal(self, version: str, models: set[str]) -> bool:
        """True when every model advertises support for this version."""
        return all(version in self.model_version_ranges.get(m, []) for m in models)  # WHY: intersection check

    def _select_version_for_model(self, model: str, devices: list[dict[str, Any]]) -> bool:  # WHY: helper definition...
        """Select firmware version for a specific model."""
        model_versions = self._get_versions_for_model(model)  # WHY: capture intermediate value
        if not model_versions:  # WHY: guard on condition
            print(f"!  No firmware versions found for model '{model}' - skipping")  # WHY: user-facing feedback
            return False  # WHY: surface computed result

        print(f"\n  Model: {model} ({len(devices)} devices)")  # WHY: user-facing feedback
        self._display_model_versions(model, model_versions)  # WHY: instance state
        return self._get_user_version_selection(model, devices, model_versions)  # WHY: surface computed result

    def _get_versions_for_model(self, model: str) -> list[dict[str, Any]]:
        """Get deduplicated, sorted versions for a model (newest first)."""
        raw_versions = self._collect_raw_versions_for_model(model)  # WHY: PCPP compute stage 1
        deduped = self._dedupe_versions_by_number(raw_versions)  # WHY: PCPP compute stage 2
        return self._sort_versions_desc(deduped)  # WHY: PCPP present stage 3

    def _collect_raw_versions_for_model(self, model: str) -> list[dict[str, Any]]:
        """Return every available_versions entry that mentions this model."""
        raw_versions: list[dict[str, Any]] = []  # WHY: accumulator for matching entries
        for entry in self.available_versions:  # WHY: descriptive loop var per CONV-NAME
            if not isinstance(entry, dict):  # WHY: skip malformed non-dict payloads
                continue  # WHY: defensive skip
            models = entry.get("models", [])  # WHY: multi-model version entries carry a list
            single = entry.get("model")  # WHY: legacy single-model entries carry a scalar
            if model in models or single == model:  # WHY: match either shape
                raw_versions.append(entry)  # WHY: dedup happens in next pass
        return raw_versions  # WHY: surface computed result

    def _dedupe_versions_by_number(self, raw_versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return one entry per unique version-number string (first sighting wins)."""
        version_dict: dict[str, dict[str, Any]] = {}  # WHY: dedup by version-number string
        for entry in raw_versions:  # WHY: single pass; first entry per number wins
            num = entry.get("version", "Unknown")  # WHY: version string is the dedup key
            version_dict.setdefault(num, entry)  # WHY: preserve API-order priority
        return list(version_dict.values())  # WHY: surface computed result

    def _sort_versions_desc(self, versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort versions descending by numeric dotted tuple; fall back to string sort."""
        try:  # WHY: attempt numeric sort first for correct dotted-version ordering
            versions.sort(key=lambda x: tuple(map(int, x.get("version", "0").split("."))), reverse=True)
        except ValueError:  # WHY: non-numeric segment triggers string fallback
            versions.sort(key=lambda x: x.get("version", ""), reverse=True)  # WHY: fallback lexicographic
        return versions  # WHY: surface computed result

    def _display_model_versions(self, model: str, versions: list[dict[str, Any]]) -> None:
        """Display current + available versions for a model."""
        current = set(self.ap_versions.get(str(d.get("id", "")), "Unknown") for d in self.aps_by_model[model])
        print(f"   Current versions: {', '.join(sorted(current, reverse=True))}")  # WHY: show installed firmware
        print(f"   Available versions ({len(versions)} found):")  # WHY: header for the numbered list
        for idx, entry in enumerate(versions):  # WHY: 0-based menu numbering (matches selection input)
            self._print_version_row(idx, entry, current)  # WHY: delegate per-row formatting

    def _print_version_row(self, idx: int, entry: dict[str, Any], current: set[str]) -> None:
        """Print one version row with RECOMMENDED / CURRENT badges."""
        num = entry.get("version", "Unknown")  # WHY: default label when API omits the field
        badges = self._version_badges(entry, num, current)  # WHY: compute badge suffix once
        print(f"      [{idx}] {num}{badges}")  # WHY: single-line row per version

    def _version_badges(self, entry: dict[str, Any], num: str, current: set[str]) -> str:
        """Return `` or ` [BADGE1, BADGE2]` suffix based on entry+installed flags."""
        indicators: list[str] = []  # WHY: accumulator preserves ordering RECOMMENDED then CURRENT
        if entry.get("recommended"):  # WHY: vendor recommendation flag
            indicators.append("RECOMMENDED")  # WHY: UI badge literal
        if num in current:  # WHY: already installed on at least one AP of this model
            indicators.append("CURRENT")  # WHY: UI badge literal
        return f" [{', '.join(indicators)}]" if indicators else ""  # WHY: empty when no badges apply

    def _get_user_version_selection(
        self,
        model: str,
        devices: list[dict[str, Any]],
        versions: list[dict[str, Any]],
    ) -> bool:
        """Prompt for version index; loop until user selects or skips."""
        prompt = f"Select version for {model} (0-{len(versions) - 1}, 's' to skip): "  # WHY: reuse prompt text
        while True:  # WHY: retry on invalid input; explicit exits inside branches
            outcome = self._read_version_choice(model, devices, versions, prompt)  # WHY: single-turn resolver
            if outcome is not None:  # WHY: helper signals completion via bool; None means "retry"
                return outcome  # WHY: propagate accept/skip decision

    def _read_version_choice(
        self,
        model: str,
        devices: list[dict[str, Any]],
        versions: list[dict[str, Any]],
        prompt: str,
    ) -> bool | None:
        """Resolve one prompt turn; None => retry loop, bool => terminate loop."""
        try:  # WHY: consolidate parse + interrupt handling in one turn
            user_input = self._input_fn(prompt).strip().lower()  # WHY: normalize whitespace + case
        except KeyboardInterrupt:  # WHY: Ctrl-C during prompt exits selection as "no"
            return False  # WHY: caller treats as skip
        if user_input == "s":  # WHY: explicit skip token
            print(f"!  Skipping firmware upgrade for {model}")  # WHY: user-facing feedback
            return False  # WHY: skip decision terminates loop
        try:  # WHY: parse index; ValueError triggers retry
            idx = int(user_input)  # WHY: convert to 0-based index
        except ValueError:  # WHY: non-integer -> retry with feedback
            print(" Invalid input.")  # WHY: user-facing feedback
            return None  # WHY: signal caller to retry
        if 0 <= idx < len(versions):  # WHY: in-range index accepted
            return self._apply_version_selection(model, devices, versions[idx])  # WHY: delegate acceptance path
        print("! Invalid selection.")  # WHY: out-of-range feedback
        return None  # WHY: retry loop

    def _apply_version_selection(  # WHY: helper definition (see docstring)
        self,
        model: str,
        devices: list[dict[str, Any]],
        selected: dict[str, Any],
    ) -> bool:
        """PCPP orchestrator: partition devices, record selection, return acceptance flag."""
        target_version = selected.get("version")  # WHY: single lookup of the candidate version string
        logging.info("apply_version_selection start model=%s v=%s n=%s", model, target_version, len(devices))  # FR-007
        needing_upgrade, already_at_target = self._partition_devices_by_version(devices, target_version)  # PCPP compute
        if already_at_target:  # WHY: only announce skips when the skip count is non-zero
            print(f"   -> Skipping {len(already_at_target)} device(s) already at {target_version}")  # FR-017 verbatim
            self.skipped_already_at_target += len(already_at_target)  # WHY: aggregate for final summary
        if not needing_upgrade:  # WHY: early return when no work remains after filtering
            print(f"!  All {len(devices)} {model} devices already at {target_version} - nothing to upgrade")  # FR-017
            logging.debug("apply_version_selection result=skipped model=%s", model)  # WHY: FR-007 debug-after
            return False  # WHY: signal caller that selection was declined
        self._record_selection_in_plan(model, target_version, selected, needing_upgrade)  # WHY: PCPP persist
        logging.debug("apply_version_selection result=accepted model=%s n=%s", model, len(needing_upgrade))  # FR-007
        return True  # WHY: signal caller that selection was accepted

    def _partition_devices_by_version(  # WHY: helper definition (see docstring)
        self,
        devices: list[dict[str, Any]],
        target_version: Any,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Compute helper: split devices into (needing_upgrade, already_at_target)."""
        logging.info("partition_devices_by_version start target=%s n=%s", target_version, len(devices))  # WHY: FR-007
        needing_upgrade: list[dict[str, Any]] = []  # WHY: accumulator for devices whose firmware differs from target
        already_at_target: list[dict[str, Any]] = []  # WHY: accumulator for devices already matching target
        for device in devices:  # WHY: single pass over the device list to classify each entry
            device_id: str = str(device.get("id", ""))  # WHY: coerce to str for dict lookup stability
            current = self.ap_versions.get(device_id, "Unknown")  # WHY: fallback keeps unknowns in upgrade bucket
            if current == target_version:  # WHY: exact-match comparison suffices for firmware version strings
                already_at_target.append(device)  # WHY: classify as no-op
            else:
                needing_upgrade.append(device)  # WHY: classify as needing upgrade
        logging.debug("partition result upgrade=%s skip=%s", len(needing_upgrade), len(already_at_target))  # FR-007
        return needing_upgrade, already_at_target  # WHY: caller consumes both buckets

    def _record_selection_in_plan(  # WHY: helper definition (see docstring)
        self,
        model: str,
        target_version: Any,
        selected: dict[str, Any],
        needing_upgrade: list[dict[str, Any]],
    ) -> None:
        """Persist helper: write selection into upgrade_plan and echo acceptance banner."""
        # WHY: FR-007 info-before with model + version + device count
        logging.info(  # WHY: info log (FR-007)
            "record_selection_in_plan model=%s version=%s upgrade_count=%s",
            model,
            target_version,
            len(needing_upgrade),
        )
        self.upgrade_plan[model] = {  # WHY: single dict write keyed by model preserves earlier plan shape
            "version": target_version,  # WHY: caller reads this when constructing upgrade body
            "version_info": selected,  # WHY: keep full selection payload for downstream P2P/canary logic
            "devices": needing_upgrade,  # WHY: only devices still needing upgrade are targeted
        }
        # WHY: FR-017 verbatim acceptance banner preserved from pre-refactor UI
        print(f"! Selected version {target_version} for {model}" f" ({len(needing_upgrade)} devices need upgrade)")
        logging.debug("record_selection_in_plan committed model=%s", model)  # WHY: FR-007 debug-after

    def _validate_upgrade_plan(self) -> bool:
        """Validate and display upgrade plan summary; prompt only when multi-version."""
        self._print_plan_summary()  # WHY: PCPP present the plan
        if len({p["version"] for p in self.upgrade_plan.values()}) <= 1:  # WHY: single-version needs no prompt
            return True  # WHY: uniform upgrade proceeds without extra confirmation
        return self._prompt_multi_version_confirmation()  # WHY: multi-version requires explicit confirm

    def _print_plan_summary(self) -> None:
        """Print header + per-model rows + totals + skipped-count line."""
        print("\n  Upgrade Plan Summary:")  # WHY: user-facing feedback header
        print("=" * 60)  # WHY: user-facing feedback separator
        total = sum(len(p["devices"]) for p in self.upgrade_plan.values())  # WHY: aggregate device count
        versions = {p["version"] for p in self.upgrade_plan.values()}  # WHY: unique target versions
        for model, plan in self.upgrade_plan.items():  # WHY: one row per planned model
            print(f"   {model}: {len(plan['devices'])} devices firmware {plan['version']}")  # WHY: FR-017 verbatim
        print(f"\n   Total: {total} devices to upgrade, {len(versions)} version(s)")  # WHY: aggregate row
        if self.skipped_already_at_target > 0:  # WHY: only announce skips when non-zero
            print(f"   Skipped: {self.skipped_already_at_target} devices already at target version")  # WHY: FR-017

    def _prompt_multi_version_confirmation(self) -> bool:
        """Ask user to confirm multi-version upgrade; return True on yes, False otherwise."""
        confirm = self._input_fn("\n  Proceed with multi-version upgrade? (y/n): ").strip().lower() or "y"
        return confirm in ("y", "yes")  # WHY: single expression evaluates confirmation

    # =========================================================================
    # STEP 6: UPGRADE CONFIGURATION
    # =========================================================================

    def _step6_configure_upgrade(self) -> bool:  # WHY: helper definition (see docstring)
        """Configure advanced upgrade options."""
        print("\n  Advanced Upgrade Configuration:")  # WHY: user-facing feedback
        print("=" * 60)  # WHY: user-facing feedback

        self._select_strategy()  # WHY: instance state
        self._configure_strategy_options()  # WHY: instance state
        self._configure_p2p()  # WHY: instance state
        self._configure_scheduling()  # WHY: instance state
        self._configure_force_option()  # WHY: instance state
        self._display_final_config()  # WHY: instance state
        return True  # WHY: surface computed result

    def _select_strategy(self) -> None:  # WHY: helper definition (see docstring)
        """PCPP orchestrator: prompt user for download + reboot strategies and persist upgrade config."""
        # WHY: FR-007 info-before signals entry into strategy selection UI
        logging.info("select_strategy starting")  # WHY: info log (FR-007)
        download_strategy = self._prompt_download_strategy()  # WHY: Present + Compute — user picks download strategy
        reboot_strategy = self._prompt_reboot_strategy()  # WHY: Present + Compute — user picks reboot strategy
        self._init_upgrade_config(download_strategy, reboot_strategy)  # WHY: Persist selections into instance state
        # WHY: FR-007 debug-after reports the chosen pair for traceability
        logging.debug(  # WHY: debug log (FR-007)
            "select_strategy result download=%s reboot=%s",
            download_strategy,
            reboot_strategy,
        )

    def _prompt_download_strategy(self) -> str:  # WHY: helper definition (see docstring)
        """Present + Compute: print DOWNLOAD strategy menu, prompt user, return selection name."""
        # WHY: FR-007 info-before signals user is being prompted for download strategy
        logging.info("prompt_download_strategy starting")  # WHY: info log (FR-007)
        download_strategies = {  # WHY: constant lookup table maps menu keys to (name, description)
            "1": ("big_bang", "Download all at once - no orchestration"),
            "2": ("serial", "Download one device at a time"),
            "3": ("canary", "Phased download rollout"),
        }
        # WHY: FR-017 verbatim banner preserved from pre-refactor UI
        print("\n DOWNLOAD Strategy (how firmware is distributed):")  # WHY: user-facing feedback
        for key, (name, desc) in download_strategies.items():  # WHY: iterate keys in dict insertion order
            print(f"   [{key}] {name.upper()}: {desc}")  # WHY: pre-refactor menu formatting preserved
        # WHY: default "3" (canary) matches pre-refactor default when user presses Enter
        download_choice = self._input_fn("Select download strategy (1-3, default=3 canary): ").strip() or "3"
        download_strategy = download_strategies.get(download_choice, download_strategies["3"])[0]  # WHY: unwrap name
        print(f"! Selected download strategy: {download_strategy.upper()}")  # WHY: FR-017 verbatim echo
        logging.debug("prompt_download_strategy selected=%s", download_strategy)  # WHY: FR-007 debug-after
        return download_strategy  # WHY: hand chosen strategy name back to orchestrator

    def _prompt_reboot_strategy(self) -> str:  # WHY: helper definition (see docstring)
        """Present + Compute: print REBOOT strategy menu, prompt user, return selection name."""
        # WHY: FR-007 info-before signals user is being prompted for reboot strategy
        logging.info("prompt_reboot_strategy starting")  # WHY: info log (FR-007)
        reboot_strategies = {  # WHY: constant lookup table for reboot strategies (RRM is AP-only)
            "1": ("big_bang", "Reboot all at once"),
            "2": ("serial", "Reboot one at a time"),
            "3": ("canary", "Phased reboot rollout"),
            "4": ("rrm", "RRM-aware reboot (AP only - minimizes Wi-Fi disruption)"),
        }
        # WHY: FR-017 verbatim banner preserved from pre-refactor UI
        print("\n REBOOT Strategy (how devices restart after download):")  # WHY: user-facing feedback
        for key, (name, desc) in reboot_strategies.items():  # WHY: iterate keys in dict insertion order
            print(f"   [{key}] {name.upper()}: {desc}")  # WHY: pre-refactor menu formatting preserved
        # WHY: default "4" (rrm) matches pre-refactor default when user presses Enter
        reboot_choice = self._input_fn("Select reboot strategy (1-4, default=4 rrm): ").strip() or "4"  # WHY: captur...
        reboot_strategy = reboot_strategies.get(reboot_choice, reboot_strategies["4"])[0]  # WHY: unwrap name
        print(f"! Selected reboot strategy: {reboot_strategy.upper()}")  # WHY: FR-017 verbatim echo
        logging.debug("prompt_reboot_strategy selected=%s", reboot_strategy)  # WHY: FR-007 debug-after
        return reboot_strategy  # WHY: hand chosen strategy name back to orchestrator

    def _init_upgrade_config(self, download_strategy: str, reboot_strategy: str) -> None:  # WHY: helper definition (...
        """Persist helper: seed self.upgrade_config with strategy pair + baseline defaults."""
        # WHY: FR-007 info-before with both chosen strategy names for traceability
        logging.info(  # WHY: info log (FR-007)
            "init_upgrade_config download=%s reboot=%s",
            download_strategy,
            reboot_strategy,
        )
        self.upgrade_config = {  # WHY: single write establishes the mutable config dict for later phases
            "download_strategy": download_strategy,  # WHY: consumed by _build_upgrade_body when POSTing
            "reboot_strategy": reboot_strategy,  # WHY: consumed by _build_upgrade_body when POSTing
            "force": False,  # WHY: default off; user can flip via _configure_force_option
            "enable_p2p": True,  # WHY: default on; user can adjust via _configure_p2p
            "max_failure_percentage": 7,  # WHY: pre-refactor default retained for FR-017 parity
            "start_time": None,  # WHY: None means "start immediately" per Mist API semantics
            "canary_phases": [1, 2, 4, 8, 16, 32, 64, 100],  # WHY: geometric phase ramp used for canary strategy
            "p2p_cluster_size": 5,  # WHY: default cluster size for peer-to-peer downloads
            "p2p_parallelism": 100,  # WHY: default parallelism percentage for P2P transfer
            "reboot": True,  # WHY: default on; user can override via reboot toggle
        }
        # WHY: FR-017 verbatim final-strategy banner preserved from pre-refactor UI
        print(f"\n! Final strategy: Download={download_strategy.upper()}," f" Reboot={reboot_strategy.upper()}")
        logging.debug("init_upgrade_config committed keys=%s", len(self.upgrade_config))  # WHY: FR-007 debug-after

    def _configure_strategy_options(self) -> None:  # WHY: helper definition (see docstring)
        """Configure strategy-specific options."""
        if self.upgrade_config["download_strategy"] == "canary":  # WHY: guard on condition
            self._configure_canary_options()  # WHY: instance state
        if self.upgrade_config["reboot_strategy"] == "rrm":  # WHY: guard on condition
            self._configure_rrm_options()  # WHY: instance state

    def _configure_canary_options(self) -> None:  # WHY: helper definition (see docstring)
        """Configure canary strategy options."""
        print("\n  Canary Strategy Configuration:")  # WHY: user-facing feedback
        try:
            failure = self._input_fn("Max failure % (default=7): ").strip()  # WHY: capture intermediate value
            if failure:  # WHY: guard on condition
                self.upgrade_config["max_failure_percentage"] = int(failure)  # WHY: instance state
        except ValueError:  # WHY: recover from failure
            pass  # WHY: explicit no-op

    def _configure_rrm_options(self) -> None:  # WHY: helper definition (see docstring)
        """Configure RRM strategy options."""
        print("\n  RRM Strategy Configuration:")  # WHY: user-facing feedback
        self.upgrade_config["rrm_node_order"] = "fringe_to_center"  # WHY: instance state
        self.upgrade_config["rrm_first_batch_percentage"] = 2  # WHY: instance state
        self.upgrade_config["rrm_max_batch_percentage"] = 10  # WHY: instance state

    def _configure_p2p(self) -> None:  # WHY: helper definition (see docstring)
        """Configure P2P settings."""
        print("\n  Peer-to-Peer Configuration:")  # WHY: user-facing feedback
        enable = self._input_fn("Enable P2P firmware sharing? (Y/n): ").strip().lower()  # WHY: capture intermediate ...
        self.upgrade_config["enable_p2p"] = enable not in ["n", "no"]  # WHY: instance state
        if self.upgrade_config["enable_p2p"]:  # WHY: guard on condition
            print(" P2P enabled")  # WHY: user-facing feedback

    def _configure_scheduling(self) -> None:  # WHY: helper definition (see docstring)
        """Configure scheduling options."""
        print("\n  Scheduling Options:")  # WHY: user-facing feedback
        schedule = self._input_fn("Schedule for later? (y/N): ").strip().lower()  # WHY: capture intermediate value
        if schedule in ["y", "yes"]:  # WHY: guard on condition
            self._get_scheduled_time()  # WHY: instance state

    def _get_scheduled_time(self) -> None:  # WHY: helper definition (see docstring)
        """Get scheduled start time from user."""
        try:
            time_input = self._input_fn("Start time (+minutes or YYYY-MM-DD HH:MM): ").strip()  # WHY: capture interm...
            if time_input.startswith("+"):  # WHY: guard on condition
                minutes = int(time_input[1:])  # WHY: capture intermediate value
                self.upgrade_config["start_time"] = int(time.time()) + (minutes * 60)  # WHY: instance state
            else:
                dt = datetime.strptime(time_input, "%Y-%m-%d %H:%M")  # WHY: capture intermediate value
                self.upgrade_config["start_time"] = int(dt.timestamp())  # WHY: instance state
        except ValueError:  # WHY: recover from failure
            print(" Invalid format, scheduling immediately")  # WHY: user-facing feedback

    def _configure_force_option(self) -> None:  # WHY: helper definition (see docstring)
        """Configure force upgrade option."""
        force = self._input_fn("Force upgrade even if same version? (y/N): ").strip().lower()  # WHY: capture interme...
        self.upgrade_config["force"] = force in ["y", "yes"]  # WHY: instance state

    def _display_final_config(self) -> None:  # WHY: helper definition (see docstring)
        """Display final upgrade configuration."""
        print("\n  Final Configuration:")  # WHY: user-facing feedback
        print(f"Download Strategy: {self.upgrade_config['download_strategy'].upper()}")  # WHY: user-facing feedback
        print(f"Reboot Strategy: {self.upgrade_config['reboot_strategy'].upper()}")  # WHY: user-facing feedback
        print(f"P2P: {self.upgrade_config['enable_p2p']}")  # WHY: user-facing feedback
        print(f"Force: {self.upgrade_config['force']}")  # WHY: user-facing feedback

    # =========================================================================
    # STEP 7: CONFIRMATION
    # =========================================================================

    def _step7_confirm_upgrade(self) -> bool:  # WHY: helper definition (see docstring)
        """Display warnings and get user confirmation."""
        total = sum(len(p["devices"]) for p in self.upgrade_plan.values())  # WHY: capture intermediate value

        if len(self.sites_to_upgrade) > 1:  # WHY: guard on condition
            self._display_multi_site_summary()  # WHY: instance state

        self._display_upgrade_warnings()  # WHY: instance state
        self._display_final_plan()  # WHY: instance state
        self._display_api_call_estimate()  # WHY: instance state

        return self._get_upgrade_confirmation(total)  # WHY: surface computed result

    def _estimate_api_calls(self) -> dict[str, Any]:  # WHY: helper definition (see docstring)
        """PCPP orchestrator: group devices by site then compute call totals + breakdown."""
        # WHY: FR-007 info-before with total plan-model count for observability
        logging.info("estimate_api_calls plan_models=%s", len(self.upgrade_plan))  # WHY: info log (FR-007)
        # WHY: Compute step 1 — group all planned devices into per-site aggregates
        devices_by_site = self._group_plan_by_site()  # WHY: capture intermediate value
        # WHY: Compute step 2 — derive breakdown + total upgrade-call count from grouping
        upgrade_calls, breakdown = self._compute_upgrade_call_breakdown(devices_by_site)  # WHY: capture intermediate...
        result = {  # WHY: shape matches pre-refactor return contract consumed by _display_api_call_estimate
            "upgrade_calls": upgrade_calls,  # WHY: per-version-per-site upgrade POST count
            "auto_upgrade_calls": len(devices_by_site),  # WHY: one auto-upgrade config call per site
            "total_calls": upgrade_calls,  # WHY: alias retained for pre-refactor consumers
            "site_count": len(devices_by_site),  # WHY: site cardinality for banner display
            "breakdown": breakdown,  # WHY: per-site call breakdown list for verbose display
        }
        logging.debug(  # WHY: FR-007 debug-after with the two headline numbers
            "estimate_api_calls result upgrade_calls=%s site_count=%s",
            upgrade_calls,
            len(devices_by_site),
        )
        return result  # WHY: hand structured estimate to caller

    def _group_plan_by_site(self) -> dict[str, dict[str, Any]]:  # WHY: helper definition (see docstring)
        """Compute helper: fold self.upgrade_plan into a per-site aggregate dict."""
        # WHY: FR-007 info-before signals aggregation phase entry
        logging.info("group_plan_by_site start plan_models=%s", len(self.upgrade_plan))  # WHY: info log (FR-007)
        devices_by_site: dict[str, dict[str, Any]] = {}  # WHY: accumulator keyed by site_id
        for _model, plan in self.upgrade_plan.items():  # WHY: iterate models to reach their device lists
            version = plan["version"]  # WHY: version needed for per-site version cardinality tally
            for device in plan["devices"]:  # WHY: fold each device into its site's aggregate entry
                site_id = device.get("_site_id")  # WHY: annotation added earlier by _record_site_ap_result
                site_name = device.get("_site_name", "Unknown")  # WHY: friendly name for breakdown lines
                if site_id not in devices_by_site:  # WHY: seed a new aggregate entry on first hit
                    devices_by_site[site_id] = {
                        "name": site_name,  # WHY: preserved for output banners
                        "versions": set(),  # WHY: set eliminates duplicate versions within a site
                        "models": set(),  # WHY: set eliminates duplicate models within a site
                        "device_count": 0,  # WHY: incremented per device
                    }
                devices_by_site[site_id]["versions"].add(version)  # WHY: track unique target versions per site
                devices_by_site[site_id]["models"].add(_model)  # WHY: track unique models per site
                devices_by_site[site_id]["device_count"] += 1  # WHY: running total for the breakdown line
        logging.debug("group_plan_by_site result sites=%s", len(devices_by_site))  # WHY: FR-007 debug-after
        return devices_by_site  # WHY: caller uses this for both the total and the breakdown

    def _compute_upgrade_call_breakdown(  # WHY: helper definition (see docstring)
        self,
        devices_by_site: dict[str, dict[str, Any]],
    ) -> tuple[int, list[dict[str, Any]]]:
        """Compute helper: turn per-site aggregate dict into (total_calls, breakdown_list)."""
        logging.info("compute_upgrade_call_breakdown sites=%s", len(devices_by_site))  # WHY: FR-007 info-before
        upgrade_calls = 0  # WHY: running total of upgrade POSTs across sites
        breakdown: list[dict[str, Any]] = []  # WHY: per-site call rows for the display step
        for _site_id, site_info in devices_by_site.items():  # WHY: one iteration per site
            num_versions = len(site_info["versions"])  # WHY: call count equals distinct version count per site
            calls_for_site = num_versions  # WHY: one Mist upgradeSiteDevices call per (site, version) pair
            reason = "single version" if num_versions == 1 else f"{num_versions} versions"  # WHY: display copy
            upgrade_calls += calls_for_site  # WHY: aggregate site's contribution into total
            breakdown.append({  # WHY: preserve pre-refactor breakdown dict shape
                "site_name": site_info["name"],  # WHY: identifier column
                "devices": site_info["device_count"],  # WHY: how many devices this call block covers
                "calls": calls_for_site,  # WHY: per-site call count
                "reason": reason,  # WHY: human-readable reason string
            })
        logging.debug("compute_upgrade_call_breakdown calls=%s rows=%s", upgrade_calls, len(breakdown))  # WHY: FR-007
        return upgrade_calls, breakdown  # WHY: caller assembles the return payload

    def _display_api_call_estimate(self) -> None:  # WHY: helper definition (see docstring)
        """PCPP orchestrator: compute estimate, print headline, breakdown, and auto-upgrade note."""
        # WHY: FR-007 info-before signals API-call estimate display entry
        logging.info("display_api_call_estimate starting")  # WHY: info log (FR-007)
        estimate = self._estimate_api_calls()  # WHY: single call collects all display data
        self._print_api_call_headline(estimate)  # WHY: Present step 1 — headline totals
        # WHY: only render per-site breakdown when there is more than one call or site
        if estimate["site_count"] > 1 or estimate["upgrade_calls"] > 1:  # WHY: guard on condition
            self._print_api_call_breakdown(estimate["breakdown"])  # WHY: instance state
        print("  " + "-" * 50)  # WHY: closing separator preserved from pre-refactor UI
        # WHY: only render auto-upgrade note when auto-upgrade would add calls
        if estimate["auto_upgrade_calls"] > 0:  # WHY: guard on condition
            print(  # WHY: FR-017 verbatim auto-upgrade hint preserved
                f"   Note: If you configure auto-upgrade (Step 9),"
                f" add {estimate['auto_upgrade_calls']} more call(s)"
            )
        # WHY: FR-007 debug-after with total call count for traceability
        logging.debug(  # WHY: debug log (FR-007)
            "display_api_call_estimate result upgrade_calls=%s sites=%s",
            estimate["upgrade_calls"],
            estimate["site_count"],
        )

    def _print_api_call_headline(self, estimate: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Present helper: print the headline block of the API call estimate."""
        # WHY: FR-017 verbatim banner sequence preserved from pre-refactor UI
        print("\n  API Call Estimate:")  # WHY: user-facing feedback
        print("  " + "-" * 50)  # WHY: separator line matches pre-refactor styling
        print(f"   Upgrade API calls: {estimate['upgrade_calls']}")  # WHY: headline upgrade count
        print(f"   Sites to process: {estimate['site_count']}")  # WHY: headline site count

    def _print_api_call_breakdown(self, breakdown: list[dict[str, Any]]) -> None:  # WHY: helper definition (see docs...
        """Present helper: print per-site breakdown rows plus optional "more sites" tail."""
        print("\n   Breakdown by site:")  # WHY: FR-017 verbatim breakdown banner preserved
        for item in breakdown[:10]:  # WHY: cap at first 10 rows to match pre-refactor truncation policy
            print(  # WHY: FR-017 verbatim row format preserved
                f"     - {item['site_name']}: {item['calls']} call(s)"
                f" ({item['reason']}, {item['devices']} devices)"
            )
        if len(breakdown) > 10:  # WHY: summarize hidden rows when truncation occurred
            remaining = len(breakdown) - 10  # WHY: count of sites not individually shown
            remaining_calls = sum(b["calls"] for b in breakdown[10:])  # WHY: aggregate call count of tail
            # WHY: FR-017 verbatim "... and N more sites" line preserved
            print(f"     ... and {remaining} more sites" f" ({remaining_calls} additional calls)")  # WHY: user-facin...

    def _display_multi_site_summary(self) -> None:  # WHY: helper definition (see docstring)
        """Display comprehensive summary for multi-site upgrades (PCPP orchestrator)."""
        # WHY: FR-007 info-before with plan model count for observability
        logging.info(  # WHY: info log (FR-007)
            "Multi-site summary starting plan_models=%s skipped=%s",
            len(self.upgrade_plan),
            self.skipped_already_at_target,
        )
        # WHY: PCPP Present — banner introducing the site list section
        print("\n  Sites with APs to Upgrade:")  # WHY: user-facing feedback
        print("  " + "=" * 70)  # WHY: user-facing feedback
        # WHY: PCPP Compute — invert plan (per-model) into per-site aggregation
        site_summary = self._build_site_summary_index()  # WHY: capture intermediate value
        self._print_site_summary_rows(site_summary)  # WHY: PCPP Present — sorted rows
        self._print_site_summary_totals(site_summary)  # WHY: PCPP Present — totals footer
        logging.debug("Multi-site summary done sites=%s", len(site_summary))  # WHY: debug log (FR-007)

    def _build_site_summary_index(self) -> dict[str, dict[str, Any]]:  # WHY: helper definition (see docstring)
        """Invert the model-indexed upgrade_plan into a site-indexed summary dict."""
        # WHY: aggregation container maps site_name -> {models: {name: count}, total, version}
        site_summary: dict[str, dict[str, Any]] = {}  # WHY: capture intermediate value
        # WHY: iterate per-model plan entries and pivot devices under their originating site
        for model, plan in self.upgrade_plan.items():  # WHY: iterate collection
            target_version = plan["version"]  # WHY: capture target version for site record
            for device in plan["devices"]:  # WHY: each device carries its owning site name
                site_name = device.get("_site_name", "Unknown")  # WHY: fallback when annotation missing
                # WHY: lazy-init the per-site record on first device seen for this site
                if site_name not in site_summary:  # WHY: guard on condition
                    site_summary[site_name] = {  # WHY: capture intermediate value
                        "models": {},
                        "total": 0,
                        "version": target_version,
                    }
                # WHY: increment per-model AP count within this site's record
                site_summary[site_name]["models"].setdefault(model, 0)  # WHY: workflow step
                site_summary[site_name]["models"][model] += 1  # WHY: capture intermediate value
                site_summary[site_name]["total"] += 1  # WHY: bump aggregate device total for site
        return site_summary  # WHY: surface computed result

    def _print_site_summary_rows(self, site_summary: dict[str, dict[str, Any]]) -> None:  # WHY: helper definition (s...
        """Print one line per site in alphabetical order."""
        # WHY: sorted iteration keeps output deterministic across runs for CI comparison
        for site_name in sorted(site_summary.keys()):  # WHY: iterate collection
            info = site_summary[site_name]  # WHY: local alias for readability in f-string
            # WHY: comma-joined model:count pairs match the pre-refactor user-visible format
            model_str = ", ".join(f"{m}:{c}" for m, c in sorted(info["models"].items()))  # WHY: capture intermediate...
            print(f"   {site_name}: {info['total']} APs ({model_str})")  # WHY: user-facing feedback

    def _print_site_summary_totals(self, site_summary: dict[str, dict[str, Any]]) -> None:  # WHY: helper definition ...
        """Print the trailing totals + skipped-at-target line."""
        print("  " + "=" * 70)  # WHY: visual delimiter matches the leading rule for symmetry
        total_aps = sum(s["total"] for s in site_summary.values())  # WHY: aggregate device count
        print(f"   Total: {len(site_summary)} sites, {total_aps} APs")  # WHY: user-facing feedback
        # WHY: only mention skipped-at-target when non-zero to keep output tidy
        if self.skipped_already_at_target > 0:  # WHY: guard on condition
            print(f"   Skipped: {self.skipped_already_at_target}" " APs already at target version")  # WHY: user-faci...

    def _display_upgrade_warnings(self) -> None:  # WHY: helper definition (see docstring)
        """Display critical upgrade warnings."""
        print("\n" + "??" * 50)  # WHY: user-facing feedback
        if self.dry_run:  # WHY: guard on condition
            print(" DRY-RUN MODE - NO ACTUAL CHANGES WILL BE MADE")  # WHY: user-facing feedback
            print("??" * 50)  # WHY: user-facing feedback
            print(" This will simulate the firmware upgrade workflow:")  # WHY: user-facing feedback
        else:
            print(" CRITICAL WARNING - ADVANCED FIRMWARE UPGRADE:")  # WHY: user-facing feedback
        print("!? APs will REBOOT during upgrade")  # WHY: user-facing feedback
        print("!? Wi-Fi connectivity will be TEMPORARILY LOST")  # WHY: user-facing feedback
        print("!? Upgrades take 5-15 minutes per device")  # WHY: user-facing feedback
        print(f"!? Download Strategy:" f" {self.upgrade_config['download_strategy'].upper()}")  # WHY: user-facing fe...
        print(f"!? Reboot Strategy:" f" {self.upgrade_config['reboot_strategy'].upper()}")  # WHY: user-facing feedback
        print("??" * 50)  # WHY: user-facing feedback

    def _display_final_plan(self) -> None:  # WHY: helper definition (see docstring)
        """Display final upgrade plan."""
        print("\n  Final Plan:")  # WHY: user-facing feedback
        if len(self.sites_to_upgrade) > 1:  # WHY: guard on condition
            print(f"   Bulk upgrade: {len(self.sites_to_upgrade)} sites")  # WHY: user-facing feedback
        for model, plan in self.upgrade_plan.items():  # WHY: iterate collection
            print(f"   {model}: {len(plan['devices'])} devices" f" firmware {plan['version']}")  # WHY: user-facing f...

    def _get_upgrade_confirmation(self, total: int) -> bool:
        """Prompt user for UPGRADE confirmation token; return True on match."""
        sites_count = len({d.get("_site_id") for p in self.upgrade_plan.values() for d in p["devices"]})  # WHY: unique
        self._print_confirmation_prompt(total, sites_count)  # WHY: single- vs multi-site header
        try:  # WHY: consolidate Ctrl-C / EOF handling around one prompt
            confirm = self._input_fn(">>> ").strip()  # WHY: read raw confirmation token
        except (KeyboardInterrupt, EOFError):  # WHY: treat abort as cancellation
            return False  # WHY: caller stops workflow
        return self._interpret_confirmation(confirm, total, sites_count)  # WHY: decide accept/cancel

    def _print_confirmation_prompt(self, total: int, sites_count: int) -> None:
        """Print the confirmation banner (multi-site variant when applicable)."""
        if sites_count > 1:  # WHY: multi-site upgrade needs extra visibility
            print(f"\n  Type 'UPGRADE' to confirm upgrading {total} devices across {sites_count} sites:")
            return  # WHY: single header per call
        print(f"\n  Type 'UPGRADE' to confirm upgrading {total} devices:")  # WHY: user-facing feedback

    def _interpret_confirmation(self, confirm: str, total: int, sites_count: int) -> bool:
        """Return True if user typed the sentinel 'UPGRADE', otherwise False."""
        if confirm != "UPGRADE":  # WHY: require exact literal to reduce accidental confirmation
            print(" Upgrade cancelled.")  # WHY: user-facing feedback
            return False  # WHY: cancel decision
        print(" User confirmed. Proceeding...")  # WHY: user-facing feedback
        logging.info("User confirmed upgrade for %s devices across %s sites", total, sites_count)  # WHY: audit log
        return True  # WHY: accept decision

    # =========================================================================
    # STEP 8: EXECUTE UPGRADES
    # =========================================================================

    def _step8_execute_upgrades(self) -> None:
        """Execute firmware upgrades across all sites (PCPP orchestrator)."""
        import mistapi  # WHY: local import keeps module boot cheap
        print("\n  Starting firmware upgrade operations...")  # WHY: user-facing header
        print("=" * 60)  # WHY: visual separator
        sites_with_upgrades = self._prepare_sites_with_upgrades()  # WHY: filtered set + skip messaging
        if not sites_with_upgrades:  # WHY: nothing to do -> early return
            print("   No sites have devices needing upgrade - nothing to do")  # WHY: user-facing feedback
            return  # WHY: workflow terminates here
        for idx, (site_id, site_data) in enumerate(sites_with_upgrades.items(), 1):  # WHY: 1-based progress index
            self._execute_site_upgrade(idx, len(sites_with_upgrades), site_id, site_data, mistapi)  # WHY: per-site call

    def _prepare_sites_with_upgrades(self) -> dict[str, dict[str, Any]]:
        """Return only sites that still have devices to upgrade; log any skipped."""
        devices_by_site = self._organize_devices_by_site()  # WHY: group current plan by site
        sites_with_upgrades = {sid: data for sid, data in devices_by_site.items() if data["devices"]}  # WHY: non-empty
        skipped = len(devices_by_site) - len(sites_with_upgrades)  # WHY: count sites filtered out
        if skipped > 0:  # WHY: inform user why some sites were dropped
            print(f"   Skipping {skipped} site(s) with no devices needing upgrade")  # WHY: user-facing feedback
        return sites_with_upgrades  # WHY: surface filtered dict for iteration

    def _organize_devices_by_site(self) -> dict[str, dict[str, Any]]:  # WHY: helper definition (see docstring)
        """Organize upgrade plan devices by site."""
        devices_by_site: dict[str, dict[str, Any]] = {}  # WHY: capture intermediate value
        for model, plan in self.upgrade_plan.items():  # WHY: iterate collection
            for device in plan["devices"]:  # WHY: iterate collection
                site_id = device.get("_site_id")  # WHY: capture intermediate value
                site_name = device.get("_site_name")  # WHY: capture intermediate value
                if site_id not in devices_by_site:  # WHY: guard on condition
                    devices_by_site[site_id] = {  # WHY: capture intermediate value
                        "name": site_name,
                        "devices": [],
                        "models": {},
                    }
                devices_by_site[site_id]["devices"].append(device)  # WHY: workflow step
                if model not in devices_by_site[site_id]["models"]:  # WHY: guard on condition
                    devices_by_site[site_id]["models"][model] = {  # WHY: capture intermediate value
                        "version": plan["version"],
                        "devices": [],
                    }
                devices_by_site[site_id]["models"][model]["devices"].append(device)  # WHY: workflow step
        return devices_by_site  # WHY: surface computed result

    def _execute_site_upgrade(  # WHY: helper definition (see docstring)
        self,
        index: int,
        total: int,
        site_id: str,
        site_data: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Execute upgrade for a single site."""
        site_name = site_data["name"]  # WHY: capture intermediate value
        print(f"\n   Site {index}/{total}: {site_name}" f" ({len(site_data['devices'])} devices)")  # WHY: user-facin...

        try:
            versions = set(m["version"] for m in site_data["models"].values())  # WHY: capture intermediate value
            if len(versions) == 1:  # WHY: guard on condition
                self._execute_single_version_upgrade(site_id, site_name, site_data, mistapi)  # WHY: instance state
            else:
                self._execute_multi_version_upgrade(site_id, site_name, site_data, mistapi)  # WHY: instance state
            self._log_upgrade_results(site_id, site_name, site_data, "Upgrade Initiated")  # WHY: instance state
        except Exception as error:  # WHY: recover from failure
            print(f"      Failed: {error}")  # WHY: user-facing feedback
            self.failed_upgrades += len(site_data["devices"])  # WHY: instance state
            self._log_upgrade_results(site_id, site_name, site_data, f"ERROR: {error}")  # WHY: instance state

    def _execute_single_version_upgrade(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        site_data: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Execute upgrade when all devices use same version (PCPP orchestrator)."""
        logging.info("Single-version upgrade start site=%s n=%s", site_name, len(site_data["devices"]))  # WHY: FR-007
        version = next(iter(site_data["models"].values()))["version"]  # WHY: PCPP prepare, shared version
        device_ids = [d.get("id") for d in site_data["devices"] if d.get("id")]  # WHY: filter to concrete ids
        body = self._build_upgrade_body(version, device_ids)  # WHY: PCPP Compute build once
        if self.dry_run:  # WHY: dry-run branch skips mutating API call
            self._log_single_dry_run(site_name, version, device_ids, site_data)  # WHY: banner + counter bump
        else:
            self._post_single_version_upgrade(site_id, site_data, body, mistapi)  # WHY: real mistapi POST
        logging.debug("Single-version upgrade done site=%s total=%s", site_name, self.successful_upgrades)  # FR-007

    def _log_single_dry_run(  # WHY: helper definition (see docstring)
        self,
        site_name: str,
        version: str,
        device_ids: list[str | None],
        site_data: dict[str, Any],
    ) -> None:
        """Print dry-run banner + bump success counter (no API call)."""
        # WHY: user-visible dry-run banner mirrors pre-refactor format for FR-017 equivalence
        print(f"      [DRY-RUN] Would upgrade {len(device_ids)}" f" devices to {version}")  # WHY: user-facing feedback
        # WHY: preserved verbatim from pre-refactor log line to satisfy FR-017 observable equivalence
        logging.info(  # WHY: info log (FR-007)
            "DRY-RUN: Would call upgradeSiteDevices for site %s with %s devices",
            site_name,
            len(device_ids),
        )
        self.successful_upgrades += len(site_data["devices"])  # WHY: dry-run counts toward totals

    def _post_single_version_upgrade(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_data: dict[str, Any],
        body: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """POST the upgrade request, capture upgrade_id, print progress line."""
        # WHY: sole mutating call in this path — mistapi endpoint per Mist docs
        resp = mistapi.api.v1.sites.devices.upgradeSiteDevices(self.apisession, site_id, body=body)  # WHY: capture i...
        # WHY: capture upgrade_id when API returns dict payload so status-check step can poll it
        if hasattr(resp, "data") and resp.data and isinstance(resp.data, dict):  # WHY: guard on condition
            upgrade_id = resp.data.get("upgrade_id")  # WHY: defensively read key that may be absent
            if upgrade_id:  # WHY: only track and announce ids the API actually returned
                self.upgrade_ids.append(upgrade_id)  # WHY: retain for post-upgrade status polling
                print(f"      Upgrade initiated - ID: {upgrade_id}")  # WHY: CLI-visible confirmation
        self.successful_upgrades += len(site_data["devices"])  # WHY: bump aggregate success counter

    def _execute_multi_version_upgrade(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        site_data: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Execute upgrade when devices use different versions."""
        print("      Multiple versions - grouping by target version...")  # WHY: user-facing feedback

        devices_by_version: dict[str, dict[str, Any]] = {}  # WHY: capture intermediate value
        for model, model_info in site_data["models"].items():  # WHY: iterate collection
            version = model_info["version"]  # WHY: capture intermediate value
            if version not in devices_by_version:  # WHY: guard on condition
                devices_by_version[version] = {"devices": [], "models": []}  # WHY: capture intermediate value
            devices_by_version[version]["devices"].extend(model_info["devices"])  # WHY: workflow step
            devices_by_version[version]["models"].append(model)  # WHY: workflow step

        for version, version_info in devices_by_version.items():  # WHY: iterate collection
            self._upgrade_version_group(site_id, site_name, version, version_info, mistapi)  # WHY: instance state

    def _upgrade_version_group(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        version: str,
        version_info: dict[str, Any],
        mistapi: Any,
    ) -> None:
        """Upgrade a group of devices sharing the same target version (PCPP orchestrator)."""
        devices = version_info["devices"]  # WHY: extract group's device list from the tuple/dict
        models = version_info["models"]  # WHY: extract group's model set for progress banner text
        logging.info("Upgrade version group start site=%s v=%s n=%s", site_name, version, len(devices))  # WHY: FR-007
        device_ids = [d.get("id") for d in devices if d.get("id")]  # WHY: PCPP prepare concrete ids
        models_str = ", ".join(models)  # WHY: comma-joined model list for user-visible banner
        body = self._build_upgrade_body(version, device_ids)  # WHY: PCPP compute request body
        if self.dry_run:  # WHY: dry-run branch skips mutating API call
            self._log_dry_run_upgrade(version, site_name, models_str, devices, device_ids)  # WHY: banner path
        else:
            self._invoke_upgrade_api(site_id, version, models_str, devices, body)  # WHY: lazy mistapi call
        logging.debug("Upgrade group done site=%s v=%s total=%s", site_name, version, self.successful_upgrades)  # WHY

    def _log_dry_run_upgrade(  # WHY: helper definition (see docstring)
        self,
        version: str,
        site_name: str,
        models_str: str,
        devices: list[dict[str, Any]],
        device_ids: list[str | None],
    ) -> None:
        """Emit dry-run banner + counter bump for a version group (no API call)."""
        logging.info("Dry-run upgrade group v=%s site=%s n=%s", version, site_name, len(device_ids))  # WHY: FR-007
        print(f"         [DRY-RUN] {version}: Would upgrade {len(devices)} devices ({models_str})")  # FR-017 banner
        logging.info("DRY-RUN upgradeSiteDevices v=%s site=%s n=%s", version, site_name, len(device_ids))  # FR-007
        self.successful_upgrades += len(devices)  # WHY: dry-run still counts to summary totals
        logging.debug("Dry-run upgrade group done v=%s counted=%s", version, len(devices))  # WHY: FR-007 debug-after

    def _invoke_upgrade_api(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        version: str,
        models_str: str,
        devices: list[dict[str, Any]],
        body: dict[str, Any],
    ) -> None:
        """Post the upgrade request, capture upgrade_id, print progress line."""
        # WHY: FR-007 info-before naming the site + version being posted for audit trail
        logging.info("Invoke upgrade API site=%s version=%s devices=%s", site_id, version, len(devices))  # WHY: info...
        import mistapi  # WHY: lazy import matches other sites in this module and keeps param budget <=5
        # WHY: sole mutating call in this path — mistapi endpoint per Mist docs
        resp = mistapi.api.v1.sites.devices.upgradeSiteDevices(self.apisession, site_id, body=body)  # WHY: capture i...
        # WHY: capture upgrade_id when API returns dict payload so status-check step can poll it
        if hasattr(resp, "data") and resp.data and isinstance(resp.data, dict):  # WHY: guard on condition
            if "upgrade_id" in resp.data:  # WHY: some responses omit id (partial success); guard first
                self.upgrade_ids.append(resp.data["upgrade_id"])  # WHY: track for post-upgrade status
        self.successful_upgrades += len(devices)  # WHY: increment aggregate counter for summary
        # WHY: user-visible progress line mirrors pre-refactor format for FR-017 equivalence
        print(f"         + {version}: {len(devices)} devices ({models_str})")  # WHY: user-facing feedback
        logging.debug("Invoke upgrade API done site=%s version=%s ids=%s", site_id, version, len(self.upgrade_ids))

    def _build_upgrade_body(self, version: str, device_ids: list[str | None]) -> dict[str, Any]:  # WHY: helper defin...
        """Build upgrade API request body (PCPP orchestrator)."""
        # WHY: FR-007 info-before with version + device count so audit log matches API request
        logging.info(  # WHY: info log (FR-007)
            "Build upgrade body version=%s devices=%s strategy=%s",
            version,
            len(device_ids),
            self.upgrade_config.get("download_strategy"),
        )
        body = self._build_base_upgrade_body(version, device_ids)  # WHY: PCPP Compute — required fields
        self._augment_body_p2p(body)  # WHY: PCPP Compute — conditional P2P tunables layered in
        self._augment_body_canary(body)  # WHY: PCPP Compute — canary phase config when applicable
        self._augment_body_rrm(body)  # WHY: PCPP Compute — RRM-strategy fields only when strategy=rrm
        self._augment_body_start_time(body)  # WHY: PCPP Compute — scheduled start_time when set
        logging.debug("Build upgrade body done keys=%s", sorted(body.keys()))  # WHY: debug log (FR-007)
        return body  # WHY: surface computed result

    def _build_base_upgrade_body(  # WHY: helper definition (see docstring)
        self,
        version: str,
        device_ids: list[str | None],
    ) -> dict[str, Any]:
        """Return the always-present portion of the upgrade request body."""
        # WHY: single dict literal for the fields Mist API requires on every upgrade request
        return {  # WHY: surface computed result
            "download_strategy": self.upgrade_config["download_strategy"],
            "reboot_strategy": self.upgrade_config["reboot_strategy"],
            "force": self.upgrade_config["force"],
            "enable_p2p": self.upgrade_config["enable_p2p"],
            "max_failure_percentage": self.upgrade_config["max_failure_percentage"],
            "reboot": self.upgrade_config["reboot"],
            "version": version,
            "device_ids": device_ids,
        }

    def _augment_body_p2p(self, body: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Add p2p_cluster_size when P2P is enabled."""
        # WHY: p2p_cluster_size only makes sense when enable_p2p is True; guard against noise
        if self.upgrade_config["enable_p2p"]:  # WHY: guard on condition
            body["p2p_cluster_size"] = self.upgrade_config["p2p_cluster_size"]  # WHY: capture intermediate value

    def _augment_body_canary(self, body: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Add canary_phases when download or reboot strategy is canary."""
        # WHY: canary_phases required by API only when a canary strategy is selected
        if (  # WHY: guard on condition
            self.upgrade_config["download_strategy"] == "canary"
            or self.upgrade_config["reboot_strategy"] == "canary"
        ):
            body["canary_phases"] = self.upgrade_config["canary_phases"]  # WHY: capture intermediate value

    def _augment_body_rrm(self, body: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Add rrm_* tunables when reboot strategy is rrm."""
        # WHY: RRM fields only accepted by API when reboot_strategy == "rrm"; skip otherwise
        if self.upgrade_config["reboot_strategy"] != "rrm":  # WHY: guard on condition
            return  # WHY: early exit from branch
        # WHY: hard-coded key list mirrors pre-refactor logic; each field is optional per key
        for key in ("rrm_node_order", "rrm_first_batch_percentage", "rrm_max_batch_percentage"):  # WHY: iterate coll...
            if key in self.upgrade_config:  # WHY: only copy keys the user actually configured
                body[key] = self.upgrade_config[key]  # WHY: capture intermediate value

    def _augment_body_start_time(self, body: dict[str, Any]) -> None:  # WHY: helper definition (see docstring)
        """Add start_time when user configured a scheduled upgrade window."""
        # WHY: start_time absent for immediate upgrades; only inject when explicitly set
        if self.upgrade_config.get("start_time"):  # WHY: guard on condition
            body["start_time"] = self.upgrade_config["start_time"]  # WHY: capture intermediate value

    def _log_upgrade_results(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        site_data: dict[str, Any],
        status: str,
    ) -> None:
        """Log upgrade results for each device (PCPP Persist row appender)."""
        logging.info("Log upgrade results start site=%s n=%s status=%s", site_name, len(site_data["devices"]), status)
        effective_status = f"DRY-RUN: {status}" if self.dry_run else status  # WHY: PCPP compute effective label
        for device in site_data["devices"]:  # WHY: PCPP persist one row per device
            row = self._build_result_row(site_id, site_name, device, effective_status)  # WHY: build row payload
            self.results.append(row)  # WHY: accumulate rows for step 11 CSV export
        logging.debug("Log upgrade results done site=%s rows=%s", site_name, len(self.results))  # WHY: FR-007

    def _build_result_row(  # WHY: helper definition (see docstring)
        self,
        site_id: str,
        site_name: str,
        device: dict[str, Any],
        effective_status: str,
    ) -> dict[str, Any]:
        """Build one CSV result row from a single device + shared context."""
        target = self._get_device_target_version(device)  # WHY: resolve target version from plan
        device_id = device.get("id", "Unknown")  # WHY: fall back to sentinel when API omits id
        return {  # WHY: surface computed result
            "Site ID": site_id,
            "Site Name": site_name,
            "Device ID": device_id,
            "Device Name": device.get("name", "Unnamed"),
            "Device MAC": device.get("mac", "Unknown"),
            "Model": device.get("model", "Unknown"),
            "Current Version": self.ap_versions.get(device_id, "Unknown"),
            "Target Version": target,
            **self._upgrade_config_columns(),  # WHY: shared upgrade-config columns injected as one block
            "Upgrade ID": self._resolve_upgrade_id_column(),
            "Status": effective_status,
            "Timestamp": datetime.now(UTC).isoformat(),
        }

    def _upgrade_config_columns(self) -> dict[str, Any]:  # WHY: helper definition (see docstring)
        """Return the subset of CSV columns sourced from self.upgrade_config as a flat dict."""
        return {  # WHY: surface columns dict for row assembly
            "Download Strategy": self.upgrade_config["download_strategy"],  # WHY: preserve pre-refactor column
            "Reboot Strategy": self.upgrade_config["reboot_strategy"],  # WHY: preserve pre-refactor column
            "P2P Enabled": self.upgrade_config["enable_p2p"],  # WHY: preserve pre-refactor column
            "Max Failure %": self.upgrade_config["max_failure_percentage"],  # WHY: preserve pre-refactor column
            "Force Upgrade": self.upgrade_config["force"],  # WHY: preserve pre-refactor column
        }

    def _resolve_upgrade_id_column(self) -> str:  # WHY: helper definition (see docstring)
        """Pick the value for the Upgrade ID CSV column (real id, dry-run sentinel, or N/A)."""
        # WHY: pull last upgrade id when available; matches pre-refactor selection semantics
        if self.upgrade_ids:  # WHY: guard on condition
            return str(self.upgrade_ids[-1])  # WHY: surface computed result
        # WHY: dry-run runs never mutate; label sentinel distinguishes them from real N/A
        if self.dry_run:  # WHY: guard on condition
            return "N/A (DRY-RUN)"  # WHY: surface computed result
        return "N/A"  # WHY: no upgrade_id returned and not a dry-run; report unknown

    def _get_device_target_version(self, device: dict[str, Any]) -> str:  # WHY: helper definition (see docstring)
        """Get target version for a device."""
        for _model, plan in self.upgrade_plan.items():  # WHY: iterate collection
            if device in plan["devices"]:  # WHY: guard on condition
                target: str = str(plan["version"])  # WHY: capture intermediate value
                return target  # WHY: surface computed result
        return "Unknown"  # WHY: surface computed result

    # =========================================================================
    # STEP 9: AUTO-UPGRADE CONFIGURATION
    # =========================================================================

    def _fetch_ap_model_families(self) -> dict[str, list[str]]:  # WHY: helper definition (see docstring)
        """Fetch AP model families from Mist const/device_models API (Prepare -> Compute -> Present)."""
        logging.info("Fetching AP model families from Mist const/device_models")  # WHY: FR-007 info-before
        print("   Fetching AP model definitions from Mist API...")  # WHY: user-visible progress marker
        raw_models = self._request_device_models()  # WHY: Prepare — isolate the API call for error handling
        if raw_models is None:  # WHY: None sentinel signals request failure; empty list means real empty payload
            return {}  # WHY: surface computed result
        families = self._group_models_by_ap_type(raw_models)  # WHY: Compute — pure grouping over raw records
        logging.debug(
            "Fetched %s AP families with %s total models", len(families), sum(len(v) for v in families.values())
        )  # WHY: FR-007 debug-after summarises the aggregate result
        logging.info(
            "Fetched %s AP families with %s total models", len(families), sum(len(v) for v in families.values())
        )  # WHY: preserved verbatim from pre-refactor log line for FR-017 observable equivalence
        return families  # WHY: surface computed result

    def _request_device_models(self) -> list[Any] | None:  # WHY: helper definition (see docstring)
        """Prepare phase: call listDeviceModels and return raw list, or None on error."""
        try:
            # WHY: importlib defers the mistapi.const submodule import to first-use for menu-launch speed
            device_models_module = importlib.import_module("mistapi.api.v1.const.device_models")  # WHY: capture inte...
            list_device_models = device_models_module.listDeviceModels  # WHY: bind function once per call
            response = list_device_models(self.apisession)  # WHY: single API call fetches the org-wide model set
            all_models = getattr(response, "data", response) or []  # WHY: mistapi wraps payload in .data
            return all_models  # WHY: raw payload passed to Compute phase for filtering + grouping
        except Exception as error:  # noqa: BLE001  # WHY: network / import errors get logged, not raised
            logging.warning("Failed to fetch AP model families from API: %s", error)  # WHY: postmortem trail
            print("   Warning: Could not fetch AP models from API")  # WHY: user-visible fallback notice
            return None  # WHY: distinct from empty-list — signals request failure to caller

    def _group_models_by_ap_type(self, raw_models: list[Any]) -> dict[str, list[str]]:
        """Compute phase: filter to AP entries and group model names by ap_type."""
        ap_type_to_models: dict[str, list[str]] = {}  # WHY: accumulator keyed by chipset/generation
        for model_info in raw_models:  # WHY: iterate device_models records
            self._add_ap_model_to_group(model_info, ap_type_to_models)  # WHY: delegate per-record grouping
        return {ap_type: sorted(models) for ap_type, models in sorted(ap_type_to_models.items())}  # WHY: deterministic

    def _add_ap_model_to_group(self, model_info: Any, groups: dict[str, list[str]]) -> None:
        """Append AP model_info's model name to its ap_type bucket; skip non-AP or malformed."""
        if not isinstance(model_info, dict):  # WHY: skip unexpected payload shapes
            return  # WHY: defensive guard
        if model_info.get("type") != "ap":  # WHY: only APs matter to this workflow
            return  # WHY: skip non-AP records
        model_name = model_info.get("model", "")  # WHY: canonical model string
        if not model_name:  # WHY: skip records missing the mandatory model field
            return  # WHY: defensive guard
        ap_type = model_info.get("ap_type", "unknown")  # WHY: chipset family key
        groups.setdefault(ap_type, []).append(model_name)  # WHY: seed bucket + extend

    def _step9_configure_auto_upgrade(self) -> None:  # WHY: helper definition (see docstring)
        """Configure site auto-upgrade settings for ALL selected sites."""
        if not self.sites_to_upgrade:  # WHY: guard on condition
            return  # WHY: early exit from branch

        print("\n  Site Auto-Upgrade Configuration")  # WHY: user-facing feedback
        print("=" * 60)  # WHY: user-facing feedback
        print(f"   This will configure auto-upgrade for" f" {len(self.sites_to_upgrade)} site(s)")  # WHY: user-facin...
        print("   Auto-upgrade ensures new APs automatically upgrade" " to target firmware")  # WHY: user-facing feed...

        try:
            prompt = self._input_fn("\n  Configure site auto-upgrade? (Y/n): ").strip().lower()  # WHY: capture inter...
            if prompt in ["n", "no"]:  # WHY: guard on condition
                print("   Skipping auto-upgrade configuration")  # WHY: user-facing feedback
                return  # WHY: early exit from branch
        except (EOFError, KeyboardInterrupt):  # WHY: recover from failure
            return  # WHY: early exit from branch

        custom_versions = {model: plan["version"] for model, plan in self.upgrade_plan.items()}  # WHY: capture inter...
        custom_versions = self._offer_additional_model_versions(custom_versions)  # WHY: capture intermediate value
        schedule_config = self._configure_auto_upgrade_schedule()  # WHY: capture intermediate value
        self._apply_auto_upgrade_to_all_sites(custom_versions, schedule_config)  # WHY: instance state

    def _offer_additional_model_versions(self, custom_versions: dict[str, str]) -> dict[str, str]:  # WHY: helper def...
        """Offer to configure firmware versions for models not at sites (PCPP)."""
        logging.info(
            "Offering additional model versions (existing=%s)", len(custom_versions)
        )  # WHY: FR-007 info-before
        self._print_current_model_targets(custom_versions)  # WHY: Present — show current mapping to operator
        if not self._prompt_add_more_models():  # WHY: Prepare — decide whether we solicit additions at all
            logging.debug("Offer additional models declined by user")  # WHY: FR-007 debug-after (short path)
            return custom_versions  # WHY: surface computed result
        ap_families = self._fetch_ap_model_families()  # WHY: Prepare — need family map before offering choices
        if not ap_families:  # WHY: cannot proceed without a family catalog
            print("   Could not fetch AP model families from API")  # WHY: user-visible fallback notice
            logging.debug("Offer additional models aborted: no families")  # WHY: FR-007 debug-after
            return custom_versions  # WHY: surface computed result
        selected_families = self._prompt_family_selection(ap_families)  # WHY: Compute — parse operator picks
        if not selected_families:  # WHY: empty selection falls through unchanged
            print("   No families selected")  # WHY: user-visible confirmation of no-op path
            logging.debug("Offer additional models: no families selected")  # WHY: FR-007 debug-after
            return custom_versions  # WHY: surface computed result
        result = self._select_versions_by_family(custom_versions, selected_families)  # WHY: Persist choices
        logging.debug("Offer additional models done total=%s", len(result))  # WHY: FR-007 debug-after
        return result  # WHY: surface computed result

    def _print_current_model_targets(self, custom_versions: dict[str, str]) -> None:  # WHY: helper definition (see d...
        """Present phase: show current upgrade targets to the operator."""
        print("\n  Additional Model Configuration")  # WHY: section banner for the operator UI
        print("-" * 60)  # WHY: horizontal rule delimits the additional-model block
        print(f"   Current upgrade targets: {len(custom_versions)} model(s)")  # WHY: count before listing
        for model, version in sorted(custom_versions.items()):  # WHY: sorted for deterministic UI ordering
            print(f"      {model}: {version}")  # WHY: two-space indent aligns with parent banner

    def _prompt_add_more_models(self) -> bool:  # WHY: helper definition (see docstring)
        """Prepare phase: ask whether to add versions for other models."""
        try:
            add_more = self._input_fn("\n  Add firmware versions for other AP models? (y/N): ").strip().lower()
            return add_more in ("y", "yes")  # WHY: default answer is no; only explicit y/yes proceeds
        except (EOFError, KeyboardInterrupt):  # WHY: treat Ctrl+C/EOF as decline, matching pre-refactor behavior
            return False  # WHY: surface computed result

    def _prompt_family_selection(self, ap_families: dict[str, list[str]]) -> dict[str, list[str]]:  # WHY: helper def...
        """Compute phase: render family list and parse operator's selection string."""
        print(
            "\n  AP Model Families (select by family to set ONE version"
            " for all models in that family):"
        )  # WHY: banner explains that a single choice will apply to all models in each picked family
        print("-" * 60)  # WHY: horizontal rule delimits the family-picker block
        family_list = list(ap_families.items())  # WHY: freeze insertion order so numeric picks are stable
        for idx, (ap_type, models) in enumerate(family_list, 1):  # WHY: 1-based numbering for operator UI
            models_str = ", ".join(models)  # WHY: single-line preview of every model under this family
            print(f"   [{idx}] {ap_type}: {models_str}")  # WHY: family entry rendered as "[N] type: models"
        print("\n  Options:")  # WHY: help block clarifies acceptable input formats
        print("   - Enter family numbers (e.g., '1,3,5')" " - you will select ONE version per family")  # WHY: user-f...
        print("   - Enter 'all' to configure all AP model families")  # WHY: user-facing feedback
        print("   - Press Enter to skip")  # WHY: user-facing feedback
        try:
            selection = self._input_fn("\n  Selection: ").strip()  # WHY: single-line free-form input
            if not selection:  # WHY: empty selection is the documented skip path
                return {}  # WHY: surface computed result
        except (EOFError, KeyboardInterrupt):  # WHY: Ctrl+C/EOF treated as skip, matching pre-refactor
            return {}  # WHY: surface computed result
        return self._parse_family_selection(selection, family_list)  # WHY: reuse existing parser

    def _parse_family_selection(self, selection: str, family_list: list[tuple[str, list[str]]]) -> dict[str, list[str]]:
        """Parse user selection into dict of {ap_type: [models]}."""
        if selection.lower() == "all":  # WHY: sentinel token selects every family in original order
            return dict(family_list)  # WHY: convert list of pairs to dict directly
        selected: dict[str, list[str]] = {}  # WHY: accumulator preserves selection order
        for part in (p.strip() for p in selection.split(",")):  # WHY: iterate stripped tokens
            self._absorb_family_token(part, family_list, selected)  # WHY: delegate per-token parse
        return selected  # WHY: surface computed result

    def _absorb_family_token(
        self,
        part: str,
        family_list: list[tuple[str, list[str]]],
        selected: dict[str, list[str]],
    ) -> None:
        """Append family for one integer token; silently drop malformed/out-of-range tokens."""
        if not part.isdigit():  # WHY: only accept pure integer indices
            return  # WHY: match legacy silent-drop behavior
        idx = int(part) - 1  # WHY: convert 1-based UI index to 0-based
        if 0 <= idx < len(family_list):  # WHY: guard against out-of-range indices
            ap_type, models = family_list[idx]  # WHY: unpack family tuple
            selected[ap_type] = models  # WHY: persist family in accumulator

    def _select_versions_by_family(  # WHY: helper definition (see docstring)
        self,
        custom_versions: dict[str, str],
        selected_families: dict[str, list[str]],
    ) -> dict[str, str]:
        """Select ONE firmware version per family."""
        print("\n  Selecting firmware versions by family")  # WHY: user-facing feedback
        print("  (One version selection applies to ALL models in each family)")  # WHY: user-facing feedback
        print("-" * 60)  # WHY: user-facing feedback

        for ap_type, models in selected_families.items():  # WHY: iterate collection
            new_models = [m for m in models if m not in custom_versions]  # WHY: capture intermediate value
            self._select_version_for_family(ap_type, new_models, custom_versions)  # WHY: instance state

        return custom_versions  # WHY: surface computed result

    def _select_version_for_family(  # WHY: helper definition (see docstring)
        self,
        ap_type: str,
        new_models: list[str],
        custom_versions: dict[str, str],
    ) -> None:
        """PCPP orchestrator: gate on empty family, list versions, delegate to choice helper."""
        # WHY: FR-007 info-before with family and unconfigured-model count
        logging.info(  # WHY: info log (FR-007)
            "select_version_for_family start family=%s new_models=%s",
            ap_type,
            len(new_models),
        )
        if not new_models:  # WHY: skip families where every model already has a version chosen
            print(f"\n   {ap_type}: All models already configured - skipping")  # WHY: FR-017 verbatim
            logging.debug("select_version_for_family result=all_configured family=%s", ap_type)  # debug-after
            return  # WHY: nothing to prompt for
        # WHY: Present + Compute step — display family header and derive candidate list
        sorted_versions = self._present_family_candidates(ap_type, new_models)  # WHY: capture intermediate value
        if not sorted_versions:  # WHY: exit when no universal version exists for the family
            logging.debug("select_version_for_family result=no_universal family=%s", ap_type)  # debug-after
            return  # WHY: no candidates available to prompt for
        # WHY: Persist step delegated to helper that prompts and mutates custom_versions
        self._apply_family_version_choice(ap_type, new_models, sorted_versions, custom_versions)  # WHY: instance state
        logging.debug("select_version_for_family result=prompted family=%s", ap_type)  # WHY: debug-after

    def _present_family_candidates(self, ap_type: str, new_models: list[str]) -> list[str]:  # WHY: helper definition
        """Present + Compute: print family header and return top-10 sorted universal versions."""
        logging.info("present_family_candidates family=%s models=%s", ap_type, len(new_models))  # WHY: FR-007
        print(f"\n   Family: {ap_type}")  # WHY: FR-017 verbatim header
        print(f"   Models: {', '.join(new_models)}")  # WHY: model list echo preserved verbatim
        universal = self._find_universal_versions_for_models(set(new_models))  # WHY: intersection across models
        if not universal:  # WHY: no version supports every model in the family
            print(f"   ! No universal version found for all models in {ap_type}")  # WHY: FR-017 verbatim
            logging.debug("present_family_candidates result=none family=%s", ap_type)  # WHY: FR-007 debug-after
            return []  # WHY: caller handles empty list as skip
        sorted_versions = sorted(universal, key=self._version_sort_key, reverse=True)[:10]  # WHY: newest first
        print(f"   Available versions (compatible with ALL {len(new_models)} models):")  # WHY: FR-017 verbatim
        for idx, version in enumerate(sorted_versions, 1):  # WHY: number choices 1..N for prompt
            print(f"      [{idx}] {version}")  # WHY: FR-017 verbatim choice row format
        logging.debug("present_family_candidates count=%s family=%s", len(sorted_versions), ap_type)  # WHY: FR-007
        return sorted_versions  # WHY: caller uses this list to bound the prompt range

    def _apply_family_version_choice(  # WHY: helper definition (see docstring)
        self,
        ap_type: str,
        new_models: list[str],
        sorted_versions: list[str],
        custom_versions: dict[str, str],
    ) -> None:
        """PCPP orchestrator: prompt user, validate choice, delegate write to persistence helper."""
        logging.info("apply_family_version_choice family=%s n=%s", ap_type, len(sorted_versions))  # WHY: FR-007
        try:  # WHY: swallow input/EOF interruptions to keep menu resilient
            choice = self._prompt_family_choice(ap_type, len(sorted_versions))  # WHY: Present + Compute
            if choice == "s":  # WHY: user opts to skip this family entirely
                print(f"   Skipped {ap_type}")  # WHY: FR-017 verbatim skip echo
                logging.debug("apply_family_version_choice result=skipped family=%s", ap_type)  # WHY: FR-007
                return  # WHY: no state to persist for a skip
            if choice.isdigit():  # WHY: only numeric choices map to a version selection
                self._commit_family_version(ap_type, new_models, sorted_versions, custom_versions, choice)  # persist
        except (EOFError, KeyboardInterrupt, ValueError):  # WHY: preserve pre-refactor lenient error handling
            pass  # WHY: silent no-op keeps UX identical
        logging.debug("apply_family_version_choice complete family=%s", ap_type)  # WHY: FR-007 debug-after

    def _prompt_family_choice(self, ap_type: str, num_candidates: int) -> str:  # WHY: helper definition (see docstring)
        """Present + Compute: read user's family-version choice as a lowercase string."""
        # WHY: FR-007 info-before with family and candidate count
        logging.info("prompt_family_choice family=%s candidates=%s", ap_type, num_candidates)  # WHY: info log (FR-007)
        # WHY: prompt string built via f-string concatenation to stay under E501 line limit
        prompt = f"\n   Select version for {ap_type} (1-{num_candidates}), 's' to skip: "  # WHY: capture intermediat...
        raw = self._input_fn(prompt)  # WHY: single injected input call keeps testability
        choice = raw.strip().lower()  # WHY: normalize to lowercase for 's' skip comparison
        logging.debug("prompt_family_choice raw=%r family=%s", choice, ap_type)  # WHY: FR-007 debug-after
        return choice  # WHY: caller inspects for 's' or digit

    def _commit_family_version(  # WHY: helper definition (see docstring)
        self,
        ap_type: str,
        new_models: list[str],
        sorted_versions: list[str],
        custom_versions: dict[str, str],
        choice: str,
    ) -> None:
        """Persist helper: validate numeric choice and copy chosen version into custom_versions."""
        # WHY: FR-007 info-before with family and raw choice for traceability
        logging.info("commit_family_version family=%s choice=%s", ap_type, choice)  # WHY: info log (FR-007)
        idx = int(choice) - 1  # WHY: convert 1-based menu index into 0-based list index
        if 0 <= idx < len(sorted_versions):  # WHY: bounds-check protects against out-of-range input
            selected_version = sorted_versions[idx]  # WHY: fetch the chosen version string
            for model in new_models:  # WHY: fan out chosen version to every model in the family
                custom_versions[model] = selected_version  # WHY: mutate shared dict passed by caller
            print(f"   -> Applied {selected_version}" f" to: {', '.join(new_models)}")  # WHY: FR-017 verbatim echo
        logging.debug("commit_family_version done family=%s", ap_type)  # WHY: FR-007 debug-after

    def _find_universal_versions_for_models(self, models: set[str]) -> list[str]:
        """Find firmware versions compatible with all specified models."""
        version_to_compatible = self._index_version_compatibility()  # WHY: build reverse index once
        return [v for v, compatible in version_to_compatible.items() if models.issubset(compatible)]  # WHY: filter

    def _index_version_compatibility(self) -> dict[str, set[str]]:
        """Aggregate every available-versions entry into {version: {supported_models}}."""
        version_to_compatible: dict[str, set[str]] = {}  # WHY: version-string -> set of supported models
        for version_info in self.available_versions:  # WHY: single pass over API entries
            self._absorb_version_compatibility(version_info, version_to_compatible)  # WHY: delegate per-entry merge
        return version_to_compatible  # WHY: surface completed index

    def _absorb_version_compatibility(
        self,
        version_info: Any,
        version_to_compatible: dict[str, set[str]],
    ) -> None:
        """Merge one available-versions entry into the reverse index (skip malformed)."""
        if not isinstance(version_info, dict):  # WHY: defensive skip against non-dict payloads
            return  # WHY: FR-011 no wrappers -> just drop malformed rows
        version = version_info.get("version", "")  # WHY: version string is the index key
        if not version:  # WHY: entries without a version string are unusable
            return  # WHY: skip empty-version rows
        entry_models = set(version_info.get("models", []))  # WHY: multi-model entries carry a list
        single = version_info.get("model")  # WHY: legacy entries carry a scalar model field
        if single:  # WHY: fold scalar into the entry's set
            entry_models.add(single)  # WHY: unify shapes for downstream subset check
        version_to_compatible.setdefault(version, set()).update(entry_models)  # WHY: safe union per version

    def _version_sort_key(self, version_string: str) -> list[int | str]:  # WHY: helper definition (see docstring)
        """Create sort key for semantic version ordering."""
        try:
            parts: list[int | str] = []  # WHY: capture intermediate value
            for part in version_string.split("."):  # WHY: iterate collection
                try:
                    parts.append(int(part))  # WHY: workflow step
                except ValueError:  # WHY: recover from failure
                    parts.append(part.lower())  # WHY: workflow step
            return parts  # WHY: surface computed result
        except Exception:  # WHY: recover from failure
            return [version_string.lower()]  # WHY: surface computed result

    def _configure_auto_upgrade_schedule(self) -> dict[str, str]:  # WHY: helper definition (see docstring)
        """Configure auto-upgrade scheduling options (day + time-of-day)."""
        logging.info("Configuring auto-upgrade schedule (day + time)")  # WHY: FR-007 info-before
        schedule: dict[str, str] = {}  # WHY: accumulator for the two schedule keys we ultimately return
        self._print_schedule_banner()  # WHY: Present — one-time UI header before either prompt
        schedule["day_of_week"] = self._prompt_schedule_day()  # WHY: Prepare/Compute — day pick, default any
        schedule["time_of_day"] = self._prompt_schedule_time()  # WHY: Prepare/Compute — time pick, default any
        logging.debug(
            "Schedule configured day=%s time=%s", schedule["day_of_week"], schedule["time_of_day"]
        )  # WHY: FR-007 debug-after summarising the chosen schedule
        return schedule  # WHY: surface computed result

    def _print_schedule_banner(self) -> None:  # WHY: helper definition (see docstring)
        """Present phase: render the auto-upgrade schedule section header."""
        print("\n  Auto-Upgrade Scheduling")  # WHY: banner announces the schedule block to the operator
        print("-" * 60)  # WHY: horizontal rule visually separates the block from prior UI
        print("   Configure when auto-upgrades should occur")  # WHY: one-line intent statement

    def _prompt_schedule_day(self) -> str:
        """Prepare phase: prompt operator to pick a day-of-week; default 'any'."""
        days = ["any", "mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # WHY: 8 slots, index 0 = any
        self._print_schedule_day_menu(days)  # WHY: extract menu rendering
        try:  # WHY: consolidate parse + interrupt handling
            day_choice = self._input_fn("\n  Select day (0-7, default=0 any): ").strip() or "0"  # WHY: default 0
        except (EOFError, KeyboardInterrupt):  # WHY: any interrupt means fall back to default
            return "any"  # WHY: surface computed result
        return self._resolve_schedule_day(day_choice, days)  # WHY: delegate index -> day-string mapping

    def _print_schedule_day_menu(self, days: list[str]) -> None:
        """Render numbered day-of-week options with the default highlighted."""
        print("\n  Day of week options:")  # WHY: menu label
        print("   [0] any (default)")  # WHY: document default explicitly
        for idx, day in enumerate(days[1:], 1):  # WHY: skip index 0 -> already rendered
            print(f"   [{idx}] {day}")  # WHY: render each real day option

    def _resolve_schedule_day(self, day_choice: str, days: list[str]) -> str:
        """Map digit input to canonical day string; anything else -> 'any'."""
        if day_choice.isdigit() and 0 <= int(day_choice) < len(days):  # WHY: bounds check before index
            return days[int(day_choice)]  # WHY: numeric pick maps to canonical day string
        return "any"  # WHY: invalid input silently falls back to default

    def _prompt_schedule_time(self) -> str:  # WHY: helper definition (see docstring)
        """Prepare phase: prompt operator to pick HH:MM or 'any'; default 'any'."""
        print("\n  Time of day (24-hour format HH:MM, or 'any'):")  # WHY: input format guidance
        print("   Examples: 02:00 (2 AM), 14:00 (2 PM), any")  # WHY: concrete examples reduce operator error
        try:
            time_input = self._input_fn("   Enter time (default=any): ").strip() or "any"  # WHY: default any
            if time_input.lower() == "any":  # WHY: explicit 'any' means no schedule constraint
                return "any"  # WHY: surface computed result
            if ":" in time_input:  # WHY: minimal HH:MM shape check; API validates the exact format
                return time_input  # WHY: surface computed result
            return "any"  # WHY: fallback for malformed strings without a colon
        except (EOFError, KeyboardInterrupt):  # WHY: Ctrl+C/EOF matches the pre-refactor 'any' default
            return "any"  # WHY: surface computed result

    def _apply_auto_upgrade_to_all_sites(self, custom_versions: dict[str, str], schedule: dict[str, str]) -> None:
        """Apply auto-upgrade configuration to ALL selected sites."""
        import mistapi  # WHY: required module import

        print(f"\n  Applying Auto-Upgrade to" f" {len(self.sites_to_upgrade)} Site(s)")  # WHY: user-facing feedback
        print("=" * 60)  # WHY: user-facing feedback

        settings = {"auto_upgrade": self._build_auto_upgrade_settings(custom_versions, schedule)}  # WHY: capture int...

        successful, failed = self._apply_settings_to_sites(settings, mistapi)  # WHY: capture intermediate value

        self._print_auto_upgrade_summary(successful, failed, custom_versions, schedule)  # WHY: instance state

    def _build_auto_upgrade_settings(self, custom_versions: dict[str, str], schedule: dict[str, str]) -> dict[str, Any]:
        """Build auto-upgrade settings payload."""
        auto_upgrade: dict[str, Any] = {  # WHY: capture intermediate value
            "enabled": True,
            "version": "custom",
            "custom_versions": custom_versions,
        }

        if schedule.get("day_of_week") and schedule["day_of_week"] != "any":  # WHY: guard on condition
            auto_upgrade["day_of_week"] = schedule["day_of_week"]  # WHY: capture intermediate value
        if schedule.get("time_of_day") and schedule["time_of_day"] != "any":  # WHY: guard on condition
            auto_upgrade["time_of_day"] = schedule["time_of_day"]  # WHY: capture intermediate value

        return auto_upgrade  # WHY: surface computed result

    def _apply_settings_to_sites(self, settings: dict[str, Any], mistapi: Any) -> tuple[int, int]:  # WHY: helper def...
        """Apply settings to each site, returning (successful, failed) counts."""
        successful = 0  # WHY: capture intermediate value
        failed = 0  # WHY: capture intermediate value

        for site in self.sites_to_upgrade:  # WHY: iterate collection
            if self._check_stop_fn and self._check_stop_fn():  # WHY: guard on condition
                break  # WHY: terminate loop
            site_id = site["id"]  # WHY: capture intermediate value
            site_name = site["name"]  # WHY: capture intermediate value

            try:
                mistapi.api.v1.sites.setting.updateSiteSettings(self.apisession, site_id, body=settings)  # WHY: capt...
                print(f"   [OK] {site_name}")  # WHY: user-facing feedback
                successful += 1  # WHY: capture intermediate value
            except Exception as error:  # WHY: recover from failure
                print(f"   [FAIL] {site_name}: {error}")  # WHY: user-facing feedback
                logging.error("Failed to configure auto-upgrade for site %s: %s", site_name, error)  # WHY: error log
                failed += 1  # WHY: capture intermediate value

        return successful, failed  # WHY: surface computed result

    def _print_auto_upgrade_summary(  # WHY: helper definition (see docstring)
        self,
        successful: int,
        failed: int,
        custom_versions: dict[str, str],
        schedule: dict[str, str],
    ) -> None:
        """Print auto-upgrade configuration summary."""
        print("\n  Auto-Upgrade Configuration Complete:")  # WHY: user-facing feedback
        print(f"   Successful: {successful} site(s)")  # WHY: user-facing feedback
        if failed > 0:  # WHY: guard on condition
            print(f"   Failed: {failed} site(s)")  # WHY: user-facing feedback
        print(f"   Models configured: {len(custom_versions)}")  # WHY: user-facing feedback
        for model, version in sorted(custom_versions.items()):  # WHY: iterate collection
            print(f"      {model}: {version}")  # WHY: user-facing feedback
        if schedule.get("day_of_week") != "any" or schedule.get("time_of_day") != "any":  # WHY: guard on condition
            print(f"   Schedule: {schedule.get('day_of_week', 'any')}" f" at {schedule.get('time_of_day', 'any')}")

    # =========================================================================
    # STEP 10: STATUS CHECK
    # =========================================================================

    def _step10_offer_status_check(self) -> None:  # WHY: helper definition (see docstring)
        """Offer to check upgrade status."""
        if self.successful_upgrades == 0:  # WHY: guard on condition
            return  # WHY: early exit from branch

        print("\n Firmware upgrades initiated successfully!")  # WHY: user-facing feedback
        print(f"   {self.successful_upgrades} upgrades started")  # WHY: user-facing feedback

        self._save_upgrade_tracking()  # WHY: instance state

        print("\n Reminder: Monitor progress using menu option 60")  # WHY: user-facing feedback
        try:
            check = self._input_fn("\n Check upgrade status now? (y/n): ").strip().lower()  # WHY: capture intermedia...
            if check in ["y", "yes"] and self._check_firmware_status_fn:  # WHY: guard on condition
                self._check_firmware_status_fn()  # WHY: instance state
        except (EOFError, KeyboardInterrupt):  # WHY: recover from failure
            pass  # WHY: explicit no-op

    def _save_upgrade_tracking(self) -> None:  # WHY: helper definition (see docstring)
        """PCPP orchestrator: guard on empty state, load, append entries, persist to disk."""
        # WHY: FR-007 info-before with upgrade ID count for observability
        logging.info("save_upgrade_tracking start upgrade_ids=%s", len(self.upgrade_ids))  # WHY: info log (FR-007)
        if not self.upgrade_ids:  # WHY: nothing to persist when no upgrades were initiated
            logging.debug("save_upgrade_tracking result=noop reason=no_upgrade_ids")  # WHY: FR-007 debug-after
            return  # WHY: skip file I/O when there is no state to save
        try:  # WHY: swallow disk errors so a tracking failure never breaks the upgrade run
            tracking_file = "ActiveUpgrades.json"  # WHY: fixed filename shared with other tracking tools
            tracking_data = self._load_existing_tracking(tracking_file)  # WHY: preserve prior entries on append
            # WHY: Compute step — extend tracking with one row per new upgrade ID
            self._append_upgrade_tracking_entries(tracking_data)  # WHY: instance state
            self._write_tracking_file(tracking_file, tracking_data)  # WHY: Persist step writes JSON back
        except Exception as error:  # WHY: broad catch matches pre-refactor behavior for FR-017 parity
            logging.warning("Failed to save tracking: %s", error)  # WHY: non-fatal warning per pre-refactor
        logging.debug("save_upgrade_tracking complete")  # WHY: FR-007 debug-after

    def _load_existing_tracking(self, tracking_file: str) -> list[dict[str, Any]]:  # WHY: helper definition (see doc...
        """Prepare helper: read ActiveUpgrades.json if present, otherwise return empty list."""
        # WHY: FR-007 info-before with target file for traceability
        logging.info("load_existing_tracking file=%s", tracking_file)  # WHY: info log (FR-007)
        tracking_data: list[dict[str, Any]] = []  # WHY: default empty list when file does not yet exist
        if os.path.exists(tracking_file):  # WHY: only attempt read when the file is present
            with open(tracking_file, encoding="utf-8") as fh:  # WHY: utf-8 matches write side
                tracking_data = json.load(fh)  # WHY: preserve pre-refactor JSON shape verbatim
        logging.debug("load_existing_tracking rows=%s", len(tracking_data))  # WHY: FR-007 debug-after
        return tracking_data  # WHY: caller extends this list in place

    def _append_upgrade_tracking_entries(self, tracking_data: list[dict[str, Any]]) -> None:  # WHY: helper definitio...
        """Compute helper: append one tracking entry per current upgrade ID."""
        # WHY: FR-007 info-before with current upgrade ID count
        logging.info("append_upgrade_tracking_entries new=%s", len(self.upgrade_ids))  # WHY: info log (FR-007)
        for upgrade_id in self.upgrade_ids:  # WHY: one row per successful Mist upgrade POST
            tracking_data.append(  # WHY: preserves pre-refactor row shape for FR-017 parity
                {
                    "upgrade_id": upgrade_id,  # WHY: primary key used by ActiveUpgrades tooling
                    "org_id": self.org_id,  # WHY: scope entry to its Mist org
                    "download_strategy": self.upgrade_config.get("download_strategy", ""),  # WHY: audit copy
                    "reboot_strategy": self.upgrade_config.get("reboot_strategy", ""),  # WHY: audit copy
                    "timestamp": datetime.now(UTC).isoformat(),  # WHY: UTC ISO-8601 for cross-system parity
                    "status": "initiated",  # WHY: matches pre-refactor initial status token
                }
            )
        logging.debug("append_upgrade_tracking_entries done rows=%s", len(tracking_data))  # WHY: debug-after

    def _write_tracking_file(self, tracking_file: str, tracking_data: list[dict[str, Any]]) -> None:  # WHY: helper d...
        """Persist helper: overwrite ActiveUpgrades.json with the extended tracking list."""
        # WHY: FR-007 info-before with file + row count
        logging.info("write_tracking_file file=%s rows=%s", tracking_file, len(tracking_data))  # WHY: info log (FR-007)
        with open(tracking_file, "w", encoding="utf-8") as fh:  # WHY: utf-8 explicit for cross-platform safety
            json.dump(tracking_data, fh, indent=2)  # WHY: indent=2 preserves human-readable form
        logging.debug("write_tracking_file complete file=%s", tracking_file)  # WHY: FR-007 debug-after

    # =========================================================================
    # STEP 11: WRITE RESULTS
    # =========================================================================

    # WHY: canonical column order for AdvancedAPFirmwareUpgrade CSV (FR-017 observable contract)
    _RESULTS_CSV_FIELDS: tuple[str, ...] = (  # WHY: capture intermediate value
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
    )

    def _step11_write_results(self) -> None:  # WHY: helper definition (see docstring)
        """Write upgrade results to CSV (Prepare -> Persist -> Present)."""
        # WHY: FR-007 info-before with row count and dry-run flag for observability
        logging.info(  # WHY: info log (FR-007)
            "Step 11 write_results starting rows=%s dry_run=%s",
            len(self.results),
            self.dry_run,
        )
        if not self.results:  # WHY: nothing to write when no upgrade attempts recorded
            return  # WHY: early exit from branch
        filename = self._build_results_filename()  # WHY: PCPP Prepare — path derived from first site + timestamp
        wrote = self._write_results_csv(filename)  # WHY: PCPP Persist — CSV write isolated for testability
        if wrote:  # WHY: only display success banners when persistence actually succeeded
            self._display_results_summary(filename)  # WHY: PCPP Present — user-visible completion summary
        logging.debug("Step 11 write_results done wrote=%s file=%s", wrote, filename)  # WHY: FR-007 debug-after

    def _build_results_filename(self) -> str:  # WHY: helper definition (see docstring)
        """Compose the results CSV path from first site + timestamp + dry-run tag."""
        # WHY: use first site name so CSV filename tracks the primary upgrade target
        site_name = self.sites_to_upgrade[0]["name"] if self.sites_to_upgrade else "Unknown"  # WHY: capture intermed...
        dry_run_suffix = "_DRYRUN" if self.dry_run else ""  # WHY: distinguishes rehearsal output from real runs
        # WHY: os.path.join keeps Windows/Unix separators portable per Constitution
        return os.path.join(  # WHY: surface computed result
            "data",
            f"AdvancedAPFirmwareUpgrade_{site_name.replace(' ', '_')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f"{dry_run_suffix}.csv",
        )

    def _write_results_csv(self, filename: str) -> bool:  # WHY: helper definition (see docstring)
        """Persist self.results to CSV; return True on success."""
        try:
            # WHY: newline="" required by csv module to avoid double line endings on Windows
            with open(filename, "w", newline="", encoding="utf-8") as fp:  # WHY: scoped resource
                writer = csv.DictWriter(fp, fieldnames=list(self._RESULTS_CSV_FIELDS))  # WHY: fixed schema
                writer.writeheader()  # WHY: header row is required for downstream consumers
                writer.writerows(self.results)  # WHY: bulk-write pre-computed row dicts
            return True  # WHY: signals caller that persistence succeeded and Present phase may run
        except Exception as error:  # noqa: BLE001  # WHY: any I/O failure must be reported, not crashed on
            print(f"! Failed to write results: {error}")  # WHY: operator-facing surface for CSV write failure
            logging.warning("Failed to write results CSV %s: %s", filename, error)  # WHY: keep for postmortem
            return False  # WHY: caller uses this to skip the success banner path

    def _display_results_summary(self, filename: str) -> None:  # WHY: helper definition (see docstring)
        """Print the run-completion banner referring to the just-written CSV."""
        if self.dry_run:  # WHY: dry-run banner emphasizes no APIs were actually invoked
            print("\n  DRY-RUN Complete - No actual upgrades performed!")  # WHY: user-facing feedback
            print(f"   Would have upgraded: {self.successful_upgrades} devices")  # WHY: user-facing feedback
        else:  # WHY: real-run banner shows success/fail counts to the operator
            print("\n  Advanced Firmware Upgrade Completed!")  # WHY: user-facing feedback
            print(f"   Successful: {self.successful_upgrades}")  # WHY: user-facing feedback
            print(f"   Failed: {self.failed_upgrades}")  # WHY: user-facing feedback
        print(f"   Results: {filename}")  # WHY: operator needs the CSV path to review the run
        logging.info("Upgrade results written to %s", filename)  # WHY: audit trail for support/debug
