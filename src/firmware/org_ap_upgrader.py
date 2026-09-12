"""Org-level AP firmware upgrade operations for Mist organizations.

Uses the upgradeOrgDevices API (POST /api/v1/orgs/{org_id}/devices/upgrade)
for massive efficiency improvements when upgrading APs across many sites.

Extracted from MistHelper.py for maintainability.
"""

from __future__ import annotations  # WHY: import required module

import importlib  # WHY: dynamic mistapi module loading avoids top-level import cycles
import logging  # WHY: structured info/debug logging bracketing every observable operation
import os  # WHY: os.path.join for portable filesystem path construction
import re  # WHY: regex parsing for time/version/canary input strings
from dataclasses import dataclass  # WHY: frozen slots dataclass collapses 11-param __init__
from datetime import UTC, datetime, timedelta  # WHY: UTC-aware time math for upgrade scheduling
from typing import Any  # WHY: Any typing for injected callables and API session handle


@dataclass(frozen=True, slots=True, kw_only=True)  # WHY: frozen+slots+kw_only per data-model.md contract
class OrgAPUpgraderConfig:  # WHY: declare OrgAPUpgraderConfig class
    """Immutable configuration object for OrgLevelAPFirmwareUpgrader.

    Collapses the pre-refactor 11-parameter __init__ into a single internal
    value object built from the kwargs the four MistHelper.py callsites
    already pass. Satisfies STRUCT-PARAMS (threshold 5) with a formal count
    of 1 (the __init__ signature becomes ``def __init__(self, **cfg)``).

    All six *_fn hooks are Optional. The class supplies sensible defaults
    (matching pre-refactor `_default_*` fallbacks) when None is provided.
    ``msp_privileges`` and ``selected_msp`` accept None for the org-mode
    entry points (callsites at lines 20247/20269) and are set to real
    values for the MSP-mode paths (callsites at lines 20289/20305).
    """

    org_id: str  # WHY: organization scope (empty string permitted at MSP-select callsites)
    apisession: Any  # WHY: Mist API session used for every HTTP call (never None)
    dry_run: bool = False  # WHY: preview-only toggle. No upgrades committed when True
    safe_input_fn: Any | None = None  # WHY: injected safe_input helper (None -> default)
    check_stop_fn: Any | None = None  # WHY: cooperative-cancel probe (None -> no-op)
    get_org_id_fn: Any | None = None  # WHY: resolves org id from prompt / cache (None -> default)
    fetch_sites_fn: Any | None = None  # WHY: site streamer for site-scope selection (None -> default)
    write_results_fn: Any | None = None  # WHY: CSV persister for per-phase results (None -> default)
    is_debug_fn: Any | None = None  # WHY: verbose-logging predicate (None -> constant False)
    msp_privileges: list[Any] | None = None  # WHY: MSP orgs list (None normalized to [])
    selected_msp: dict[str, Any] | None = None  # WHY: pre-selected MSP payload (name + id)

    def __post_init__(self) -> None:  # WHY: declare private helper __post_init__
        """Validate every field per data-model.md validation-rules table."""
        logging.info("Validating OrgAPUpgraderConfig for org %s", self.org_id)  # WHY: bracket-open trace
        self._validate_identity()  # WHY: enforce str org_id + non-None apisession
        object.__setattr__(self, "dry_run", bool(self.dry_run))  # WHY: permissive bool coercion (frozen ok)
        self._validate_di_hooks()  # WHY: enforce None-or-callable for the six DI hooks
        self._validate_msp_context()  # WHY: normalize msp_privileges + shape-check selected_msp
        logging.debug("OrgAPUpgraderConfig validated (org_id=%s)", self.org_id)  # WHY: bracket-close trace

    def _validate_identity(self) -> None:  # WHY: declare private helper _validate_identity
        """Enforce identity-field types per data-model.md validation-rules table."""
        if not isinstance(self.org_id, str):  # WHY: enforce string identity (empty allowed for MSP paths)
            raise TypeError("org_id must be a string")  # WHY: fail-fast on wrong identity type
        # WHY: apisession=None is permitted here. Every network-call site guards it explicitly
        # WHY: (see _fetch_org_aps, _step3_fetch_firmware_stats, _step4_fetch_available_firmware,
        # WHY: _select_orgs_from_msp) and returns False/[] for graceful degradation.

    def _validate_di_hooks(self) -> None:  # WHY: declare private helper _validate_di_hooks
        """Enforce that every DI hook is either None or callable."""
        for name in (  # WHY: iterate the six optional DI hook field names
            "safe_input_fn",
            "check_stop_fn",
            "get_org_id_fn",
            "fetch_sites_fn",
            "write_results_fn",
            "is_debug_fn",
        ):
            value = getattr(self, name)  # WHY: fetch hook value via its slot name
            if value is not None and not callable(value):  # WHY: allow None-or-callable only
                raise TypeError(f"{name} must be callable or None")  # WHY: name offending field

    def _validate_msp_context(self) -> None:  # WHY: declare private helper _validate_msp_context
        """Normalize msp_privileges (None -> []) and shape-check selected_msp."""
        if self.msp_privileges is None:  # WHY: normalize absent MSP list so helpers see [] not None
            object.__setattr__(self, "msp_privileges", [])  # WHY: frozen-safe None-to-empty normalization
        elif not isinstance(self.msp_privileges, list):  # WHY: strict type check on non-None MSP list
            raise TypeError("msp_privileges must be a list or None")  # WHY: no dict-vs-list confusion
        if self.selected_msp is not None and not isinstance(self.selected_msp, dict):  # WHY: guard shape
            raise TypeError("selected_msp must be a dict or None")  # WHY: MSP payload is always a dict


