"""SSID Template Consolidation — 5-Phase Guided Workflow.

Consolidates per-site WLAN templates into cluster-based templates
using Mist Edge tunnel topology.  Each phase is independently
testable and requires explicit CONFIRM for write operations.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation of forward-referenced deps type

import logging  # WHY: workflow telemetry across all 5 phases
import os  # WHY: file existence checks + path composition
import re  # WHY: pilot-site regex pattern is a class constant
from dataclasses import dataclass  # WHY: bundle 6 injected deps into a frozen struct
from datetime import datetime  # WHY: ISO timestamps for confirmation + cache freshness
from typing import Any  # WHY: broad response typing for mistapi wrappers

import mistapi  # WHY: paginated fetch + REST call factories

from ._ssid_template_cache import (  # WHY: re-export helpers referenced by name in tests
    _cache_age_minutes,  # WHY: re-export for tests + module-level use in _phase1_load_or_fetch
    _check_cache_exists,  # WHY: re-export for backward-compat imports
    _check_prerequisite_for_all,  # WHY: re-export for run-all-phases pre-flight
    _handle_completed_resume,  # WHY: re-export used by parent _offer_resume delegate
    _handle_partial_resume,  # WHY: re-export used by parent _offer_resume delegate
    _SsidTemplateCacheCluster,  # WHY: cache/resume cluster bound in __init__
)
from ._ssid_template_phase1 import (  # WHY: re-export phase 1 helpers referenced by name in tests
    _analyze_group_deviations,  # WHY: re-export for backward-compat imports
    _append_drift_record,  # WHY: re-export for backward-compat imports
    _assemble_site_row,  # WHY: re-export for backward-compat imports
    _build_deviation_record,  # WHY: re-export for backward-compat imports
    _build_mxtunnel_lookup,  # WHY: re-export for backward-compat imports
    _build_site_row,  # WHY: re-export for backward-compat imports
    _build_sitegroup_lookup,  # WHY: re-export for backward-compat imports
    _build_template_lookup,  # WHY: re-export for backward-compat imports
    _classify_site,  # WHY: re-export for backward-compat imports
    _collect_comparison_keys,  # WHY: re-export for backward-compat imports
    _collect_group_wlan_configs,  # WHY: re-export for backward-compat imports
    _collect_key_values,  # WHY: re-export for backward-compat imports
    _detect_cross_cluster_drift,  # WHY: re-export for backward-compat imports
    _determine_target_group,  # WHY: re-export for backward-compat imports
    _find_target_wlan,  # WHY: re-export for backward-compat imports
    _get_template_wlans,  # WHY: re-export for backward-compat imports
    _group_by_target,  # WHY: re-export for backward-compat imports
    _print_phase1_summary,  # WHY: re-export for backward-compat imports
    _resolve_template,  # WHY: re-export for backward-compat imports
    _SiteLookups,  # WHY: re-export dataclass for tests using new _build_site_row signature
    _SsidTemplatePhase1Cluster,  # WHY: phase-1 audit cluster bound in __init__
)
from ._ssid_template_phase2 import (  # WHY: re-export phase 2 helpers referenced by name in tests
    _build_skip_entry,  # WHY: re-export for backward-compat imports
    _build_variable_entry,  # WHY: re-export for backward-compat imports
    _compute_variable_plan,  # WHY: re-export for backward-compat imports
    _display_variable_summary,  # WHY: re-export for backward-compat imports
    _extract_deviation_params,  # WHY: re-export for backward-compat imports
    _get_cached_site_vars,  # WHY: re-export for backward-compat imports
    _group_entries_by_site,  # WHY: re-export for backward-compat imports
    _print_conflicts,  # WHY: re-export for backward-compat imports
    _SsidTemplatePhase2Cluster,  # WHY: phase-2 site-variables cluster bound in __init__
)
from ._ssid_template_phase3 import (  # WHY: re-export phase 3 helpers referenced by name in tests
    _add_pilot_group,  # WHY: re-export for backward-compat imports
    _assign_matrix_sites,  # WHY: re-export for backward-compat imports
    _build_assign_results,  # WHY: re-export for backward-compat imports
    _build_cluster_groups,  # WHY: re-export for backward-compat imports
    _build_failed_assign_results,  # WHY: re-export for backward-compat imports
    _compute_group_plan,  # WHY: re-export for backward-compat imports
    _display_group_plan,  # WHY: re-export for backward-compat imports
    _get_existing_group_site_ids,  # WHY: re-export for backward-compat imports
    _SsidTemplatePhase3Cluster,  # WHY: phase-3 site-groups cluster bound in __init__
)
from ._ssid_template_phase45 import (  # WHY: re-export phase 4/5 helpers referenced by name in tests
    TemplateOpParams,  # WHY: dataclass bundle used by parent's mistapi-touching template helpers
    TemplateOutcome,  # WHY: dataclass bundle used by _template_result
    _build_all_template_configs,  # WHY: re-export for backward-compat imports
    _build_disable_base,  # WHY: re-export for backward-compat imports
    _build_disable_plan,  # WHY: re-export for backward-compat imports
    _build_template_config,  # WHY: re-export for backward-compat imports
    _classify_disable_entry,  # WHY: re-export for backward-compat imports
    _display_disable_plan,  # WHY: re-export for backward-compat imports
    _display_template_plan,  # WHY: re-export for backward-compat imports
    _find_representative,  # WHY: re-export for backward-compat imports
    _load_group_plan_from_results,  # WHY: re-export for backward-compat imports
    _populate_from_representative,  # WHY: re-export for backward-compat imports
    _print_phase_summary,  # WHY: re-export shared per-phase status summary helper
    _resolve_deviations,  # WHY: re-export for backward-compat imports
    _resolve_single_deviation,  # WHY: re-export for backward-compat imports
    _set_ssid_disabled,  # WHY: re-export for backward-compat imports
    _SsidTemplatePhase45Cluster,  # WHY: phase-4/5 templates+disable cluster bound in __init__
)

# WHY: declare the module-level re-export surface so ruff F401 does not flag the
# intentional pass-throughs above (tests reach these helpers by patching them at
# ``ssid_template_consolidation.<name>``, which requires the symbol to bind here).
__all__ = [  # WHY: explicit re-export list. Keeps ruff F401 quiet on intentional pass-throughs
    "SSIDTemplateConsolidationManager",
    "SsidTemplateDeps",
    "TemplateOpParams",
    "TemplateOutcome",
    "_add_pilot_group",
    "_analyze_group_deviations",
    "_append_drift_record",
    "_assemble_site_row",
    "_assign_matrix_sites",
    "_build_all_template_configs",
    "_build_assign_results",
    "_build_cluster_groups",
    "_build_deviation_record",
    "_build_disable_base",
    "_build_disable_plan",
    "_build_failed_assign_results",
    "_build_mxtunnel_lookup",
    "_build_site_row",
    "_build_sitegroup_lookup",
    "_build_skip_entry",
    "_build_template_config",
    "_build_template_lookup",
    "_build_variable_entry",
    "_cache_age_minutes",
    "_check_cache_exists",
    "_check_prerequisite_for_all",
    "_classify_disable_entry",
    "_classify_site",
    "_collect_comparison_keys",
    "_collect_group_wlan_configs",
    "_collect_key_values",
    "_compute_group_plan",
    "_compute_variable_plan",
    "_detect_cross_cluster_drift",
    "_determine_target_group",
    "_display_disable_plan",
    "_display_group_plan",
    "_display_template_plan",
    "_display_variable_summary",
    "_extract_deviation_params",
    "_find_representative",
    "_find_target_wlan",
    "_get_cached_site_vars",
    "_get_existing_group_site_ids",
    "_get_template_wlans",
    "_group_by_target",
    "_group_entries_by_site",
    "_handle_completed_resume",
    "_handle_partial_resume",
    "_load_group_plan_from_results",
    "_populate_from_representative",
    "_print_conflicts",
    "_print_phase1_summary",
    "_print_phase_summary",
    "_resolve_deviations",
    "_resolve_single_deviation",
    "_resolve_template",
    "_set_ssid_disabled",
    "_SiteLookups",
    "_SsidTemplateCacheCluster",
    "_SsidTemplatePhase1Cluster",
    "_SsidTemplatePhase2Cluster",
    "_SsidTemplatePhase3Cluster",
    "_SsidTemplatePhase45Cluster",
]

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
SafeInputFn = Any  # Callable[[str, ...], str]
WriteDataFn = Any  # Callable[[...], None]
GetOrgIdFn = Any  # Callable[[], str | None]


def _fetch_and_log(  # WHY: parent-owned so its __globals__ points here for mistapi test patches
    label: str,
    api_fn: Any,
    session: Any,
    org_id: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Fetch data via API, paginate, and log count.

    Defined in the parent module (rather than re-exported from
    ``_ssid_template_phase1``) so its ``__globals__`` binding is the
    parent module's namespace. That keeps tests that use
    ``patch.object(ssid_template_consolidation, "mistapi", ...)``
    observable when they call ``_mod._fetch_and_log`` directly.
    """
    logging.warning("Fetching %s...", label)  # WHY: operator telemetry during multi-call fetch
    response = api_fn(session, org_id, **kwargs)  # WHY: mistapi list endpoint call
    data: list[dict[str, Any]] = mistapi.get_all(response=response, mist_session=session) or []  # WHY: paginate
    logging.info("%s fetched: %d", label.capitalize(), len(data))  # WHY: audit trail per collection
    return data  # WHY: caller receives the fully paginated list


