"""FirmwareManager - Firmware upgrade status checking and execution.

Manages firmware upgrades for APs, switches, and SSR devices across
Mist organization sites.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import csv  # WHY: CSV read/write for firmware plan artifacts
import importlib  # WHY: lazy import of MistHelper for _MistHelperProxy late-binding
import json  # WHY: read stored ActiveUpgrades.json tracker in FirmwareUpgradeStatusChecker
import logging  # WHY: emit info/debug audit trail per Constitution VII
import os  # WHY: filesystem existence check for ActiveUpgrades.json tracker
import sys  # WHY: needed for _bind_module_globals to rebind module attrs
import time  # WHY: polling delays for continuous monitoring mode
from collections.abc import Callable  # WHY: type hints for injected dependency callables
from dataclasses import dataclass  # WHY: FirmwareManagerConfig frozen value object
from datetime import UTC, datetime  # WHY: UTC-aware ISO timestamps and CSV filenames
from typing import Any, cast  # WHY: Any for opaque API objects; cast narrows mypy return types

# Type aliases for injected dependencies keep readable signatures across helpers.
SafeInputFn = Callable[..., str]  # WHY: safe_input(prompt, context=...) returning stripped text
SelectSiteFn = Callable[..., Any]  # WHY: interactive site picker used by menu 196 sub-flows
CheckCacheFn = Callable[..., Any]  # WHY: CSV cache warm-up / regenerate helper
GetCsvPathFn = Callable[[str], str]  # WHY: resolves per-org CSV filesystem path
GeneratorFn = Callable[..., Any]  # WHY: streaming generator for templates / sites

# Module-level stubs for globals declared in method bodies.
# Methods use 'global <name>' to read/write these at runtime.
# apisession and org_id are set per-instance in __init__ via _bind_module_globals.
# msp_privileges and PROGRESS_EMITTER are sourced from the main module.
msp_privileges: list[Any] = []  # WHY: cached MSP privilege records for cross-flow reuse
apisession: Any = None  # WHY: module-scope api session read by legacy helpers
org_id: str = ""  # WHY: module-scope org id read by legacy helpers
PROGRESS_EMITTER: Any = None  # WHY: shared progress emitter for menu 196 sub-flows


try:
    import mistapi as _mistapi_module  # WHY: optional Mist SDK - module may be absent in test env
except ImportError:  # pragma: no cover
    _mistapi_module = None  # WHY: null fallback keeps import graph loadable in tests
# WHY: Annotate as Any so pyright treats mistapi.<attr> uniformly under both branches;
# WHY: production callsites remain guarded by mistapi truthiness where relevant.
mistapi: Any = _mistapi_module


class _MistHelperProxy:  # WHY: attribute forwarder to live MistHelper module
    """Forward attribute access to the currently-loaded MistHelper module.

    Enables the co-located FirmwareUpgradeStatusChecker class to reference
    MistHelper-owned utility singletons (ConfigUtils, PromptUtils, etc.)
    without importing MistHelper at module load time (which would create a
    circular import). Attributes are resolved at call time so test
    monkey-patches applied to MistHelper are honoured.
    """

    def __getattr__(self, name: str) -> Any:  # WHY: only invoked when the attr is missing normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # WHY: lazy import at call time
        return getattr(misthelper_module, name)  # WHY: fetch current bound value from MistHelper


_MH = _MistHelperProxy()  # WHY: sole module-level proxy handle used by FirmwareUpgradeStatusChecker


@dataclass(frozen=True, slots=True, kw_only=True)
class FirmwareManagerConfig:
    """Immutable configuration object for FirmwareManager.

    Collapses the pre-refactor 8-parameter ``__init__`` into a single positional
    argument, satisfying STRUCT-PARAMS (threshold 5) and matching the 1004
    ``BulkAPUpgraderConfig`` prior-art template exactly.

    All six ``*_fn`` hooks are Optional; the class supplies sensible fallbacks
    where required, preserving pre-refactor behavior (FR-017).
    """

    # Required identity fields
    apisession: Any  # WHY: Mist API session for all HTTP calls
    org_id: str  # WHY: organization scope for every operation

    # Dependency-injection hooks (all optional; class supplies defaults)
    safe_input_fn: SafeInputFn | None = None  # WHY: prompt helper with context-tag audit trail
    select_site_fn: SelectSiteFn | None = None  # WHY: site-picker used by menu 196 sub-flows
    check_cache_fn: CheckCacheFn | None = None  # WHY: CSV cache warm-up / regenerate logic
    get_csv_path_fn: GetCsvPathFn | None = None  # WHY: resolves per-org CSV output path
    gateway_templates_fn: GeneratorFn | None = None  # WHY: gateway template streamer for SSR flow
    sites_fn: GeneratorFn | None = None  # WHY: site streamer for cross-org iteration

    def __post_init__(self) -> None:
        """Fail-fast validation so downstream helpers never see invalid state."""
        if self.apisession is None:  # WHY: identity field must never be None
            raise ValueError("apisession is required")  # WHY: prevent silent None-passing into HTTP layer
        if not isinstance(self.org_id, str) or not self.org_id:  # WHY: org scope must be a non-empty string
            raise ValueError("org_id must be a non-empty string")  # WHY: guard against empty-scope leakage
        self._validate_optional_hooks()  # WHY: delegate hook-callable check to helper (keeps CC <= 5)

    def _validate_optional_hooks(self) -> None:
        """Verify all six ``*_fn`` hook fields are either ``None`` or callable."""
        hook_names = (  # WHY: canonical list of optional DI hooks
            "safe_input_fn",
            "select_site_fn",
            "check_cache_fn",
            "get_csv_path_fn",
            "gateway_templates_fn",
            "sites_fn",
        )
        for name in hook_names:  # WHY: iterate hooks for callable-or-None check
            value = getattr(self, name)  # WHY: read slot value by name
            if value is not None and not callable(value):  # WHY: allow only None or callable
                raise TypeError(f"{name} must be callable or None")  # WHY: clear diagnostic for mis-injected fixtures


def _bind_module_globals(config: FirmwareManagerConfig) -> None:
    """Rebind module-level globals used by helpers that declare ``global <name>``.

    Isolates the four module-scope side effects (apisession, org_id,
    msp_privileges, PROGRESS_EMITTER) into a single auditable helper so
    ``__init__`` remains under STRUCT-LENGTH / STRUCT-COMPLEXITY thresholds.
    """
    global apisession, org_id, msp_privileges, PROGRESS_EMITTER  # WHY: mutate typed module-scope stubs directly
    logging.info("Rebinding firmware_manager module globals for org %s", config.org_id)  # WHY: audit trail
    apisession = config.apisession  # WHY: rebinds module-scope api session for legacy helpers
    org_id = config.org_id  # WHY: rebinds module-scope org id for legacy helpers
    main_module = sys.modules.get("__main__") or sys.modules.get("MistHelper")  # WHY: locate host module
    if main_module is not None:  # WHY: only sync when a host module is loaded
        msp_privileges = getattr(main_module, "msp_privileges", [])  # WHY: preserve msp cache visibility
        PROGRESS_EMITTER = getattr(main_module, "PROGRESS_EMITTER", None)  # WHY: hook up progress emitter
    logging.debug("firmware_manager module globals rebound for org %s", config.org_id)  # WHY: confirm side effects


class FirmwareManager:
    """Advanced Firmware Management System for Mist Access Points.

    This class provides comprehensive firmware upgrade capabilities including:
    1. Firmware status monitoring and reporting
    2. Site-based bulk firmware upgrades
    3. Gateway template-based firmware upgrades
    4. Automatic site auto-upgrade configuration
    5. Multi-strategy upgrade orchestration (big_bang, canary, rrm, serial)
    6. Progress monitoring and audit logging

    Follows NASA/JPL coding standards for safety-critical operations with:
    - Comprehensive validation and error handling
    - Explicit user confirmation for destructive operations
    - Complete audit trails and logging
    - Rollback and recovery capabilities
    """

    def __init__(self, config: FirmwareManagerConfig) -> None:
        """Initialize FirmwareManager from an immutable ``FirmwareManagerConfig``.

        Args:
            config: Frozen dataclass carrying identity fields (``apisession``,
                ``org_id``) plus six optional dependency-injection hooks.
                Constructed exclusively by the MistHelper.py factory wrapper
                (six-callsite insulation — see FR-011).
        """
        logging.info("Initializing FirmwareManager for org %s", config.org_id)  # WHY: audit trail per Constitution VII
        self._config: FirmwareManagerConfig = config  # WHY: single source of truth for injected deps
        self.apisession = config.apisession  # WHY: back-compat attribute for helpers reading self.apisession
        self.org_id = config.org_id  # WHY: back-compat attribute for helpers reading self.org_id
        self._safe_input_fn: SafeInputFn = config.safe_input_fn or input  # WHY: default to built-in input()
        self._select_site_fn = config.select_site_fn  # WHY: preserve pre-refactor helper attribute
        self._check_cache_fn = config.check_cache_fn  # WHY: preserve pre-refactor cache helper attribute
        self._get_csv_path_fn = config.get_csv_path_fn  # WHY: preserve pre-refactor path helper attribute
        self._gateway_templates_fn = config.gateway_templates_fn  # WHY: preserve pre-refactor templates streamer
        self._sites_fn = config.sites_fn  # WHY: preserve pre-refactor sites streamer attribute
        _bind_module_globals(config)  # WHY: rebind module-scope globals for legacy helpers
        logging.debug("FirmwareManager init complete for org %s", config.org_id)  # WHY: confirm bootstrap finished

    def _compare_version_parts(self, current_parts: list[str], target_parts: list[str]) -> bool:
        """Compare version part lists numerically; return True if target is older than current."""
        for current_part, target_part in zip(current_parts, target_parts, strict=False):  # WHY: iterate part-wise
            outcome = self._compare_single_version_pair(current_part, target_part)  # WHY: delegate per-part
            if outcome is not None:  # WHY: only stop when a definitive verdict is reached
                return outcome  # WHY: propagate downgrade/upgrade decision
        return False  # WHY: all parts equal — not a downgrade

    def _compare_single_version_pair(self, current_part: str, target_part: str) -> bool | None:
        """Compare one version segment; return True if downgrade, False if upgrade, None if equal."""
        try:
            current_num, target_num = int(current_part), int(target_part)  # WHY: prefer numeric compare
        except ValueError:
            return self._compare_scalar_pair(target_part, current_part)  # WHY: lexical fallback
        return self._compare_scalar_pair(target_num, current_num)  # WHY: numeric compare via shared helper

    def _compare_scalar_pair(self, target: Any, current: Any) -> bool | None:
        """Return True if ``target < current`` (downgrade), False if greater (upgrade), None if equal."""
        if target < current:  # WHY: strictly older target -> downgrade
            return True  # WHY: definitive downgrade signal
        if target > current:  # WHY: strictly newer target -> upgrade
            return False  # WHY: definitive upgrade signal
        return None  # WHY: equal, defer to next segment

    def _is_firmware_downgrade(self, current_version: str, target_version: str) -> bool:
        """Check if the target version is a downgrade from the current version.

        This method performs a basic version comparison to detect potential downgrades.
        SSR firmware versions typically follow patterns like: 6.3.4-7.r2, 6.3.5-37.sts

        Args:
            current_version (str): Current firmware version
            target_version (str): Target firmware version

        Returns:
            bool: True if target_version appears to be older than current_version
        """
        if not current_version or not target_version:  # WHY: guard empty versions early
            return False  # WHY: cannot compare, assume upgrade path
        try:
            current_parts, target_parts = self._normalize_version_parts(  # WHY: pad to equal length
                current_version, target_version
            )
            return self._compare_version_parts(current_parts, target_parts)  # WHY: numeric compare
        except Exception as e:
            logging.warning(  # WHY: audit uncomparable version error
                "Could not compare versions %s vs %s: %s", current_version, target_version, e
            )
            return False  # WHY: fail-open — allow upgrade path if compare fails

    def _normalize_version_parts(self, current_version: str, target_version: str) -> tuple[list[str], list[str]]:
        """Split versions on '-', split remainder on '.', pad both to equal length."""
        current_parts = current_version.split("-")[0].split(".")  # WHY: drop suffix, split MMP
        target_parts = target_version.split("-")[0].split(".")  # WHY: same for target version
        max_len = max(len(current_parts), len(target_parts))  # WHY: choose common length
        while len(current_parts) < max_len:  # WHY: pad shorter current
            current_parts.append("0")  # WHY: zero-pad for numeric parity
        while len(target_parts) < max_len:  # WHY: pad shorter target
            target_parts.append("0")  # WHY: zero-pad for numeric parity
        return current_parts, target_parts  # WHY: hand equal-length parts to comparator

    def _prompt_scope_selection(self) -> str | None:
        """Display scope menu and prompt user to select status check scope (1-6).

        Returns:
            str: Scope choice ('1'-'6'), or None if cancelled.
        """
        print("\n  Select status check scope:")  # WHY: menu header
        print("   [1] Organization-wide status (all sites and devices)")  # WHY: scope 1 option
        print("   [2] Specific site status")  # WHY: scope 2 option
        print("   [3] Active upgrade operations only")  # WHY: scope 3 option
        print("   [4] Failed upgrades only")  # WHY: scope 4 option
        print("   [5] Continuous monitoring mode (auto-refresh until complete)")  # WHY: scope 5 option
        print("   [6] Org-level upgrade jobs (with P2P/scheduling details)")  # WHY: scope 6 option
        while True:  # WHY: retry loop until valid selection or cancel
            try:
                choice = self._safe_input_fn("Select scope (1-6): ", context="firmware_manager").strip()  # WHY: prompt
                if choice in ["1", "2", "3", "4", "5", "6"]:  # WHY: gate to valid range
                    logging.debug("User selected scope: %s", choice)  # WHY: audit trail
                    return choice  # WHY: propagate valid choice
                print(" Invalid selection. Please choose 1-6.")  # WHY: operator hint
                logging.debug("Invalid scope selection: %s", choice)  # WHY: audit
            except KeyboardInterrupt:  # WHY: allow ctrl-C to cancel cleanly
                print("\n Operation cancelled by user.")  # WHY: user feedback
                return None  # WHY: signal cancellation upstream

    def check_firmware_upgrade_status(
        self,
        scope_choice: str | None = None,
        site_filter: str | None = None,
    ) -> None:
        """Check current firmware upgrade status across the organization."""
        logging.info("Starting firmware upgrade status check scope=%s site=%s", scope_choice, site_filter)  # WHY: audit
        print(" Firmware Upgrade Status Check")  # WHY: banner
        print("=" * 60)  # WHY: divider
        scope_choice = self._resolve_scope_choice(scope_choice)  # WHY: prompt if not passed
        if scope_choice is None:  # WHY: user cancelled scope prompt
            return None  # WHY: exit cleanly
        site_filter = self._resolve_site_filter_for_status(scope_choice, site_filter)  # WHY: prompt if scope=2
        if scope_choice == "2" and site_filter is None:  # WHY: scope=2 without site => cancelled
            return None  # WHY: exit cleanly
        self._dispatch_status_scope(scope_choice, site_filter)  # WHY: route to correct handler
        logging.debug("Status check completed scope=%s", scope_choice)  # WHY: trace
        return None  # WHY: uniform sentinel return

    def _resolve_scope_choice(self, scope_choice: str | None) -> str | None:  # WHY: prompt-or-passthrough
        """Return scope selection: passthrough if provided, else prompt operator."""
        if scope_choice is not None:  # WHY: caller pre-selected
            return scope_choice  # WHY: honor pre-selection
        return self._prompt_scope_selection()  # WHY: interactive fallback

    def _resolve_site_filter_for_status(  # WHY: only scope=2 requires a site pick
        self,
        scope_choice: str,
        site_filter: str | None,
    ) -> str | None:
        """Return site filter for the status check; prompt when scope=2 and none supplied."""
        if scope_choice != "2" or site_filter is not None:  # WHY: only mode 2 with no filter needs prompt
            return site_filter  # WHY: pass through untouched
        logging.debug("User selected specific site mode")  # WHY: audit interactive path
        if self._select_site_fn is None:  # WHY: DI hook missing
            logging.error("select_site_fn not configured")  # WHY: audit config error
            return None  # WHY: cannot proceed
        chosen = self._select_site_fn()  # WHY: prompt operator
        if not chosen:  # WHY: user cancelled site selection
            print(" No site selected. Exiting.")  # WHY: operator visibility
            logging.warning("No site selected in specific site mode")  # WHY: audit
            return None  # WHY: signal cancellation to caller
        logging.debug("Selected site filter: %s", chosen)  # WHY: audit chosen site
        return cast(str, chosen)  # WHY: narrow Any-return DI hook to str for callers

    def _dispatch_status_scope(self, scope_choice: str, site_filter: str | None) -> None:
        """Route to the correct status handler based on scope."""
        if scope_choice == "5":  # WHY: continuous monitoring is separate flow
            logging.info("Entering continuous monitoring mode")  # WHY: audit
            self._continuous_monitoring_mode(site_filter)  # WHY: dispatch
            return None  # WHY: void handler completed
        if scope_choice == "6":  # WHY: org-level upgrade jobs listing
            logging.info("Fetching org-level upgrade jobs")  # WHY: audit
            self._show_org_level_upgrade_jobs()  # WHY: dispatch
            return None  # WHY: void handler completed
        self._execute_status_check(scope_choice, site_filter)  # WHY: default
        return None  # WHY: uniform sentinel

    def _continuous_monitoring_mode(self, site_filter: str | None = None) -> None:
        """Continuous monitoring mode that auto-refreshes upgrade status until complete or cancelled."""
        logging.info("Entering continuous monitoring mode site_filter=%s", site_filter)  # WHY: audit entry
        self._present_monitoring_header()  # WHY: emit banner explaining refresh cadence + Ctrl-C exit
        try:  # WHY: outer try catches user Ctrl-C for clean exit
            self._run_monitoring_loop(site_filter)  # WHY: delegate refresh loop to helper
        except KeyboardInterrupt:  # WHY: operator pressed Ctrl-C mid-refresh
            print("\n\n  Monitoring mode cancelled by user.")  # WHY: visible exit banner
            logging.info("Continuous monitoring mode cancelled by user")  # WHY: audit user cancel
            return  # WHY: exit without raising further
        logging.debug("Continuous monitoring mode exited normally")  # WHY: trace clean exit

    def _present_monitoring_header(self) -> None:  # WHY: extract banner block for testability
        """Print the fixed banner describing monitoring behavior."""
        print("\n  Continuous Monitoring Mode")  # WHY: title line
        print("=" * 70)  # WHY: divider matches other section headers
        print("   Monitoring active firmware upgrades...")  # WHY: purpose line
        print("   Press Ctrl+C to exit at any time")  # WHY: exit instruction
        print("   Auto-refreshing every 7 seconds")  # WHY: cadence disclosure
        print("   NOTE: Each refresh scans ALL devices for active upgrades")  # WHY: scope disclosure
        print("=" * 70)  # WHY: closing divider
        logging.info("Starting continuous monitoring mode with 7-second refresh interval")  # WHY: audit

    def _run_monitoring_loop(self, site_filter: str | None) -> None:
        """Drive the poll-print-sleep loop until all upgrades complete."""
        iteration = 0  # WHY: counter used in refresh banner
        while True:  # WHY: loop exits via break when all upgrades done or via KeyboardInterrupt
            iteration += 1  # WHY: increment before display so first refresh reads #1
            self._clear_monitoring_screen()  # WHY: fresh visual for each iteration
            self._present_monitoring_iteration_header(iteration)  # WHY: banner per iteration
            result = self._execute_monitoring_check(site_filter)  # WHY: fetch upgrades
            if self._handle_monitoring_result(result, iteration):  # WHY: True means loop should exit
                return  # WHY: propagate loop-exit signal
            time.sleep(7)  # WHY: pause before next refresh per documented cadence

    def _clear_monitoring_screen(self) -> None:  # WHY: platform abstraction wrapped in a helper
        """Clear the terminal window between refreshes."""
        import os  # noqa: PLC0415  # WHY: lazy import to keep monitoring cost off startup
        import platform  # noqa: PLC0415  # WHY: lazy import platform detection

        if platform.system() == "Windows":  # WHY: cmd.exe uses cls
            os.system("cls")  # nosec B605 B607  # WHY: intentional shell call for terminal reset
        else:  # WHY: POSIX terminals use clear
            os.system("clear")  # nosec B605 B607  # WHY: intentional shell call for terminal reset

    def _present_monitoring_iteration_header(self, iteration: int) -> None:  # WHY: per-refresh banner block
        """Print the header shown at the top of each refresh."""
        print("\n  Firmware Upgrade Monitoring - Live View")  # WHY: subtitle
        print("=" * 70)  # WHY: divider
        print(f"   Refresh #{iteration} | Press Ctrl+C to exit")  # WHY: progress + exit reminder
        print("   Scanning all devices for active upgrades...")  # WHY: informational hint
        print("=" * 70)  # WHY: closing divider

    def _handle_monitoring_result(self, result: int | None, iteration: int) -> bool:
        """Interpret the check result; return True if loop should exit."""
        if result is None:  # WHY: transient error path
            print("\n   Error fetching upgrade status. Retrying...")  # WHY: user-visible retry hint
            logging.warning("Monitoring iteration %s failed", iteration)  # WHY: audit failure
            return False  # WHY: keep polling despite one failed iteration
        if result == 0:  # WHY: zero active upgrades => job complete
            print("\n  All upgrades completed!")  # WHY: completion banner
            print("   No active firmware upgrades detected.")  # WHY: clarify outcome
            print("   Exiting monitoring mode.")  # WHY: user notice
            logging.info("Monitoring mode exiting - all upgrades complete")  # WHY: audit success
            return True  # WHY: signal loop exit
        print(f"\n   Found {result} device(s) actively upgrading")  # WHY: progress signal
        print("   Next refresh in 7 seconds...")  # WHY: set expectation for cadence
        return False  # WHY: continue polling

    def _print_upgrade_job_timing_info(self, details: dict[str, Any]) -> None:
        """Print start and reboot time for an upgrade job, converting epoch to human-readable."""
        from datetime import datetime as dt_module  # noqa: PLC0415

        start_time = details.get("start_time")  # WHY: read epoch start time
        if start_time:  # WHY: only render when present
            try:
                start_str = dt_module.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")  # WHY: format epoch
                print(f"    Start Time: {start_str}")  # WHY: human-readable output
            except Exception:
                print(f"    Start Time: {start_time} (epoch)")  # WHY: fallback to raw epoch
        reboot_at = details.get("reboot_at")  # WHY: read epoch reboot time
        if reboot_at:  # WHY: only render when present
            try:
                reboot_str = dt_module.fromtimestamp(reboot_at).strftime("%Y-%m-%d %H:%M:%S")  # WHY: format epoch
                print(f"    Reboot Time: {reboot_str}")  # WHY: human-readable output
            except Exception:
                print(f"    Reboot Time: {reboot_at} (epoch)")  # WHY: fallback to raw epoch

    def _print_upgrade_job_p2p_config(self, details: dict[str, Any]) -> None:
        """Print P2P, canary phase, and max failure configuration for an upgrade job."""
        enable_p2p = details.get("enable_p2p", False)  # WHY: read P2P flag
        print(f"    P2P Enabled: {enable_p2p}")  # WHY: report P2P setting
        if enable_p2p:  # WHY: extra details only if P2P is enabled
            cluster_size = details.get("p2p_cluster_size", "Not specified")  # WHY: read cluster size
            print(f"    P2P Cluster Size: {cluster_size}")  # WHY: report cluster size
            parallelism = details.get("p2p_parallelism", "Not specified")  # WHY: read parallelism
            print(f"    P2P Parallelism: {parallelism}")  # WHY: report parallelism
        canary_phases = details.get("canary_phases")  # WHY: read canary schedule
        if canary_phases:  # WHY: only render when present
            print(f"    Canary Phases: {canary_phases}")  # WHY: report canary phases
        max_failure = details.get("max_failure_percentage")  # WHY: read failure tolerance
        if max_failure is not None:  # WHY: 0 is a legitimate value, so use is not None
            print(f"    Max Failure %: {max_failure}")  # WHY: report failure ceiling
        current_phase = details.get("current_phase")  # WHY: read active phase
        if current_phase is not None:  # WHY: 0 is a legitimate value, so use is not None
            print(f"    Current Phase: {current_phase}")  # WHY: report current phase

    def _print_upgrade_job_progress_summary(self, details: dict[str, Any]) -> None:
        """Print progress counts (upgraded/downloaded/downloading) for an upgrade job."""
        targets = details.get("targets", {})  # WHY: read progress buckets
        if targets:  # WHY: only render when present
            total = targets.get("total", 0)  # WHY: total device count
            upgraded = len(targets.get("upgraded", []))  # WHY: count upgraded devices
            downloaded = len(targets.get("downloaded", []))  # WHY: count downloaded devices
            downloading = len(targets.get("download_requested", []))  # WHY: count in-flight downloads
            progress_line = (
                f"    Progress: {upgraded}/{total} upgraded, " f"{downloaded} downloaded, {downloading} downloading"
            )  # WHY: build progress summary line
            print(progress_line)  # WHY: report progress
        upgrades = details.get("upgrades", [])  # WHY: list of site-level upgrade records
        if upgrades:  # WHY: only render when present
            print(f"    Sites: {len(upgrades)} site upgrade(s)")  # WHY: report site count

    def _print_upgrade_job_detail_block(self, org_devices_api: Any, job_id: str) -> None:
        """Fetch detailed info for a single upgrade job and print all sections."""
        try:
            detail_response = org_devices_api.getOrgDeviceUpgrade(  # WHY: fetch job detail
                self.apisession, self.org_id, job_id
            )
            if not (detail_response and hasattr(detail_response, "data")):  # WHY: guard empty response
                return  # WHY: nothing to print
            details = detail_response.data if isinstance(detail_response.data, dict) else {}  # WHY: coerce to dict
            print(f"    Status: {details.get('status', 'Unknown')}")  # WHY: report job status
            print(f"    Target Version: {details.get('target_version', 'Unknown')}")  # WHY: report target version
            print(f"    Strategy: {details.get('strategy', 'Unknown')}")  # WHY: report upgrade strategy
            self._print_upgrade_job_timing_info(details)  # WHY: delegate timing detail
            self._print_upgrade_job_p2p_config(details)  # WHY: delegate P2P/canary detail
            self._print_upgrade_job_progress_summary(details)  # WHY: delegate progress detail
        except Exception as e:
            print(f"    Error fetching details: {e}")  # WHY: surface fetch error to operator
            logging.error("Error fetching upgrade job %s: %s", job_id, e)  # WHY: audit fetch failure

    def _show_org_level_upgrade_jobs(self) -> None:
        """Display org-level upgrade jobs with full configuration details.

        Orchestrator: fetch job list, iterate, print details, catch top-level errors.
        """
        logging.info("Showing org-level upgrade jobs org=%s", self.org_id)  # WHY: audit entry
        print("\n  Org-Level Upgrade Jobs")  # WHY: section header
        print("=" * 70)  # WHY: header underline
        try:  # WHY: guard API/import errors
            org_devices_api, upgrade_jobs = self._fetch_org_upgrade_jobs()  # WHY: uniform fetch helper
            if not upgrade_jobs:  # WHY: nothing to render
                print("  No org-level upgrade jobs found.")  # WHY: operator feedback
                return  # WHY: short-circuit exit
            print(f"  Found {len(upgrade_jobs)} org-level upgrade job(s)\n")  # WHY: count preview
            self._render_org_upgrade_jobs(org_devices_api, upgrade_jobs)  # WHY: per-job detail block
            print("=" * 70)  # WHY: closing divider
            print("  Org-level upgrade job details complete.")  # WHY: completion marker
        except Exception as exc:  # WHY: broad guard per spec
            print(f"  Error fetching org-level upgrades: {exc}")  # WHY: operator feedback
            logging.error("Error in _show_org_level_upgrade_jobs: %s", exc)  # WHY: audit failure
        logging.debug("Org-level upgrade jobs display done")  # WHY: trace exit

    def _fetch_org_upgrade_jobs(self) -> tuple[Any, list[Any]]:
        """Return (api_module, upgrade_jobs_list) tuple from the mist API."""
        import mistapi.api.v1.orgs.devices as org_devices_api  # noqa: PLC0415   # WHY: lazy import per policy

        print("  Fetching org-level upgrade jobs...")  # WHY: operator progress line
        list_response = org_devices_api.listOrgDeviceUpgrades(self.apisession, self.org_id)  # WHY: API call
        if not list_response or not hasattr(list_response, "data"):  # WHY: response shape guard
            return org_devices_api, []  # WHY: empty list signals no jobs
        upgrade_jobs = list_response.data if isinstance(list_response.data, list) else []  # WHY: normalize
        return org_devices_api, upgrade_jobs  # WHY: hand to renderer

    def _render_org_upgrade_jobs(self, org_devices_api: Any, upgrade_jobs: list[Any]) -> None:
        """Iterate over upgrade_jobs and print each job's detail block."""
        for job in upgrade_jobs:  # WHY: enumerate per-job records
            job_id = job.get("id") if isinstance(job, dict) else getattr(job, "id", None)  # WHY: dual shape
            if not job_id:  # WHY: skip malformed rows
                continue  # WHY: nothing to render
            print(f"  Upgrade Job: {job_id}")  # WHY: job header
            print("-" * 70)  # WHY: header underline
            self._print_upgrade_job_detail_block(org_devices_api, job_id)  # WHY: delegate detail rendering
            print()  # WHY: blank separator

    def _fetch_device_stats_for_monitoring(self, site_filter: str | None) -> Any:
        """Fetch fresh device statistics from API for monitoring purposes."""
        if site_filter:
            stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                self.apisession, site_filter, type="all", limit=1000
            )
        else:
            stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
                self.apisession, self.org_id, type="all", fields="*", limit=1000
            )
        return mistapi.get_all(response=stats_resp, mist_session=self.apisession)

    def _is_active_fw_update(self, fwupdate: dict[str, Any]) -> bool:
        """Return True if the fwupdate record represents an in-progress (non-stale) upgrade."""
        fw_status = fwupdate.get("status", "unknown")  # WHY: read current status
        fw_progress = fwupdate.get("progress", 0)  # WHY: read completion percent
        fw_timestamp = fwupdate.get("timestamp", 0)  # WHY: read last-update epoch
        is_active = fw_status in ("inprogress", "upgrading", "downloading")  # WHY: gate on status verb
        if is_active and fw_progress == 100 and fw_timestamp:  # WHY: detect stale 100%-complete records
            try:
                is_active = (time.time() - fw_timestamp) / 3600 <= 1  # WHY: only recent (<=1hr) counts as active
            except (ValueError, OSError, TypeError):
                pass  # WHY: guard bad epoch; leave is_active as-is
        return is_active  # WHY: propagate active flag

    def _get_active_upgrades_from_stats(self, all_device_stats: list[Any]) -> list[dict[str, Any]]:
        """Scan device stats and return a list of devices that are actively upgrading."""
        active_upgrades: list[dict[str, Any]] = []  # WHY: accumulator for filtered devices
        for device_stat in all_device_stats:  # WHY: iterate raw stat records
            fwupdate = device_stat.get("fwupdate")  # WHY: read firmware-update subrecord
            if not fwupdate or not self._is_active_fw_update(fwupdate):  # WHY: skip stale/absent
                continue
            active_upgrades.append(  # WHY: preserve compact snapshot for display
                {
                    "name": device_stat.get("name", "Unnamed"),  # WHY: device name for report
                    "type": device_stat.get("type", "unknown"),  # WHY: device type for report
                    "model": device_stat.get("model", "Unknown"),  # WHY: device model for report
                    "progress": fwupdate.get("progress", 0) or 0,  # WHY: progress percent
                    "status": fwupdate.get("status", "unknown"),  # WHY: status string
                }
            )
        return active_upgrades  # WHY: hand back filtered list

    def _print_active_upgrades_table(self, active_upgrades: list[dict[str, Any]]) -> None:
        """Print a formatted table of devices currently upgrading."""
        if not active_upgrades:  # WHY: skip render when nothing to show
            return
        import sys as _sys  # noqa: PLC0415

        _main_d = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")  # WHY: resolve MistHelper module
        print("\n  Devices Currently Upgrading:")  # WHY: section header
        print("  " + "=" * 86)  # WHY: top divider
        header = f"  {'Device Name':<25} {'Type':<10} {'Model':<15} {'Status':<12} {'Progress':<20}"  # WHY: header row
        print(header)  # WHY: column headers
        print("  " + "-" * 86)  # WHY: header/body separator
        for upgrade in active_upgrades:  # WHY: emit one row per active upgrade
            if _main_d is None:
                progress_bar = ""  # WHY: MistHelper unavailable; render blank bar
            else:
                progress_bar = _main_d.DisplayUtils.create_progress_bar(  # WHY: ASCII bar
                    upgrade["progress"], bar_length=15
                )
            print(
                f"  {upgrade['name']:<25} {upgrade['type']:<10} {upgrade['model']:<15} "
                f"{upgrade['status']:<12} {progress_bar}"
            )
        print("  " + "=" * 86)  # WHY: bottom divider

    def _execute_monitoring_check(self, site_filter: str | None = None) -> int | None:
        """Execute a single monitoring check iteration.

        This method performs a FULL fresh query of all devices on each call.
        It does NOT track specific devices from the first iteration - instead,
        it queries the API for ALL devices and checks their current upgrade status.

        This means:
        - New devices that start upgrading will be detected
        - Devices that complete will drop off automatically
        - Progress percentages are always current/live

        Returns:
            int: Number of devices actively upgrading, or None if error
        """
        try:
            all_device_stats = self._fetch_device_stats_for_monitoring(site_filter)
            active_upgrades = self._get_active_upgrades_from_stats(all_device_stats)
            self._print_active_upgrades_table(active_upgrades)
            return len(active_upgrades)
        except Exception as e:
            logging.exception("Error in monitoring check: %s", e)
            return None

    def _upgrade_ap_firmware_by_gateway_template(self) -> None:
        """Advanced AP firmware upgrade organized by Gateway Template assignment."""
        logging.info("Starting template-based AP firmware upgrade")  # WHY: audit start
        print(" Advanced AP Firmware Upgrade by Gateway Template")  # WHY: banner
        print("=" * 70)  # WHY: divider
        self._prepare_template_cache()  # WHY: ensure OrgGatewayTemplates.csv + SiteList.csv fresh
        template_id, template_name = self._select_template_for_upgrade()  # WHY: interactive template pick
        if template_id is None or template_name is None:  # WHY: user cancelled or none found
            return None  # WHY: exit early with no side effects
        sites_to_upgrade = self._resolve_template_sites(template_id, template_name)  # WHY: expand template to sites
        if not sites_to_upgrade:  # WHY: template has no site assignments
            return None  # WHY: nothing to do
        self._present_template_summary(template_id, template_name, sites_to_upgrade)  # WHY: recap to operator
        logging.debug("Template upgrade dispatch site_count=%d", len(sites_to_upgrade))  # WHY: audit dispatch
        self._execute_template_based_upgrade(sites_to_upgrade, template_name)  # WHY: delegate execution
        return None  # WHY: uniform sentinel return

    def _prepare_template_cache(self) -> None:  # WHY: reused CSV-freshness step for template flow
        """Warm cached template + site CSVs so downstream helpers can read them."""
        logging.info("Preparing template and site CSV cache")  # WHY: audit entry
        print("\n  Preparing template and site data...")  # WHY: operator progress hint
        if self._check_cache_fn is not None:  # WHY: DI-injected cache fn may be absent in tests
            self._check_cache_fn("OrgGatewayTemplates.csv", self._gateway_templates_fn)  # WHY: template CSV
            self._check_cache_fn("SiteList.csv", self._sites_fn)  # WHY: site inventory CSV
        logging.debug("Template CSV cache prepared")  # WHY: trace exit

    def _select_template_for_upgrade(self) -> tuple[str | None, str | None]:  # WHY: prompt + resolve
        """Load templates, prompt operator, return (template_id, template_name) or (None, None)."""
        template_name_to_id, template_sites_mapping = self._load_template_sites_mapping()  # WHY: load mapping
        if not template_name_to_id:  # WHY: no templates configured
            print(" No gateway templates found.")  # WHY: operator visibility
            logging.warning("No gateway templates available for upgrade")  # WHY: audit
            return None, None  # WHY: caller treats as cancellation
        selected_id, selected_name = self._prompt_template_selection(  # WHY: pick template
            template_name_to_id,
            template_sites_mapping,
        )
        if not selected_id:  # WHY: user cancelled selection
            print(" No template selected. Exiting.")  # WHY: operator visibility
            logging.info("Template-based upgrade cancelled - no template selected")  # WHY: audit
            return None, None  # WHY: caller treats as cancellation
        return selected_id, selected_name  # WHY: happy path returns concrete IDs

    def _resolve_template_sites(  # WHY: turn template ID into a concrete site list
        self,
        template_id: str,
        template_name: str,
    ) -> list[dict[str, Any]]:
        """Look up sites for the selected template; warn + return [] if empty."""
        _template_name_to_id, template_sites_mapping = self._load_template_sites_mapping()  # WHY: reload mapping
        sites_to_upgrade = template_sites_mapping.get(template_id, [])  # WHY: fetch mapped sites
        if not sites_to_upgrade:  # WHY: empty template
            print(f" No sites found using template '{template_name}'.")  # WHY: operator visibility
            logging.warning("No sites found for template %s (ID: %s)", template_name, template_id)  # WHY: audit
        return sites_to_upgrade  # WHY: pass typed mapping value back

    def _present_template_summary(  # WHY: emit operator-facing template recap
        self,
        template_id: str,
        template_name: str,
        sites_to_upgrade: list[dict[str, Any]],
    ) -> None:
        """Print the selection summary and log per-site debug details."""
        print("\n  Template Selection Summary:")  # WHY: section header
        print(f"   Selected Template: {template_name}")  # WHY: recap chosen template
        print(f"   Template ID: {template_id}")  # WHY: expose UUID for auditors
        print(f"   Sites in Template: {len(sites_to_upgrade)}")  # WHY: expected work size
        logging.info("Template upgrade '%s' with %s sites", template_name, len(sites_to_upgrade))  # WHY: audit
        for site_info in sites_to_upgrade:  # WHY: per-site debug trail
            logging.debug("  Site: %s (ID: %s)", site_info["name"], site_info["id"])  # WHY: audit

    def _ensure_template_csv_freshness(self) -> None:
        """Ensure that required template and site CSV files are fresh and available.

        This method generates or refreshes the CSV files needed for template-based
        operations if they don't exist or are stale.
        """
        logging.debug("Ensuring template CSV files are fresh")
        print("  Preparing template and site data...")

        # Generate required CSV files using existing export functions
        if self._check_cache_fn is not None:
            self._check_cache_fn("OrgGatewayTemplates.csv", self._gateway_templates_fn)
            self._check_cache_fn("SiteList.csv", self._sites_fn)

        logging.debug("Template CSV files ensured fresh")

    def _map_sites_to_template(
        self, template_sites_mapping: dict[str, list[dict[str, Any]]], site_list_path: str
    ) -> None:
        """Read site CSV and append each site to its assigned template's list."""
        with open(site_list_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gw_tid = row.get("gatewaytemplate_id", "").strip()
                site_id = row.get("id", "").strip()
                site_name = row.get("name", "").strip()
                if gw_tid in template_sites_mapping and site_id and site_name:
                    template_sites_mapping[gw_tid].append({"id": site_id, "name": site_name})

    def _log_template_mapping_stats(
        self,
        template_sites_mapping: dict[str, list[dict[str, Any]]],
        template_name_to_id: dict[str, str],
    ) -> None:
        """Log per-template site counts at DEBUG level."""
        for template_id, sites in template_sites_mapping.items():
            template_name = next((name for name, tid in template_name_to_id.items() if tid == template_id), "Unknown")
            logging.debug("Template '%s': %s sites", template_name, len(sites))

    def _load_template_sites_mapping(self) -> tuple[dict[str, str], dict[str, list[dict[str, Any]]]]:
        """Load gateway templates and create mapping of templates to their assigned sites.

        Returns:
            tuple: (template_name_to_id dict, template_sites_mapping dict)
        """
        logging.info("Loading gateway template-to-sites mapping org=%s", self.org_id)  # WHY: audit entry
        if self._get_csv_path_fn is None:  # WHY: guard early when path helper is not wired
            return {}, {}  # WHY: empty mapping short-circuit
        try:
            template_name_to_id, template_sites_mapping = self._read_gateway_templates_csv()  # WHY: read + parse
            site_list_path = self._get_csv_path_fn("SiteList.csv")  # WHY: resolve site list CSV path
            self._map_sites_to_template(template_sites_mapping, site_list_path)  # WHY: join sites onto templates
            self._log_template_mapping_stats(template_sites_mapping, template_name_to_id)  # WHY: audit stats
        except Exception as e:  # WHY: broad guard for FS/CSV parse errors
            logging.error("Failed to load template-sites mapping: %s", e)  # WHY: capture stack context
            print(f"! Failed to load template and site data: {e}")  # WHY: surface to operator
            return {}, {}  # WHY: safe fallback preserves menu flow
        logging.debug("Template mapping load complete count=%d", len(template_name_to_id))  # WHY: audit exit
        return template_name_to_id, template_sites_mapping  # WHY: hand back to orchestrator

    def _read_gateway_templates_csv(self) -> tuple[dict[str, str], dict[str, list[dict[str, Any]]]]:
        """Read OrgGatewayTemplates.csv and return (name->id, id->sites-list) mappings."""
        template_name_to_id: dict[str, str] = {}  # WHY: reverse-lookup for menu display
        template_sites_mapping: dict[str, list[dict[str, Any]]] = {}  # WHY: primary mapping keyed by template id
        if self._get_csv_path_fn is None:  # WHY: narrow Optional callable for mypy strict
            logging.warning("get_csv_path_fn not configured; returning empty template mapping")  # WHY: audit
            return template_name_to_id, template_sites_mapping  # WHY: safe empty fallback
        gateway_templates_path = self._get_csv_path_fn("OrgGatewayTemplates.csv")  # WHY: resolved above
        with open(gateway_templates_path, encoding="utf-8") as f:  # WHY: read templates roster
            reader = csv.DictReader(f)  # WHY: named-column parse
            for row in reader:  # WHY: iterate roster rows
                name = row.get("name", "").strip()  # WHY: display label
                tid = row.get("id", "").strip()  # WHY: template identifier
                if name and tid:  # WHY: skip rows missing either half of the pair
                    template_name_to_id[name] = tid  # WHY: record lookup entry
                    template_sites_mapping[tid] = []  # WHY: initialize empty site list slot
        logging.info("Loaded %s gateway templates", len(template_name_to_id))  # WHY: parity with pre-refactor
        return template_name_to_id, template_sites_mapping  # WHY: mappings for downstream site join

    def _prompt_template_selection(
        self,
        template_name_to_id: dict[str, str],
        template_sites_mapping: dict[str, list[dict[str, Any]]],
    ) -> tuple[str | None, str | None]:
        """Present interactive template selection with site counts.

        Args:
            template_name_to_id: Dict mapping template names to IDs
            template_sites_mapping: Dict mapping template IDs to site lists

        Returns:
            tuple: (selected_template_id, selected_template_name) or (None, None)
        """
        logging.info("Prompting template selection count=%d", len(template_name_to_id))  # WHY: entry audit
        sorted_templates = sorted(template_name_to_id.items())  # WHY: stable order
        template_index_map = self._render_template_selection_menu(  # WHY: draw menu, build index
            sorted_templates, template_sites_mapping
        )
        result = self._loop_template_selection_input(  # WHY: read until valid or cancel
            template_index_map, template_name_to_id, len(sorted_templates)
        )
        logging.debug("Template selection resolved template=%s", result[1])  # WHY: exit audit
        return result

    def _render_template_selection_menu(
        self,
        sorted_templates: list[tuple[str, str]],
        template_sites_mapping: dict[str, list[dict[str, Any]]],
    ) -> dict[str, tuple[str, str]]:
        """Print the template selection table and return the index->(id, name) map."""
        print("\n  Available Gateway Templates:")  # WHY: section header
        print(f"  {'Index':<8} {'Template Name':<40} {'Sites':<8}")  # WHY: table header
        print(f"  {'-' * 8} {'-' * 40} {'-' * 8}")  # WHY: header divider
        template_index_map: dict[str, tuple[str, str]] = {}  # WHY: map index-string -> template payload
        for idx, (template_name, template_id) in enumerate(sorted_templates, 1):  # WHY: 1-based for UX
            site_count = len(template_sites_mapping.get(template_id, []))  # WHY: display column
            print(f"  [{idx:<7}] {template_name:<40} {site_count:<8}")  # WHY: row output
            template_index_map[str(idx)] = (template_id, template_name)  # WHY: capture payload
        print("\n  Selection Options:")  # WHY: footer header
        print(f"   !? Enter index number (1-{len(sorted_templates)})")  # WHY: index instruction
        print("   !? Type exact template name")  # WHY: name instruction
        print("   !? Press Enter to cancel")  # WHY: cancel instruction
        return template_index_map  # WHY: hand back to loop

    def _loop_template_selection_input(
        self,
        template_index_map: dict[str, tuple[str, str]],
        template_name_to_id: dict[str, str],
        total_templates: int,
    ) -> tuple[str | None, str | None]:
        """Read user input until a valid template selection or cancel."""
        while True:  # WHY: retry until match or cancel
            try:
                user_input = self._safe_input_fn(  # WHY: prompt with audit tag
                    "\n  Select template: ", context="firmware_manager"
                ).strip()
            except KeyboardInterrupt:
                print("\n   Template selection cancelled.")  # WHY: cancel notice
                return None, None  # WHY: cancel sentinel
            if not user_input:  # WHY: blank input cancels
                return None, None  # WHY: cancel sentinel
            resolved = self._resolve_template_selection(  # WHY: index-or-name lookup
                user_input, template_index_map, template_name_to_id
            )
            if resolved is not None:  # WHY: valid short-circuits
                return resolved  # WHY: forward tuple
            print(  # WHY: invalid selection feedback
                f"   Invalid selection. Please enter a valid index (1-{total_templates}) or exact template name."
            )

    def _resolve_template_selection(
        self,
        user_input: str,
        template_index_map: dict[str, tuple[str, str]],
        template_name_to_id: dict[str, str],
    ) -> tuple[str, str] | None:
        """Match user_input against index map first, then exact template name."""
        if user_input in template_index_map:  # WHY: numeric index path
            template_id, template_name = template_index_map[user_input]  # WHY: unpack payload
            logging.debug("Template selected by index %s: %s", user_input, template_name)  # WHY: audit
            return template_id, template_name  # WHY: valid result
        if user_input in template_name_to_id:  # WHY: exact-name path
            template_id = template_name_to_id[user_input]  # WHY: id lookup by name
            logging.debug("Template selected by name: %s", user_input)  # WHY: audit
            return template_id, user_input  # WHY: valid result
        return None  # WHY: no match sentinel

    def _execute_template_based_upgrade(self, sites_to_upgrade: list[dict[str, Any]], template_name: str) -> None:
        """Execute firmware upgrade for all sites in a gateway template.

        This method reuses the existing bulk upgrade logic but with template context.

        Args:
            sites_to_upgrade: List of site info dicts with 'id' and 'name'
            template_name: Name of the selected template for logging

        Returns:
            Results of the upgrade operation
        """
        logging.info(  # WHY: audit entry with sizing
            "Executing template-based firmware upgrade for template '%s' with %s sites",
            template_name,
            len(sites_to_upgrade),
        )
        self._print_template_upgrade_banner(template_name, sites_to_upgrade)  # WHY: operator visibility
        self._bulk_upgrade_ap_firmware_by_site(  # WHY: reuse bulk site upgrade with override list
            sites_to_upgrade_override=sites_to_upgrade,
        )
        logging.debug("Template-based upgrade returned for '%s'", template_name)  # WHY: audit exit

    def _print_template_upgrade_banner(self, template_name: str, sites_to_upgrade: list[Any]) -> None:
        """Render the fixed banner + site table for the template-based upgrade run."""
        print("\n  Template-Based Upgrade Execution")  # WHY: section header for operator
        print(f"  Template: {template_name}")  # WHY: identify selected template
        print(f"  Sites to process: {len(sites_to_upgrade)}")  # WHY: sizing
        print(f"  {'Site Name':<40} {'Site ID':<40}")  # WHY: column headings
        print(f"  {'-' * 40} {'-' * 40}")  # WHY: divider row
        for site_info in sites_to_upgrade:  # WHY: enumerate each site row
            print(f"  {site_info['name']:<40} {site_info['id']:<40}")  # WHY: formatted output row

    def execute_firmware_upgrade_with_mode_selection(self) -> list[dict[str, Any]] | None:
        """Main entry point for AP firmware upgrades with mode selection.

        Presents site/template/MSP choice; delegates to picked flow. MSP option
        appears only when an MSP session is active.
        """
        logging.info("Starting AP firmware upgrade with mode selection")  # WHY: audit entry
        self._emit_ap_upgrade_progress_start()  # WHY: cross-cut progress signal
        msp_mode_available = self._is_msp_mode_available()  # WHY: gate MSP branch
        self._print_ap_upgrade_banner()  # WHY: title box
        valid_choices, prompt = self._render_ap_mode_menu(msp_mode_available)  # WHY: menu + choices contract
        mode_choice = self._prompt_ap_upgrade_mode(prompt, valid_choices)  # WHY: read operator selection
        if mode_choice is None:  # WHY: KeyboardInterrupt cancel
            return None  # WHY: honour operator cancel
        result = self._dispatch_ap_upgrade_mode(mode_choice)  # WHY: route chosen flow
        logging.debug("AP upgrade mode dispatch done choice=%s", mode_choice)  # WHY: trace exit
        return result  # WHY: pass through flow result

    def _emit_ap_upgrade_progress_start(self) -> None:
        """Fire the progress emitter start event for menu 90 (AP firmware)."""
        emitter = PROGRESS_EMITTER  # WHY: module-global emitter
        if emitter:  # WHY: emitter is optional
            emitter.emit_progress_start("90", "firmware_upgrade", 1)  # WHY: single-op progress

    def _is_msp_mode_available(self) -> bool:
        """Return True when MSP privileges are cached (MSP session active)."""
        global msp_privileges  # WHY: read module-global cache
        return bool(msp_privileges)  # WHY: truthy on non-empty list

    def _print_ap_upgrade_banner(self) -> None:
        """Print the AP firmware upgrade banner (title + underline)."""
        print(" Advanced AP Firmware Upgrade")  # WHY: page title
        print("=" * 60)  # WHY: title underline

    def _render_ap_mode_menu(self, msp_mode_available: bool) -> tuple[list[str], str]:
        """Print the mode menu and return (valid_choices, prompt) tuple."""
        print("\n  Select upgrade mode:")  # WHY: menu heading
        print("   [1] By Site - Upgrade specific sites (CSV file, bulk list, or single site selection)")  # opt1
        print("   [2] By Gateway Template - Upgrade all sites assigned to a selected Gateway Template")  # opt2
        if msp_mode_available:  # WHY: extra MSP branch
            print("   [3] MSP Multi-Org - Upgrade across multiple organizations (MSP session active)")  # opt3
            return ["1", "2", "3"], "\n  Select mode (1-3): "  # WHY: three-way choice contract
        return ["1", "2"], "\n  Select mode (1-2): "  # WHY: two-way choice contract

    def _prompt_ap_upgrade_mode(self, prompt: str, valid_choices: list[str]) -> str | None:
        """Loop until operator enters a valid choice; return None on KeyboardInterrupt."""
        while True:  # WHY: retry until valid/cancel
            try:  # WHY: catch Ctrl-C
                mode_choice = self._safe_input_fn(prompt, context="firmware_manager").strip()  # WHY: audited
            except KeyboardInterrupt:  # WHY: operator cancel
                print("\n\n  Firmware upgrade cancelled by user.")  # WHY: operator feedback
                logging.info("Firmware upgrade cancelled during mode selection")  # WHY: audit cancel
                return None  # WHY: signal cancel to caller
            if mode_choice in valid_choices:  # WHY: gate valid tokens only
                return mode_choice  # WHY: hand to dispatcher
            print(f"   Invalid selection. Please choose {'/'.join(valid_choices)}.")  # WHY: retry hint
            logging.debug("Invalid mode selection: %s", mode_choice)  # WHY: audit bad input

    def _dispatch_ap_upgrade_mode(self, mode_choice: str) -> list[dict[str, Any]] | None:
        """Route the validated mode choice to the appropriate AP upgrade flow."""
        if mode_choice == "1":  # WHY: site-based branch
            logging.info("User selected site-based upgrade mode")  # WHY: audit selection
            print("\n  Site-based upgrade mode selected")  # WHY: operator confirmation
            self._bulk_upgrade_ap_firmware_by_site()  # WHY: void bulk flow
            return None  # WHY: site-based flow has no aggregate result
        if mode_choice == "2":  # WHY: template-based branch
            logging.info("User selected template-based upgrade mode")  # WHY: audit selection
            print("\n  Template-based upgrade mode selected")  # WHY: operator confirmation
            self._upgrade_ap_firmware_by_gateway_template()  # WHY: template flow entry
            return None  # WHY: template flow has no aggregate result
        logging.info("User selected MSP multi-org upgrade mode")  # WHY: MSP branch (mode==3)
        print("\n  MSP Multi-Organization upgrade mode selected")  # WHY: operator confirmation
        return self._execute_msp_multi_org_upgrade()  # WHY: MSP orchestrator entry

    def _add_org_to_upgrade_plan(
        self,
        upgrade_plan: list[dict[str, Any]],
        msp_id: str,
        msp_name: str,
        org_info: dict[str, Any],
    ) -> None:
        """Select sites for one org and append it to the upgrade plan if sites are selected."""
        org_target_id = org_info["id"]
        org_name = org_info["name"]
        print(f"\n    Organization: {org_name}")
        selected_sites = self._select_sites_for_org_upgrade(org_target_id, org_name)  # WHY: interactive site pick
        if not selected_sites:
            print(f"      Skipping org {org_name} - no sites selected")
            return
        upgrade_plan.append(
            {
                "msp_id": msp_id,
                "msp_name": msp_name,
                "org_id": org_target_id,
                "org_name": org_name,
                "sites": selected_sites,
            }
        )

    def _build_msp_upgrade_plan(self, selected_msps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Iterate MSPs and their orgs to build the full upgrade plan."""
        upgrade_plan: list[dict[str, Any]] = []
        for msp_info in selected_msps:
            msp_id = msp_info["msp_id"]
            msp_name = msp_info.get("msp_name", "Unknown MSP")
            print(f"\n{'-' * 70}\n  MSP: {msp_name}\n{'-' * 70}")
            selected_orgs = self._select_orgs_for_upgrade(msp_id, msp_name)  # WHY: typed org selector
            if not selected_orgs:
                print(f"    Skipping MSP {msp_name} - no organizations selected")
                continue
            for org_info in selected_orgs:
                self._add_org_to_upgrade_plan(upgrade_plan, msp_id, msp_name, org_info)
        return upgrade_plan

    def _confirm_msp_upgrade(self, upgrade_plan: list[dict[str, Any]]) -> bool:
        """Print destructive-operation warning and ask user to type UPGRADE.

        Returns:
            True if user confirmed; False otherwise.
        """
        total_sites = sum(len(p["sites"]) for p in upgrade_plan)  # WHY: aggregate site count across orgs
        total_orgs = len(upgrade_plan)  # WHY: total org count for banner
        divider = "!" * 68  # WHY: banner divider
        print(f"\n  {divider}\n  !  DESTRUCTIVE OPERATION - FIRMWARE UPGRADE ACROSS MULTIPLE ORGS  !\n  {divider}\n")
        print("  You are about to upgrade AP firmware in:")  # WHY: preamble
        print(f"    - {total_orgs} organization(s)")  # WHY: report org count
        print(f"    - {total_sites} site(s) total")  # WHY: report site count
        print()
        try:
            prompt_text = "  Type 'UPGRADE' to proceed: "  # WHY: build prompt text
            confirm = self._safe_input_fn(prompt_text, context="msp_firmware_upgrade").strip()  # WHY: hard prompt
        except SystemExit:
            return False  # WHY: user cancelled via safe_input SystemExit
        if confirm != "UPGRADE":  # WHY: enforce literal-match confirmation
            print("  X Upgrade cancelled - confirmation not received")  # WHY: user feedback
            logging.warning("MSP multi-org upgrade cancelled - user did not confirm")  # WHY: audit
            return False  # WHY: signal abort upstream
        return True  # WHY: confirmed and safe to proceed

    def _execute_msp_multi_org_upgrade(self) -> list[dict[str, Any]] | None:
        """Execute firmware upgrade across multiple MSPs and organizations."""
        logging.info("Starting MSP multi-org upgrade orchestrator")  # WHY: audit entry
        dry_run = getattr(globals().get("args", None), "dry_run", False)  # WHY: honor CLI dry-run flag
        self._print_msp_multi_org_banner(dry_run)  # WHY: render fixed banner + warning block
        upgrade_plan = self._collect_msp_upgrade_plan()  # WHY: drive MSP + org + site selection
        if not upgrade_plan:  # WHY: None (cancel) or empty (no targets) both abort
            if upgrade_plan is not None:  # WHY: distinguish empty from cancel for messaging
                print("\n  No upgrade targets configured. Operation cancelled.")  # WHY: surface to operator
            return None  # WHY: nothing to execute
        results = self._finalize_msp_upgrade(upgrade_plan, dry_run)  # WHY: preview + confirm + run + summary
        logging.debug("MSP multi-org upgrade complete result_count=%d", len(results) if results else 0)  # WHY: audit
        return results  # WHY: return aggregate results to caller

    def _finalize_msp_upgrade(self, upgrade_plan: list[Any], dry_run: bool) -> list[dict[str, Any]] | None:
        """Render plan summary, confirm, execute, and print closing summary; return results or None."""
        self._display_upgrade_plan_summary(upgrade_plan, dry_run)  # WHY: preview via typed helper
        if not self._await_msp_upgrade_confirmation(upgrade_plan, dry_run):  # WHY: gate execution
            return None  # WHY: operator declined confirmation
        results = self._execute_msp_upgrade_plan(upgrade_plan, dry_run)  # WHY: run
        self._print_msp_upgrade_summary(results, dry_run)  # WHY: closing summary
        return results  # WHY: return typed list to caller

    def _print_msp_multi_org_banner(self, dry_run: bool) -> None:
        """Render the fixed banner + warning block for the MSP multi-org upgrade flow."""
        print(f"\n{'=' * 70}\n  MSP MULTI-ORGANIZATION FIRMWARE UPGRADE\n{'=' * 70}\n")  # WHY: section header
        if dry_run:  # WHY: mark simulation runs distinctly
            print("  >> DRY-RUN MODE ENABLED <<\n  >> No actual upgrades will be performed - simulation only <<\n")
        print("  WARNING: This will upgrade AP firmware across multiple organizations.")  # WHY: risk note
        print("  Please review selections carefully before confirming.\n")  # WHY: operator caution

    def _collect_msp_upgrade_plan(self) -> list[Any] | None:
        """Drive MSP + org + site selection; return upgrade plan list, or None on cancel."""
        selected_msps = self._select_msps_for_upgrade()  # WHY: pick MSPs via typed selector
        if not selected_msps:  # WHY: cancel signal from selector
            print("  Cancelled - no MSP selected")  # WHY: operator feedback
            return None  # WHY: propagate cancel upward
        print(f"\n  + Selected {len(selected_msps)} MSP(s)")  # WHY: confirm count
        upgrade_plan = self._build_msp_upgrade_plan(selected_msps)  # WHY: expand MSPs -> orgs -> sites
        return upgrade_plan  # WHY: empty list means no targets; caller handles

    def _await_msp_upgrade_confirmation(self, upgrade_plan: list[Any], dry_run: bool) -> bool:
        """Return True when execution should proceed (dry-run auto-approves)."""
        if dry_run:  # WHY: simulations skip confirmation prompts
            print("\n  >> DRY-RUN: Skipping confirmation - proceeding with simulation <<")  # WHY: signal skip
            return True  # WHY: proceed with simulated execution
        return self._confirm_msp_upgrade(upgrade_plan)  # WHY: delegate to interactive confirm prompt

    def _select_msps_for_upgrade(self) -> list[dict[str, Any]] | None:
        """Select MSPs for multi-org upgrade with support for multi-selection.

        Returns list of selected MSP dicts or None if cancelled. Supports single
        index, comma-separated indices, dash/'through' ranges, and 'all'.
        """
        logging.info("Selecting MSPs for multi-org upgrade org=%s", self.org_id)  # WHY: audit entry
        global msp_privileges  # WHY: read module-global cache
        if not msp_privileges:  # WHY: guard empty MSP list
            logging.debug("No MSPs available; returning None")  # WHY: trace early exit
            return None  # WHY: caller handles None as cancel
        if len(msp_privileges) == 1:  # WHY: single-MSP shortcut
            return self._auto_select_single_msp()  # WHY: skip prompt when only one
        self._display_msps_for_selection()  # WHY: numbered list + options
        selection = self._prompt_msp_selection_input()  # WHY: capture operator token
        if selection is None:  # WHY: 'q' or SystemExit path
            return None  # WHY: bubble cancel up
        result = self._resolve_msp_selection(selection)  # WHY: turn token into MSP list
        logging.debug("MSP selection resolved selected=%d", len(result) if result else 0)  # WHY: audit result
        return result  # WHY: return chosen MSP dicts

    def _auto_select_single_msp(self) -> list[dict[str, Any]]:
        """Return the sole MSP wrapped in a list with a preview log line."""
        global msp_privileges  # WHY: read module-global cache
        msp_name = msp_privileges[0].get("msp_name", "Unknown")  # WHY: display friendly name
        print(f"  Single MSP available: {msp_name}")  # WHY: operator preview
        logging.debug("Auto-selected sole MSP=%s", msp_name)  # WHY: audit auto-select
        return cast(list[dict[str, Any]], msp_privileges)  # WHY: narrow module-global list for callers

    def _display_msps_for_selection(self) -> None:
        """Print the numbered list of MSPs and the selection-syntax help block."""
        global msp_privileges  # WHY: read module-global cache
        print("  Available MSPs:")  # WHY: section header
        print("")  # WHY: visual spacing
        for idx, msp in enumerate(msp_privileges, start=1):  # WHY: enumerate for 1-based UI
            msp_name = msp.get("msp_name", "Unknown")  # WHY: safe name fallback
            msp_role = msp.get("role", "unknown")  # WHY: safe role fallback
            print(f"    {idx:>3}. {msp_name} (role: {msp_role})")  # WHY: aligned numeric column
        print("")  # WHY: separator before help
        print("  Selection options:")  # WHY: help-block header
        print("    - Single: '1'")  # WHY: teach single-index syntax
        print("    - Multiple: '1,3,5'")  # WHY: teach comma syntax
        print("    - Range: '1-3' or '1 through 3'")  # WHY: teach range syntax
        print("    - All: 'all'")  # WHY: teach all-shortcut
        print("    - Cancel: 'q'")  # WHY: teach cancel token
        print("")  # WHY: separator before prompt

    def _prompt_msp_selection_input(self) -> str | None:
        """Prompt operator for MSP selection token; return normalized string or None."""
        try:  # WHY: safe_input may raise SystemExit
            token = self._safe_input_fn("  Select MSP(s): ", context="msp_multi_select")  # WHY: audited prompt
        except SystemExit:  # WHY: honour Ctrl-C / EOF
            logging.debug("SystemExit at MSP selection prompt")  # WHY: trace cancel path
            return None  # WHY: bubble cancel up
        selection = token.strip().lower()  # WHY: normalize casing/spaces
        if selection == "q" or selection == "":  # WHY: explicit cancel tokens
            return None  # WHY: bubble cancel up
        return selection  # WHY: pass to resolver

    def _resolve_msp_selection(self, selection: str) -> list[dict[str, Any]] | None:
        """Turn a normalized selection token into a list of MSP dicts."""
        global msp_privileges  # WHY: read module-global cache
        if selection == "all":  # WHY: fast-path all shortcut
            return cast(list[dict[str, Any]], msp_privileges)  # WHY: entire cached list narrowed for caller
        selected_indices = self._parse_selection_input(selection, len(msp_privileges))  # WHY: shared parser
        if not selected_indices:  # WHY: reject malformed tokens
            print("  X Invalid selection")  # WHY: operator feedback
            logging.debug("Invalid MSP selection token=%s", selection)  # WHY: trace failure
            return None  # WHY: bubble cancel up
        return [msp_privileges[idx] for idx in selected_indices]  # WHY: materialize chosen MSPs

    def _extract_response_list(self, response: Any) -> list[Any] | None:
        """Coerce a Mist API response into a list, or None when empty/absent."""
        data = getattr(response, "data", None) if response else None  # WHY: safe attribute access
        if not data:  # WHY: empty payload -> None sentinel
            return None  # WHY: signal absence to caller
        return data if isinstance(data, list) else [data]  # WHY: normalize single-object payloads

    def _fetch_msp_org_list(self, msp_id: str) -> list[dict[str, Any]] | None:
        """Fetch and sort the list of orgs for an MSP via API.

        Returns:
            Sorted list of org dicts, or None if unavailable.
        """
        import mistapi.api.v1.msps.orgs as msp_orgs_api  # noqa: PLC0415

        global apisession
        logging.info("Fetching MSP org list msp=%s", msp_id)  # WHY: audit entry
        response = msp_orgs_api.listMspOrgs(apisession, msp_id)  # WHY: HTTP call for MSP roster
        orgs_data = self._extract_response_list(response)  # WHY: normalize response into list-or-None
        if orgs_data is None:  # WHY: absence sentinel
            logging.debug("MSP org list empty msp=%s", msp_id)  # WHY: trace empty result
            return None  # WHY: caller treats None as unavailable
        sorted_orgs = sorted(orgs_data, key=lambda x: x.get("name", "").lower()) or None  # WHY: order + sentinel
        logging.debug("MSP org list count=%d msp=%s", len(sorted_orgs) if sorted_orgs else 0, msp_id)  # WHY: audit
        return sorted_orgs  # WHY: propagate to caller

    def _select_orgs_for_upgrade(self, msp_id: str, msp_name: str) -> list[dict[str, Any]] | None:
        """Fetch orgs from MSP and let operator select which to upgrade.

        Supports single index, comma-separated indices, dash ranges, 'all', 'q'.
        Returns list of selected org dicts or None if cancelled/failed.
        """
        logging.info("Selecting orgs for MSP upgrade msp=%s", msp_name)  # WHY: audit destructive selection
        orgs_data = self._fetch_orgs_for_selection(msp_id, msp_name)  # WHY: fetch + validate org list
        if not orgs_data:  # WHY: fetch failed or MSP has no orgs
            logging.debug("Org selection aborted - no orgs available")  # WHY: trace early exit
            return None  # WHY: preserve pre-refactor cancel behavior
        self._display_orgs_for_selection(orgs_data)  # WHY: render numbered index for operator
        selection = self._prompt_org_selection_input()  # WHY: read operator picker string
        if selection is None:  # WHY: EOF/interrupt/blank input
            logging.debug("Org selection cancelled by operator")  # WHY: trace decline
            return None  # WHY: signal cancel
        result = self._resolve_org_selection(selection, orgs_data)  # WHY: parse picker string into org list
        logging.debug("Org selection resolved selected=%d", len(result) if result else 0)  # WHY: trace outcome
        return result  # WHY: propagate to caller (may be None on invalid input)

    def _fetch_orgs_for_selection(self, msp_id: str, msp_name: str) -> list[dict[str, Any]] | None:
        """Fetch the MSP org list and print operator-facing status.

        Returns the list of org dicts on success or None on API failure /
        missing session / empty response.
        """
        global apisession  # WHY: module-global session set by MistHelper factory
        logging.info("Fetching MSP orgs for upgrade selection msp=%s", msp_id)  # WHY: audit API call
        print(f"    Fetching organizations from MSP {msp_name}...")  # WHY: operator progress feedback
        if apisession is None:  # WHY: defensive guard against unbound module global
            print("    X API session not initialized")  # WHY: operator diagnostic
            logging.warning("apisession is None during org fetch for msp=%s", msp_id)  # WHY: audit misconfiguration
            return None  # WHY: cannot proceed without session
        try:
            orgs_data = self._fetch_msp_org_list(msp_id)  # WHY: delegate paginated MSP-orgs API call
        except Exception as exc:  # WHY: API layer may raise on network/auth failure
            print(f"    X Error fetching organizations: {exc}")  # WHY: operator diagnostic
            logging.error("Failed to fetch MSP orgs for upgrade: %s", exc)  # WHY: audit exception detail
            return None  # WHY: signal fetch failure to caller
        if not orgs_data:  # WHY: MSP returned zero orgs or None
            print("    X Failed to retrieve organizations or no orgs found")  # WHY: operator diagnostic
            logging.warning("MSP %s returned no orgs for upgrade selection", msp_id)  # WHY: audit empty result
            return None  # WHY: signal caller nothing to display
        logging.debug("Fetched orgs count=%d for msp=%s", len(orgs_data), msp_id)  # WHY: trace count
        return orgs_data  # WHY: hand off to display step

    def _display_orgs_for_selection(self, orgs_data: list[dict[str, Any]]) -> None:
        """Print numbered org list plus selection-syntax help."""
        logging.debug("Rendering org selection table count=%d", len(orgs_data))  # WHY: trace UI helper
        print(f"    Found {len(orgs_data)} organization(s):\n")  # WHY: operator context header
        for idx, org in enumerate(orgs_data, start=1):  # WHY: 1-based index for operator readability
            org_name = org.get("name", "Unknown")  # WHY: tolerate missing name field
            org_id_preview = org.get("id", "N/A")[:8]  # WHY: truncated ID keeps table compact
            print(f"      {idx:>3}. {org_name} ({org_id_preview}...)")  # WHY: aligned numbered row
        print("\n    Selection: single '1', multiple '1,3,5', range '1-3', 'all', or 'q'\n")  # WHY: syntax help

    def _prompt_org_selection_input(self) -> str | None:
        """Prompt operator for org selection string; returns lowercase text or None."""
        logging.debug("Prompting operator for org selection")  # WHY: trace prompt entry
        try:
            selection = (
                self._safe_input_fn("    Select organization(s): ", context="org_multi_select").strip().lower()
            )  # WHY: strip + lower normalizes 'ALL', ' 1-3 ', etc.
        except SystemExit:  # WHY: safe_input raises SystemExit on EOF/interrupt for SSH-safe abort
            logging.info("Org selection prompt cancelled (EOF/interrupt)")  # WHY: audit SSH-safe cancel
            return None  # WHY: signal cancel to caller
        if selection in ("q", ""):  # WHY: explicit quit or empty enter = cancel
            logging.debug("Org selection returned quit token '%s'", selection)  # WHY: trace decline
            return None  # WHY: signal cancel
        return selection  # WHY: hand normalized token to resolver

    def _resolve_org_selection(self, selection: str, orgs_data: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        """Resolve normalized selection token into a list of org dicts.

        Accepts 'all' (returns full list), indices, ranges, comma lists. Returns
        None when the token cannot be parsed into any valid index.
        """
        logging.debug("Resolving org selection token='%s' pool=%d", selection, len(orgs_data))  # WHY: trace resolve
        if selection == "all":  # WHY: shortcut for MSP-wide upgrade fan-out
            logging.info("Operator selected all %d orgs", len(orgs_data))  # WHY: audit bulk selection
            return orgs_data  # WHY: return full list unchanged
        selected_indices = self._parse_selection_input(selection, len(orgs_data))  # WHY: shared index parser
        if not selected_indices:  # WHY: parser rejected the token (invalid syntax / out-of-range)
            print("    X Invalid selection")  # WHY: operator diagnostic
            logging.warning("Org selection token '%s' produced zero indices", selection)  # WHY: audit reject
            return None  # WHY: signal caller to retry or abort
        picked = [orgs_data[idx] for idx in selected_indices]  # WHY: project indices into org dicts
        logging.info("Operator selected %d of %d orgs", len(picked), len(orgs_data))  # WHY: audit final count
        return picked  # WHY: hand off to upgrade dispatcher

    def _fetch_and_validate_org_sites(self, target_org_id: str) -> list[dict[str, Any]] | None:
        """Fetch, validate, and sort the site list for an org.

        Returns:
            Sorted list of site dicts, or None if unavailable.
        """
        import mistapi.api.v1.orgs.sites as org_sites_api  # noqa: PLC0415

        global apisession
        logging.info("Fetching org sites org=%s", target_org_id)  # WHY: audit entry
        response = org_sites_api.listOrgSites(apisession, target_org_id)  # WHY: HTTP call for site roster
        sites_data = self._extract_response_list(response)  # WHY: reuse shared list-or-None extractor
        if sites_data is None:  # WHY: absence sentinel
            logging.debug("Org site list empty org=%s", target_org_id)  # WHY: trace empty result
            return None  # WHY: caller treats None as unavailable
        sorted_sites = sorted(sites_data, key=lambda x: x.get("name", "").lower()) or None  # WHY: order+sentinel
        logging.debug("Org sites count=%d org=%s", len(sorted_sites) if sorted_sites else 0, target_org_id)
        return sorted_sites  # WHY: propagate to caller

    def _display_sites_page(
        self,
        sites_data: list[dict[str, Any]],
        start_idx: int,
        end_idx: int,
        current_page: int,
        total_pages: int,
    ) -> None:
        """Print one page of sites with their 1-based index numbers."""
        for idx in range(start_idx, end_idx):
            site_name = sites_data[idx].get("name", "Unknown")
            print(f"        {idx + 1:>4}. {site_name}")
        if total_pages > 1:
            print(f"\n      Page {current_page + 1}/{total_pages}")
            print("      [n]ext page, [p]rev page, or enter selection:")

    def _handle_site_page_input(self, selection: str, current_page: int, total_pages: int) -> tuple[str, Any]:
        """Interpret site selection input and return an (action, value) tuple.

        Actions: 'quit', 'all', 'next', 'prev', 'select'.
        Value: new page index for navigation, or original selection string for 'select'.
        """
        if selection in ("q", ""):  # WHY: quit sentinel or empty -> cancel
            return "quit", None  # WHY: signal cancel
        if selection == "all":  # WHY: bulk-select shortcut
            return "all", None  # WHY: signal select-all
        nav = self._resolve_site_page_navigation(selection, current_page, total_pages)  # WHY: page nav helper
        if nav is not None:  # WHY: input was next/prev
            return nav  # WHY: propagate navigation tuple
        return "select", selection  # WHY: default -> treat as index/range selection

    def _resolve_site_page_navigation(
        self,
        selection: str,
        current_page: int,
        total_pages: int,
    ) -> tuple[str, int] | None:
        """Return a navigation action tuple for 'n'/'p' or ``None`` when not a nav command."""
        if selection == "n" and current_page < total_pages - 1:  # WHY: forward paging allowed
            return "next", current_page + 1  # WHY: advance page index
        if selection == "p" and current_page > 0:  # WHY: backward paging allowed
            return "prev", current_page - 1  # WHY: rewind page index
        return None  # WHY: not a paging command

    def _run_site_selection_loop(self, sites_data: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        """Interactively loop until user selects sites or quits."""
        logging.info("Starting site selection loop total_sites=%d", len(sites_data))  # WHY: audit entry
        page_size = 25  # WHY: fixed pagination window for menu 196 flows
        total_pages = (len(sites_data) + page_size - 1) // page_size  # WHY: ceiling division
        current_page = 0  # WHY: start at first page
        while True:  # WHY: loop until operator commits or quits
            selection = self._prompt_site_page_selection(sites_data, current_page, page_size, total_pages)
            if selection is None:  # WHY: SystemExit was caught by helper
                return None  # WHY: propagate cancel
            outcome = self._apply_site_selection_action(selection, current_page, total_pages, sites_data)
            if outcome[0] == "commit":  # WHY: helper produced a final result
                return cast(list[dict[str, Any]] | None, outcome[1])  # WHY: narrow tuple[str, Any] payload
            current_page = outcome[1]  # WHY: navigation updated the page pointer

    def _prompt_site_page_selection(
        self,
        sites_data: list[dict[str, Any]],
        current_page: int,
        page_size: int,
        total_pages: int,
    ) -> str | None:
        """Render the current page and read one operator selection token."""
        start_idx = current_page * page_size  # WHY: page start row
        end_idx = min(start_idx + page_size, len(sites_data))  # WHY: page end row bounded by list length
        self._display_sites_page(sites_data, start_idx, end_idx, current_page, total_pages)  # WHY: render
        print("\n      Selection: single '1', multiple '1,3,5', range '1-10', 'all', or 'q'\n")  # WHY: help
        try:
            return self._safe_input_fn("      Select site(s): ", context="site_multi_select").strip().lower()
        except SystemExit:  # WHY: honor ^C / EOF as cancel
            return None  # WHY: signal cancel via sentinel

    def _handle_simple_page_action(
        self,
        action: str,
        value: Any,
        sites_data: list[dict[str, Any]],
    ) -> tuple[str, Any] | None:
        """Resolve quit/all/next/prev site page actions, or return None to indicate custom selection."""
        if action == "quit":  # WHY: cancel path
            return "commit", None  # WHY: final null result
        if action == "all":  # WHY: select-all shortcut
            return "commit", sites_data  # WHY: return full site list
        if action in ("next", "prev"):  # WHY: paging navigation
            return "navigate", value  # WHY: update page pointer
        return None  # WHY: signal caller to handle explicit selection tokens

    def _apply_site_selection_action(
        self,
        selection: str,
        current_page: int,
        total_pages: int,
        sites_data: list[dict[str, Any]],
    ) -> tuple[str, Any]:
        """Route a page-selection token to a commit / navigate outcome tuple."""
        action, value = self._handle_site_page_input(selection, current_page, total_pages)  # WHY: parse
        simple = self._handle_simple_page_action(action, value, sites_data)  # WHY: quit/all/nav shortcut
        if simple is not None:  # WHY: shortcut handled the token
            return simple  # WHY: pass through routed outcome
        selected_indices = self._parse_selection_input(value, len(sites_data))  # WHY: range/index parser
        if selected_indices:  # WHY: valid explicit picks
            return "commit", [sites_data[idx] for idx in selected_indices]  # WHY: project onto site dicts
        print("      X Invalid selection - try again")  # WHY: invalid input feedback
        return "navigate", current_page  # WHY: stay on current page and re-prompt

    def _select_sites_for_org_upgrade(
        self,
        target_org_id: str,
        org_name: str,
    ) -> list[dict[str, Any]] | None:
        """Fetch sites from org and let user select which to upgrade; return picks or None."""
        global apisession
        logging.info("Selecting sites for org upgrade org=%s", target_org_id)  # WHY: audit entry
        print(f"      Fetching sites from {org_name}...")  # WHY: operator progress signal
        if apisession is None:  # WHY: guard against uninitialized session
            print("      X API session not initialized")  # WHY: operator diagnostic
            return None  # WHY: nothing to do
        sites_data = self._safe_fetch_sites_for_org(target_org_id)  # WHY: fetch with error handling
        if not sites_data:  # WHY: empty or failed fetch
            return None  # WHY: propagate cancel/failure
        print(f"      Found {len(sites_data)} site(s):\n")  # WHY: operator visibility
        result = self._run_site_selection_loop(sites_data)  # WHY: interactive picker loop
        logging.debug("Site selection resolved count=%d", len(result) if result else 0)  # WHY: audit exit
        return result  # WHY: propagate selection to caller

    def _safe_fetch_sites_for_org(self, target_org_id: str) -> list[dict[str, Any]] | None:
        """Fetch org sites with error handling; return list, empty, or None sentinel."""
        try:
            sites_data = self._fetch_and_validate_org_sites(target_org_id)  # WHY: HTTP + validation
        except Exception as e:  # WHY: broad guard for network/lib errors
            print(f"      X Error fetching sites: {e}")  # WHY: operator diagnostic
            logging.error("Failed to fetch org sites for upgrade: %s", e)  # WHY: audit failure
            return None  # WHY: signal fetch failure
        if not sites_data:  # WHY: empty roster
            print("      X Failed to retrieve sites or no sites found")  # WHY: operator diagnostic
            return None  # WHY: propagate empty as cancel
        return sites_data  # WHY: successful fetch

    def _parse_range_bounds(self, part: str) -> tuple[int, int] | None:
        """Parse a range token like '1-5' (1-based) into 0-based (start, end) or None."""
        range_parts = part.split("-")  # WHY: split into two halves
        if len(range_parts) != 2:  # WHY: reject malformed ranges
            return None  # WHY: signal parse failure
        try:
            start = int(range_parts[0].strip()) - 1  # WHY: normalize to 0-based
            end = int(range_parts[1].strip()) - 1  # WHY: normalize to 0-based
        except ValueError:
            logging.warning("Invalid range format: %s", part)  # WHY: audit malformed input
            return None  # WHY: signal parse failure
        if start > end:  # WHY: allow reversed bounds
            start, end = end, start  # WHY: normalize order
        return start, end  # WHY: bounds ready for expansion

    def _append_index_if_valid(self, idx: int, max_count: int, selected_indices: list[int]) -> None:
        """Append a 0-based index if within bounds and not already selected; log overflow diagnostic."""
        if 0 <= idx < max_count and idx not in selected_indices:  # WHY: bounds + dedupe gate
            selected_indices.append(idx)  # WHY: register valid index
        elif idx >= max_count:  # WHY: overflow diagnostic path
            print(f"      !? Index {idx + 1} out of range (max: {max_count})")  # WHY: operator hint

    def _parse_range_token(self, part: str, max_count: int, selected_indices: list[int]) -> None:
        """Parse a range token like '1-5' (1-based) and append valid 0-based indices."""
        bounds = self._parse_range_bounds(part)  # WHY: extract validated 0-based bounds
        if bounds is None:  # WHY: parse failure short-circuits
            return  # WHY: nothing to append
        start, end = bounds  # WHY: unpack for iteration
        for idx in range(start, end + 1):  # WHY: iterate inclusive range
            self._append_index_if_valid(idx, max_count, selected_indices)  # WHY: delegate bounds/dedupe check

    def _parse_single_token(self, part: str, max_count: int, selected_indices: list[int]) -> None:
        """Parse a single index token like '3' (1-based) and append 0-based index if valid."""
        try:
            idx = int(part) - 1  # WHY: normalize to 0-based
        except ValueError:
            logging.warning("Invalid index: %s", part)  # WHY: audit malformed token
            return  # WHY: nothing to append on parse failure
        self._append_index_if_valid(idx, max_count, selected_indices)  # WHY: delegate bounds/dedupe check

    def _parse_selection_input(self, user_input: str, max_count: int) -> list[int]:
        """Parse selection input into 0-based indices; supports single, csv, dash and 'through' ranges."""
        selected_indices: list[int] = []  # WHY: accumulator for parsed indices
        normalized_input = (  # WHY: unify range syntax before tokenizing
            user_input.lower().replace(" through ", "-").replace("through", "-")
        )
        parts = [part.strip() for part in normalized_input.split(",")]  # WHY: comma-separated tokens
        for part in parts:  # WHY: dispatch each token to range or single parser
            if "-" in part and not part.startswith("-"):  # WHY: detect range excluding negatives
                self._parse_range_token(part, max_count, selected_indices)  # WHY: expand into indices
            else:
                self._parse_single_token(part, max_count, selected_indices)  # WHY: append single index
        selected_indices.sort()  # WHY: return indices in ascending order
        return selected_indices

    def _display_upgrade_plan_summary(self, upgrade_plan: list[dict[str, Any]], dry_run: bool) -> None:
        """Display a summary of the planned upgrades."""
        self._print_upgrade_plan_header(dry_run)  # WHY: banner + title
        total_sites = 0  # WHY: accumulate site count across plans
        msps_seen: set[str] = set()  # WHY: unique MSP tracker for totals row
        for plan in upgrade_plan:  # WHY: iterate every org-level plan entry
            sites = plan["sites"]  # WHY: needed for both render + counter
            total_sites += len(sites)  # WHY: bump running total
            msps_seen.add(plan["msp_id"])  # WHY: register unique MSP id
            self._print_upgrade_plan_entry(plan, sites)  # WHY: render org+sites block
        self._print_upgrade_plan_totals(msps_seen, upgrade_plan, total_sites)  # WHY: totals footer

    def _print_upgrade_plan_header(self, dry_run: bool) -> None:
        """Render the upgrade plan banner and title row."""
        print("")  # WHY: visual break
        print("=" * 70)  # WHY: top divider
        print("  UPGRADE PLAN SUMMARY" + (" (DRY-RUN)" if dry_run else ""))  # WHY: title + mode
        print("=" * 70)  # WHY: bottom divider
        print("")  # WHY: spacing before first plan entry

    def _print_upgrade_plan_entry(self, plan: dict[str, Any], sites: list[dict[str, Any]]) -> None:
        """Render one org-level plan entry with its first five sites."""
        print(f"  MSP: {plan['msp_name']}")  # WHY: identify MSP scope
        print(f"    Organization: {plan['org_name']}")  # WHY: identify org
        print(f"    Sites ({len(sites)}):")  # WHY: site-count header
        for site in sites[:5]:  # WHY: preview first five sites only
            print(f"      - {site.get('name', 'Unknown')}")  # WHY: safe site name render
        if len(sites) > 5:  # WHY: elide long lists
            print(f"      ... and {len(sites) - 5} more")  # WHY: truncation hint
        print("")  # WHY: spacing between entries

    def _print_upgrade_plan_totals(
        self,
        msps_seen: set[str],
        upgrade_plan: list[dict[str, Any]],
        total_sites: int,
    ) -> None:
        """Render the totals footer for the upgrade plan summary."""
        print("-" * 70)  # WHY: totals divider
        print("  TOTALS:")  # WHY: totals label
        print(f"    MSPs: {len(msps_seen)}")  # WHY: unique MSP count
        print(f"    Organizations: {len(upgrade_plan)}")  # WHY: org row count
        print(f"    Sites: {total_sites}")  # WHY: site aggregate
        print("-" * 70)  # WHY: closing divider

    def _execute_msp_upgrade_plan(
        self,
        upgrade_plan: list[dict[str, Any]],
        dry_run: bool,
    ) -> list[dict[str, Any]]:
        """Execute the upgrade plan across all orgs and sites."""
        global org_id  # WHY: MSP flow mutates module scope for helper reuse
        logging.info("Executing MSP plan across %d orgs (dry_run=%s)", len(upgrade_plan), dry_run)  # WHY: audit
        results: list[dict[str, Any]] = []  # WHY: accumulator for per-org status records
        original_org_id = org_id  # WHY: snapshot to restore module state after loop
        stopped = self._run_msp_upgrade_loop(upgrade_plan, dry_run, results)  # WHY: delegate iteration to helper
        org_id = original_org_id  # WHY: always restore module org scope
        logging.debug("MSP upgrade plan complete stopped=%s results=%d", stopped, len(results))  # WHY: trace exit
        return results  # WHY: caller renders summary from accumulated records

    def _run_msp_upgrade_loop(  # WHY: iterate plan and drive per-org execution + interrupt policy
        self,
        upgrade_plan: list[dict[str, Any]],
        dry_run: bool,
        results: list[dict[str, Any]],
    ) -> bool:
        """Iterate the upgrade plan; return True if the user requested stop."""
        total_items = len(upgrade_plan)  # WHY: used for progress header rendering
        for idx, plan in enumerate(upgrade_plan, 1):  # WHY: 1-based counter matches user-facing display
            self._present_msp_plan_header(idx, total_items, plan)  # WHY: print banner before work begins
            outcome = self._execute_msp_single_org(plan, dry_run)  # WHY: run one org and classify outcome
            results.append(outcome["record"])  # WHY: persist per-org record regardless of status
            if outcome["stop"]:  # WHY: interrupted user declined continuation
                return True  # WHY: signal caller to abort remaining plan entries
        return False  # WHY: normal end-of-plan without user abort

    def _present_msp_plan_header(  # WHY: render the per-org banner in one place
        self,
        idx: int,
        total: int,
        plan: dict[str, Any],
    ) -> None:
        """Emit the banner block that announces the org about to be upgraded."""
        print("")  # WHY: blank line separator between org sections
        print(f"  [{idx}/{total}] Processing: {plan['org_name']} (MSP: {plan['msp_name']})")  # WHY: progress line
        print(f"      Organization ID: {plan['org_id']}")  # WHY: expose target org UUID for auditors
        print(f"      Sites to upgrade: {len(plan['sites'])}")  # WHY: expected work size
        print("-" * 70)  # WHY: visual divider matches other summary blocks

    def _execute_msp_single_org(  # WHY: run one org's upgrade and classify success/interrupt/failure
        self,
        plan: dict[str, Any],
        dry_run: bool,
    ) -> dict[str, Any]:
        """Execute a single org upgrade; return record + stop flag."""
        global org_id  # WHY: helper mutates module scope for underlying upgrader
        target_org_id = plan["org_id"]  # WHY: pin target once for consistent record fields
        target_org_name = plan["org_name"]  # WHY: rendered in prompts and logs
        try:
            org_id = target_org_id  # WHY: point global helpers at the target org
            self._run_msp_bulk_upgrader(target_org_id, plan["sites"], dry_run)  # WHY: delegate to bulk upgrader
            return {"record": self._make_msp_record(plan, "completed", dry_run), "stop": False}  # WHY: happy path
        except KeyboardInterrupt:  # WHY: user pressed Ctrl-C mid-flow
            return self._handle_msp_interrupt(plan, target_org_name, dry_run)  # WHY: prompt continuation policy
        except Exception as exc:  # noqa: BLE001  # WHY: surface any downstream failure without abort
            return self._handle_msp_failure(plan, target_org_name, exc, dry_run)  # WHY: capture error record

    def _run_msp_bulk_upgrader(  # WHY: construct + execute the pre-selected-sites bulk upgrader
        self,
        target_org_id: str,
        sites: list[dict[str, Any]],
        dry_run: bool,
    ) -> None:
        """Invoke BulkAPFirmwareUpgrader for the given org + site list."""
        sites_for_upgrader = [  # WHY: normalize site shape expected by BulkAPFirmwareUpgrader
            {"id": s["id"], "name": s.get("name", "Unknown")} for s in sites
        ]
        main_module = sys.modules.get("__main__") or sys.modules.get("MistHelper")  # WHY: locate host module
        if main_module is None:  # WHY: guard against missing host (e.g., isolated unit test)
            logging.debug("MSP upgrade skipped: MistHelper host module not loaded")  # WHY: trace skip
            return  # WHY: no-op when host absent, caller records completion
        bulk_upgrader_cls = main_module.BulkAPFirmwareUpgrader  # WHY: lazy attr avoids circular import
        upgrader = bulk_upgrader_cls(target_org_id, sites_for_upgrader, dry_run=dry_run)  # WHY: construct
        upgrader.execute()  # WHY: run the actual bulk upgrade
        logging.info("MSP upgrade %s for org id %s", "simulated" if dry_run else "completed", target_org_id)  # WHY: log

    def _handle_msp_interrupt(  # WHY: format interrupted record + confirm continuation
        self,
        plan: dict[str, Any],
        target_org_name: str,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Handle Ctrl-C during a single-org upgrade."""
        print(f"\n  Upgrade interrupted at organization: {target_org_name}")  # WHY: notify operator
        record = self._make_msp_record(plan, "interrupted", dry_run)  # WHY: preserve run history
        try:  # WHY: safe_input can raise SystemExit under EOF policy
            answer = (
                self._safe_input_fn(  # WHY: prompt operator for continuation
                    "  Continue with remaining orgs? (y/N): ",
                    context="msp_continue",
                )
                .strip()
                .lower()
            )  # WHY: normalize for comparison
        except SystemExit:  # WHY: treat EOF as stop
            return {"record": record, "stop": True}  # WHY: end plan run
        if answer != "y":  # WHY: any non-y answer aborts remaining plan
            print("  Stopping MSP upgrade process")  # WHY: user-visible confirmation
            return {"record": record, "stop": True}  # WHY: signal loop exit
        return {"record": record, "stop": False}  # WHY: continue with next org

    def _handle_msp_failure(  # WHY: format failure record with error message
        self,
        plan: dict[str, Any],
        target_org_name: str,
        exc: Exception,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Convert an exception into a failure record."""
        error_msg = str(exc)  # WHY: capture textual error for the record
        print(f"  X Error upgrading {target_org_name}: {error_msg}")  # WHY: surface to operator
        logging.error("MSP upgrade failed for org %s: %s", target_org_name, exc)  # WHY: audit failure
        record = self._make_msp_record(plan, "failed", dry_run, error=error_msg)  # WHY: capture with error field
        return {"record": record, "stop": False}  # WHY: single-org failure never aborts full plan

    def _make_msp_record(  # WHY: single builder eliminates 4x duplicated dict literals
        self,
        plan: dict[str, Any],
        status: str,
        dry_run: bool,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Build a status record for one org in the MSP plan."""
        record: dict[str, Any] = {  # WHY: shared field set across completed/failed/interrupted
            "msp_name": plan["msp_name"],
            "org_id": plan["org_id"],
            "org_name": plan["org_name"],
            "sites_count": len(plan["sites"]),
            "status": status,
            "result": None,
            "dry_run": dry_run,
        }
        if error is not None:  # WHY: only failed records carry an error field
            record["error"] = error  # WHY: preserve diagnostic text for later reporting
        return record  # WHY: caller appends to results list

    def _split_results_by_status(
        self, results: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Split upgrade results into completed, failed, and interrupted lists."""
        buckets: dict[str, list[dict[str, Any]]] = {  # WHY: single-pass bucket lookup
            "completed": [],  # WHY: successful org runs
            "failed": [],  # WHY: exception-terminated org runs
            "interrupted": [],  # WHY: operator-cancelled org runs
        }
        for record in results:  # WHY: single pass over results list
            buckets.setdefault(record["status"], []).append(record)  # WHY: dispatch by status key
        return buckets["completed"], buckets["failed"], buckets["interrupted"]  # WHY: fixed-order triple

    def _print_completed_orgs_detail(self, completed: list[dict[str, Any]]) -> None:
        """Print details for completed organizations."""
        if not completed:  # WHY: skip empty section quickly
            return
        print("  Completed organizations:")  # WHY: section header for reviewer scanning summary
        for result in completed:  # WHY: iterate per-org upgrade result records
            status_prefix = "(DRY-RUN) " if result.get("dry_run") else ""  # WHY: distinguish dry-run rows
            print(f"    + {status_prefix}{result['org_name']} ({result.get('sites_count', 0)} sites)")

    def _print_failed_orgs_detail(self, failed: list[dict[str, Any]]) -> None:
        """Print details for failed organizations."""
        if not failed:  # WHY: skip empty section quickly
            return
        print("\n  Failed organizations:")  # WHY: section header for reviewer scanning summary
        for record in failed:  # WHY: iterate per-org failure records
            print(f"    X {record['org_name']}: {record.get('error', 'Unknown error')}")

    def _print_interrupted_orgs_detail(self, interrupted: list[dict[str, Any]]) -> None:
        """Print details for interrupted organizations."""
        if not interrupted:  # WHY: skip empty section quickly
            return
        print("\n  Interrupted organizations:")  # WHY: section header for reviewer scanning summary
        for report_row in interrupted:  # WHY: iterate interrupted org rows for reporting
            print(f"    ! {report_row['org_name']}")

    def _print_msp_upgrade_summary(
        self,
        results: list[dict[str, Any]],
        dry_run: bool = False,
    ) -> None:
        """Print summary of MSP multi-org upgrade results."""
        print(f"\n{'=' * 70}\n  MSP UPGRADE SUMMARY{' (DRY-RUN)' if dry_run else ''}\n{'=' * 70}\n")
        completed, failed, interrupted = self._split_results_by_status(results)
        self._print_msp_summary_totals(results, completed, failed, interrupted)  # WHY: totals block
        self._print_completed_orgs_detail(completed)
        self._print_failed_orgs_detail(failed)
        self._print_interrupted_orgs_detail(interrupted)
        self._log_msp_summary_totals(dry_run, completed, failed, interrupted)  # WHY: audit totals

    def _print_msp_summary_totals(
        self,
        results: list[dict[str, Any]],
        completed: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        interrupted: list[dict[str, Any]],
    ) -> None:
        """Print the aggregate totals block for the MSP upgrade summary."""
        total_sites = sum(row.get("sites_count", 0) for row in results)  # WHY: aggregate sites processed
        print(f"  Total organizations processed: {len(results)}")
        print(f"  Total sites targeted: {total_sites}")
        print(f"    + Completed: {len(completed)}")
        print(f"    X Failed: {len(failed)}")
        print(f"    ! Interrupted: {len(interrupted)}\n")

    def _log_msp_summary_totals(
        self,
        dry_run: bool,
        completed: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        interrupted: list[dict[str, Any]],
    ) -> None:
        """Emit the audit log line for the MSP upgrade summary totals."""
        mode_str = "DRY-RUN " if dry_run else ""  # WHY: distinguish dry-run in audit trail
        logging.info(
            "MSP %supgrade summary: %s completed, %s failed, %s interrupted",
            mode_str,
            len(completed),
            len(failed),
            len(interrupted),
        )

    def _select_msp_for_upgrade(self) -> dict[str, Any] | None:
        """DEPRECATED: Use _select_msps_for_upgrade() instead. Kept for compatibility."""
        msps = self._select_msps_for_upgrade()  # WHY: delegate to typed multi-selector
        return msps[0] if msps and len(msps) == 1 else None  # WHY: preserve single-MSP semantics

    def _bulk_upgrade_ap_firmware_by_site(
        self,
        sites_to_upgrade_override: list[dict[str, Any]] | None = None,
    ) -> None:
        """Bulk upgrade AP firmware for selected site(s) via CSV, interactive picker, or template override."""
        global apisession  # WHY: helpers below read module-level session state
        original_apisession = apisession  # WHY: snapshot to restore after upgrade
        apisession = self.apisession  # WHY: install instance session for helper use
        try:
            self._execute_bulk_upgrade(sites_to_upgrade_override)  # WHY: delegate to void executor
        finally:
            apisession = original_apisession  # WHY: always restore module state

    def _execute_bulk_upgrade(
        self,
        sites_to_upgrade_override: list[dict[str, Any]] | None,
    ) -> None:
        """Execute the bulk firmware upgrade using BulkAPFirmwareUpgrader class."""
        import sys as _sys

        _main = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")
        if _main is None:
            return
        BulkAPFirmwareUpgrader = _main.BulkAPFirmwareUpgrader  # lazy import avoids circular
        # Check for dry_run flag from global args
        dry_run = getattr(getattr(_main, "args", None), "dry_run", False)
        upgrader = BulkAPFirmwareUpgrader(self.org_id, sites_to_upgrade_override, dry_run=dry_run)
        upgrader.execute()

    def _execute_status_check(self, scope_choice: str, site_filter: str | None) -> None:
        """Execute the firmware status check using the co-located FirmwareUpgradeStatusChecker."""
        logging.info(
            "Dispatching status check (scope=%s, site_filter=%s)", scope_choice, site_filter
        )  # WHY: audit trail before wiring module globals
        global apisession  # WHY: co-located checker reads bare apisession at module scope
        original_apisession = apisession  # WHY: preserve caller's session for restoration
        apisession = self.apisession  # WHY: bind this FirmwareManager's session for the checker
        try:  # WHY: guarantee restoration on any exception path
            FirmwareUpgradeStatusChecker(scope_choice, site_filter).check()  # WHY: run the co-located workflow
        finally:  # WHY: always restore even if the checker raises
            apisession = original_apisession  # WHY: leave module globals as we found them
        logging.debug("Status check dispatch complete")  # WHY: audit trail after restoration

    # ===============================================================================
    # SWITCH FIRMWARE UPGRADE METHODS
    # ===============================================================================

    def execute_switch_firmware_upgrade_with_mode_selection(self) -> None:
        """Main entry point for switch firmware upgrades with mode selection.

        Presents site-based vs template-based choice; delegates to the picked flow.
        """
        logging.info("Starting switch firmware upgrade with mode selection")  # WHY: audit entry
        self._print_switch_upgrade_banner()  # WHY: destructive-op warnings
        self._print_switch_mode_menu()  # WHY: mode-choice UI
        mode_choice = self._prompt_switch_upgrade_mode()  # WHY: read operator selection
        if mode_choice is None:  # WHY: EOF/interrupt cancel
            return None  # WHY: honour operator cancel
        self._dispatch_switch_upgrade_mode(mode_choice)  # WHY: route to chosen flow
        logging.debug("Switch upgrade mode dispatch done choice=%s", mode_choice)  # WHY: trace exit
        return None  # WHY: unified void return preserves prior contract

    def _print_switch_upgrade_banner(self) -> None:
        """Print the destructive-operation banner for switch firmware upgrades."""
        print(" Advanced Switch Firmware Upgrade")  # WHY: page title
        print("=" * 60)  # WHY: title underline
        print("")  # WHY: spacing
        print("  DESTRUCTIVE OPERATION WARNING")  # WHY: attention header
        print("  ===========================")  # WHY: header underline
        print("  Switch firmware upgrades will:")  # WHY: preamble
        print("  X  Reboot switches during upgrade process")  # WHY: risk item 1
        print("  X  Potentially disrupt network connectivity")  # WHY: risk item 2
        print("  X  Affect production traffic flow")  # WHY: risk item 3
        print("  X  Require recovery snapshots for Junos devices")  # WHY: risk item 4
        print("")  # WHY: spacing before menu

    def _print_switch_mode_menu(self) -> None:
        """Print the mode-selection menu (1=site, 2=template)."""
        print("  Select upgrade mode:")  # WHY: menu heading
        print("   [1] By Site - Upgrade specific sites (individual site selection)")  # WHY: site option
        print("   [2] By Gateway Template - Upgrade all sites assigned to a selected Gateway Template")  # tmpl

    def _prompt_switch_upgrade_mode(self) -> str | None:
        """Loop until operator enters a valid mode ('1' or '2'); return None on EOF."""
        while True:  # WHY: retry until valid or cancel
            try:  # WHY: catch EOF/interrupt
                mode_choice = self._safe_input_fn("\n  Select mode (1-2): ", context="firmware_manager").strip()
            except (EOFError, KeyboardInterrupt):  # WHY: SSH/container safe exit
                print("\n  Operation cancelled by user.")  # WHY: operator feedback
                logging.info("Switch firmware upgrade cancelled (EOF/interrupt)")  # WHY: audit cancel
                return None  # WHY: signal cancel to caller
            if mode_choice in ("1", "2"):  # WHY: only two legal choices
                return mode_choice  # WHY: hand valid token to dispatcher
            print("  Invalid selection. Please choose 1 or 2.")  # WHY: operator retry hint
            logging.debug("Invalid mode selection: %s", mode_choice)  # WHY: audit invalid input

    def _dispatch_switch_upgrade_mode(self, mode_choice: str) -> None:
        """Route the validated mode choice to the appropriate switch upgrade flow."""
        if mode_choice == "1":  # WHY: site-based branch
            logging.info("User selected site-based switch upgrade mode")  # WHY: audit selection
            print("\n  Site-based switch upgrade mode selected")  # WHY: operator confirmation
            self._bulk_upgrade_switch_firmware_by_site()  # WHY: run site-based flow
            return  # WHY: single-path exit for mode 1
        logging.info("User selected template-based switch upgrade mode")  # WHY: template-based branch
        print("\n  Template-based switch upgrade mode selected")  # WHY: operator confirmation
        self._upgrade_switch_firmware_by_gateway_template()  # WHY: run template-based flow

    def _bulk_upgrade_switch_firmware_by_site(
        self, sites_to_upgrade_override: list[dict[str, Any]] | None = None
    ) -> None:
        """Bulk switch firmware upgrade for selected site(s) via interactive picker or template override."""
        logging.info("Starting bulk switch firmware upgrade by site...")  # WHY: audit entry
        logging.debug("FirmwareManager._bulk_upgrade_switch_firmware_by_site() initiated")  # WHY: trace call
        import sys as _sys  # noqa: PLC0415  # WHY: lazy import to avoid circular deps

        _main = _sys.modules.get("__main__") or _sys.modules.get("MistHelper")  # WHY: locate entry module
        if _main is None:  # WHY: guard when neither module surface is present
            return  # WHY: cannot proceed without the upgrader class
        BulkSwitchFirmwareUpgrader = _main.BulkSwitchFirmwareUpgrader  # WHY: lazy attribute access
        BulkSwitchFirmwareUpgrader(self.org_id, sites_to_upgrade_override).execute()  # WHY: run upgrade flow

    def _upgrade_switch_firmware_by_gateway_template(self) -> None:
        """Advanced switch firmware upgrade organized by Gateway Template assignment.

        Reuses shared template infrastructure (CSV freshness + template->sites
        mapping) then dispatches to the switch-specific bulk upgrade. Destructive:
        callers must have obtained explicit operator confirmation upstream.
        """
        logging.info("Starting template-based switch firmware upgrade for org %s", self.org_id)  # WHY: audit entry
        self._print_switch_template_banner()  # WHY: mandatory operator hazard banner
        template_sites_mapping = self._prepare_template_upgrade("switch")  # WHY: shared freshness + mapping
        if template_sites_mapping is None:  # WHY: no templates or no assignments
            logging.debug("Switch template upgrade aborted - no template-site assignments")  # WHY: trace early exit
            return None  # WHY: preserve pre-refactor cancel behavior
        template_name_to_id, sites_mapping = template_sites_mapping  # WHY: unpack prep tuple
        selection = self._select_template_and_sites(template_name_to_id, sites_mapping)  # WHY: prompt operator
        if selection is None:  # WHY: operator declined template picker
            logging.debug("Switch template upgrade cancelled at template prompt")  # WHY: trace decline
            return None  # WHY: preserve pre-refactor cancel behavior
        selected_template_name, sites_to_upgrade = selection  # WHY: unpack picker result
        self._execute_template_based_switch_upgrade(sites_to_upgrade, selected_template_name)  # WHY: dispatch
        logging.debug("Switch tmpl upgrade done template=%s sites=%d", selected_template_name, len(sites_to_upgrade))
        return None  # WHY: explicit None return preserves prior contract

    def _print_switch_template_banner(self) -> None:
        """Emit the switch-template upgrade banner (operator hazard header)."""
        logging.debug("Rendering switch template upgrade banner")  # WHY: trace UI-only helper entry
        print(" Advanced Switch Firmware Upgrade by Gateway Template")  # WHY: menu title for operator
        print("=" * 70)  # WHY: separator aligned with pre-refactor banner width

    def _execute_template_based_switch_upgrade(
        self, sites_to_upgrade: list[dict[str, Any]], selected_template_name: str
    ) -> None:
        """Execute the template-based switch upgrade with the existing switch implementation."""
        print(f"  Proceeding with switch firmware upgrade for template: {selected_template_name}")
        print(f"  Target sites: {len(sites_to_upgrade)}")

        # Use the switch-specific bulk upgrade implementation
        self._bulk_upgrade_switch_firmware_by_site(sites_to_upgrade)  # WHY: run switch-specific bulk flow

    # ===============================================================================
    # SSR FIRMWARE UPGRADE METHODS
    # ===============================================================================

    def execute_ssr_firmware_upgrade_with_mode_selection(self) -> dict[str, Any] | None:
        """Main entry point for SSR firmware upgrades with mode selection."""
        logging.info("SSR upgrade mode-selection menu entered")  # WHY: audit destructive entrypoint
        self._present_ssr_upgrade_warning()  # WHY: mandatory operator hazard banner before any input
        mode_choice = self._prompt_ssr_mode_selection()  # WHY: obtain validated 1|2|None mode
        if mode_choice is None:  # WHY: EOF/interrupt -> abort without dispatch
            logging.debug("SSR upgrade cancelled at mode prompt")  # WHY: trace early exit
            return None  # WHY: preserve pre-refactor cancel behavior
        result = self._dispatch_ssr_upgrade_mode(mode_choice)  # WHY: route to site or template handler
        logging.debug("SSR upgrade dispatch complete mode=%s", mode_choice)  # WHY: trace exit
        return result  # WHY: propagate handler return to caller

    def _present_ssr_upgrade_warning(self) -> None:
        """Emit the destructive-SSR-upgrade warning banner and mode-selection prompt."""
        logging.warning("Menu #100 DESTRUCTIVE: SSR firmware upgrade with mode selection started")  # WHY: audit
        logging.debug("FirmwareManager.execute_ssr_firmware_upgrade_with_mode_selection() initiated")  # WHY: trace
        self._print_ssr_hazards_block()  # WHY: banner + hazards output extracted for length compliance
        self._print_ssr_precautions_block()  # WHY: precautions + mode-selector output extracted

    def _print_ssr_hazards_block(self) -> None:
        """Print the SSR upgrade banner title and hazard list."""
        logging.debug("Rendering SSR upgrade hazards block")  # WHY: trace banner render
        print(" Advanced SSR Firmware Upgrade")  # WHY: banner title for operator context
        print("=" * 60)  # WHY: visual separator between banner and body
        print("")  # WHY: blank spacer for readability
        print("  CRITICAL ROUTING INFRASTRUCTURE WARNING")  # WHY: hazard header
        print("  ======================================")  # WHY: underline hazard header
        print("  SSR firmware upgrades will:")  # WHY: introduce impact list
        print("  X  Reboot Session Smart Routers")  # WHY: reboot impact disclosure
        print("  X  Disrupt WAN and SD-WAN connectivity")  # WHY: connectivity impact disclosure
        print("  X  Affect branch office connectivity")  # WHY: branch impact disclosure
        print("  X  Impact tunnel establishment and failover")  # WHY: tunnel impact disclosure
        print("  X  Require careful HA pair coordination")  # WHY: HA coordination hint
        print("  X  Potentially cause extended outages")  # WHY: outage disclosure

    def _print_ssr_precautions_block(self) -> None:
        """Print the SSR upgrade precautions list and mode-selector menu."""
        logging.debug("Rendering SSR upgrade precautions block")  # WHY: trace banner render
        print("")  # WHY: blank spacer between hazards and precautions
        print("  RECOMMENDED PRECAUTIONS:")  # WHY: introduce precautions list
        print("  X  Schedule maintenance windows")  # WHY: maintenance guidance
        print("  X  Verify backup connectivity paths")  # WHY: rollback path guidance
        print("  X  Coordinate with network operations")  # WHY: coordination guidance
        print("  X  Monitor upgrade progress closely")  # WHY: monitoring guidance
        print("")  # WHY: blank spacer before mode selector
        print("  Select upgrade mode:")  # WHY: mode-selector introduction
        print("   [1] By Site - Upgrade specific sites (individual site selection)")  # WHY: mode 1 description
        print("   [2] By Gateway Template - Upgrade all sites assigned to a selected Gateway Template")  # WHY: mode 2

    def _prompt_ssr_mode_selection(self) -> str | None:
        """Prompt for SSR upgrade mode until valid or cancelled; returns "1", "2", or None."""
        logging.info("Prompting SSR upgrade mode selection")  # WHY: trace prompt entry
        while True:  # WHY: retry until valid input or EOF/interrupt
            try:  # WHY: catch shell/SSH interrupt for safe exit
                mode_choice = self._safe_input_fn("\n  Select mode (1-2): ", context="firmware_manager").strip()
            except (EOFError, KeyboardInterrupt):  # WHY: SSH/container-safe cancel path
                print("\n  Operation cancelled by user.")  # WHY: user-visible cancel confirmation
                logging.info("SSR upgrade cancelled (EOF/interrupt) - SSH-safe exit")  # WHY: audit
                return None  # WHY: sentinel signals cancellation to orchestrator
            if mode_choice in ("1", "2"):  # WHY: accept only defined modes
                logging.debug("SSR mode selected: %s", mode_choice)  # WHY: trace selection
                return mode_choice  # WHY: pass validated choice back
            print("  Invalid selection. Please choose 1 or 2.")  # WHY: user-visible reprompt reason
            logging.debug("Invalid mode selection: %s", mode_choice)  # WHY: trace invalid input

    def _dispatch_ssr_upgrade_mode(self, mode_choice: str) -> dict[str, Any] | None:
        """Dispatch validated SSR upgrade mode to the matching handler."""
        logging.info("Dispatching SSR upgrade mode=%s", mode_choice)  # WHY: audit dispatch selection
        result: dict[str, Any] | None  # WHY: unify return type across both branches
        if mode_choice == "1":  # WHY: site-based path
            logging.info("User selected site-based SSR upgrade mode")  # WHY: preserve pre-refactor audit line
            print("\n  Site-based SSR upgrade mode selected")  # WHY: operator visible mode confirmation
            result = self._bulk_upgrade_ssr_firmware_by_site()  # WHY: run site flow
        else:  # WHY: mode_choice guaranteed "2" by _prompt_ssr_mode_selection
            logging.info("User selected template-based SSR upgrade mode")  # WHY: preserve pre-refactor audit line
            print("\n  Template-based SSR upgrade mode selected")  # WHY: operator visible mode confirmation
            self._upgrade_ssr_firmware_by_gateway_template()  # WHY: template flow (no meaningful return)
            result = None  # WHY: template flow returns None, uniform across dispatch
        logging.debug("SSR mode dispatch complete mode=%s", mode_choice)  # WHY: trace exit
        return result  # WHY: return handler result to orchestrator

    def _validate_org_for_ssr_upgrade(self) -> tuple[str, dict[str, Any] | None]:
        """Validate organization access for SSR upgrade.

        Returns:
            tuple: (org_name, error_dict or None)
        """
        logger = logging.getLogger(__name__)  # WHY: local logger for validation errors
        print("\n-> Validating organization access...")  # WHY: user feedback pre-API
        try:
            org_info = mistapi.api.v1.orgs.orgs.getOrg(self.apisession, self.org_id)  # WHY: fetch org record
            if org_info.status_code != 200:  # WHY: guard non-success
                print(f"X  Error accessing organization: {org_info.status_code}")  # WHY: operator hint
                logger.error("Failed to access organization %s: %s", self.org_id, org_info.status_code)  # WHY: audit
                return "", {"error": "Organization access failed"}  # WHY: propagate error envelope
            org_name = org_info.data.get("name", "Unknown")  # WHY: capture org display name
            print(f"!? Organization: {org_name}")  # WHY: confirm to operator
            logger.debug("Organization validated: %s", org_name)  # WHY: audit success
            return org_name, None  # WHY: signal success upstream
        except Exception as e:
            print(f"X  Error validating organization: {str(e)}")  # WHY: user-facing error
            logger.error("Organization validation failed: %s", str(e))  # WHY: structured audit
            return "", {"error": f"Organization validation error: {str(e)}"}  # WHY: propagate error envelope

    def _prompt_ssr_site_selection(
        self, all_sites: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Present site list and prompt user for selection.

        Returns:
            tuple: (selected_sites list, error_dict or None)
        """
        print("\nAvailable sites:")  # WHY: section header
        for index, site in enumerate(all_sites, 1):  # WHY: emit numbered site listing
            site_line = f"{index:3}. {site.get('name', 'Unnamed')} (ID: {site.get('id', 'Unknown')})"  # WHY: build row
            print(site_line)  # WHY: emit line item
        print("\nSite selection options:\nA. All sites\nS. Select specific sites\nC. Cancel operation")  # WHY: menu
        raw_choice = self._safe_input_fn("\nEnter your choice (A/S/C): ", context="firmware_manager")  # WHY: prompt
        choice = raw_choice.strip().upper()  # WHY: normalize casing
        if choice == "C":  # WHY: cancel branch
            print("-> Operation cancelled by user")  # WHY: user feedback
            return [], {"cancelled": True}  # WHY: signal cancellation
        if choice == "A":  # WHY: bulk-select branch
            print(f"-> Selected all {len(all_sites)} sites")  # WHY: user feedback
            return all_sites, None  # WHY: propagate full list
        if choice == "S":  # WHY: interactive-picker branch
            return self._parse_ssr_site_selection(all_sites)  # WHY: delegate to picker
        print("X  Invalid selection")  # WHY: catch-all bad input
        return [], {"error": "Invalid selection"}  # WHY: propagate error envelope

    def _parse_ssr_site_selection(
        self, all_sites: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Parse site index/range input for SSR upgrade.

        Returns:
            tuple: (selected_sites list, error_dict or None)
        """
        logging.info("Parsing SSR site selection sites=%d", len(all_sites))  # WHY: entry audit
        print("\nEnter site numbers (comma-separated) or ranges (e.g., 1-5):")  # WHY: instruction banner
        site_input = self._safe_input_fn("Sites: ", context="firmware_manager").strip()  # WHY: injected prompt
        try:
            selected_sites = self._resolve_ssr_site_tokens(site_input, all_sites)  # WHY: token dispatch
        except Exception as e:  # WHY: catch parse/index errors uniformly
            print(f"X  Invalid site selection: {str(e)}")  # WHY: user feedback
            logging.warning("Invalid SSR site selection: %s", e)  # WHY: audit failure
            return [], {"error": "Invalid site selection"}  # WHY: signal error to caller
        print(f"-> Selected {len(selected_sites)} sites")  # WHY: confirmation line
        logging.debug("Resolved SSR site selection count=%d", len(selected_sites))  # WHY: exit audit
        return selected_sites, None  # WHY: success path

    def _resolve_ssr_site_tokens(self, site_input: str, all_sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resolve a comma-separated tokens string into a list of site dicts."""
        selected_sites: list[dict[str, Any]] = []  # WHY: accumulate resolved rows
        for part in site_input.split(","):  # WHY: comma-separated tokens
            token = part.strip()  # WHY: normalize whitespace
            if not token:  # WHY: skip empty tokens
                continue  # WHY: no-op on blank
            self._extend_sites_from_token(token, all_sites, selected_sites)  # WHY: dispatch per-token
        return selected_sites  # WHY: hand back accumulated list

    def _extend_sites_from_token(
        self, token: str, all_sites: list[dict[str, Any]], selected_sites: list[dict[str, Any]]
    ) -> None:
        """Append resolved site rows for a single index-or-range token."""
        if "-" not in token:  # WHY: single-index token
            idx = int(token) - 1  # WHY: 0-based index
            if 0 <= idx < len(all_sites):  # WHY: range guard
                selected_sites.append(all_sites[idx])  # WHY: keep site
            return  # WHY: single-index path done
        start, end = map(int, token.split("-"))  # WHY: range endpoints
        for idx in range(start - 1, end):  # WHY: inclusive of end
            if 0 <= idx < len(all_sites):  # WHY: range guard
                selected_sites.append(all_sites[idx])  # WHY: keep site

    def _select_ssr_sites_for_upgrade(
        self, sites_to_upgrade_override: list[dict[str, Any]] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Select sites for SSR upgrade operation.

        Returns:
            tuple: (selected_sites list, error_dict or None)
        """
        logger = logging.getLogger(__name__)  # WHY: local logger for site discovery errors
        if sites_to_upgrade_override:  # WHY: caller supplied preselected list
            print(f"-> Using provided site list: {len(sites_to_upgrade_override)} sites")  # WHY: audit hint
            return sites_to_upgrade_override, None  # WHY: skip discovery
        try:
            print("\n-> Discovering available sites...")  # WHY: user feedback pre-API
            sites_response = mistapi.api.v1.orgs.sites.listOrgSites(self.apisession, self.org_id)  # WHY: list sites
            if sites_response.status_code != 200:  # WHY: guard non-success
                print(f"X  Error retrieving sites: {sites_response.status_code}")  # WHY: operator hint
                return [], {"error": "Failed to retrieve sites"}  # WHY: propagate failure envelope
            all_sites = sites_response.data  # WHY: capture site list
            print(f"!? Found {len(all_sites)} total sites")  # WHY: report discovery count
            return self._prompt_ssr_site_selection(all_sites)  # WHY: delegate to interactive picker
        except Exception as e:
            print(f"X  Error during site discovery: {str(e)}")  # WHY: user-facing error
            logger.error("Site discovery failed: %s", str(e))  # WHY: structured audit
            return [], {"error": f"Site discovery error: {str(e)}"}  # WHY: propagate error envelope

    def _select_ssr_upgrade_strategy(self) -> str:
        """Interactive selection of SSR upgrade strategy.

        Returns:
            str: upgrade strategy ('serial' or 'big_bang')
        """
        print("\nUpgrade Strategy Options:")  # WHY: menu header
        print("1. Serial   - Upgrade SSRs one at a time (safer, longer downtime window)")  # WHY: option 1
        print("2. Big Bang  - Upgrade all SSRs simultaneously (faster, higher risk)")  # WHY: option 2
        while True:  # WHY: retry loop until valid selection
            strategy_choice = self._safe_input_fn(
                "\nSelect upgrade strategy (1-2): ", context="firmware_manager"
            ).strip()  # WHY: normalize input
            if strategy_choice == "1":  # WHY: serial branch
                print("-> Selected strategy: serial")  # WHY: user feedback
                return "serial"  # WHY: propagate strategy id
            if strategy_choice == "2":  # WHY: big-bang branch
                print("!? WARNING: Big bang strategy will upgrade all SSRs simultaneously")  # WHY: safety warning
                print("   This may cause widespread WAN connectivity disruption")  # WHY: elaborate risk
                return "big_bang"  # WHY: propagate strategy id
            print("X  Please enter 1 or 2")  # WHY: catch-all bad input

    def _select_ssr_reboot_timing(self) -> bool:
        """Interactive selection of SSR reboot timing.

        Returns:
            bool: True for auto reboot, False for manual reboot
        """
        print("\nReboot Timing Options:")  # WHY: menu header
        print("1. Automatic - Reboot immediately after firmware download (recommended)")  # WHY: option 1
        print("2. Manual    - Download firmware only, manual reboot required later")  # WHY: option 2
        while True:  # WHY: retry until valid selection
            choice = self._safe_input_fn("\nReboot timing? (1-2): ", context="firmware_manager").strip()  # WHY: prompt
            if choice == "1":  # WHY: auto-reboot branch
                return True  # WHY: propagate auto-reboot flag
            if choice == "2":  # WHY: manual-reboot branch
                print("!? WARNING: SSRs require manual reboot to activate new firmware")  # WHY: safety warning
                print("   New firmware will not be operational until manual reboot")  # WHY: elaborate consequence
                return False  # WHY: propagate manual-reboot flag
            print("X  Please enter 1 or 2")  # WHY: catch-all bad input

    def _select_ssr_firmware_channel(self) -> str:
        """Interactive selection of SSR firmware channel.

        Returns:
            str: firmware channel ('stable', 'beta', or 'alpha')
        """
        print("\nFirmware Channel Options:")  # WHY: menu header
        print("1. stable - Production-ready releases (recommended)")  # WHY: option 1
        print("2. beta   - Pre-release versions for testing")  # WHY: option 2
        print("3. alpha  - Development versions (not recommended for production)")  # WHY: option 3
        while True:  # WHY: retry until valid selection
            raw_choice = self._safe_input_fn(  # WHY: prompt for channel selection
                "\nSelect firmware channel (1-3): ",
                context="firmware_manager",
            )
            choice = raw_choice.strip()  # WHY: strip whitespace
            if choice == "1":  # WHY: stable branch
                return "stable"  # WHY: propagate channel id
            if choice == "2":  # WHY: beta branch
                return "beta"  # WHY: propagate channel id
            if choice == "3":  # WHY: alpha branch
                print("!? WARNING: alpha channel contains development versions")  # WHY: safety warning
                print("   Not recommended for production environments")  # WHY: elaborate risk
                return "alpha"  # WHY: propagate channel id
            print("X  Please enter 1, 2, or 3")  # WHY: catch-all bad input

    def _setup_ssr_upgrade_params(self) -> dict[str, Any] | None:
        """Interactively select upgrade strategy, reboot timing, and firmware channel.

        Returns:
            dict with 'strategy', 'auto_reboot', 'channel' keys, or None if cancelled
        """
        upgrade_strategy = self._select_ssr_upgrade_strategy()
        if upgrade_strategy is None:
            return None
        auto_reboot = self._select_ssr_reboot_timing()
        firmware_channel = self._select_ssr_firmware_channel()
        return {"strategy": upgrade_strategy, "auto_reboot": auto_reboot, "channel": firmware_channel}

    def _get_ssr_available_versions(self, firmware_channel: str) -> list[dict[str, Any]]:
        """Fetch available SSR firmware versions for the given channel from the Mist API.

        Returns:
            list of version dicts with 'version', 'package', 'default' keys
        """
        logging.info("Discovering SSR versions channel=%s", firmware_channel)  # WHY: entry audit
        print(f"\n{'=' * 60}\nSSR FIRMWARE VERSION SELECTION\n{'=' * 60}")  # WHY: banner
        print("\n-> Discovering available SSR firmware versions...")  # WHY: user feedback
        raw_rows = self._fetch_ssr_version_rows(firmware_channel)  # WHY: raw API rows
        if raw_rows is None:  # WHY: fetch failed, error already emitted
            return []  # WHY: empty list means "no versions"
        available_versions = self._normalize_ssr_version_rows(raw_rows)  # WHY: normalize dict/str
        self._print_ssr_version_summary(available_versions, firmware_channel)  # WHY: user summary
        logging.debug("Discovered SSR versions count=%d", len(available_versions))  # WHY: exit audit
        return available_versions  # WHY: caller uses this list

    def _fetch_ssr_version_rows(self, firmware_channel: str) -> list[Any] | None:
        """Fetch raw SSR version rows from the API; None on failure."""
        logging.info("Fetching SSR version rows channel=%s", firmware_channel)  # WHY: entry audit
        response = mistapi.api.v1.orgs.ssr.listOrgAvailableSsrVersions(  # WHY: channel-scoped SSR versions
            self.apisession, self.org_id, channel=firmware_channel
        )
        if response.status_code != 200:  # WHY: non-2xx is failure
            print(f"X  Error retrieving SSR firmware versions: {response.status_code}")  # WHY: user error banner
            logging.error("Failed to retrieve SSR versions: %s", response.status_code)  # WHY: audit failure
            return None  # WHY: signal failure to caller
        logging.debug("Fetched SSR version rows count=%d", len(response.data or []))  # WHY: exit audit
        return response.data or []  # WHY: normalize None to empty list

    def _normalize_ssr_version_rows(self, raw_rows: list[Any]) -> list[dict[str, Any]]:
        """Normalize raw rows (dicts or strings) into uniform version dicts."""
        logging.info("Normalizing SSR version rows count=%d", len(raw_rows))  # WHY: entry audit
        available_versions: list[dict[str, Any]] = []  # WHY: accumulate normalized entries
        for row in raw_rows:  # WHY: process each API row
            entry = self._parse_single_ssr_version_row(row)  # WHY: single-row dispatch
            if entry is not None:  # WHY: skip malformed rows
                available_versions.append(entry)  # WHY: keep normalized entry
        logging.debug("Normalized SSR versions count=%d", len(available_versions))  # WHY: exit audit
        return available_versions  # WHY: hand back normalized list

    def _parse_single_ssr_version_row(self, row: Any) -> dict[str, Any] | None:
        """Coerce a single SSR row into the normalized dict, or None if invalid."""
        if isinstance(row, dict) and row.get("version"):  # WHY: dict rows carry richer metadata
            return {  # WHY: normalized shape
                "version": row.get("version"),  # WHY: canonical version string
                "package": row.get("package", "SSR"),  # WHY: default package label
                "default": row.get("default", False),  # WHY: default flag defaults False
            }
        if isinstance(row, str):  # WHY: legacy string-only row format
            return {"version": row, "package": "SSR", "default": False}  # WHY: minimal normalized shape
        return None  # WHY: skip unrecognized row

    def _print_ssr_version_summary(self, available_versions: list[dict[str, Any]], firmware_channel: str) -> None:
        """Print the SSR version discovery summary line."""
        if not available_versions:  # WHY: none-found branch
            print(f"X  No SSR firmware versions available for {firmware_channel} channel")  # WHY: user error
            return  # WHY: nothing else to print
        print(  # WHY: hit-count summary
            f"!? Found {len(available_versions)} available SSR firmware versions for channel: {firmware_channel}"
        )

    def _collect_ssr_inventory_data(self, gw_list: list[dict[str, Any]]) -> tuple[int, set[str], set[str]]:
        """Scan gateway inventory and collect SSR device count, models, and versions.

        Returns:
            tuple: (ssr_count, models_set, versions_set)
        """
        logging.info("Collecting SSR inventory data rows=%d", len(gw_list))  # WHY: entry audit
        ssr_count = 0  # WHY: running SSR match count
        models: set[str] = set()  # WHY: deduped model names
        versions: set[str] = set()  # WHY: deduped version strings
        for gw in gw_list:  # WHY: iterate every gateway row
            if not self._is_ssr_inventory_row(gw):  # WHY: single-branch predicate
                continue  # WHY: skip non-SSR rows
            ssr_count += 1  # WHY: count matched SSR
            self._collect_ssr_row_metadata(gw, models, versions)  # WHY: mutate sets in place
        logging.debug("Collected SSR inventory data count=%d", ssr_count)  # WHY: exit audit
        return ssr_count, models, versions  # WHY: caller displays these

    def _is_ssr_inventory_row(self, gw: dict[str, Any]) -> bool:
        """Return True if the inventory row is SSR-family."""
        if gw.get("type", "") == "ssr":  # WHY: canonical type match
            return True  # WHY: fast-path SSR type
        model = gw.get("model", "")  # WHY: fallback to model pattern
        return "SSR" in model or "128T" in model  # WHY: model-string OR match

    def _collect_ssr_row_metadata(self, gw: dict[str, Any], models: set[str], versions: set[str]) -> None:
        """Add non-empty model and version fields from a row to the caller's sets."""
        version = gw.get("version")  # WHY: optional firmware version
        if version:  # WHY: skip empty
            versions.add(version)  # WHY: dedupe by add-to-set
        model_val = gw.get("model")  # WHY: optional model
        if model_val:  # WHY: skip empty
            models.add(model_val)  # WHY: dedupe by add-to-set

    def _display_ssr_inventory_stats(self, ssr_count: int, models: set[str], versions: set[str]) -> None:
        """Print SSR inventory summary if any SSR devices were found."""
        if ssr_count <= 0:
            return
        print(f"!? Found {ssr_count} SSR device(s) in organization")
        if models:
            print(f"  Models: {', '.join(sorted(models))}")
        if versions:
            print(f"  Current versions: {', '.join(sorted(versions))}")

    def _display_ssr_inventory_info(self) -> None:
        """Display current SSR inventory (models and versions) for reference."""
        print("\n-> Checking current SSR devices...")
        try:
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(self.apisession, self.org_id, type="gateway")
            if response.status_code != 200:
                return
            ssr_count, models, versions = self._collect_ssr_inventory_data(response.data or [])
            self._display_ssr_inventory_stats(ssr_count, models, versions)
        except Exception:
            pass  # Inventory info is informational only

    def _select_ssr_version_from_list(self, available_versions: list[dict[str, Any]]) -> str:
        """Display version list and prompt user to select target version.

        Returns:
            str: selected version string
        """
        logging.info("Selecting SSR version count=%d", len(available_versions))  # WHY: entry audit
        self._render_ssr_version_menu(available_versions)  # WHY: draw menu
        target_version = self._loop_ssr_version_input(available_versions)  # WHY: read + validate
        logging.debug("Selected SSR version target=%s", target_version)  # WHY: exit audit
        return target_version  # WHY: caller uses this string

    def _render_ssr_version_menu(self, available_versions: list[dict[str, Any]]) -> None:
        """Draw the numbered menu of SSR firmware versions."""
        print(f"\n{'=' * 50}\nAVAILABLE SSR FIRMWARE VERSIONS\n{'=' * 50}")  # WHY: banner
        for i, info in enumerate(available_versions, 1):  # WHY: 1-based indexing
            marker = " (default)" if info["default"] else ""  # WHY: highlight default row
            print(f"{i:2d}. {info['version']} [{info['package']}]{marker}")  # WHY: menu line

    def _loop_ssr_version_input(self, available_versions: list[dict[str, Any]]) -> str:
        """Loop until a valid version index is chosen. Returns the version string."""
        logging.info("Awaiting SSR version selection")  # WHY: entry audit
        while True:  # WHY: retry until valid
            choice = self._safe_input_fn(  # WHY: prompt via injected input helper
                f"\nSelect firmware version (1-{len(available_versions)}): ",
                context="firmware_manager",
            ).strip()
            resolved = self._resolve_ssr_version_choice(choice, available_versions)  # WHY: dispatch
            if resolved is not None:  # WHY: valid choice terminates loop
                print(f"-> Selected firmware version: {resolved}")  # WHY: confirmation line
                logging.debug("Resolved SSR version target=%s", resolved)  # WHY: exit audit
                return resolved  # WHY: hand back to caller

    def _resolve_ssr_version_choice(self, choice: str, available_versions: list[dict[str, Any]]) -> str | None:
        """Return the resolved version string, or None to retry the loop."""
        if not choice:  # WHY: empty input path
            print("X  Please enter a selection")  # WHY: user feedback
            return None  # WHY: retry
        try:
            idx = int(choice) - 1  # WHY: 0-based index
        except ValueError:  # WHY: non-numeric input
            print("X  Please enter a valid number")  # WHY: user feedback
            return None  # WHY: retry
        if 0 <= idx < len(available_versions):  # WHY: range check
            return str(available_versions[idx]["version"])  # WHY: valid selection
        print(f"X  Please enter a number between 1 and {len(available_versions)}")  # WHY: out-of-range feedback
        return None  # WHY: retry

    def _fetch_and_select_ssr_version(self, firmware_channel: str) -> tuple[str, dict[str, Any] | None]:
        """Fetch available SSR versions and prompt for selection.

        Returns:
            tuple: (target_version string, error_dict or None)
        """
        logger = logging.getLogger(__name__)
        try:
            available_versions = self._get_ssr_available_versions(firmware_channel)
            if not available_versions:
                msg = f"No SSR firmware versions available for {firmware_channel} channel"
                return "", {"error": msg}
            self._display_ssr_inventory_info()
            return self._select_ssr_version_from_list(available_versions), None
        except Exception as e:
            logger.error("SSR firmware discovery failed: %s", str(e))
            return "", {"error": f"SSR firmware discovery error: {str(e)}"}

    def _confirm_ssr_upgrade(
        self,
        org_name: str,
        selected_sites: list[dict[str, Any]],
        target_version: str,
        upgrade_config: dict[str, Any],
    ) -> bool:
        """Print upgrade summary, warning, and request UPGRADE confirmation.

        Returns:
            bool: True if confirmed, False if cancelled
        """
        logging.info("Confirming SSR upgrade org=%s sites=%d", org_name, len(selected_sites))  # WHY: entry audit
        self._print_ssr_upgrade_summary(org_name, selected_sites, target_version, upgrade_config)  # WHY: show config
        self._print_ssr_upgrade_warning()  # WHY: mandatory operator warning
        result = self._read_ssr_upgrade_confirmation()  # WHY: read confirm token
        logging.debug("SSR upgrade confirmation resolved confirmed=%s", result)  # WHY: exit audit
        return result

    def _print_ssr_upgrade_summary(
        self,
        org_name: str,
        selected_sites: list[dict[str, Any]],
        target_version: str,
        upgrade_config: dict[str, Any],
    ) -> None:
        """Print the SSR upgrade configuration summary block."""
        print(f"\n{'=' * 60}\nSSR UPGRADE CONFIGURATION SUMMARY\n{'=' * 60}")  # WHY: section banner
        print(f"Organization ID: {self.org_id}")  # WHY: identify org scope
        print(f"Organization: {org_name}")  # WHY: human-readable org name
        print(f"Sites to upgrade: {len(selected_sites)}")  # WHY: site fanout size
        print(f"Target firmware: {target_version}")  # WHY: show chosen version
        print(f"Firmware channel: {upgrade_config['channel']}")  # WHY: channel disclosure
        print(f"Upgrade strategy: {upgrade_config['strategy']}")  # WHY: strategy disclosure
        print(f"Auto reboot: {'Yes' if upgrade_config['auto_reboot'] else 'No'}")  # WHY: reboot disclosure

    def _print_ssr_upgrade_warning(self) -> None:
        """Print the SSR-specific routing infrastructure warning block."""
        print("\n!? CRITICAL ROUTING INFRASTRUCTURE WARNING !?")  # WHY: highlight impact
        print("SSR firmware upgrades will cause WAN connectivity disruption!")  # WHY: disruption notice
        print("- SSRs will reboot and SD-WAN tunnels will be offline during upgrade")  # WHY: tunnel outage
        print("- Branch offices may lose connectivity")  # WHY: branch impact
        print("- Plan extended maintenance windows")  # WHY: scheduling caution
        print("- Verify backup connectivity paths before execution")  # WHY: prerequisite check
        print("- Monitor upgrade progress closely")  # WHY: monitoring requirement
        print("\nTo proceed with SSR firmware upgrade, type: UPGRADE")  # WHY: token instruction

    def _read_ssr_upgrade_confirmation(self) -> bool:
        """Read and validate the UPGRADE confirmation token."""
        try:
            confirmation = self._safe_input_fn(  # WHY: prompt with audit tag
                "Confirmation: ", context="SSR firmware upgrade confirmation"
            )
        except SystemExit:
            print("-> Operation cancelled")  # WHY: user-facing cancel notice
            return False  # WHY: cancel path
        if confirmation != "UPGRADE":  # WHY: strict token match required
            print("-> Operation cancelled - incorrect confirmation")  # WHY: reject feedback
            logging.info("SSR firmware upgrade cancelled by user")  # WHY: audit rejection
            return False  # WHY: cancel path
        return True  # WHY: confirmed path

    def _build_ssr_upgrade_results(self, target_version: str, upgrade_config: dict[str, Any]) -> dict[str, Any]:
        """Initialize the upgrade results tracking dictionary.

        Returns:
            dict: upgrade_results with initial counters and metadata
        """
        logger = logging.getLogger(__name__)
        results: dict[str, Any] = {
            "operation_id": f"ssr_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_version": target_version,
            "strategy": upgrade_config["strategy"],
            "channel": upgrade_config["channel"],
            "reboot": upgrade_config["auto_reboot"],
            "sites_processed": 0,
            "ssrs_upgraded": 0,
            "errors": [],
            "start_time": datetime.now().isoformat(),
            "site_results": [],
        }
        logger.info("Starting SSR firmware upgrade operation: %s", results["operation_id"])
        return results

    def _load_org_ssr_inventory(self) -> dict[str, dict[str, Any]]:
        """Load org-level SSR inventory for device validation.

        Returns:
            dict: mapping device_id -> model/type/version/site_id info
        """
        logging.info("Loading org SSR inventory org=%s", self.org_id)  # WHY: entry audit
        print("-> Validating SSR devices from organization inventory...")  # WHY: user feedback banner
        gateways = self._fetch_org_gateway_inventory()  # WHY: raw gateway list or None on error
        if gateways is None:  # WHY: fetch failed already logged
            return {}  # WHY: empty inventory on failure
        inventory = self._extract_ssr_devices_from_gateways(gateways)  # WHY: filter SSR-family devices
        print(f"!? Found {len(inventory)} SSR device(s) in organization inventory")  # WHY: summary line
        logging.debug("Loaded org SSR inventory count=%d", len(inventory))  # WHY: exit audit
        return inventory  # WHY: hand back the built map

    def _fetch_org_gateway_inventory(self) -> list[dict[str, Any]] | None:
        """Fetch gateway inventory rows from the org endpoint.

        Returns:
            list of gateway dicts on success, None on error.
        """
        logging.info("Fetching org gateway inventory org=%s", self.org_id)  # WHY: entry audit
        try:  # WHY: network call may raise
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: gateway-type inventory endpoint
                self.apisession, self.org_id, type="gateway"
            )
        except Exception as e:  # WHY: broad guard for network / library errors
            logging.error("Error getting org SSR inventory: %s", e)  # WHY: audit failure
            print(f"X  Error validating SSR inventory: {e}")  # WHY: user-facing error banner
            return None  # WHY: signal failure to caller
        if response.status_code != 200:  # WHY: non-2xx indicates API failure
            logging.error("Failed to get org inventory: %s", response.status_code)  # WHY: audit status
            print("X  Failed to validate SSR inventory")  # WHY: user-facing failure banner
            return None  # WHY: signal failure to caller
        logging.debug("Fetched org gateway inventory rows=%d", len(response.data or []))  # WHY: exit audit
        return response.data or []  # WHY: normalize None to empty list

    def _extract_ssr_devices_from_gateways(self, gateways: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Filter gateway rows to SSR-family devices only.

        Returns:
            dict: mapping device_id -> model/type/version/site_id info
        """
        logging.info("Extracting SSR devices from gateways count=%d", len(gateways))  # WHY: entry audit
        inventory: dict[str, dict[str, Any]] = {}  # WHY: accumulate SSR entries
        for gw in gateways:  # WHY: iterate every gateway row
            entry = self._ssr_entry_from_gateway(gw)  # WHY: keyed extraction with SSR gating
            if entry is None:  # WHY: gateway is not SSR or lacks a valid id
                continue  # WHY: skip non-SSR / unusable rows
            gw_id, gw_info = entry  # WHY: unpack tuple for dict insert
            inventory[gw_id] = gw_info  # WHY: keyed by device id
        logging.debug("Extracted SSR devices count=%d", len(inventory))  # WHY: exit audit
        return inventory  # WHY: caller uses this as validation table

    def _ssr_entry_from_gateway(self, gw: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
        """Return (device_id, info) for an SSR gateway row, or None if not eligible."""
        gw_type = gw.get("type", "")  # WHY: gateway type discriminator
        gw_model = gw.get("model", "")  # WHY: model string for SSR pattern match
        if not self._is_ssr_gateway_row(gw_type, gw_model):  # WHY: gate to SSR-family only
            return None  # WHY: skip non-SSR gateway
        gw_id = gw.get("id")  # WHY: extract device id for keying
        if not isinstance(gw_id, str) or not gw_id:  # WHY: skip rows without a usable id
            return None  # WHY: dict key must be non-empty str
        info = {  # WHY: normalized SSR entry payload
            "model": gw_model,  # WHY: preserve model for later display
            "type": gw_type,  # WHY: preserve type for validation logic
            "version": gw.get("version", ""),  # WHY: current firmware
            "site_id": gw.get("site_id", ""),  # WHY: site anchor for scoping
        }
        return gw_id, info  # WHY: hand keyed entry to accumulator

    def _is_ssr_gateway_row(self, gw_type: str, gw_model: str) -> bool:
        """Return True when gateway type/model identifies an SSR-family device."""
        return gw_type == "ssr" or "SSR" in gw_model or "128T" in gw_model  # WHY: SSR predicate

    def _discover_site_ssr_devices(self, site: dict[str, Any], ssr_models: list[str]) -> list[dict[str, Any]]:
        """Get SSR devices at a site, filtered from all gateway devices.

        Returns:
            list of SSR device dicts, or empty list on error/no SSRs
        """
        site_id = site.get("id")  # WHY: scoping key for site devices call
        site_name = site.get("name", "Unknown")  # WHY: user-friendly label for banners
        logging.info("Discovering SSR devices site=%s", site_name)  # WHY: entry audit
        print(f"  -> Discovering SSRs at {site_name}...")  # WHY: progress banner
        gateway_devices = self._fetch_site_gateway_devices(site_id, site_name)  # WHY: raw list or None
        if gateway_devices is None:  # WHY: fetch failure already logged
            return []  # WHY: empty result on failure
        ssrs = self._filter_devices_by_ssr_model(gateway_devices, ssr_models)  # WHY: pattern-match SSRs
        logging.debug("Discovered SSR devices site=%s count=%d", site_name, len(ssrs))  # WHY: exit audit
        return ssrs  # WHY: caller pipes into upgrade planner

    def _fetch_site_gateway_devices(self, site_id: Any, site_name: str) -> list[dict[str, Any]] | None:
        """Fetch gateway devices for a single site.

        Returns:
            list of device dicts on success, None on API error.
        """
        logging.info("Fetching site gateway devices site=%s", site_name)  # WHY: entry audit
        response = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: site-scoped gateway listing
            self.apisession, site_id, type="gateway"
        )
        if response.status_code != 200:  # WHY: non-2xx is API failure
            logging.error("Failed to retrieve devices for site %s: %s", site_name, response.status_code)  # WHY: audit
            return None  # WHY: signal failure
        rows = response.data or []  # WHY: normalize None to empty list
        logging.debug("Fetched site gateway devices site=%s rows=%d", site_name, len(rows))  # WHY: exit audit
        return rows  # WHY: hand back list for filtering

    def _filter_devices_by_ssr_model(
        self, devices: list[dict[str, Any]], ssr_models: list[str]
    ) -> list[dict[str, Any]]:
        """Filter gateway devices down to SSR-model matches.

        Returns:
            list of SSR-classified device dicts.
        """
        logging.info("Filtering devices for SSR models count=%d", len(devices))  # WHY: entry audit
        ssrs: list[dict[str, Any]] = []  # WHY: accumulate matched SSRs
        for device in devices:  # WHY: iterate every gateway row
            if not self._is_ssr_gateway(device, ssr_models):  # WHY: single-branch dispatch
                logging.debug("Skipping non-SSR device: %s", device.get("id", ""))  # WHY: audit skip
                continue  # WHY: move on
            ssrs.append(device)  # WHY: keep SSR-classified device
            logging.info("Identified SSR device: %s (model: %s)", device.get("id", ""), device.get("model", ""))
            print(f"    -> Identified SSR: {device.get('model', '')} ({device.get('id', '')})")  # WHY: op line
        logging.debug("Filtered SSR devices count=%d", len(ssrs))  # WHY: exit audit
        return ssrs  # WHY: caller consumes this list

    def _is_ssr_gateway(self, device: dict[str, Any], ssr_models: list[str]) -> bool:
        """Return True if device is a gateway matching any SSR model pattern."""
        if device.get("type", "") != "gateway":  # WHY: only gateway type is eligible
            return False  # WHY: bail early on non-gateway
        model = device.get("model", "")  # WHY: single model lookup
        if "SSR" in model:  # WHY: literal SSR substring match
            return True  # WHY: fast-path match
        return any(pattern in model for pattern in ssr_models)  # WHY: user-supplied pattern match

    def _validate_ssr_devices_for_version(
        self,
        device_ids: list[str],
        inventory: dict[str, dict[str, Any]],
        target_version: str,
    ) -> tuple[list[str], list[str]]:
        """Validate SSR device IDs against inventory and check firmware versions.

        Returns:
            tuple: (validated_ids, skipped_ids)
        """
        logging.info("Validating SSR devices count=%d target=%s", len(device_ids), target_version)  # WHY: audit
        validated: list[str] = []  # WHY: accumulate upgrade-eligible ids
        skipped: list[str] = []  # WHY: accumulate rejected ids
        for dev_id in device_ids:  # WHY: iterate all requested ids
            verdict = self._classify_ssr_device_for_upgrade(dev_id, inventory, target_version)  # WHY: dispatch
            if verdict == "upgrade":  # WHY: only upgrade verdict enters validated list
                validated.append(dev_id)  # WHY: keep eligible id
            else:  # WHY: any other verdict is a skip
                skipped.append(dev_id)  # WHY: keep for reporting
        logging.debug("Validated SSR devices upgrade=%d skip=%d", len(validated), len(skipped))  # WHY: exit
        return validated, skipped  # WHY: caller uses both lists

    def _classify_ssr_device_for_upgrade(
        self,
        dev_id: str,
        inventory: dict[str, dict[str, Any]],
        target_version: str,
    ) -> str:
        """Return a single-word verdict for one candidate device.

        Verdicts: 'missing' / 'current' / 'downgrade' / 'upgrade'.
        """
        logging.info("Classifying SSR device id=%s target=%s", dev_id, target_version)  # WHY: entry audit
        if dev_id not in inventory:  # WHY: id must be present in inventory to proceed
            self._emit_ssr_verdict_missing(dev_id)  # WHY: uniform missing feedback
            return "missing"  # WHY: sentinel for orchestrator
        info = inventory[dev_id]  # WHY: fetch model/version pair
        current = info.get("version", "")  # WHY: currently-running firmware
        if current == target_version:  # WHY: already at target -> no-op
            self._emit_ssr_verdict_current(dev_id, target_version)  # WHY: uniform current feedback
            return "current"  # WHY: sentinel for orchestrator
        if self._is_firmware_downgrade(current, target_version):
            self._emit_ssr_verdict_downgrade(dev_id, info, current, target_version)  # WHY: uniform downgrade
            return "downgrade"  # WHY: sentinel for orchestrator
        self._emit_ssr_verdict_upgrade(dev_id, info, current, target_version)  # WHY: uniform upgrade feedback
        return "upgrade"  # WHY: sentinel for orchestrator

    def _emit_ssr_verdict_missing(self, dev_id: str) -> None:
        """Log + print the missing-inventory verdict."""
        logging.warning("Device %s not found in org SSR inventory - skipping", dev_id)  # WHY: audit miss
        print(f"    !? Device {dev_id} not in SSR inventory - skipping")  # WHY: operator feedback

    def _emit_ssr_verdict_current(self, dev_id: str, target_version: str) -> None:
        """Log + print the already-at-target verdict."""
        logging.info("Device %s already at target version %s - skipping", dev_id, target_version)  # WHY: audit
        print(f"    -> Device {dev_id} already at version {target_version} - skipping")  # WHY: operator feedback

    def _emit_ssr_verdict_downgrade(self, dev_id: str, info: dict[str, Any], current: str, target_version: str) -> None:
        """Log + print the downgrade-rejected verdict."""
        logging.warning("Device %s downgrade rejected: %s -> %s", dev_id, current, target_version)  # WHY: audit
        print(f"    ! Downgrade detected: {info['model']} ({current} -> {target_version}) - skipping")  # WHY: op

    def _emit_ssr_verdict_upgrade(self, dev_id: str, info: dict[str, Any], current: str, target_version: str) -> None:
        """Log + print the upgrade-eligible verdict."""
        logging.info("Validated SSR %s: %s %s -> %s", dev_id, info["model"], current, target_version)  # WHY: audit
        print(f"    -> Upgrade needed: {info['model']} ({current} -> {target_version})")  # WHY: op feedback

    def _handle_ssr_upgrade_error_response(
        self,
        site_name: str,
        response: Any,
        site_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse an error response from the SSR upgrade API call.

        Delegates body-extraction and classification to helpers to satisfy PCPP.
        """
        logging.info("Handling SSR upgrade error site=%s status=%s", site_name, response.status_code)  # WHY: audit
        try:  # WHY: response.body access can raise
            text = self._extract_ssr_error_text(response)  # WHY: uniform body decode
            self._classify_ssr_error_text(text, site_name, response, site_result)  # WHY: route by keyword
        except Exception as exc:  # WHY: guard attr/decode faults
            logging.error("Could not read response details: %s", exc)  # WHY: audit failure
            fallback = f"Upgrade initiation failed for {site_name}: {response.status_code}"  # WHY: fallback text
            site_result["error"] = fallback  # WHY: propagate fallback error
        logging.debug("SSR upgrade error handling done site=%s", site_name)  # WHY: trace exit
        return site_result  # WHY: mutated dict propagates up

    def _extract_ssr_error_text(self, response: Any) -> str:
        """Return the best-available textual payload from a mistapi response."""
        data = getattr(response, "data", None)  # WHY: preferred parsed field
        if data:  # WHY: truthy data wins first
            return str(data)  # WHY: stringify structured data
        text = getattr(response, "text", None)  # WHY: fallback to raw text
        if text:  # WHY: truthy text wins second
            return cast(str, text)  # WHY: narrow getattr Any to declared str
        content = getattr(response, "content", None)  # WHY: fallback to raw bytes
        if content:  # WHY: truthy content wins third
            return cast(str, content.decode("utf-8"))  # WHY: normalize decode Any to str
        return f"Status: {response.status_code}"  # WHY: last-resort placeholder

    def _classify_ssr_error_text(
        self,
        text: str,
        site_name: str,
        response: Any,
        site_result: dict[str, Any],
    ) -> None:
        """Route the response text into skip_reason vs error on site_result."""
        text_lower = text.lower()  # WHY: case-insensitive match
        if "already at the requested fw version" in text_lower:  # WHY: benign no-op skip
            logging.info("SSR upgrade skipped at %s: already at target version", site_name)  # WHY: audit skip
            print(f"  - SSRs at {site_name} already at target version")  # WHY: operator preview
            site_result["skip_reason"] = "already_at_version"  # WHY: mark benign skip
            return  # WHY: short-circuit further checks
        if "downgrade fw version not allowed" in text_lower:  # WHY: business rule rejection
            logging.warning("SSR downgrade rejected at %s", site_name)  # WHY: audit reject
            print(f"  ! Firmware downgrade not allowed at {site_name}")  # WHY: operator feedback
            site_result["skip_reason"] = "downgrade_not_allowed"  # WHY: mark policy skip
            return  # WHY: short-circuit further checks
        logging.error("SSR upgrade API error: %s", text)  # WHY: audit true failure
        print(f"  -> API Response: {text}")  # WHY: expose raw text to op
        error = f"Upgrade initiation failed for {site_name}: {response.status_code}"  # WHY: uniform error label
        print(f"  X  {error}")  # WHY: operator failure marker
        site_result["error"] = error  # WHY: propagate error to caller

    def _call_ssr_upgrade_api(
        self,
        site_name: str,
        validated_ids: list[str],
        target_version: str,
        upgrade_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Call the Mist API to initiate SSR firmware upgrade for validated devices.

        Returns:
            dict: site_result with upgrade_initiated, skip_reason, or error fields
        """
        logging.info("Calling SSR upgrade API site=%s devices=%d", site_name, len(validated_ids))  # WHY: entry audit
        site_result: dict[str, Any] = {"upgrade_initiated": False}  # WHY: fixed initial shape
        upgrade_body = self._build_ssr_upgrade_body(validated_ids, target_version, upgrade_config)  # WHY: request body
        self._log_ssr_upgrade_request(upgrade_body, validated_ids, target_version, upgrade_config)  # WHY: audit body
        response = mistapi.api.v1.orgs.ssr.upgradeOrgSsrs(  # WHY: fire upgrade API
            self.apisession, self.org_id, body=upgrade_body
        )
        result = self._interpret_ssr_upgrade_response(response, site_name, validated_ids, site_result)  # WHY: dispatch
        logging.debug("SSR upgrade API done site=%s ok=%s", site_name, result.get("upgrade_initiated"))  # WHY: exit
        return result

    def _build_ssr_upgrade_body(
        self,
        validated_ids: list[str],
        target_version: str,
        upgrade_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the SSR upgrade API request body, honoring the auto_reboot flag."""
        upgrade_body: dict[str, Any] = {  # WHY: canonical request shape
            "device_ids": validated_ids,  # WHY: target devices
            "channel": upgrade_config["channel"],  # WHY: chosen channel
            "version": target_version,  # WHY: chosen firmware version
            "strategy": upgrade_config["strategy"],  # WHY: rollout strategy
        }
        if not upgrade_config["auto_reboot"]:  # WHY: opt-out of auto reboot
            upgrade_body["reboot_at"] = -1  # WHY: sentinel disables reboot
        return upgrade_body  # WHY: hand body to API layer

    def _log_ssr_upgrade_request(
        self,
        upgrade_body: dict[str, Any],
        validated_ids: list[str],
        target_version: str,
        upgrade_config: dict[str, Any],
    ) -> None:
        """Log the SSR upgrade request body and print operator-visible summary lines."""
        logging.info("SSR upgrade request: %s", upgrade_body)  # WHY: full body to audit log
        channel = upgrade_config["channel"]  # WHY: local alias for print
        strategy = upgrade_config["strategy"]  # WHY: local alias for print
        print(f"  -> channel='{channel}', version='{target_version}', strategy='{strategy}'")  # WHY: operator view
        print(f"  -> Device IDs: {validated_ids}")  # WHY: operator device disclosure

    def _interpret_ssr_upgrade_response(
        self,
        response: Any,
        site_name: str,
        validated_ids: list[str],
        site_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Interpret upgrade API response — success or delegated error handler."""
        if response.status_code in [200, 202]:  # WHY: success codes
            print(f"  !? Firmware upgrade initiated for {len(validated_ids)} SSR(s)")  # WHY: operator success line
            site_result["upgrade_initiated"] = True  # WHY: mark success
            logging.info("Successfully initiated SSR firmware upgrade at %s", site_name)  # WHY: audit success
            return site_result  # WHY: propagate success
        return self._handle_ssr_upgrade_error_response(site_name, response, site_result)  # WHY: delegate error branch

    def _process_ssr_site_upgrade(
        self,
        site: dict[str, Any],
        site_index: int,
        total_sites: int,
        upgrade_config: dict[str, Any],
        results: dict[str, Any],
    ) -> None:
        """Process SSR firmware upgrade for a single site.

        Orchestrator: init result, discover+upgrade under try, record outcome.
        """
        site_name = site.get("name", "Unknown")  # WHY: display+audit label
        logging.info("Processing SSR site %s/%s: %s", site_index, total_sites, site_name)  # WHY: audit entry
        print(f"\n[{site_index}/{total_sites}] Processing site: {site_name}")  # WHY: operator progress line
        site_result = self._init_ssr_site_result(site)  # WHY: consistent result shape
        try:  # WHY: guard per-site failures
            self._run_ssr_site_upgrade_flow(site, site_result, upgrade_config, results)  # WHY: happy-path work
        except Exception as exc:  # WHY: broad guard per-site
            self._record_ssr_site_error(site_name, exc, site_result, results)  # WHY: uniform error record
        results["sites_processed"] += 1  # WHY: bump processed counter
        results["site_results"].append(site_result)  # WHY: append per-site record
        logging.debug("SSR site done name=%s upgraded=%s", site_name, site_result.get("upgrade_initiated"))  # audit

    def _init_ssr_site_result(self, site: dict[str, Any]) -> dict[str, Any]:
        """Return the zeroed per-site result dict used to accumulate outcome."""
        return {  # WHY: fixed schema for downstream
            "site_id": site.get("id"),  # WHY: preserve site linkage
            "site_name": site.get("name", "Unknown"),  # WHY: safe display name
            "ssrs_found": 0,  # WHY: initial device count
            "upgrade_initiated": False,  # WHY: flag flips on API success
            "error": None,  # WHY: nullable error slot
        }

    def _tally_ssr_site_upgrade_result(
        self,
        site_result: dict[str, Any],
        validated: list[Any],
        results: dict[str, Any],
    ) -> None:
        """Fold per-site SSR upgrade outcome into the global results counters."""
        if site_result.get("upgrade_initiated"):  # WHY: successful kickoff
            results["ssrs_upgraded"] += len(validated)  # WHY: bump global counter
        if site_result.get("error"):  # WHY: propagate error record
            results["errors"].append(site_result["error"])  # WHY: aggregate for summary

    def _run_ssr_site_upgrade_flow(
        self,
        site: dict[str, Any],
        site_result: dict[str, Any],
        upgrade_config: dict[str, Any],
        results: dict[str, Any],
    ) -> None:
        """Discover devices, validate, call upgrade API, and update results tallies."""
        ssr_models = upgrade_config.get("ssr_models", ["SSR", "128T"])  # WHY: default model filter
        site_ssrs = self._discover_site_ssr_devices(site, ssr_models)  # WHY: enumerate SSRs at site
        site_result["ssrs_found"] = len(site_ssrs)  # WHY: record discovery count
        if not site_ssrs:  # WHY: nothing to upgrade here
            return  # WHY: skip remaining work
        ssr_ids = [ssr["id"] for ssr in site_ssrs]  # WHY: id list for validator
        validated, _ = self._validate_ssr_devices_for_version(  # WHY: filter incompatible SSRs
            ssr_ids, upgrade_config["inventory"], upgrade_config["version"]
        )
        if not validated:  # WHY: nothing left after filter
            return  # WHY: skip upgrade call
        api_result = self._call_ssr_upgrade_api(  # WHY: fire mist upgrade API
            site_result["site_name"], validated, upgrade_config["version"], upgrade_config
        )
        site_result.update(api_result)  # WHY: fold API outcome into result
        self._tally_ssr_site_upgrade_result(site_result, validated, results)  # WHY: aggregate counters

    def _record_ssr_site_error(
        self,
        site_name: str,
        exc: Exception,
        site_result: dict[str, Any],
        results: dict[str, Any],
    ) -> None:
        """Record a per-site exception into both the site_result and results errors."""
        error_msg = f"Error processing site {site_name}: {str(exc)}"  # WHY: uniform error label
        print(f"  X  {error_msg}")  # WHY: operator failure marker
        site_result["error"] = error_msg  # WHY: record on site slot
        results["errors"].append(error_msg)  # WHY: aggregate global errors
        logging.error("Site processing error for %s: %s", site_name, str(exc))  # WHY: audit failure

    def _print_ssr_upgrade_completion(self, results: dict[str, Any]) -> None:
        """Print the SSR upgrade operation completion summary."""
        print(f"\n{'=' * 60}\nSSR FIRMWARE UPGRADE OPERATION COMPLETED\n{'=' * 60}")
        print(f"Operation ID: {results['operation_id']}")
        print(f"Sites processed: {results['sites_processed']}")
        print(f"SSRs upgraded: {results['ssrs_upgraded']}")
        print(f"Errors encountered: {len(results['errors'])}")
        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")
        print("\nSSR upgrade operations have been initiated.")
        print("Monitor progress through Mist dashboard or API.")
        print("Check individual SSR status for completion and connectivity.")
        print("Verify SD-WAN tunnel re-establishment after reboots.")
        # Issue #433 Phase A: hand-converted; codemod doesn't yet detect the
        # logging.getLogger(__name__).<level>(...) dynamic-call pattern.
        logging.getLogger(__name__).info("SSR firmware upgrade operation completed: %s", results["operation_id"])

    def _iterate_ssr_site_upgrades(
        self,
        selected_sites: list[dict[str, Any]],
        upgrade_config: dict[str, Any],
        results: dict[str, Any],
    ) -> None:
        """Iterate selected sites and process each SSR upgrade in sequence."""
        total_sites = len(selected_sites)  # WHY: precompute progress denominator
        for site_index, site in enumerate(selected_sites, 1):  # WHY: 1-based progress index
            self._process_ssr_site_upgrade(  # WHY: delegate per-site upgrade
                site, site_index, total_sites, upgrade_config, results
            )

    def _run_ssr_site_upgrades(
        self,
        selected_sites: list[dict[str, Any]],
        target_version: str,
        upgrade_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute SSR firmware upgrades across all selected sites and return operation summary."""
        logger = logging.getLogger(__name__)  # WHY: module-scoped logger for error path
        results = self._build_ssr_upgrade_results(target_version, upgrade_config)  # WHY: init results envelope
        upgrade_config["inventory"] = self._load_org_ssr_inventory()  # WHY: cache org inventory once
        upgrade_config["ssr_models"] = ["SSR", "128T"]  # WHY: fixed SSR model filter
        upgrade_config["version"] = target_version  # WHY: propagate target version for validators
        print(f"\n{'=' * 60}\nEXECUTING SSR FIRMWARE UPGRADE\n{'=' * 60}")  # WHY: operator banner
        try:
            self._iterate_ssr_site_upgrades(selected_sites, upgrade_config, results)  # WHY: batch loop
            results["end_time"] = datetime.now().isoformat()  # WHY: stamp completion time
            self._print_ssr_upgrade_completion(results)  # WHY: summary output
        except Exception as e:
            results["end_time"] = datetime.now().isoformat()  # WHY: stamp failure time
            results["error"] = str(e)  # WHY: attach error message
            print(f"\nX  Critical error in SSR firmware upgrade: {str(e)}")  # WHY: operator failure marker
            logger.error("Critical error in SSR firmware upgrade: %s", str(e))  # WHY: audit failure
        return results  # WHY: hand back full operation summary

    def _bulk_upgrade_ssr_firmware_by_site(
        self, sites_to_upgrade_override: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """DESTRUCTIVE bulk SSR firmware upgrade across selected sites."""
        logging.info("Starting bulk SSR firmware upgrade - org_id: %s", self.org_id)  # WHY: audit entrypoint
        prepared, error = self._prepare_ssr_bulk_upgrade(sites_to_upgrade_override)  # WHY: gather org/sites/version
        if error is not None:  # WHY: propagate first prep failure
            return error  # WHY: cancel/validation error surfaces to caller
        assert prepared is not None  # WHY: mypy narrowing - error None implies prepared populated
        org_name, selected_sites, upgrade_config, target_version = prepared  # WHY: unpack ready state
        if not self._confirm_ssr_upgrade(org_name, selected_sites, target_version, upgrade_config):  # WHY: last gate
            logging.info("SSR bulk upgrade cancelled at confirmation prompt")  # WHY: audit user cancel
            return {"cancelled": True}  # WHY: preserve pre-refactor cancel sentinel
        logging.debug("SSR bulk upgrade confirmed sites=%d version=%s", len(selected_sites), target_version)  # WHY
        return self._run_ssr_site_upgrades(selected_sites, target_version, upgrade_config)  # WHY: execute batch

    def _resolve_ssr_sites_or_error(
        self, sites_to_upgrade_override: list[dict[str, Any]] | None
    ) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
        """Pick SSR upgrade target sites and normalize empty-selection into a uniform error tuple."""
        selected_sites, error = self._select_ssr_sites_for_upgrade(sites_to_upgrade_override)  # WHY: site picker
        if error:  # WHY: propagate site selection error
            return None, error  # WHY: preserve pre-refactor return shape
        if not selected_sites:  # WHY: empty selection is a user cancel
            print("X  No sites selected")  # WHY: user-visible cancel message
            return None, {"error": "No sites selected"}  # WHY: preserve pre-refactor error shape
        return selected_sites, None  # WHY: success signal with sites list

    def _prepare_ssr_bulk_upgrade(
        self, sites_to_upgrade_override: list[dict[str, Any]] | None
    ) -> tuple[tuple[str, list[dict[str, Any]], dict[str, Any], str] | None, dict[str, Any] | None]:
        """Prepare SSR bulk-upgrade context: validate org, select sites, setup params, resolve version."""
        logging.info("Preparing SSR bulk upgrade context override=%s", sites_to_upgrade_override is not None)  # WHY
        org_and_sites, error = self._resolve_ssr_org_and_sites(sites_to_upgrade_override)  # WHY: org + sites gate
        if error:  # WHY: propagate org / site resolution error uniformly
            return None, error  # WHY: preserve pre-refactor return shape
        assert org_and_sites is not None  # WHY: narrow after error None guard
        org_name, selected_sites = org_and_sites  # WHY: unpack org name + selected sites
        config_and_version, error = self._resolve_ssr_config_and_version()  # WHY: pick channel/strategy + version
        if error:  # WHY: propagate cancel / version resolution error uniformly
            return None, error  # WHY: preserve pre-refactor return shape
        assert config_and_version is not None  # WHY: narrow after error None guard
        upgrade_config, target_version = config_and_version  # WHY: unpack resolver tuple
        logging.debug("SSR bulk upgrade prep complete sites=%d", len(selected_sites))  # WHY: trace success
        return (org_name, selected_sites, upgrade_config, target_version), None  # WHY: tuple + None-error signals ok

    def _resolve_ssr_org_and_sites(
        self, sites_to_upgrade_override: list[dict[str, Any]] | None
    ) -> tuple[tuple[str, list[dict[str, Any]]] | None, dict[str, Any] | None]:
        """Validate org access and resolve sites; return ((org_name, sites), None) or (None, error)."""
        org_name, error = self._validate_org_for_ssr_upgrade()  # WHY: verify org access before user prompts
        if error:  # WHY: propagate org validation error
            return None, error  # WHY: two-slot tuple keeps caller uniform
        selected_sites, error = self._resolve_ssr_sites_or_error(sites_to_upgrade_override)  # WHY: pick+guard sites
        if error:  # WHY: propagate site-resolution error
            return None, error  # WHY: preserve pre-refactor return shape
        assert selected_sites is not None  # WHY: narrow after error None guard
        return (org_name, selected_sites), None  # WHY: success two-slot tuple

    def _resolve_ssr_config_and_version(
        self,
    ) -> tuple[tuple[dict[str, Any], str] | None, dict[str, Any] | None]:
        """Prompt for SSR upgrade params and firmware version; return ((cfg, version), None) or (None, error)."""
        upgrade_config = self._setup_ssr_upgrade_params()  # WHY: pick channel/strategy/timeouts
        if upgrade_config is None:  # WHY: user cancelled param prompts
            return None, {"cancelled": True}  # WHY: preserve pre-refactor cancel sentinel
        target_version, error = self._fetch_and_select_ssr_version(upgrade_config["channel"])  # WHY: pick version
        if error:  # WHY: propagate version resolution error
            return None, error  # WHY: preserve pre-refactor return shape
        return (upgrade_config, target_version), None  # WHY: success two-slot tuple

    def _upgrade_ssr_firmware_by_gateway_template(self) -> None:
        """Advanced SSR firmware upgrade organized by Gateway Template assignment.

        Reuses AP/switch template infrastructure (CSV freshness + template->sites
        mapping) then dispatches to the SSR-specific bulk upgrade. Destructive:
        callers must have obtained explicit operator confirmation upstream.
        """
        logging.info("Starting template-based SSR firmware upgrade for org %s", self.org_id)  # WHY: audit entry
        self._print_ssr_template_banner()  # WHY: mandatory operator hazard banner
        template_sites_mapping = self._prepare_template_upgrade("SSR")  # WHY: freshness + mapping load
        if template_sites_mapping is None:  # WHY: mapping load failed (no templates or no assignments)
            logging.debug("SSR template upgrade aborted - no template-site assignments")  # WHY: trace early exit
            return None  # WHY: preserve pre-refactor cancel behavior
        template_name_to_id, sites_mapping = template_sites_mapping  # WHY: unpack Step-2 tuple
        selection = self._select_template_and_sites(template_name_to_id, sites_mapping)  # WHY: prompt operator
        if selection is None:  # WHY: operator declined the template picker
            logging.debug("SSR template upgrade cancelled at template prompt")  # WHY: trace operator cancel
            return None  # WHY: preserve pre-refactor cancel behavior
        selected_template_name, sites_to_upgrade = selection  # WHY: unpack picker result
        self._execute_template_based_ssr_upgrade(sites_to_upgrade, selected_template_name)  # WHY: dispatch
        logging.debug("SSR template upgrade done template=%s sites=%d", selected_template_name, len(sites_to_upgrade))
        return None  # WHY: explicit None return preserves prior contract

    def _print_ssr_template_banner(self) -> None:
        """Emit the SSR-template upgrade banner (operator hazard header)."""
        logging.debug("Rendering SSR template upgrade banner")  # WHY: trace UI-only helper entry
        print(" Advanced SSR Firmware Upgrade by Gateway Template")  # WHY: menu title for operator context
        print("=" * 70)  # WHY: separator aligned with pre-refactor banner width

    def _prepare_template_upgrade(
        self, device_kind: str
    ) -> tuple[dict[str, str], dict[str, list[dict[str, Any]]]] | None:
        """Refresh template CSVs and load the template->sites mapping.

        device_kind is a short label (e.g. 'SSR' or 'switch') used only for
        audit logs. Returns (template_name_to_id, sites_mapping) on success
        or None when no Gateway Templates have any assigned sites.
        """
        logging.info("Preparing %s template upgrade for org %s", device_kind, self.org_id)  # WHY: audit prep phase
        self._ensure_template_csv_freshness()  # WHY: Step 1 - freshen CSV cache
        template_name_to_id, template_sites_mapping = self._load_template_sites_mapping()  # WHY: load mapping
        if not template_sites_mapping:  # WHY: no template has any assigned site
            print("\n! No Gateway Templates with assigned sites found.")  # WHY: operator diagnostic
            print("  Make sure sites are assigned to Gateway Templates and try again.")  # WHY: remediation hint
            logging.warning("No Gateway Templates with site assignments found (%s upgrade)", device_kind)  # WHY: audit
            return None  # WHY: signal caller to abort without dispatching
        logging.debug("Template mapping loaded templates=%d kind=%s", len(template_sites_mapping), device_kind)
        return template_name_to_id, template_sites_mapping  # WHY: hand off to selection step

    def _select_template_and_sites(
        self,
        template_name_to_id: dict[str, str],
        template_sites_mapping: dict[str, list[dict[str, Any]]],
    ) -> tuple[str, list[dict[str, Any]]] | None:
        """Prompt operator to pick a Gateway Template and resolve its site list.

        Returns (selected_template_name, sites_to_upgrade) on success or None
        when the operator declines the selection prompt.
        """
        logging.info("Prompting SSR template selection templates=%d", len(template_sites_mapping))  # WHY: trace
        selected_template_id, selected_template_name = self._prompt_template_selection(  # WHY: pick
            template_name_to_id, template_sites_mapping
        )
        if not selected_template_id or selected_template_name is None:  # WHY: operator declined or empty input
            print(" No template selected. Exiting.")  # WHY: acknowledge decline
            logging.debug("SSR template selection cancelled by operator")  # WHY: trace decline
            return None  # WHY: signal caller to abort dispatch
        sites_to_upgrade = template_sites_mapping.get(selected_template_id, [])  # WHY: resolve sites
        print(f"\n  Template '{selected_template_name}' includes {len(sites_to_upgrade)} sites")  # WHY: preview
        logging.info("Template %s has %s assigned sites", selected_template_name, len(sites_to_upgrade))  # WHY: audit
        return selected_template_name, sites_to_upgrade  # WHY: hand off to bulk-upgrade dispatcher

    def _execute_template_based_ssr_upgrade(
        self, sites_to_upgrade: list[dict[str, Any]], selected_template_name: str
    ) -> dict[str, Any]:
        """Execute the template-based SSR upgrade with the existing SSR implementation."""
        print(f"  Proceeding with SSR firmware upgrade for template: {selected_template_name}")
        print(f"  Target sites: {len(sites_to_upgrade)}")

        # Use the SSR-specific bulk upgrade implementation
        return self._bulk_upgrade_ssr_firmware_by_site(sites_to_upgrade)  # WHY: run SSR-specific bulk flow


# NOTE: check_firmware_upgrade_status_direct removed - use FirmwareManager(apisession, org_id).check_firmware_upgrade_status() directly  # noqa: E501


class FirmwareUpgradeStatusChecker:
    """Comprehensive firmware upgrade status monitoring and reporting.

    Analyzes device firmware status across organization or specific sites,
    tracks active upgrade operations, and exports detailed status reports.
    Co-located with FirmwareManager per FR-015 (fold firmware helpers into
    the firmware_manager module rather than a fresh src/refactors/* file).

    Features:
    - Device firmware status analysis (in-progress, completed, failed)
    - Active upgrade operation discovery (SSR, AP, Switch)
    - Stale upgrade detection (100% but not marked complete)
    - Progress visualization and distribution analysis
    - CSV export for detailed analysis

    Usage:
        FirmwareUpgradeStatusChecker(scope_choice, site_filter).check()
    """

    # Stale upgrade threshold (hours) - upgrades at 100% older than this are treated as complete
    STALE_UPGRADE_HOURS = 1  # WHY: default staleness cutoff shared across helpers

    # Device type display names
    DEVICE_TYPE_NAMES = {  # WHY: canonical friendly labels for device-type distribution output
        "ap": "Access Points",  # WHY: menu-facing label for AP rows
        "switch": "Switches",  # WHY: menu-facing label for switch rows
        "gateway": "Gateways/SSRs",  # WHY: menu-facing label combines gateway and SSR
        "ssr": "Session Smart Routers",  # WHY: dedicated label for SSR devices when reported distinctly
    }

    def __init__(self, scope_choice: str | None = None, site_filter: str | None = None):
        """Initialize the status checker.

        Args:
            scope_choice: '2' for specific site, '3' for active only, '4' for failed only
            site_filter: Site ID filter (required if scope_choice='2')
        """
        logging.info(  # WHY: audit trail before touching MistHelper singletons
            "Initializing FirmwareUpgradeStatusChecker (scope=%s, site_filter=%s)",
            scope_choice,
            site_filter,
        )
        self.scope_choice = scope_choice  # WHY: menu scope selector (2/3/4)
        self.site_filter = site_filter  # WHY: optional single-site override
        self.org_id = _MH.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: resolve org via MistHelper cache
        self.all_device_stats: list[dict[str, Any]] = []  # WHY: raw device stats collected across API calls
        self.upgrade_results: list[dict[str, Any]] = []  # WHY: rows for the CSV export
        self.active_upgrades: list[dict[str, Any]] = []  # WHY: active upgrade operations for the CSV export
        self.site_lookup: dict[str, str] = {}  # WHY: site_id -> site_name enrichment map
        self.summary = self._create_empty_summary()  # WHY: aggregated counters and distributions
        logging.debug("FirmwareUpgradeStatusChecker initialized for org %s", self.org_id)  # WHY: post-init trace

    def _create_empty_summary(self) -> dict[str, Any]:
        """Create empty firmware status summary structure."""
        return {  # WHY: canonical shape consumed by every _display_* helper
            "total_devices": 0,  # WHY: incremented per processed device
            "devices_with_fwupdate": 0,  # WHY: count of devices that reported fwupdate payload
            "upgrade_in_progress": 0,  # WHY: count of active upgrades
            "upgrade_failed": 0,  # WHY: count of failed upgrades
            "upgrade_completed": 0,  # WHY: count of completed upgrades
            "upgrade_unknown": 0,  # WHY: count of devices with unrecognized status
            "devices_by_status": {},  # WHY: histogram keyed by raw status string
            "devices_by_version": {},  # WHY: histogram keyed by firmware version
            "devices_by_model": {},  # WHY: histogram keyed by hardware model
            "devices_by_type": {},  # WHY: histogram keyed by device type (ap/switch/gateway/ssr)
            "progress_total": 0,  # WHY: running sum of percent-complete values for mean
            "progress_count": 0,  # WHY: divisor for mean progress calculation
            "devices_upgrading": [],  # WHY: rows for real-time upgrade table
        }

    def check(self) -> None:
        """Main entry point - execute firmware upgrade status check."""
        logging.info("Starting firmware upgrade status check...")  # WHY: audit trail for top-level entry
        logging.debug("Scope: %s, Site filter: %s", self.scope_choice, self.site_filter)  # WHY: detail scope

        if not self._resolve_site_filter():  # WHY: user may cancel site selection
            return  # WHY: exit cleanly when no site is chosen
        if not self._fetch_device_stats():  # WHY: bail when the API returns nothing
            return  # WHY: exit cleanly when device stats unavailable
        self._fetch_site_lookup()  # WHY: enrich device rows with site names
        self._process_all_devices()  # WHY: iterate device stats into structured rows
        self._display_summary()  # WHY: print aggregate counters and distributions
        self._display_upgrading_devices()  # WHY: real-time table for in-progress upgrades
        self._check_active_operations()  # WHY: probe SSR/site upgrade endpoints
        self._export_results()  # WHY: write CSV artifacts
        self._display_recommendations()  # WHY: closing operator guidance

        logging.info("Firmware upgrade status check completed successfully")  # WHY: audit trail on success

    def _resolve_site_filter(self) -> bool:
        """Resolve site filter if specific site mode selected."""
        if self.scope_choice == "2" and self.site_filter is None:  # WHY: only prompt when mode 2 and no override
            logging.debug("User selected specific site mode")  # WHY: trace prompt entry
            self.site_filter = _MH.PromptUtils.select_site()  # WHY: interactive site picker via MistHelper
            if not self.site_filter:  # WHY: user cancelled selection
                print(" No site selected. Exiting.")  # WHY: operator-facing cancel notice
                logging.warning("No site selected in specific site mode")  # WHY: audit trail for cancellation
                return False  # WHY: signal caller to abort
            logging.debug("Selected site filter: %s", self.site_filter)  # WHY: trace resolved site id
        return True  # WHY: proceed with (possibly None) filter

    def _fetch_device_stats(self) -> bool:
        """Fetch device statistics from API."""
        print("\n  Fetching device statistics...")  # WHY: operator-facing progress banner
        logging.debug("Scope: %s, site_filter: %s", self.scope_choice, self.site_filter)  # WHY: trace scope

        try:  # WHY: tolerate API failures without crashing menu
            if self.site_filter:  # WHY: single-site branch when filter set
                return self._fetch_site_stats()
            return self._fetch_org_stats()  # WHY: org-wide branch otherwise
        except Exception as exception:  # WHY: any API error yields graceful failure
            print(f"! Failed to fetch device statistics: {exception}")  # WHY: operator notice
            logging.error("Failed to fetch device statistics: %s", exception)  # WHY: structured error log
            return False  # WHY: signal caller to abort

    def _fetch_site_stats(self) -> bool:
        """Fetch device stats for a single site."""
        print("   Fetching stats for selected site...")  # WHY: operator-facing progress banner
        stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(  # WHY: fetch first page for site
            apisession, self.site_filter, type="all", limit=1000
        )
        site_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)  # WHY: paginate to completion
        self.all_device_stats.extend(site_stats)  # WHY: accumulate into shared list

        print(f"   Retrieved stats for {len(site_stats)} devices at selected site")  # WHY: user-visible count
        logging.info("Retrieved stats for %s devices at site %s", len(site_stats), self.site_filter)  # WHY: audit
        return len(self.all_device_stats) > 0 or self._handle_empty_stats()  # WHY: empty-state handling

    def _fetch_org_stats(self) -> bool:
        """Fetch device stats organization-wide."""
        print("   Fetching organization-wide device statistics...")  # WHY: operator-facing progress banner
        stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(  # WHY: fetch first page org-wide
            apisession, self.org_id, type="all", fields="*", limit=1000
        )
        org_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)  # WHY: paginate to completion
        self.all_device_stats.extend(org_stats)  # WHY: accumulate into shared list

        print(f"   Retrieved stats for {len(org_stats)} devices organization-wide")  # WHY: user-visible count
        logging.info("Retrieved stats for %s devices organization-wide", len(org_stats))  # WHY: audit trail
        return len(self.all_device_stats) > 0 or self._handle_empty_stats()  # WHY: empty-state handling

    def _handle_empty_stats(self) -> bool:
        """Handle case when no device statistics found."""
        print(" No device statistics found.")  # WHY: operator-facing empty-state notice
        return False  # WHY: signal caller to abort

    def _fetch_site_lookup(self) -> None:
        """Fetch site information for device enrichment."""
        print("   Fetching site information for device enrichment...")  # WHY: operator-facing progress banner
        try:  # WHY: tolerate API failure; lookup is optional enrichment
            all_sites = _MH.APICoreFetchUtils.all_sites_with_limit(self.org_id)  # WHY: cached fetch via MistHelper
            for site in all_sites:  # WHY: build site_id -> site_name map
                site_id = site.get("id")  # WHY: primary lookup key
                site_name = site.get("name", "Unknown")  # WHY: fallback when name missing
                if site_id:  # WHY: skip rows without an id
                    self.site_lookup[site_id] = site_name  # WHY: cache in instance dict
        except Exception as exception:  # WHY: enrichment failure must not abort report
            logging.warning("Failed to fetch site information: %s", exception)  # WHY: warn but continue
            self.site_lookup.clear()  # WHY: leave empty rather than partial

    def _process_all_devices(self) -> None:
        """Process firmware status for all devices."""
        print(f"\n  Analyzing firmware status for {len(self.all_device_stats)} devices...")  # WHY: banner

        for device_stats in self.all_device_stats:  # WHY: iterate every collected device
            device_info = self._extract_device_info(device_stats)  # WHY: normalize identity fields
            fw_info = self._process_fwupdate(device_stats, device_info)  # WHY: parse fwupdate payload
            self._update_summary_counters(device_info, fw_info)  # WHY: increment histograms
            self._maybe_add_to_results(device_info, fw_info)  # WHY: append row when in scope

    def _extract_device_info(self, device_stats: dict[str, Any]) -> dict[str, Any]:
        """Extract device information from stats."""
        site_id = device_stats.get("site_id", "Unknown")  # WHY: used for both row and site_lookup
        return {  # WHY: canonical device identity block
            "device_id": device_stats.get("id", "Unknown"),  # WHY: primary device id
            "device_name": device_stats.get("name", "Unnamed"),  # WHY: display name
            "device_mac": device_stats.get("mac", "Unknown"),  # WHY: MAC identifier
            "device_model": device_stats.get("model", "Unknown"),  # WHY: hardware model
            "device_type": device_stats.get("type", "Unknown"),  # WHY: type bucket (ap/switch/etc)
            "device_version": device_stats.get("version", "Unknown"),  # WHY: current firmware version
            "site_id": site_id,  # WHY: propagate for lookup
            "site_name": self.site_lookup.get(site_id, "Unknown Site"),  # WHY: enriched site name
            "last_seen": device_stats.get("last_seen", 0),  # WHY: epoch for freshness display
        }

    def _process_fwupdate(self, device_stats: dict[str, Any], device_info: dict[str, Any]) -> dict[str, Any]:
        """Process fwupdate field from device stats."""
        fwupdate = device_stats.get("fwupdate", {})  # WHY: extract nested firmware payload

        if not fwupdate:  # WHY: no firmware information reported
            return self._create_no_upgrade_info(device_info["last_seen"])  # WHY: default row shape

        self.summary["devices_with_fwupdate"] += 1  # WHY: count fw-reporting devices
        return self._parse_fwupdate_data(fwupdate, device_info)  # WHY: build structured fw row

    def _create_no_upgrade_info(self, last_seen: Any) -> dict[str, Any]:
        """Create default firmware info when no upgrade data exists."""
        return {  # WHY: canonical empty-fwupdate row shape
            "fw_status": "no_upgrade_info",  # WHY: sentinel status
            "fw_progress": 0,  # WHY: zero progress by default
            "fw_timestamp": 0,  # WHY: no timestamp yet
            "fw_status_id": 0,  # WHY: no status id yet
            "fw_will_retry": False,  # WHY: no retry scheduled
            "fw_time_str": "N/A",  # WHY: display fallback
            "last_seen_str": self._format_timestamp(last_seen),  # WHY: preserve freshness display
        }

    def _parse_fwupdate_data(self, fwupdate: dict[str, Any], device_info: dict[str, Any]) -> dict[str, Any]:
        """Parse fwupdate dictionary into structured info."""
        fw_status = fwupdate.get("status", "unknown")  # WHY: primary status keyword
        fw_progress = fwupdate.get("progress", 0)  # WHY: percent-complete
        fw_timestamp = fwupdate.get("timestamp", 0)  # WHY: last status-change epoch

        fw_info = {  # WHY: canonical parsed fw row shape
            "fw_status": fw_status,
            "fw_progress": fw_progress,
            "fw_timestamp": fw_timestamp,
            "fw_status_id": fwupdate.get("status_id", 0),
            "fw_will_retry": fwupdate.get("will_retry", False),
            "fw_time_str": self._format_timestamp(fw_timestamp),
            "last_seen_str": self._format_timestamp(device_info["last_seen"]),
        }

        self._categorize_status(fw_status, fw_progress, fw_timestamp, device_info)  # WHY: bucket status
        self._track_status_distribution(fw_status)  # WHY: increment histogram

        return fw_info  # WHY: caller consumes structured row

    def _categorize_status(
        self, fw_status: str, fw_progress: Any, fw_timestamp: Any, device_info: dict[str, Any]
    ) -> None:
        """Categorize device upgrade status and update summary."""
        if fw_status in ("inprogress", "upgrading", "downloading"):  # WHY: active states
            if self._is_stale_upgrade(fw_progress, fw_timestamp):  # WHY: stuck at 100% for too long
                self.summary["upgrade_completed"] += 1  # WHY: treat stale as complete
            else:
                self._track_active_upgrade(fw_progress, fw_timestamp, device_info)  # WHY: live upgrade
        elif fw_status == "failed":  # WHY: explicit failure
            self.summary["upgrade_failed"] += 1  # WHY: increment failure counter
        elif fw_status in ("upgraded", "success"):  # WHY: explicit success
            self.summary["upgrade_completed"] += 1  # WHY: increment completion counter
        else:
            self.summary["upgrade_unknown"] += 1  # WHY: fallback for unrecognized status

    def _is_stale_upgrade(self, fw_progress: Any, fw_timestamp: Any) -> bool:
        """Check if upgrade at 100% is stale (older than threshold)."""
        if fw_progress != 100:  # WHY: only a completed (100%) upgrade can be stale
            return False  # WHY: not complete -- not stale
        if not self._is_valid_upgrade_timestamp(fw_timestamp):  # WHY: timestamp must be usable
            return False  # WHY: cannot judge staleness without a valid timestamp

        try:  # WHY: clock math can raise on pathological values
            upgrade_age_hours = (time.time() - fw_timestamp) / 3600  # WHY: age in hours
            return upgrade_age_hours > self.STALE_UPGRADE_HOURS  # type: ignore[no-any-return]
        except (ValueError, OSError, TypeError):  # WHY: defensive: treat bad math as not stale
            return False  # WHY: could not compute age -- treat as not stale

    @staticmethod
    def _is_valid_upgrade_timestamp(fw_timestamp: Any) -> bool:
        """Return True when fw_timestamp is a positive int/float usable for age math."""
        if not isinstance(fw_timestamp, (int, float)):  # WHY: must be numeric for clock math
            return False  # WHY: non-numeric timestamp is unusable
        return fw_timestamp > 0  # WHY: reject zero/negative epoch values

    def _track_active_upgrade(self, fw_progress: Any, fw_timestamp: Any, device_info: dict[str, Any]) -> None:
        """Track an actively upgrading device."""
        self.summary["upgrade_in_progress"] += 1  # WHY: increment active counter

        if fw_progress is not None and isinstance(fw_progress, (int, float)):  # WHY: only count numeric progress
            self.summary["progress_total"] += fw_progress  # WHY: accumulate for mean
            self.summary["progress_count"] += 1  # WHY: increment divisor

        self.summary["devices_upgrading"].append(  # WHY: retain a row for the real-time table
            {
                "device_name": device_info["device_name"],
                "device_mac": device_info["device_mac"],
                "device_type": device_info["device_type"],
                "device_model": device_info["device_model"],
                "site_name": device_info["site_name"],
                "current_version": device_info["device_version"],
                "progress": fw_progress if fw_progress is not None else 0,
                "fw_timestamp": fw_timestamp,
            }
        )

    def _track_status_distribution(self, fw_status: str) -> None:
        """Track status distribution in summary."""
        if fw_status not in self.summary["devices_by_status"]:  # WHY: initialize bucket lazily
            self.summary["devices_by_status"][fw_status] = 0
        self.summary["devices_by_status"][fw_status] += 1  # WHY: increment bucket

    def _format_timestamp(self, timestamp: Any) -> str:
        """Format a Unix timestamp to readable string."""
        if not timestamp or not isinstance(timestamp, (int, float)) or timestamp <= 0:  # WHY: guard invalid values
            return "Unknown"
        try:  # WHY: fromtimestamp may raise on invalid epoch
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")  # WHY: display format
        except (ValueError, OSError, TypeError):  # WHY: any conversion error yields diagnostic string
            return f"Invalid: {timestamp}"

    def _update_summary_counters(self, device_info: dict[str, Any], fw_info: dict[str, Any]) -> None:
        """Update summary counters for version, model, and type."""
        del fw_info  # WHY: kept in signature for symmetry with sibling; only device_info is used
        version = device_info["device_version"]  # WHY: histogram key
        model = device_info["device_model"]  # WHY: histogram key
        device_type = device_info["device_type"]  # WHY: histogram key

        self.summary["devices_by_version"][version] = self.summary["devices_by_version"].get(version, 0) + 1
        self.summary["devices_by_model"][model] = self.summary["devices_by_model"].get(model, 0) + 1
        self.summary["devices_by_type"][device_type] = self.summary["devices_by_type"].get(device_type, 0) + 1
        self.summary["total_devices"] += 1  # WHY: overall device counter

    @staticmethod
    def _build_upgrade_result_row(
        device_info: dict[str, Any], fw_info: dict[str, Any], progress_display: str
    ) -> dict[str, Any]:
        """Build one upgrade-results row from device identity + firmware status + progress text."""
        return {  # WHY: canonical CSV row shape
            "Site ID": device_info["site_id"],
            "Site Name": device_info["site_name"],
            "Device ID": device_info["device_id"],
            "Device Name": device_info["device_name"],
            "Device MAC": device_info["device_mac"],
            "Device Model": device_info["device_model"],
            "Device Type": device_info["device_type"],
            "Current Version": device_info["device_version"],
            "Last Seen": fw_info["last_seen_str"],
            "FW Upgrade Status": fw_info["fw_status"],
            "FW Progress %": fw_info["fw_progress"],
            "FW Progress Display": progress_display,
            "FW Status ID": fw_info["fw_status_id"],
            "FW Will Retry": fw_info["fw_will_retry"],
            "FW Timestamp": fw_info["fw_time_str"],
            "Timestamp": datetime.now(UTC).isoformat(),
        }

    def _maybe_add_to_results(self, device_info: dict[str, Any], fw_info: dict[str, Any]) -> None:
        """Add device to results if it matches scope filter."""
        if not self._should_include_device(fw_info):  # WHY: scope gate
            return
        progress_display = self._create_progress_display(fw_info)  # WHY: build display string
        self.upgrade_results.append(
            self._build_upgrade_result_row(device_info, fw_info, progress_display)  # WHY: append CSV row
        )

    def _should_include_device(self, fw_info: dict[str, Any]) -> bool:
        """Check if device matches scope filter."""
        fw_status = fw_info["fw_status"]  # WHY: current firmware lifecycle status
        fw_progress = fw_info["fw_progress"]  # WHY: percent-complete when upgrading
        fw_timestamp = fw_info["fw_timestamp"]  # WHY: last status-change epoch for staleness

        if self.scope_choice == "3":  # WHY: active upgrades only
            is_active = fw_status in ("inprogress", "upgrading", "downloading")  # WHY: live states
            if is_active and self._is_stale_upgrade(fw_progress, fw_timestamp):  # WHY: drop stuck rows
                return False  # WHY: exclude stale rows from the active view
            return is_active  # WHY: otherwise include only live upgrades
        if self.scope_choice == "4":  # WHY: failed upgrades only
            return fw_status == "failed"  # type: ignore[no-any-return]
        return True  # WHY: default scope keeps every device

    def _render_active_progress(self, fw_progress: Any, fw_timestamp: Any) -> str:
        """Render the cell for a device that reports an in-flight upgrade."""
        if self._is_stale_upgrade(fw_progress, fw_timestamp):  # WHY: no movement past threshold = stuck
            return "[===============] 100% (Complete - Stale)"  # WHY: full bar but flag staleness
        if fw_progress is not None:  # WHY: a real percent is available
            return _MH.DisplayUtils.create_progress_bar(fw_progress, bar_length=15)  # type: ignore[no-any-return]
        return "N/A"  # WHY: active but no percent yet -- match outer fallback

    def _create_progress_display(self, fw_info: dict[str, Any]) -> str:
        """Create visual progress display for CSV."""
        fw_status = fw_info["fw_status"]  # WHY: status selects which glyph to render
        fw_progress = fw_info["fw_progress"]  # WHY: percent used to size the bar
        fw_timestamp = fw_info["fw_timestamp"]  # WHY: timestamp detects stale rows

        if fw_status in ("inprogress", "upgrading", "downloading"):  # WHY: device reports active work
            return self._render_active_progress(fw_progress, fw_timestamp)  # WHY: delegate active rendering
        if fw_status in ("upgraded", "success"):  # WHY: upgrade finished cleanly
            return "[===============] 100% (Complete)"  # WHY: full bar marks completion
        if fw_status == "failed":  # WHY: upgrade ended in failure
            return "[!!!!! FAILED !!!!!]"  # WHY: loud marker for failures
        return "N/A"  # WHY: idle/unknown devices have no progress

    def _display_summary(self) -> None:
        """Display firmware status summary."""
        print("\n  Firmware Status Summary:")  # WHY: section header
        print(f"   X  Total devices analyzed: {self.summary['total_devices']}")  # WHY: devices examined
        print(f"   X  Devices with upgrade info: {self.summary['devices_with_fwupdate']}")  # WHY: with fw data
        print(f"   X  Upgrades in progress: {self.summary['upgrade_in_progress']}")  # WHY: running upgrades

        self._display_average_progress()  # WHY: mean progress when upgrades active

        print(f"   X  Upgrades completed: {self.summary['upgrade_completed']}")  # WHY: completed tally
        print(f"   X  Upgrades failed: {self.summary['upgrade_failed']}")  # WHY: failed tally
        print(f"   X  Unknown status: {self.summary['upgrade_unknown']}")  # WHY: unreadable-status tally

        self._display_status_distribution()  # WHY: counts by raw firmware status
        self._display_type_distribution()  # WHY: counts by device type
        self._display_version_distribution()  # WHY: counts by firmware version
        self._display_model_distribution()  # WHY: counts by hardware model

    def _display_average_progress(self) -> None:
        """Display average progress for in-progress upgrades."""
        if self.summary["progress_count"] > 0:  # WHY: only when some upgrade reported progress
            avg_progress = self.summary["progress_total"] / self.summary["progress_count"]  # WHY: mean
            progress_bar = _MH.DisplayUtils.create_progress_bar(int(avg_progress))  # WHY: render mean as bar
            print(f"   X  Average upgrade progress: {progress_bar}")  # WHY: emit the averaged line

    def _display_status_distribution(self) -> None:
        """Display status distribution."""
        if self.summary["devices_by_status"]:  # WHY: skip when no status data collected
            print("\n  Status Distribution:")  # WHY: sub-section header
            for status, count in sorted(self.summary["devices_by_status"].items()):  # WHY: alphabetical order
                print(f"   X  {status}: {count} devices")  # WHY: one line per status bucket

    def _display_type_distribution(self) -> None:
        """Display device type distribution."""
        print("\n  Device Type Distribution:")  # WHY: sub-section header always shown
        if self.summary["devices_by_type"]:  # WHY: render buckets when type data exists
            sorted_types = sorted(
                self.summary["devices_by_type"].items(), key=lambda x: x[1], reverse=True
            )  # WHY: descending count order
            for device_type, count in sorted_types:  # WHY: walk each type bucket
                type_display = self.DEVICE_TYPE_NAMES.get(device_type, device_type.upper())  # WHY: friendly label
                print(f"   X  {type_display}: {count} devices")  # WHY: one line per device type
        else:
            print("   X  No device type information available")  # WHY: message when no type data gathered

    def _display_version_distribution(self) -> None:
        """Display version distribution."""
        print("\n  Version Distribution:")  # WHY: sub-section header
        sorted_versions = sorted(
            self.summary["devices_by_version"].items(), key=lambda x: x[1], reverse=True
        )  # WHY: descending count order
        for version, count in sorted_versions:  # WHY: walk each version bucket
            print(f"   X  {version}: {count} devices")

    def _display_model_distribution(self) -> None:
        """Display model distribution."""
        print("\n  Model Distribution:")  # WHY: sub-section header
        sorted_models = sorted(
            self.summary["devices_by_model"].items(), key=lambda x: x[1], reverse=True
        )  # WHY: descending count order
        for model, count in sorted_models:  # WHY: walk each model bucket
            print(f"   X  {model}: {count} devices")

    def _display_upgrading_devices(self) -> None:
        """Display detailed progress for devices currently upgrading."""
        if not self.summary["devices_upgrading"]:  # WHY: skip when nothing is upgrading
            return

        print("\n  Devices Currently Upgrading (Real-Time Progress):")  # WHY: section banner
        print(f"  {'=' * 110}")  # WHY: table top border

        sorted_upgrading = sorted(
            self.summary["devices_upgrading"], key=lambda x: x["progress"], reverse=True
        )  # WHY: highest progress first

        print(f"  {'Device Name':<35} {'Type':<8} {'Site':<35} {'Progress':<30}")  # WHY: column headers
        print(f"  {'-' * 35} {'-' * 8} {'-' * 35} {'-' * 30}")  # WHY: header separator

        for device in sorted_upgrading:  # WHY: emit each device row
            self._print_upgrading_device(device)

        print(f"  {'=' * 110}")  # WHY: table bottom border
        self._display_progress_distribution(sorted_upgrading)  # WHY: histogram of progress buckets

    def _print_upgrading_device(self, device: dict[str, Any]) -> None:
        """Print a single upgrading device row."""
        name = device["device_name"] or "Unnamed"  # WHY: fallback display name
        dtype = device["device_type"] or "Unknown"  # WHY: fallback type
        site = device["site_name"] or "Unknown"  # WHY: fallback site
        progress_bar = _MH.DisplayUtils.create_progress_bar(device["progress"], bar_length=15)  # WHY: render bar
        print(f"  {name:<35} {dtype:<8} {site:<35} {progress_bar}")

    @staticmethod
    def _classify_progress_bucket(progress: int) -> str:
        """Return the histogram bucket label for one device progress value."""
        if progress <= 25:  # WHY: first quartile
            return "0-25%"
        if progress <= 50:  # WHY: second quartile
            return "26-50%"
        if progress <= 75:  # WHY: third quartile
            return "51-75%"
        if progress < 100:  # WHY: pre-completion bucket
            return "76-99%"
        return "100%"  # WHY: fully complete

    def _display_progress_distribution(self, sorted_upgrading: list[dict[str, Any]]) -> None:
        """Display progress distribution for upgrading devices."""
        ranges = {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-99%": 0, "100%": 0}  # WHY: histogram buckets
        for device in sorted_upgrading:  # WHY: count each device into its bucket
            bucket = self._classify_progress_bucket(device["progress"])  # WHY: resolve the bucket
            ranges[bucket] += 1  # WHY: increment that bucket
        print("\n  Progress Distribution:")  # WHY: section header
        for range_label, count in ranges.items():  # WHY: print each non-empty bucket
            if count > 0:  # WHY: skip zero buckets to keep output compact
                print(f"   X  {range_label}: {count} device(s)")

    def _check_active_operations(self) -> None:
        """Check for active upgrade operations from various sources."""
        print("\n  Checking for active upgrade operations...")  # WHY: banner

        self._check_ssr_upgrades()  # WHY: SSR upgrades via org endpoint
        self._check_stored_upgrades()  # WHY: stored ActiveUpgrades.json tracker
        self._check_audit_logs()  # WHY: recent audit-log firmware events
        self._check_device_events()  # WHY: SYSTEM_UPGRADE_* device events
        self._check_site_upgrades()  # WHY: per-site upgrade endpoint probe

    def _fetch_ssr_upgrades_payload(self) -> list | None:  # type: ignore[type-arg]
        """Fetch SSR upgrades list; returns list-or-None (empty list signals 'no upgrades')."""
        ssr_resp = mistapi.api.v1.orgs.ssr.listOrgSsrUpgrades(apisession, self.org_id)  # WHY: SSR API call
        if ssr_resp.status_code != 200 or not hasattr(ssr_resp, "data"):  # WHY: HTTP or shape error
            print(f"   -> Failed to retrieve SSR upgrade operations: {ssr_resp.status_code}")  # WHY: user-facing
            return None  # WHY: signal hard failure to caller
        return ssr_resp.data or []  # WHY: empty list keeps caller's truthiness check intact

    def _check_ssr_upgrades(self) -> None:
        """Check for active SSR upgrade operations."""
        try:  # WHY: tolerate transient API failures
            print("   Checking for active SSR upgrade operations...")  # WHY: operator banner
            ssr_upgrades = self._fetch_ssr_upgrades_payload()  # WHY: delegate API call + validation
            if ssr_upgrades is None:  # WHY: hard failure already logged by helper
                return
            if not ssr_upgrades:  # WHY: empty payload -- nothing to process
                print("   -> No active SSR upgrade operations found")
                return
            print(f"   !? Found {len(ssr_upgrades)} SSR upgrade operation(s)")  # WHY: summary count
            for upgrade in ssr_upgrades:  # WHY: process each SSR upgrade record
                self._process_ssr_upgrade(upgrade)
        except Exception as exception:  # WHY: any failure yields graceful warning
            print(f"   -> Error checking SSR upgrade operations: {exception}")
            logging.warning("Failed to check SSR upgrade operations: %s", exception)

    def _record_ssr_upgrade(
        self, upgrade_id: str, status: str, strategy: str, total: int, upgrade: dict[str, Any]
    ) -> None:
        """Append one SSR upgrade record to active_upgrades with org-level placeholder site fields."""
        self.active_upgrades.append(
            {
                "upgrade_id": upgrade_id,
                "site_id": "N/A (Org-level)",
                "site_name": "SSR Upgrade (Org-level)",
                "status": status,
                "strategy": strategy,
                "source": "ssr_api",
                "total_devices": total,
                "details": upgrade,
            }
        )

    def _process_ssr_upgrade(self, upgrade: dict[str, Any]) -> None:
        """Process a single SSR upgrade record."""
        upgrade_id = upgrade.get("id", "Unknown")  # WHY: unique upgrade id
        status = upgrade.get("status", "Unknown")  # WHY: current status
        strategy = upgrade.get("strategy", "Unknown")  # WHY: rollout strategy
        counts = upgrade.get("counts", {})  # WHY: per-status counts
        versions = upgrade.get("versions", {})  # WHY: target versions
        total = sum(counts.values()) if counts else 0  # WHY: total across all status buckets
        status_parts = self._build_ssr_status_parts(counts)  # WHY: per-status display fragments
        version_info = self._build_version_info(versions)  # WHY: target-version display
        status_summary = " | ".join(status_parts) if status_parts else f"Status: {status}"  # WHY: fallback
        print(f"      SSR Upgrade {upgrade_id[:8]}... [{strategy} strategy]: {status_summary}")
        print(f"         Channel: {upgrade.get('channel', 'Unknown')} | Devices: {total} | {version_info}")
        self._record_ssr_upgrade(upgrade_id, status, strategy, total, upgrade)  # WHY: persist record

    def _build_ssr_status_parts(self, counts: dict[str, int]) -> list[str]:
        """Build status parts list for SSR upgrade display."""
        parts = []  # WHY: accumulate non-empty status fragments
        if counts.get("upgrading", 0) > 0:
            parts.append(f"{counts['upgrading']} upgrading")
        if counts.get("success", 0) > 0:
            parts.append(f"{counts['success']} completed")
        if counts.get("failed", 0) > 0:
            parts.append(f"{counts['failed']} failed")
        if counts.get("queued", 0) > 0:
            parts.append(f"{counts['queued']} queued")
        return parts

    def _build_version_info(self, versions: dict[str, str]) -> str:
        """Build version info string from versions mapping."""
        if not versions:  # WHY: default when no version data
            return "Multiple versions"
        target_versions = list(versions.values())  # WHY: extract distinct target values
        if len(target_versions) == 1:  # WHY: single target -> show it directly
            return f"-> {target_versions[0]}"
        return f"Multiple versions ({len(target_versions)} different)"  # WHY: multi-target summary

    def _load_org_upgrades_from_file(self, upgrade_file: str) -> list[dict[str, Any]] | None:
        """Read ``ActiveUpgrades.json`` and return rows matching ``self.org_id`` (``None`` on read error)."""
        try:  # WHY: open + parse tracker file
            with open(upgrade_file, encoding="utf-8") as f:
                stored = json.load(f)  # WHY: deserialize JSON list
        except Exception as exception:  # WHY: tolerate IO/JSON errors
            print(f"   -> Failed to read stored upgrade tracking data: {exception}")
            logging.warning("Failed to read stored upgrade tracking: %s", exception)
            return None  # WHY: signal failure to caller
        return [u for u in stored if u.get("org_id") == self.org_id]  # WHY: filter to current org

    def _check_stored_upgrades(self) -> None:
        """Check stored upgrade IDs from ActiveUpgrades.json."""
        print("   Checking for site-level upgrade operations...")  # WHY: section banner
        upgrade_file = "ActiveUpgrades.json"  # WHY: persistent tracker path
        if not os.path.exists(upgrade_file):  # WHY: no tracker file yet
            print("   -> No site-level upgrade tracking file found")
            return
        org_upgrades = self._load_org_upgrades_from_file(upgrade_file)  # WHY: load + filter to org
        if org_upgrades is None:  # WHY: read/parse failed (logged inside helper)
            return
        if not org_upgrades:  # WHY: empty after filter
            print("   -> No stored upgrades match current organization")
            return
        print(f"   !? Found {len(org_upgrades)} stored upgrade operation(s)")  # WHY: summary
        for record in org_upgrades:  # WHY: probe each tracked upgrade
            self._check_stored_upgrade(record)

    def _record_stored_upgrade(self, upgrade_id: str, site_id: str, site_name: str, details: dict[str, Any]) -> None:
        """Append one stored-upgrade record from a getSiteDeviceUpgrade response into active_upgrades."""
        print(
            f"      Upgrade {upgrade_id[:8]}... at site '{site_name}': Status = {details.get('status', 'Unknown')}"  # noqa: E501
        )
        self.active_upgrades.append(
            {
                "upgrade_id": upgrade_id,
                "site_id": site_id,
                "site_name": site_name,
                "status": details.get("status", "Unknown"),
                "source": "stored_tracking",
                "details": details,
            }
        )

    @staticmethod
    def _safe_get_site_upgrade_data(upgrade_id: str, site_id: str, site_name: str) -> dict[str, Any] | None:
        """Call ``getSiteDeviceUpgrade`` and return ``resp.data`` if present, otherwise ``None``."""
        del site_name  # WHY: kept in signature for symmetry with caller diagnostics
        try:  # WHY: tolerate transient API failures
            resp = mistapi.api.v1.sites.devices.getSiteDeviceUpgrade(apisession, site_id, upgrade_id)  # WHY: API call
        except Exception as exception:  # WHY: any error yields graceful notice
            print(f"      Failed to check upgrade {upgrade_id[:8]}...: {exception}")
            return None
        if resp and hasattr(resp, "data") and resp.data:  # WHY: live upgrade with details present
            return resp.data  # type: ignore[no-any-return]
        return None  # WHY: API returned empty body -> upgrade no longer active

    def _check_stored_upgrade(self, record: dict[str, Any]) -> None:
        """Check status of a stored upgrade record."""
        upgrade_id = record.get("upgrade_id")  # WHY: tracked upgrade id
        site_id = record.get("site_id")  # WHY: site the upgrade ran against
        site_name = record.get("site_name", "Unknown")  # WHY: display name fallback
        if not upgrade_id or not site_id:  # WHY: skip blank tracking rows
            return
        data = type(self)._safe_get_site_upgrade_data(upgrade_id, site_id, site_name)  # WHY: single API call
        if data:  # WHY: still tracked upstream
            self._record_stored_upgrade(upgrade_id, site_id, site_name, data)  # WHY: append to active list
            return
        print(f"      Upgrade {upgrade_id[:8]}... at site '{site_name}': No longer active")  # WHY: stale tracking row

    def _fetch_audit_logs_24h(self) -> list[dict[str, Any]]:
        """Fetch the last 24h of org audit logs (paginated to completion) for upgrade triage."""
        end_time = int(time.time())  # WHY: upper bound = now
        start_time = end_time - (24 * 60 * 60)  # WHY: lower bound = 24h ago
        logging.info("Fetching org audit logs (last 24h) for upgrade triage")  # WHY: log before API
        resp = mistapi.api.v1.orgs.logs.listOrgAuditLogs(
            apisession, self.org_id, start=start_time, end=end_time, limit=1000
        )
        logs = mistapi.get_all(response=resp, mist_session=apisession)  # WHY: paginate to completion
        logging.debug("Org audit logs returned %s entries", len(logs) if logs else 0)  # WHY: log after API
        return logs or []

    def _filter_upgrade_events(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return only the audit-log entries that look like upgrade events."""
        return [log for log in logs if self._is_upgrade_event(log)]  # WHY: delegate per-row predicate

    def _check_audit_logs(self) -> None:
        """Check organization audit logs for recent upgrade events."""
        try:  # WHY: tolerate API or auth errors
            print("   Checking organization audit logs for recent upgrade events...")
            logs = self._fetch_audit_logs_24h()  # WHY: pull the raw 24h window
            if not logs:
                print("   -> No audit logs available for the last 24 hours")
                return
            upgrade_events = self._filter_upgrade_events(logs)  # WHY: delegate keyword filter
            if not upgrade_events:
                print("   -> No upgrade-related events found in audit logs")
                return
            print(f"   !? Found {len(upgrade_events)} upgrade-related audit event(s) in last 24 hours")
            self._display_audit_events(upgrade_events[:5])  # WHY: show first 5
        except Exception as exception:  # WHY: tolerate API or auth errors
            print(f"   -> Error checking audit logs: {exception}")
            logging.warning("Failed to search org audit logs: %s", exception)

    def _is_upgrade_event(self, log_entry: dict[str, Any]) -> bool:
        """Check if log entry is upgrade-related."""
        message = log_entry.get("message", "").lower()  # WHY: case-insensitive match
        return any(kw in message for kw in ["upgrade", "firmware", "version"])  # WHY: keyword predicate

    def _display_audit_events(self, events: list[dict[str, Any]]) -> None:
        """Display recent audit events."""
        for event in sorted(events, key=lambda x: x.get("timestamp", 0), reverse=True):  # WHY: newest first
            timestamp = self._format_timestamp(event.get("timestamp", 0))  # WHY: human-readable time
            admin = event.get("admin_name", "System")  # WHY: actor label
            message = event.get("message", "No message")  # WHY: event text
            site = event.get("site_name", "Organization")  # WHY: scope label
            print(f"      -> {timestamp} | {admin} | {site}: {message[:60]}...")

    def _fetch_device_upgrade_events_24h(self) -> list[dict[str, Any]]:
        """Fetch the last 24h of org-wide SYSTEM_UPGRADE_* device events for upgrade triage."""
        end_time = int(time.time())  # WHY: upper bound = now
        start_time = end_time - (24 * 60 * 60)  # WHY: lower bound = 24h ago
        logging.info("Fetching org device upgrade events (last 24h)")  # WHY: log before API
        resp = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
            apisession,
            self.org_id,
            type="SYSTEM_UPGRADE_COMPLETED,SYSTEM_UPGRADE_FAILED,SYSTEM_UPGRADE_STARTED",
            start=start_time,
            end=end_time,
            limit=50,
        )
        events = mistapi.get_all(response=resp, mist_session=apisession)  # WHY: paginate to completion
        logging.debug("Device upgrade events returned %s entries", len(events) if events else 0)  # WHY: log after API
        return events or []

    def _check_device_events(self) -> None:
        """Check organization device events for upgrade activity."""
        try:  # WHY: tolerate transient API failures
            print("   Checking organization device events for upgrade activity...")
            events = self._fetch_device_upgrade_events_24h()  # WHY: pull the SYSTEM_UPGRADE_* window
            if not events:
                print("   -> No device upgrade events found in last 24 hours")
                return
            print(f"   !? Found {len(events)} device upgrade event(s) in last 24 hours")
            self._display_device_events(events)  # WHY: group + print
        except Exception as exception:  # WHY: tolerate transient API failures
            print(f"   -> Error checking device events: {exception}")
            logging.warning("Failed to search device upgrade events: %s", exception)

    def _display_device_events(self, events: list[dict[str, Any]]) -> None:
        """Display device events grouped by type."""
        by_type: dict[str, list[dict[str, Any]]] = {}  # WHY: group rows by event type
        for event in events:  # WHY: bucket each event
            event_type = event.get("type", "Unknown")
            if event_type not in by_type:
                by_type[event_type] = []
            by_type[event_type].append(event)

        for event_type, type_events in by_type.items():  # WHY: emit one summary line per bucket
            display = event_type.replace("SYSTEM_UPGRADE_", "").title()  # WHY: friendly label
            print(f"      {display}: {len(type_events)} event(s)")

    def _report_sites_without_upgrades(self, total: int, sites_with_upgrades: int) -> None:
        """Print trailing 'N site(s) have no active upgrade operations' when scanning all sites."""
        if self.site_filter:  # WHY: caller scoped to one site -> no summary line needed
            return
        without = total - sites_with_upgrades  # WHY: sites that came back empty
        if without > 0:  # WHY: only print when there's something to report
            print(f"   -> {without} site(s) have no active upgrade operations")

    def _check_site_upgrades(self) -> None:
        """Check individual site upgrade operations."""
        if not self.site_filter:  # WHY: banner only for full-org scan
            print("\n   Checking individual site upgrade operations (first 5 sites)...")
        sites = [self.site_filter] if self.site_filter else list(self.site_lookup.keys())[:5]  # WHY: scope selector
        sites_with_upgrades = 0  # WHY: counter for trailing summary
        for site_id in sites:  # WHY: probe each scoped site
            if self._check_single_site_upgrades(site_id):  # WHY: True -> upgrade(s) found at site
                sites_with_upgrades += 1
        self._report_sites_without_upgrades(len(sites), sites_with_upgrades)  # WHY: emit trailing summary

    def _check_single_site_upgrades(self, site_id: str) -> bool:
        """Check upgrades for a single site. Returns True if upgrades found."""
        site_name = self.site_lookup.get(site_id, "Unknown")  # WHY: friendly site label

        try:  # WHY: tolerate transient API failures
            resp = mistapi.api.v1.sites.devices.listSiteDeviceUpgrades(apisession, site_id)
            upgrades = mistapi.get_all(response=resp, mist_session=apisession)

            if not upgrades:  # WHY: no upgrades at this site
                return False

            print(f"   Site '{site_name}': !? {len(upgrades)} upgrade operation(s)")
            for upgrade in upgrades:  # WHY: process each upgrade row
                self._process_site_upgrade(upgrade, site_id, site_name)
            return True

        except Exception as exception:  # WHY: any error yields graceful warning
            print(f"   Site '{site_name}': -> Error checking upgrades: {exception}")
            logging.warning("Failed to check upgrades for site %s: %s", site_id, exception)
            return False

    def _record_site_upgrade(self, info: dict[str, Any]) -> None:
        """Append one site-upgrade record into active_upgrades; info bundles identity + stage fields."""
        counts = info["counts"]  # WHY: stage-count sub-dict
        self.active_upgrades.append(
            {
                "site_id": info["site_id"],
                "site_name": info["site_name"],
                "upgrade_id": info["upgrade_id"],
                "status": info["status"],
                "strategy": info["strategy"],
                "target_version": info["target"],
                "source": "site_lookup",
                "timestamp": datetime.now(UTC).isoformat(),
                **{k: counts.get(k, 0) for k in ["total", "downloaded", "rebooted", "failed"]},
            }
        )

    def _process_site_upgrade(self, upgrade: dict[str, Any], site_id: str, site_name: str) -> None:
        """Process a single site upgrade record."""
        upgrade_id = upgrade.get("id", "Unknown")  # WHY: unique upgrade id
        status = upgrade.get("status", "Unknown")  # WHY: current status
        strategy = upgrade.get("strategy", "Unknown")  # WHY: rollout strategy
        target = upgrade.get("target_version", "Unknown")  # WHY: target firmware version
        counts = upgrade.get("counts", {})  # WHY: per-stage counts
        progress_parts = self._build_site_upgrade_progress(counts)  # WHY: per-stage display fragments
        progress_info = " | ".join(progress_parts) if progress_parts else f"Status: {status}"  # WHY: fallback
        print(f"      Upgrade {upgrade_id[:8]}... [{strategy}]: {progress_info}")
        print(f"         Target: {target} | Started: {self._format_timestamp(upgrade.get('start_time', 0))}")
        self._record_site_upgrade(
            {
                "upgrade_id": upgrade_id,
                "status": status,
                "strategy": strategy,
                "target": target,
                "counts": counts,
                "site_id": site_id,
                "site_name": site_name,
            }
        )

    def _build_site_upgrade_progress(self, counts: dict[str, int]) -> list[str]:
        """Build progress parts for site upgrade display."""
        parts = []  # WHY: accumulate non-empty progress fragments
        total = counts.get("total", 0)
        if total > 0:  # WHY: only render fragments when a total is known
            if counts.get("downloaded", 0) > 0:
                parts.append(f"{counts['downloaded']}/{total} downloaded")
            if counts.get("rebooted", 0) > 0:
                parts.append(f"{counts['rebooted']}/{total} rebooted")
            if counts.get("failed", 0) > 0:
                parts.append(f"{counts['failed']} failed")
        return parts

    def _export_results(self) -> None:
        """Export results to CSV files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # WHY: shared filename timestamp

        self._export_device_status(timestamp)  # WHY: emit per-device firmware status CSV
        self._export_active_operations(timestamp)  # WHY: emit active-upgrade operations CSV

    def _export_device_status(self, timestamp: str) -> None:
        """Export device firmware status to CSV."""
        if not self.upgrade_results:  # WHY: nothing to export
            return

        filename = f"FirmwareUpgradeStatus_{timestamp}.csv"  # WHY: output filename
        try:  # WHY: tolerate write errors
            _MH.DataExporter.write_with_format_selection(self.upgrade_results, filename)  # WHY: lazy MistHelper attr resolved via _MH proxy
            print(f"\n[SUCCESS] Device firmware status exported to: data/{filename}")
            print(f"   [DATA] {len(self.upgrade_results)} device records exported")
            logging.info("Exported %s device status records", len(self.upgrade_results))  # WHY: audit
        except Exception as exception:  # WHY: tolerate write errors
            print(f"! Failed to export device status: {exception}")
            logging.error("Failed to export device status: %s", exception)

    _ACTIVE_UPGRADE_FIELDNAMES = [  # WHY: canonical CSV header order for active operations
        "site_id",
        "site_name",
        "upgrade_id",
        "status",
        "strategy",
        "target_version",
        "start_time",
        "enable_p2p",
        "total_devices",
        "downloaded",
        "download_requested",
        "rebooted",
        "reboot_in_progress",
        "failed",
        "skipped",
        "source",
        "timestamp",
    ]

    def _export_active_operations(self, timestamp: str) -> None:
        """Export active upgrade operations to CSV."""
        if not self.active_upgrades:  # WHY: nothing to export
            return
        filename = os.path.join("data", f"ActiveUpgradeOperations_{timestamp}.csv")  # WHY: output path
        try:  # WHY: tolerate write errors
            mapped = [self._map_upgrade_for_export(u) for u in self.active_upgrades]  # WHY: project rows
            with open(filename, mode="w", newline="", encoding="utf-8") as f:  # WHY: write CSV
                writer = csv.DictWriter(f, fieldnames=self._ACTIVE_UPGRADE_FIELDNAMES)  # WHY: header set
                writer.writeheader()  # WHY: emit header row
                writer.writerows(mapped)  # WHY: emit data rows
            print(f"! Active upgrade operations exported to: {filename}")
            print(f"   {len(self.active_upgrades)} upgrade operations exported")
            logging.info("Exported %s active upgrade operations", len(self.active_upgrades))  # WHY: audit
        except Exception as exception:  # WHY: tolerate write errors
            print(f"! Failed to export upgrade operations: {exception}")
            logging.error("Failed to export upgrade operations: %s", exception)

    # Export count fields: (export_key, upgrade_top_level_key, details_counts_key). Resolution is
    # `upgrade.get(top_level) or counts.get(counts_key, 0)` -- looped in a helper so the parent stays CC<=5.
    _UPGRADE_COUNT_FIELDS = [
        ("total_devices", "total_devices", "total"),
        ("downloaded", "downloaded", "downloaded"),
        ("download_requested", "download_requested", "download_requested"),
        ("rebooted", "rebooted", "rebooted"),
        ("reboot_in_progress", "reboot_in_progress", "reboot_in_progress"),
        ("failed", "failed", "failed"),
        ("skipped", "skipped", "skipped"),
    ]

    def _map_upgrade_for_export(self, upgrade: dict[str, Any]) -> dict[str, Any]:
        """Map upgrade record for CSV export."""
        details = upgrade.get("details", {})  # WHY: nested details payload (may be empty)
        counts = details.get("counts", {}) if details else {}  # WHY: per-status device counts
        start_time = self._resolve_upgrade_start_time(upgrade, details)  # WHY: formatted start time
        resolved_counts = self._resolve_upgrade_counts(upgrade, counts)  # WHY: per-status count columns
        return {
            "site_id": upgrade.get("site_id", "Unknown"),
            "site_name": upgrade.get("site_name", "Unknown"),
            "upgrade_id": upgrade.get("upgrade_id", "Unknown"),
            "status": upgrade.get("status", "Unknown"),
            "strategy": upgrade.get("strategy", "Unknown"),
            "target_version": upgrade.get("target_version", "Unknown"),
            "start_time": start_time or "Unknown",
            "enable_p2p": upgrade.get("enable_p2p") or details.get("enable_p2p", "Unknown"),
            **resolved_counts,
            "source": upgrade.get("source", "unknown"),
            "timestamp": upgrade.get("timestamp") or datetime.now(UTC).isoformat(),
        }

    def _resolve_upgrade_start_time(self, upgrade: dict[str, Any], details: dict[str, Any]) -> Any:
        """Resolve upgrade start time from top-level or details and format when a positive epoch."""
        start_time = upgrade.get("start_time") or details.get("start_time", 0)  # WHY: pick source
        if isinstance(start_time, (int, float)) and start_time > 0:  # WHY: looks like a usable epoch
            return self._format_timestamp(start_time)  # WHY: format to human-readable string
        return start_time  # WHY: non-epoch value passes through unchanged

    def _resolve_upgrade_counts(self, upgrade: dict[str, Any], counts: dict[str, Any]) -> dict[str, Any]:
        """Resolve each export count column from top-level upgrade, falling back to details counts."""
        return {
            export_key: (upgrade.get(top_key) or counts.get(counts_key, 0))
            for export_key, top_key, counts_key in self._UPGRADE_COUNT_FIELDS
        }

    def _display_recommendations(self) -> None:
        """Display summary and recommendations."""
        print("\n  Summary and Recommendations:")  # WHY: section banner

        if self.summary["upgrade_failed"] > 0:  # WHY: guide operator on failed upgrades
            print(f"   {self.summary['upgrade_failed']} devices have failed upgrades")
            print("   Check failed devices for retry eligibility or manual intervention")

        if self.summary["upgrade_in_progress"] > 0:  # WHY: caution around active upgrades
            print(f"   {self.summary['upgrade_in_progress']} devices currently upgrading")
            print("   Monitor progress and avoid disrupting these devices")

        if len(self.summary["devices_by_version"]) > 3:  # WHY: version-sprawl heuristic
            count = len(self.summary["devices_by_version"])
            print(f"   Multiple firmware versions detected ({count} different versions)")
            print("   Consider standardizing on a consistent firmware version")

        if self.active_upgrades:  # WHY: highlight active operations for follow-up
            print(f"   {len(self.active_upgrades)} active upgrade operations found")
            print("   Monitor upgrade progress in exported CSV files")
        else:
            print("   No active upgrade operations detected")

        print("\n  Status check complete. Check exported CSV files for detailed analysis.")
