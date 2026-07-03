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
    _SsidTemplateCacheCluster,  # WHY: cache/resume cluster bound in __init__
    _cache_age_minutes,  # WHY: re-export for tests + module-level use in _phase1_load_or_fetch
    _check_cache_exists,  # WHY: re-export for backward-compat imports
    _check_prerequisite_for_all,  # WHY: re-export for run-all-phases pre-flight
    _handle_completed_resume,  # WHY: re-export used by parent _offer_resume delegate
    _handle_partial_resume,  # WHY: re-export used by parent _offer_resume delegate
)

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
SafeInputFn = Any  # Callable[[str, ...], str]
WriteDataFn = Any  # Callable[[...], None]
GetOrgIdFn = Any  # Callable[[], str | None]


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
    # Phase 1: Read-Only Audit
    # ------------------------------------------------------------------

    def phase1_audit(self) -> None:
        """Phase 1 orchestrator — fetch data, build matrix, analyze."""
        print("\n=== Phase 1: Read-Only Audit ===")
        logging.info(
            "Phase 1: Starting read-only audit for SSID '%s'",
            self.target_ssid,
        )

        org_data = self._phase1_load_or_fetch()
        if not org_data:
            print("! Failed to load or fetch organization data.")
            return

        matrix = self._build_matrix(org_data)
        deviations = self._analyze_deviations(matrix, org_data)
        self._phase1_save_and_report(org_data, matrix, deviations)

    def _phase1_load_or_fetch(self) -> dict[str, Any] | None:
        """Load cached data or fetch fresh from API."""
        cached = self._load_cache()  # WHY: cache cluster proxy returns dict[str, Any] | None
        if cached and cached.get("data"):
            age = _cache_age_minutes(cached.get("collected_at", ""))
            print(f"  Cached data found ({age:.0f} minutes old).")
            choice = self.safe_input_fn(
                "  Use cached data? (Y/n): ",
                default_value="Y",
                context="ssid_consolidation_cache_reuse",
            )
            if choice.strip().lower() not in ("n", "no"):
                logging.info("Using cached org data")
                cached_data: dict[str, Any] | None = cached.get("data")  # WHY: proxy erases type -> narrow
                return cached_data
        print("  Fetching fresh organization data...")
        return self._fetch_all_org_data()

    def _phase1_save_and_report(
        self,
        org_data: dict[str, Any],
        matrix: list[dict[str, Any]],
        deviations: list[dict[str, Any]],
    ) -> None:
        """Save Phase 1 outputs and print summary."""
        cache_payload: dict[str, Any] = {
            "data": org_data,
            "matrix": matrix,
            "deviations": deviations,
        }
        self._save_cache(cache_payload)

        self.write_data_fn(
            data=matrix,
            filename_or_table="ssid_consolidation_matrix",
            api_function_name="ssidConsolidationMatrix",
        )
        self.write_data_fn(
            data=deviations,
            filename_or_table="ssid_consolidation_deviations",
            api_function_name="ssidConsolidationDeviation",
        )

        _print_phase1_summary(matrix, deviations)

    def _fetch_all_org_data(self) -> dict[str, Any]:
        """Fetch all org data using 5 bulk API calls."""
        result: dict[str, Any] = {}
        session = self.apisession

        result["wlan_templates"] = _fetch_and_log(
            "templates",
            mistapi.api.v1.orgs.templates.listOrgTemplates,
            session,
            self.org_id,
        )
        result["org_wlans"] = _fetch_and_log(
            "org WLANs",
            mistapi.api.v1.orgs.wlans.listOrgWlans,
            session,
            self.org_id,
            limit=self.page_limit,
        )
        result["sites"] = _fetch_and_log(
            "sites",
            mistapi.api.v1.orgs.sites.listOrgSites,
            session,
            self.org_id,
            limit=self.page_limit,
        )
        result["mxtunnels"] = _fetch_and_log(
            "Mist Edge tunnels",
            mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels,
            session,
            self.org_id,
        )
        result["sitegroups"] = _fetch_and_log(
            "site groups",
            mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups,
            session,
            self.org_id,
        )

        total_calls = 5
        logging.info("Total org-level API calls: %d", total_calls)
        print(f"    Done ({total_calls} API calls)")
        return result

    # ------------------------------------------------------------------
    # Phase 1: Matrix builder
    # ------------------------------------------------------------------

    def _build_matrix(self, org_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build per-site consolidation matrix from org data."""
        mxtunnel_lookup = _build_mxtunnel_lookup(org_data.get("mxtunnels", []))
        template_lookup = _build_template_lookup(org_data.get("wlan_templates", []))
        sitegroup_lookup = _build_sitegroup_lookup(org_data.get("sitegroups", []))

        matrix: list[dict[str, Any]] = []
        for site in org_data.get("sites", []):
            row = _build_site_row(
                site,
                self.target_ssid,
                self.PSK_AUTH_TYPES,
                self.PILOT_PATTERN,
                template_lookup,
                sitegroup_lookup,
                mxtunnel_lookup,
            )
            if row:
                matrix.append(row)
        logging.info("Matrix built: %d sites", len(matrix))
        return matrix

    # ------------------------------------------------------------------
    # Phase 1: Deviation analysis
    # ------------------------------------------------------------------

    def _analyze_deviations(
        self,
        matrix: list[dict[str, Any]],
        org_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Detect per-cluster deviations and cross-cluster drift."""
        eligible = [row for row in matrix if not row.get("anomaly") and not row.get("psk_detected")]
        template_lookup = _build_template_lookup(org_data.get("wlan_templates", []))

        groups = _group_by_target(eligible)
        deviations: list[dict[str, Any]] = []
        cluster_canonicals: dict[str, dict[str, Any]] = {}

        for group_name, rows in groups.items():
            group_devs, canonicals = _analyze_group_deviations(
                group_name,
                rows,
                template_lookup,
                self.target_ssid,
                self.METADATA_FIELDS,
            )
            deviations.extend(group_devs)
            cluster_canonicals[group_name] = canonicals

        drift = _detect_cross_cluster_drift(cluster_canonicals)
        deviations.extend(drift)
        logging.info(
            "Deviations found: %d (including cross-cluster drift)",
            len(deviations),
        )
        return deviations

    # ------------------------------------------------------------------
    # Phase 2: Site Variables
    # ------------------------------------------------------------------

    def phase2_site_variables(self) -> None:
        """Phase 2 orchestrator — compute variable plan, write to sites."""
        print("\n=== Phase 2: Write Site Variables ===")
        logging.info("Phase 2: Starting site variable configuration")

        cached = self._load_cache()
        if not cached:
            print("! Phase 1 cache not found. Run Phase 1 first.")
            return
        self.cache = cached

        resuming, prior_results = self._offer_resume(2, [])
        plan = _compute_variable_plan(self.cache)
        if not plan:
            print("  No site variables to configure " "(no deviations detected).")
            return

        _display_variable_summary(plan)
        pending = len([p for p in plan if p["status"] == "pending"])
        if not self._confirm_or_cancel(f"Write site variables for {pending} sites?"):
            return

        results = self._write_site_variables(plan, prior_results if resuming else [])
        self._save_phase_results(2, results)
        self.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_site_vars",
            api_function_name="ssidConsolidationSiteVars",
        )
        _print_phase_summary("Phase 2", results)

    def _write_site_variables(
        self,
        plan: list[dict[str, Any]],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Write site variables via updateSiteInfo."""
        completed_ids = {row.get("site_id") for row in resume_from if row.get("status") == "written"}
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []

        pending_entries = [
            entry for entry in plan if entry["status"] == "pending" and entry["site_id"] not in completed_ids
        ]
        site_groups = _group_entries_by_site(pending_entries)

        for site_id, entries in site_groups.items():
            result = _write_single_site_vars(site_id, entries, self.cache, self.apisession)
            results.extend(result)
            if len(results) % 10 == 0:
                self._save_phase_results(2, results)

        return results

    # ------------------------------------------------------------------
    # Phase 3: Site Groups
    # ------------------------------------------------------------------

    def phase3_site_groups(self) -> None:
        """Phase 3 orchestrator — create groups and assign sites."""
        print("\n=== Phase 3: Create / Assign Site Groups ===")
        logging.info("Phase 3: Starting site group configuration")

        cached = self._load_cache()
        if not cached:
            print("! Phase 1 cache not found. Run Phase 1 first.")
            return
        self.cache = cached

        resuming, prior_results = self._offer_resume(3, [])
        group_plan = _compute_group_plan(self.cache)
        _display_group_plan(group_plan)

        group_count = len(group_plan["groups"])
        if not self._confirm_or_cancel(f"Create/assign {group_count} site groups?"):
            return

        group_plan = self._ensure_groups_exist(group_plan)
        results = self._assign_sites_to_groups(group_plan, prior_results if resuming else [])
        self._save_phase_results(3, results)
        self.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_site_groups",
            api_function_name="ssidConsolidationSiteGroups",
        )
        _print_phase_summary("Phase 3", results)

    def _ensure_groups_exist(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Create missing site groups and record their IDs."""
        for group in plan.get("groups", []):
            if group["exists"]:
                logging.info(
                    "Group '%s' already exists (id=%s)",
                    group["group_name"],
                    group["group_id"],
                )
                continue
            _create_site_group(group, self.org_id, self.apisession)
        return plan

    def _assign_sites_to_groups(
        self,
        plan: dict[str, Any],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Assign sites to their target groups via additive merge."""
        completed_ids: set[tuple[str, str]] = {
            (str(row.get("site_id", "")), str(row.get("group_id", "")))
            for row in resume_from
            if row.get("status") == "assigned"
        }
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []

        for group in plan.get("groups", []):
            if not group.get("group_id"):
                continue
            group_results = _assign_group_sites(
                group,
                completed_ids,
                self.cache,
                self.org_id,
                self.apisession,
            )
            results.extend(group_results)
        return results

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


# ======================================================================
# Module-level helper functions (pure logic, no self)
# ======================================================================


def _fetch_and_log(
    label: str,
    api_fn: Any,
    session: Any,
    org_id: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Fetch data via API, paginate, and log count."""
    print(f"    Fetching {label}...")
    response = api_fn(session, org_id, **kwargs)
    data: list[dict[str, Any]] = mistapi.get_all(response=response, mist_session=session) or []
    logging.info("%s fetched: %d", label.capitalize(), len(data))
    return data


def _build_mxtunnel_lookup(
    mxtunnels: list[dict[str, Any]],
) -> dict[str, str]:
    """Build cluster_id -> cluster_name lookup."""
    return {tunnel.get("id", ""): tunnel.get("name", "") for tunnel in mxtunnels if tunnel.get("id")}


def _build_template_lookup(
    templates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build template_id -> template object lookup."""
    return {tmpl.get("id", ""): tmpl for tmpl in templates if tmpl.get("id")}


def _build_sitegroup_lookup(
    sitegroups: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build sitegroup_id -> sitegroup object lookup."""
    return {group.get("id", ""): group for group in sitegroups if group.get("id")}


def _build_site_row(
    site: dict[str, Any],
    target_ssid: str,
    psk_auth_types: tuple[str, ...],
    pilot_pattern: re.Pattern[str],
    template_lookup: dict[str, dict[str, Any]],
    sitegroup_lookup: dict[str, dict[str, Any]],
    mxtunnel_lookup: dict[str, str],
) -> dict[str, Any] | None:
    """Build a single matrix row for one site."""
    site_id = site.get("id", "")
    site_name = site.get("name", "")
    if not site_id:
        return None

    template, template_id = _resolve_template(site, template_lookup, sitegroup_lookup)
    template_name = template.get("name", "") if template else ""
    wlans = _get_template_wlans(template) if template else []
    matched_wlan = _find_target_wlan(wlans, target_ssid)

    psk, anomaly, reason = _classify_site(template, wlans, matched_wlan, mxtunnel_lookup, psk_auth_types)

    mxtunnel_ids = matched_wlan.get("mxtunnel_ids", []) if matched_wlan else []
    first_tunnel_id = mxtunnel_ids[0] if mxtunnel_ids else ""
    cluster_name = mxtunnel_lookup.get(first_tunnel_id, "")
    target_group = _determine_target_group(site_name, cluster_name, pilot_pattern)

    return _assemble_site_row(
        site_name,
        site_id,
        template_name,
        template_id,
        matched_wlan,
        first_tunnel_id,
        cluster_name,
        psk,
        anomaly,
        reason,
        wlans,
        site,
        target_group,
    )


def _assemble_site_row(
    site_name: str,
    site_id: str,
    template_name: str,
    template_id: str,
    matched_wlan: dict[str, Any] | None,
    first_tunnel_id: str,
    cluster_name: str,
    psk_detected: bool,
    anomaly: bool,
    anomaly_reason: str,
    wlans: list[dict[str, Any]],
    site: dict[str, Any],
    target_group: str,
) -> dict[str, Any]:
    """Assemble the final site row dictionary."""
    return {
        "site_name": site_name,
        "site_id": site_id,
        "template_name": template_name,
        "template_id": template_id,
        "ssid_name": (matched_wlan.get("ssid", "") if matched_wlan else ""),
        "ssid_id": (matched_wlan.get("id", "") if matched_wlan else ""),
        "auth_type": (matched_wlan.get("auth", {}).get("type", "") if matched_wlan else ""),
        "vlan_id": (str(matched_wlan.get("vlan_id", "")) if matched_wlan else ""),
        "mxtunnel_id": first_tunnel_id,
        "mxtunnel_name": cluster_name,
        "psk_detected": psk_detected,
        "anomaly": anomaly,
        "anomaly_reason": anomaly_reason,
        "ssid_enabled": (matched_wlan.get("enabled", True) if matched_wlan else False),
        "ssid_count_in_template": len(wlans),
        "sitegroup_ids": json.dumps(site.get("sitegroup_ids") or []),
        "target_group": target_group,
    }


def _resolve_template(
    site: dict[str, Any],
    template_lookup: dict[str, dict[str, Any]],
    sitegroup_lookup: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    """Find the WLAN template assigned to a site via applies scope."""
    for template_id, template in template_lookup.items():
        applies = template.get("applies", {})
        site_ids = applies.get("site_ids") or []
        if site.get("id") in site_ids:
            return template, template_id
        group_ids = applies.get("sitegroup_ids") or []
        site_groups = site.get("sitegroup_ids") or []
        if any(gid in group_ids for gid in site_groups):
            return template, template_id
    return None, ""


def _get_template_wlans(
    template: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract WLANs list from a template object."""
    wlans: list[dict[str, Any]] = template.get("wlans", []) or []
    return wlans


def _find_target_wlan(wlans: list[dict[str, Any]], target_ssid: str) -> dict[str, Any] | None:
    """Find the WLAN matching the target SSID name."""
    for wlan in wlans:
        if wlan.get("ssid", "").lower() == target_ssid.lower():
            return wlan
    return None


def _classify_site(
    template: dict[str, Any] | None,
    wlans: list[dict[str, Any]],
    matched_wlan: dict[str, Any] | None,
    mxtunnel_lookup: dict[str, str],
    psk_auth_types: tuple[str, ...],
) -> tuple[bool, bool, str]:
    """Classify a site as PSK, anomaly, or eligible."""
    if not template:
        return False, True, "no template assigned"
    if not matched_wlan:
        return False, True, "target SSID not found"
    ssid_count = len(wlans)
    if ssid_count == 0:
        return False, True, "0 SSIDs"
    if ssid_count == 1:
        return False, True, "1 SSID"
    if ssid_count >= 3:
        return False, True, "3+ SSIDs"
    auth_type = matched_wlan.get("auth", {}).get("type", "")
    psk_detected = auth_type in psk_auth_types
    mxtunnel_ids = matched_wlan.get("mxtunnel_ids", [])
    first_id = mxtunnel_ids[0] if mxtunnel_ids else ""
    if not first_id or first_id not in mxtunnel_lookup:
        return psk_detected, True, "no Edge cluster mapping"
    return psk_detected, False, ""


def _determine_target_group(
    site_name: str,
    cluster_name: str,
    pilot_pattern: re.Pattern[str],
) -> str:
    """Assign target group — pilot if name matches pattern, else cluster."""
    if pilot_pattern.search(site_name):
        return "pilot"
    return cluster_name if cluster_name else "unknown"


# ------------------------------------------------------------------
# Deviation analysis helpers
# ------------------------------------------------------------------


def _group_by_target(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group matrix rows by target_group name."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        group_name = row.get("target_group", "unknown")
        groups.setdefault(group_name, []).append(row)
    return groups


def _analyze_group_deviations(
    group_name: str,
    rows: list[dict[str, Any]],
    template_lookup: dict[str, dict[str, Any]],
    target_ssid: str,
    metadata_fields: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Analyze deviations within a single group."""
    wlan_configs = _collect_group_wlan_configs(rows, template_lookup, target_ssid)
    if not wlan_configs:
        return [], {}

    all_keys = _collect_comparison_keys(wlan_configs, metadata_fields)
    deviations: list[dict[str, Any]] = []
    canonicals: dict[str, Any] = {}

    for key in all_keys:
        values_map = _collect_key_values(key, wlan_configs, rows)
        if len(values_map) > 1:
            deviation = _build_deviation_record(group_name, rows, key, values_map)
            deviations.append(deviation)
            canonicals[key] = deviation.get("canonical_value")
        elif values_map:
            canonicals[key] = next(iter(values_map.keys()))
    return deviations, canonicals


def _collect_group_wlan_configs(
    rows: list[dict[str, Any]],
    template_lookup: dict[str, dict[str, Any]],
    target_ssid: str,
) -> list[dict[str, Any]]:
    """Collect matched WLAN JSON dicts for all rows in a group."""
    configs: list[dict[str, Any]] = []
    for row in rows:
        template = template_lookup.get(row.get("template_id", ""))
        if not template:
            continue
        wlans = _get_template_wlans(template)
        matched = _find_target_wlan(wlans, target_ssid)
        if matched:
            configs.append(matched)
    return configs


def _collect_comparison_keys(
    wlan_configs: list[dict[str, Any]],
    metadata_fields: set[str],
) -> set[str]:
    """Build union of all WLAN config keys excluding metadata."""
    all_keys: set[str] = set()
    for config in wlan_configs:
        all_keys.update(config.keys())
    return all_keys - metadata_fields


def _collect_key_values(
    key: str,
    wlan_configs: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Collect unique values for a key with their site names."""
    values_map: dict[str, list[str]] = {}
    for index, config in enumerate(wlan_configs):
        value = json.dumps(config.get(key), default=str, sort_keys=True)
        site_name = rows[index].get("site_name", "") if index < len(rows) else ""
        values_map.setdefault(value, []).append(site_name)
    return values_map


def _build_deviation_record(
    group_name: str,
    rows: list[dict[str, Any]],
    key: str,
    values_map: dict[str, list[str]],
) -> dict[str, Any]:
    """Build a deviation record for a parameter with multiple values."""
    unique_values = [
        {
            "value": json.loads(value),
            "sites": sites,
            "count": len(sites),
        }
        for value, sites in values_map.items()
    ]
    unique_values.sort(key=lambda entry: entry["count"], reverse=True)
    canonical = unique_values[0]["value"] if unique_values else None
    cluster_id = rows[0].get("mxtunnel_id", "") if rows else ""
    return {
        "cluster_name": group_name,
        "cluster_id": cluster_id,
        "parameter": key,
        "unique_values": json.dumps(unique_values, default=str),
        "canonical_value": json.dumps(canonical, default=str),
    }


def _detect_cross_cluster_drift(
    cluster_canonicals: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect parameters where canonical values differ across clusters."""
    if len(cluster_canonicals) < 2:
        return []
    all_params: set[str] = set()
    for canonicals in cluster_canonicals.values():
        all_params.update(canonicals.keys())

    drift: list[dict[str, Any]] = []
    for param in all_params:
        values_by_cluster: dict[str, Any] = {}
        for cluster_name, canonicals in cluster_canonicals.items():
            if param in canonicals:
                values_by_cluster[cluster_name] = canonicals[param]
        unique_canonical = {json.dumps(value, default=str, sort_keys=True) for value in values_by_cluster.values()}
        if len(unique_canonical) > 1:
            _append_drift_record(drift, param, values_by_cluster)
    return drift


def _append_drift_record(
    drift: list[dict[str, Any]],
    param: str,
    values_by_cluster: dict[str, Any],
) -> None:
    """Append a cross-cluster drift deviation record."""
    unique_values = [{"value": value, "sites": [cluster], "count": 1} for cluster, value in values_by_cluster.items()]
    drift.append(
        {
            "cluster_name": "cross_cluster",
            "cluster_id": "",
            "parameter": param,
            "unique_values": json.dumps(unique_values, default=str),
            "canonical_value": "",
        }
    )


# ------------------------------------------------------------------
# Phase 2 helpers
# ------------------------------------------------------------------


def _compute_variable_plan(
    cache: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build variable assignment plan from Phase 1 deviations."""
    deviations = cache.get("deviations", [])
    matrix = cache.get("matrix", [])
    variable_params = _extract_deviation_params(deviations)
    if not variable_params:
        return []

    plan: list[dict[str, Any]] = []
    for row in matrix:
        if row.get("psk_detected") or row.get("anomaly"):
            for param in variable_params:
                plan.append(_build_skip_entry(row, param))
            continue
        site_vars = _get_cached_site_vars(cache, row.get("site_id", ""))
        for param in variable_params:
            entry = _build_variable_entry(row, param, site_vars)
            plan.append(entry)
    return plan


def _extract_deviation_params(
    deviations: list[dict[str, Any]],
) -> list[str]:
    """Extract unique parameter names from deviations."""
    params: set[str] = set()
    for deviation in deviations:
        if deviation.get("cluster_name") != "cross_cluster":
            params.add(deviation.get("parameter", ""))
    return sorted(params - {""})


def _build_skip_entry(row: dict[str, Any], param: str) -> dict[str, Any]:
    """Build a skipped variable entry for PSK/anomaly sites."""
    reason = "PSK site" if row.get("psk_detected") else f"Anomaly: {row.get('anomaly_reason', '')}"
    return {
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "variable_name": f"MISTHELPER_{param.upper()}",
        "proposed_value": "",
        "current_value": "",
        "status": "skipped",
        "reason": reason,
        "timestamp": "",
    }


def _get_cached_site_vars(cache: dict[str, Any], site_id: str) -> dict[str, str]:
    """Get existing site vars from cached org data."""
    for site in cache.get("data", {}).get("sites", []):
        if site.get("id") == site_id:
            vars_dict: dict[str, str] = site.get("vars", {}) or {}
            return vars_dict
    return {}


def _build_variable_entry(
    row: dict[str, Any],
    param: str,
    site_vars: dict[str, str],
) -> dict[str, Any]:
    """Build a single variable assignment entry."""
    var_name = f"MISTHELPER_{param.upper()}"
    proposed = str(row.get(param, row.get("vlan_id", "")))
    current = str(site_vars.get(var_name, ""))

    if current and current == proposed:
        status = "already_configured"
        reason = "Same value already exists"
    elif current and current != proposed:
        status = "conflict"
        reason = f"Existing value: {current}"
    else:
        status = "pending"
        reason = ""

    return {
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "variable_name": var_name,
        "proposed_value": proposed,
        "current_value": current,
        "status": status,
        "reason": reason,
        "timestamp": "",
    }


def _display_variable_summary(
    plan: list[dict[str, Any]],
) -> None:
    """Display variable assignment summary table."""
    pending = [e for e in plan if e["status"] == "pending"]
    skipped = [e for e in plan if e["status"] == "skipped"]
    configured = [e for e in plan if e["status"] == "already_configured"]
    conflicts = [e for e in plan if e["status"] == "conflict"]

    print("\n  Variable Assignment Plan:")
    print(f"    Pending:            {len(pending)}")
    print(f"    Already configured: {len(configured)}")
    print(f"    Conflicts:          {len(conflicts)}")
    print(f"    Skipped:            {len(skipped)}")

    if conflicts:
        _print_conflicts(conflicts)


def _print_conflicts(conflicts: list[dict[str, Any]]) -> None:
    """Print conflict details for variable summary."""
    print("\n  Conflicts (existing value differs from proposed):")
    for entry in conflicts[:10]:
        site = entry["site_name"]
        var_name = entry["variable_name"]
        current = entry["current_value"]
        proposed = entry["proposed_value"]
        print(f"    {site}: {var_name} = {current} -> {proposed}")
    if len(conflicts) > 10:
        print(f"    ... and {len(conflicts) - 10} more")


def _group_entries_by_site(
    entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group variable entries by site_id for batched writes."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        groups.setdefault(entry["site_id"], []).append(entry)
    return groups


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


def _compute_group_plan(cache: dict[str, Any]) -> dict[str, Any]:
    """Build site group assignment plan from matrix data."""
    matrix = cache.get("matrix", [])
    mxtunnels = cache.get("data", {}).get("mxtunnels", [])
    existing_groups = cache.get("data", {}).get("sitegroups", [])
    existing_lookup = {group.get("name", ""): group for group in existing_groups}

    cluster_names = sorted({tunnel.get("name", "") for tunnel in mxtunnels if tunnel.get("name")})
    groups = _build_cluster_groups(cluster_names, existing_lookup)
    _add_pilot_group(groups, existing_lookup)

    group_name_map = {g["group_name"]: g for g in groups}
    _assign_matrix_sites(matrix, group_name_map)
    return {"groups": groups}


def _build_cluster_groups(
    cluster_names: list[str],
    existing_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build production group entries for each cluster."""
    groups: list[dict[str, Any]] = []
    for cluster_name in cluster_names:
        group_name = f"misthelper_prod_{cluster_name}"
        existing = existing_lookup.get(group_name)
        groups.append(
            {
                "group_name": group_name,
                "cluster_name": cluster_name,
                "group_id": (existing.get("id", "") if existing else ""),
                "exists": bool(existing),
                "sites": [],
            }
        )
    return groups


def _add_pilot_group(
    groups: list[dict[str, Any]],
    existing_lookup: dict[str, dict[str, Any]],
) -> None:
    """Add the pilot site group entry."""
    pilot_existing = existing_lookup.get("misthelper_pilot")
    groups.append(
        {
            "group_name": "misthelper_pilot",
            "cluster_name": "pilot",
            "group_id": (pilot_existing.get("id", "") if pilot_existing else ""),
            "exists": bool(pilot_existing),
            "sites": [],
        }
    )


def _assign_matrix_sites(
    matrix: list[dict[str, Any]],
    group_name_map: dict[str, dict[str, Any]],
) -> None:
    """Assign matrix sites to their target groups."""
    for row in matrix:
        if row.get("psk_detected") or row.get("anomaly"):
            continue
        target = row.get("target_group", "")
        mapped = "misthelper_pilot" if target == "pilot" else f"misthelper_prod_{target}"
        target_group = group_name_map.get(mapped)
        if target_group:
            target_group["sites"].append(
                {
                    "site_id": row.get("site_id", ""),
                    "site_name": row.get("site_name", ""),
                }
            )


def _display_group_plan(plan: dict[str, Any]) -> None:
    """Print the group assignment plan."""
    print("\n  Site Group Plan:")
    for group in plan.get("groups", []):
        status = "exists" if group["exists"] else "to create"
        site_count = len(group["sites"])
        print(f"    {group['group_name']} ({status}) " f"- {site_count} sites")
        for site in group["sites"][:5]:
            print(f"      - {site['site_name']}")
        if len(group["sites"]) > 5:
            print(f"      ... and {len(group['sites']) - 5} more")


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


def _build_assign_results(
    sites: list[dict[str, Any]],
    existing_ids: list[str],
    group: dict[str, Any],
    group_id: str,
) -> list[dict[str, Any]]:
    """Build assignment result records for successful operations."""
    timestamp = datetime.now().isoformat()
    results: list[dict[str, Any]] = []
    for site in sites:
        status = "already_assigned" if site["site_id"] in existing_ids else "assigned"
        results.append(
            {
                "site_name": site["site_name"],
                "site_id": site["site_id"],
                "group_name": group["group_name"],
                "group_id": group_id,
                "cluster_name": group.get("cluster_name", ""),
                "status": status,
                "reason": "",
                "timestamp": timestamp,
            }
        )
    return results


def _build_failed_assign_results(
    sites: list[dict[str, Any]],
    group: dict[str, Any],
    group_id: str,
    error: Exception,
) -> list[dict[str, Any]]:
    """Build failed assignment result records."""
    return [
        {
            "site_name": site["site_name"],
            "site_id": site["site_id"],
            "group_name": group["group_name"],
            "group_id": group_id,
            "cluster_name": group.get("cluster_name", ""),
            "status": "failed",
            "reason": str(error),
            "timestamp": datetime.now().isoformat(),
        }
        for site in sites
    ]


def _get_existing_group_site_ids(cache: dict[str, Any], group_id: str) -> list[str]:
    """Get current site_ids from cached sitegroup data."""
    for group in cache.get("data", {}).get("sitegroups", []):
        if group.get("id") == group_id:
            ids: list[str] = group.get("site_ids", []) or []
            return ids
    return []


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


def _print_phase1_summary(
    matrix: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
) -> None:
    """Print Phase 1 audit summary."""
    eligible = [row for row in matrix if not row.get("anomaly") and not row.get("psk_detected")]
    psk_count = sum(1 for row in matrix if row.get("psk_detected"))
    anomaly_count = sum(1 for row in matrix if row.get("anomaly"))
    print(f"\n  Total sites:   {len(matrix)}")
    print(f"  Eligible:      {len(eligible)}")
    print(f"  PSK excluded:  {psk_count}")
    print(f"  Anomalies:     {anomaly_count}")
    print(f"  Deviations:    {len(deviations)}")
    logging.info(
        "Phase 1 complete: %d sites, %d eligible, %d deviations",
        len(matrix),
        len(eligible),
        len(deviations),
    )


def _print_phase_summary(phase_label: str, results: list[dict[str, Any]]) -> None:
    """Print a summary of phase results by status."""
    status_counts: dict[str, int] = {}
    for result in results:
        status = result.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"\n  {phase_label} Summary:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")