@dataclass(frozen=True)
class SsidTemplateDeps:  # WHY: frozen dataclass bundle keeps execute() under STRUCT-PARAMS
    """Injected dependencies for :class:`SSIDTemplateConsolidationManager`.

    Bundles the 6 constructor arguments into a single frozen dataclass so
    construction sites and tests build one struct instead of passing 6
    kwargs, and so the parent ``__init__`` stays under the STRUCT-PARAMS
    limit (which Rank 5 established for :class:`DeviceUtilityCommands`).
    """

    org_id: str  # WHY: org scope for every Mist API call
    target_ssid: str  # WHY: the SSID name being consolidated across sites
    apisession: Any  # WHY: mistapi.APISession handle
    page_limit: int  # WHY: paginated fetch limit
    safe_input_fn: SafeInputFn  # WHY: EOF-safe stdin reader
    write_data_fn: WriteDataFn  # WHY: exporter for matrix/deviation/plan tables


class SSIDTemplateConsolidationManager:  # pylint: disable=too-many-instance-attributes
    # WHY: coordinator entry for Menu 159 (5-phase workflow)
    """SSID Template Consolidation (Menu 159) — 5-Phase Guided Workflow.

    Consolidates per-site WLAN templates into cluster-based templates
    using Mist Edge tunnel topology.  Each phase is independently
    testable and requires explicit CONFIRM for write operations.

    Phases:
        1. Read-only audit: collect org data, build matrix, detect deviations
        2. Write site variables: auto-detect + write MISTHELPER_* vars
        3. Create/assign site groups: 4 production + 1 pilot
        4. Create consolidated templates: variable refs for deviations
        5. Disable old SSIDs: set enabled=false on old per-site templates

    Usage:
        SSIDTemplateConsolidationManager.execute(
            apisession=session,
            page_limit=1000,
            safe_input_fn=my_input,
            write_data_fn=my_writer,
            get_org_id_fn=my_org_getter,
        )
    """

    CACHE_FILE = os.path.join("data", "ssid_consolidation_cache.json")  # WHY: on-disk Phase 1 cache
    PHASE_RESULT_FILES = {  # WHY: per-phase result files for --resume support
        2: os.path.join("data", "ssid_consolidation_phase2_results.json"),
        3: os.path.join("data", "ssid_consolidation_phase3_results.json"),
        4: os.path.join("data", "ssid_consolidation_phase4_results.json"),
        5: os.path.join("data", "ssid_consolidation_phase5_results.json"),
    }
    CACHE_FRESHNESS_MINUTES = 60  # WHY: prompt to refetch when cache is older than this
    PSK_AUTH_TYPES = ("psk", "psk-tkip", "psk-wpa2-tkip")  # WHY: PSK auth types are excluded
    METADATA_FIELDS = {  # WHY: fields ignored when comparing WLAN configs for drift
        "id",
        "org_id",
        "site_id",
        "template_id",
        "created_time",
        "modified_time",
    }
    PILOT_PATTERN = re.compile(r"(?i)\b(pilot|test|lab)\b")  # WHY: sites matching this go to pilot group
    CONFIRM_KEYWORD = "CONFIRM"  # WHY: literal typed by operator to unlock write actions

    def __init__(self, deps: SsidTemplateDeps) -> None:  # WHY: single deps bundle keeps ctor lean
        """Initialize with the injected :class:`SsidTemplateDeps` bundle.

        Args:
            deps: Frozen dataclass carrying the 6 dependency values consumed
                by the various phase orchestrators.
        """
        self.org_id = deps.org_id  # WHY: expose as public attr (tests read it)
        self.target_ssid = deps.target_ssid  # WHY: public attr referenced across phases
        self.apisession = deps.apisession  # WHY: public attr used by cluster + phase code
        self.page_limit = deps.page_limit  # WHY: public attr used by fetch helpers
        self.safe_input_fn = deps.safe_input_fn  # WHY: public attr — cache cluster prompts
        self.write_data_fn = deps.write_data_fn  # WHY: public attr — phase exporters
        self.cache: dict[str, Any] = {}  # WHY: Phase 1 org-data cache shared across phases
        self._clusters: tuple[Any, ...] = (  # WHY: bundle clusters so parent stays under R0902 gate
            _SsidTemplateCacheCluster(self),  # WHY: cache + resume + phase-result I/O cluster
            _SsidTemplatePhase1Cluster(self),  # WHY: read-only audit + matrix + deviation cluster
            _SsidTemplatePhase2Cluster(self),  # WHY: site-variables plan + write cluster
            _SsidTemplatePhase3Cluster(self),  # WHY: site-groups plan + create + assign cluster
            _SsidTemplatePhase45Cluster(self),  # WHY: template create/update + disable-old cluster
        )

    def __getattr__(self, name: str) -> Any:  # WHY: proxy unknown attrs to registered clusters
        """Proxy cluster-attribute access to helper clusters.

        Python only invokes ``__getattr__`` when normal lookup fails, so
        this method resolves cluster method calls (``self._load_cache``,
        ``self._save_phase_results``, ``self._offer_resume`` and so on) without
        explicit delegator wrappers. The class-level ``hasattr`` check on
        ``type(cluster)`` avoids invoking the cluster's own ``__getattr__``
        (which would proxy back to this class and cause infinite recursion
        for unknown attrs).
        """
        for cluster in self.__dict__.get("_clusters", ()):  # WHY: iterate bundled clusters
            if hasattr(type(cluster), name):  # WHY: class-level lookup avoids cluster __getattr__ recursion
                return getattr(cluster, name)  # WHY: bound method resolves through cluster
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")  # WHY: no cluster matched

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    @staticmethod
    def execute(  # WHY: sole public entry point invoked by the CLI menu dispatcher
        *,
        apisession: Any,
        page_limit: int,
        safe_input_fn: SafeInputFn,
        write_data_fn: WriteDataFn,
        get_org_id_fn: GetOrgIdFn,
    ) -> None:
        """Menu 159 entry point — prompt for SSID, launch phase menu."""
        logging.warning(
            "=== SSID Template Consolidation (5-Phase Guided Workflow) ==="
        )  # WHY: banner for operator context
        logging.info("Starting SSID Template Consolidation workflow")  # WHY: audit-log workflow entry
        context = SSIDTemplateConsolidationManager._resolve_target_context(  # WHY: extracted for STRUCT-LENGTH
            get_org_id_fn, safe_input_fn
        )
        if context is None:  # WHY: resolver already printed the user-visible reason
            return  # WHY: abort execution when org/ssid resolution failed
        current_org_id, target_ssid = context  # WHY: destructure validated org + ssid pair
        logging.info("Target SSID: %s, Org: %s", target_ssid, current_org_id)  # WHY: audit-log operator inputs
        # fmt: off
        deps = SsidTemplateDeps(  # WHY: bundle 6 deps into frozen struct. STRUCT-LENGTH block
            org_id=current_org_id, target_ssid=target_ssid, apisession=apisession,
            page_limit=page_limit, safe_input_fn=safe_input_fn, write_data_fn=write_data_fn,
        )
        # fmt: on
        SSIDTemplateConsolidationManager(deps).run_phase_menu()  # WHY: hand off to the phase menu loop

    @staticmethod
    def _resolve_target_context(  # WHY: extracted from execute() to satisfy STRUCT-LENGTH
        get_org_id_fn: GetOrgIdFn,
        safe_input_fn: SafeInputFn,
    ) -> tuple[str, str] | None:
        """Resolve (org_id, target_ssid) or None when either is missing."""
        current_org_id: str | None = get_org_id_fn()  # WHY: pull active org from injected getter
        if not current_org_id:
            logging.warning("No organization selected. Exiting.")  # WHY: fail fast when no org is bound
            return None  # WHY: caller treats None as an aborted workflow
        target_ssid = SSIDTemplateConsolidationManager._prompt_target_ssid(safe_input_fn)  # WHY: prompt operator
        if not target_ssid:
            logging.warning("No target SSID specified. Exiting.")  # WHY: empty SSID -> nothing to consolidate
            return None  # WHY: caller treats None as an aborted workflow
        return current_org_id, target_ssid  # WHY: hand off validated pair to execute()

    @staticmethod
    def _prompt_target_ssid(safe_input_fn: SafeInputFn) -> str:  # WHY: split so execute() stays lean
        """Prompt the operator for the target SSID (env default supported)."""
        default_ssid = os.getenv("MIST_TARGET_SSID", "")  # WHY: env override for repeat runs
        prompt = (  # WHY: show default in prompt only when one is set
            f"Enter target SSID name [{default_ssid}]: " if default_ssid else "Enter target SSID name: "
        )
        target_ssid: str = safe_input_fn(  # WHY: EOF-safe stdin reader with context tag
            prompt,
            default_value=default_ssid,
            allow_empty=False,
            context="ssid_consolidation_ssid",
        )
        return target_ssid  # WHY: caller consumes possibly-defaulted SSID name

    # ------------------------------------------------------------------
    # Phase menu
    # ------------------------------------------------------------------

    def run_phase_menu(self) -> None:  # WHY: phase-menu loop used by execute() + tests
        """Display phase sub-menu and dispatch selected phase."""
        phase_labels = {  # WHY: menu row -> human-readable phase description
            "1": "Phase 1: Read-Only Audit (matrix + deviation report)",
            "2": "Phase 2: Write Site Variables",
            "3": "Phase 3: Create / Assign Site Groups",
            "4": "Phase 4: Create Consolidated Templates",
            "5": "Phase 5: Disable Old SSIDs",
            "6": "Run All Phases Sequentially",
        }
        dispatch = self._build_phase_dispatch()  # WHY: menu row -> bound phase handler
        while True:  # WHY: keep prompting until operator quits or selects the all-phases path
            self._display_phase_menu(phase_labels)  # WHY: reprint menu each iteration
            choice = self.safe_input_fn(  # WHY: EOF-safe stdin reader with menu context tag
                "Select phase [1-6, q=quit]: ",
                context="ssid_consolidation_menu",
            )
            if self._handle_menu_choice(choice, dispatch):  # WHY: helper returns True when menu should exit
                return  # WHY: unwind the loop when the choice was terminal (quit / phase 6)

    def _handle_menu_choice(self, choice: str, dispatch: dict[str, Any]) -> bool:  # WHY: extracted so complexity <= 5
        """Route one menu selection. Return True when the menu should exit."""
        if choice.lower() in ("q", "quit", ""):  # WHY: quit tokens include blank enter
            logging.warning("Returning to main menu.")  # WHY: operator feedback before unwinding
            return True  # WHY: signal caller to exit the menu loop
        if choice == "6":  # WHY: 6 = sequential run of all phases
            self._run_all_phases(dispatch)  # WHY: delegates to shared runner
            return True  # WHY: sequential run is terminal like quit
        if choice not in dispatch:  # WHY: guard against typos before int() cast
            logging.warning("Invalid selection: %s", choice)  # WHY: surface the bad token
            return False  # WHY: stay in the menu after typo
        phase_number = int(choice)  # WHY: dispatch keys are digit strings
        if not self._check_prerequisite(phase_number):  # WHY: bail if the preceding phase artifact missing
            return False  # WHY: stay in the menu when prereq check failed
        dispatch[choice]()  # WHY: run the selected phase handler
        return False  # WHY: return to menu after a single phase run

    def _build_phase_dispatch(self) -> dict[str, Any]:  # WHY: menu number -> bound phase handler map
        """Build phase number -> handler mapping."""
        return {  # WHY: five phase entries drive the menu dispatch
            "1": self.phase1_audit,
            "2": self.phase2_site_variables,
            "3": self.phase3_site_groups,
            "4": self.phase4_templates,
            "5": self.phase5_disable_old,
        }

    def _display_phase_menu(self, labels: dict[str, str]) -> None:  # WHY: printer split from loop for clarity
        """Print the numbered phase menu."""
        logging.warning("--- SSID Template Consolidation: %s ---", self.target_ssid)  # WHY: banner shows target SSID
        for key, description in labels.items():  # WHY: iterate the ordered menu rows
            logging.warning("%s. %s", key, description)  # WHY: numbered menu row
        logging.warning("q. Return to main menu")  # WHY: escape hatch back to the top-level CLI

    def _run_all_phases(self, dispatch: dict[str, Any]) -> None:  # WHY: sequential all-phases runner
        """Execute phases 1-5 sequentially, stopping on failure."""
        for phase_key in ("1", "2", "3", "4", "5"):  # WHY: run every phase in order
            phase_number = int(phase_key)  # WHY: dispatch keys are digit strings
            logging.warning("%s", "=" * 60)  # WHY: visual separator between phases
            logging.warning("Starting Phase %d", phase_number)  # WHY: operator sees which phase started
            logging.warning("%s", "=" * 60)  # WHY: closing separator for banner symmetry
            if not _check_prerequisite_for_all(phase_number):  # WHY: gate the phase on its prerequisite artifact
                logging.warning("Phase %d prerequisite not met. Stopping.", phase_number)  # WHY: fail-fast message
                return  # WHY: stop the run-all when prereqs are missing
            try:
                dispatch[phase_key]()  # WHY: invoke the phase's bound handler
            except Exception as error:  # WHY: convert phase failures into operator-visible messages
                logging.exception("Phase %d failed: %s", phase_number, error)  # WHY: audit-log full traceback
                logging.warning("Phase %d failed: %s", phase_number, error)  # WHY: surface the error to the operator
                return  # WHY: halt the sequence on the first failure
        logging.warning("All 5 phases completed successfully.")  # WHY: success message after full sequence

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _confirm_or_cancel(self, summary: str) -> bool:  # WHY: shared CONFIRM gate for write phases
        """Display summary and require CONFIRM to proceed."""
        logging.warning("%s", summary)  # WHY: print the operator-facing plan summary before prompting
        confirmation = self.safe_input_fn(  # WHY: EOF-safe stdin reader with confirmation context tag
            f'Type "{self.CONFIRM_KEYWORD}" to proceed: ',
            context="ssid_consolidation_confirm",
        )
        if confirmation != self.CONFIRM_KEYWORD:  # WHY: literal-match gate blocks accidental writes
            logging.warning("Operation cancelled - confirmation not provided")  # WHY: audit-log cancel
            logging.warning("Operation cancelled.")  # WHY: user-visible cancel message
            return False  # WHY: caller aborts the write path
        logging.info("Operation confirmed at %s", datetime.now().isoformat())  # WHY: audit-log confirmation time
        return True  # WHY: caller proceeds with the write

    # ------------------------------------------------------------------
    # Phase 1: Read-Only Audit (methods live in _ssid_template_phase1.py)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Phase 2: Site Variables
    # ------------------------------------------------------------------
    # WHY: phase2_site_variables + _write_site_variables live on the
    # phase-2 cluster. Access is transparent via __getattr__ delegation.

    # ------------------------------------------------------------------
    # Phase 3: Site Groups
    # ------------------------------------------------------------------
    # WHY: phase3_site_groups + _ensure_groups_exist +
    # _assign_sites_to_groups live on the phase-3 cluster. Access is
    # transparent via __getattr__ delegation.

    # ------------------------------------------------------------------
    # Phase 4: Templates
    # ------------------------------------------------------------------
    # WHY: phase4_templates + _create_or_update_templates live on the
    # phase-4/5 cluster. Access is transparent via __getattr__ delegation.

    # ------------------------------------------------------------------
    # Phase 5: Disable Old SSIDs
    # ------------------------------------------------------------------
    # WHY: phase5_disable_old + _disable_ssids live on the phase-4/5
    # cluster. Access is transparent via __getattr__ delegation.