class OrgLevelAPFirmwareUpgrader:
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

    def __init__(self, **cfg: Any) -> None:  # WHY: declare private helper __init__
        """Initialize the org-level AP firmware upgrader from kwargs.

        Accepts the same 11 keyword arguments the four MistHelper.py callsites
        already pass (see data-model.md "Producer Side"). Builds the immutable
        OrgAPUpgraderConfig internally and rebinds the pre-refactor
        ``self.<attr>`` surface via ``_apply_config_to_attributes`` so every
        downstream helper continues to read collaborators unchanged.
        """
        logging.info(  # WHY: bracket-open trace at constructor boundary
            "Initializing OrgLevelAPFirmwareUpgrader (dry_run=%s)",
            cfg.get("dry_run", False),
        )
        self._config: OrgAPUpgraderConfig = OrgAPUpgraderConfig(**cfg)  # WHY: single source of truth from kwargs
        self._apply_config_to_attributes()  # WHY: preserve pre-refactor self.<attr> surface for helpers
        self._init_selection_state()  # WHY: existing helper, initializes site-scope selection state
        self._init_device_state()  # WHY: existing helper, initializes device/firmware state
        self._init_results_state()  # WHY: existing helper, initializes results tracking state
        logging.debug(  # WHY: bracket-close trace after init
            "OrgLevelAPFirmwareUpgrader init complete for org %s",
            self._config.org_id,
        )

    def _apply_config_to_attributes(self) -> None:  # WHY: declare private helper _apply_config_to_attributes
        """Rebind pre-refactor instance attributes from the frozen config.

        Preserves the ``self.<attr>`` surface every downstream helper reads
        today so no other helper needs to change simultaneously with the
        constructor migration.
        """
        logging.info(  # WHY: bracket-open trace before rebinding attributes
            "Applying config to instance attributes for org %s",
            self._config.org_id,
        )
        self._apply_identity_and_flags()  # WHY: rebind org_id / apisession / dry_run
        self._apply_di_hooks()  # WHY: rebind six DI hooks with sensible fallbacks
        self._apply_msp_context()  # WHY: rebind MSP list (narrowed) + selected_msp
        logging.debug("Applied %d config fields to instance", 11)  # WHY: bracket-close trace

    def _apply_identity_and_flags(self) -> None:  # WHY: declare private helper _apply_identity_and_flags
        """Rebind identity fields + dry_run flag onto the pre-refactor surface."""
        self.org_id = self._config.org_id  # WHY: back-compat surface for helpers reading self.org_id
        self.apisession = self._config.apisession  # WHY: back-compat surface for self.apisession
        self.dry_run = self._config.dry_run  # WHY: back-compat surface for self.dry_run

    def _apply_di_hooks(self) -> None:  # WHY: declare private helper _apply_di_hooks
        """Rebind the six DI hooks with pre-refactor default fallbacks."""
        self._input_fn = (  # WHY: fallback to EOF-safe default when no injection provided
            self._config.safe_input_fn or self._default_safe_input
        )
        self._check_stop_fn = self._config.check_stop_fn  # WHY: cooperative-cancel probe (None ok)
        self._get_org_id_fn = self._config.get_org_id_fn  # WHY: org-id resolver hook (None ok)
        self._fetch_sites_fn = self._config.fetch_sites_fn  # WHY: site streamer hook (None ok)
        self._write_results_fn = self._config.write_results_fn  # WHY: CSV persister hook (None ok)
        self._is_debug_fn = self._config.is_debug_fn or (lambda: False)  # WHY: constant-False fallback

    def _apply_msp_context(self) -> None:  # WHY: declare private helper _apply_msp_context
        """Rebind MSP-context fields with None-to-empty narrowing for mypy."""
        # WHY: normalize None-to-empty-list narrowing so mypy sees list[Any] downstream
        self._msp_privileges: list[Any] = self._config.msp_privileges or []  # WHY: init/update _msp_privileges attribut
        self._selected_msp = self._config.selected_msp  # WHY: pre-selected MSP payload or None

    @staticmethod
    def _default_safe_input(prompt: str, context: str = "org_ap_upgrader") -> str:  # WHY: declare private helper _defau
        """EOF-safe default input used when no safe_input_fn is injected (issue #452)."""
        from src.utils.input_utils import InputUtils  # Local import avoids any import cycle at load time.

        return InputUtils.safe_input(prompt, context=context)  # Delegate to the canonical wrapper.

    def _init_selection_state(self) -> None:  # WHY: declare private helper _init_selection_state
        """Initialize site selection state."""
        self.target_all_sites: bool = True  # WHY: init/update target_all_sites attribute
        self.selected_site_ids: list[Any] = []  # WHY: init/update selected_site_ids attribute
        self.selected_sites: list[Any] = []  # WHY: init/update selected_sites attribute

    def _init_device_state(self) -> None:  # WHY: declare private helper _init_device_state
        """Initialize device and firmware state."""
        self.all_aps: list[Any] = []  # WHY: init/update all_aps attribute
        self.aps_by_model: dict[str, list[Any]] = {}  # WHY: init/update aps_by_model attribute
        self.ap_versions: dict[str, str] = {}  # WHY: init/update ap_versions attribute
        self.available_versions: list[Any] = []  # WHY: init/update available_versions attribute
        self.model_version_ranges: dict[str, list[str]] = {}  # WHY: init/update model_version_ranges attribute
        self.upgrade_plan: dict[str, dict[str, Any]] = {}  # WHY: init/update upgrade_plan attribute
        self.skipped_already_at_target: int = 0  # WHY: init/update skipped_already_at_target attribute
        self.upgrade_config: dict[str, Any] = {}  # WHY: init/update upgrade_config attribute

    def _init_results_state(self) -> None:  # WHY: declare private helper _init_results_state
        """Initialize results tracking state."""
        self.results: list[dict[str, Any]] = []  # WHY: init/update results attribute
        self.successful_api_calls: int = 0  # WHY: init/update successful_api_calls attribute
        self.failed_api_calls: int = 0  # WHY: init/update failed_api_calls attribute
        self.total_devices_upgraded: int = 0  # WHY: init/update total_devices_upgraded attribute

    # =========================================================================
    # ENTRY POINTS
    # =========================================================================

    def run(self) -> None:  # WHY: declare public entry point
        """Entry point that detects MSP privileges and branches accordingly."""
        logging.info("OrgLevelAPFirmwareUpgrader workflow started, dry_run=%s", self.dry_run)  # WHY: audit workflow ent
        if self._try_msp_mode():  # WHY: consume MSP branch when privileges detected and user selects it
            return  # WHY: MSP mode fully handled. No single-org fallthrough
        self._run_single_org_mode()  # WHY: default single-org path
        logging.debug("OrgLevelAPFirmwareUpgrader.run completed")  # WHY: bracket exit

    def _try_msp_mode(self) -> bool:  # WHY: declare private helper _try_msp_mode
        """Return True when MSP multi-org mode was selected and executed."""
        if not self._has_msp_privileges():  # WHY: guard clause short-circuits non-MSP orgs
            return False  # WHY: fall through to single-org mode
        logging.debug("MSP privileges detected: %d MSP(s)", len(self._msp_privileges or []))  # WHY: trace count
        mode = self._prompt_msp_mode()  # WHY: ask user which mode to run
        if mode is None:  # WHY: SystemExit sentinel from prompt helper
            return True  # WHY: treat cancellation as fully-handled (no further action)
        if mode == "2":  # WHY: option 2 == MSP multi-org
            logging.info("User selected MSP Multi-Org mode")  # WHY: audit selection
            self._execute_msp_mode()  # WHY: run MSP workflow
            return True  # WHY: MSP path finished. Skip single-org
        return False  # WHY: user chose single-org (option 1)

    def _has_msp_privileges(self) -> bool:  # WHY: declare private helper _has_msp_privileges
        """Return True when at least one MSP privilege entry is present."""
        return bool(self._msp_privileges) and len(self._msp_privileges) > 0  # WHY: predicate consolidates check

    def _run_single_org_mode(self) -> None:  # WHY: declare private helper _run_single_org_mode
        """Resolve org_id then run the single-org execute workflow."""
        logging.info("Using single-org mode")  # WHY: audit branch selection
        org_id = self._resolve_org_id()  # WHY: use injected resolver or existing self.org_id
        if not org_id:  # WHY: guard against empty/missing org selection
            print("  X No organization selected")  # WHY: surface fault to the user
            logging.warning("No organization selected")  # WHY: audit warning for missing org
            return  # WHY: cannot proceed without target org
        logging.info("Single-org mode: org_id=%s", org_id)  # WHY: audit resolved id
        self.org_id = org_id  # WHY: persist for downstream helpers reading self.org_id
        self.execute()  # WHY: dispatch to the multi-step orchestration

    def _prompt_msp_mode(self) -> str | None:  # WHY: declare private helper _prompt_msp_mode
        """Prompt user to select MSP vs single-org mode."""
        print("")  # WHY: surface user-facing message
        print("=" * 70)  # WHY: surface user-facing message
        print("  ORG-LEVEL AP FIRMWARE UPGRADE")  # WHY: surface user-facing message
        print("=" * 70)  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print("  MSP privileges detected. Select operation mode:")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print("    [1] Single Organization - upgrade APs in current org")  # WHY: surface user-facing message
        print("    [2] MSP Multi-Org - select orgs from your MSP(s)")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message

        try:
            return self._input_fn("  Select mode (1-2) [1]: ", "msp_mode_select").strip() or "1"  # WHY: return computed
        except SystemExit:  # WHY: handle expected error
            logging.debug("SystemExit during mode selection")  # WHY: action-log after operation
            return None  # WHY: return computed result

    def _resolve_org_id(self) -> str | None:  # WHY: declare private helper _resolve_org_id
        """Resolve org ID via the injected function."""
        if self._get_org_id_fn:  # WHY: branch on condition
            result: str | None = self._get_org_id_fn()  # WHY: assign computed value
            return result  # WHY: return computed result
        return self.org_id if self.org_id else None  # WHY: return computed result

    # =========================================================================
    # MSP MULTI-ORG MODE
    # =========================================================================

    def _execute_msp_mode(self) -> None:  # WHY: declare private helper _execute_msp_mode
        """Execute MSP multi-organization upgrade mode via three phase helpers."""
        logging.info("Starting MSP Multi-Org AP firmware upgrade workflow")  # WHY: workflow entry audit
        self._print_msp_mode_header()  # WHY: banner + dry-run notice for user
        selected_orgs = self._msp_phase_select()  # WHY: pick MSPs, gather orgs. None on cancel
        if selected_orgs is None:  # WHY: guard cancelled selection - cancel msg already printed
            return  # WHY: exit early on user cancel
        if not self._confirm_msp_orgs(selected_orgs):  # WHY: user must confirm before execution
            return  # WHY: exit early on decline
        self._msp_phase_iterate(selected_orgs)  # WHY: drive per-org upgrades + print summary
        logging.debug("_execute_msp_mode completed for %d orgs", len(selected_orgs))  # WHY: exit trace

    def _msp_phase_select(self) -> list[Any] | None:  # WHY: declare private helper _msp_phase_select
        """MSP phase 1: select MSPs and gather orgs. Returns None if user cancels."""
        logging.info("MSP phase: select MSPs and collect orgs")  # WHY: phase entry audit
        selected_msps = self._select_msps()  # WHY: user picks one or more MSPs
        if not selected_msps:  # WHY: cancellation guard on MSP selection
            print("  X Cancelled - no MSP selected")  # WHY: user-visible cancel notice
            logging.warning("MSP selection cancelled")  # WHY: audit trail
            return None  # WHY: signal cancellation upstream
        logging.info("User selected %s MSP(s)", len(selected_msps))  # WHY: audit selection count
        selected_orgs = self._collect_orgs_from_msps(selected_msps)  # WHY: expand MSPs -> orgs
        if not selected_orgs:  # WHY: cancellation guard on org selection
            print("  X Cancelled - no organizations selected")  # WHY: user-visible cancel notice
            logging.warning("Organization selection cancelled")  # WHY: audit trail
            return None  # WHY: signal cancellation upstream
        logging.info("User selected %s organization(s) for upgrade", len(selected_orgs))  # WHY: audit
        return selected_orgs  # WHY: hand off to confirm/iterate phases

    def _msp_phase_iterate(self, selected_orgs: list[Any]) -> None:  # WHY: declare private helper _msp_phase_iterate
        """MSP phase 3: execute per-org upgrades and print final summary."""
        logging.info("MSP phase: executing upgrades on %d orgs", len(selected_orgs))  # WHY: phase entry
        all_results = self._execute_org_upgrades(selected_orgs)  # WHY: drive per-org upgrade workflow
        logging.info("MSP multi-org upgrade completed: %s organizations processed", len(all_results))  # WHY: audit
        self._print_msp_summary(all_results, self.dry_run)  # WHY: user-visible cross-org summary
        logging.debug("MSP phase iterate complete for %d orgs", len(all_results))  # WHY: exit trace

    def _print_msp_mode_header(self) -> None:  # WHY: declare private helper _print_msp_mode_header
        """Print MSP mode header banner."""
        print("")  # WHY: surface user-facing message
        print("=" * 70)  # WHY: surface user-facing message
        print("  MSP MULTI-ORG AP FIRMWARE UPGRADE")  # WHY: surface user-facing message
        print("=" * 70)  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print(f"  Your account has access to {len(self._msp_privileges)} MSP(s).")  # WHY: surface user-facing message
        print("  This workflow will guide you through selecting MSPs and organizations,")  # WHY: surface user-facing me
        print("  then execute firmware upgrades across all selected organizations.")  # WHY: surface user-facing message

        if self.dry_run:  # WHY: branch on condition
            print("")  # WHY: surface user-facing message
            print("  >> DRY-RUN MODE: No actual upgrades will be performed <<")  # WHY: surface user-facing message
            logging.debug("Dry-run mode enabled")  # WHY: action-log after operation

    def _collect_orgs_from_msps(self, selected_msps: list[Any]) -> list[Any]:  # WHY: declare private helper _collect_or
        """Collect orgs from each selected MSP."""
        selected_orgs: list[Any] = []  # WHY: assign computed value
        for msp in selected_msps:  # WHY: iterate collection
            orgs = self._select_orgs_from_msp(msp)  # WHY: compute orgs
            if orgs:  # WHY: branch on condition
                selected_orgs.extend(orgs)  # WHY: advance computation
        return selected_orgs  # WHY: return computed result

    def _confirm_msp_orgs(self, selected_orgs: list[Any]) -> bool:  # WHY: declare private helper _confirm_msp_orgs
        """Confirm selected orgs before proceeding (PCPP: present -> collect -> decide)."""
        logging.info("Presenting confirmation for %d orgs", len(selected_orgs))  # WHY: phase entry
        self._present_msp_confirmation(selected_orgs)  # WHY: user-visible confirmation banner
        confirm = self._prompt_msp_confirmation()  # WHY: capture user's Y/n input
        if confirm is None:  # WHY: guard SystemExit sentinel from input helper
            return False  # WHY: treat cancel as decline
        return self._decide_msp_confirmation(confirm, selected_orgs)  # WHY: interpret input -> bool

    def _present_msp_confirmation(self, selected_orgs: list[Any]) -> None:  # WHY: declare private helper _present_msp_c
        """Print the STEP 3 confirmation banner listing selected orgs."""
        print("")  # WHY: blank spacer for readability
        print("-" * 70)  # WHY: top separator line
        print("  STEP 3: Confirmation")  # WHY: step label
        print("-" * 70)  # WHY: bottom separator line
        print("")  # WHY: blank spacer for readability
        print(f"  Ready to upgrade firmware across {len(selected_orgs)} organization(s):")  # WHY: summary
        print("")  # WHY: blank spacer before org list
        for idx, org in enumerate(selected_orgs, start=1):  # WHY: enumerate each org for user review
            print(f"    {idx:>3}. {org.get('name', 'Unknown')}")  # WHY: numbered list of org names
        print("")  # WHY: blank spacer before footer notes
        print("  Each organization will be processed sequentially.")  # WHY: user-visible sequencing note
        print("  You will configure upgrade settings for each organization.")  # WHY: workflow expectation
        print("")  # WHY: blank spacer before prompt

    def _prompt_msp_confirmation(self) -> str | None:  # WHY: declare private helper _prompt_msp_confirmation
        """Prompt user for MSP confirmation input. Returns None on SystemExit."""
        try:  # WHY: guard against Ctrl+C / EOF during input
            return self._input_fn("  Proceed with these organizations? (Y/n): ", "msp_confirm").strip().lower()
        except SystemExit:  # WHY: user aborted via safe_input
            logging.debug("SystemExit during MSP confirmation")  # WHY: audit abort
            return None  # WHY: signal abort to orchestrator

    def _decide_msp_confirmation(self, confirm: str, selected_orgs: list[Any]) -> bool:  # WHY: declare private helper _
        """Interpret confirmation input and emit final user-visible messaging."""
        if confirm in ["n", "no"]:  # WHY: explicit decline branch
            print("  Cancelled.")  # WHY: user-visible cancel notice
            logging.warning("User declined MSP multi-org confirmation")  # WHY: audit decline
            return False  # WHY: signal decline to orchestrator
        print("")  # WHY: blank spacer before confirmation notice
        print(f"  + Confirmed - proceeding with {len(selected_orgs)} organization(s)")  # WHY: user-visible confirm
        logging.info("User confirmed MSP multi-org upgrade for %s organization(s)", len(selected_orgs))  # WHY: audit
        return True  # WHY: proceed with execution phase

    def _execute_org_upgrades(self, selected_orgs: list[Any]) -> list[dict[str, Any]]:  # WHY: declare private helper _e
        """Execute upgrade for each selected org via named phase helpers."""
        logging.info("Executing per-org upgrades across %d org(s)", len(selected_orgs))  # WHY: entry audit
        all_results: list[dict[str, Any]] = []  # WHY: accumulator for cross-org summary
        for idx, org_info in enumerate(selected_orgs, start=1):  # WHY: sequential per-org loop
            result = self._org_phase_process_one(idx, org_info, len(selected_orgs))  # WHY: process a single org
            all_results.append(result)  # WHY: aggregate result for summary phase
        logging.debug("_execute_org_upgrades produced %d results", len(all_results))  # WHY: exit trace
        return all_results  # WHY: hand results to summary printer

    def _org_phase_process_one(  # WHY: declare private helper _org_phase_process_one
        self, idx: int, org_info: dict[str, Any], total: int
    ) -> dict[str, Any]:
        """Process a single org: banner -> spawn per-org upgrader -> collect result."""
        org_id = org_info["id"]  # WHY: extract identifier for spawned upgrader
        org_name = org_info["name"]  # WHY: extract display name for banner + logs
        self._org_phase_print_banner(idx, org_name, total)  # WHY: user-visible org header
        logging.info("Processing organization %s/%s: %s", idx, total, org_name)  # WHY: audit each org
        upgrader = self._org_phase_spawn_upgrader(org_id)  # WHY: build per-org OrgLevel instance
        upgrader.execute()  # WHY: run the full per-org workflow synchronously
        return self._org_phase_collect_result(org_id, org_name, upgrader)  # WHY: harvest stats

    def _org_phase_print_banner(self, idx: int, org_name: str, total: int) -> None:  # WHY: declare private helper _org_
        """Print the per-org header banner."""
        print("")  # WHY: blank spacer for readability
        print("=" * 70)  # WHY: top separator line
        print(f"  ORGANIZATION {idx}/{total}: {org_name}")  # WHY: progress + name banner
        print("=" * 70)  # WHY: bottom separator line

    def _org_phase_spawn_upgrader(self, org_id: str) -> OrgLevelAPFirmwareUpgrader:  # WHY: declare private helper _org_
        """Spawn a per-org OrgLevelAPFirmwareUpgrader with propagated DI hooks."""
        logging.debug("Spawning OrgLevelAPFirmwareUpgrader for org %s", org_id)  # WHY: audit spawn
        return OrgLevelAPFirmwareUpgrader(  # WHY: reuse the same class for each org
            org_id=org_id,  # WHY: scope to the specific org for this iteration
            apisession=self.apisession,  # WHY: share Mist API session
            dry_run=self.dry_run,  # WHY: propagate preview-only mode
            safe_input_fn=self._input_fn,  # WHY: propagate safe input helper
            check_stop_fn=self._check_stop_fn,  # WHY: propagate cooperative-cancel probe
            get_org_id_fn=self._get_org_id_fn,  # WHY: propagate org-id resolver
            fetch_sites_fn=self._fetch_sites_fn,  # WHY: propagate site streamer
            write_results_fn=self._write_results_fn,  # WHY: propagate CSV persister
            is_debug_fn=self._is_debug_fn,  # WHY: propagate verbose predicate
        )

    def _org_phase_collect_result(  # WHY: declare private helper _org_phase_collect_result
        self, org_id: str, org_name: str, upgrader: OrgLevelAPFirmwareUpgrader
    ) -> dict[str, Any]:
        """Extract stats from a completed per-org upgrader into a result dict."""
        result = {  # WHY: build normalized result record for summary phase
            "org_id": org_id,  # WHY: identifier for cross-referencing
            "org_name": org_name,  # WHY: display name for summary
            "success": upgrader.successful_api_calls,  # WHY: successful-API count
            "failed": upgrader.failed_api_calls,  # WHY: failed-API count
            "devices": upgrader.total_devices_upgraded,  # WHY: device-count metric
        }
        logging.debug(
            "Organization %s: success=%s, failed=%s, devices=%s",
            org_name,
            result["success"],
            result["failed"],
            result["devices"],
        )  # WHY: audit per-org outcome
        return result  # WHY: append to cross-org accumulator

    # =========================================================================
    # MSP / ORG SELECTION
    # =========================================================================

    def _select_msps(self) -> list[Any]:
        """Select MSPs for upgrade."""
        logging.debug("Entering _select_msps()")  # WHY: action-log after operation
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 1: MSP Selection")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print(f"  Your account has access to {len(self._msp_privileges)} MSP(s).")  # WHY: surface user-facing message
        print("  Select which MSP(s) to operate on.")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message

        if len(self._msp_privileges) == 1:  # WHY: branch on condition
            msp_name = self._msp_privileges[0].get("msp_name", "Unknown")  # WHY: compute msp_name
            print(f"  Only one MSP available: {msp_name}")  # WHY: surface user-facing message
            print(f"  + Auto-selected: {msp_name}")  # WHY: surface user-facing message
            logging.info("Auto-selected single MSP: %s", msp_name)  # WHY: action-log before operation
            return list(self._msp_privileges)  # WHY: return computed result

        default_idx = self._find_selected_msp_index()  # WHY: compute default_idx
        self._display_msp_list(default_idx)  # WHY: advance computation

        return self._collect_msp_selection(default_idx)  # WHY: return computed result

    def _find_selected_msp_index(self) -> int | None:  # WHY: declare private helper _find_selected_msp_index
        """Find index of currently selected MSP."""
        if not self._selected_msp:  # WHY: guard against missing precondition
            return None  # WHY: return computed result
        for idx, msp in enumerate(self._msp_privileges):  # WHY: iterate collection
            if msp.get("msp_id") == self._selected_msp.get("msp_id"):  # WHY: branch on condition
                return idx + 1  # WHY: return computed result
        return None  # WHY: return computed result

    def _display_msp_list(self, default_idx: int | None) -> None:  # WHY: declare private helper _display_msp_list
        """Display available MSPs."""
        print("  Available MSPs:")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        for idx, msp in enumerate(self._msp_privileges, start=1):  # WHY: iterate collection
            current_marker = " <-- currently selected" if default_idx == idx else ""  # WHY: compute current_marker
            print(  # WHY: surface user-facing message
                f"    [{idx:>2}] {msp.get('msp_name', 'Unknown')} "
                f"(role: {msp.get('role', 'unknown')}){current_marker}"
            )
        print("")  # WHY: surface user-facing message
        print("  Selection Options:")  # WHY: surface user-facing message
        print("    - Single MSP: Enter number (e.g., '1')")  # WHY: surface user-facing message
        print("    - Multiple MSPs: Comma-separated (e.g., '1,3,5')")  # WHY: surface user-facing message
        print("    - Range: Dash or 'through' (e.g., '1-3' or '1 through 3')")  # WHY: surface user-facing message
        print("    - ALL MSPs: Enter 'all'")  # WHY: surface user-facing message
        print("    - Cancel: Enter 'q'")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message

    def _collect_msp_selection(self, default_idx: int | None) -> list[Any]:  # WHY: declare private helper _collect_msp_
        """Collect MSP selection from user."""
        prompt = self._build_msp_selection_prompt(default_idx)  # Build prompt once so default wording stays consistent.
        selection = self._read_selection_value(
            prompt, "msp_select"
        )  # Centralize EOF-safe input handling for selection parsing.
        if selection is None:  # Treat EOF-safe cancellation as an empty result so callers can stop gracefully.
            return []  # WHY: return computed result
        if self._should_use_default_msp_selection(
            selection, default_idx
        ):  # Reuse current MSP only when Enter has explicit meaning.
            return self._use_default_msp()  # WHY: return computed result
        if self._is_cancelled_selection(
            selection
        ):  # Stop early when operator cancels or submits blank without a default.
            print("  Cancelled.")  # Make cancellation obvious in interactive runs.
            logging.info("MSP selection cancelled")  # Preserve audit trail for operator cancellation.
            return []  # WHY: return computed result
        if self._is_select_all_selection(selection):  # Route explicit bulk selection through dedicated summary logic.
            return self._select_all_msps()  # WHY: return computed result
        return self._select_msps_by_indices(selection)  # Fall back to index parsing for single, multi, and range input.

    @staticmethod
    def _build_msp_selection_prompt(default_idx: int | None) -> str:  # WHY: declare private helper _build_msp_selection
        """Build MSP selection prompt text."""
        if default_idx:  # Mention current selection only when operator can safely reuse it.
            return f"  Select MSP(s) [Enter for current selection {default_idx}]: "  # WHY: return computed result
        return "  Select MSP(s): "  # Keep prompt simple when no default exists.

    def _read_selection_value(self, prompt: str, context: str) -> str | None:  # WHY: declare private helper _read_selec
        """Read and normalize a selection string."""
        try:
            return self._input_fn(prompt, context).strip().lower()  # Normalize once so later checks stay deterministic.
        except SystemExit:  # WHY: handle expected error
            return None  # Convert controlled exits into sentinel value for caller-specific cancellation handling.

    def _should_use_default_msp_selection(self, selection: str, default_idx: int | None) -> bool:  # WHY: declare privat
        """Determine whether Enter should keep the current MSP."""
        has_default = bool(
            default_idx and self._selected_msp is not None
        )  # Require both visible prompt state and stored MSP data.
        return selection == "" and has_default  # Only blank input should reuse the active MSP context.

    @staticmethod
    def _is_cancelled_selection(selection: str) -> bool:  # WHY: declare private helper _is_cancelled_selection
        """Determine whether selection means cancel."""
        return selection in ["q", ""]  # Support quit token and blank-without-default using one rule.

    @staticmethod
    def _is_select_all_selection(selection: str) -> bool:  # WHY: declare private helper _is_select_all_selection
        """Determine whether selection means all items."""
        return selection == "all"  # Keep bulk-selection keyword check explicit and reusable.

    def _use_default_msp(self) -> list[Any]:  # WHY: declare private helper _use_default_msp
        """Return the currently selected MSP as a list."""
        msp = self._selected_msp or {}  # WHY: compute msp
        print(f"  + Using current MSP: {msp.get('msp_name', 'Unknown')}")  # WHY: surface user-facing message
        logging.debug("Using default MSP: %s", msp.get("msp_name"))  # WHY: action-log after operation
        return [self._selected_msp]  # WHY: return computed result

    def _select_all_msps(self) -> list[Any]:  # WHY: declare private helper _select_all_msps
        """Select all available MSPs."""
        print("")  # WHY: surface user-facing message
        print(f"  + Selected ALL {len(self._msp_privileges)} MSP(s):")  # WHY: surface user-facing message
        for msp in self._msp_privileges:  # WHY: iterate collection
            print(f"      - {msp.get('msp_name', 'Unknown')}")  # WHY: surface user-facing message
        logging.info("User selected ALL %s MSP(s)", len(self._msp_privileges))  # WHY: action-log before operation
        return list(self._msp_privileges)  # WHY: return computed result

    def _select_msps_by_indices(self, selection: str) -> list[Any]:  # WHY: declare private helper _select_msps_by_indic
        """Select MSPs by parsed index selection."""
        indices = self._parse_selection(selection, len(self._msp_privileges))  # WHY: compute indices
        if not indices:  # WHY: guard against missing precondition
            print("  X Invalid selection")  # WHY: surface user-facing message
            logging.warning("Invalid MSP selection: %s", selection)  # WHY: surface non-fatal issue
            return []  # WHY: return computed result

        selected = [self._msp_privileges[i] for i in indices]  # WHY: compute selected
        print("")  # WHY: surface user-facing message
        print(f"  + Selected {len(selected)} MSP(s):")  # WHY: surface user-facing message
        for msp in selected:  # WHY: iterate collection
            print(f"      - {msp.get('msp_name', 'Unknown')}")  # WHY: surface user-facing message
        logging.info("User selected %s MSP(s)", len(selected))  # WHY: action-log before operation
        return selected  # WHY: return computed result

    def _select_orgs_from_msp(self, msp: dict[str, Any]) -> list[Any]:  # WHY: declare private helper _select_orgs_from_
        """Select organizations from a specific MSP (PCPP: prepare -> compute -> present)."""
        logging.info("Selecting orgs from MSP %s", msp.get("msp_name"))  # WHY: phase entry audit
        msp_id, msp_name = self._prepare_msp_identity(msp)  # WHY: extract stable id + name
        self._present_msp_org_header(msp_name)  # WHY: user-visible STEP 2 banner
        if self.apisession is None:  # WHY: guard uninitialised session
            print("  X API session not initialized")  # WHY: user-visible error
            logging.error("API session not initialized for org fetch")  # WHY: audit precondition failure
            return []  # WHY: no orgs can be fetched
        return self._collect_msp_orgs_safely(msp_id, msp_name)  # WHY: wrap fetch+display in try/except

    def _prepare_msp_identity(self, msp: dict[str, Any]) -> tuple[str, str]:  # WHY: declare private helper _prepare_msp
        """Extract (msp_id, msp_name) from the MSP payload."""
        msp_id = msp["msp_id"]  # WHY: required key for API call
        msp_name = msp.get("msp_name", "Unknown")  # WHY: display name with safe fallback
        return msp_id, msp_name  # WHY: hand tuple to caller

    def _present_msp_org_header(self, msp_name: str) -> None:  # WHY: declare private helper _present_msp_org_header
        """Print STEP 2 org-selection banner for a given MSP."""
        print("")  # WHY: blank spacer for readability
        print("-" * 70)  # WHY: top separator line
        print(f"  STEP 2: Organization Selection for MSP: {msp_name}")  # WHY: step + context label
        print("-" * 70)  # WHY: bottom separator line
        print("")  # WHY: blank spacer before status
        print(f"  Fetching organizations from {msp_name}...")  # WHY: user-visible progress

    def _collect_msp_orgs_safely(self, msp_id: str, msp_name: str) -> list[Any]:  # WHY: declare private helper _collect
        """Fetch, display, and collect user's org picks with safe error handling."""
        try:  # WHY: guard downstream API + UI code from unexpected exceptions
            orgs = self._fetch_msp_orgs(msp_id, msp_name)  # WHY: hit Mist API for MSP -> orgs
            if not orgs:  # WHY: guard empty result
                return []  # WHY: nothing to display
            self._display_org_list(orgs)  # WHY: show user picking list. The banner already named the MSP
            return self._collect_org_selection(orgs, msp_name)  # WHY: capture user choice
        except Exception as error:  # WHY: broad guard preserves pre-refactor behavior
            print(f"  X Error fetching organizations: {error}")  # WHY: user-visible error
            logging.error("Failed to fetch orgs from MSP %s: %s", msp_name, error)  # WHY: audit failure
            return []  # WHY: safe fallback for orchestrator

    def _fetch_msp_orgs(self, msp_id: str, msp_name: str) -> list[Any]:  # WHY: declare private helper _fetch_msp_orgs
        """Fetch organizations from an MSP."""
        logging.info("Fetching orgs for MSP %s", msp_name)  # WHY: bracket entry
        response = self._call_list_msp_orgs(msp_id)  # WHY: HTTP call isolated for CC hygiene
        orgs = self._extract_msp_orgs(response, msp_name)  # WHY: normalize response into list
        if not orgs:  # WHY: guard against empty MSP inventory
            return []  # WHY: caller handles empty list gracefully
        sorted_orgs = sorted(orgs, key=lambda x: x.get("name", "").lower())  # WHY: alphabetical UX
        print(f"  + Found {len(sorted_orgs)} organization(s) under {msp_name}")  # WHY: user feedback
        logging.info("Found %s organizations under MSP %s", len(sorted_orgs), msp_name)  # WHY: audit count
        return sorted_orgs  # WHY: return sorted result

    def _call_list_msp_orgs(self, msp_id: str) -> Any:  # WHY: declare private helper _call_list_msp_orgs
        """Invoke listMspOrgs for the supplied MSP id."""
        msp_orgs_api = importlib.import_module("mistapi.api.v1.msps.orgs")  # WHY: late import keeps startup light
        logging.debug("Calling listMspOrgs for msp_id=%s", msp_id)  # WHY: audit API call
        return msp_orgs_api.listMspOrgs(self.apisession, msp_id)  # WHY: HTTP round-trip

    def _extract_msp_orgs(self, response: Any, msp_name: str) -> list[Any]:  # WHY: declare private helper _extract_msp_
        """Normalize a listMspOrgs response into a list of org dicts."""
        logging.info("Extracting MSP orgs from response for msp=%s", msp_name)  # WHY: bracket entry with MSP identity
        if not self._response_has_data(response):  # WHY: guard against network failure/malformed response
            self._warn_msp_fetch_failed(msp_name)  # WHY: emit fault message + audit log
            return []  # WHY: signal empty inventory to caller so it can skip this MSP
        orgs = self._normalize_msp_org_payload(response.data)  # WHY: fold scalar->list and None->[] variants
        if not orgs:  # WHY: empty inventory is a valid but reportable outcome
            self._warn_msp_empty(msp_name)  # WHY: surface empty result to operator + audit log
        logging.debug("Extracted %d org(s) from MSP %s", len(orgs), msp_name)  # WHY: bracket exit with count
        return orgs  # WHY: caller inspects list truthiness to decide next step

    @staticmethod
    def _warn_msp_fetch_failed(msp_name: str) -> None:  # WHY: declare private helper _warn_msp_fetch_failed
        """Emit user-visible + audit-log messages when MSP org fetch fails."""
        print(f"  X Failed to fetch organizations from {msp_name}")  # WHY: user-visible fault line
        logging.warning("Failed to fetch organizations from MSP %s", msp_name)  # WHY: audit trail for operators

    @staticmethod
    def _warn_msp_empty(msp_name: str) -> None:  # WHY: declare private helper _warn_msp_empty
        """Emit user-visible + audit-log messages when an MSP contains no orgs."""
        print(f"  X No organizations found under {msp_name}")  # WHY: user-visible empty-result line
        logging.warning("No organizations found under MSP %s", msp_name)  # WHY: audit trail for downstream skip

    @staticmethod
    def _normalize_msp_org_payload(raw: Any) -> list[Any]:  # WHY: declare private helper _normalize_msp_org_payload
        """Coerce a listMspOrgs data payload into a list of org dicts."""
        if isinstance(raw, list):  # WHY: happy-path is a list of org dicts
            return raw  # WHY: pass through unchanged
        if raw:  # WHY: single org payload arrives as a dict. Wrap to preserve caller contract
            return [raw]  # WHY: caller iterates a list, wrap scalar to keep loop uniform
        return []  # WHY: None / empty -> caller-visible empty inventory

    def _display_org_list(self, orgs: list[Any]) -> None:  # WHY: the body prints no MSP name, so the parameter went
        """Display numbered organization list."""
        print("")  # WHY: surface user-facing message
        print("  Organizations:")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        for idx, org in enumerate(orgs, start=1):  # WHY: iterate collection
            print(f"    [{idx:>3}] {org.get('name', 'Unknown')}")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print("  Selection Options:")  # WHY: surface user-facing message
        print("    - Single org: Enter number (e.g., '1')")  # WHY: surface user-facing message
        print("    - Multiple orgs: Comma-separated (e.g., '1,3,5')")  # WHY: surface user-facing message
        print("    - Range: Dash or 'through' (e.g., '1-10' or '1 through 10')")  # WHY: surface user-facing message
        print("    - ALL orgs under this MSP: Enter 'all'")  # WHY: surface user-facing message
        print("    - Skip this MSP: Enter 'q'")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message

    def _collect_org_selection(self, orgs: list[Any], msp_name: str) -> list[Any]:  # WHY: declare private helper _colle
        """Collect org selection from user."""
        selection = (
            self._read_org_selection_value()
        )  # Reuse normalized input flow so org logic stays focused on outcomes.
        if selection is None:  # Stop quietly when safe_input requests controlled exit.
            logging.debug("SystemExit during org selection")  # Preserve existing diagnostic event for early exits.
            return []  # WHY: return computed result
        logging.debug("User selection input: '%s'", selection)  # Keep traceability for operator-entered scope.
        if self._should_skip_org_selection(selection):  # Treat quit and blank as intentional MSP skip actions.
            print(f"  Skipping {msp_name}")  # Confirm which MSP branch is being skipped.
            logging.info("User skipped MSP %s", msp_name)  # Preserve operator choice in logs.
            return []  # WHY: return computed result
        if self._is_select_all_selection(selection):  # Bulk select needs separate summary output for clarity.
            self._print_all_org_selection(orgs, msp_name)  # Show full list so operator can verify wide scope.
            logging.info(
                "User selected ALL %s organizations from MSP %s", len(orgs), msp_name
            )  # Keep existing summary logging.
            return orgs  # WHY: return computed result
        return self._select_orgs_by_indices(
            selection, orgs, msp_name
        )  # Delegate index parsing and summary display to cohesive helper.

    def _read_org_selection_value(self) -> str | None:  # WHY: declare private helper _read_org_selection_value
        """Read organization selection input."""
        return self._read_selection_value(
            "  Select organization(s): ", "org_select"
        )  # Share common normalization behavior across selectors.

    @staticmethod
    def _should_skip_org_selection(selection: str) -> bool:  # WHY: declare private helper _should_skip_org_selection
        """Determine whether org selection should skip current MSP."""
        return selection in ["q", ""]  # Blank input means skip because org selection has no default value.

    @staticmethod
    def _print_selection_names(items: list[Any]) -> None:  # WHY: declare private helper _print_selection_names
        """Print item names in standard bullet format."""
        for item in items:  # Use one display helper so selection summaries stay visually consistent.
            print(f"      - {item.get('name', 'Unknown')}")  # Fall back to placeholder when API data is incomplete.

    def _print_all_org_selection(self, orgs: list[Any], msp_name: str) -> None:  # WHY: declare private helper _print_al
        """Print summary for selecting all orgs under an MSP."""
        print("")  # Separate summary block from prompt section for readability.
        print(
            f"  + Selected ALL {len(orgs)} organization(s) under {msp_name}:"
        )  # Confirm wide-scope action before execution continues.
        self._print_selection_names(orgs)  # Reuse standard name-list formatting across selection summaries.

    def _select_orgs_by_indices(self, selection: str, orgs: list[Any], msp_name: str) -> list[Any]:  # WHY: declare priv
        """Select organizations by parsed indices."""
        indices = self._parse_selection(selection, len(orgs))  # Convert free-form tokens into zero-based org positions.
        if not indices:  # Reject invalid selections before any orgs are accepted.
            print("  X Invalid selection, skipping this MSP")  # Make skipped scope explicit to operator.
            logging.warning(
                "Invalid org selection '%s' for MSP %s", selection, msp_name
            )  # Preserve invalid-input diagnostics.
            return []  # WHY: return computed result
        selected = [orgs[i] for i in indices]  # Materialize chosen org records only after validation succeeds.
        print("")  # Add spacing so positive summary stands out from prompt area.
        print(
            f"  + Selected {len(selected)} organization(s) from {msp_name}:"
        )  # Echo exact scope to reduce destructive mistakes.
        self._print_selection_names(selected)  # Keep list formatting identical to ALL-selection summary.
        logging.info(
            "User selected %s organization(s) from MSP %s", len(selected), msp_name
        )  # Preserve existing success logging.
        return selected  # WHY: return computed result

    # =========================================================================
    # SELECTION PARSING UTILITIES
    # =========================================================================

    @staticmethod
    def _parse_selection(selection: str, max_items: int) -> list[int]:  # WHY: declare private helper _parse_selection
        """Parse selection string into list of indices."""
        indices: list[int] = []  # WHY: assign computed value
        parts = selection.replace(",", " ").split()  # WHY: compute parts

        for part in parts:  # WHY: iterate collection
            indices.extend(OrgLevelAPFirmwareUpgrader._parse_selection_part(part, max_items))  # WHY: advance computatio

        through_indices = OrgLevelAPFirmwareUpgrader._parse_through_range(selection, max_items)  # WHY: compute through_
        if through_indices:  # WHY: branch on condition
            indices = through_indices  # WHY: compute indices

        return sorted(set(indices))  # WHY: return computed result

    @staticmethod
    def _parse_selection_part(part: str, max_items: int) -> list[int]:  # WHY: declare private helper _parse_selection_p
        """Parse a single selection part (number or range)."""
        dash_range = OrgLevelAPFirmwareUpgrader._parse_dash_selection_range(
            part, max_items
        )  # Prefer explicit range parsing before single-index fallback.
        if dash_range is not None:  # Distinguish invalid dash syntax from non-range tokens.
            return dash_range  # WHY: return computed result
        if OrgLevelAPFirmwareUpgrader._contains_through_keyword(
            part
        ):  # Ignore split "through" token because full-range parser handles it later.
            return []  # WHY: return computed result
        return OrgLevelAPFirmwareUpgrader._parse_single_selection_index(
            part, max_items
        )  # Parse remaining token as one-based index.

    @staticmethod
    def _parse_dash_selection_range(part: str, max_items: int) -> list[int] | None:  # WHY: declare private helper _pars
        """Parse a dashed numeric range token."""
        if "-" not in part or part.startswith("-"):  # Only treat internal dashes as valid range syntax.
            return None  # WHY: return computed result
        try:
            start, end = part.split("-", 1)  # Split once so accidental extra dashes fail validation naturally.
            start_idx = int(start) - 1  # Convert user-facing numbering into zero-based list positions.
            end_idx = int(end) - 1  # Keep same conversion for upper bound before validation.
        except ValueError:  # WHY: handle expected error
            return []  # Invalid numeric range should be rejected instead of crashing selection flow.
        if 0 <= start_idx <= end_idx < max_items:  # Reject inverted or out-of-range selections consistently.
            return list(range(start_idx, end_idx + 1))  # WHY: return computed result
        return []  # Return empty list so caller can mark selection invalid.

    @staticmethod
    def _contains_through_keyword(part: str) -> bool:  # WHY: declare private helper _contains_through_keyword
        """Determine whether token belongs to a through-range expression."""
        return (
            "through" in part.lower()
        )  # Skip token here because whole-expression parser handles natural-language ranges.

    @staticmethod
    def _parse_single_selection_index(part: str, max_items: int) -> list[int]:  # WHY: declare private helper _parse_sin
        """Parse a single numeric selection token."""
        try:
            idx = int(part) - 1  # Convert one-based user input into internal zero-based position.
        except ValueError:  # WHY: handle expected error
            return []  # Non-numeric tokens are invalid once range cases are exhausted.
        if 0 <= idx < max_items:  # Only accept indices that point at actual list members.
            return [idx]  # WHY: return computed result
        return []  # Out-of-range tokens should not silently coerce to valid values.

    @staticmethod
    def _parse_through_range(selection: str, max_items: int) -> list[int]:  # WHY: declare private helper _parse_through
        """Parse 'X through Y' range from selection string."""
        through_match = re.search(r"(\d+)\s*through\s*(\d+)", selection, re.IGNORECASE)  # WHY: compute through_match
        if not through_match:  # WHY: guard against missing precondition
            return []  # WHY: return computed result
        try:
            start_idx = int(through_match.group(1)) - 1  # WHY: compute start_idx
            end_idx = int(through_match.group(2)) - 1  # WHY: compute end_idx
            if 0 <= start_idx <= end_idx < max_items:  # WHY: branch on condition
                return list(range(start_idx, end_idx + 1))  # WHY: return computed result
        except ValueError:  # WHY: handle expected error
            pass  # WHY: no-op placeholder
        return []  # WHY: return computed result

    @staticmethod
    def _print_msp_summary(results: list[dict[str, Any]], dry_run: bool) -> None:  # WHY: declare private helper _print_
        """Print summary of MSP multi-org upgrade."""
        logging.info("Printing MSP summary for %d org(s), dry_run=%s", len(results), dry_run)  # WHY: bracket entry
        OrgLevelAPFirmwareUpgrader._print_msp_summary_header(dry_run)  # WHY: emit banner + dry-run notice
        totals = OrgLevelAPFirmwareUpgrader._compute_msp_totals(results)  # WHY: aggregate counters once
        OrgLevelAPFirmwareUpgrader._print_msp_summary_totals(len(results), totals)  # WHY: overall counters
        OrgLevelAPFirmwareUpgrader._print_msp_summary_breakdown(results)  # WHY: per-org detail block
        logging.debug("MSP summary printed")  # WHY: bracket exit

    @staticmethod
    def _print_msp_summary_header(dry_run: bool) -> None:  # WHY: declare private helper _print_msp_summary_header
        """Emit the fixed-width banner and optional dry-run marker."""
        print("")  # WHY: leading spacer
        print("=" * 70)  # WHY: fixed-width header rule
        print("  MSP MULTI-ORG UPGRADE SUMMARY")  # WHY: title line
        print("=" * 70)  # WHY: closing header rule
        if dry_run:  # WHY: emphasize preview-only status
            print("  >> DRY-RUN MODE - No actual changes made <<")  # WHY: user notice for dry-run

    @staticmethod
    def _compute_msp_totals(results: list[dict[str, Any]]) -> dict[str, int]:  # WHY: declare private helper _compute_ms
        """Return aggregated counters across all MSP results."""
        return {  # WHY: bundle three counters into a single return object
            "success": sum(r["success"] for r in results),  # WHY: total successful API calls
            "failed": sum(r["failed"] for r in results),  # WHY: total failed API calls
            "devices": sum(r["devices"] for r in results),  # WHY: total devices targeted
        }

    @staticmethod
    def _print_msp_summary_totals(org_count: int, totals: dict[str, int]) -> None:  # WHY: declare private helper _print
        """Emit the aggregate counter block."""
        print(f"\n  Organizations: {org_count}")  # WHY: org headcount
        print(f"  API Calls: {totals['success']} success, {totals['failed']} failed")  # WHY: HTTP stats
        print(f"  Devices: {totals['devices']}")  # WHY: device count

    @staticmethod
    def _print_msp_summary_breakdown(results: list[dict[str, Any]]) -> None:  # WHY: declare private helper _print_msp_s
        """Emit per-org outcome lines under a heading."""
        print("\n  Per-Org Breakdown:")  # WHY: section header
        for result in results:  # WHY: print each org outcome so partial failures stay visible
            OrgLevelAPFirmwareUpgrader._print_single_msp_result(result)  # WHY: reuse existing formatter

    @staticmethod
    def _print_single_msp_result(result: dict[str, Any]) -> None:  # WHY: declare private helper _print_single_msp_resul
        """Print one MSP summary line."""
        status = "OK" if result["failed"] == 0 else "PARTIAL"  # Highlight partial failures without adding more columns.
        print(
            f"    {result['org_name']}: {result['devices']} devices ({status})"
        )  # Preserve compact at-a-glance summary format.

    # =========================================================================
    # MAIN EXECUTE WORKFLOW
    # =========================================================================

    def _get_execute_steps(self) -> tuple[Any, ...]:  # WHY: declare private helper _get_execute_steps
        """Return workflow steps in execution order."""
        return (  # Keep workflow definition centralized so execute() stays linear and easy to audit.
            self._step1_select_site_scope,
            self._step2_discover_aps,
            self._step3_fetch_firmware_stats,
            self._step4_fetch_available_firmware,
            self._step5_select_firmware_versions,
            self._step6_configure_upgrade,
            self._step7_confirm_and_execute,
        )

    def _run_execute_steps(self) -> bool:  # WHY: declare private helper _run_execute_steps
        """Run upgrade workflow steps until one fails."""
        for step in self._get_execute_steps():  # Iterate ordered steps so future insertions touch one place only.
            if not step():  # Stop immediately because later steps depend on prior collected state.
                return False  # WHY: return computed result
        return True  # Signal completion so caller can perform final result writing once.

    def execute(self) -> None:  # WHY: declare public method execute
        """Execute the org-level AP firmware upgrade workflow."""
        logging.info(
            "Starting org-level AP firmware upgrade..."
        )  # Keep top-level entry log for workflow observability.
        logging.debug("OrgLevelAPFirmwareUpgrader.execute() initiated")  # Preserve detailed lifecycle tracing.
        logging.debug("Using org_id: %s", self.org_id)  # Capture current org context before any prompts mutate state.
        self._print_execute_header()  # Show operator-facing banner before interactive workflow starts.
        try:
            if self._run_execute_steps():  # Run ordered steps through shared loop to reduce branching noise.
                self._step8_write_results()  # Only persist results after full workflow succeeds.
        except KeyboardInterrupt:  # WHY: handle expected error
            print("\n Operation cancelled by user.")  # Mirror prior cancel message for operator awareness.
            logging.info(
                "Org-level AP firmware upgrade cancelled by user interrupt"
            )  # Preserve interruption audit trail.

    def _print_execute_header(self) -> None:  # WHY: declare private helper _print_execute_header
        """Print execute workflow header."""
        print("")  # WHY: surface user-facing message
        print("=" * 70)  # WHY: surface user-facing message
        print("  ORG-LEVEL AP FIRMWARE UPGRADE (Efficient Multi-Site)")  # WHY: surface user-facing message
        print("=" * 70)  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print("  This operation uses the org-level upgrade API for efficiency:")  # WHY: surface user-facing message
        print("    - 1 API call per unique version (vs 1 per site per version)")  # WHY: surface user-facing message
        print("    - Supports all sites or selected sites per org")  # WHY: surface user-facing message
        print("    - Same upgrade strategies as site-level (big_bang, canary, etc.)")  # WHY: surface user-facing messag

        if self.dry_run:  # WHY: branch on condition
            print("")  # WHY: surface user-facing message
            print("  >> DRY-RUN MODE: No actual upgrades will be performed <<")  # WHY: surface user-facing message
            logging.info("DRY-RUN MODE enabled - no API calls will be made")  # WHY: action-log before operation

    # =========================================================================
    # STEP 1: SITE SCOPE SELECTION
    # =========================================================================

    def _step1_select_site_scope(self) -> bool:  # WHY: declare private helper _step1_select_site_scope
        """Select whether to upgrade all sites or specific sites (PCPP)."""
        logging.info("Prompting for site scope selection")  # WHY: phase entry audit
        self._present_site_scope_menu()  # WHY: show scope options to user
        choice = self._prompt_site_scope()  # WHY: capture user input
        if choice is None:  # WHY: guard SystemExit sentinel
            return False  # WHY: treat cancel as failure
        return self._decide_site_scope(choice)  # WHY: interpret choice -> outcome

    def _present_site_scope_menu(self) -> None:  # WHY: declare private helper _present_site_scope_menu
        """Print the STEP 1 site-scope selection menu."""
        print("")  # WHY: blank spacer for readability
        print("-" * 70)  # WHY: top separator line
        print("  STEP 1: Site Scope Selection")  # WHY: step label
        print("-" * 70)  # WHY: bottom separator line
        print("")  # WHY: blank spacer before options
        print("  Select scope for this organization:")  # WHY: prompt lead-in
        print("   [1] All sites - upgrade APs across ALL sites in this org")  # WHY: option 1 description
        print("   [2] Select sites - choose specific sites to include")  # WHY: option 2 description
        print("")  # WHY: blank spacer before prompt

    def _prompt_site_scope(self) -> str | None:  # WHY: declare private helper _prompt_site_scope
        """Prompt user for site-scope choice. Returns None on SystemExit."""
        try:  # WHY: guard Ctrl+C / EOF
            choice = self._input_fn("  Select scope (1 or 2): ", "org_scope_select").strip()  # WHY: compute choice
        except SystemExit:  # WHY: user aborted via safe_input
            logging.debug("SystemExit during site scope selection")  # WHY: audit abort
            return None  # WHY: signal abort upstream
        logging.debug("Site scope selection: %s", choice)  # WHY: audit chosen value
        return choice  # WHY: return normalized input

    def _decide_site_scope(self, choice: str) -> bool:  # WHY: declare private helper _decide_site_scope
        """Interpret site-scope choice and apply state changes."""
        if choice == "1":  # WHY: all-sites branch
            self.target_all_sites = True  # WHY: mark org-wide scope
            self.selected_site_ids = []  # WHY: empty list means all sites
            print("  + Targeting ALL sites in organization")  # WHY: user-visible confirmation
            logging.info("Org-level upgrade: targeting all sites")  # WHY: audit choice
            return True  # WHY: proceed to next step
        if choice == "2":  # WHY: specific-sites branch
            return self._select_specific_sites()  # WHY: delegate to sub-picker
        print("  X Invalid selection")  # WHY: user-visible error for other input
        logging.warning("Invalid site scope selection")  # WHY: audit invalid input
        return False  # WHY: signal failure to caller

    def _select_specific_sites(self) -> bool:  # WHY: declare private helper _select_specific_sites
        """Allow user to select specific sites for upgrade."""
        print("")  # WHY: surface user-facing message
        print("  Fetching sites from organization...")  # WHY: surface user-facing message

        sites_data = self._fetch_sorted_sites()  # WHY: compute sites_data
        if not sites_data:  # WHY: guard against missing precondition
            return False  # WHY: return computed result

        self._display_site_list(sites_data)  # WHY: advance computation
        return self._collect_site_selection(sites_data)  # WHY: return computed result

    def _fetch_sorted_sites(self) -> list[Any] | None:  # WHY: declare private helper _fetch_sorted_sites
        """Fetch and sort sites by name."""
        try:
            if self._fetch_sites_fn:  # WHY: branch on condition
                sites_data = self._fetch_sites_fn(self.org_id)  # WHY: compute sites_data
            else:
                return None  # WHY: return computed result
            if not sites_data:  # WHY: guard against missing precondition
                print("  X No sites found in organization")  # WHY: surface user-facing message
                return None  # WHY: return computed result
            return sorted(sites_data, key=lambda s: s.get("name", "").lower())  # WHY: return computed result
        except Exception as error:  # WHY: handle expected error
            print(f"  X Error fetching sites: {error}")  # WHY: surface user-facing message
            logging.error("Failed to fetch sites for org-level upgrade: %s", error)  # WHY: surface fatal issue
            return None  # WHY: return computed result

    def _display_site_list(self, sites_data: list[Any]) -> None:  # WHY: declare private helper _display_site_list
        """Display numbered site list."""
        print(f"  Found {len(sites_data)} site(s):")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        for idx, site in enumerate(sites_data, start=1):  # WHY: iterate collection
            print(f"    {idx:>4}. {site.get('name', 'Unknown')}")  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message
        print("  Selection: single '1', multiple '1,3,5', range '1-3', 'all', or 'q'")  # WHY: surface user-facing messa
        print("")  # WHY: surface user-facing message

    def _collect_site_selection(self, sites_data: list[Any]) -> bool:  # WHY: declare private helper _collect_site_selec
        """Collect and process site selection from user."""
        try:
            selection = self._input_fn("  Select site(s): ", "site_multi_select").strip().lower()  # WHY: compute select
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        if selection in ["q", ""]:  # WHY: branch on condition
            return False  # WHY: return computed result

        if selection == "all":  # WHY: branch on condition
            self.target_all_sites = True  # WHY: init/update target_all_sites attribute
            self.selected_site_ids = []  # WHY: init/update selected_site_ids attribute
            print("  + Targeting ALL sites")  # WHY: surface user-facing message
            return True  # WHY: return computed result

        return self._apply_site_selection(sites_data, selection)  # WHY: return computed result

    def _apply_site_selection(self, sites_data: list[Any], selection: str) -> bool:  # WHY: declare private helper _appl
        """Apply parsed site selection."""
        selected_indices = self._parse_selection(selection, len(sites_data))  # Inlined: direct range/list parse
        if not selected_indices:  # WHY: guard against missing precondition
            print("  X Invalid selection")  # WHY: surface user-facing message
            return False  # WHY: return computed result

        self.target_all_sites = False  # WHY: init/update target_all_sites attribute
        self.selected_sites = [sites_data[idx] for idx in selected_indices]  # WHY: init/update selected_sites attribute
        self.selected_site_ids = [site["id"] for site in self.selected_sites]  # WHY: init/update selected_site_ids attr
        print(f"  + Selected {len(self.selected_site_ids)} site(s)")  # WHY: surface user-facing message
        return True  # WHY: return computed result

    # =========================================================================
    # STEP 2: DEVICE DISCOVERY
    # =========================================================================

    def _step2_discover_aps(self) -> bool:  # WHY: declare private helper _step2_discover_aps
        """Discover APs from selected scope."""
        logging.debug("Entering _step2_discover_aps()")  # WHY: action-log after operation
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 2: Device Discovery")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message

        if self.target_all_sites:  # WHY: branch on condition
            print("  Fetching all APs from organization...")  # WHY: surface user-facing message
            logging.debug("Fetching APs from all sites in organization")  # WHY: action-log after operation
            return self._fetch_org_aps()  # WHY: return computed result
        print(f"  Fetching APs from {len(self.selected_site_ids)} selected site(s)...")  # WHY: surface user-facing mess
        logging.debug("Fetching APs from %s selected sites", len(self.selected_site_ids))  # WHY: action-log after opera
        return self._fetch_selected_sites_aps()  # WHY: return computed result

    def _fetch_org_aps(self) -> bool:  # WHY: declare private helper _fetch_org_aps
        """Fetch all APs from the organization with full pagination (PCPP)."""
        logging.info("Fetching org APs for %s", self.org_id)  # WHY: phase entry audit
        if self.apisession is None or self.org_id is None:  # WHY: precondition guard
            print("  X API session or org_id not initialized")  # WHY: user-visible error
            logging.error("API session or org_id not initialized for AP fetch")  # WHY: audit failure
            return False  # WHY: cannot proceed without session/org
        return self._fetch_org_aps_safely()  # WHY: wrap fetch in guarded helper

    def _fetch_org_aps_safely(self) -> bool:  # WHY: declare private helper _fetch_org_aps_safely
        """Guarded fetch of org devices. Return True on success, False on any error."""
        try:  # WHY: broad guard preserves pre-refactor behavior
            devices_data = self._get_org_inventory()  # WHY: hit inventory API for full page
            return self._process_inventory_result(devices_data)  # WHY: normalize + assign result
        except Exception as error:  # WHY: catch API errors + parse errors + assignment errors
            print(f"  X Error fetching devices: {error}")  # WHY: user-visible error
            logging.error("Failed to fetch org devices: %s", error)  # WHY: audit failure
            return False  # WHY: safe fallback

    def _process_inventory_result(self, devices_data: list[Any]) -> bool:  # WHY: declare private helper _process_invent
        """Normalize inventory data into self.all_aps and organize by model."""
        if not devices_data:  # WHY: guard empty response
            print("  X Failed to retrieve devices")  # WHY: user-visible error
            logging.warning("No device data returned from org inventory")  # WHY: audit empty
            return False  # WHY: nothing to process
        self.all_aps = self._filter_ap_devices(devices_data)  # WHY: keep AP-type devices only
        if not self.all_aps:  # WHY: guard zero APs
            print("  X No access points found in organization")  # WHY: user-visible error
            logging.warning("No APs found in organization")  # WHY: audit zero-AP condition
            return False  # WHY: nothing to upgrade
        logging.info("Discovered %s APs in organization", len(self.all_aps))  # WHY: audit count
        return self._organize_aps_by_model()  # WHY: build model->APs mapping

    def _get_org_inventory(self) -> list[Any]:  # WHY: declare private helper _get_org_inventory
        """Retrieve org inventory with pagination."""
        logging.info("Retrieving org inventory for org_id=%s", self.org_id)  # WHY: trace entry into inventory fetch
        if not self._has_apisession():  # WHY: guard clause on missing session
            return []  # WHY: bail out with empty inventory
        response = self._call_get_org_inventory()  # WHY: single API-boundary helper for CC reduction
        if not self._response_has_data(response):  # WHY: reuse existing response-shape predicate
            return []  # WHY: no data available, return empty list
        devices_data = self._collect_paginated_inventory(response)  # WHY: normalize paginated data into a list
        logging.debug("Retrieved %d device(s) from org inventory", len(devices_data))  # WHY: post-op observability
        return devices_data  # WHY: return normalized inventory list

    def _has_apisession(self) -> bool:  # WHY: declare private helper _has_apisession
        """Guard predicate confirming API session is present."""
        if self.apisession is None:  # WHY: single check keeps caller CC low
            print("  X API session not initialized")  # WHY: user-visible diagnostic
            logging.error("API session not initialized for org %s", self.org_id)  # WHY: audit log for missing session
            return False  # WHY: signal caller to abort
        return True  # WHY: session available, continue

    def _call_get_org_inventory(self) -> Any:  # WHY: declare private helper _call_get_org_inventory
        """Invoke mistapi getOrgInventory and return the raw response."""
        logging.info("Calling getOrgInventory for org %s", self.org_id)  # WHY: trace API-boundary call
        org_inventory_api = importlib.import_module("mistapi.api.v1.orgs.inventory")  # WHY: lazy import to keep top of
        response = org_inventory_api.getOrgInventory(  # WHY: paginated AP inventory fetch
            self.apisession, self.org_id, type="ap", limit=1000  # WHY: cap page size to reduce round-trips
        )
        logging.debug("getOrgInventory returned response=%s", bool(response))  # WHY: post-op observability
        return response  # WHY: hand raw response to shape predicate

    def _collect_paginated_inventory(self, response: Any) -> list[Any]:  # WHY: declare private helper _collect_paginate
        """Normalize mistapi paginated response into a list."""
        logging.info("Collecting paginated inventory for org %s", self.org_id)  # WHY: trace pagination step
        import mistapi  # WHY: lazy import. Only needed for pagination helper

        devices_data = mistapi.get_all(response=response, mist_session=self.apisession)  # WHY: exhaust pagination curso
        if not isinstance(devices_data, list):  # WHY: mistapi may return a single dict on empty pages
            normalized = [devices_data] if devices_data else []  # WHY: coerce scalar to list-of-one or empty list
        else:
            normalized = devices_data  # WHY: already the expected shape
        logging.debug("Paginated inventory normalized to %d device(s)", len(normalized))  # WHY: post-op observability
        return normalized  # WHY: return uniform list to caller

    @staticmethod
    def _filter_ap_devices(devices_data: list[Any]) -> list[Any]:  # WHY: declare private helper _filter_ap_devices
        """Filter list to only AP devices."""
        return [d for d in devices_data if d.get("type") == "ap" or d.get("model", "").startswith("AP")]  # WHY: return

    def _fetch_selected_sites_aps(self) -> bool:  # WHY: declare private helper _fetch_selected_sites_aps
        """Fetch APs from selected sites only."""
        try:
            self.all_aps = self._collect_aps_from_sites()  # WHY: init/update all_aps attribute

            if not self.all_aps:  # WHY: guard against missing precondition
                print("  X No access points found in selected sites")  # WHY: surface user-facing message
                return False  # WHY: return computed result

            return self._organize_aps_by_model()  # WHY: return computed result

        except Exception as error:  # WHY: handle expected error
            print(f"  X Error fetching devices: {error}")  # WHY: surface user-facing message
            logging.error("Failed to fetch site devices: %s", error)  # WHY: surface fatal issue
            return False  # WHY: return computed result

    def _collect_aps_from_sites(self) -> list[Any]:  # WHY: declare private helper _collect_aps_from_sites
        """Collect APs from each selected site."""
        all_aps: list[Any] = []  # WHY: assign computed value
        for site in self.selected_sites:  # WHY: iterate collection
            if self._check_stop_fn and self._check_stop_fn():  # WHY: branch on condition
                break  # WHY: exit loop early
            site_aps = self._fetch_site_aps(site["id"], site.get("name", "Unknown"))  # WHY: compute site_aps
            all_aps.extend(site_aps)  # WHY: advance computation
        return all_aps  # WHY: return computed result

    def _fetch_site_aps(self, site_id: str, site_name: str) -> list[Any]:  # WHY: declare private helper _fetch_site_aps
        """Fetch APs from a single site."""
        logging.info("Fetching APs from site %s (id=%s)", site_name, site_id)  # WHY: trace entry into per-site fetch
        print(f"    Fetching APs from {site_name}...")  # WHY: user-visible progress line
        response = self._call_list_site_devices(site_id)  # WHY: single API-boundary helper for CC reduction
        if not self._site_response_has_devices(response):  # WHY: guard predicate handles empty / missing data
            return []  # WHY: bail early with empty list
        site_aps = self._normalize_site_devices(response)  # WHY: coerce data payload into a list of devices
        self._tag_devices_with_site(site_aps, site_id, site_name)  # WHY: annotate every AP with originating site
        logging.debug("Fetched %d AP(s) from site %s", len(site_aps), site_name)  # WHY: post-op observability
        return site_aps  # WHY: return tagged list to caller

    def _call_list_site_devices(self, site_id: str) -> Any:  # WHY: declare private helper _call_list_site_devices
        """Invoke mistapi listSiteDevices for the given site."""
        logging.info("Calling listSiteDevices for site %s", site_id)  # WHY: trace API-boundary call
        import mistapi.api.v1.sites.devices  # WHY: lazy import to avoid module-load cost

        response = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: filtered listing by AP type
            self.apisession, site_id, type="ap"
        )
        logging.debug("listSiteDevices returned response=%s", bool(response))  # WHY: post-op observability
        return response  # WHY: hand raw response back for shape validation

    @staticmethod
    def _site_response_has_devices(response: Any) -> bool:  # WHY: declare private helper _site_response_has_devices
        """Return True when the site response carries a non-empty data payload."""
        return bool(response) and hasattr(response, "data") and bool(response.data)  # WHY: three-part shape check as gu

    @staticmethod
    def _normalize_site_devices(response: Any) -> list[Any]:  # WHY: declare private helper _normalize_site_devices
        """Return a list of devices from either a list or scalar data payload."""
        if isinstance(response.data, list):  # WHY: expected shape for multi-device sites
            return response.data  # WHY: pass list through unchanged
        return [response.data]  # WHY: coerce single-device dict to list-of-one

    @staticmethod
    def _tag_devices_with_site(devices: list[Any], site_id: str, site_name: str) -> None:  # WHY: declare private helper
        """Annotate each device dict with its originating site id and name."""
        for ap in devices:  # WHY: iterate the fetched device list
            ap["_site_id"] = site_id  # WHY: preserve owning site id downstream
            ap["_site_name"] = site_name  # WHY: preserve owning site name downstream

    def _organize_aps_by_model(self) -> bool:  # WHY: declare private helper _organize_aps_by_model
        """Organize discovered APs by model."""
        for ap in self.all_aps:  # WHY: iterate collection
            model = ap.get("model", "Unknown")  # WHY: compute model
            if model not in self.aps_by_model:  # WHY: branch on condition
                self.aps_by_model[model] = []  # WHY: compute aps_by_model
            self.aps_by_model[model].append(ap)  # WHY: advance computation

        print(f"  + Found {len(self.all_aps)} AP(s) across {len(self.aps_by_model)} model(s)")  # WHY: surface user-faci
        for model, aps in sorted(self.aps_by_model.items()):  # WHY: iterate collection
            print(f"      {model}: {len(aps)} device(s)")  # WHY: surface user-facing message

        return True  # WHY: return computed result

    # =========================================================================
    # STEP 3: FIRMWARE STATS
    # =========================================================================

    def _step3_fetch_firmware_stats(self) -> bool:  # WHY: declare private helper _step3_fetch_firmware_stats
        """Fetch current firmware versions for all discovered APs."""
        logging.debug("Entering _step3_fetch_firmware_stats()")  # WHY: action-log after operation
        self._print_step3_header()  # WHY: advance computation

        if self.apisession is None or self.org_id is None:  # WHY: branch on condition
            print("  X API session or org_id not initialized")  # WHY: surface user-facing message
            logging.error("API session or org_id not initialized for firmware stats")  # WHY: surface fatal issue
            return False  # WHY: return computed result

        try:
            self._populate_ap_versions()  # WHY: advance computation
            logging.info("Retrieved firmware versions for %s devices", len(self.ap_versions))  # WHY: action-log before
            self._display_version_distribution()  # WHY: advance computation
            return True  # WHY: return computed result
        except Exception as error:  # WHY: handle expected error
            print(f"  X Error fetching firmware stats: {error}")  # WHY: surface user-facing message
            logging.error("Failed to fetch firmware stats: %s", error)  # WHY: surface fatal issue
            return False  # WHY: return computed result

    def _print_step3_header(self) -> None:  # WHY: declare private helper _print_step3_header
        """Print Step 3 header."""
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 3: Current Firmware Versions")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  Fetching device firmware versions...")  # WHY: surface user-facing message

    def _fetch_ap_stats_data(self) -> list[Any]:  # WHY: declare private helper _fetch_ap_stats_data
        """Fetch AP stats payload from org stats API."""
        import mistapi  # Keep import local so module load stays lightweight for non-upgrade flows.

        org_stats_api = importlib.import_module(
            "mistapi.api.v1.orgs.stats"
        )  # Resolve API lazily because upgrade path is optional.
        response = org_stats_api.listOrgDevicesStats(
            self.apisession, self.org_id, type="ap", limit=1000
        )  # Request AP stats in largest supported page.
        if not response or not hasattr(
            response, "data"
        ):  # Treat missing response payload as no stats instead of raising here.
            return []  # WHY: return computed result
        stats_data = mistapi.get_all(
            response=response, mist_session=self.apisession
        )  # Expand paginated response so every discovered AP can be matched.
        return self._normalize_stats_data(
            stats_data
        )  # Normalize singleton payloads into one list shape for downstream processing.

    @staticmethod
    def _normalize_stats_data(stats_data: Any) -> list[Any]:  # WHY: declare private helper _normalize_stats_data
        """Normalize Mist stats payload into a list."""
        if isinstance(stats_data, list):  # Preserve already-expanded pagination output as-is.
            return stats_data  # WHY: return computed result
        if stats_data:  # Wrap truthy singleton payloads so loop logic never branches on shape.
            return [stats_data]  # WHY: return computed result
        return []  # Return empty list for missing payloads to keep callers simple.

    def _record_ap_version(self, stat: dict[str, Any]) -> None:  # WHY: declare private helper _record_ap_version
        """Record firmware version for one AP stat entry."""
        mac = stat.get("mac")  # Use MAC as stable lookup key because later steps map firmware by device MAC.
        if mac:  # Skip malformed stat rows that cannot be joined back to discovered APs.
            self.ap_versions[mac] = (
                stat.get("version") or "Unknown"
            )  # Preserve explicit Unknown marker for offline or incomplete devices.

    def _populate_ap_versions(self) -> None:  # WHY: declare private helper _populate_ap_versions
        """Populate ap_versions dict from org stats API."""
        if self.apisession is None:  # Leave existing state untouched when API session has not been established.
            return  # WHY: return early
        for stat in self._fetch_ap_stats_data():  # Isolate API fetch complexity from per-record state updates.
            if isinstance(stat, dict):  # Ignore any unexpected payload fragments returned by SDK helpers.
                self._record_ap_version(stat)  # Capture version mapping through one dedicated mutation helper.

    @staticmethod
    def _format_unknown_device_names(unknown_devices: list[Any]) -> str:  # WHY: declare private helper _format_unknown_
        """Format short offline-device summary."""
        device_names = [
            d.get("name", d.get("mac", "unnamed")) for d in unknown_devices[:5]
        ]  # Show recognizable identifiers for first few offline APs.
        names_str = ", ".join(device_names)  # Keep summary concise because this appears in dense distribution output.
        if len(unknown_devices) > 5:  # Avoid flooding screen when many devices lack current firmware data.
            names_str += f" +{len(unknown_devices) - 5} more"  # WHY: assign computed value
        return names_str  # Return ready-to-print label so caller only decides which format path to use.

    def _print_distribution_entry(self, version: str, count: int, unknown_devices: list[Any]) -> None:  # WHY: declare p
        """Print one firmware distribution line."""
        if (
            version == "Unknown" and unknown_devices
        ):  # Add richer context only for unknown versions linked to likely offline APs.
            names_str = self._format_unknown_device_names(
                unknown_devices
            )  # Reuse compact formatter to keep branch focused on messaging.
            print(f"      {version}: {count} device(s) - likely offline ({names_str})")  # WHY: surface user-facing mess
            return  # WHY: return early
        print(f"      {version}: {count} device(s)")  # Use simple summary for all known versions.

    def _display_version_distribution(self) -> None:  # WHY: declare private helper _display_version_distribution
        """Display firmware version distribution."""
        version_counts = self._count_versions_by_mac()  # Count by discovered AP list so offline devices remain visible.
        unknown_devices = (
            self._get_unknown_firmware_devices()
        )  # Collect offline or unreported devices once for richer Unknown output.
        print("  + Current firmware distribution:")  # Keep summary header unchanged for operator familiarity.
        for version, count in sorted(
            version_counts.items(), key=lambda x: x[0] or "", reverse=True
        ):  # Preserve descending version display order.
            self._print_distribution_entry(
                version, count, unknown_devices
            )  # Delegate special Unknown formatting to focused helper.

    def _get_unknown_firmware_devices(self) -> list[Any]:  # WHY: declare private helper _get_unknown_firmware_devices
        """Get devices with unknown firmware."""
        unknown: list[Any] = []  # WHY: assign computed value
        for ap in self.all_aps:  # WHY: iterate collection
            version = self.ap_versions.get(ap.get("mac"))  # WHY: compute version
            if not version or version == "Unknown":  # WHY: guard against missing precondition
                unknown.append(ap)  # WHY: advance computation
        return unknown  # WHY: return computed result

    def _count_versions_by_mac(self) -> dict[str, int]:  # WHY: declare private helper _count_versions_by_mac
        """Count devices by version using MAC address lookup."""
        version_counts: dict[str, int] = {}  # WHY: assign computed value
        for ap in self.all_aps:  # WHY: iterate collection
            version = self.ap_versions.get(ap.get("mac")) or "Unknown"  # WHY: compute version
            version_counts[version] = version_counts.get(version, 0) + 1  # WHY: compute version_counts
        return version_counts  # WHY: return computed result

    # =========================================================================
    # STEP 4: AVAILABLE FIRMWARE
    # =========================================================================

    def _step4_fetch_available_firmware(self) -> bool:  # WHY: declare private helper _step4_fetch_available_firmware
        """Fetch available firmware versions for each model."""
        logging.debug("Entering _step4_fetch_available_firmware()")  # WHY: action-log after operation
        self._print_step4_header()  # WHY: advance computation

        if self.apisession is None or self.org_id is None:  # WHY: branch on condition
            print("  X API session or org_id not initialized")  # WHY: surface user-facing message
            logging.error("API session or org_id not initialized for firmware fetch")  # WHY: surface fatal issue
            return False  # WHY: return computed result

        try:
            if not self._load_available_versions():  # WHY: guard against missing precondition
                print("  X Failed to retrieve available firmware versions")  # WHY: surface user-facing message
                logging.warning("Failed to load available firmware versions")  # WHY: surface non-fatal issue
                return False  # WHY: return computed result

            logging.debug("Loaded %s firmware version entries", len(self.available_versions))  # WHY: action-log after o
            self._build_model_version_mapping()  # WHY: advance computation
            return self._display_version_summary()  # WHY: return computed result

        except Exception as error:  # WHY: handle expected error
            print(f"  X Error fetching available firmware: {error}")  # WHY: surface user-facing message
            logging.error("Failed to fetch available firmware: %s", error)  # WHY: surface fatal issue
            return False  # WHY: return computed result

    def _print_step4_header(self) -> None:  # WHY: declare private helper _print_step4_header
        """Print Step 4 header."""
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 4: Available Firmware Versions")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  Fetching available firmware for each model...")  # WHY: surface user-facing message

    def _load_available_versions(self) -> bool:  # WHY: declare private helper _load_available_versions
        """Load available firmware versions from API."""
        if self.apisession is None:  # WHY: branch on condition
            print("  X API session not initialized")  # WHY: surface user-facing message
            return False  # WHY: return computed result
        org_devices_api = importlib.import_module("mistapi.api.v1.orgs.devices")  # WHY: compute org_devices_api
        response = org_devices_api.listOrgAvailableDeviceVersions(self.apisession, self.org_id, type="ap")  # WHY: compu

        if not response or not hasattr(response, "data"):  # WHY: guard against missing precondition
            return False  # WHY: return computed result

        self.available_versions = response.data if isinstance(response.data, list) else []  # WHY: init/update available
        return True  # WHY: return computed result

    def _build_model_version_mapping(self) -> None:  # WHY: declare private helper _build_model_version_mapping
        """Build model-to-versions mapping from available_versions."""
        logging.info("Building model->versions mapping from %d version entries", len(self.available_versions))
        for version_info in self.available_versions:  # WHY: single loop reduces branching in caller
            self._accumulate_version_entry(version_info)  # WHY: each entry handled by predicate + append helper
        logging.debug("Model->versions mapping now covers %d model(s)", len(self.model_version_ranges))  # WHY: post-op

    def _accumulate_version_entry(self, version_info: Any) -> None:  # WHY: declare private helper _accumulate_version_e
        """Add a single version entry to the model->versions mapping."""
        if not isinstance(version_info, dict):  # WHY: skip malformed entries defensively
            return  # WHY: nothing to accumulate
        model = version_info.get("model")  # WHY: model key drives bucket selection
        version = version_info.get("version")  # WHY: version value goes into the bucket
        if not (model and version):  # WHY: skip incomplete rows
            return  # WHY: partial data cannot form a mapping row
        self.model_version_ranges.setdefault(model, []).append(version)  # WHY: create-or-append in one call

    def _display_version_summary(self) -> bool:  # WHY: declare private helper _display_version_summary
        """Display version summary for discovered models."""
        models_found = 0  # WHY: compute models_found
        for model in self.aps_by_model:  # WHY: iterate collection
            if model in self.model_version_ranges:  # WHY: branch on condition
                models_found += 1  # WHY: assign computed value
                print(f"    {model}: {len(self.model_version_ranges[model])} version(s) available")  # WHY: surface user
            else:
                print(f"    {model}: No firmware versions found")  # WHY: surface user-facing message

        if models_found == 0:  # WHY: branch on condition
            print("  X No firmware versions available for discovered models")  # WHY: surface user-facing message
            return False  # WHY: return computed result

        print(f"  + Loaded firmware data for {models_found} model(s)")  # WHY: surface user-facing message
        return True  # WHY: return computed result

    # =========================================================================
    # STEP 5: VERSION SELECTION
    # =========================================================================

    def _step5_select_firmware_versions(self) -> bool:  # WHY: declare private helper _step5_select_firmware_versions
        """Let user select firmware version for each model."""
        logging.debug("Entering _step5_select_firmware_versions()")  # WHY: action-log after operation
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 5: Firmware Version Selection")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message

        model_selections = self._collect_model_selections()  # WHY: compute model_selections

        if not model_selections:  # WHY: guard against missing precondition
            print("\n  X No upgrades selected")  # WHY: surface user-facing message
            logging.warning("No firmware versions selected by user")  # WHY: surface non-fatal issue
            return False  # WHY: return computed result

        logging.info("User selected firmware for %s model(s)", len(model_selections))  # WHY: action-log before operatio
        self._organize_by_version(model_selections)  # WHY: advance computation
        return True  # WHY: return computed result

    def _collect_model_selections(self) -> dict[str, Any]:  # WHY: declare private helper _collect_model_selections
        """Collect firmware version selections for each model."""
        model_selections: dict[str, Any] = {}  # WHY: assign computed value

        for model, devices in sorted(self.aps_by_model.items()):  # WHY: iterate collection
            selection = self._process_single_model(model, devices)  # WHY: compute selection
            if selection is None:  # WHY: branch on condition
                return {}  # WHY: return computed result
            if selection:  # WHY: branch on condition
                model_selections[model] = selection  # WHY: compute model_selections

        return model_selections  # WHY: return computed result

    def _process_single_model(self, model: str, devices: list[Any]) -> dict[str, Any] | None:  # WHY: private helper
        """Process version selection for a single model."""
        model_versions = self._get_versions_for_model(model)  # WHY: compute model_versions
        if not model_versions:  # WHY: guard against missing precondition
            print(f"  ! No firmware versions found for {model} - skipping")  # WHY: surface user-facing message
            return {}  # WHY: return computed result

        current_versions = set(self.ap_versions.get(d.get("mac"), "Unknown") for d in devices)  # WHY: compute current_v
        self._display_model_options(model, devices, model_versions, current_versions)  # WHY: advance computation

        user_input = self._get_version_selection_input(model_versions)  # WHY: compute user_input
        if user_input is None:  # WHY: branch on condition
            return None  # WHY: return computed result
        if user_input == "s":  # WHY: branch on condition
            print(f"    Skipping {model}")  # WHY: surface user-facing message
            return {}  # WHY: return computed result

        return self._apply_version_selection(model, devices, model_versions, user_input)  # WHY: return computed result

    def _display_model_options(  # WHY: declare private helper _display_model_options
        self,
        model: str,
        devices: list[Any],
        model_versions: list[Any],
        current_versions: set[str],
    ) -> None:
        """Display available firmware versions for a model."""
        print(f"\n  Model: {model} ({len(devices)} devices)")  # WHY: surface user-facing message
        self._print_current_versions(devices, current_versions)  # WHY: advance computation
        print("    Available versions:")  # WHY: surface user-facing message
        self._print_version_list(model_versions, current_versions)  # WHY: advance computation

    def _get_unknown_devices_for_model(self, devices: list[Any]) -> list[Any]:  # WHY: declare private helper _get_unkno
        """Return devices whose current firmware version is unknown."""
        return [
            d for d in devices if self.ap_versions.get(d.get("mac"), "Unknown") == "Unknown"
        ]  # Keep offline detection consistent with earlier summaries.

    @staticmethod
    def _get_known_current_versions(current_versions: set[str]) -> list[str]:  # WHY: declare private helper _get_known_
        """Return sorted known firmware versions."""
        return sorted(
            [version for version in current_versions if version != "Unknown"], reverse=True
        )  # Exclude Unknown so current-version line stays precise.

    @staticmethod
    def _format_offline_device_names(unknown_devs: list[Any]) -> str:  # WHY: declare private helper _format_offline_dev
        """Format short list of offline device names."""
        offline_names = ", ".join(
            [d.get("name", d.get("mac", "unnamed")[:8]) for d in unknown_devs[:3]]
        )  # Prefer human-friendly names while keeping width manageable.
        if len(unknown_devs) > 3:  # Collapse long tails so summary remains readable in terminal width.
            offline_names += f" +{len(unknown_devs) - 3} more"  # WHY: assign computed value
        return offline_names  # Return one compact label for caller to print.

    def _print_current_versions(self, devices: list[Any], current_versions: set[str]) -> None:  # WHY: declare private h
        """Print current version info including offline devices."""
        if "Unknown" not in current_versions:  # Use compact one-line output when all devices report a concrete version.
            print(f"    Current: {', '.join(sorted(current_versions, reverse=True))}")  # WHY: surface user-facing messa
            return  # WHY: return early
        unknown_devs = self._get_unknown_devices_for_model(
            devices
        )  # Gather offline devices once so both count and names stay aligned.
        known_versions = self._get_known_current_versions(
            current_versions
        )  # Separate known versions from Unknown marker for cleaner messaging.
        offline_names = self._format_offline_device_names(
            unknown_devs
        )  # Reuse compact formatter to avoid long inline list logic.
        if known_versions:  # Only print known-version line when at least one device reports firmware successfully.
            print(f"    Current: {', '.join(known_versions)}")  # WHY: surface user-facing message
        print(
            f"    Offline ({len(unknown_devs)}): {offline_names}"
        )  # Always show offline count when Unknown appears in current set.

    @staticmethod
    def _print_version_list(model_versions: list[Any], current_versions: set[str]) -> None:  # WHY: declare private help
        """Print numbered list of available firmware versions."""
        for idx, version_info in enumerate(model_versions):  # WHY: iterate collection
            version_num = version_info.get("version", "Unknown")  # WHY: compute version_num
            indicators: list[str] = []  # WHY: assign computed value
            if version_info.get("recommended"):  # WHY: branch on condition
                indicators.append("RECOMMENDED")  # WHY: advance computation
            if version_num in current_versions:  # WHY: branch on condition
                indicators.append("CURRENT")  # WHY: advance computation
            ind_text = f" [{', '.join(indicators)}]" if indicators else ""  # WHY: compute ind_text
            print(f"      [{idx}] {version_num}{ind_text}")  # WHY: surface user-facing message

    def _get_version_selection_input(self, model_versions: list[Any]) -> str | None:  # WHY: declare private helper _get
        """Get user input for version selection."""
        try:
            return (  # WHY: return computed result
                self._input_fn(
                    f"    Select version (0-{len(model_versions) - 1}, 's' to skip): ",
                    "version_select",
                )
                .strip()
                .lower()
            )
        except SystemExit:  # WHY: handle expected error
            return None  # WHY: return computed result

    def _apply_version_selection(  # WHY: declare private helper _apply_version_selection
        self,
        model: str,
        devices: list[Any],
        model_versions: list[Any],
        user_input: str,
    ) -> dict[str, Any]:
        """Apply user's version selection for a model (PCPP)."""
        selected = self._resolve_selected_version(model_versions, user_input)  # WHY: validate numeric pick
        if selected is None:  # WHY: guard invalid input
            print("    Invalid input - skipping model")  # WHY: user-visible skip notice
            return {}  # WHY: caller drops model from plan
        raw_version = selected.get("version")  # WHY: extract raw dict value before narrowing type
        if not isinstance(raw_version, str):  # WHY: narrow Any|None -> str for downstream helper
            print(f"    Invalid version data for {model} - skipping model")  # WHY: user-visible skip notice
            return {}  # WHY: caller drops model when version metadata is malformed
        target_version: str = raw_version  # WHY: bind narrowed type for helper signature
        devices_needing = self._get_devices_needing_version(devices, target_version)  # WHY: filter no-op devices
        if not devices_needing:  # WHY: guard case where all devices already match target
            print(f"    All {model} devices already at {target_version}")  # WHY: user-visible no-op notice
            return {}  # WHY: nothing to upgrade for this model
        return self._finalize_version_selection(target_version, devices, devices_needing)  # WHY: record + emit plan

    def _finalize_version_selection(  # WHY: declare private helper _finalize_version_selection
        self,
        target_version: str,
        devices: list[Any],
        devices_needing: list[Any],
    ) -> dict[str, Any]:
        """Record skipped devices, emit confirmation, and build plan entry."""
        self._record_already_at_target_devices(len(devices), len(devices_needing))  # WHY: track skipped devices
        print(f"    + Selected {target_version} for {len(devices_needing)} device(s)")  # WHY: user-visible confirm
        logging.debug("Version %s applied to %d devices", target_version, len(devices_needing))  # WHY: audit
        return {"version": target_version, "devices": devices_needing}  # WHY: plan entry for orchestrator

    @staticmethod
    def _resolve_selected_version(model_versions: list[Any], user_input: str) -> dict[str, Any] | None:  # WHY: declare
        """Resolve validated user selection to a version entry."""
        try:
            idx = int(user_input)  # Accept only explicit numeric menu choices from operator input.
        except ValueError:  # WHY: handle expected error
            return None  # Reject non-numeric tokens so caller can skip model safely.
        if 0 <= idx < len(model_versions):  # Ensure index points at an available version before returning record.
            result: dict[str, Any] = model_versions[idx]  # Narrow Any to expected dict shape for mypy strict.
            return result  # WHY: return computed result
        return None  # Reject out-of-range menu choices without mutating plan state.

    def _get_devices_needing_version(self, devices: list[Any], target_version: Any) -> list[Any]:  # WHY: declare privat
        """Return devices not already on the target firmware."""
        return [
            d for d in devices if self.ap_versions.get(d.get("mac")) != target_version
        ]  # Use MAC lookup so offline devices still remain eligible.

    def _record_already_at_target_devices(self, total_devices: int, devices_needing: int) -> None:  # WHY: declare priva
        """Record and display count of devices already on target."""
        skipped = (
            total_devices - devices_needing
        )  # Compute no-op count once because both print and counter need same value.
        if skipped:  # Only mention skipped devices when optimization actually removed work.
            print(f"    Skipping {skipped} device(s) already at target")  # WHY: surface user-facing message
            self.skipped_already_at_target += skipped  # Preserve cumulative metric for final summary reporting.

    @staticmethod
    def _version_matches_model(version_entry: dict[str, Any], model: str) -> bool:  # WHY: declare private helper _versi
        """Check whether a firmware entry applies to a model."""
        models = version_entry.get("models", [])  # Prefer explicit multi-model compatibility list when present.
        single_model = version_entry.get("model")  # Fall back to legacy single-model field for older API responses.
        return (
            model in models or single_model == model
        )  # Support both response shapes without branching in main collector.

    def _collect_matching_versions(self, model: str) -> list[Any]:  # WHY: declare private helper _collect_matching_vers
        """Collect firmware entries that apply to a model."""
        matching: list[Any] = []  # Keep collector local so caller receives only model-relevant entries.
        for version_entry in self.available_versions:  # Scan raw API list once for target model compatibility.
            if isinstance(version_entry, dict) and self._version_matches_model(version_entry, model):  # WHY: branch on
                matching.append(
                    version_entry
                )  # Preserve original entry so later callers retain recommended flags and metadata.
        return matching  # WHY: return computed result

    @staticmethod
    def _deduplicate_version_entries(version_entries: list[Any]) -> list[Any]:  # WHY: declare private helper _deduplica
        """Deduplicate firmware entries by version string."""
        seen: set[str] = set()  # Track emitted versions so duplicate compatibility rows collapse cleanly.
        unique: list[Any] = []  # Preserve first occurrence because it carries full metadata already.
        for version_entry in version_entries:  # Walk in API order before final sorting deduplicates versions.
            version_num = version_entry.get("version")  # Deduplicate by displayed firmware version value.
            if version_num and version_num not in seen:  # WHY: branch on condition
                seen.add(version_num)  # WHY: advance computation
                unique.append(version_entry)  # WHY: advance computation
        return unique  # WHY: return computed result

    @staticmethod
    def _build_version_sort_key(version_entry: dict[str, Any]) -> tuple[bool, tuple[int, ...], str]:  # WHY: declare pri
        """Build comparable key for version sorting."""
        version_num = str(
            version_entry.get("version", "")
        )  # Normalize missing values to empty string for stable sorting.
        numeric_parts = tuple(
            int(part) for part in version_num.split(".") if part.isdigit()
        )  # Parse dotted numeric versions without raising on suffixes.
        is_fully_numeric = bool(version_num) and all(
            part.isdigit() for part in version_num.split(".")
        )  # Ensure partially numeric tags do not outrank clean semantic versions.
        return (
            is_fully_numeric,
            numeric_parts,
            version_num,
        )  # Favor numeric versions, then numeric tuple, then raw string as final tiebreaker.

    def _get_versions_for_model(self, model: str) -> list[Any]:  # WHY: declare private helper _get_versions_for_model
        """Get sorted versions for a model."""
        matching_versions = self._collect_matching_versions(
            model
        )  # Isolate compatibility filtering from dedupe and sort steps.
        unique_versions = self._deduplicate_version_entries(
            matching_versions
        )  # Collapse duplicate version rows before presenting choices.
        unique_versions.sort(
            key=self._build_version_sort_key, reverse=True
        )  # Keep highest numeric or lexical versions first for operator convenience.
        return unique_versions  # WHY: return computed result

    def _organize_by_version(self, model_selections: dict[str, Any]) -> None:  # WHY: declare private helper _organize_b
        """Reorganize selections by version for org-level API."""
        logging.info("Organizing %d model selection(s) by version", len(model_selections))  # WHY: trace entry
        self._accumulate_version_buckets(model_selections)  # WHY: mutate upgrade_plan in a single helper
        self._print_upgrade_plan_summary()  # WHY: user-visible per-version summary
        self._print_api_efficiency_summary()  # WHY: user-visible API-call count report
        logging.debug("Upgrade plan now contains %d version bucket(s)", len(self.upgrade_plan))  # WHY: post-op observab

    def _accumulate_version_buckets(self, model_selections: dict[str, Any]) -> None:  # WHY: declare private helper _acc
        """Populate self.upgrade_plan by rearranging model->version into version->models."""
        for model, data in model_selections.items():  # WHY: single pass over model selections
            version = data["version"]  # WHY: bucket key is the target version
            device_ids = [d.get("id") for d in data["devices"] if d.get("id")]  # WHY: keep only devices with ids
            bucket = self.upgrade_plan.setdefault(  # WHY: create-or-fetch bucket in one call
                version, {"models": [], "device_ids": []}
            )
            bucket["models"].append(model)  # WHY: record contributing model name
            bucket["device_ids"].extend(device_ids)  # WHY: aggregate device ids into bucket

    def _print_upgrade_plan_summary(self) -> None:  # WHY: declare private helper _print_upgrade_plan_summary
        """Print the per-version summary block."""
        print("\n  Upgrade Plan Summary (grouped by version):")  # WHY: section header for user output
        for version, data in sorted(self.upgrade_plan.items()):  # WHY: deterministic sort for repeatable UX
            models_str = ", ".join(data["models"])  # WHY: comma-join for compact display
            print(f"    {version}: {len(data['device_ids'])} device(s) ({models_str})")  # WHY: one line per version buc

    def _print_api_efficiency_summary(self) -> None:  # WHY: declare private helper _print_api_efficiency_summary
        """Print the API-call efficiency block."""
        print("\n  API Efficiency:")  # WHY: section header for efficiency block
        print(f"    - Org-level calls needed: {len(self.upgrade_plan)}")  # WHY: baseline of org-scope calls
        if self.target_all_sites:  # WHY: no savings comparison when all sites selected
            return  # WHY: skip comparative block
        site_count = len(self.selected_site_ids)  # WHY: derive site cardinality for comparison
        site_level_calls = site_count * len(self.upgrade_plan)  # WHY: hypothetical site-scoped call total
        print(f"    - Site-level would need: ~{site_level_calls} calls")  # WHY: what we would have paid without org sco
        print(f"    - Savings: {site_level_calls - len(self.upgrade_plan)} fewer API calls")  # WHY: net savings figure

    # =========================================================================
    # STEP 6: UPGRADE CONFIGURATION
    # =========================================================================

    def _step6_configure_upgrade(self) -> bool:  # WHY: declare private helper _step6_configure_upgrade
        """Configure upgrade parameters."""
        logging.info("Entering _step6_configure_upgrade()")  # WHY: trace entry into step 6
        self._print_step6_header()  # WHY: user-visible step banner
        if not self._run_configuration_stages():  # WHY: table-driven stage runner keeps CC low
            return False  # WHY: any stage cancellation aborts step 6
        if not self._apply_default_settings():  # WHY: fill in defaults after user answers
            return False  # WHY: defaults failure aborts step 6
        self._display_configuration()  # WHY: show the composed configuration to user
        logging.info("Upgrade configuration complete: %s", self.upgrade_config)  # WHY: audit final config payload
        return True  # WHY: step 6 succeeded

    def _run_configuration_stages(self) -> bool:  # WHY: declare private helper _run_configuration_stages
        """Iterate the ordered configuration stages, bailing on first cancel."""
        stages = (  # WHY: dispatch table replaces 4 if-guards
            (self._configure_download_strategy, "Download strategy configuration cancelled"),
            (self._configure_reboot_strategy, "Reboot strategy configuration cancelled"),
            (self._configure_scheduling, "Scheduling configuration cancelled"),
            (self._configure_p2p, "P2P configuration cancelled"),
        )
        for stage_fn, cancel_msg in stages:  # WHY: single loop keeps caller CC at 2
            if not stage_fn():  # WHY: each stage returns bool
                logging.info(cancel_msg)  # WHY: audit which stage cancelled
                return False  # WHY: propagate cancellation upward
        return True  # WHY: all stages accepted user input

    def _print_step6_header(self) -> None:  # WHY: declare private helper _print_step6_header
        """Print Step 6 header."""
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 6: Upgrade Configuration")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message

    def _configure_download_strategy(self) -> bool:  # WHY: declare private helper _configure_download_strategy
        """Configure download strategy."""
        print("\n  Download Strategy:")  # WHY: surface user-facing message
        print("    [1] big_bang - Download to all devices simultaneously")  # WHY: surface user-facing message
        print("    [2] serial - Download to one device at a time")  # WHY: surface user-facing message
        print("    [3] canary - Download in phases")  # WHY: surface user-facing message

        try:
            choice = self._input_fn("  Select (1-3) [1]: ", "dl_strategy").strip() or "1"  # WHY: compute choice
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        strategies = {"1": "big_bang", "2": "serial", "3": "canary"}  # WHY: compute strategies
        self.upgrade_config["download_strategy"] = strategies.get(choice, "big_bang")  # WHY: assign computed value
        return True  # WHY: return computed result

    def _configure_reboot_strategy(self) -> bool:  # WHY: declare private helper _configure_reboot_strategy
        """Configure reboot strategy."""
        print("\n  Reboot Strategy:")  # WHY: surface user-facing message
        print("    [1] big_bang - Reboot all devices simultaneously")  # WHY: surface user-facing message
        print("    [2] serial - Reboot one device at a time")  # WHY: surface user-facing message
        print("    [3] rrm - RF-aware sequential reboot")  # WHY: surface user-facing message
        print("    [4] canary - Reboot in phases")  # WHY: surface user-facing message

        try:
            choice = self._input_fn("  Select (1-4) [1]: ", "rb_strategy").strip() or "1"  # WHY: compute choice
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        strategies = {"1": "big_bang", "2": "serial", "3": "rrm", "4": "canary"}  # WHY: compute strategies
        self.upgrade_config["reboot_strategy"] = strategies.get(choice, "big_bang")  # WHY: assign computed value
        return True  # WHY: return computed result

    @staticmethod
    def _normalize_relative_offset_input(offset_str: str) -> str:  # WHY: declare private helper _normalize_relative_off
        """Normalize relative-offset text before pattern matching."""
        normalized = offset_str.strip().lower()  # Collapse surrounding whitespace and case so regex rules stay simple.
        if normalized.startswith(
            "in "
        ):  # Remove conversational prefix because parser only cares about quantity and unit.
            return normalized[3:].strip()  # WHY: return computed result
        if normalized.startswith("+"):  # Remove symbolic relative marker for same reason as natural-language prefix.
            return normalized[1:].strip()  # WHY: return computed result
        return normalized  # Return untouched normalized text when no prefix stripping is required.

    @staticmethod
    def _iter_relative_offset_patterns() -> tuple[tuple[str, str], ...]:  # WHY: declare private helper _iter_relative_o
        """Return supported relative-offset regex patterns."""
        return (  # Keep accepted units centralized so schedule parsers share one grammar.
            (r"^(\d+)\s*m(?:in(?:ute)?s?)?$", "minutes"),
            (r"^(\d+)\s*h(?:(?:ou)?rs?)?$", "hours"),
            (r"^(\d+)\s*d(?:ays?)?$", "days"),
        )

    @staticmethod
    def _build_relative_timedelta(value: int, unit: str) -> timedelta:  # WHY: declare private helper _build_relative_ti
        """Build a timedelta from parsed relative units."""
        delta_factories = {  # Map units to constructors so caller avoids branching by unit.
            "minutes": timedelta(minutes=value),
            "hours": timedelta(hours=value),
            "days": timedelta(days=value),
        }
        return delta_factories[unit]  # WHY: return computed result

    def _parse_relative_offset(self, offset_str: str) -> timedelta | None:  # WHY: declare private helper _parse_relativ
        """Parse relative time offset like 'in 15 minutes', '+3h', '2 days'."""
        normalized = self._normalize_relative_offset_input(
            offset_str
        )  # Normalize once so each regex sees same canonical text.
        for (
            pattern,
            unit,
        ) in self._iter_relative_offset_patterns():  # Try each supported relative unit until one matches.
            match = re.match(pattern, normalized)  # WHY: compute match
            if match:  # WHY: branch on condition
                value = int(match.group(1))  # Convert captured quantity only after syntax is known to be valid.
                return self._build_relative_timedelta(value, unit)  # WHY: return computed result
        return None  # Return no match when string does not fit any supported relative format.

    def _parse_time_input(  # WHY: declare private helper _parse_time_input
        self,
        time_str: str,
        base_datetime: datetime | None = None,
        is_for_reboot: bool = False,
    ) -> str | None:
        """Parse time input to ISO 8601 format."""
        logging.info("Parsing time input=%r is_for_reboot=%s", time_str, is_for_reboot)  # WHY: trace parser entry
        if self._is_immediate_time(time_str):  # WHY: guard clause on empty / 'now' sentinel
            return None  # WHY: immediate execution has no ISO stamp
        normalized = time_str.strip()  # WHY: single normalization for downstream parsers
        use_site_local = self.upgrade_config.get("use_site_local_time", False)  # WHY: pass-through config toggle
        ctx = (normalized, base_datetime, is_for_reboot, use_site_local)  # WHY: bundle parser args to keep call sites n
        for strategy in (self._try_parse_relative, self._try_parse_after):  # WHY: table-driven strategy list (R-5)
            matched, value = self._resolve_time_strategy(strategy, ctx)  # WHY: bool tuple replaces sentinel
            if matched:  # WHY: bool tuple element narrows dispatcher outcome without object type
                logging.debug("_parse_time_input resolved via %s", strategy.__name__)  # WHY: audit which parser hit
                return value  # WHY: return final ISO string or None
        result = self._parse_absolute_time(normalized, use_site_local)  # WHY: fall-through to absolute-time parser
        logging.debug("_parse_time_input absolute result=%s", result)  # WHY: post-op observability
        return result  # WHY: return absolute-time parser result

    @staticmethod
    def _is_immediate_time(time_str: str) -> bool:  # WHY: declare private helper _is_immediate_time
        """Return True when input signals 'run immediately' (empty or 'now')."""
        return not time_str or time_str.lower() in ("now", "immediate", "")  # WHY: single-line predicate keeps caller

    def _resolve_time_strategy(  # WHY: declare private helper _resolve_time_strategy
        self, strategy: Any, ctx: tuple[str, datetime | None, bool, bool]
    ) -> tuple[bool, str | None]:
        """Invoke a parser strategy. Return (matched, resolved_value) for the dispatcher."""
        outcome = strategy(*ctx)  # WHY: unpack ctx into strategy's argument list
        if outcome is None:  # WHY: None means 'strategy did not match'
            return (False, None)  # WHY: dispatcher keeps iterating on unmatched strategy
        if outcome == "":  # WHY: empty string means 'matched but produced no result'
            return (True, None)  # WHY: normalize to Python None for caller
        return (True, str(outcome))  # WHY: coerce Any -> str for strict return type

    def _try_parse_after(  # WHY: declare private helper _try_parse_after
        self,
        time_str: str,
        base_datetime: datetime | None,
        is_for_reboot: bool,
        use_site_local: bool,
    ) -> str | None:
        """Try parsing 'X after' format. Returns None if not matching, '' for no result."""
        logging.info("Trying 'after' parser on input=%r", time_str)  # WHY: trace parser entry
        if "after" not in time_str.lower():  # WHY: fast-exit predicate for non-matching input
            return None  # WHY: signal 'not this format'
        if self._reboot_relative_disallowed(is_for_reboot, use_site_local):  # WHY: single predicate for combined-mode g
            return ""  # WHY: matched but produced no result
        result = self._compute_after_offset(time_str, base_datetime)  # WHY: extracted arithmetic helper keeps CC low
        logging.debug("_try_parse_after result=%r", result)  # WHY: post-op observability
        return result  # WHY: return offset stamp or '' fallthrough

    def _reboot_relative_disallowed(self, is_for_reboot: bool, use_site_local: bool) -> bool:  # WHY: private helper
        """Predicate: reboot + site-local means relative offsets are disallowed."""
        if use_site_local and is_for_reboot:  # WHY: combined-mode restriction from prior behavior
            print("    ! Relative times not supported for reboot in site-local mode. Use HH:MM format.")  # WHY: user-vi
            return True  # WHY: signal caller to bail
        return False  # WHY: normal path allowed

    def _compute_after_offset(self, time_str: str, base_datetime: datetime | None) -> str:  # WHY: declare private helpe
        """Compute the ISO 8601 stamp for 'X after' relative offsets."""
        after_idx = time_str.lower().find("after")  # WHY: locate the 'after' token position
        time_portion = time_str[:after_idx].strip()  # WHY: portion before 'after' carries the offset
        relative_offset = self._parse_relative_offset(time_portion)  # WHY: reuse existing relative-offset parser
        if relative_offset and base_datetime:  # WHY: both offset and anchor required
            target_dt = base_datetime + relative_offset  # WHY: add offset to caller-provided anchor
            return target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # WHY: emit ISO 8601 stamp
        return ""  # WHY: matched but no result

    def _try_parse_relative(  # WHY: declare private helper _try_parse_relative
        self,
        time_str: str,
        base_datetime: datetime | None,
        is_for_reboot: bool,
        use_site_local: bool,
    ) -> str | None:
        """Try parsing as relative offset. Returns None if not relative, '' to signal no result."""
        relative_offset = self._parse_relative_offset(time_str)  # WHY: compute relative_offset
        if not relative_offset:  # WHY: guard against missing precondition
            return None  # WHY: return computed result
        if use_site_local and is_for_reboot:  # WHY: branch on condition
            print("    ! Relative times not supported for reboot in site-local mode. Use HH:MM format.")  # WHY: surface
            return ""  # WHY: return computed result
        target_dt = (base_datetime or datetime.now(UTC)) + relative_offset  # WHY: compute target_dt
        return target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # WHY: return computed result

    @staticmethod
    def _strip_utc_suffix(time_str: str) -> tuple[str, bool]:  # WHY: declare private helper _strip_utc_suffix
        """Strip optional UTC suffix from time input."""
        is_utc = time_str.upper().endswith(" UTC")  # Detect explicit timezone token before trimming text.
        if is_utc:  # WHY: branch on condition
            return time_str[:-4].strip(), True  # Remove suffix so remaining parser sees raw HH:MM content.
        return time_str, False  # Keep original text when no explicit UTC suffix is present.

    @staticmethod
    def _parse_hour_minute_parts(time_str: str) -> tuple[int, int] | None:  # WHY: declare private helper _parse_hour_mi
        """Parse validated HH:MM components."""
        try:
            time_parts = time_str.split(":")  # Split once on colon because only HH:MM format is supported.
            if len(time_parts) != 2:  # WHY: branch on condition
                return None  # WHY: return computed result
            hour = int(time_parts[0])  # Convert hour only after structural validation succeeds.
            minute = int(time_parts[1])  # Convert minute from same validated shape.
        except (ValueError, IndexError):  # WHY: handle expected error
            return None  # Reject malformed numeric parts without propagating parse exceptions.
        if 0 <= hour <= 23 and 0 <= minute <= 59:  # Enforce valid 24-hour clock range before formatting.
            return hour, minute  # WHY: return computed result
        return None  # Reject impossible times so callers can re-prompt operator.

    def _parse_absolute_time(self, time_str: str, use_site_local: bool) -> str | None:  # WHY: declare private helper _p
        """Parse absolute HH:MM time input."""
        normalized_time, is_utc = self._strip_utc_suffix(
            time_str
        )  # Separate suffix handling from numeric parsing for reuse.
        parsed_parts = self._parse_hour_minute_parts(
            normalized_time
        )  # Parse and validate HH:MM once for both UTC and site-local modes.
        if parsed_parts is None:  # WHY: branch on condition
            return None  # WHY: return computed result
        hour, minute = parsed_parts  # Unpack only after successful validation keeps values trustworthy.
        if use_site_local:  # Site-local mode keeps local wall-clock value without UTC conversion.
            return self._format_site_local_time(hour, minute)  # WHY: return computed result
        return self._format_utc_time(
            hour, minute, is_utc
        )  # Global mode converts plain local or explicit UTC input appropriately.

    @staticmethod
    def _format_site_local_time(hour: int, minute: int) -> str:  # WHY: declare private helper _format_site_local_time
        """Format time for site-local scheduling."""
        now = datetime.now()  # WHY: compute now
        target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)  # WHY: compute target_dt
        if target_dt <= now:  # WHY: branch on condition
            target_dt += timedelta(days=1)  # WHY: assign computed value
        return target_dt.strftime("%Y-%m-%dT%H:%M:%S")  # WHY: return computed result

    @staticmethod
    def _format_utc_time(hour: int, minute: int, is_utc: bool) -> str:  # WHY: declare private helper _format_utc_time
        """Format time for UTC scheduling."""
        if is_utc:  # WHY: branch on condition
            now = datetime.now(UTC)  # WHY: compute now
            target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)  # WHY: compute target_dt
            if target_dt <= now:  # WHY: branch on condition
                target_dt += timedelta(days=1)  # WHY: assign computed value
            return target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # WHY: return computed result
        now_utc = datetime.now(UTC)  # WHY: compute now_utc
        local_now = datetime.now()  # WHY: compute local_now
        target_local = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)  # WHY: compute target_local
        if target_local <= local_now:  # WHY: branch on condition
            target_local += timedelta(days=1)  # WHY: assign computed value
        utc_offset = now_utc.replace(tzinfo=None) - local_now  # WHY: compute utc_offset
        target_utc = target_local + utc_offset  # WHY: compute target_utc
        return target_utc.strftime("%Y-%m-%dT%H:%M:%SZ")  # WHY: return computed result

    def _parse_download_datetime(self, time_str: str) -> datetime | None:  # WHY: declare private helper _parse_download
        """Parse download time as datetime for reboot offset calculation."""
        if not time_str or time_str.lower() in ["now", "immediate", ""]:  # WHY: guard against missing precondition
            return None  # WHY: return computed result

        time_str = time_str.strip()  # WHY: compute time_str

        relative_offset = self._parse_relative_offset(time_str)  # WHY: compute relative_offset
        if relative_offset:  # WHY: branch on condition
            return datetime.now(UTC) + relative_offset  # WHY: return computed result

        return self._parse_download_absolute(time_str)  # WHY: return computed result

    def _parse_download_absolute(self, time_str: str) -> datetime | None:  # WHY: declare private helper _parse_download
        """Parse absolute time string into datetime for download scheduling."""
        normalized_time, is_utc = self._strip_utc_suffix(
            time_str
        )  # Reuse same UTC-suffix logic as string formatter to keep behavior aligned.
        parsed_parts = self._parse_hour_minute_parts(
            normalized_time
        )  # Share HH:MM validation so absolute parsers reject same invalid inputs.
        if parsed_parts is None:  # WHY: branch on condition
            return None  # WHY: return computed result
        hour, minute = parsed_parts  # Unpack only after validation ensures values fit datetime replace().
        if is_utc:  # Explicit UTC input should not be treated as local wall-clock time.
            return self._resolve_utc_datetime(hour, minute)  # WHY: return computed result
        return self._resolve_local_to_utc_datetime(hour, minute)  # Default plain HH:MM input to operator local time.

    @staticmethod
    def _resolve_utc_datetime(hour: int, minute: int) -> datetime:  # WHY: declare private helper _resolve_utc_datetime
        """Resolve hour:minute in UTC to next occurrence."""
        now = datetime.now(UTC)  # WHY: compute now
        target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)  # WHY: compute target_dt
        if target_dt <= now:  # WHY: branch on condition
            target_dt += timedelta(days=1)  # WHY: assign computed value
        return target_dt  # WHY: return computed result

    @staticmethod
    def _resolve_local_to_utc_datetime(hour: int, minute: int) -> datetime:  # WHY: declare private helper _resolve_loca
        """Resolve local hour:minute to UTC datetime."""
        now_utc = datetime.now(UTC)  # WHY: compute now_utc
        local_now = datetime.now()  # WHY: compute local_now
        target_local = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)  # WHY: compute target_local
        if target_local <= local_now:  # WHY: branch on condition
            target_local += timedelta(days=1)  # WHY: assign computed value
        offset = now_utc.replace(tzinfo=None) - local_now  # WHY: compute offset
        return target_local + offset  # WHY: return computed result

    def _configure_scheduling(self) -> bool:  # WHY: declare private helper _configure_scheduling
        """Configure download and reboot scheduling."""
        if not self._configure_time_mode():  # WHY: guard against missing precondition
            return False  # WHY: return computed result
        if not self._configure_download_schedule():  # WHY: guard against missing precondition
            return False  # WHY: return computed result
        return self._configure_reboot_schedule()  # WHY: return computed result

    def _configure_time_mode(self) -> bool:  # WHY: declare private helper _configure_time_mode
        """Prompt for UTC vs site-local time mode."""
        print("\n  Time Zone Mode:")  # WHY: surface user-facing message
        print("    [1] Global (UTC) - All sites upgrade at the same instant")  # WHY: surface user-facing message
        print("    [2] Site-Local - Each site upgrades at that time in its timezone")  # WHY: surface user-facing messag
        print("        Example: '21:00' site-local = 9pm Eastern, 9pm Pacific, 9pm Central, etc.")  # WHY: surface user-

        try:
            mode_input = self._input_fn("  Select time mode (1-2) [1]: ", "time_mode").strip() or "1"  # WHY: compute mo
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        self.upgrade_config["use_site_local_time"] = mode_input == "2"  # WHY: assign computed value
        if self.upgrade_config["use_site_local_time"]:  # WHY: branch on condition
            print("    + Using site-local time (rolling upgrade across timezones)")  # WHY: surface user-facing message
        else:
            print("    + Using global UTC time (all sites at same instant)")  # WHY: surface user-facing message
        return True  # WHY: return computed result

    def _configure_download_schedule(self) -> bool:  # WHY: declare private helper _configure_download_schedule
        """Prompt for download start time."""
        self._print_download_time_help()  # WHY: advance computation

        try:
            download_input = self._input_fn("  Download start time [now]: ", "sched_download").strip()  # WHY: compute d
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        self.upgrade_config["start_datetime"] = self._parse_time_input(download_input, is_for_reboot=False)  # WHY: assi
        self.upgrade_config["_download_dt"] = self._parse_download_datetime(download_input)  # WHY: assign computed valu
        self._print_download_confirmation()  # WHY: advance computation
        return True  # WHY: return computed result

    def _print_download_time_help(self) -> None:  # WHY: declare private helper _print_download_time_help
        """Print download scheduling help text."""
        print("\n  Download Scheduling:")  # WHY: surface user-facing message
        if self.upgrade_config.get("use_site_local_time"):  # WHY: branch on condition
            print("    Absolute: 'HH:MM' (24-hour, site-local)")  # WHY: surface user-facing message
            print("    Relative: 'in 15 minutes', '+3h', '+2m' (converts to UTC)")  # WHY: surface user-facing message
            print("    Note: Relative times start download immediately across all sites;")  # WHY: surface user-facing m
            print("          HH:MM schedules download at that time in each site's timezone")  # WHY: surface user-facing
        else:
            print("    Absolute: '21:30' (your local) or '19:45 UTC'")  # WHY: surface user-facing message
            print("    Relative: 'in 15 minutes', 'in 3 hours', 'in 2 days', '+3h'")  # WHY: surface user-facing message
        print("    Immediate: blank or 'now'")  # WHY: surface user-facing message

    def _print_download_confirmation(self) -> None:  # WHY: declare private helper _print_download_confirmation
        """Print download time confirmation."""
        start_dt = self.upgrade_config.get("start_datetime")  # WHY: compute start_dt
        if start_dt:  # WHY: branch on condition
            is_utc = start_dt.endswith("Z")  # WHY: compute is_utc
            use_site_local = self.upgrade_config.get("use_site_local_time", False)  # WHY: compute use_site_local
            if is_utc and use_site_local:  # WHY: branch on condition
                print(f"    + Download scheduled: {start_dt} (UTC - immediate start)")  # WHY: surface user-facing messa
            else:
                time_suffix = " (site-local)" if use_site_local else " (UTC)"  # WHY: compute time_suffix
                print(f"    + Download scheduled: {start_dt}{time_suffix}")  # WHY: surface user-facing message
        else:
            print("    + Download: immediate")  # WHY: surface user-facing message

    def _configure_reboot_schedule(self) -> bool:  # WHY: declare private helper _configure_reboot_schedule
        """Prompt for reboot start time."""
        self._print_reboot_time_help()  # WHY: advance computation

        try:
            reboot_input = self._input_fn("  Reboot start time [immediate]: ", "sched_reboot").strip()  # WHY: compute r
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        download_dt = self.upgrade_config.pop("_download_dt", None)  # WHY: compute download_dt
        parsed_reboot = self._parse_time_input(reboot_input, base_datetime=download_dt, is_for_reboot=True)  # WHY: comp
        self.upgrade_config["reboot_datetime"] = parsed_reboot if parsed_reboot else None  # WHY: assign computed value

        if self.upgrade_config["reboot_datetime"]:  # WHY: branch on condition
            time_suffix = " (site-local)" if self.upgrade_config.get("use_site_local_time") else " (UTC)"  # WHY: comput
            print(f"    + Reboot scheduled: {self.upgrade_config['reboot_datetime']}{time_suffix}")  # WHY: surface user
        else:
            print("    + Reboot: immediate (after download completes)")  # WHY: surface user-facing message

        return True  # WHY: return computed result

    def _print_reboot_time_help(self) -> None:  # WHY: declare private helper _print_reboot_time_help
        """Print reboot scheduling help text."""
        print("\n    Reboot time options:")  # WHY: surface user-facing message
        if self.upgrade_config.get("use_site_local_time"):  # WHY: branch on condition
            print("      Time format: 'HH:MM' (24-hour, site-local)")  # WHY: surface user-facing message
            print("      Example: '02:00' = 2am at each site's local time")  # WHY: surface user-facing message
        else:
            print("      Absolute: '21:30', '19:45 UTC'")  # WHY: surface user-facing message
            if self.upgrade_config.get("start_datetime"):  # WHY: branch on condition
                print("      Relative to download: '+4h', '4 hours after', 'in 6 hours'")  # WHY: surface user-facing me
        print("      Immediate (after download): blank or 'now'")  # WHY: surface user-facing message

    def _apply_default_settings(self) -> bool:
        """Apply default upgrade settings with optional user prompts."""
        uses_canary = (  # WHY: compute uses_canary
            self.upgrade_config.get("download_strategy") == "canary"
            or self.upgrade_config.get("reboot_strategy") == "canary"
        )

        if uses_canary:  # WHY: branch on condition
            if not self._configure_canary_phases():  # WHY: guard against missing precondition
                return False  # WHY: return computed result

        if not self._configure_failure_threshold():  # WHY: guard against missing precondition
            return False  # WHY: return computed result

        self.upgrade_config["force"] = False  # WHY: assign computed value
        return True  # WHY: return computed result

    @staticmethod
    def _default_canary_phases() -> list[int]:  # WHY: declare private helper _default_canary_phases
        """Return default canary phase percentages."""
        return [
            1,
            2,
            4,
            8,
            16,
            32,
            64,
            100,
        ]  # Keep default wave plan defined once for prompt, fallback, and body generation.

    @staticmethod
    def _parse_canary_phase_values(phases_input: str) -> list[int] | None:  # WHY: declare private helper _parse_canary_
        """Parse comma-separated canary phases."""
        logging.info("Parsing canary phase input=%r", phases_input)  # WHY: bracket entry with sanitized user input
        phases = OrgLevelAPFirmwareUpgrader._tokenize_canary_phases(phases_input)  # WHY: strict integer tokenization
        if phases is None:  # WHY: tokenizer returns None when any token failed int() conversion
            return None  # WHY: propagate parse failure so caller falls back to default plan
        if not OrgLevelAPFirmwareUpgrader._canary_phases_in_range(phases):  # WHY: enforce 1..100 percentage bounds
            logging.debug("Canary phases rejected: empty or out-of-range")  # WHY: bracket rejection reason
            return None  # WHY: reject empty or out-of-range phase lists to prevent invalid API payloads
        logging.debug("Canary phases accepted: %s", phases)  # WHY: bracket successful acceptance
        return phases  # WHY: return validated integer wave plan

    @staticmethod
    def _tokenize_canary_phases(phases_input: str) -> list[int] | None:  # WHY: declare private helper _tokenize_canary_
        """Split canary-phase CSV and coerce each non-empty token to int()."""
        try:  # WHY: comprehension may raise ValueError on any non-integer token
            return [  # WHY: build integer list from CSV. Skip empty segments so stray commas are tolerated
                int(part.strip()) for part in phases_input.split(",") if part.strip()
            ]
        except ValueError:  # WHY: any bad token invalidates the entire wave definition
            return None  # WHY: sentinel signals tokenization failure to caller

    @staticmethod
    def _canary_phases_in_range(phases: list[int]) -> bool:  # WHY: declare private helper _canary_phases_in_range
        """Return True when every phase is a strictly positive percentage <= 100."""
        if not phases:  # WHY: empty list is invalid rollout - need at least one wave
            return False  # WHY: caller falls back to default when we return False
        return all(0 < phase <= 100 for phase in phases)  # WHY: enforce (0, 100] percentage semantics

    def _set_default_canary_phases(self, message: str | None = None) -> None:  # WHY: declare private helper _set_defaul
        """Store default canary phases with optional explanation."""
        if message:  # Print explanation only when user input was provided but invalid.
            print(message)  # WHY: surface user-facing message
        self.upgrade_config["canary_phases"] = (
            self._default_canary_phases()
        )  # Always fall back to known-safe wave progression.

    def _configure_canary_phases(self) -> bool:  # WHY: declare private helper _configure_canary_phases
        """Configure canary phase percentages."""
        logging.info("Configuring canary phases")  # WHY: bracket entry to phase configuration
        self._canary_phase_present()  # WHY: emit banner + wave-format guidance
        phases_input = self._canary_phase_prompt()  # WHY: gather user rollout string via safe_input
        if phases_input is None:  # WHY: SystemExit sentinel from prompt helper
            return False  # WHY: abort configuration when user interrupts
        result = self._canary_phase_apply(phases_input)  # WHY: parse + persist phase plan
        logging.debug("_configure_canary_phases result=%s", result)  # WHY: bracket completion
        return result  # WHY: propagate success to Step 6 orchestrator

    def _canary_phase_present(self) -> None:  # WHY: declare private helper _canary_phase_present
        """Present canary configuration banner to the user."""
        print("\n  Canary Configuration:")  # WHY: separate canary prompt from prior config section for readability
        print("    Canary phases define what percentage of devices to upgrade in each wave.")  # WHY: explain field
        print("    Example: '1,2,4,8,16,32,64,100' means 1%, then 2%, then 4%, etc.")  # WHY: illustrate wave format

    def _canary_phase_prompt(self) -> str | None:  # WHY: declare private helper _canary_phase_prompt
        """Prompt for canary phase values. Return stripped input or None on SystemExit."""
        try:  # WHY: safe_input may raise SystemExit if session drops
            phases_input = self._input_fn(  # WHY: safe_input wrapper for SSH/container resiliency
                "  Canary phases (comma-separated) [1,2,4,8,16,32,64,100]: ",
                "canary_phases",
            ).strip()  # WHY: normalize whitespace before parsing
        except SystemExit:  # WHY: propagate cancellation to caller as sentinel
            return None  # WHY: None signals aborted prompt to the orchestrator
        return phases_input  # WHY: return trimmed rollout percentage string

    def _canary_phase_apply(self, phases_input: str) -> bool:  # WHY: declare private helper _canary_phase_apply
        """Parse, validate, and persist canary phase percentages."""
        if not phases_input:  # WHY: blank input intentionally uses default rollout profile
            self._set_default_canary_phases()  # WHY: seed config with standard 1,2,4,...,100 plan
            return True  # WHY: default is valid, keep workflow moving
        parsed_phases = self._parse_canary_phase_values(phases_input)  # WHY: validate wave percentages
        if parsed_phases is None:  # WHY: parser returns None on any malformed token
            self._set_default_canary_phases(  # WHY: fall back to default profile on invalid input
                "    ! Invalid phases, using default [1,2,4,8,16,32,64,100]"
            )
            return True  # WHY: continue workflow after graceful fallback
        self.upgrade_config["canary_phases"] = parsed_phases  # WHY: persist validated custom rollout plan
        return True  # WHY: success path confirms user-supplied phases accepted

    def _configure_failure_threshold(self) -> bool:  # WHY: declare private helper _configure_failure_threshold
        """Configure max failure percentage."""
        print("\n  Failure Threshold:")  # WHY: surface user-facing message
        print("    Maximum percentage of devices that can fail before aborting upgrade.")  # WHY: surface user-facing me
        try:
            failure_input = self._input_fn("  Max failure percentage [7]: ", "max_failure").strip()  # WHY: compute fail
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        if failure_input:  # WHY: branch on condition
            try:
                failure_pct = int(failure_input)  # WHY: compute failure_pct
                if 0 <= failure_pct <= 100:  # WHY: branch on condition
                    self.upgrade_config["max_failure_percentage"] = failure_pct  # WHY: assign computed value
                else:
                    print("    ! Invalid percentage, using default 7%")  # WHY: surface user-facing message
                    self.upgrade_config["max_failure_percentage"] = 7  # WHY: assign computed value
            except ValueError:  # WHY: handle expected error
                print("    ! Invalid input, using default 7%")  # WHY: surface user-facing message
                self.upgrade_config["max_failure_percentage"] = 7  # WHY: assign computed value
        else:
            self.upgrade_config["max_failure_percentage"] = 7  # WHY: assign computed value
        return True  # WHY: return computed result

    def _configure_p2p(self) -> bool:
        """Configure peer-to-peer firmware distribution settings."""
        print("\n  Peer-to-Peer Configuration:")  # WHY: surface user-facing message
        print("    P2P allows APs to share firmware with nearby APs to reduce bandwidth.")  # WHY: surface user-facing m
        try:
            p2p_input = self._input_fn("  Enable P2P firmware sharing? (Y/n) [Y]: ", "p2p_enable").strip().lower()
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        self.upgrade_config["enable_p2p"] = p2p_input not in ["n", "no"]  # WHY: assign computed value

        if self.upgrade_config["enable_p2p"]:  # WHY: branch on condition
            print("    + P2P enabled")  # WHY: surface user-facing message
            if not self._configure_p2p_cluster_size():  # WHY: guard against missing precondition
                return False  # WHY: return computed result
            if not self._configure_p2p_parallelism():  # WHY: guard against missing precondition
                return False  # WHY: return computed result
        else:
            print("    + P2P disabled")  # WHY: surface user-facing message
            self.upgrade_config["p2p_cluster_size"] = 5  # WHY: assign computed value
            self.upgrade_config["p2p_parallelism"] = 100  # WHY: assign computed value

        return True  # WHY: return computed result

    def _configure_p2p_cluster_size(self) -> bool:  # WHY: declare private helper _configure_p2p_cluster_size
        """Configure P2P cluster size."""
        try:
            cluster_input = self._input_fn("  P2P cluster size (APs per cluster) [5]: ", "p2p_cluster").strip()
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        if cluster_input:  # WHY: branch on condition
            try:
                cluster_size = int(cluster_input)  # WHY: compute cluster_size
                if 1 <= cluster_size <= 100:  # WHY: branch on condition
                    self.upgrade_config["p2p_cluster_size"] = cluster_size  # WHY: assign computed value
                else:
                    print("    ! Invalid size, using default 5")  # WHY: surface user-facing message
                    self.upgrade_config["p2p_cluster_size"] = 5  # WHY: assign computed value
            except ValueError:  # WHY: handle expected error
                print("    ! Invalid input, using default 5")  # WHY: surface user-facing message
                self.upgrade_config["p2p_cluster_size"] = 5  # WHY: assign computed value
        else:
            self.upgrade_config["p2p_cluster_size"] = 5  # WHY: assign computed value
        return True  # WHY: return computed result

    def _configure_p2p_parallelism(self) -> bool:  # WHY: declare private helper _configure_p2p_parallelism
        """Configure P2P parallelism."""
        try:
            parallel_input = self._input_fn(  # WHY: compute parallel_input
                "  P2P parallelism (simultaneous site batches) [100]: ", "p2p_parallelism"
            ).strip()
        except SystemExit:  # WHY: handle expected error
            return False  # WHY: return computed result

        if parallel_input:  # WHY: branch on condition
            try:
                parallelism = int(parallel_input)  # WHY: compute parallelism
                if 1 <= parallelism <= 500:  # WHY: branch on condition
                    self.upgrade_config["p2p_parallelism"] = parallelism  # WHY: assign computed value
                else:
                    print("    ! Invalid value, using default 100")  # WHY: surface user-facing message
                    self.upgrade_config["p2p_parallelism"] = 100  # WHY: assign computed value
            except ValueError:  # WHY: handle expected error
                print("    ! Invalid input, using default 100")  # WHY: surface user-facing message
                self.upgrade_config["p2p_parallelism"] = 100  # WHY: assign computed value
        else:
            self.upgrade_config["p2p_parallelism"] = 100  # WHY: assign computed value
        return True  # WHY: return computed result

    def _print_time_mode_summary(self) -> None:  # WHY: declare private helper _print_time_mode_summary
        """Print time-mode summary line."""
        use_site_local = self.upgrade_config.get(
            "use_site_local_time", False
        )  # Read mode flag once so label logic stays simple.
        time_mode = (
            "Site-Local" if use_site_local else "Global (UTC)"
        )  # Convert boolean config into operator-friendly wording.
        print(
            f"      Time Mode: {time_mode}"
        )  # Keep time-mode visibility high because schedule semantics depend on it.

    def _print_schedule_summary(self) -> None:  # WHY: declare private helper _print_schedule_summary
        """Print download and reboot schedule summary."""
        start_dt = self.upgrade_config.get(
            "start_datetime"
        )  # Pull configured download schedule for immediate fallback wording.
        reboot_dt = self.upgrade_config.get(
            "reboot_datetime"
        )  # Pull configured reboot schedule for dependent fallback wording.
        reboot_label = (
            reboot_dt if reboot_dt else ("Same as download" if start_dt else "Immediate")
        )  # Explain implicit reboot timing explicitly.
        print(f"      Download Time: {start_dt if start_dt else 'Immediate'}")  # WHY: surface user-facing message
        print(f"      Reboot Time: {reboot_label}")  # WHY: surface user-facing message

    def _print_canary_summary(self) -> None:  # WHY: declare private helper _print_canary_summary
        """Print canary summary when configured."""
        if (
            "canary_phases" in self.upgrade_config
        ):  # Only show canary field when strategy actually requires or captured it.
            phases_str = ", ".join(
                str(phase) for phase in self.upgrade_config["canary_phases"]
            )  # Render stored wave list compactly.
            print(f"      Canary Phases: [{phases_str}]%")  # WHY: surface user-facing message

    def _print_p2p_summary(self) -> None:  # WHY: declare private helper _print_p2p_summary
        """Print peer-to-peer summary."""
        if self.upgrade_config.get("enable_p2p"):  # Show detailed knobs only when P2P is active in final payload.
            print(  # WHY: surface user-facing message
                f"      P2P Enabled: Yes (cluster: {self.upgrade_config.get('p2p_cluster_size', 5)}, "
                f"parallel: {self.upgrade_config.get('p2p_parallelism', 100)})"
            )
            return  # WHY: return early
        print("      P2P Enabled: No")  # Keep explicit disabled state so operator does not infer omission accidentally.

    def _display_configuration(self) -> None:  # WHY: declare private helper _display_configuration
        """Display configured upgrade settings."""
        print("\n  + Configuration:")  # Start summary block after configuration prompts finish.
        print(
            f"      Download Strategy: {self.upgrade_config['download_strategy']}"
        )  # Show chosen download behavior prominently for final confirmation.
        print(
            f"      Reboot Strategy: {self.upgrade_config['reboot_strategy']}"
        )  # Show chosen reboot behavior beside download strategy for comparison.
        self._print_time_mode_summary()  # Keep time-mode wording isolated.
        self._print_schedule_summary()  # Keep schedule output isolated.
        print(
            f"      Max Failure: {self.upgrade_config['max_failure_percentage']}%"
        )  # Preserve hard-stop threshold visibility before execution.
        self._print_canary_summary()  # Print optional rollout phases only when present in config.
        self._print_p2p_summary()  # Print P2P details or explicit disabled state in one place.

    # =========================================================================
    # STEP 7: CONFIRM AND EXECUTE
    # =========================================================================

    def _step7_confirm_and_execute(self) -> bool:  # WHY: declare private helper _step7_confirm_and_execute
        """Confirm upgrade plan and execute."""
        logging.debug("Entering _step7_confirm_and_execute()")  # WHY: action-log after operation
        self._print_step7_header()  # WHY: advance computation
        self._display_upgrade_summary()  # WHY: advance computation
        self._display_version_breakdown()  # WHY: advance computation

        if self.dry_run:  # WHY: branch on condition
            print("\n  >> DRY-RUN: Simulating execution <<")  # WHY: surface user-facing message
            logging.debug("Executing dry-run simulation")  # WHY: action-log after operation
            return self._execute_dry_run()  # WHY: return computed result

        return self._confirm_and_execute_live()  # WHY: return computed result

    def _print_step7_header(self) -> None:  # WHY: declare private helper _print_step7_header
        """Print Step 7 header."""
        print("")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message
        print("  STEP 7: Confirm and Execute")  # WHY: surface user-facing message
        print("-" * 70)  # WHY: surface user-facing message

    def _display_upgrade_summary(self) -> None:  # WHY: declare private helper _display_upgrade_summary
        """Display upgrade summary statistics."""
        total_devices = sum(len(d["device_ids"]) for d in self.upgrade_plan.values())  # WHY: compute total_devices
        total_calls = len(self.upgrade_plan)  # WHY: compute total_calls

        print("\n  Summary:")  # WHY: surface user-facing message
        print(f"    - Organization: {self.org_id[:8]}...")  # WHY: surface user-facing message
        scope = "All sites" if self.target_all_sites else f"{len(self.selected_site_ids)} selected site(s)"  # WHY: comp
        print(f"    - Site Scope: {scope}")  # WHY: surface user-facing message
        print(f"    - Total Devices: {total_devices}")  # WHY: surface user-facing message
        print(f"    - API Calls: {total_calls}")  # WHY: surface user-facing message

    def _display_version_breakdown(self) -> None:  # WHY: declare private helper _display_version_breakdown
        """Display upgrades by version."""
        print("\n  Upgrades by Version:")  # WHY: surface user-facing message
        for version, data in sorted(self.upgrade_plan.items()):  # WHY: iterate collection
            models_str = ", ".join(data["models"])  # WHY: compute models_str
            print(f"    {version}: {len(data['device_ids'])} device(s) ({models_str})")  # WHY: surface user-facing mess

    def _confirm_and_execute_live(self) -> bool:  # WHY: declare private helper _confirm_and_execute_live
        """Confirm and execute live upgrade."""
        logging.debug("Entering _confirm_and_execute_live()")  # WHY: action-log after operation
        self._print_destructive_warning()  # WHY: advance computation

        try:
            confirm = self._input_fn("  Type 'UPGRADE' to proceed: ", "upgrade_confirm").strip()  # WHY: compute confirm
        except SystemExit:  # WHY: handle expected error
            logging.debug("SystemExit during upgrade confirmation")  # WHY: action-log after operation
            return False  # WHY: return computed result

        logging.debug("User confirmation input: '%s'", confirm)  # WHY: action-log after operation

        if confirm != "UPGRADE":  # WHY: branch on condition
            print("  X Upgrade cancelled")  # WHY: surface user-facing message
            logging.warning("User cancelled upgrade - confirmation failed")  # WHY: surface non-fatal issue
            return False  # WHY: return computed result

        logging.info("User confirmed upgrade - executing")  # WHY: action-log before operation
        return self._execute_upgrades()  # WHY: return computed result

    @staticmethod
    def _print_destructive_warning() -> None:  # WHY: declare private helper _print_destructive_warning
        """Print destructive operation warning banner."""
        print("")  # WHY: surface user-facing message
        print("  " + "!" * 60)  # WHY: surface user-facing message
        print("  !  WARNING: DESTRUCTIVE OPERATION - FIRMWARE UPGRADE  !")  # WHY: surface user-facing message
        print("  " + "!" * 60)  # WHY: surface user-facing message
        print("")  # WHY: surface user-facing message

    def _execute_dry_run(self) -> bool:  # WHY: declare private helper _execute_dry_run
        """Execute dry-run simulation."""
        print("")  # WHY: surface user-facing message
        for version, data in sorted(self.upgrade_plan.items()):  # WHY: iterate collection
            self._print_dry_run_entry(version, data)  # WHY: advance computation
            self._record_dry_run_results(version, data)  # WHY: advance computation

        print("")  # WHY: surface user-facing message
        print("  DRY-RUN Complete:")  # WHY: surface user-facing message
        print(f"    - API Calls (simulated): {self.successful_api_calls}")  # WHY: surface user-facing message
        print(f"    - Devices (simulated): {self.total_devices_upgraded}")  # WHY: surface user-facing message
        return True  # WHY: return computed result

    def _print_dry_run_entry(self, version: str, data: dict[str, Any]) -> None:  # WHY: declare private helper _print_dr
        """Print a single dry-run upgrade entry."""
        logging.info("Rendering dry-run entry for version=%s device_count=%d", version, len(data["device_ids"]))
        summary = self._build_dry_run_summary(version, data)  # WHY: separate prepare from present per PCPP
        self._render_dry_run_summary(summary)  # WHY: emit prepared summary to stdout
        self._print_dry_run_extras()  # WHY: append optional canary/P2P details when configured
        logging.debug("Dry-run entry rendered for version=%s", version)  # WHY: bracket exit

    def _build_dry_run_summary(self, version: str, data: dict[str, Any]) -> dict[str, str]:  # WHY: declare private help
        """Assemble the printable fields for a dry-run upgrade entry."""
        start_dt = self.upgrade_config.get("start_datetime")  # WHY: capture optional download timestamp once
        reboot_dt = self.upgrade_config.get("reboot_datetime")  # WHY: capture optional reboot timestamp once
        use_site_local = self.upgrade_config.get("use_site_local_time", False)  # WHY: pick display timezone label
        return {  # WHY: return prepared strings so present-phase has zero branching
            "version": version,  # WHY: firmware version target for this dry-run entry
            "models": ", ".join(data["models"]),  # WHY: human-readable model list from upgrade plan bucket
            "device_count": str(len(data["device_ids"])),  # WHY: coerce int to str for uniform format helper
            "scope": self._describe_dry_run_scope(),  # WHY: derive site-scope label via dedicated helper
            "time_mode": "Site-Local" if use_site_local else "Global (UTC)",  # WHY: timezone semantics for viewer
            "download_time": start_dt or "Immediate",  # WHY: fallback label when no explicit start_datetime set
            "reboot_time": self._describe_reboot_time(start_dt, reboot_dt),  # WHY: derive reboot label via helper
        }

    def _describe_dry_run_scope(self) -> str:  # WHY: declare private helper _describe_dry_run_scope
        """Return the human-readable scope description for a dry-run entry."""
        if self.target_all_sites:  # WHY: all-sites path uses the API-level flag semantics
            return "all_sites=true"  # WHY: match the exact literal callers grep for in dry-run logs
        return f"{len(self.selected_site_ids)} site_ids"  # WHY: count-based label for selected-site path

    @staticmethod
    def _describe_reboot_time(start_dt: Any, reboot_dt: Any) -> str:  # WHY: declare private helper _describe_reboot_tim
        """Return the reboot-time label used in the dry-run summary line."""
        if reboot_dt:  # WHY: explicit reboot timestamp always wins
            return str(reboot_dt)  # WHY: coerce to str for uniform print formatting
        if start_dt:  # WHY: download-only case implies reboot piggybacks the download
            return "Same as download"  # WHY: match the canonical dry-run wording expected by tests
        return "Immediate"  # WHY: no download, no reboot -> immediate reboot label

    @staticmethod
    def _render_dry_run_summary(summary: dict[str, str]) -> None:  # WHY: declare private helper _render_dry_run_summary
        """Print the prepared dry-run summary block."""
        print("  [DRY-RUN] Would call upgradeOrgDevices:")  # WHY: banner identifies dry-run mode to the operator
        print(f"      Version: {summary['version']}")  # WHY: emit firmware version target
        print(f"      Models: {summary['models']}")  # WHY: emit model list captured in prepare step
        print(f"      Devices: {summary['device_count']}")  # WHY: emit device count captured in prepare step
        print(f"      Site Scope: {summary['scope']}")  # WHY: emit scope description captured in prepare step
        print(f"      Time Mode: {summary['time_mode']}")  # WHY: emit timezone label captured in prepare step
        print(f"      Download Time: {summary['download_time']}")  # WHY: emit download timestamp label
        print(f"      Reboot Time: {summary['reboot_time']}")  # WHY: emit reboot timestamp label

    def _print_dry_run_extras(self) -> None:  # WHY: declare private helper _print_dry_run_extras
        """Print optional dry-run config details (canary, P2P)."""
        if "canary_phases" in self.upgrade_config:  # WHY: branch on condition
            phases_str = ", ".join(str(p) for p in self.upgrade_config["canary_phases"])  # WHY: compute phases_str
            print(f"      Canary Phases: [{phases_str}]%")  # WHY: surface user-facing message
        if self.upgrade_config.get("enable_p2p"):  # WHY: branch on condition
            print(  # WHY: surface user-facing message
                f"      P2P: Enabled (cluster: {self.upgrade_config.get('p2p_cluster_size', 5)}, "
                f"parallel: {self.upgrade_config.get('p2p_parallelism', 100)})"
            )

    def _record_dry_run_results(self, version: str, data: dict[str, Any]) -> None:  # WHY: declare private helper _recor
        """Record dry-run results for a version."""
        self.successful_api_calls += 1  # WHY: assign computed value
        self.total_devices_upgraded += len(data["device_ids"])  # WHY: assign computed value
        for device_id in data["device_ids"]:  # WHY: iterate collection
            self.results.append(  # WHY: advance computation
                {
                    "org_id": self.org_id,
                    "version": version,
                    "device_id": device_id,
                    "status": "DRY-RUN: Would upgrade",
                }
            )

    def _execute_upgrades(self) -> bool:  # WHY: declare private helper _execute_upgrades
        """Execute actual org-level upgrades."""
        logging.info("Executing org-level AP firmware upgrades")  # WHY: bracket entry for observability
        if not self._upgrade_phase_precheck():  # WHY: guard against missing session/org before API calls
            return False  # WHY: propagate failure to run() orchestrator
        self._upgrade_phase_dispatch()  # WHY: iterate upgrade plan invoking single-version helper
        self._upgrade_phase_report()  # WHY: emit counters summary to the user
        logging.debug(
            "_execute_upgrades completed with successful=%d failed=%d",
            self.successful_api_calls,
            self.failed_api_calls,
        )
        return True  # WHY: success sentinel for caller

    def _upgrade_phase_precheck(self) -> bool:  # WHY: declare private helper _upgrade_phase_precheck
        """Validate prerequisites before invoking the upgrade API."""
        print("\n  Executing org-level upgrades...")  # WHY: user-visible banner for phase begin
        if self.apisession is None or self.org_id is None:  # WHY: guard clause avoids AttributeError deeper in stack
            print("  X API session or org_id not initialized")  # WHY: surface the fault to the user
            logging.error("API session or org_id not initialized for upgrade execution")  # WHY: audit trail
            return False  # WHY: signal precheck failure to orchestrator
        return True  # WHY: prerequisites satisfied

    def _upgrade_phase_dispatch(self) -> None:  # WHY: declare private helper _upgrade_phase_dispatch
        """Iterate the upgrade plan calling the single-version helper."""
        org_devices_api = importlib.import_module("mistapi.api.v1.orgs.devices")  # WHY: late import keeps startup light
        for version, data in sorted(self.upgrade_plan.items()):  # WHY: deterministic order across runs
            self._execute_single_version_upgrade(version, data, org_devices_api)  # WHY: delegate per-version work

    def _upgrade_phase_report(self) -> None:  # WHY: declare private helper _upgrade_phase_report
        """Emit the post-upgrade counters summary."""
        print("")  # WHY: spacing before summary block
        print("  Execution Complete:")  # WHY: summary header for the user
        print(f"    - Successful API Calls: {self.successful_api_calls}")  # WHY: report success counter
        print(f"    - Failed API Calls: {self.failed_api_calls}")  # WHY: report failure counter
        print(f"    - Total Devices: {self.total_devices_upgraded}")  # WHY: report devices touched
        logging.info(  # WHY: emit structured summary for log consumers
            "Org-level upgrade execution complete: successful=%s, failed=%s, total_devices=%s",
            self.successful_api_calls,
            self.failed_api_calls,
            self.total_devices_upgraded,
        )

    def _execute_single_version_upgrade(  # WHY: declare private helper _execute_single_version_upgrade
        self,
        version: str,
        data: dict[str, Any],
        org_devices_api: Any,
    ) -> None:
        """Execute upgrade for a single version."""
        models_str = ", ".join(data["models"])  # WHY: compute models_str
        print(f"\n  Upgrading to {version} ({models_str})...")  # WHY: surface user-facing message
        logging.info("Processing upgrade to version %s for models: %s", version, models_str)  # WHY: action-log before o

        body = self._build_upgrade_body(version, data)  # WHY: compute body

        logging.debug("Upgrade API body: %s", body)  # WHY: action-log after operation
        if self._is_debug_fn():  # WHY: branch on condition
            print(f"    API Body: {body}")  # WHY: surface user-facing message

        try:
            response = org_devices_api.upgradeOrgDevices(self.apisession, self.org_id, body=body)  # WHY: compute respon
            self._process_upgrade_response(response, version, data)  # WHY: advance computation
        except Exception as exc:  # WHY: handle expected error
            print(f"    X Error: {exc}")  # WHY: surface user-facing message
            logging.error("Org-level upgrade failed for version %s: %s", version, exc)  # WHY: surface fatal issue
            self.failed_api_calls += 1  # WHY: assign computed value

    def _create_base_upgrade_body(self, version: str, data: dict[str, Any]) -> dict[str, Any]:  # WHY: declare private h
        """Create required base upgrade payload."""
        return {  # Build required fields first so optional enrichments can layer on top deterministically.
            "versions": [{"firmware_type": "ap", "version": version}],
            "models": [[model] for model in data["models"]],
            "strategy": self.upgrade_config["reboot_strategy"],
            "download_strategy": self.upgrade_config["download_strategy"],
            "max_failure_percentage": self.upgrade_config["max_failure_percentage"],
        }

    def _add_schedule_fields(self, body: dict[str, Any]) -> None:  # WHY: declare private helper _add_schedule_fields
        """Add optional schedule fields to upgrade body."""
        if self.upgrade_config.get(
            "start_datetime"
        ):  # Include download schedule only when operator requested delayed execution.
            body["start_datetime"] = self.upgrade_config["start_datetime"]  # WHY: assign computed value
        if self.upgrade_config.get(
            "reboot_datetime"
        ):  # Include reboot schedule only when it differs from default implied behavior.
            body["reboot_datetime"] = self.upgrade_config["reboot_datetime"]  # WHY: assign computed value

    def _add_scope_fields(self, body: dict[str, Any]) -> None:  # WHY: declare private helper _add_scope_fields
        """Add org-vs-site scope fields to upgrade body."""
        if self.target_all_sites:  # Use org-wide flag when operator targeted every site in the organization.
            body["all_sites"] = True  # WHY: assign computed value
            return  # WHY: return early
        body["site_ids"] = self.selected_site_ids  # Otherwise restrict payload to explicit site subset chosen earlier.

    def _add_canary_fields(self, body: dict[str, Any]) -> None:  # WHY: declare private helper _add_canary_fields
        """Add optional canary rollout fields to upgrade body."""
        if "canary_phases" in self.upgrade_config:  # Send phased rollout details only when configuration captured them.
            body["canary_phases"] = self.upgrade_config["canary_phases"]  # WHY: assign computed value

    def _add_p2p_fields(self, body: dict[str, Any]) -> None:  # WHY: declare private helper _add_p2p_fields
        """Add optional peer-to-peer settings to upgrade body."""
        if self.upgrade_config.get("enable_p2p"):  # Include P2P knobs only when feature is enabled.
            body["enable_p2p"] = True  # WHY: assign computed value
            body["p2p_cluster_size"] = self.upgrade_config.get("p2p_cluster_size", 5)  # WHY: assign computed value
            body["p2p_parallelism"] = self.upgrade_config.get("p2p_parallelism", 100)  # WHY: assign computed value

    def _build_upgrade_body(self, version: str, data: dict[str, Any]) -> dict[str, Any]:  # WHY: declare private helper
        """Build the API request body for an upgrade."""
        body = self._create_base_upgrade_body(
            version, data
        )  # Start from required fields shared by every upgrade request.
        self._add_schedule_fields(body)  # Layer in optional schedule controls when configured.
        self._add_scope_fields(body)  # Add either org-wide or scoped site targeting fields.
        self._add_canary_fields(body)  # Add rollout phases only when present in config.
        self._add_p2p_fields(body)  # Add P2P options last because they are fully optional payload enrichments.
        return body  # WHY: return computed result

    def _process_upgrade_response(  # WHY: declare private helper _process_upgrade_response
        self,
        response: Any,
        version: str,
        data: dict[str, Any],
    ) -> None:
        """Process the response from an upgrade API call."""
        logging.info("Processing upgrade response for version %s", version)  # WHY: bracket entry
        if not self._response_has_data(response):  # WHY: guard clause for empty/invalid response
            self._record_upgrade_failure()  # WHY: increment failure counter and notify user
            return  # WHY: exit early on missing response payload
        upgrade_id = self._extract_upgrade_id(response)  # WHY: pull the upgrade job id when available
        self._record_upgrade_success(upgrade_id, version, data)  # WHY: persist per-device result rows
        logging.debug("_process_upgrade_response recorded %d devices", len(data["device_ids"]))  # WHY: bracket exit

    @staticmethod
    def _response_has_data(response: Any) -> bool:  # WHY: declare private helper _response_has_data
        """Return True when the API response carries a data payload."""
        return bool(response) and hasattr(response, "data")  # WHY: truthy response plus expected attribute

    @staticmethod
    def _extract_upgrade_id(response: Any) -> Any:  # WHY: declare private helper _extract_upgrade_id
        """Return the upgrade job id from response.data or None."""
        if isinstance(response.data, dict):  # WHY: only dict payloads carry the id field
            return response.data.get("id")  # WHY: pull id when present, None otherwise
        return None  # WHY: non-dict payload has no addressable id

    def _record_upgrade_success(self, upgrade_id: Any, version: str, data: dict[str, Any]) -> None:  # WHY: declare priv
        """Persist per-device rows for a successful upgrade dispatch."""
        print(f"    + Upgrade initiated - ID: {upgrade_id or 'N/A'}")  # WHY: user-visible confirmation
        self.successful_api_calls += 1  # WHY: increment success counter for summary report
        self.total_devices_upgraded += len(data["device_ids"])  # WHY: aggregate device-touch counter
        for device_id in data["device_ids"]:  # WHY: one CSV row per targeted device
            self.results.append(  # WHY: accumulate persistence buffer for _step8_write_results
                {
                    "org_id": self.org_id,  # WHY: keep org for MSP-aggregated output
                    "version": version,  # WHY: retain target firmware version
                    "device_id": device_id,  # WHY: identify the individual AP
                    "upgrade_id": upgrade_id,  # WHY: link result to Mist upgrade job
                    "status": "Initiated",  # WHY: initial state. Polling not part of this workflow
                }
            )

    def _record_upgrade_failure(self) -> None:  # WHY: declare private helper _record_upgrade_failure
        """Record a failed upgrade dispatch."""
        print("    X Failed - no response data")  # WHY: surface failure to the user
        self.failed_api_calls += 1  # WHY: track for summary counters

    # =========================================================================
    # STEP 8: WRITE RESULTS
    # =========================================================================

    def _step8_write_results(self) -> None:  # WHY: declare private helper _step8_write_results
        """Write upgrade results to file."""
        logging.debug("Entering _step8_write_results()")  # WHY: action-log after operation
        if not self.results:  # WHY: guard against missing precondition
            logging.debug("No results to write")  # WHY: action-log after operation
            return  # WHY: return early

        filename = os.path.join("data", "org_level_ap_upgrade_results.csv")  # WHY: compute filename
        try:
            if self._write_results_fn:  # WHY: branch on condition
                self._write_results_fn(self.results, filename, api_function_name="orgLevelAPFirmwareUpgrade")  # WHY: xx
            print(f"\n  Results written to: {filename}")  # WHY: surface user-facing message
            logging.info("Upgrade results written to: %s", filename)  # WHY: action-log before operation
        except Exception as exc:  # WHY: handle expected error
            print(f"  X Failed to write results: {exc}")  # WHY: surface user-facing message
            logging.error("Failed to write upgrade results: %s", exc)  # WHY: surface fatal issue
