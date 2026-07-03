"""SSID Template Consolidation — 5-Phase Guided Workflow.

Consolidates per-site WLAN templates into cluster-based templates
using Mist Edge tunnel topology.  Each phase is independently
testable and requires explicit CONFIRM for write operations.

Extracted from MistHelper.py for maintainability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation of forward-referenced deps type

import json  # WHY: JSON is the persistence format for cache + phase results
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

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
SafeInputFn = Any  # Callable[[str, ...], str]
WriteDataFn = Any  # Callable[[...], None]
GetOrgIdFn = Any  # Callable[[], str | None]


def _fetch_and_log(
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
    print(f"    Fetching {label}...")  # WHY: operator telemetry during multi-call fetch
    response = api_fn(session, org_id, **kwargs)  # WHY: mistapi list endpoint call
    data: list[dict[str, Any]] = mistapi.get_all(response=response, mist_session=session) or []
    logging.info("%s fetched: %d", label.capitalize(), len(data))  # WHY: audit trail per collection
    return data


@dataclass(frozen=True)
class SsidTemplateDeps:
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


class SSIDTemplateConsolidationManager:
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

    CACHE_FILE = os.path.join("data", "ssid_consolidation_cache.json")
    PHASE_RESULT_FILES = {
        2: os.path.join("data", "ssid_consolidation_phase2_results.json"),
        3: os.path.join("data", "ssid_consolidation_phase3_results.json"),
        4: os.path.join("data", "ssid_consolidation_phase4_results.json"),
        5: os.path.join("data", "ssid_consolidation_phase5_results.json"),
    }
    CACHE_FRESHNESS_MINUTES = 60
    PSK_AUTH_TYPES = ("psk", "psk-tkip", "psk-wpa2-tkip")
    METADATA_FIELDS = {
        "id",
        "org_id",
        "site_id",
        "template_id",
        "created_time",
        "modified_time",
    }
    PILOT_PATTERN = re.compile(r"(?i)\b(pilot|test|lab)\b")
    CONFIRM_KEYWORD = "CONFIRM"

    def __init__(self, deps: SsidTemplateDeps) -> None:
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
        )

    def __getattr__(self, name: str) -> Any:
        """Proxy cluster-attribute access to helper clusters.

        Python only invokes ``__getattr__`` when normal lookup fails, so
        this method resolves cluster method calls (``self._load_cache``,
        ``self._save_phase_results``, ``self._offer_resume`` etc.) without
        explicit delegator wrappers. The class-level ``hasattr`` check on
        ``type(cluster)`` avoids invoking the cluster's own ``__getattr__``
        (which would proxy back to this class and cause infinite recursion
        for unknown attrs).
        """
        for cluster in self.__dict__.get("_clusters", ()):  # WHY: iterate bundled clusters
            if hasattr(type(cluster), name):  # WHY: class-level lookup avoids cluster __getattr__ recursion
                return getattr(cluster, name)  # WHY: bound method resolves through cluster
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    @staticmethod
    def execute(
        *,
        apisession: Any,
        page_limit: int,
        safe_input_fn: SafeInputFn,
        write_data_fn: WriteDataFn,
        get_org_id_fn: GetOrgIdFn,
    ) -> None:
        """Menu 159 entry point — prompt for SSID, launch phase menu."""
        print("\n=== SSID Template Consolidation (5-Phase Guided Workflow) ===")
        logging.info("Starting SSID Template Consolidation workflow")

        current_org_id: str | None = get_org_id_fn()
        if not current_org_id:
            print("! No organization selected. Exiting.")
            return

        default_ssid = os.getenv("MIST_TARGET_SSID", "")
        prompt = f"Enter target SSID name [{default_ssid}]: " if default_ssid else "Enter target SSID name: "
        target_ssid: str = safe_input_fn(
            prompt,
            default_value=default_ssid,
            allow_empty=False,
            context="ssid_consolidation_ssid",
        )
        if not target_ssid:
            print("! No target SSID specified. Exiting.")
            return

        logging.info("Target SSID: %s, Org: %s", target_ssid, current_org_id)
        deps = SsidTemplateDeps(  # WHY: bundle 6 deps into frozen struct for the manager
            org_id=current_org_id,
            target_ssid=target_ssid,
            apisession=apisession,
            page_limit=page_limit,
            safe_input_fn=safe_input_fn,
            write_data_fn=write_data_fn,
        )
        manager = SSIDTemplateConsolidationManager(deps)
        manager.run_phase_menu()

    # ------------------------------------------------------------------
    # Phase menu
    # ------------------------------------------------------------------

    def run_phase_menu(self) -> None:
        """Display phase sub-menu and dispatch selected phase."""
        phase_labels = {
            "1": "Phase 1: Read-Only Audit (matrix + deviation report)",
            "2": "Phase 2: Write Site Variables",
            "3": "Phase 3: Create / Assign Site Groups",
            "4": "Phase 4: Create Consolidated Templates",
            "5": "Phase 5: Disable Old SSIDs",
            "6": "Run All Phases Sequentially",
        }
        dispatch = self._build_phase_dispatch()
        while True:
            self._display_phase_menu(phase_labels)
            choice = self.safe_input_fn(
                "Select phase [1-6, q=quit]: ",
                context="ssid_consolidation_menu",
            )
            if choice.lower() in ("q", "quit", ""):
                print("Returning to main menu.")
                return
            if choice == "6":
                self._run_all_phases(dispatch)
                return
            if choice not in dispatch:
                print(f"! Invalid selection: {choice}")
                continue
            phase_number = int(choice)
            if not self._check_prerequisite(phase_number):
                continue
            dispatch[choice]()

    def _build_phase_dispatch(self) -> dict[str, Any]:
        """Build phase number -> handler mapping."""
        return {
            "1": self.phase1_audit,
            "2": self.phase2_site_variables,
            "3": self.phase3_site_groups,
            "4": self.phase4_templates,
            "5": self.phase5_disable_old,
        }

    def _display_phase_menu(self, labels: dict[str, str]) -> None:
        """Print the numbered phase menu."""
        print(f"\n--- SSID Template Consolidation: {self.target_ssid} ---")
        for key, description in labels.items():
            print(f"  {key}. {description}")
        print("  q. Return to main menu")

    def _run_all_phases(self, dispatch: dict[str, Any]) -> None:
        """Execute phases 1-5 sequentially, stopping on failure."""
        for phase_key in ("1", "2", "3", "4", "5"):
            phase_number = int(phase_key)
            print(f"\n{'=' * 60}")
            print(f"  Starting Phase {phase_number}")
            print(f"{'=' * 60}")
            if not _check_prerequisite_for_all(phase_number):
                print(f"! Phase {phase_number} prerequisite not met. Stopping.")
                return
            try:
                dispatch[phase_key]()
            except Exception as error:
                logging.exception("Phase %d failed: %s", phase_number, error)
                print(f"! Phase {phase_number} failed: {error}")
                return
        print("\nAll 5 phases completed successfully.")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _confirm_or_cancel(self, summary: str) -> bool:
        """Display summary and require CONFIRM to proceed."""
        print(f"\n{summary}")
        confirmation = self.safe_input_fn(
            f'Type "{self.CONFIRM_KEYWORD}" to proceed: ',
            context="ssid_consolidation_confirm",
        )
        if confirmation != self.CONFIRM_KEYWORD:
            logging.warning("Operation cancelled - confirmation not provided")
            print("! Operation cancelled.")
            return False
        logging.info("Operation confirmed at %s", datetime.now().isoformat())
        return True

    # ------------------------------------------------------------------
    # Phase 1: Read-Only Audit (methods live in _ssid_template_phase1.py)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Phase 2: Site Variables
    # ------------------------------------------------------------------
    # WHY: phase2_site_variables + _write_site_variables live on the
    # phase-2 cluster; access is transparent via __getattr__ delegation.

    # ------------------------------------------------------------------
    # Phase 3: Site Groups
    # ------------------------------------------------------------------
    # WHY: phase3_site_groups + _ensure_groups_exist +
    # _assign_sites_to_groups live on the phase-3 cluster; access is
    # transparent via __getattr__ delegation.

    # ------------------------------------------------------------------
    # Phase 4: Templates
    # ------------------------------------------------------------------

    def phase4_templates(self) -> None:
        """Phase 4 orchestrator — resolve deviations, create templates."""
        print("\n=== Phase 4: Create Consolidated Templates ===")
        logging.info("Phase 4: Starting template creation")

        cached = self._load_cache()
        if not cached:
            print("! Phase 1 cache not found. Run Phase 1 first.")
            return
        self.cache = cached

        phase3_results = self._load_phase_results(3)
        if not phase3_results:
            print("! Phase 3 results not found. Run Phase 3 first.")
            return

        resolutions = _resolve_deviations(self.cache, self.safe_input_fn)
        group_plan = _load_group_plan_from_results(phase3_results)
        configs = _build_all_template_configs(group_plan, resolutions, self.cache, self.target_ssid)

        _display_template_plan(configs, group_plan)
        if not self._confirm_or_cancel(f"Create/update {len(configs)} templates?"):
            return

        results = self._create_or_update_templates(configs, group_plan)
        self._save_phase_results(4, results)
        self.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_templates",
            api_function_name="ssidConsolidationTemplates",
        )
        _print_phase_summary("Phase 4", results)

    def _create_or_update_templates(
        self,
        configs: dict[str, dict[str, Any]],
        group_plan: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Create or update templates for each group."""
        basename = os.environ.get("MIST_TEMPLATE_BASENAME", self.target_ssid)
        existing_templates = {
            tmpl.get("name", ""): tmpl for tmpl in self.cache.get("data", {}).get("wlan_templates", [])
        }
        results: list[dict[str, Any]] = []

        for group_name, config in configs.items():
            group_info = group_plan.get(group_name, {})
            template_name = f"misthelper_{group_name}_{basename}"
            result = _create_or_update_single_template(
                template_name,
                config,
                group_info,
                existing_templates,
                self.target_ssid,
                self.org_id,
                self.apisession,
                self.safe_input_fn,
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Phase 5: Disable Old SSIDs
    # ------------------------------------------------------------------

    def phase5_disable_old(self) -> None:
        """Phase 5 orchestrator — disable matching SSIDs in old templates."""
        print("\n=== Phase 5: Disable Old SSIDs ===")
        logging.info("Phase 5: Starting old SSID disable")

        cached = self._load_cache()
        if not cached:
            print("! Phase 1 cache not found. Run Phase 1 first.")
            return
        self.cache = cached

        resuming, prior_results = self._offer_resume(5, [])
        plan = _build_disable_plan(self.cache)
        to_disable = [entry for entry in plan if entry["status"] == "to_disable"]

        _display_disable_plan(plan)
        if not to_disable:
            print("  No SSIDs to disable.")
            return
        if not self._confirm_or_cancel(f"Disable {len(to_disable)} SSIDs in old templates?"):
            return

        results = self._disable_ssids(plan, prior_results if resuming else [])
        self._save_phase_results(5, results)
        self.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_disable",
            api_function_name="ssidConsolidationDisable",
        )
        _print_phase_summary("Phase 5", results)

    def _disable_ssids(
        self,
        plan: list[dict[str, Any]],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Disable SSIDs in old templates via GET-modify-PUT."""
        completed_ids = {
            (row.get("site_id"), row.get("ssid_id")) for row in resume_from if row.get("status") == "disabled"
        }
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []

        for entry in plan:
            if entry["status"] != "to_disable":
                key = (entry.get("site_id"), entry.get("ssid_id"))
                if key not in completed_ids:
                    results.append(entry)
                continue
            key = (entry.get("site_id"), entry.get("ssid_id"))
            if key in completed_ids:
                continue
            result = _disable_single_ssid(entry, self.org_id, self.apisession)
            results.append(result)
            if len(results) % 10 == 0:
                self._save_phase_results(5, results)
        return results


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


def _write_single_site_vars(
    site_id: str,
    entries: list[dict[str, Any]],
    cache: dict[str, Any],
    apisession: Any,
) -> list[dict[str, Any]]:
    """Write variables for a single site via GET-merge-PUT."""
    results: list[dict[str, Any]] = []
    try:
        existing_vars = _get_cached_site_vars(cache, site_id)
        merged_vars = dict(existing_vars)
        for entry in entries:
            merged_vars[entry["variable_name"]] = entry["proposed_value"]

        mistapi.api.v1.sites.sites.updateSiteInfo(apisession, site_id, body={"vars": merged_vars})
        timestamp = datetime.now().isoformat()
        for entry in entries:
            entry_copy = dict(entry)
            entry_copy["status"] = "written"
            entry_copy["timestamp"] = timestamp
            results.append(entry_copy)
        logging.info(
            "Site vars written for %s (%d vars)",
            site_id,
            len(entries),
        )
    except Exception as error:
        logging.error("Failed to write vars for site %s: %s", site_id, error)
        for entry in entries:
            entry_copy = dict(entry)
            entry_copy["status"] = "failed"
            entry_copy["reason"] = str(error)
            results.append(entry_copy)
    return results


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


def _create_site_group(group: dict[str, Any], org_id: str, apisession: Any) -> None:
    """Create a single site group via API."""
    try:
        response = mistapi.api.v1.orgs.sitegroups.createOrgSiteGroup(
            apisession, org_id, body={"name": group["group_name"]}
        )
        created = response.data if hasattr(response, "data") else {}
        group["group_id"] = created.get("id", "")
        group["exists"] = True
        logging.info(
            "Created group '%s' (id=%s)",
            group["group_name"],
            group["group_id"],
        )
        print(f"  Created group: {group['group_name']}")
    except Exception as error:
        logging.error(
            "Failed to create group '%s': %s",
            group["group_name"],
            error,
        )
        print(f"  ! Failed to create group: " f"{group['group_name']}: {error}")


def _assign_group_sites(
    group: dict[str, Any],
    completed_ids: set[tuple[str, str]],
    cache: dict[str, Any],
    org_id: str,
    apisession: Any,
) -> list[dict[str, Any]]:
    """Assign all sites for a single group."""
    group_id = group["group_id"]
    group_name = group["group_name"]
    sites_to_assign = [site for site in group["sites"] if (site["site_id"], group_id) not in completed_ids]
    if not sites_to_assign:
        return []

    try:
        existing_ids = _get_existing_group_site_ids(cache, group_id)
        new_ids = [site["site_id"] for site in sites_to_assign if site["site_id"] not in existing_ids]
        merged = list(set(existing_ids + new_ids))

        if new_ids:
            mistapi.api.v1.orgs.sitegroups.updateOrgSiteGroup(
                apisession,
                org_id,
                group_id,
                body={"site_ids": merged},
            )
            logging.info(
                "Updated group '%s' with %d new sites",
                group_name,
                len(new_ids),
            )

        return _build_assign_results(sites_to_assign, existing_ids, group, group_id)
    except Exception as error:
        logging.error(
            "Failed to assign sites to group '%s': %s",
            group_name,
            error,
        )
        return _build_failed_assign_results(sites_to_assign, group, group_id, error)


# WHY: _build_assign_results, _build_failed_assign_results, and
# _get_existing_group_site_ids live on the phase-3 cluster module and
# are imported at the top of this parent for tests + for the
# ``_assign_group_sites`` helper above.


# ------------------------------------------------------------------
# Phase 4 helpers
# ------------------------------------------------------------------


def _resolve_deviations(cache: dict[str, Any], safe_input_fn: SafeInputFn) -> dict[tuple[str, str], Any]:
    """Interactively resolve deviations — no pre-selected default."""
    deviations = cache.get("deviations", [])
    resolutions: dict[tuple[str, str], Any] = {}

    for deviation in deviations:
        if deviation.get("cluster_name") == "cross_cluster":
            continue
        _resolve_single_deviation(deviation, resolutions, safe_input_fn)
    return resolutions


def _resolve_single_deviation(
    deviation: dict[str, Any],
    resolutions: dict[tuple[str, str], Any],
    safe_input_fn: SafeInputFn,
) -> None:
    """Resolve a single deviation interactively."""
    cluster = deviation.get("cluster_name", "")
    param = deviation.get("parameter", "")
    unique_values: list[dict[str, Any]] = json.loads(deviation.get("unique_values", "[]"))

    print(f"\n  Deviation: {param} in cluster '{cluster}'")
    for index, entry in enumerate(unique_values, 1):
        sites_preview = ", ".join(entry["sites"][:3])
        print(f"    {index}. {entry['value']} " f"({entry['count']} sites: {sites_preview})")
        if len(entry["sites"]) > 3:
            remaining = len(entry["sites"]) - 3
            print(f"       ... and {remaining} more sites")

    choice: str = safe_input_fn(
        f"  Select canonical value [1-{len(unique_values)}]: ",
        context="ssid_consolidation_deviation_resolution",
    )
    try:
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(unique_values):
            selected = unique_values[selected_index]["value"]
            resolutions[(cluster, param)] = selected
            logging.info(
                "Deviation resolved: %s/%s = %s " "(selected from %d options at %s)",
                cluster,
                param,
                selected,
                len(unique_values),
                datetime.now().isoformat(),
            )
        else:
            print(f"  ! Invalid selection. Skipping {param}.")
    except ValueError:
        print(f"  ! Invalid input. Skipping {param}.")


def _load_group_plan_from_results(
    phase3_results: dict[str, Any],
) -> dict[str, dict[str, str]]:
    """Extract group_name -> group_id mapping from Phase 3 results."""
    group_map: dict[str, dict[str, str]] = {}
    for result in phase3_results.get("results", []):
        group_name = result.get("group_name", "")
        if group_name and group_name not in group_map:
            group_map[group_name] = {
                "group_id": result.get("group_id", ""),
                "cluster_name": result.get("cluster_name", ""),
            }
    return group_map


def _build_all_template_configs(
    group_plan: dict[str, dict[str, str]],
    resolutions: dict[tuple[str, str], Any],
    cache: dict[str, Any],
    target_ssid: str,
) -> dict[str, dict[str, Any]]:
    """Build WLAN configs for each group's template."""
    configs: dict[str, dict[str, Any]] = {}
    for group_name, group_info in group_plan.items():
        cluster = group_info.get("cluster_name", "")
        config = _build_template_config(cluster, resolutions, cache, target_ssid)
        configs[group_name] = config
    return configs


def _build_template_config(
    cluster_name: str,
    resolutions: dict[tuple[str, str], Any],
    cache: dict[str, Any],
    target_ssid: str,
) -> dict[str, Any]:
    """Build a single WLAN config with variable refs for deviations."""
    deviations = cache.get("deviations", [])
    deviation_params = {
        dev.get("parameter")
        for dev in deviations
        if dev.get("cluster_name") == cluster_name and dev.get("cluster_name") != "cross_cluster"
    }

    representative = _find_representative(cache, cluster_name)
    config: dict[str, Any] = {
        "ssid": target_ssid,
        "enabled": True,
    }
    if representative:
        _populate_from_representative(config, representative, deviation_params)

    for param in deviation_params:
        if param not in ("vlan_id",):
            config[param] = f"{{{{MISTHELPER_{param.upper()}}}}}"
    return config


def _find_representative(cache: dict[str, Any], cluster_name: str) -> dict[str, Any] | None:
    """Find a representative matrix row for the cluster."""
    matrix: list[dict[str, Any]] = cache.get("matrix", [])
    for row in matrix:
        if row.get("target_group") == cluster_name and not row.get("anomaly") and not row.get("psk_detected"):
            return row
    for row in matrix:
        if row.get("target_group") == "pilot" and not row.get("anomaly") and not row.get("psk_detected"):
            return row
    return None


def _populate_from_representative(
    config: dict[str, Any],
    representative: dict[str, Any],
    deviation_params: set[str | None],
) -> None:
    """Populate template config from representative row."""
    if "vlan_id" in deviation_params:
        config["vlan_id"] = "{{MISTHELPER_VLAN_ID}}"
    else:
        config["vlan_id"] = representative.get("vlan_id", "")
    config["auth"] = {"type": representative.get("auth_type", "")}
    mxtunnel_id = representative.get("mxtunnel_id", "")
    if mxtunnel_id:
        config["mxtunnel_ids"] = [mxtunnel_id]


def _display_template_plan(
    configs: dict[str, dict[str, Any]],
    group_plan: dict[str, dict[str, str]],
) -> None:
    """Print template creation plan."""
    print("\n  Template Plan:")
    for group_name, config in configs.items():
        group_info = group_plan.get(group_name, {})
        group_id = group_info.get("group_id", "new")
        print(f"    {group_name} (group_id={group_id})")
        print(f"      SSID: {config.get('ssid', '')}")
        for key, value in config.items():
            if key != "ssid":
                print(f"      {key}: {value}")


def _create_or_update_single_template(
    template_name: str,
    wlan_config: dict[str, Any],
    group_info: dict[str, str],
    existing_templates: dict[str, dict[str, Any]],
    target_ssid: str,
    org_id: str,
    apisession: Any,
    safe_input_fn: SafeInputFn,
) -> dict[str, Any]:
    """Create or update a single template."""
    group_id = group_info.get("group_id", "")
    timestamp = datetime.now().isoformat()
    existing = existing_templates.get(template_name)

    try:
        if existing and template_name.startswith("misthelper_"):
            return _append_ssid_to_template(
                existing,
                wlan_config,
                template_name,
                group_info,
                timestamp,
                target_ssid,
                org_id,
                apisession,
            )
        if existing:
            return _handle_existing_non_misthelper(
                template_name,
                wlan_config,
                group_id,
                group_info,
                timestamp,
                org_id,
                apisession,
                safe_input_fn,
            )
        return _create_new_template(
            template_name,
            wlan_config,
            group_id,
            group_info,
            timestamp,
            org_id,
            apisession,
        )
    except Exception as error:
        logging.error(
            "Template operation failed for '%s': %s",
            template_name,
            error,
        )
        return _template_result(template_name, "", group_info, "failed", str(error), timestamp)


def _handle_existing_non_misthelper(
    template_name: str,
    wlan_config: dict[str, Any],
    group_id: str,
    group_info: dict[str, str],
    timestamp: str,
    org_id: str,
    apisession: Any,
    safe_input_fn: SafeInputFn,
) -> dict[str, Any]:
    """Handle template that exists but was not created by this tool."""
    confirm: str = safe_input_fn(
        f"  Template '{template_name}' exists but was not " f"created by this tool. Overwrite? (y/N): ",
        context="ssid_consolidation_template_overwrite",
    )
    if confirm.strip().lower() not in ("y", "yes"):
        return _template_result(
            template_name,
            "",
            group_info,
            "skipped",
            "User declined overwrite",
            timestamp,
        )
    return _create_new_template(
        template_name,
        wlan_config,
        group_id,
        group_info,
        timestamp,
        org_id,
        apisession,
    )


def _append_ssid_to_template(
    existing: dict[str, Any],
    wlan_config: dict[str, Any],
    template_name: str,
    group_info: dict[str, str],
    timestamp: str,
    target_ssid: str,
    org_id: str,
    apisession: Any,
) -> dict[str, Any]:
    """Append SSID to an existing misthelper template."""
    template_id = existing.get("id", "")
    full_response = mistapi.api.v1.orgs.templates.getOrgTemplate(apisession, org_id, template_id)
    template_data = full_response.data if hasattr(full_response, "data") else existing
    current_wlans: list[dict[str, Any]] = template_data.get("wlans", []) or []

    for wlan in current_wlans:
        if wlan.get("ssid", "").lower() == target_ssid.lower():
            return _template_result(
                template_name,
                template_id,
                group_info,
                "already_exists",
                "SSID already in template",
                timestamp,
            )

    current_wlans.append(wlan_config)
    template_data["wlans"] = current_wlans
    mistapi.api.v1.orgs.templates.updateOrgTemplate(apisession, org_id, template_id, body=template_data)
    logging.info("Appended SSID to template '%s'", template_name)
    return _template_result(
        template_name,
        template_id,
        group_info,
        "updated_append",
        "",
        timestamp,
    )


def _create_new_template(
    template_name: str,
    wlan_config: dict[str, Any],
    group_id: str,
    group_info: dict[str, str],
    timestamp: str,
    org_id: str,
    apisession: Any,
) -> dict[str, Any]:
    """Create a brand new template."""
    body: dict[str, Any] = {
        "name": template_name,
        "wlans": [wlan_config],
        "applies": ({"sitegroup_ids": [group_id]} if group_id else {}),
    }
    response = mistapi.api.v1.orgs.templates.createOrgTemplate(apisession, org_id, body=body)
    created = response.data if hasattr(response, "data") else {}
    template_id: str = created.get("id", "")
    logging.info(
        "Created template '%s' (id=%s)",
        template_name,
        template_id,
    )
    return _template_result(
        template_name,
        template_id,
        group_info,
        "created",
        "",
        timestamp,
    )


def _template_result(
    name: str,
    template_id: str,
    group_info: dict[str, str],
    action: str,
    error: str,
    timestamp: str,
) -> dict[str, Any]:
    """Build a template result record."""
    return {
        "template_name": name,
        "template_id": template_id,
        "group_name": group_info.get("group_id", ""),
        "group_id": group_info.get("group_id", ""),
        "ssid_name": "",
        "action": action,
        "status": "failed" if action == "failed" else "success",
        "error": error,
        "timestamp": timestamp,
    }


# ------------------------------------------------------------------
# Phase 5 helpers
# ------------------------------------------------------------------


def _build_disable_plan(
    cache: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build plan for disabling old SSIDs."""
    matrix = cache.get("matrix", [])
    plan: list[dict[str, Any]] = []
    for row in matrix:
        plan.append(_classify_disable_entry(row))
    return plan


def _classify_disable_entry(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Classify a single site for disable action."""
    base = _build_disable_base(row)
    if row.get("psk_detected"):
        base["status"] = "skipped"
        base["reason"] = "PSK site"
        return base
    if row.get("anomaly"):
        base["status"] = "skipped"
        base["reason"] = f"Anomaly: {row.get('anomaly_reason', '')}"
        return base
    if not row.get("ssid_enabled", True):
        base["status"] = "already_disabled"
        base["reason"] = "SSID already disabled"
        return base
    if not row.get("ssid_id"):
        base["status"] = "skipped"
        base["reason"] = "No SSID ID found"
        return base
    base["status"] = "to_disable"
    base["reason"] = ""
    return base


def _build_disable_base(row: dict[str, Any]) -> dict[str, Any]:
    """Build base dictionary for a disable plan entry."""
    return {
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "old_template_name": row.get("template_name", ""),
        "old_template_id": row.get("template_id", ""),
        "ssid_name": row.get("ssid_name", ""),
        "ssid_id": row.get("ssid_id", ""),
        "previous_enabled": row.get("ssid_enabled", True),
        "timestamp": "",
    }


def _display_disable_plan(
    plan: list[dict[str, Any]],
) -> None:
    """Print disable plan summary."""
    to_disable = [e for e in plan if e["status"] == "to_disable"]
    already = [e for e in plan if e["status"] == "already_disabled"]
    skipped = [e for e in plan if e["status"] == "skipped"]

    print("\n  Disable Plan:")
    print(f"    To disable:       {len(to_disable)}")
    print(f"    Already disabled: {len(already)}")
    print(f"    Skipped:          {len(skipped)}")


def _disable_single_ssid(entry: dict[str, Any], org_id: str, apisession: Any) -> dict[str, Any]:
    """Disable a single SSID in its old template."""
    template_id = entry.get("old_template_id", "")
    ssid_id = entry.get("ssid_id", "")
    result = dict(entry)
    try:
        response = mistapi.api.v1.orgs.templates.getOrgTemplate(apisession, org_id, template_id)
        template_data = response.data if hasattr(response, "data") else {}
        wlans: list[dict[str, Any]] = template_data.get("wlans", []) or []

        updated = _set_ssid_disabled(wlans, ssid_id)
        if updated:
            template_data["wlans"] = wlans
            mistapi.api.v1.orgs.templates.updateOrgTemplate(apisession, org_id, template_id, body=template_data)
            result["status"] = "disabled"
            result["timestamp"] = datetime.now().isoformat()
            logging.info(
                "Disabled SSID %s in template %s",
                ssid_id,
                template_id,
            )
        else:
            result["status"] = "skipped"
            result["reason"] = "SSID not found in template"
    except Exception as error:
        logging.error(
            "Failed to disable SSID %s in template %s: %s",
            ssid_id,
            template_id,
            error,
        )
        result["status"] = "failed"
        result["reason"] = str(error)
    return result


def _set_ssid_disabled(wlans: list[dict[str, Any]], ssid_id: str) -> bool:
    """Set enabled=False on the matching SSID. Returns True if found."""
    for wlan in wlans:
        if wlan.get("id") == ssid_id:
            wlan["enabled"] = False
            return True
    return False


# ------------------------------------------------------------------
# Shared output helpers
# ------------------------------------------------------------------


def _print_phase_summary(phase_label: str, results: list[dict[str, Any]]) -> None:
    """Print a summary of phase results by status."""
    status_counts: dict[str, int] = {}
    for result in results:
        status = result.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"\n  {phase_label} Summary:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")