# ------------------------------------------------------------------
# Phase 2 helpers
# ------------------------------------------------------------------
# WHY: The eight pure Phase-2 helpers (_compute_variable_plan,
# _extract_deviation_params, _build_skip_entry, _get_cached_site_vars,
# _build_variable_entry, _display_variable_summary, _print_conflicts,
# _group_entries_by_site) now live in ``_ssid_template_phase2`` and
# are re-exported from this module's import block at the top of the
# file. Only ``_write_single_site_vars`` stays here because tests
# patch ``mistapi`` through this module's namespace (``patch.object(
# ssid_template_consolidation, "mistapi", ...)``), which only affects
# functions whose ``__globals__`` binding is this module.


def _write_single_site_vars(  # WHY: parent-owned so tests can patch mistapi at this module
    site_id: str,
    entries: list[dict[str, Any]],
    cache: dict[str, Any],
    apisession: Any,
) -> list[dict[str, Any]]:
    """Write variables for a single site via GET-merge-PUT."""
    try:
        existing_vars = _get_cached_site_vars(cache, site_id)  # WHY: pull current per-site vars from cache
        merged_vars = dict(existing_vars)  # WHY: shallow copy so we can additively merge
        for entry in entries:  # WHY: overlay MISTHELPER_* entries onto existing vars
            merged_vars[entry["variable_name"]] = entry["proposed_value"]  # WHY: variable_name -> proposed_value
        mistapi.api.v1.sites.sites.updateSiteInfo(  # WHY: PUT merged vars back to Mist
            apisession, site_id, body={"vars": merged_vars}
        )
        logging.info("Site vars written for %s (%d vars)", site_id, len(entries))  # WHY: audit-log success
        return _build_success_write_results(entries)  # WHY: mark each entry written+timestamp
    except Exception as error:  # WHY: convert API/network failure into structured records
        logging.error("Failed to write vars for site %s: %s", site_id, error)  # WHY: audit-log failure
        return _build_failed_write_results(entries, error)  # WHY: mark each entry failed+reason


def _build_success_write_results(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:  # WHY: success rows builder
    """Build ``status=written`` result records with a shared timestamp."""
    timestamp = datetime.now().isoformat()  # WHY: single ISO timestamp for the batch
    results: list[dict[str, Any]] = []  # WHY: accumulator for the per-entry success rows
    for entry in entries:  # WHY: fan out per-variable success rows
        entry_copy = dict(entry)  # WHY: do not mutate caller's plan entries
        entry_copy["status"] = "written"  # WHY: sentinel consumed by resume logic
        entry_copy["timestamp"] = timestamp  # WHY: record when the write happened
        results.append(entry_copy)  # WHY: collect the success row
    return results  # WHY: caller writes rows to the phase result file


def _build_failed_write_results(  # WHY: failure rows builder mirrors the success builder
    entries: list[dict[str, Any]],
    error: Exception,
) -> list[dict[str, Any]]:
    """Build ``status=failed`` result records carrying the error text."""
    results: list[dict[str, Any]] = []  # WHY: accumulator for the per-entry failure rows
    for entry in entries:  # WHY: fan out per-variable failure rows
        entry_copy = dict(entry)  # WHY: do not mutate caller's plan entries
        entry_copy["status"] = "failed"  # WHY: sentinel consumed by resume + summary logic
        entry_copy["reason"] = str(error)  # WHY: surface stringified error for the report
        results.append(entry_copy)  # WHY: collect the failure row
    return results  # WHY: caller writes rows to the phase result file


# ------------------------------------------------------------------
# Phase 3 helpers
# ------------------------------------------------------------------
# WHY: pure helpers (_compute_group_plan, _build_cluster_groups,
# _add_pilot_group, _assign_matrix_sites, _display_group_plan,
# _build_assign_results, _build_failed_assign_results,
# _get_existing_group_site_ids) live on the phase-3 cluster module
# and are re-exported from this parent for test import continuity.
# _create_site_group and _assign_group_sites stay in the parent so
# their ``mistapi`` name resolution follows the parent module's
# ``__globals__`` — required by tests that use
# ``patch.object(_mod, "mistapi", ...)``.


def _create_site_group(group: dict[str, Any], org_id: str, apisession: Any) -> None:  # WHY: mistapi-touching creator
    """Create a single site group via API."""
    try:
        response = mistapi.api.v1.orgs.sitegroups.createOrgSiteGroup(  # WHY: POST createOrgSiteGroup
            apisession, org_id, body={"name": group["group_name"]}
        )
        created = response.data if hasattr(response, "data") else {}  # WHY: mistapi returns .data
        group["group_id"] = created.get("id", "")  # WHY: cache new id for downstream assignments
        group["exists"] = True  # WHY: flip flag so downstream logic reuses this group
        logging.info(  # WHY: audit-log the successful creation
            "Created group '%s' (id=%s)",
            group["group_name"],
            group["group_id"],
        )
        logging.warning("Created group: %s", group["group_name"])  # WHY: operator feedback for the create
    except Exception as error:  # WHY: convert API/network failure into an audit-log + user message
        logging.error(  # WHY: audit-log the failure with the group name
            "Failed to create group '%s': %s",
            group["group_name"],
            error,
        )
        logging.warning("Failed to create group: %s: %s", group["group_name"], error)  # WHY: user-visible failure line


def _assign_group_sites(  # WHY: mistapi-touching site-group assigner (parent-owned for test patching)
    group: dict[str, Any],
    completed_ids: set[tuple[str, str]],
    cache: dict[str, Any],
    org_id: str,
    apisession: Any,
) -> list[dict[str, Any]]:
    """Assign all sites for a single group."""
    group_id = group["group_id"]  # WHY: id of the sitegroup we are mutating
    sites_to_assign = _filter_pending_sites(group, group_id, completed_ids)  # WHY: strip pairs already done
    if not sites_to_assign:  # WHY: nothing pending -> skip API call entirely
        return []  # WHY: no rows to append to results
    try:
        return _do_assign_group_sites(group, sites_to_assign, cache, org_id, apisession)  # WHY: happy path
    except Exception as error:  # WHY: convert API/network failure into structured records
        logging.error("Failed to assign sites to group '%s': %s", group["group_name"], error)  # WHY: audit-log
        return _build_failed_assign_results(sites_to_assign, group, group_id, error)  # WHY: failure rows


def _filter_pending_sites(  # WHY: split so _assign_group_sites stays under complexity 5
    group: dict[str, Any],
    group_id: str,
    completed_ids: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Return sites whose (site, group) pair is not already completed."""
    return [  # WHY: filter out (site,group) pairs already completed in a prior run
        site for site in group["sites"] if (site["site_id"], group_id) not in completed_ids
    ]


def _do_assign_group_sites(  # WHY: happy-path branch extracted for complexity reduction
    group: dict[str, Any],
    sites_to_assign: list[dict[str, Any]],
    cache: dict[str, Any],
    org_id: str,
    apisession: Any,
) -> list[dict[str, Any]]:
    """Push merged site_ids and build success result rows (may raise)."""
    group_id = group["group_id"]  # WHY: single source of truth for the sitegroup id
    existing_ids = _get_existing_group_site_ids(cache, group_id)  # WHY: preserve unrelated members
    new_ids = [  # WHY: subset that is not already in the group -> triggers the API call
        site["site_id"] for site in sites_to_assign if site["site_id"] not in existing_ids
    ]
    _push_group_site_ids(group, existing_ids, new_ids, org_id, apisession)  # WHY: PUT merged set
    return _build_assign_results(sites_to_assign, existing_ids, group, group_id)  # WHY: success rows


def _push_group_site_ids(  # WHY: mistapi PUT extracted so callers stay slim
    group: dict[str, Any],
    existing_ids: list[str],
    new_ids: list[str],
    org_id: str,
    apisession: Any,
) -> None:
    """PUT merged site_ids to Mist when there is anything new to add."""
    if not new_ids:  # WHY: no-op the API call when everything is already assigned
        return  # WHY: caller still records success rows via _build_assign_results
    merged = list(set(existing_ids + new_ids))  # WHY: union preserves prior members while adding new
    mistapi.api.v1.orgs.sitegroups.updateOrgSiteGroup(  # WHY: additive PUT for the sitegroup
        apisession,
        org_id,
        group["group_id"],
        body={"site_ids": merged},
    )
    logging.info("Updated group '%s' with %d new sites", group["group_name"], len(new_ids))  # WHY: audit-log


# WHY: _build_assign_results, _build_failed_assign_results, and
# _get_existing_group_site_ids live on the phase-3 cluster module and
# are imported at the top of this parent for tests + for the
# ``_assign_group_sites`` helper above.


# ------------------------------------------------------------------
# Phase 4 helpers
# ------------------------------------------------------------------
# WHY: The pure Phase-4 helpers (_resolve_deviations,
# _resolve_single_deviation, _load_group_plan_from_results,
# _build_all_template_configs, _build_template_config,
# _find_representative, _populate_from_representative,
# _display_template_plan) live in ``_ssid_template_phase45`` and are
# re-exported from this module's import block at the top of the file.
# The five mistapi-touching template helpers below stay in the parent
# because tests patch ``mistapi`` through this module's namespace
# (``patch.object(ssid_template_consolidation, "mistapi", ...)``),
# which only intercepts functions whose ``__globals__`` binding is
# this module.


def _create_or_update_single_template(  # WHY: mistapi-touching template dispatcher (parent-owned)
    params: TemplateOpParams,
    existing_templates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Create or update a single template.

    Args:
        params: :class:`TemplateOpParams` bundle carrying the shared
            template create/update state.
        existing_templates: name -> template lookup for the append path.
    """
    existing = existing_templates.get(params.template_name)  # WHY: dispatch on existing template presence
    try:
        return _dispatch_template_op(params, existing)  # WHY: route to append/overwrite/create branch
    except Exception as error:  # WHY: convert exceptions into structured failure records
        logging.error("Template operation failed for '%s': %s", params.template_name, error)  # WHY: audit-log
        return _template_result(params, TemplateOutcome(template_id="", action="failed", error=str(error)))


def _dispatch_template_op(  # WHY: three-branch router keeps complexity of _create_or_update_single_template low
    params: TemplateOpParams,
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    """Route to the append / overwrite / create branch based on state."""
    if existing and params.template_name.startswith("misthelper_"):  # WHY: MistHelper-owned -> additive
        return _append_ssid_to_template(params, existing)  # WHY: safe additive path
    if existing:  # WHY: 3rd-party template -> operator must confirm overwrite
        return _handle_existing_non_misthelper(params)  # WHY: overwrite requires opt-in
    return _create_new_template(params)  # WHY: nothing exists -> plain create


def _handle_existing_non_misthelper(  # WHY: overwrite path split for readability
    params: TemplateOpParams,
) -> dict[str, Any]:
    """Handle template that exists but was not created by this tool."""
    confirm: str = params.safe_input_fn(  # WHY: overwrite requires explicit operator opt-in
        f"  Template '{params.template_name}' exists but was not " f"created by this tool. Overwrite? (y/N): ",
        context="ssid_consolidation_template_overwrite",
    )
    if confirm.strip().lower() not in ("y", "yes"):  # WHY: accept only affirmative yes tokens
        return _template_result(  # WHY: record the skip so the report captures the operator decision
            params,
            TemplateOutcome(template_id="", action="skipped", error="User declined overwrite"),
        )
    return _create_new_template(params)  # WHY: operator confirmed -> proceed with fresh create


def _append_ssid_to_template(  # WHY: additive path for misthelper_-owned templates
    params: TemplateOpParams,
    existing: dict[str, Any],
) -> dict[str, Any]:
    """Append SSID to an existing misthelper template."""
    template_id = existing.get("id", "")  # WHY: existing template id from cache lookup
    template_data = _fetch_template_data(params, template_id, existing)  # WHY: refresh in case cache is stale
    current_wlans: list[dict[str, Any]] = template_data.get("wlans", []) or []  # WHY: empty template edge case

    if _ssid_already_present(current_wlans, params.target_ssid):  # WHY: dedupe idempotently
        return _template_result(  # WHY: record no-op with a clear reason for the report
            params,
            TemplateOutcome(template_id=template_id, action="already_exists", error="SSID already in template"),
        )

    current_wlans.append(params.wlan_config)  # WHY: additive merge preserves other SSIDs
    template_data["wlans"] = current_wlans  # WHY: PUT payload carries the merged wlan list
    mistapi.api.v1.orgs.templates.updateOrgTemplate(  # WHY: PUT updated wlan list back to Mist
        params.apisession, params.org_id, template_id, body=template_data
    )
    logging.info("Appended SSID to template '%s'", params.template_name)  # WHY: audit-log the append
    return _template_result(  # WHY: return updated_append row for the phase report
        params,
        TemplateOutcome(template_id=template_id, action="updated_append"),
    )


def _fetch_template_data(  # WHY: refresh helper isolated for reuse + test patching
    params: TemplateOpParams,
    template_id: str,
    fallback: dict[str, Any],
) -> dict[str, Any]:
    """Fetch fresh template data via getOrgTemplate (fallback to cached copy)."""
    full_response = mistapi.api.v1.orgs.templates.getOrgTemplate(  # WHY: refetch full template body
        params.apisession, params.org_id, template_id
    )
    data: dict[str, Any] = full_response.data if hasattr(full_response, "data") else fallback  # WHY: fallback on stub
    return data  # WHY: caller merges wlans into this payload


def _ssid_already_present(wlans: list[dict[str, Any]], target_ssid: str) -> bool:  # WHY: dedupe predicate
    """Return True when target_ssid already exists in the wlan list (case-insensitive)."""
    lowered = target_ssid.lower()  # WHY: single normalization outside the loop
    return any(wlan.get("ssid", "").lower() == lowered for wlan in wlans)  # WHY: case-insensitive membership


def _create_new_template(  # WHY: fresh-create path (used by initial create + overwrite branch)
    params: TemplateOpParams,
) -> dict[str, Any]:
    """Create a brand new template."""
    group_id = params.group_info.get("group_id", "")  # WHY: bind template to sitegroup when known
    body: dict[str, Any] = {  # WHY: request body for createOrgTemplate
        "name": params.template_name,
        "wlans": [params.wlan_config],
        "applies": ({"sitegroup_ids": [group_id]} if group_id else {}),
    }
    response = mistapi.api.v1.orgs.templates.createOrgTemplate(  # WHY: POST createOrgTemplate
        params.apisession, params.org_id, body=body
    )
    created = response.data if hasattr(response, "data") else {}  # WHY: mistapi returns .data
    template_id: str = created.get("id", "")  # WHY: id returned by createOrgTemplate
    logging.info(  # WHY: audit-log the successful create
        "Created template '%s' (id=%s)",
        params.template_name,
        template_id,
    )
    return _template_result(  # WHY: return created row for the phase report
        params,
        TemplateOutcome(template_id=template_id, action="created"),
    )


def _template_result(  # WHY: unified result-record builder used by every template branch
    params: TemplateOpParams,
    outcome: TemplateOutcome,
) -> dict[str, Any]:
    """Build a template result record."""
    return {  # WHY: schema used by phase result files + summary printers
        "template_name": params.template_name,  # WHY: identity fields sourced from params bundle
        "template_id": outcome.template_id,
        "group_name": params.group_info.get("group_id", ""),
        "group_id": params.group_info.get("group_id", ""),
        "ssid_name": "",
        "action": outcome.action,
        "status": "failed" if outcome.action == "failed" else "success",
        "error": outcome.error,
        "timestamp": params.timestamp,
    }


# ------------------------------------------------------------------
# Phase 5 helpers
# ------------------------------------------------------------------
# WHY: The pure Phase-5 helpers (_build_disable_plan, _classify_disable_entry,
# _build_disable_base, _display_disable_plan, _set_ssid_disabled) live in
# ``_ssid_template_phase45`` and are re-exported from this module's import
# block at the top of the file. Only ``_disable_single_ssid`` stays here
# because tests patch ``mistapi`` through this module's namespace
# (``patch.object(ssid_template_consolidation, "mistapi", ...)``), which only
# intercepts functions whose ``__globals__`` binding is this module.


def _disable_single_ssid(entry: dict[str, Any], org_id: str, apisession: Any) -> dict[str, Any]:
    """Disable a single SSID in its old template."""
    template_id = entry.get("old_template_id", "")  # WHY: identify template holding the SSID
    ssid_id = entry.get("ssid_id", "")  # WHY: identify the WLAN row to disable
    result = dict(entry)  # WHY: copy so we do not mutate the input plan entry
    try:
        _apply_ssid_disable(result, template_id, ssid_id, org_id, apisession)  # WHY: mutates result in place
    except Exception as error:  # WHY: convert API/network failure into structured record
        logging.error("Failed to disable SSID %s in template %s: %s", ssid_id, template_id, error)  # WHY: audit-log
        result["status"] = "failed"  # WHY: sentinel consumed by resume + summary logic
        result["reason"] = str(error)  # WHY: surface stringified error for the report
    return result


def _apply_ssid_disable(
    result: dict[str, Any],
    template_id: str,
    ssid_id: str,
    org_id: str,
    apisession: Any,
) -> None:
    """Fetch template, flip SSID enabled=false, PUT it back (mutates result)."""
    response = mistapi.api.v1.orgs.templates.getOrgTemplate(apisession, org_id, template_id)  # WHY: fetch current
    template_data = response.data if hasattr(response, "data") else {}  # WHY: mistapi returns .data
    wlans: list[dict[str, Any]] = template_data.get("wlans", []) or []  # WHY: empty template edge case
    updated = _set_ssid_disabled(wlans, ssid_id)  # WHY: in-place flip. Returns True if found
    if updated:  # WHY: only PUT + report success when the WLAN row was located
        template_data["wlans"] = wlans  # WHY: PUT payload carries the mutated wlan list
        # fmt: off
        mistapi.api.v1.orgs.templates.updateOrgTemplate(  # WHY: PUT mutated wlans. STRUCT-LENGTH block
            apisession, org_id, template_id, body=template_data,
        )
        # fmt: on
        result["status"] = "disabled"  # WHY: sentinel consumed by resume + summary logic
        result["timestamp"] = datetime.now().isoformat()  # WHY: record when the flip happened
        logging.info("Disabled SSID %s in template %s", ssid_id, template_id)  # WHY: audit-log success
    else:  # WHY: SSID row not in template -> record skip, do not PUT
        result["status"] = "skipped"  # WHY: sentinel consumed by resume + summary logic
        result["reason"] = "SSID not found in template"  # WHY: surface skip reason in the report


# WHY: ``_set_ssid_disabled`` is imported from ``_ssid_template_phase45`` at the
# top of this module (re-exported for backward-compat).  The parent's earlier
# in-file def duplicated the same implementation and triggered mypy no-redef;
# tests still access it via ``_mod._set_ssid_disabled`` because the re-export
# binds the name into this module's namespace.


# ------------------------------------------------------------------
# Shared output helpers
# ------------------------------------------------------------------
# WHY: ``_print_phase_summary`` lives in ``_ssid_template_phase45`` and is
# re-exported at the top of this module. No mistapi calls -> no reason to
# keep a copy in the parent namespace.
